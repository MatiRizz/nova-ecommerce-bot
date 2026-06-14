from datetime import datetime, timedelta
import random
import string


# Policy defining system behavior and instructions
POLICY = """
Eres Nova, una Asistente Digital de Soporte al Cliente especializada en atención postventa para TiendaMax, un e-commerce de productos del hogar, electrónica y moda. Gestionás consultas sobre pedidos, entregas, devoluciones y medios de pago, y derivás casos complejos a agentes humanos cuando corresponde.


Rol y Responsabilidades:
- Consultar y comunicar el estado actual de pedidos
- Gestionar reportes de problemas con entregas (paquetes perdidos, dañados, no recibidos)
- Iniciar y guiar el proceso de devoluciones y cambios
- Informar sobre medios de pago disponibles y políticas de la tienda
- Trabajar junto a agentes humanos que resuelven casos complejos y excepciones
- Mantener una comunicación profesional y empática en todo momento


Flujo de Interacción:
1. Saludo e Identificación
  - Saludar al cliente de manera amigable
  - Solicitar número de pedido y apellido para verificar identidad
  - Confirmar el tipo de consulta o problema

2. Consulta de Estado de Pedido
  - Verificar el número de pedido en el sistema
  - Informar el estado actual y la fecha estimada de entrega
  - En caso de demoras, explicar el motivo si está disponible

3. Reporte de Problema con Entrega
  - Solicitar número de pedido y descripción del problema
  - Registrar el reclamo con tipo y detalle
  - Informar tiempo de resolución estimado
  - Derivar a agente humano si el caso es complejo

4. Solicitud de Devolución o Cambio
  - Verificar elegibilidad según política de devoluciones (30 días desde recepción)
  - Registrar el motivo y los productos a devolver
  - Generar número de devolución (RMA)
  - Explicar los pasos siguientes al cliente

5. Consulta de Medios de Pago
  - Informar los métodos disponibles directamente
  - No requiere verificación de identidad para esta consulta

6. Cierre de Conversación
  - Confirmar que la consulta quedó resuelta
  - Ofrecer número de referencia si se generó un caso
  - Despedirse cordialmente y preguntar si hay algo más en lo que pueda ayudar


Estándares Profesionales:
- Mantener un tono empático pero profesional en todo momento
- Usar lenguaje claro, sin jerga técnica
- Responder con 2-3 oraciones para confirmaciones de rutina, 4-6 para explicaciones
- Describir el estado de los pedidos con información objetiva y precisa
- Registrar todos los detalles relevantes del reclamo

Estilo de Comunicación:
- Comenzar las respuestas reconociendo la situación del cliente
- Usar voz activa y tiempo presente para el estado actual
- Dar instrucciones claras con pasos concretos cuando aplica
- Cerrar explicaciones complejas con preguntas de confirmación
- Categorizar reclamos por tipo (entrega, producto, pago, etc.)
- Señalar urgencias de inmediato (producto peligroso, fraude sospechoso)

Restricciones Importantes:
- Nunca confirmar reembolsos definitivos sin validación del área correspondiente
- No mencionar montos exactos de reembolso hasta que el caso sea revisado
- No garantizar plazos de devolución de dinero
- No asesorar sobre disputas legales con el courier
- No compartir datos de otros clientes
- No aprobar excepciones a la política de devoluciones sin derivar a un agente
- No comprometerse con resoluciones que dependen de terceros (correos, proveedores)

Mantener siempre los límites profesionales y derivar casos complejos a agentes humanos cuando sea necesario.
"""


