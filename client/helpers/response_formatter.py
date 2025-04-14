import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
from .templates import TEMPLATES
import re
import copy

load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_information_with_llm(tool_name: str, raw_data: str, llm_response: str) -> Dict[str, Any]:
    """
    Usa un LLM para extraer y estructurar la información relevante.
    
    Args:
        tool_name: Nombre de la herramienta
        raw_data: Datos raw de la respuesta
        llm_response: Respuesta del LLM con información estructurada
        
    Returns:
        Diccionario con la información estructurada
    """
    # Obtener la plantilla correspondiente
    template = TEMPLATES.get(tool_name, TEMPLATES["airbnb_search"])
    
    # Crear el prompt para el LLM
    prompt = f'''
    Analiza la siguiente información y extrae los datos relevantes según la plantilla proporcionada.
    
    Datos raw:
    {raw_data}
    
    Respuesta del LLM:
    {llm_response}
    
    Plantilla a seguir:
    {json.dumps(template, indent=2)}
    
    Extrae la información relevante y devuélvela en formato JSON siguiendo la estructura de la plantilla.
    Solo incluye los campos que puedas extraer de manera confiable.
    '''
    
    try:
        print(prompt)
        # Llamar al LLM para extraer la información
        response = openai_client.chat.completions.create(
            model="o3-mini-2025-01-31",
            messages=[
                {"role": "system", "content": "Eres un asistente especializado en extraer y estructurar información."},
                {"role": "user", "content": prompt}
            ],
        )
        # Parsear la respuesta del LLM
        extracted_data = json.loads(response.choices[0].message.content)
        return extracted_data
        
    except Exception as e:
        print(f"Error al extraer información con LLM: {str(e)}")
        return template

def format_tool_result(tool_name: str, result: str, llm_response: str) -> Dict[str, Any]:
    """
    Formatea el resultado de una herramienta usando una plantilla predefinida
    y la respuesta del LLM para extraer la información relevante.
    
    Args:
        tool_name: Nombre de la herramienta que generó el resultado
        result: Resultado raw de la herramienta
        llm_response: Respuesta del LLM que contiene la información estructurada
        
    Returns:
        Un diccionario con la información formateada según la plantilla
    """
    try:
        # Parsear el resultado raw
        raw_data = json.loads(result) if isinstance(result, str) else result
        
        # Extraer información usando el LLM
        formatted_data = extract_information_with_llm(tool_name, json.dumps(raw_data), llm_response)
        
        # Asegurar que el resultado tenga la estructura correcta
        return {
            "type": tool_name,
            "data": formatted_data
        }
        
    except Exception as e:
        print(f"Error al formatear el resultado: {str(e)}")
        return {
            "type": tool_name,
            "data": {
                "error": str(e),
                "raw_result": result
            }
        }

def format_conversation_response(
    query: str,
    assistant_response: str,
    tool_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Formatea la respuesta completa de la conversación.
    
    Args:
        query: Consulta original del usuario
        assistant_response: Respuesta del asistente
        tool_results: Lista de resultados formateados de las herramientas
        
    Returns:
        Un diccionario con la respuesta formateada
    """
    try:
        # Asegurar que la respuesta del asistente no esté vacía
        if not assistant_response or assistant_response.isspace():
            assistant_response = "Aquí tienes la información solicitada."
        
        # Devolver solo el texto en formato JSON
        return {
            "texto": assistant_response
        }
        
    except Exception as e:
        print(f"Error al formatear la respuesta: {str(e)}")
        return {
            "texto": "Lo siento, ocurrió un error al procesar tu consulta."
        }

def _clean_directions(maps_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Limpia y formatea los datos de direcciones eliminando etiquetas HTML.
    
    Args:
        maps_data: Datos de mapas en formato JSON
        
    Returns:
        Datos de mapas limpios
    """
    # Crear una copia para no modificar el original
    cleaned_data = copy.deepcopy(maps_data)
    
    # Limpiar las instrucciones en cada paso
    for route in cleaned_data.get("routes", []):
        for step in route.get("steps", []):
            if "instructions" in step:
                # Eliminar etiquetas HTML
                instructions = step["instructions"]
                instructions = re.sub(r'<[^>]*>', '', instructions)  # Eliminar todas las etiquetas HTML
                instructions = re.sub(r'\s+', ' ', instructions)      # Normalizar espacios
                step["instructions"] = instructions.strip()
    
    return cleaned_data

def _extract_places_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extrae información de lugares a partir de texto plano.
    
    Args:
        text: Texto que contiene información sobre lugares
        
    Returns:
        Lista de lugares extraídos
    """
    places = []
    
    # Si hay una sección con lugares listados con viñetas, extraerlos
    bullet_pattern = r'[•\-]\s*([^•\n]+)'
    bullets = re.findall(bullet_pattern, text)
    
    if bullets:
        for bullet in bullets:
            # Limpiar y formatear el texto
            bullet_text = re.sub(r'<[^>]*>', '', bullet)  # Eliminar etiquetas HTML
            bullet_text = re.sub(r'\s+', ' ', bullet_text)  # Normalizar espacios
            
            # Intentar separar nombre y descripción si hay dos puntos
            if ":" in bullet_text:
                name, description = bullet_text.split(":", 1)
            else:
                # Buscar el primer período o coma para separar nombre y descripción
                match = re.search(r'[.,]', bullet_text)
                if match:
                    name = bullet_text[:match.start()].strip()
                    description = bullet_text[match.start()+1:].strip()
                else:
                    name = bullet_text
                    description = ""
                
            places.append({
                "nombre": name.strip(),
                "descripcion": description.strip()
            })
    
    # Si no se encontraron lugares con viñetas, buscar párrafos
    if not places:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for p in paragraphs:
            if "Plaza de Mayo" in p:
                places.append({
                    "nombre": "Lugares cerca de Plaza de Mayo",
                    "descripcion": re.sub(r'<[^>]*>', '', p)  # Eliminar etiquetas HTML
                })
                break
    
    return places 