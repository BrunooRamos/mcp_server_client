from flask import Flask, request, jsonify
import asyncio
import json
from client.client import MCPClient
from client.helpers.response_formatter import format_conversation_response
import os
from dotenv import load_dotenv
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
client = MCPClient()

@app.route('/', methods=['GET'])
def index():
    return "Hello, World!"

@app.route('/query', methods=['POST'])
def handle_query():
    """Endpoint para procesar consultas."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Se requiere un campo "query" en el cuerpo de la solicitud'
            }), 400

        query = data['query']
        
        # Ejecuta la consulta de forma asíncrona
        try:
            # Obtener la respuesta raw
            raw_response = asyncio.run(client.process_query(query))
            logger.info(f"Respuesta raw recibida")
            
            # Extraer la respuesta del asistente y los resultados de herramientas
            try:
                # Dividir la respuesta por secciones
                sections = raw_response.split("\n=== Resultados de ")
                
                # La primera sección es la respuesta del asistente
                assistant_response = sections[0].strip() if sections else ""
                
                # Procesar secciones específicas (Google Maps o generales, ignorando Airbnb)
                tool_results = []
                for i, section in enumerate(sections[1:], 1):
                    if not section.strip():
                        continue
                        
                    # Determinar el tipo de herramienta
                    section_header = section.split("\n")[0] if section else ""
                    tool_type = ""
                    
                    # Ignora Airbnb ya que no es relevante para esta consulta
                    if "Airbnb" in section_header:
                        continue
                    
                    # Determinar tipo de resultado
                    if "Google Maps" in section_header:
                        if "lugares" in section.lower() or "direcciones" in section.lower():
                            tool_type = "maps_search_places"
                        else:
                            tool_type = "maps_directions"
                    else:
                        # Si no podemos determinar, usar un tipo genérico
                        tool_type = "general_results"
                    
                    # Extraer el contenido (omitir la primera línea que es parte del encabezado)
                    content_lines = section.split("\n")[1:] if section else []
                    content = "\n".join(content_lines).strip()
                    
                    if content:
                        tool_results.append({
                            "type": tool_type,
                            "data": content
                        })
                
                # Si no hay respuesta del asistente, usar uno por defecto
                if not assistant_response:
                    assistant_response = "Aquí tienes la información solicitada sobre tu consulta."
                
                # Formatear usando el response_formatter
                formatted_response = format_conversation_response(
                    query=query,
                    assistant_response=assistant_response,
                    tool_results=tool_results
                )
                
                # Verificar si necesitamos hacer algo más con la respuesta antes de enviarla
                return jsonify(formatted_response)
                
            except Exception as format_error:
                logger.error(f"Error al formatear la respuesta: {str(format_error)}")
                # Si falla el formateo, intentar usar el formatter con la respuesta raw
                fallback_response = format_conversation_response(
                    query=query,
                    assistant_response="Aquí tienes la información solicitada.",
                    tool_results=[{"type": "general_results", "data": raw_response}]
                )
                return jsonify(fallback_response)
                
        except Exception as e:
            logger.error(f"Error al procesar la consulta: {str(e)}")
            return jsonify({
                'query': query,
                'response': f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}",
                'data': {}
            }), 500
        
    except Exception as e:
        logger.error(f"Error en el endpoint: {str(e)}")
        return jsonify({
            'error': f'Error en el servidor: {str(e)}'
        }), 500

@app.route('/tools', methods=['GET'])
def list_tools():
    """
    Endpoint para listar todas las herramientas disponibles.
    """
    try:
        # Obtener la lista de herramientas del cliente
        tools = client.get_available_tools()
        
        # Formatear la respuesta
        tools_list = []
        for tool in tools:
            tools_list.append({
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            })
        
        return jsonify({
            "status": "success",
            "tools": tools_list
        })
        
    except Exception as e:
        logger.error(f"Error al listar herramientas: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5005) 