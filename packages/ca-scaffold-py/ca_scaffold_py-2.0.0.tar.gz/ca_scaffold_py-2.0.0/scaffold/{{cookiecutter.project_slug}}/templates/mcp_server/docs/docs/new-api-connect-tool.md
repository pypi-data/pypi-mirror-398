# Guía Completa para Agregar una Nueva API de API Connect en MCP Server

Esta guía detalla paso a paso cómo agregar una nueva integración con API Connect, siguiendo el patrón implementado en la API de Personal Data.

---

## Arquitectura General

```
Entry Point (Tool) → Use Case → Gateway (Interface) → Adapter → API Connect
                                                          ↓
                                                   ApiConnectAdapter (Shared)
```

---

## Pasos Detallados

### 1. Definir Modelos de Dominio (`src/domain/model/`)

**Propósito:** Definir las estructuras de datos que representan el dominio de negocio.

#### 1.1. Crear la estructura de carpetas
```
src/domain/model/
└── nueva_funcionalidad/
    ├── __init__.py
    ├── request_model.py (opcional)
    ├── response_model.py
    └── gateways/
        ├── __init__.py
        └── nueva_funcionalidad_adapter.py
```

#### 1.2. Crear los modelos Pydantic

**Archivo:** `response_model.py`

**Puntos clave:**
- Usa `BaseModel` de Pydantic para los modelos
- Define campos obligatorios y opcionales con tipos
- Usa `Optional[object]` para estructuras anidadas dinámicas
- Documenta cada modelo con docstrings
- Crea clases anidadas si la respuesta tiene múltiples niveles
- Los nombres de campos deben coincidir con la respuesta de la API

**Referencia:** Ver `basic_information_model.py` y `detail_information_model.py`

#### 1.3. Crear el Gateway (Interfaz abstracta)

**Archivo:** `gateways/nueva_funcionalidad_adapter.py`

**Puntos clave:**
- Hereda de `ABC` (Abstract Base Class)
- Todos los métodos deben ser `@abstractmethod`
- Los métodos deben ser `async`
- Define el contrato que implementará el adapter
- Incluye docstrings descriptivos
- Retorna los modelos de dominio creados anteriormente

**Referencia:** Ver `personal_data_adapter.py`

#### 1.4. Actualizar `__init__.py`

**Archivo:** `src/domain/model/nueva_funcionalidad/__init__.py`

**Puntos clave:**
- Importa todos los modelos creados
- Exporta en `__all__` para facilitar importaciones
- Mantén consistencia con otros módulos

---

### 2. Crear Custom Error (`src/domain/model/errors/`)

**Propósito:** Manejo específico de errores del dominio.

**Archivo:** `src/domain/model/errors/nueva_funcionalidad_error.py`

**Puntos clave:**
- Hereda de `Exception`
- Incluye un mensaje por defecto descriptivo
- Implementa `__init__` y `__str__`
- Usa un nombre descriptivo que termine en `Error`
- Agrega docstrings explicativos

**Referencia:** Ver `personal_data_error.py`

---

### 3. Implementar el Adapter de API Connect

**Propósito:** Implementar la integración real con API Connect.

#### 3.1. Crear estructura de carpetas
```
src/infrastructure/driven_adapters/
└── api_connect_adapter/
    ├── __init__.py
    ├── errors/
    │   ├── __init__.py
    │   └── api_connect_error.py (ya existe)
    └── adapter/
        ├── api_connect_adapter.py (ya existe, compartido)
        └── nueva_funcionalidad_api_adapter.py (NUEVO)
```

#### 3.2. Implementar el Adapter específico

**Archivo:** `adapter/nueva_funcionalidad_api_adapter.py`

**Puntos clave:**
- Implementa la interfaz del gateway creado en el paso 1.3
- Recibe `config: Dict` y `api_adapter: ApiConnectAdapter` en el constructor
- Extrae el endpoint de la configuración usando `config.get()`
- Inicializa logger con `logging.getLogger(__name__)`
- Construye el payload según especificación de la API
- Usa `api_adapter.make_post_request()` o `make_get_request()` según corresponda
- Siempre llama a `api_adapter.handle_api_error(result)` para validar respuesta
- Captura `ApiConnectError` y lanza el error de dominio personalizado
- Agrega logging detallado para debugging
- Retorna instancia del modelo de dominio usando `**result["body"]["data"]`

