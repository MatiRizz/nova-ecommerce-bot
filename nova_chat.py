import os
import json
import litellm
from nova_ecommerce_bot import POLICY, TOOL_DEFINITIONS, TOOLS

# ── Configuración del modelo ──────────────────────────────────────────────────
#
#  Cambiá MODEL y la variable de entorno correspondiente para usar otro proveedor.
#
#  Anthropic (default):
#    MODEL = "claude-sonnet-4-6"
#    export ANTHROPIC_API_KEY="sk-ant-..."
#
#  OpenAI:
#    MODEL = "gpt-4o"
#    export OPENAI_API_KEY="sk-..."
#
#  Google Gemini:
#    MODEL = "gemini/gemini-1.5-pro"
#    export GEMINI_API_KEY="..."
#
MODEL = os.environ.get("NOVA_MODEL", "claude-sonnet-4-6")


# ── Ejecutar tool call localmente ─────────────────────────────────────────────
def ejecutar_tool(nombre: str, argumentos: dict) -> str:
    """Despacha la llamada al método correspondiente en TOOLS y devuelve JSON."""
    metodos = {
        "verificar_cliente":        TOOLS.verificar_cliente,
        "consultar_estado_pedido":  TOOLS.consultar_estado_pedido,
        "registrar_reclamo":        TOOLS.registrar_reclamo,
        "iniciar_devolucion":       TOOLS.iniciar_devolucion,
        "consultar_medios_de_pago": TOOLS.consultar_medios_de_pago,
        "derivar_a_agente":         TOOLS.derivar_a_agente,
    }

    if nombre not in metodos:
        return json.dumps({"error": f"Tool '{nombre}' no encontrada."})

    try:
        resultado = metodos[nombre](**argumentos)
        return json.dumps(resultado, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Loop principal de conversación ────────────────────────────────────────────
def chat():
    historial = []

    print("=" * 60)
    print(f"  Nova — Soporte al Cliente de TiendaMax")
    print(f"  Modelo: {MODEL}")
    print("  (escribí 'salir' para terminar)")
    print("=" * 60)

    # Saludo inicial de Nova
    respuesta_inicial = litellm.completion(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": POLICY},
            {"role": "user",   "content": "Hola"},
        ],
        tools=TOOL_DEFINITIONS,
    )
    saludo = respuesta_inicial.choices[0].message.content or ""
    print(f"\nNova: {saludo.strip()}\n")

    historial.append({"role": "user",      "content": "Hola"})
    historial.append({"role": "assistant", "content": saludo})

    # Loop de turnos
    while True:
        entrada = input("Vos: ").strip()
        if not entrada:
            continue
        if entrada.lower() in ("salir", "exit", "chau", "bye"):
            print("\nNova: ¡Hasta luego! Que tengas un excelente día. 👋\n")
            break

        historial.append({"role": "user", "content": entrada})

        # Ciclo de tool use
        while True:
            respuesta = litellm.completion(
                model=MODEL,
                max_tokens=1024,
                messages=[{"role": "system", "content": POLICY}] + historial,
                tools=TOOL_DEFINITIONS,
            )

            mensaje = respuesta.choices[0].message
            finish_reason = respuesta.choices[0].finish_reason

            # Mostrar texto si lo hay
            if mensaje.content:
                print(f"\nNova: {mensaje.content.strip()}\n")

            # Agregar respuesta del asistente al historial
            historial.append({"role": "assistant", "content": mensaje.content or ""})

            # Si no hay tool calls, terminamos este turno
            if finish_reason != "tool_calls" or not mensaje.tool_calls:
                break

            # Procesar tool calls y devolver resultados
            for tool_call in mensaje.tool_calls:
                nombre = tool_call.function.name
                argumentos = json.loads(tool_call.function.arguments)

                print(f"  [🔧 Consultando sistema: {nombre}...]")
                resultado_str = ejecutar_tool(nombre, argumentos)

                historial.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": nombre,
                    "content": resultado_str,
                })


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Verificar que haya al menos una API key configurada
    claves = {
        "ANTHROPIC_API_KEY": "Anthropic (Claude)",
        "OPENAI_API_KEY":    "OpenAI (GPT)",
        "GEMINI_API_KEY":    "Google (Gemini)",
    }
    configuradas = [nombre for var, nombre in claves.items() if os.environ.get(var)]

    if not configuradas:
        print("\n⚠️  No encontré ninguna API key configurada.")
        print("   Según el modelo que quieras usar, ejecutá uno de estos:")
        print("   export ANTHROPIC_API_KEY='sk-ant-...'   # para Claude")
        print("   export OPENAI_API_KEY='sk-...'          # para GPT")
        print("   export GEMINI_API_KEY='...'             # para Gemini")
        print("\n   Luego podés elegir el modelo con:")
        print("   export NOVA_MODEL='gpt-4o'              # o gemini/gemini-1.5-pro\n")
    else:
        chat()
