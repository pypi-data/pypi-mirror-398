# 🤖 Agent Template - Plantilla de Agentes IA con Arquitectura Limpia

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121.1+-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0.3+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![LangChain](https://img.shields.io/badge/LangChain-1.0.5+-brown.svg)](https://docs.langchain.com/oss/python/langchain/overview)
[![A2A Protocol](https://img.shields.io/badge/A2A-0.3.11+-purple.svg)](https://a2a-protocol.org/)
[![Kafka](https://img.shields.io/badge/Kafka-aiokafka_0.12.0+-red.svg)](https://kafka.apache.org/)

## 📋 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Características Principales](#-características-principales)
- [Arquitectura del Proyecto](#-arquitectura-del-proyecto)
- [Protocolo A2A Implementado](#-protocolo-a2a-implementado)
- [Estructura de Directorios](#-estructura-de-directorios)
- [Configuración e Instalación](#-configuración-e-instalación)
- [Uso del Sistema](#-uso-del-sistema)
- [Flujos de Comunicación](#-flujos-de-comunicación)
- [Endpoints Disponibles](#-endpoints-disponibles)
- [Ejemplos de Uso](#-ejemplos-de-uso)
- [Desarrollo y Extensión](#-desarrollo-y-extensión)

---

## 🎯 Descripción General

Este proyecto es una **plantilla modular y extensible** para crear agentes de Inteligencia Artificial utilizando **Arquitectura Limpia (Clean Architecture)**. Integra tecnologías de vanguardia como **LangGraph**, **Model Context Protocol (MCP)**, y el **Protocolo A2A de Google** para la comunicación entre agentes.

### ¿Qué hace este template?

- ✅ Crea agentes de IA conversacionales usando LangGraph
- ✅ Se conecta a LLMs externos (OpenAI, Azure, etc.) mediante configuración
- ✅ Integra herramientas externas vía Model Context Protocol (MCP)
- ✅ Implementa el protocolo A2A para comunicación inter-agentes
- ✅ Soporta comunicación asíncrona mediante Kafka (opcional)
- ✅ Mantiene separación de responsabilidades con Arquitectura Limpia
- ✅ Soporta tanto comunicación tradicional (REST) como A2A

---

## ✨ Características Principales

### 🏗️ Arquitectura Limpia
- **Separación en capas**: Domain, Application, Infrastructure
- **Inyección de dependencias**: Usando `dependency-injector`
- **Desacoplamiento**: Interfaces (Ports) y adaptadores claramente definidos
- **Testeable y mantenible**: Fácil de extender y modificar

### 🔗 Integración LangGraph
- Motor de agentes basado en **ReAct** (Reasoning + Acting)
- Soporte para múltiples herramientas
- Prompts configurables vía variables de entorno
- Ejecución asíncrona nativa

### 🌐 Protocolo A2A (Agent-to-Agent)
- **Descubrimiento de agentes**: Endpoint `/.well-known/agent.json`
- **Agent Card**: Publicación de capacidades y skills
- **Comunicación síncrona**: Endpoint `/a2a/tasks`
- **Comunicación streaming**: Endpoint `/a2a/tasks/stream`
- **Cliente A2A integrado**: Para comunicarse con otros agentes

### 🔌 Model Context Protocol (MCP)
- Conexión a servidores MCP externos
- Conversión automática de herramientas MCP a LangChain
- Configuración flexible de endpoints

### 🔄 Sistema Híbrido
- **Endpoints tradicionales**: Para clientes que no usan A2A
- **Endpoints A2A**: Para comunicación inter-agentes
- **Endpoint de colaboración**: Para iniciar colaboraciones administrativamente

### 📨 Integración Kafka (Opcional)
- **Consumer asíncrono**: Recibe mensajes de tópicos Kafka
- **Producer integrado**: Envía respuestas a tópicos de salida
- **Configuración flexible**: Se activa/desactiva mediante variable de entorno
- **Arquitectura event-driven**: Procesamiento asíncrono de mensajes
- **Retry mechanism**: Reintentos automáticos en caso de fallo
- **Integración transparente**: Se comunica directamente con los casos de uso

---

## 🏛️ Arquitectura del Proyecto

El proyecto sigue los principios de **Clean Architecture** dividido en 4 capas principales:

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTRY POINTS (API)                       │
│  - FastAPI endpoints (REST tradicional)                     │
│  - A2A Server (Servidor del protocolo A2A)                  │
│  - Agent Card Builder (Publicación de capabilities)         │
│  - Kafka Consumer (Mensajes asíncronos) [OPCIONAL]          │
└─────────────────────────────────────────────────────────────┘
                            ↓↑
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                          │
│  - Use Cases (Lógica de negocio)                            │
│  - Settings & Configuration                                  │
│  - Dependency Injection Container                            │
└─────────────────────────────────────────────────────────────┘
                            ↓↑
┌─────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                             │
│  - Entities (Skills, Agent Card)                            │
│  - Ports/Gateways (Interfaces abstractas)                   │
│  - Business Rules                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓↑
┌─────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                        │
│  - LangGraph Agent Adapter                                   │
│  - LLM Gateway (OpenAI, Azure, etc.)                        │
│  - MCP Client (Model Context Protocol)                      │
│  - A2A Client (Comunicación con otros agentes)              │
│  - Kafka Producer (Respuestas asíncronas) [OPCIONAL]        │
└─────────────────────────────────────────────────────────────┘
```

### Principios Aplicados

1. **Inversión de Dependencias**: Las capas externas dependen de las internas
2. **Separación de Responsabilidades**: Cada capa tiene un propósito específico
3. **Ports & Adapters**: Interfaces en el dominio, implementaciones en infraestructura
4. **Inyección de Dependencias**: Configuración centralizada en `Container`

---

## 🔌 Protocolo A2A Implementado

El **Protocolo A2A (Agent-to-Agent)** de Google permite que agentes de IA se comuniquen entre sí de forma estandarizada.

### Componentes del Protocolo A2A en este Template

#### 1️⃣ **Agent Card** (`/.well-known/agent.json`)

El **Agent Card** es el mecanismo de descubrimiento. Publica:

```json
{
  "name": "Mi Agente",
  "description": "Descripción de las capacidades del agente",
  "url": "http://localhost:8001",
  "version": "1.0.0",
  "protocol_version": "0.0.1",
  "capabilities": {
    "streaming": true,
    "task_management": true
  },
  "skills": [
    {
      "name": "analyze_text",
      "description": "Crea componentes de UI basados en análisis de texto",
      "input_schema": { /* ... */ },
      "output_schema": { /* ... */ }
    }
  ]
}
```

**Ubicación**: `infraestructure/entry_points/a2a/agent_card.py`

**Características**:
- Se construye dinámicamente desde `domain/model/skills.py`
- Incluye metadatos del agente
- Lista todas las habilidades disponibles

#### 2️⃣ **A2A Server** (Recibir mensajes de otros agentes)

El servidor A2A expone dos endpoints principales:

**Endpoint Síncrono** (`POST /a2a/tasks`):
```python
# Recibe mensajes en formato A2A
{
  "message": {
    "role": "user",
    "parts": [{"kind": "text", "text": "Hola agente"}]
  }
}

# Responde en formato A2A
{
  "message": {
    "role": "assistant",
    "parts": [{"kind": "text", "text": "Respuesta del agente"}]
  }
}
```

**Endpoint Streaming** (`POST /a2a/tasks/stream`):
- Recibe el mismo formato
- Responde con eventos SSE (Server-Sent Events)
- Eventos: `start`, `content`, `end`

**Ubicación**: `infraestructure/entry_points/a2a/a2a_server.py`

**Flujo Interno**:
1. Recibe mensaje en formato A2A
2. Extrae el contenido del mensaje
3. Delega a `AgentInteractionUseCase`
4. El Use Case usa `LangGraphAgentAdapter`
5. Formatea la respuesta en formato A2A
6. Retorna al agente solicitante

#### 3️⃣ **A2A Client** (Enviar mensajes a otros agentes)

El cliente A2A permite comunicarse con agentes externos:

**Ubicación**: `infraestructure/driven_adapters/a2a/a2a_client.py`

**Funcionalidades**:

```python
# 1. Descubrir capacidades de un agente
agent_card = await a2a_client.discover_agent("http://otro-agente:8002")

# 2. Enviar mensaje síncrono
response = await a2a_client.send_to_agent(
    "http://otro-agente:8002", 
    "Analiza este texto"
)

# 3. Recibir respuesta streaming
async for chunk in a2a_client.stream_from_agent(
    "http://otro-agente:8002", 
    "Genera un reporte"
):
    print(chunk)
```

**Wrapper de la Librería A2A**:
- Utiliza `a2a-sdk[http-server]` (librería oficial de Google)
- Wrapper en `infraestructure/entry_points/a2a/a2a_client_wrapper.py`
- Mantiene conexiones reutilizables (pool de clientes)

#### 4️⃣ **Skills System**

Las **Skills** definen las capacidades del agente:

**Ubicación**: `domain/model/skills.py`

```python
@dataclass
class Skill:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

def get_available_skills() -> List[Skill]:
    return [
        Skill(
            name="analyze_text",
            description="Crea componentes de UI con Angular",
            input_schema={...},
            output_schema={...}
        )
    ]
```

**Propósito**:
- Define qué puede hacer el agente
- Se publica en el Agent Card
- Permite a otros agentes saber cómo colaborar

---

## 📨 Integración con Kafka (Opcional)

La integración con **Apache Kafka** permite que el agente procese mensajes de forma **asíncrona** y **event-driven**, complementando los endpoints síncronos REST y A2A.

### ¿Cuándo usar Kafka?

✅ **Casos de uso ideales**:
- Procesamiento asíncrono de gran volumen de mensajes
- Integración con sistemas event-driven
- Comunicación desacoplada entre microservicios
- Necesidad de retry automático y tolerancia a fallos
- Procesamiento batch o en cola

❌ **Cuándo NO usar Kafka**:
- Comunicación síncrona en tiempo real (usar endpoints REST/A2A)
- Respuestas inmediatas requeridas
- Bajo volumen de mensajes
- Desarrollo local simple

### Arquitectura Kafka en el Template

```
┌─────────────────────────────────────────────────────────────┐
│                  KAFKA CLUSTER                               │
│                                                              │
│  Topic: agent-input-topic                                    │
│  │                                                           │
│  └─→ [Mensaje 1] [Mensaje 2] [Mensaje 3] ...               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│        KAFKA CONSUMER ADAPTER (Entry Point)                  │
│  - Consume mensajes del topic de entrada                     │
│  - Deserializa y valida mensajes                            │
│  - Delega a AgentMessageHandler                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│        AGENT MESSAGE HANDLER                                 │
│  - Extrae el mensaje del evento Kafka                       │
│  - Invoca AgentInteractionUseCase                           │
│  - Obtiene respuesta del agente                             │
│  - Delega al Producer para enviar respuesta                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│     AGENT INTERACTION USE CASE (Domain)                      │
│  - Lógica de negocio independiente del canal                │
│  - Procesa mensaje con LangGraph Agent                      │
│  - Retorna respuesta                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│        KAFKA PRODUCER ADAPTER (Infrastructure)               │
│  - Serializa respuesta                                       │
│  - Envía al topic de salida                                 │
│  - Maneja reintentos                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  KAFKA CLUSTER                               │
│                                                              │
│  Topic: agent-output-topic                                   │
│  │                                                           │
│  └─→ [Respuesta 1] [Respuesta 2] [Respuesta 3] ...         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Componentes de la Integración

#### 1️⃣ **Kafka Settings** (`application/settings/kafka_settings.py`)

Define toda la configuración de Kafka con validación:

```python
class KafkaProducerSettings(BaseModel):
    bootstrap_servers: str
    output_topic: str
    acks: str = "all"
    retries: int = 3
    # ...

class KafkaConsumerSettings(BaseModel):
    bootstrap_servers: str
    input_topic: str
    group_id: str
    auto_offset_reset: str = "earliest"
    # ...
```

#### 2️⃣ **Kafka Consumer Adapter** (`infrastructure/entry_points/kafka/adapters/`)

Consume mensajes del topic de entrada:

**Características**:
- Basado en `aiokafka` (asíncrono)
- Procesamiento concurrente de mensajes
- Manejo de errores con reintentos
- Commit automático o manual de offsets
- Deserialización automática JSON

**Ubicación**: `infrastructure/entry_points/kafka/adapters/kafka_consumer_adapter.py`

#### 3️⃣ **Agent Message Handler** (`infrastructure/entry_points/kafka/handlers/`)

Procesa mensajes específicos del agente:

**Responsabilidades**:
- Extrae el mensaje del evento Kafka
- Invoca `AgentInteractionUseCase` (mismo que REST y A2A)
- Obtiene la respuesta del agente
- Envía respuesta al Producer

**Ubicación**: `infrastructure/entry_points/kafka/handlers/agent_message_handler.py`

```python
class AgentMessageHandler(BaseHandler):
    async def handle(self, message: dict) -> None:
        # Procesar mensaje
        user_message = message.get("message", "")
        
        # Invocar caso de uso (transparente al canal)
        response = await self.agent_interaction_use_case.interact_with_agent(user_message)
        
        # Enviar respuesta al topic de salida
        await self.kafka_producer.send_message({
            "response": response,
            "original_message": message
        })
```

#### 4️⃣ **Kafka Producer Adapter** (`infrastructure/driven_adapters/kafka_producer_adapter/`)

Envía respuestas al topic de salida:

**Características**:
- Serialización JSON automática
- Compresión de mensajes (gzip)
- Reintentos configurables
- ACKs para garantizar entrega

**Ubicación**: `infrastructure/driven_adapters/kafka_producer_adapter/adapter/kafka_producer_adapter.py`

### Configuración de Kafka

#### Variables de Entorno

En el archivo `.env`:

```env
# Habilitar Kafka
MOUNT_KAFKA=true

# Conexión
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SECURITY_PROTOCOL=SASL_SSL
KAFKA_SASL_MECHANISM=SCRAM-SHA-512
KAFKA_SASL_USERNAME=mi-usuario
KAFKA_SASL_PASSWORD=mi-password

# Consumer
KAFKA_INPUT_TOPIC=agent-requests
KAFKA_GROUP_ID=my-agent-group
KAFKA_AUTO_OFFSET_RESET=earliest
KAFKA_ENABLE_AUTO_COMMIT=true
KAFKA_MAX_CONCURRENT_MESSAGES=10
KAFKA_MAX_RETRY_MESSAGES=3

# Producer
KAFKA_OUTPUT_TOPIC=agent-responses
KAFKA_ACKS=all
KAFKA_RETRIES=3
KAFKA_COMPRESSION_TYPE=gzip
```

#### Inicialización en el Container

El `Container` carga Kafka **solo si** `MOUNT_KAFKA=true`:

```python
# application/settings/container.py

def create_kafka_producer_if_enabled(config):
    if config.mount_kafka:
        return KafkaProducerAdapter(config=config.kafka_producer)
    return None

def create_kafka_consumer_if_enabled(config, use_case, producer):
    if not config.mount_kafka:
        return None
    
    handler = AgentMessageHandler(
        agent_interaction_use_case=use_case,
        kafka_producer=producer
    )
    
    return KafkaConsumerAdapter(
        kafka_config=config.kafka_consumer.model_dump(),
        message_handler=handler
    )
```

#### Inicialización en `main.py`

El consumer se inicia solo si está habilitado:

```python
@asynccontextmanager
async def lifespan(application: FastAPI):
    container = Container()
    await container.init_resources()
    
    # Cargar Kafka solo si está habilitado
    kafka_task = None
    if container.config.mount_kafka():
        logger.info("Kafka habilitado. Iniciando consumer...")
        kafka_consumer = await container.kafka_consumer()
        kafka_task = asyncio.create_task(kafka_consumer.start())
    else:
        logger.info("Kafka deshabilitado")
    
    yield
    
    # Shutdown: detener consumer
    if kafka_task:
        await kafka_consumer.stop()
        kafka_task.cancel()
```

### Flujo de Procesamiento Kafka

```
1. Mensaje llega al topic de entrada
   ↓
2. KafkaConsumerAdapter lo recibe
   ↓
3. Deserializa el mensaje JSON
   ↓
4. Invoca AgentMessageHandler
   ↓
5. Handler extrae contenido del mensaje
   ↓
6. Invoca AgentInteractionUseCase (mismo que REST/A2A)
   ↓
7. LangGraphAgentAdapter procesa con LLM + Tools
   ↓
8. Respuesta retorna al Handler
   ↓
9. Handler invoca KafkaProducerAdapter
   ↓
10. Producer serializa y envía al topic de salida
    ↓
11. Mensaje de respuesta disponible en Kafka
```

### Formato de Mensajes

#### Mensaje de Entrada (Input Topic)

```json
{
  "message": "Crea un componente de login en Angular",
  "user_id": "user-123",
  "session_id": "session-456",
  "timestamp": "2025-11-11T10:30:00Z"
}
```

#### Mensaje de Salida (Output Topic)

```json
{
  "response": {
    "messages": [
      {
        "role": "assistant",
        "content": "Aquí está tu componente de login..."
      }
    ]
  },
  "original_message": {
    "message": "Crea un componente de login en Angular",
    "user_id": "user-123",
    "session_id": "session-456"
  },
  "processed_at": "2025-11-11T10:30:05Z"
}
```

### Ventajas de la Integración Kafka

1. **Desacoplamiento**: El agente no necesita saber quién envía los mensajes
2. **Escalabilidad**: Múltiples instancias del agente pueden consumir del mismo topic
3. **Resiliencia**: Mensajes persisten en Kafka hasta ser procesados
4. **Reintentos**: Manejo automático de fallos con reintentos
5. **Arquitectura Limpia**: Se integra transparentemente en la capa de infraestructura
6. **Opcional**: No afecta el funcionamiento REST/A2A si está deshabilitado

### Librerías Utilizadas

- **`aiokafka>=0.12.0`**: Cliente asíncrono de Kafka para Python
  - Alto rendimiento con asyncio
  - Compatible con Kafka 0.9+
  - Soporte para SASL, SSL, y múltiples protocolos de seguridad

### Monitoreo y Logs

El sistema incluye logging estructurado para Kafka:

```python
# Logs al iniciar
INFO: Kafka habilitado. Iniciando consumer...
INFO: Conectando a Kafka: localhost:9092
INFO: Suscrito al topic: agent-requests

# Logs al procesar mensajes
INFO: Mensaje recibido del topic agent-requests
INFO: Procesando mensaje para user-123
INFO: Respuesta enviada al topic agent-responses

# Logs de errores
ERROR: Error procesando mensaje, reintento 1/3
WARNING: Mensaje fallido después de 3 reintentos
```

---

## 📁 Estructura de Directorios

```
agent-template/
│
├── main.py                          # 🚀 Punto de entrada de la aplicación
│
├── application/                     # 📦 Capa de Aplicación
│   └── settings/
│       ├── .env
│       ├── __init__.py
│       ├── base_settings.py         # Configuración base con Pydantic
│       ├── settings.py              # Variables de entorno
│       └── container.py             # 💉 Contenedor de Inyección de Dependencias
│
├── domain/                          # 🎯 Capa de Dominio (Reglas de Negocio)
│   ├── model/
│   │   ├── entities.py              # Entidades del dominio
│   │   ├── skills.py                # ⚡ Definición de Skills del agente
│   │   └── gateways/
│   │       └── agent/
│   │           ├── agent_adapter.py          # 🔌 Port para agentes
│   │           └── collaborate_adapter.py    # 🔌 Port para colaboración A2A
│   │
│   └── usecase/
│       ├── agent_interaction_usecase.py      # 💬 Caso de uso: Interactuar con el agente
│       └── agent_collaboration_usecase.py    # 🤝 Caso de uso: Colaborar con otros agentes
│
├── infraestructure/                 # 🔧 Capa de Infraestructura
│   │
│   ├── driven_adapters/             # Adaptadores de Salida
│   │   ├── langgraph_agent/
│   │   │   └── langgraph_agent_adapter.py    # 🤖 Implementación con LangGraph
│   │   │
│   │   ├── llm/
│   │   │   └── llm_gateway.py               # 🧠 Gateway a LLMs externos
│   │   │
│   │   ├── tools/
│   │   │   └── mcp_client.py                # 🔌 Cliente MCP (Model Context Protocol)
│   │   │
│   │   ├── a2a/
│   │   │   └── a2a_client.py                # 📡 Cliente A2A (enviar a otros agentes)
│   │   │
│   │   ├── kafka_producer_adapter/          # 📨 Productor Kafka [OPCIONAL]
│   │   │   └── adapter/
│   │   │       └── kafka_producer_adapter.py
│   │   │
│   │   └── logging/
│   │       └── logger_config.py             # 📋 Configuración de logging
│   │
│   └── entry_points/                # Adaptadores de Entrada
│       ├── api/
│       │   └── dto/
│       │       ├── chat_request.py          # DTO para peticiones
│       │       └── chat_response.py         # DTO para respuestas
│       │
│       ├── a2a/
│       │   ├── a2a_server.py                # 🌐 Servidor A2A (recibir de otros agentes)
│       │   ├── a2a_client_wrapper.py        # 🎁 Wrapper del SDK A2A oficial
│       │   └── agent_card.py                # 🎴 Constructor del Agent Card
│       │
│       └── kafka/                           # 📨 Integración Kafka [OPCIONAL]
│           ├── kafka_app.py                 # Aplicación principal de Kafka
│           ├── adapters/
│           │   └── kafka_consumer_adapter.py  # Consumer de Kafka
│           └── handlers/
│               ├── base_handler.py           # Handler base abstracto
│               └── agent_message_handler.py  # Handler para mensajes del agente
│       ├── api/
│       │   └── dto/
│       │       ├── chat_request.py          # DTO para peticiones
│       │       └── chat_response.py         # DTO para respuestas
│       │
│       └── a2a/
│           ├── a2a_server.py                # 🌐 Servidor A2A (recibir de otros agentes)
│           ├── a2a_client_wrapper.py        # 🎁 Wrapper del SDK A2A oficial
│           └── agent_card.py                # 🎴 Constructor del Agent Card
│
├── pyproject.toml                   # 📦 Dependencias del proyecto
├── uv.lock                          # 🔒 Lock de dependencias
└── README.md                        # 📖 Este archivo
```

---

## ⚙️ Configuración e Instalación

### Prerrequisitos

- **Python 3.13+**
- **uv** (gestor de paquetes) o **pip**
- **Git** (para clonar el repositorio)

### 1️⃣ Clonar el Repositorio

#### Pendiente 

```bash
git clone <url-del-repositorio>
cd agent-template
```

### 2️⃣ Crear y Activar el Entorno Virtual

Un entorno virtual aísla las dependencias de este proyecto del resto de tu sistema.

#### En Windows (cmd.exe o PowerShell):

```bash
# Crear el entorno virtual
python -m venv venv

# Activar el entorno virtual
venv\Scripts\activate
```

#### En Linux/macOS (bash/zsh):

```bash
# Crear el entorno virtual
python3 -m venv venv

# Activar el entorno virtual
source venv/bin/activate
```

**Verificación**: Deberías ver `(venv)` al inicio de tu línea de comandos.

### 3️⃣ Instalar Dependencias

```bash
# Con uv (recomendado - más rápido)
uv sync

# O con pip
pip install -e .
```

### 4️⃣ Configurar Variables de Entorno

Crear un archivo `.env` en la carpeta `./application/settings/` con el siguiente contenido:

```env
# ============================================
# 🔑 Configuración del LLM
# ============================================
API_KEY=tu-api-key-aqui
API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4o
TEMPERATURE=0.7

# ============================================
# 🤖 Instrucciones del Agente
# ============================================
AGENT_INSTRUCTIONS=Eres un asistente útil que ayuda a crear componentes de UI con Angular.

# ============================================
# 🔌 Configuración MCP
# ============================================
MCP_SERVER_ENDPOINT=http://localhost:3000
MCP_SERVER_NAME=mi-servidor-mcp

# ============================================
# 🌐 Configuración A2A
# ============================================
AGENT_NAME=Mi Agente UI
AGENT_DESCRIPTION=Agente especializado en crear componentes de UI con Angular
AGENT_BASE_URL=http://localhost:8001

# ============================================
# 📨 Configuración Kafka (OPCIONAL)
# ============================================
# Habilitar/deshabilitar integración con Kafka
MOUNT_KAFKA=false

# Si MOUNT_KAFKA=true, configurar las siguientes variables:

# Servidores de Kafka (separados por comas para múltiples brokers)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Protocolo de seguridad (PLAINTEXT, SASL_SSL, SSL)
KAFKA_SECURITY_PROTOCOL=SASL_SSL

# Mecanismo SASL (SCRAM-SHA-512, PLAIN, etc.)
KAFKA_SASL_MECHANISM=SCRAM-SHA-512

# Credenciales Kafka
KAFKA_SASL_USERNAME=tu-kafka-username
KAFKA_SASL_PASSWORD=tu-kafka-password

# Configuración del Consumer
KAFKA_INPUT_TOPIC=agent-input-topic
KAFKA_GROUP_ID=agent-consumer-group
KAFKA_AUTO_OFFSET_RESET=earliest
KAFKA_ENABLE_AUTO_COMMIT=true
KAFKA_MAX_CONCURRENT_MESSAGES=10
KAFKA_MAX_RETRY_MESSAGES=3

# Configuración del Producer
KAFKA_OUTPUT_TOPIC=agent-output-topic
KAFKA_ACKS=all
KAFKA_RETRIES=3
KAFKA_COMPRESSION_TYPE=gzip
```

> **Nota**: Para un ambiente local sin Kafka, deja `MOUNT_KAFKA=false`. El agente funcionará normalmente con endpoints REST y A2A.

### 5️⃣ Ejecutar el Agente

```bash
# Asegúrate de que el entorno virtual está activado
python main.py
```

El servidor se iniciará en `http://localhost:8001`

### 6️⃣ Desactivar el Entorno Virtual (Opcional)

Cuando termines de trabajar:

```bash
deactivate
```

---
## 🎮 Uso del Sistema

### Endpoints Disponibles

#### 1️⃣ **Endpoint Tradicional (Sin A2A)**

**POST** `/chat`

Endpoint para clientes que **no** usan el protocolo A2A.

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Crea un componente de login"}'
```

**Respuesta**:
```json
{
  "messages": [
    {
      "content": "Aquí está tu componente de login en Angular...",
      "role": "assistant"
    }
  ]
}
```

#### 2️⃣ **Endpoint de Colaboración Administrativa**

**POST** `/collaborate`

Para que un administrador inicie una colaboración con otro agente.

```bash
curl -X POST "http://localhost:8001/collaborate?agent_url=http://otro-agente:8002&task=Analiza este código"
```

**Flujo**:
1. Descubre el agente externo (`/.well-known/agent.json`)
2. Envía la tarea al agente externo (vía A2A)
3. Recibe la respuesta
4. La procesa con tu agente interno
5. Retorna resultado formateado

#### 3️⃣ **Agent Card (Descubrimiento A2A)**

**GET** `/.well-known/agent.json`

Endpoint de descubrimiento según protocolo A2A.

```bash
curl http://localhost:8001/.well-known/agent.json
```

**Respuesta**:
```json
{
  "name": "Mi Agente UI",
  "description": "Agente especializado en crear componentes de UI",
  "url": "http://localhost:8001",
  "version": "1.0.0",
  "protocol_version": "0.0.1",
  "capabilities": {
    "streaming": true,
    "task_management": true
  },
  "skills": [...]
}
```

#### 4️⃣ **Recibir Tarea A2A (Síncrono)**

**POST** `/a2a/tasks`

Endpoint para que **otros agentes** envíen tareas a este agente.

```bash
curl -X POST http://localhost:8001/a2a/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "Crea un botón"}]
    }
  }'
```

#### 5️⃣ **Recibir Tarea A2A (Streaming)**

**POST** `/a2a/tasks/stream`

Mismo formato pero con respuesta en streaming (SSE).

---

## 🔄 Flujos de Comunicación

### Flujo 1: Cliente Tradicional → Este Agente

```
Cliente REST
    │
    │ POST /chat {"message": "Hola"}
    ▼
FastAPI Endpoint
    │
    ▼
AgentInteractionUseCase
    │
    ▼
LangGraphAgentAdapter
    │
    ▼
LLM (OpenAI/Azure) + MCP Tools
    │
    ▼
Respuesta al Cliente
```

### Flujo 2: Este Agente → Otro Agente (A2A)

```
Administrador
    │
    │ POST /collaborate?agent_url=http://otro-agente:8002
    ▼
AgentCollaborationUseCase
    │
    ├─→ A2AClient.discover_agent()
    │   └─→ GET http://otro-agente:8002/.well-known/agent.json
    │
    ├─→ A2AClient.send_to_agent()
    │   └─→ POST http://otro-agente:8002/a2a/tasks
    │
    ▼
Respuesta del Agente Externo
    │
    ▼
AgentInteractionUseCase (procesa respuesta)
    │
    ▼
Resultado Formateado
```

### Flujo 3: Otro Agente → Este Agente (A2A)

```
Agente Externo
    │
    │ POST /a2a/tasks (formato A2A)
    ▼
A2AServer.receive_message()
    │
    ├─→ Extrae contenido del mensaje A2A
    │
    ▼
AgentInteractionUseCase
    │
    ▼
LangGraphAgentAdapter
    │
    ▼
LLM + Tools
    │
    ▼
A2AServer.format_response()
    │
    └─→ Formatea en protocolo A2A
    │
    ▼
Respuesta al Agente Externo (formato A2A)
```

### Flujo 4: Comunicación Multi-Agente

```
Agente A (Este Template)
    │
    │ Necesita información de Agente B
    ▼
AgentCollaborationUseCase
    │
    ├─→ Descubre Agente B
    │   GET http://agente-b:8002/.well-known/agent.json
    │
    ├─→ Envía tarea a Agente B
    │   POST http://agente-b:8002/a2a/tasks
    │
    ▼
Agente B procesa
    │
    ▼
Agente B responde (formato A2A)
    │
    ▼
Agente A recibe y procesa
    │
    ▼
Agente A puede consultar Agente C si es necesario
    │
    ▼
Resultado final
```

### Flujo 5: Comunicación Asíncrona vía Kafka (Opcional)

```
Sistema Externo/Orquestador
    │
    │ Produce mensaje en Kafka
    ▼
Kafka Topic: agent-requests
    │
    │ {"message": "Tarea asíncrona", "user_id": "123"}
    ▼
KafkaConsumerAdapter
    │
    ├─→ Consume mensaje
    ├─→ Deserializa JSON
    │
    ▼
AgentMessageHandler
    │
    ├─→ Extrae contenido
    │
    ▼
AgentInteractionUseCase (MISMO que REST/A2A)
    │
    ├─→ Procesa con LangGraph
    │
    ▼
LangGraphAgentAdapter + LLM
    │
    ▼
Respuesta generada
    │
    ▼
KafkaProducerAdapter
    │
    ├─→ Serializa respuesta
    ├─→ Envía a topic de salida
    │
    ▼
Kafka Topic: agent-responses
    │
    │ {"response": {...}, "original_message": {...}}
    ▼
Sistema Externo consume respuesta
```

**Características del Flujo Kafka**:
- ✅ **Asíncrono**: No bloquea el sistema que envía el mensaje
- ✅ **Desacoplado**: Productor y consumidor no se conocen
- ✅ **Resiliente**: Mensajes persisten hasta ser procesados
- ✅ **Escalable**: Múltiples consumidores pueden procesar en paralelo
- ✅ **Transparente**: Usa el mismo caso de uso que REST y A2A

---

## 🔧 Desarrollo y Extensión

### Añadir Nuevas Skills

1. **Editar** `domain/model/skills.py`:

```python
def get_available_skills() -> List[Skill]:
    return [
        # ...skills existentes...
        Skill(
            name="nueva_skill",
            description="Descripción de la nueva habilidad",
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                },
                "required": ["param1"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            }
        )
    ]
```

2. Las skills se publican automáticamente en el Agent Card

### Añadir Nuevos Endpoints

Editar `main.py`:

```python
@app.post("/mi-nuevo-endpoint")
@inject
async def mi_nuevo_endpoint(
    parametro: str,
    use_case: AgentInteractionUseCase = Depends(Provide[Container.agent_interaction_use_case])
):
    resultado = await use_case.interact_with_agent(parametro)
    return {"resultado": resultado}
```

### Cambiar el LLM Provider

Editar `infraestructure/driven_adapters/llm/llm_gateway.py` para soportar otros providers (Anthropic, Gemini, etc.).

### Conectar Diferentes Servidores MCP

Modificar las variables de entorno:

```env
MCP_SERVER_ENDPOINT=http://nuevo-servidor-mcp:3000
MCP_SERVER_NAME=nuevo-servidor
```

### Comunicarse con Otros Agentes

#### Opción 1: Usar el endpoint `/collaborate`

```bash
curl -X POST "http://localhost:8001/collaborate?agent_url=http://agente-externo:8003&task=Mi tarea"
```

#### Opción 2: Crear tu propio agente cliente

```python
from infrastructure.driven_adapters.a2a.a2a_client import A2AClient

client = A2AClient()

# Descubrir agente
card = await client.discover_agent("http://agente-externo:8003")

# Enviar mensaje
response = await client.send_to_agent(
    "http://agente-externo:8003",
    "¿Puedes ayudarme con esto?"
)
```

#### Opción 3: Otro agente te consume a ti

Desde otro agente:

```python
import httpx

# 1. Descubrir tus capacidades
async with httpx.AsyncClient() as client:
    card = await client.get("http://localhost:8001/.well-known/agent.json")
    print(card.json())

# 2. Enviar tarea en formato A2A
response = await client.post(
    "http://localhost:8001/a2a/tasks",
    json={
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": "Hola"}]
        }
    }
)
```

---


## 📚 Conceptos Clave

### Clean Architecture

- **Domain**: Reglas de negocio puras, independientes de frameworks
- **Application**: Casos de uso, orquestación de lógica de negocio
- **Infrastructure**: Implementaciones concretas (LangGraph, A2A, MCP)
- **Entry Points**: APIs, servidores, interfaces externas

### Dependency Injection

El `Container` centraliza todas las dependencias:

```python
# container.py
llm_gateway = providers.Singleton(LlmGateway, ...)
mcp_client = providers.Singleton(MCPClient, ...)
langgraph_agent = providers.Singleton(LangGraphAgentAdapter, ...)
a2a_server = providers.Singleton(A2AServer, ...)
```

### Ports & Adapters

**Ports** (Interfaces en `domain/model/gateways/`):
- `AgentAdapter`: Interfaz para agentes
- `CollaborateAdapter`: Interfaz para colaboración

**Adapters** (Implementaciones en `infraestructure/`):
- `LangGraphAgentAdapter`: Implementa `AgentAdapter`
- `A2AClient`: Implementa `CollaborateAdapter`

---

## 🚀 Próximos Pasos

### Para Empezar
1. Configura tus variables de entorno
2. Ejecuta `python main.py`
3. Prueba el endpoint `/chat`
4. Explora el Agent Card en `/.well-known/agent.json`

### Para Comunicarte con Otros Agentes
1. Clona este template en otro puerto
2. Cambia las variables `AGENT_NAME`, `AGENT_DESCRIPTION`, `AGENT_BASE_URL`
3. Usa el endpoint `/collaborate` para conectarlos

### Para Extender
1. Añade nuevas skills en `domain/model/skills.py`
2. Crea nuevos use cases en `domain/usecase/`
3. Implementa nuevos adapters en `infraestructure/driven_adapters/`

---

## 🐛 Troubleshooting


**Verificar**:
1. Que el servidor MCP esté corriendo en `MCP_SERVER_ENDPOINT`
2. Que el endpoint sea accesible
3. Revisar los logs del servidor MCP

### Error: Agente externo no encontrado

**Verificar**:
1. Que el agente externo esté corriendo
2. Que la URL sea correcta (incluir protocolo `http://`)
3. Que el agente externo tenga el endpoint `/.well-known/agent.json`
