# Nova — Conversational Support Agent for E-commerce

Nova is an AI-powered customer support agent designed for a retail/e-commerce context. It handles the most common post-sale interactions through natural, Spanish-language conversation.

Built as a end-to-end demonstration of conversational AI design: intent mapping, tool use architecture, multi-turn dialogue flow, fallback handling, and escalation to human agents.

---

## What Nova can do

| User intent | What happens |
|---|---|
| Check order status | Verifies identity, queries order DB, reports current status |
| Report a delivery problem | Logs a support case, assigns case number, estimates resolution time |
| Request a return or exchange | Validates 30-day return policy, generates RMA number, gives instructions |
| Ask about payment methods | Responds directly, no identity verification needed |
| Complex or sensitive case | Escalates to human agent with priority level and notes |

---

## Project structure

```
nova-ecommerce-bot/
├── nova_ecommerce_bot.py   ← core file: policy prompt, tool definitions, business logic
├── nova_chat.py            ← conversation loop connecting Nova to the API
├── requirements.txt
└── .gitignore
```

### `nova_ecommerce_bot.py` — the core file

This is where the conversational design lives:

- **`POLICY`** — the system prompt that defines Nova's role, interaction flow, communication style, and restrictions. Written as production-level bot copy in Spanish.
- **`TOOL_DEFINITIONS`** — the six tools Nova can call, each with typed parameters and descriptions written for the model to understand when and how to use them.
- **`EcommerceTools`** — the class that implements each tool with a mock database of orders, customers, complaints, and returns. Includes realistic Argentine data (local couriers, local payment methods, ARS pricing).

### `nova_chat.py` — the runner

Implements the tool-use loop: sends the conversation history to the Claude API, detects tool calls in the response, executes them locally, feeds the results back, and repeats until Nova produces a final text response.

---

## Conversation flow

```
User message
     │
     ▼
API (Nova's policy + tool definitions + conversation history)
     │
     ├── stop_reason: "end_turn"  →  Nova replies in text
     │
     └── stop_reason: "tool_use" →  tool executed locally
                                         │
                                         ▼
                                    result sent back to API
                                         │
                                         ▼
                                    Nova replies in text
```

---

## Tools

| Tool | Trigger intent | Key parameters |
|---|---|---|
| `verificar_cliente` | Any inquiry requiring identity | `numero_pedido`, `apellido` |
| `consultar_estado_pedido` | "Where is my order?" | `numero_pedido` |
| `registrar_reclamo` | Delivery problem | `tipo_reclamo`, `descripcion` |
| `iniciar_devolucion` | Return or exchange | `motivo_devolucion`, `productos`, `tipo` |
| `consultar_medios_de_pago` | Payment methods | `tipo_consulta` |
| `derivar_a_agente` | Complex / sensitive case | `motivo_derivacion`, `prioridad` |

---

## Test data included

The mock database includes five customer orders in different states so you can test every flow immediately:

| Order | Status | Good for testing |
|---|---|---|
| TM-1001 / García | En camino | Order status query |
| TM-1002 / Rodríguez | Entregado | Return request |
| TM-1003 / López | Preparando | Early-stage order |
| TM-1004 / Fernández | Demorado | Complaint + escalation |
| TM-2000 / Test | Entregado | General testing |

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/nova-ecommerce-bot.git
cd nova-ecommerce-bot
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set your Anthropic API key**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**4. Run**
```bash
python3 nova_chat.py
```

---

## Example conversation

```
Nova: ¡Hola! Soy Nova, tu asistente de TiendaMax. ¿En qué puedo ayudarte hoy?

Vos: Quiero saber dónde está mi pedido

Nova: Con gusto te ayudo. ¿Me podés dar tu número de pedido y apellido?

Vos: TM-1001, García

  [🔧 Consultando sistema: verificar_cliente...]
  [🔧 Consultando sistema: consultar_estado_pedido...]

Nova: ¡Hola, Carlos! Tu pedido TM-1001 está en camino. 
      El último registro lo ubica en el centro de distribución de Córdoba 
      y la fecha estimada de entrega es el 15 de junio. 
      Tu número de seguimiento con Andreani es AND-7823456.
      ¿Hay algo más en lo que pueda ayudarte?
```

---

## Stack

- **Language:** Python 3.10+
- **AI:** Anthropic Claude API (`claude-sonnet-4-6`) with Tool Use
- **Architecture:** stateful multi-turn conversation loop with local tool execution
- **Language of conversation:** Spanish (Argentina)