**Referencia:** Ver `personal_data_api_adapter.py`

#### 3.3. Actualizar `__init__.py`

**Archivo:** `src/infrastructure/driven_adapters/api_connect_adapter/__init__.py`

**Puntos clave:**
- Importa el nuevo adapter creado
- Agrégalo a la lista `__all__`
- Mantén el orden alfabético

---

### 4. Implementar el Caso de Uso

**Propósito:** Lógica de negocio que orquesta la operación.

**Archivo:** `src/domain/usecase/nueva_funcionalidad_use_case.py`

**Puntos clave:**
- Recibe el adapter del gateway por inyección de dependencias en `__init__`
- Crea métodos `async` que correspondan a las operaciones necesarias
- Los métodos deben delegar al adapter
- Agrega documentación completa con docstrings (Args, Returns, Raises)
- Puede agregar lógica de negocio adicional si es necesario (validaciones, transformaciones)
- Propaga excepciones del adapter sin capturarlas
- Usa nombres descriptivos para los métodos

**Referencia:** Ver `retrieve_personal_data_use_case.py`

---

### 5. Configurar Settings

**Propósito:** Agregar configuración de endpoints y variables de entorno.

**Archivo:** `src/applications/settings/settings.py`

#### 5.1. Agregar el nuevo endpoint en la clase `Config`

**Puntos clave:**
- Agrega un nuevo campo tipo `str` con `Field()`
- Usa `default=""` como valor por defecto
- Define el `alias` con el nombre de la variable de entorno (UPPERCASE)
- Documenta el propósito del endpoint

#### 5.2. Actualizar el validador de endpoints