TOOL_DEFINITIONS = [
    {
        "name": "verificar_cliente",
        "description": "Verificar número de pedido y apellido para identificar al cliente y recuperar información básica",
        "parameters": {
            "type": "object",
            "properties": {
                "numero_pedido": {
                    "type": "string",
                    "description": "Número de pedido proporcionado por el cliente (formato: TM-XXXX)"
                },
                "apellido": {
                    "type": "string",
                    "description": "Apellido del cliente para verificación"
                },
                "email": {
                    "type": "string",
                    "description": "Email asociado al pedido (opcional, para verificación adicional)"
                }
            },
            "required": ["numero_pedido", "apellido"]
        }
    },
    {
        "name": "consultar_estado_pedido",
        "description": "Consultar el estado actual de un pedido y su información de entrega",
        "parameters": {
            "type": "object",
            "properties": {
                "numero_pedido": {
                    "type": "string",
                    "description": "Número de pedido verificado (formato: TM-XXXX)"
                }
            },
            "required": ["numero_pedido"]
        }
    },
    {
        "name": "registrar_reclamo",
        "description": "Registrar un reclamo por problema con la entrega y generar número de caso",
        "parameters": {
            "type": "object",
            "properties": {
                "numero_pedido": {
                    "type": "string",
                    "description": "Número de pedido verificado"
                },
                "tipo_reclamo": {
                    "type": "string",
                    "enum": ["no_recibido", "paquete_dañado", "producto_incorrecto", "faltante_en_paquete", "demora_excesiva", "otro"],
                    "description": "Tipo de problema reportado"
                },
                "descripcion": {
                    "type": "string",
                    "description": "Descripción detallada del problema reportado por el cliente"
                },
                "requiere_foto": {
                    "type": "boolean",
                    "description": "Si el reclamo requiere que el cliente envíe fotos del problema"
                }
            },
            "required": ["numero_pedido", "tipo_reclamo", "descripcion"]
        }
    },
    {
        "name": "iniciar_devolucion",
        "description": "Iniciar el proceso de devolución o cambio de un producto y generar número RMA",
        "parameters": {
            "type": "object",
            "properties": {
                "numero_pedido": {
                    "type": "string",
                    "description": "Número de pedido verificado"
                },
                "motivo_devolucion": {
                    "type": "string",
                    "enum": ["arrepentimiento", "producto_defectuoso", "producto_incorrecto", "no_cumple_expectativas", "doble_compra", "otro"],
                    "description": "Motivo de la devolución"
                },
                "productos": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de productos a devolver (nombres o SKUs)"
                },
                "tipo": {
                    "type": "string",
                    "enum": ["devolucion", "cambio"],
                    "description": "Si el cliente quiere devolver o cambiar el producto"
                }
            },
            "required": ["numero_pedido", "motivo_devolucion", "productos", "tipo"]
        }
    },
    {
        "name": "consultar_medios_de_pago",
        "description": "Consultar los medios de pago disponibles en TiendaMax",
        "parameters": {
            "type": "object",
            "properties": {
                "tipo_consulta": {
                    "type": "string",
                    "enum": ["todos", "tarjetas", "transferencia", "billeteras_digitales", "cuotas"],
                    "description": "Tipo de información de pago que se desea consultar"
                }
            },
            "required": ["tipo_consulta"]
        }
    },
    {
        "name": "derivar_a_agente",
        "description": "Derivar el caso a un agente humano cuando el problema es complejo o requiere autorización especial",
        "parameters": {
            "type": "object",
            "properties": {
                "numero_pedido": {
                    "type": "string",
                    "description": "Número de pedido relacionado al caso"
                },
                "motivo_derivacion": {
                    "type": "string",
                    "enum": ["caso_complejo", "excepcion_politica", "fraude_sospechoso", "cliente_insatisfecho", "reembolso_alto_valor", "problema_reincidente", "solicitud_legal"],
                    "description": "Motivo por el que se deriva a un agente humano"
                },
                "prioridad": {
                    "type": "string",
                    "enum": ["urgente", "alta", "normal", "baja"],
                    "description": "Prioridad del caso para el agente"
                },
                "notas": {
                    "type": "string",
                    "description": "Notas adicionales para el agente humano"
                }
            },
            "required": ["numero_pedido", "motivo_derivacion", "prioridad"]
        }
    }
]


