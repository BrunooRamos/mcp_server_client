import asyncio
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Dict, Any

load_dotenv()

class MCPClient:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Configuración para los servidores MCP
        self.airbnb_server_params = StdioServerParameters(
            command="node",
            args=["/Users/brunoramos/Desktop/Bruno/mcp/servers/mcp-server-airbnb/dist/index.js", "--ignore-robots-txt"],
        )
        
        self.google_maps_server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-google-maps"],
            env={"GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY")}
        )

    def convert_mcp_tools_to_openai_format(self, mcp_tools):
        """Convierte herramientas MCP al formato esperado por OpenAI."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in mcp_tools
        ]

    async def list_all_tools(self):
        """Lista todas las herramientas disponibles de ambos servidores."""
        all_tools = []
        
        # Obtener herramientas de Airbnb
        try:
            async with stdio_client(self.airbnb_server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    airbnb_tools = await session.list_tools()
                    print("[INFO] Herramientas de Airbnb cargadas")
                    all_tools.extend(airbnb_tools.tools)
        except Exception as e:
            print(f"[ERROR] Al obtener herramientas de Airbnb: {str(e)}")
        
        # Obtener herramientas de Google Maps
        try:
            async with stdio_client(self.google_maps_server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    maps_tools = await session.list_tools()
                    print("[INFO] Herramientas de Google Maps cargadas")
                    all_tools.extend(maps_tools.tools)
        except Exception as e:
            print(f"[ERROR] Al obtener herramientas de Google Maps: {str(e)}")
        
        return all_tools

    async def process_query(self, query: str):
        """Procesa la consulta usando los clientes MCP."""
        try:
            # Procesar con Google Maps
            maps_results = await self._process_with_server(
                query, 
                self.google_maps_server_params, 
                "Google Maps"
            )
            
            # Procesar con Airbnb
            airbnb_results = await self._process_with_server(
                query, 
                self.airbnb_server_params, 
                "Airbnb"
            )
            
            # Combinar resultados
            all_results = []
            
            if maps_results:
                all_results.append(maps_results)
                
            if airbnb_results:
                all_results.append(airbnb_results)
                
            if not all_results:
                return "No se pudieron obtener resultados de ninguna fuente."
                
            return "\n".join(all_results)
            
        except Exception as e:
            print(f"[ERROR] Durante el procesamiento de la consulta: {str(e)}")
            return f"Error al procesar la consulta: {str(e)}"
            
    async def _process_with_server(self, query: str, server_params: StdioServerParameters, server_name: str):
        """Procesa una consulta con un servidor específico."""
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    results = await self.handle_conversation(query, tools.tools, session)
                    if results:
                        return results
            return None
        except Exception as e:
            print(f"[ERROR] Al procesar con {server_name}: {str(e)}")
            return f"\n=== Resultados de {server_name} ===\nError: {str(e)}"

    async def handle_conversation(self, query: str, tools: list, session: ClientSession):
        """Gestiona la conversación con OpenAI y las llamadas a herramientas."""
        print("\n[INICIO] Nueva conversación")
        print(f"[QUERY] {query}")
        
        # Inicialización
        conversation = [{"role": "user", "content": query}]
        tool_results = []
        
        while True:
            try:
                # Llamar a OpenAI
                print("\n[OPENAI] Enviando consulta")
                response = self.openai_client.chat.completions.create(
                    model="o3-mini-2025-01-31",
                    messages=conversation,
                    tools=self.convert_mcp_tools_to_openai_format(tools),
                    tool_choice="auto"
                )
                message = response.choices[0].message
                
                # Procesar respuesta
                has_tool_calls = hasattr(message, "tool_calls") and message.tool_calls
                assistant_message = {"role": "assistant", "content": message.content or ""}
                
                if has_tool_calls:
                    print("[TOOL_CALLS] Iniciando llamadas")
                    tool_calls_data = []
                    for tc in message.tool_calls:
                        tool_calls_data.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        })
                        print(f"[TOOL] {tc.function.name}")
                    assistant_message["tool_calls"] = tool_calls_data
                
                # Actualizar conversación
                conversation.append(assistant_message)
                
                # Verificar si terminamos
                if not has_tool_calls:
                    print("[FIN] No hay más llamadas")
                    break
                
                # Procesar cada llamada a herramienta
                for tool_call in message.tool_calls:
                    result_content = await self._process_tool_call(tool_call, session)
                    
                    if result_content:
                        # Guardar resultado
                        tool_results.append({
                            "type": tool_call.function.name,
                            "data": result_content
                        })
                        
                        # Añadir a la conversación
                        conversation.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": result_content
                        })
                
            except Exception as e:
                print(f"[ERROR] En la conversación: {str(e)}")
                break
        
        # Obtener respuesta final
        final_response = "No se pudo obtener una respuesta clara."
        for msg in reversed(conversation):
            if msg.get("role") == "assistant" and msg.get("content"):
                final_response = msg["content"]
                break
        
        print("[FINAL] Respuesta generada")
        
        # Construir respuesta completa
        server_type = "Google Maps" if any("maps" in r["type"] for r in tool_results) else "Airbnb"
        return self._format_response(final_response, tool_results, server_type)
    
    async def _process_tool_call(self, tool_call, session):
        """Procesa una llamada a una herramienta."""
        try:
            print(f"[PROCESANDO] {tool_call.function.name}")
            args = json.loads(tool_call.function.arguments)
            
            result = await session.call_tool(tool_call.function.name, args)
            print(f"[OK] Llamada completada")
            
            if hasattr(result, 'content'):
                content = result.content
                if isinstance(content, list):
                    content = content[0].text if content else ""
                
                # Formatear contenido
                formatted_content = content
                try:
                    if content and content.strip().startswith('{') and content.strip().endswith('}'):
                        json_content = json.loads(content)
                        formatted_content = json.dumps(json_content, ensure_ascii=False, indent=2)
                        print("[FORMATO] JSON válido")
                    else:
                        print("[FORMATO] Texto plano")
                except json.JSONDecodeError as e:
                    print(f"[ERROR] JSON inválido: {str(e)}")
                
                return formatted_content
            else:
                raise ValueError("El resultado no tiene contenido")
            
        except Exception as e:
            print(f"[ERROR] {tool_call.function.name}: {str(e)}")
            return f"Error: {str(e)}"
    
    def _format_response(self, assistant_response, tool_results, server_type):
        """Formatea la respuesta final combinando la respuesta del asistente y los resultados."""
        response_parts = [assistant_response]
        
        # Añadir resultados de herramientas
        for result in tool_results:
            try:
                tool_type = result["type"]
                tool_data = result["data"]
                
                # Determinar tipo de servidor
                result_server_type = "Google Maps" if "maps" in tool_type else "Airbnb"
                
                # Añadir encabezado
                response_parts.append(f"\n=== Resultados de {result_server_type} ===")
                
                # Añadir datos
                if isinstance(tool_data, str):
                    response_parts.append(tool_data)
                else:
                    response_parts.append(str(tool_data))
                    
            except Exception as e:
                print(f"[ERROR] Al formatear resultado: {str(e)}")
        
        return "\n".join(response_parts)

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Retorna la lista de herramientas disponibles."""
        try:
            all_tools = asyncio.run(self.list_all_tools())
            
            return [{
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            } for tool in all_tools]
            
        except Exception as e:
            print(f"[ERROR] Al obtener herramientas: {str(e)}")
            return []

async def main():
    client = MCPClient()
    await client.list_all_tools()
    
    while True:
        query = input("\nIngrese su búsqueda (o 'quit' para salir): ")
        if query.lower() == 'quit':
            break
        
        final_response = await client.process_query(query)
        print(f"\nRespuesta final:\n{final_response}")

if __name__ == "__main__":
    asyncio.run(main())