**Puntos clave:**
- Agrega el nombre del nuevo campo al decorador `@field_validator()`
- Esto asegurará que el endpoint sea una URL válida (http:// o https://)
- El validador también verificará que no esté vacío

**Variables de entorno requeridas:**
- `API_SECRET_NAME`: Nombre del secreto en AWS Secret Manager
- `NUEVA_FUNCIONALIDAD_ENDPOINT`: URL completa del endpoint

**Referencia:** Ver configuración de `basic_information_endpoint` y `detail_information_endpoint`

---

### 6. Configurar Inyección de Dependencias

**Propósito:** Registrar todas las dependencias en el contenedor.

**Archivo:** `src/applications/settings/container.py`

#### 6.1. Agregar imports necesarios

**Puntos clave:**
- Importa el nuevo use case creado
- Importa el nuevo adapter creado

#### 6.2. Registrar el adapter en el contenedor

**Puntos clave:**
- Usa `providers.Singleton()` para el adapter
- Primer argumento: la clase del adapter
- Parámetro `config=config.provided`: pasa toda la configuración
- Parámetro `api_adapter=api_connect_adapter`: reutiliza el adapter compartido
- No crear nueva instancia de `ApiConnectAdapter`

#### 6.3. Registrar el use case en el contenedor

**Puntos clave:**
- Usa `providers.Singleton()` para use cases stateless
- Usa `providers.Factory()` si necesitas nueva instancia cada vez
- Inyecta el adapter creado anteriormente por nombre de parámetro
- El nombre del parámetro debe coincidir con el constructor del use case

**Referencia:** Ver configuración de `personal_data_adapter` y `personal_data_usecase`

---

### 7. Definir la Tool en MCP Server

**Propósito:** Exponer la funcionalidad a través del MCP Server.

**Archivo:** `src/infrastructure/entry_points/mcp/tools.py`

#### 7.1. Agregar imports

**Puntos clave:**
- Importa el use case creado

#### 7.2. Agregar el use case a la función `bind_tools`

**Puntos clave:**
- Agrega un parámetro con el use case
- Usa `@inject` de dependency_injector
- Sintaxis: `nombre_usecase: ClaseUseCase = Provide[Container.nombre_usecase]`

#### 7.3. Crear la tool

**Puntos clave:**
- Usa el decorador `@mcp.tool("nombre_tool")` con nombre en snake_case
- Define parámetros con tipos (str, int, float, etc.)
- Incluye docstring completo: descripción, Args y Returns
- Llama al método del use case con await
- Convierte el resultado a dict con `.model_dump()`
- Retorna el diccionario

**Referencia:** Ver `get_basic_personal_data` y `get_detailed_personal_data`

---

### 8. Crear Pruebas Unitarias

#### 8.1. Test del Adapter

**Archivo:** `tests/unit-test/test_infrastructure/driven_adapters/test_nueva_funcionalidad_api_adapter.py`

**Puntos clave:**
- Crea fixtures para mocks (`mock_api_adapter`, `config`, `adapter`)
- Usa `@pytest.mark.asyncio` para tests asíncronos
- Usa `AsyncMock` para métodos asíncronos
- Prueba caso de éxito: mock de respuesta exitosa
- Prueba caso de error: mock que lanza `ApiConnectError`
- Verifica que se llamen los métodos correctos (`assert_called_once`)
- Verifica tipos de retorno
- Verifica que se lance el error de dominio personalizado

**Referencia:** Ver `test_personal_data_api_adapter.py`

#### 8.2. Test del Use Case

**Archivo:** `tests/unit-test/test_domain/usecase/test_nueva_funcionalidad_use_case.py`

**Puntos clave:**
- Crea fixtures para mocks (`mock_adapter`, `use_case`)
- Usa `@pytest.mark.asyncio` para tests asíncronos
- Usa `AsyncMock` para mockear métodos del adapter
- Prueba caso de éxito con datos esperados
- Prueba caso de error verificando que se propague la excepción
- Verifica que se llamen los métodos del adapter correctamente
- Usa `assert result == expected_data` para validar

**Referencia:** Ver `test_retrieve_personal_data_use_case.py`

---

## Flujo Completo de Implementación

### Orden Recomendado:

1. **Definir Modelos de Dominio** (Paso 1)
   - Modelos de request/response con Pydantic
   - Gateway (interfaz abstracta)
   - Actualizar `__init__.py`

2. **Crear Custom Error** (Paso 2)
   - Error específico del dominio que hereda de Exception

3. **Agregar Settings** (Paso 5)
   - Endpoint en la clase Config
   - Variables de entorno
   - Validadores de URLs

4. **Implementar Adapter** (Paso 3)
   - Adapter específico que implementa el gateway
   - Actualizar `__init__.py` del módulo

5. **Implementar Use Case** (Paso 4)
   - Lógica de negocio que usa el adapter

6. **Configurar Container** (Paso 6)
   - Registrar adapter como Singleton
   - Registrar use case con sus dependencias

7. **Definir Tool** (Paso 7)
   - Exponer funcionalidad en MCP Server

8. **Crear Tests** (Paso 8)
   - Tests del adapter con mocks
   - Tests del use case

---

## Checklist de Implementación

### Archivos a Crear:

**Dominio:**
- [ ] `src/domain/model/nueva_funcionalidad/__init__.py`
- [ ] `src/domain/model/nueva_funcionalidad/response_model.py`
- [ ] `src/domain/model/nueva_funcionalidad/gateways/__init__.py`
- [ ] `src/domain/model/nueva_funcionalidad/gateways/nueva_funcionalidad_adapter.py`
- [ ] `src/domain/model/errors/nueva_funcionalidad_error.py`

**Infraestructura:**
- [ ] `src/infrastructure/driven_adapters/api_connect_adapter/adapter/nueva_funcionalidad_api_adapter.py`
- [ ] `src/domain/usecase/nueva_funcionalidad_use_case.py`

**Tests:**
- [ ] `tests/unit-test/test_infrastructure/driven_adapters/test_nueva_funcionalidad_api_adapter.py`
- [ ] `tests/unit-test/test_domain/usecase/test_nueva_funcionalidad_use_case.py`

### Archivos a Modificar:

**Configuración:**
- [ ] `src/applications/settings/settings.py` - Agregar endpoint y validadores
- [ ] `src/applications/settings/container.py` - Registrar adapter y use case
- [ ] `src/infrastructure/driven_adapters/api_connect_adapter/__init__.py` - Exportar nuevo adapter
- [ ] `src/infrastructure/entry_points/mcp/tools.py` - Agregar nueva tool

**Variables de Entorno:**
- [ ] Agregar `NUEVA_FUNCIONALIDAD_ENDPOINT=https://...` al ambiente
- [ ] Verificar que `API_SECRET_NAME` esté configurado

---

## Patrones y Best Practices

### 1. **Reutilización de ApiConnectAdapter**
- Siempre reutiliza la instancia compartida del `ApiConnectAdapter`
- No crear nuevas instancias del adapter base
- La autenticación y manejo de credenciales es centralizado

### 2. **Manejo de Errores por Capas**
- **Adapter:** Captura `ApiConnectError` → Lanza error de dominio
- **Use Case:** Propaga el error de dominio sin capturarlo
- **Tool:** Deja que el framework MCP maneje la excepción

### 3. **Separación de Responsabilidades**
- **Gateway:** Contrato/interfaz (qué se puede hacer)
- **Adapter:** Implementación técnica (cómo se hace)
- **Use Case:** Lógica de negocio (cuándo y por qué)
- **Tool:** Exposición del servicio (entrada/salida)

### 4. **Inyección de Dependencias**
- Usa el Container para todas las dependencias
- `Singleton` para servicios sin estado
- `Factory` si necesitas instancias únicas por llamada
- Los nombres de parámetros deben coincidir exactamente

### 5. **Async/Await**
- Todos los métodos de integración externa son async
- Usa `await` al llamar métodos async
- En tests, usa `AsyncMock` para simular comportamiento async

### 6. **Validación y Configuración**
- Valida URLs en settings con `@field_validator`
- Valida campos requeridos
- Usa Pydantic para validación automática de modelos

### 7. **Testing**
- Usa fixtures para reutilizar configuración de tests
- Mock todas las dependencias externas
- Prueba tanto casos exitosos como errores
- Verifica llamadas a métodos con `assert_called_once`

---

## Ejemplo de Integración Completa

### Caso: Customer Address API

**Especificación:**
- **Endpoint:** `POST /customer/address`
- **Request:** `{ "data": { "customerId": "123" } }`
- **Response:** `{ "data": { "customer": { "address": {...} } } }`

**Archivos necesarios:**

1. **Modelos:**
   - `src/domain/model/customer_address/address_model.py`
   - `src/domain/model/customer_address/gateways/customer_address_adapter.py`

2. **Error:**
   - `src/domain/model/errors/customer_address_error.py`

3. **Adapter:**
   - `src/infrastructure/driven_adapters/api_connect_adapter/adapter/customer_address_api_adapter.py`

4. **Use Case:**
   - `src/domain/usecase/retrieve_customer_address_use_case.py`

5. **Configuración:**
   - Modificar `settings.py`: agregar `CUSTOMER_ADDRESS_ENDPOINT`
   - Modificar `container.py`: registrar adapter y use case

6. **Tool:**
   - Modificar `tools.py`: agregar `get_customer_address(customer_id: str)`

7. **Tests:**
   - `test_customer_address_api_adapter.py`
   - `test_retrieve_customer_address_use_case.py`

---

## Referencias de Código

### Archivos de Referencia para Personal Data:

**Modelos:**
- `src/domain/model/personal_data/basic_information_model.py`
- `src/domain/model/personal_data/detail_information_model.py`
- `src/domain/model/personal_data/__init__.py`

**Gateway:**
- `src/domain/model/personal_data/gateways/personal_data_adapter.py`

**Error:**
- `src/domain/model/errors/personal_data_error.py`

**Adapter:**
- `src/infrastructure/driven_adapters/api_connect_adapter/adapter/api_connect_adapter.py` (base compartido)
- `src/infrastructure/driven_adapters/api_connect_adapter/adapter/personal_data_api_adapter.py`

**Use Case:**
- `src/domain/usecase/retrieve_personal_data_use_case.py`

**Tests:**
- `tests/unit-test/test_infrastructure/driven_adapters/test_personal_data_api_adapter.py`
- `tests/unit-test/test_domain/usecase/test_retrieve_personal_data_use_case.py`

---

## Troubleshooting

### Error: "Endpoint cannot be empty"
**Causa:** Variable de entorno no definida o mal configurada  
**Solución:**
- Verificar que la variable esté en el archivo `.env` o en el ambiente
- Verificar que el nombre coincida con el `alias` en `settings.py`
- Verificar que el endpoint esté en el validador `@field_validator`

### Error: "ApiConnectError: 401 Unauthorized"
**Causa:** Credenciales inválidas o expiradas  
**Solución:**
- Verificar que `API_SECRET_NAME` apunte al secreto correcto
- Verificar que el secreto en AWS Secret Manager contenga `client_id` y `client_secret`
- Verificar formato JSON del secreto: `{"client_id": "...", "client_secret": "..."}`

### Error: "Failed to get data"
**Causa:** Error en la comunicación con API Connect  
**Solución:**
- Revisar logs del adapter para detalles
- Verificar que la estructura del payload coincida con la especificación de la API
- Verificar que el endpoint sea correcto y accesible
- Verificar que la respuesta tenga la estructura esperada

### Tests fallan con "coroutine was never awaited"
**Causa:** Método async llamado sin `await` o mock incorrecto  
**Solución:**
- Usar `AsyncMock` en lugar de `MagicMock` para métodos async
- Agregar `await` al llamar métodos async en tests
- Verificar que el test tenga el decorador `@pytest.mark.asyncio`

### Error: "Provider is not defined"
**Causa:** Dependencia no registrada en el Container  
**Solución:**
- Verificar que el adapter esté registrado en `container.py`
- Verificar que el use case esté registrado con el adapter correcto
- Verificar que los nombres de parámetros coincidan exactamente

### Error de importación circular
**Causa:** Imports cruzados entre módulos  
**Solución:**
- Verificar que los imports sigan el flujo: Tool → Use Case → Gateway ← Adapter
- Usar imports relativos donde sea apropiado
- Revisar el patrón usado en Personal Data

---

## Documentación de Referencia

### Frameworks y Librerías:
- **Pydantic:** Validación de datos y modelos - https://docs.pydantic.dev/
- **Dependency Injector:** Inyección de dependencias - https://python-dependency-injector.ets-labs.org/
- **Pytest:** Testing framework - https://docs.pytest.org/
- **AsyncIO:** Programación asíncrona en Python - https://docs.python.org/3/library/asyncio.html

### Patrones de Diseño:
- **Hexagonal Architecture:** Puertos y Adaptadores
- **Dependency Injection:** Inversión de control
- **Repository Pattern:** Abstracción de acceso a datos
- **Gateway Pattern:** Interfaz para sistemas externos

---

## Notas Finales

### Convenciones de Nombres:
- **Módulos:** `snake_case` (ej: `customer_address`)
- **Clases:** `PascalCase` (ej: `CustomerAddressAdapter`)
- **Métodos/Funciones:** `snake_case` (ej: `get_customer_address`)
- **Constantes:** `UPPER_CASE` (ej: `API_SECRET_NAME`)
- **Tools MCP:** `snake_case` (ej: `get_customer_address`)

### Estructura de Docstrings:
```
"""Brief description.

Detailed description if needed.

Args:
    param1: Description of param1
    param2: Description of param2

Returns:
    Description of return value

Raises:
    ExceptionType: When this exception is raised
"""
```

### Logging Best Practices:
- Usa `logging.getLogger(__name__)` en cada clase
- Log nivel `ERROR` para excepciones capturadas
- Log nivel `WARNING` para situaciones anómalas
- Log nivel `INFO` para flujo normal relevante
- Incluye contexto relevante en los mensajes

---

**✅ Con esta guía tienes todo lo necesario para agregar una nueva integración de API Connect siguiendo los patrones establecidos en el proyecto.**