# Tools implementation class
class EcommerceTools:
    def __init__(self):

        self.db = {
            "clientes": [
                {
                    "numero_pedido": "TM-1001",
                    "apellido": "García",
                    "email": "carlos.garcia@email.com",
                    "nombre_completo": "Carlos García",
                    "telefono": "11-4523-6789",
                    "direccion_entrega": "Av. Corrientes 1234, CABA"
                },
                {
                    "numero_pedido": "TM-1002",
                    "apellido": "Rodríguez",
                    "email": "ana.rodriguez@email.com",
                    "nombre_completo": "Ana Rodríguez",
                    "telefono": "11-5678-9012",
                    "direccion_entrega": "Belgrano 456, Rosario"
                },
                {
                    "numero_pedido": "TM-1003",
                    "apellido": "López",
                    "email": "martin.lopez@email.com",
                    "nombre_completo": "Martín López",
                    "telefono": "11-3456-7890",
                    "direccion_entrega": "San Martín 789, Córdoba"
                },
                {
                    "numero_pedido": "TM-1004",
                    "apellido": "Fernández",
                    "email": "laura.fernandez@email.com",
                    "nombre_completo": "Laura Fernández",
                    "telefono": "11-9012-3456",
                    "direccion_entrega": "Rivadavia 321, Mendoza"
                },
                {
                    "numero_pedido": "TM-2000",
                    "apellido": "Test",
                    "email": "test@test.com",
                    "nombre_completo": "Usuario Test",
                    "telefono": "11-0000-0000",
                    "direccion_entrega": "Calle Falsa 123, Springfield"
                }
            ],
            "pedidos": [
                {
                    "numero_pedido": "TM-1001",
                    "estado": "en_camino",
                    "fecha_compra": "2026-06-05",
                    "fecha_estimada_entrega": "2026-06-15",
                    "productos": ["Auriculares Bluetooth Sony WH-1000XM5", "Cable USB-C x2"],
                    "total": 89500,
                    "courier": "Andreani",
                    "numero_seguimiento": "AND-7823456",
                    "ultima_actualizacion": "2026-06-12T10:00:00",
                    "historial": [
                        {"fecha": "2026-06-05", "estado": "Pago confirmado"},
                        {"fecha": "2026-06-06", "estado": "Preparando pedido"},
                        {"fecha": "2026-06-09", "estado": "Despachado desde depósito"},
                        {"fecha": "2026-06-12", "estado": "En tránsito - Centro de distribución Córdoba"}
                    ]
                },
                {
                    "numero_pedido": "TM-1002",
                    "estado": "entregado",
                    "fecha_compra": "2026-05-28",
                    "fecha_estimada_entrega": "2026-06-02",
                    "fecha_entrega_real": "2026-06-03",
                    "productos": ["Licuadora Oster 600W", "Set de cuchillos Tramontina x6"],
                    "total": 42300,
                    "courier": "OCA",
                    "numero_seguimiento": "OCA-4512678",
                    "ultima_actualizacion": "2026-06-03T14:30:00"
                },
                {
                    "numero_pedido": "TM-1003",
                    "estado": "preparando",
                    "fecha_compra": "2026-06-11",
                    "fecha_estimada_entrega": "2026-06-18",
                    "productos": ["Zapatillas Nike Air Max 270 - Talle 42", "Medias deportivas x3 pares"],
                    "total": 67800,
                    "courier": "Correo Argentino",
                    "numero_seguimiento": None,
                    "ultima_actualizacion": "2026-06-11T16:00:00"
                },
                {
                    "numero_pedido": "TM-1004",
                    "estado": "demorado",
                    "fecha_compra": "2026-06-01",
                    "fecha_estimada_entrega": "2026-06-08",
                    "productos": ["Smart TV Samsung 55\" 4K", "Soporte de pared universal"],
                    "total": 385000,
                    "courier": "Andreani",
                    "numero_seguimiento": "AND-6634512",
                    "motivo_demora": "Condiciones climáticas adversas en zona de entrega",
                    "nueva_fecha_estimada": "2026-06-16",
                    "ultima_actualizacion": "2026-06-10T09:00:00"
                },
                {
                    "numero_pedido": "TM-2000",
                    "estado": "entregado",
                    "fecha_compra": "2026-06-01",
                    "fecha_estimada_entrega": "2026-06-05",
                    "fecha_entrega_real": "2026-06-05",
                    "productos": ["Producto de prueba"],
                    "total": 1000,
                    "courier": "Test Courier",
                    "numero_seguimiento": "TEST-0000",
                    "ultima_actualizacion": "2026-06-05T12:00:00"
                }
            ],
            "reclamos": [],
            "devoluciones": [],
            "derivaciones": []
        }
        self.reclamo_counter = 100
        self.devolucion_counter = 100

    def verificar_cliente(self, numero_pedido, apellido, email=None):
        """Verificar identidad del cliente por número de pedido y apellido"""
        if not numero_pedido.startswith("TM-"):
            numero_pedido = f"TM-{numero_pedido}"

        for cliente in self.db['clientes']:
            if (cliente['numero_pedido'] == numero_pedido and
                    cliente['apellido'].lower() == apellido.lower()):
                if email and cliente['email'].lower() != email.lower():
                    return {"error": "El email no coincide con el pedido. Por favor verificá tus datos."}

                return {
                    "verificado": True,
                    "numero_pedido": cliente['numero_pedido'],
                    "nombre": cliente['nombre_completo'],
                    "email_contacto": cliente['email'],
                    "telefono": cliente['telefono'],
                    "direccion_entrega": cliente['direccion_entrega']
                }

        return {"error": "No encontramos un pedido con ese número y apellido. Por favor verificá los datos ingresados."}

    def consultar_estado_pedido(self, numero_pedido):
        """Consultar el estado actual del pedido"""
        if not numero_pedido.startswith("TM-"):
            numero_pedido = f"TM-{numero_pedido}"

        for pedido in self.db['pedidos']:
            if pedido['numero_pedido'] == numero_pedido:
                estados_legibles = {
                    "preparando": "Preparando tu pedido",
                    "en_camino": "En camino",
                    "entregado": "Entregado",
                    "demorado": "Demorado",
                    "cancelado": "Cancelado"
                }

                resultado = {
                    "numero_pedido": numero_pedido,
                    "estado_actual": estados_legibles.get(pedido['estado'], pedido['estado']),
                    "fecha_compra": pedido['fecha_compra'],
                    "productos": pedido['productos'],
                    "total": f"${pedido['total']:,.0f}",
                    "courier": pedido['courier'],
                    "numero_seguimiento": pedido.get('numero_seguimiento', 'Aún no disponible'),
                    "ultima_actualizacion": pedido['ultima_actualizacion']
                }

                if pedido['estado'] == 'demorado':
                    resultado['motivo_demora'] = pedido.get('motivo_demora', 'En investigación')
                    resultado['nueva_fecha_estimada'] = pedido.get('nueva_fecha_estimada')
                elif pedido['estado'] == 'entregado':
                    resultado['fecha_entrega_real'] = pedido.get('fecha_entrega_real')
                else:
                    resultado['fecha_estimada_entrega'] = pedido.get('fecha_estimada_entrega')

                if 'historial' in pedido:
                    resultado['ultimo_evento'] = pedido['historial'][-1]

                return resultado

        return {"error": "Pedido no encontrado. Por favor verificá el número ingresado."}

    def registrar_reclamo(self, numero_pedido, tipo_reclamo, descripcion, requiere_foto=False):
        """Registrar un reclamo por problema con la entrega"""
        if not numero_pedido.startswith("TM-"):
            numero_pedido = f"TM-{numero_pedido}"

        # Verificar que el pedido existe
        pedido_existe = any(p['numero_pedido'] == numero_pedido for p in self.db['pedidos'])
        if not pedido_existe:
            return {"error": "Número de pedido no encontrado"}

        numero_caso = f"REC-{self.reclamo_counter:03d}"
        self.reclamo_counter += 1

        tiempos_resolucion = {
            "no_recibido": "5 a 7 días hábiles",
            "paquete_dañado": "3 a 5 días hábiles",
            "producto_incorrecto": "3 a 5 días hábiles",
            "faltante_en_paquete": "3 a 5 días hábiles",
            "demora_excesiva": "2 a 3 días hábiles",
            "otro": "5 a 7 días hábiles"
        }

        reclamo = {
            "numero_caso": numero_caso,
            "numero_pedido": numero_pedido,
            "tipo_reclamo": tipo_reclamo,
            "descripcion": descripcion,
            "requiere_foto": requiere_foto,
            "estado": "iniciado",
            "fecha_creacion": datetime.now().isoformat(),
            "ultima_actualizacion": datetime.now().isoformat(),
            "tiempo_resolucion_estimado": tiempos_resolucion.get(tipo_reclamo, "5 a 7 días hábiles")
        }

        self.db['reclamos'].append(reclamo)

        return {
            "estado": "reclamo_registrado",
            "numero_caso": numero_caso,
            "numero_pedido": numero_pedido,
            "tipo_reclamo": tipo_reclamo.replace("_", " ").title(),
            "tiempo_resolucion_estimado": reclamo['tiempo_resolucion_estimado'],
            "requiere_foto": requiere_foto,
            "proximos_pasos": "Un agente revisará tu reclamo y te contactaremos por email con novedades",
            "instrucciones_foto": "Por favor enviá las fotos a soporte@tiendamax.com indicando el número de caso" if requiere_foto else None
        }

    def iniciar_devolucion(self, numero_pedido, motivo_devolucion, productos, tipo):
        """Iniciar proceso de devolución o cambio"""
        if not numero_pedido.startswith("TM-"):
            numero_pedido = f"TM-{numero_pedido}"

        # Buscar el pedido y validar elegibilidad (30 días desde entrega)
        pedido = None
        for p in self.db['pedidos']:
            if p['numero_pedido'] == numero_pedido:
                pedido = p
                break

        if not pedido:
            return {"error": "Pedido no encontrado"}

        if pedido['estado'] != 'entregado':
            return {"error": "El pedido aún no fue entregado. No es posible iniciar una devolución en este momento."}

        fecha_entrega = datetime.strptime(pedido.get('fecha_entrega_real', pedido['fecha_estimada_entrega']), '%Y-%m-%d')
        dias_desde_entrega = (datetime.now() - fecha_entrega).days

        if dias_desde_entrega > 30:
            return {
                "error": f"El plazo de devolución de 30 días ya venció (han pasado {dias_desde_entrega} días desde la entrega). Este caso debe ser revisado por un agente.",
                "requiere_agente": True
            }

        numero_rma = f"RMA-{self.devolucion_counter:03d}"
        self.devolucion_counter += 1

        devolucion = {
            "numero_rma": numero_rma,
            "numero_pedido": numero_pedido,
            "tipo": tipo,
            "motivo": motivo_devolucion,
            "productos": productos,
            "estado": "iniciada",
            "fecha_creacion": datetime.now().isoformat(),
            "fecha_limite_envio": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        }

        self.db['devoluciones'].append(devolucion)

        return {
            "estado": "devolucion_iniciada",
            "numero_rma": numero_rma,
            "numero_pedido": numero_pedido,
            "tipo": "Devolución" if tipo == "devolucion" else "Cambio",
            "productos_a_devolver": productos,
            "motivo": motivo_devolucion.replace("_", " ").title(),
            "fecha_limite_envio": devolucion['fecha_limite_envio'],
            "instrucciones": [
                f"Anotá tu número RMA: {numero_rma}",
                "Empaquetá el producto en su caja original si es posible",
                f"Enviá el paquete antes del {devolucion['fecha_limite_envio']} a nuestro depósito",
                "Incluí una nota con el número RMA dentro del paquete",
                "Te enviaremos la etiqueta de envío por email"
            ],
            "reembolso_estimado": "El reembolso se procesará en 5 a 10 días hábiles luego de recibir el producto" if tipo == "devolucion" else None
        }

    def consultar_medios_de_pago(self, tipo_consulta="todos"):
        """Consultar medios de pago disponibles"""
        medios = {
            "tarjetas": {
                "credito": ["Visa", "Mastercard", "American Express", "Naranja X", "Cabal"],
                "debito": ["Visa Débito", "Mastercard Débito", "Maestro"],
                "cuotas_sin_interes": "Hasta 12 cuotas sin interés con bancos seleccionados"
            },
            "transferencia": {
                "metodos": ["Transferencia bancaria", "CBU/CVU"],
                "descuento": "5% de descuento pagando con transferencia"
            },
            "billeteras_digitales": {
                "disponibles": ["Mercado Pago", "Ualá", "MODO", "Naranja X"],
                "cuotas": "Hasta 6 cuotas con Mercado Pago"
            },
            "otros": ["Pago Fácil", "Rapipago"]
        }

        if tipo_consulta == "tarjetas":
            return {"medios_de_pago": {"tarjetas": medios["tarjetas"]}}
        elif tipo_consulta == "transferencia":
            return {"medios_de_pago": {"transferencia": medios["transferencia"]}}
        elif tipo_consulta == "billeteras_digitales":
            return {"medios_de_pago": {"billeteras_digitales": medios["billeteras_digitales"]}}
        elif tipo_consulta == "cuotas":
            return {
                "cuotas": {
                    "credito": medios["tarjetas"]["cuotas_sin_interes"],
                    "mercado_pago": medios["billeteras_digitales"]["cuotas"]
                }
            }
        else:
            return {"medios_de_pago": medios}

    def derivar_a_agente(self, numero_pedido, motivo_derivacion, prioridad, notas=None):
        """Derivar caso a agente humano"""
        if not numero_pedido.startswith("TM-"):
            numero_pedido = f"TM-{numero_pedido}"

        tiempos_espera = {
            "urgente": "menos de 1 hora",
            "alta": "2 a 4 horas",
            "normal": "24 a 48 horas hábiles",
            "baja": "48 a 72 horas hábiles"
        }

        derivacion = {
            "numero_pedido": numero_pedido,
            "motivo": motivo_derivacion,
            "prioridad": prioridad,
            "notas": notas,
            "fecha_derivacion": datetime.now().isoformat(),
            "estado": "pendiente_de_agente",
            "tiempo_espera_estimado": tiempos_espera[prioridad]
        }

        self.db['derivaciones'].append(derivacion)

        return {
            "estado": "derivado_a_agente",
            "numero_pedido": numero_pedido,
            "prioridad": prioridad.title(),
            "motivo": motivo_derivacion.replace("_", " ").title(),
            "tiempo_estimado_contacto": tiempos_espera[prioridad],
            "mensaje_cliente": f"Tu caso fue derivado a uno de nuestros agentes. Te contactaremos en {tiempos_espera[prioridad]} al email y teléfono registrados.",
            "notificacion_agente": "El agente fue notificado por el sistema interno"
        }


# Create instance of tools class
TOOLS = EcommerceTools()
