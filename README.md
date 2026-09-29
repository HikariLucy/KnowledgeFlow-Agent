# KnowledgeFlow Agent

Agente inteligente organizacional desarrollado para **ISY0101 - Ingeniería de Soluciones con IA (Evaluación Parcial N°2)**. El proyecto evoluciona directamente desde **KnowledgeFlow RAG**, reutilizando el motor RAG de la EP1 como una herramienta de consulta dentro de una arquitectura agentic con estado, persistencia, herramientas tipadas, memoria y planificación adaptativa.

> **Estado actual:** fundación EP2 en desarrollo sobre la rama feat/ep2-agent-foundation. La base heredada de EP1 se mantiene funcional y la suite completa suma actualmente **217 pruebas automatizadas offline**.

---

## 1. Continuidad desde KnowledgeFlow RAG

La EP2 se construye sobre el mismo proyecto organizacional de NovaTech SpA.

La evolución arquitectónica es:

~~~text
EP1 — KnowledgeFlow RAG
Usuario
  ↓
RAGPipeline
  ↓
Routing → Retrieval → FAISS → Grounded Generation
  ↓
Respuesta con citas

EP2 — KnowledgeFlow Agent
Usuario
  ↓
Manager / Orquestación
  ↓
Planificación y selección de herramientas
  ├── search_knowledge → KnowledgeRAGTool → RAGPipeline heredado
  ├── create_incident
  ├── search_incidents
  └── append_incident_note
  ↓
Estado + Memoria + Persistencia
  ↓
Respuesta / Acción
~~~

El objetivo no es reemplazar el RAG desarrollado en la EP1, sino convertirlo en una capacidad reutilizable que un agente pueda invocar cuando necesite evidencia documental.

Repositorio de origen EP1: **HikariLucy/Knowledge-RAG**

Repositorio EP2: **HikariLucy/KnowledgeFlow-Agent**

---

## 2. Problema organizacional

En NovaTech SpA, la información necesaria para resolver solicitudes internas puede estar distribuida entre políticas, procedimientos, documentación técnica y estándares externos. Un sistema RAG permite localizar y fundamentar respuestas, pero no gestiona por sí solo un flujo operativo completo.

KnowledgeFlow Agent amplía esa capacidad para que el sistema pueda:

1. analizar una solicitud;
2. decidir si necesita consultar conocimiento;
3. recuperar evidencia mediante el RAG;
4. mantener estado durante el flujo;
5. validar argumentos antes de ejecutar herramientas;
6. registrar y consultar incidentes;
7. mantener continuidad entre interacciones;
8. adaptar los siguientes pasos según el resultado obtenido.

---

## 3. Objetivo de la EP2

Construir un **agente funcional** capaz de integrar:

- herramientas de consulta;
- herramientas de escritura;
- razonamiento y planificación;
- memoria de corto plazo;
- memoria persistente y recuperación semántica;
- toma de decisiones adaptativa;
- trazabilidad de acciones y resultados;
- límites de iteración para reducir loops descontrolados.

La solución se diseña de forma modular para que cada capacidad pueda probarse de manera aislada antes de incorporarse a la orquestación multiagente.

---

## 4. Estado de implementación

### Implementado

#### Base EP1 preservada

- FastAPI.
- Google Gemini mediante google-genai.
- embeddings con gemini-embedding-2.
- FAISS con similitud coseno.
- carga de documentos internos y externos.
- chunking y metadatos trazables.
- SourceRouter.
- recuperación internal / external / all.
- generación grounded.
- citas S1..SN.
- validación y reparación controlada de citas.
- abstención ante evidencia insuficiente.
- evaluación reproducible y threshold sweep.
- interfaz web y API RAG.

#### Fundación agentic EP2

- **AgentState** para representar el estado operacional de una ejecución.
- registro de plan, pasos completados, herramienta seleccionada, llamadas y observaciones.
- control de seguridad mediante max_iterations.
- persistencia operacional con **SQLite**.
- dominio Incident e IncidentNote.
- identificadores públicos del tipo INC-00001.
- búsqueda y filtrado de incidentes.
- schemas Pydantic para Function Calling.
- validación de categorías, severidades, estados, límites y campos obligatorios.
- **KnowledgeRAGTool**, que expone el RAG de EP1 como herramienta agentic.
- preservación explícita de abstención, citas y fuentes al atravesar la frontera RAG → Tool.
- **IncidentTools ejecutables** para `create_incident`, `search_incidents` y `append_incident_note`.
- separación explícita entre consulta documental y escritura operacional.
- **ShortTermMemory** con ventana configurable de conversación reciente.
- **LongTermMemoryStore** persistente sobre SQLite.
- **SemanticMemory** para recuperar memorias relevantes mediante similitud coseno.
- **RuleBasedPlanner** determinista y consciente de memoria para clasificar intención, generar planes y seleccionar herramientas.
- resolución de `incident_id` desde la solicitud, el estado o memorias recuperadas.
- aclaración adaptativa cuando una operación requiere contexto que aún no está disponible.
- **AdaptiveOrchestrator** para ejecutar planes, registrar observaciones y detener escrituras cuando falta evidencia o contexto.
- **ManagerAgent** sin herramientas operacionales, orientado a planificación y delegación.
- **KnowledgeAgent** restringido a `search_knowledge`.
- **OperationsAgent** restringido a creación, búsqueda y seguimiento de incidentes.
- perfiles de agentes independientes del framework para facilitar la integración posterior con CrewAI.

### Próximos hitos

- orquestación jerárquica con CrewAI;
- trazabilidad visual de plan, herramientas, memoria y resultados;
- escenarios end-to-end para la demo de EP2.

---

## 5. Arquitectura actual

~~~mermaid
flowchart TD
    U[Usuario] --> O[AdaptiveOrchestrator]
    O --> P[RuleBasedPlanner]
    P --> AS[AgentState]

    AS --> KQT[KnowledgeQueryInput]
    O --> KQT[KnowledgeQueryInput]
    KQT --> KRT[KnowledgeRAGTool]

    KRT --> RP[RAGPipeline EP1]
    RP --> SR[SourceRouter]
    RP --> RET[Retriever]
    RET --> VS[FAISS Vector Store]
    RP --> GEN[Grounded Generator]
    GEN --> KR[KnowledgeQueryResult]

    AS --> TS[Tool Schemas]
    TS --> CI[CreateIncidentInput]
    TS --> SI[SearchIncidentsInput]
    TS --> AN[AppendIncidentNoteInput]

    O --> CI[CreateIncidentInput]
    O --> SI[SearchIncidentsInput]
    O --> AN[AppendIncidentNoteInput]
    CI --> CIT[CreateIncidentTool]
    SI --> SIT[SearchIncidentsTool]
    AN --> NIT[AppendIncidentNoteTool]

    DB[(SQLite)]
    CIT --> IR[IncidentRepository]
    SIT --> IR
    NIT --> IR
    IR --> DB
    IR --> INC[Incidents]
    IR --> NOTES[Incident Notes]

    KR --> AS
    INC --> AS
    NOTES --> AS

    P --> STM[ShortTermMemory]
    P --> SM[SemanticMemory]
    STM --> AS
    SM --> AS
    SM --> LTM[LongTermMemoryStore]
    LTM --> DB
~~~

La arquitectura actual separa deliberadamente:

- **RAG**: conocimiento documental.
- **Estado**: información activa de una ejecución.
- **Persistencia operacional**: incidentes y notas.
- **Schemas de tools**: frontera validada para llamadas de herramientas.
- **IncidentTools**: operaciones ejecutables de creación, búsqueda y seguimiento sobre SQLite.
- **Memoria**: ventana reciente en memoria y almacenamiento persistente con recuperación semántica.
- **Planner**: clasificación determinista de intención, secuencia de pasos, selección de tools y detección de aclaraciones.
- **Orquestación adaptativa**: ejecución secuencial, observaciones, abstención segura y bloqueo de escrituras ante contexto insuficiente.

---

## 6. Arquitectura objetivo EP2

~~~mermaid
flowchart TD
    U[Usuario] --> M[Manager Agent]

    M --> P[Planner]
    P --> S[Shared AgentState]

    M --> KA[Knowledge Agent]
    M --> OA[Operations Agent]

    KA --> KRT[search_knowledge]
    KRT --> RAG[KnowledgeFlow RAG EP1]

    OA --> CIT[create_incident]
    OA --> SIT[search_incidents]
    OA --> NIT[append_incident_note]

    CIT --> DB[(SQLite)]
    SIT --> DB
    NIT --> DB

    S --> STM[Short-term Memory]
    S --> LTM[Long-term / Semantic Memory]

    RAG --> M
    DB --> M
    STM --> M
    LTM --> M

    M --> O[Respuesta / Acción]
~~~

> La arquitectura objetivo se documenta desde el inicio, pero los componentes marcados como próximos hitos no deben interpretarse como ya implementados.

---

## 7. Componentes principales

### Roles de agentes

Ubicación:

~~~text
app/agents/
├── profile.py
├── manager.py
├── knowledge_agent.py
└── operations_agent.py
~~~

Separación de responsabilidades:

- `ManagerAgent`: planifica y delega; `tools=()` y `allow_delegation=True`.
- `KnowledgeAgent`: solo puede consultar conocimiento mediante `search_knowledge`.
- `OperationsAgent`: solo puede operar sobre incidentes mediante `create_incident`, `search_incidents` y `append_incident_note`.

Los perfiles son independientes de CrewAI para conservar testabilidad y evitar acoplar la lógica de dominio al framework.

### AdaptiveOrchestrator

Ubicación:

~~~text
app/agentic/orchestrator.py
~~~

Responsabilidades actuales:

- ejecutar en orden las tools requeridas por el planner;
- registrar llamadas y observaciones en `AgentState`;
- detener el flujo cuando el RAG se abstiene;
- impedir `create_incident` si no existen argumentos Pydantic validados;
- validar la existencia de un incidente antes de agregar seguimiento;
- solicitar aclaración cuando faltan datos o un identificador no es válido;
- devolver estados controlados: `completed`, `needs_clarification`, `abstained` y `failed`.

Este componente implementa adaptación observable: el plan inicial puede acortarse según los resultados de las tools.

### RuleBasedPlanner

Ubicación:

~~~text
app/agentic/planner.py
~~~

Responsabilidades actuales:

- clasificar solicitudes en `knowledge_query`, `incident_create`, `incident_search` o `incident_note`;
- hidratar `AgentState.memory_context` desde memoria de corto plazo y memoria semántica;
- conservar contexto previamente inyectado por otros componentes;
- resolver `INC-xxxxx` desde la solicitud, estado o memoria;
- generar una secuencia explícita de pasos y tools requeridas;
- marcar `requires_clarification` cuando falta información indispensable;
- incrementar y respetar el contador de iteraciones de `AgentState`.

El planner expone únicamente un plan operacional estructurado; no expone razonamiento privado del modelo.

### AgentState

Ubicación:

~~~text
app/agentic/state.py
~~~

Representa el estado operacional de una ejecución.

Incluye, entre otros:

- conversation_id;
- user_request;
- intent;
- plan;
- retrieved_context;
- memory_context;
- selected_tool;
- tool_calls;
- observations;
- incident_id;
- completed_steps;
- requires_clarification;
- iteration_count;
- max_iterations.

El estado operacional se mantiene separado de la memoria conversacional a largo plazo.

### Memoria de corto y largo plazo

Ubicación:

~~~text
app/memory/
├── models.py
├── short_term.py
├── long_term.py
└── semantic.py
~~~

Capacidades implementadas:

- ventana de conversación reciente mediante `ShortTermMemory`;
- aislamiento por `conversation_id`;
- persistencia de hechos, eventos, resúmenes y resultados de tools;
- identificadores públicos `MEM-xxxxx`;
- metadata estructurada en JSON;
- almacenamiento opcional de embeddings;
- recuperación semántica con similitud coseno y filtros por conversación;
- reutilización de la abstracción `BaseEmbeddings` heredada de EP1.

La memoria de corto plazo y la memoria persistente son componentes distintos: la primera mantiene continuidad inmediata, mientras que la segunda permite recuperar experiencias pasadas relevantes.

### Persistencia SQLite

Ubicación:

~~~text
app/storage/
├── database.py
├── models.py
└── repositories.py
~~~

Tablas principales:

~~~text
incidents
├── id
├── public_id
├── title
├── description
├── category
├── severity
├── status
├── created_at
└── updated_at

incident_notes
├── id
├── incident_id
├── note
└── created_at
~~~

La base local de desarrollo se mantiene fuera de Git mediante .gitignore.

### Schemas de herramientas

Ubicación:

~~~text
app/tools/schemas.py
~~~

Actualmente se definen contratos tipados para:

- CreateIncidentInput;
- SearchIncidentsInput;
- AppendIncidentNoteInput;
- KnowledgeQueryInput;
- KnowledgeQueryResult;
- KnowledgeSource.

Estos modelos funcionan como frontera de validación antes de que los argumentos lleguen a herramientas de lectura o escritura.

### IncidentTools

Ubicación:

~~~text
app/tools/incidents.py
~~~

Herramientas disponibles:

- `create_incident`: crea un incidente validado y devuelve su identificador público `INC-xxxxx`.
- `search_incidents`: recupera incidentes por texto, identificador o estado.
- `append_incident_note`: agrega seguimiento a un incidente existente sin sobrescribir su historial.

Las tres herramientas reutilizan `IncidentRepository`, por lo que la capa agentic no ejecuta SQL directamente.

### KnowledgeRAGTool

Ubicación:

~~~text
app/tools/knowledge.py
~~~

Nombre lógico de la herramienta:

~~~text
search_knowledge
~~~

Responsabilidad:

- recibir una consulta validada;
- delegar la ejecución al RAGPipeline existente;
- conservar source_scope y top_k;
- retornar respuesta estructurada;
- conservar citas y fuentes;
- conservar el estado de abstención.

La tool depende de la abstracción RAGPipeline y no de FastAPI, evitando acoplar la futura capa agentic a la capa HTTP.

---

## 8. Flujo de consulta implementado

~~~text
KnowledgeQueryInput
        ↓
KnowledgeRAGTool.run()
        ↓
RAGPipeline.run()
        ↓
Source Routing
        ↓
Semantic Retrieval
        ↓
Evidence Filtering
        ↓
Grounded Generation
        ↓
RAGAnswer
        ↓
KnowledgeQueryResult
~~~

La integración tiene pruebas unitarias del adapter y una prueba de integración offline usando el RAGPipeline real junto con proveedores fake deterministas.

---

## 9. Flujo operacional objetivo

Ejemplo de caso EP2:

> “Perdí mi dispositivo de autenticación. Revisa qué procedimiento corresponde y registra un incidente.”

Flujo esperado:

~~~text
1. Manager analiza la solicitud.
2. Planner determina que necesita evidencia.
3. Knowledge Agent usa search_knowledge.
4. El RAG recupera el procedimiento aplicable.
5. Manager evalúa el resultado.
6. Si existe evidencia suficiente:
      Operations Agent crea el incidente.
7. Si falta información:
      el sistema solicita aclaración y no escribe todavía.
8. El resultado queda asociado al estado y a la memoria.
9. Se responde con evidencia e identificador del incidente.
~~~

Este escenario se implementará y probará como flujo end-to-end en los siguientes hitos.

---

## 10. Estructura del repositorio

~~~text
KnowledgeFlow-Agent/
├── app/
│   ├── agentic/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── planner.py
│   │   └── state.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── knowledge_agent.py
│   │   ├── manager.py
│   │   ├── operations_agent.py
│   │   ├── profile.py
│   │   └── source_router.py
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   └── config.py
│   ├── evaluation/
│   ├── llm/
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── long_term.py
│   │   ├── models.py
│   │   ├── semantic.py
│   │   └── short_term.py
│   ├── rag/
│   │   ├── ask.py
│   │   ├── chunking.py
│   │   ├── context.py
│   │   ├── embeddings.py
│   │   ├── generator.py
│   │   ├── indexer.py
│   │   ├── loaders.py
│   │   ├── pipeline.py
│   │   ├── prompts.py
│   │   ├── retriever.py
│   │   ├── schemas.py
│   │   ├── search.py
│   │   └── vectorstore.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repositories.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── incidents.py
│   │   ├── knowledge.py
│   │   └── schemas.py
│   ├── ui/
│   └── main.py
├── docs/
├── evaluation/
├── knowledge/
│   ├── internal/
│   └── external/
├── scripts/
├── tests/
│   ├── test_agent_roles.py
│   ├── test_agent_state.py
│   ├── test_incident_storage.py
│   ├── test_incident_tools.py
│   ├── test_knowledge_tool.py
│   ├── test_long_term_memory.py
│   ├── test_orchestrator.py
│   ├── test_planner.py
│   ├── test_semantic_memory.py
│   ├── test_short_term_memory.py
│   ├── test_tool_schemas.py
│   └── ... pruebas heredadas de EP1
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
~~~

---

## 11. Requisitos

- Python 3.11 o superior.
- Git.
- Acceso a Google Gemini para pruebas en vivo.
- Linux, Windows o macOS.

El desarrollo actual de EP2 se ha validado en Python 3.12.

---

## 12. Instalación

### Linux

~~~bash
git clone https://github.com/HikariLucy/KnowledgeFlow-Agent.git
cd KnowledgeFlow-Agent

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
~~~

### Windows PowerShell

~~~powershell
git clone https://github.com/HikariLucy/KnowledgeFlow-Agent.git
cd KnowledgeFlow-Agent

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
~~~

---

## 13. Configuración

Crear un archivo .env a partir de .env.example.

Parámetros heredados de EP1:

- APP_NAME;
- APP_ENV;
- GEMINI_API_KEY;
- GEMINI_ROUTER_MODEL;
- GEMINI_CHAT_MODEL;
- GEMINI_EMBEDDING_MODEL;
- CHUNK_SIZE;
- CHUNK_OVERLAP;
- EMBEDDING_DIMENSION;
- RETRIEVAL_TOP_K;
- RAG_MIN_SIMILARITY;
- LLM_TEMPERATURE;
- VECTORSTORE_DIR.

Nunca se debe versionar una API key real.

---

## 14. Uso del RAG heredado

### Crear índice

~~~bash
python -m app.rag.indexer
~~~

### Consultar mediante CLI

~~~bash
python -m app.rag.ask "¿Cómo reportar un incidente de seguridad?"
~~~

### API FastAPI

~~~bash
uvicorn app.main:app --reload --port 8000
~~~

Endpoints principales:

~~~text
GET  /health
POST /api/query
GET  /docs
~~~

---

## 15. Pruebas

Toda la fundación EP2 se desarrolla con pruebas offline para evitar consumo innecesario de cuota y separar fallas de integración externa de fallas de lógica local.

Ejecutar toda la suite:

~~~bash
pytest -q
~~~

Estado actual:

~~~text
217 passed
1 warning de deprecación Starlette/FastAPI
~~~

El warning corresponde a la denominación de HTTP 422 utilizada por una dependencia y no representa una falla de la suite.

### Cobertura agregada en EP2

~~~text
test_agent_state.py
  - defaults aislados
  - validación de campos obligatorios
  - tracking de pasos y tools
  - max_iterations

test_incident_storage.py
  - creación de schema SQLite
  - creación y lectura de incidentes
  - búsquedas
  - filtros de estado
  - notas
  - rechazo de incidentes inexistentes

test_tool_schemas.py
  - categorías y severidades válidas
  - rechazo de valores inválidos
  - límites de búsqueda
  - validación de notas

test_knowledge_tool.py
  - forwarding de argumentos
  - resultado estructurado
  - abstención controlada
  - validación de query y top_k
  - integración offline con RAGPipeline

test_incident_tools.py
  - creación real de incidentes desde una tool
  - búsqueda de incidentes
  - filtrado por estado
  - persistencia de notas de seguimiento
  - rechazo controlado de incidentes inexistentes

test_short_term_memory.py
  - orden cronológico
  - ventana reciente configurable
  - aislamiento entre conversaciones
  - rechazo de mensajes vacíos

test_long_term_memory.py
  - persistencia SQLite
  - recarga por identificador
  - filtrado por conversación
  - comportamiento ante IDs inexistentes

test_semantic_memory.py
  - persistencia de embeddings
  - ranking por similitud
  - filtrado por conversación

test_planner.py
  - consulta general → search_knowledge
  - creación de incidente → plan multietapa
  - búsqueda de incidentes
  - notas con identificador explícito
  - aclaración cuando falta incident_id
  - reutilización de memory_context preexistente
  - hidratación de short-term memory
  - recuperación semántica y reutilización de incident_id

test_orchestrator.py
  - consulta de conocimiento end-to-end controlada
  - abstención RAG bloquea escrituras
  - creación de incidente tras evidencia válida
  - aclaración ante payload de escritura ausente
  - búsqueda de incidentes
  - seguimiento de incidente existente
  - bloqueo ante incidente inexistente
  - aclaración ante nota faltante

test_agent_roles.py
  - Manager sin tools y con delegación habilitada
  - Manager devuelve plan sin ejecutar tools
  - Knowledge Agent restringido a search_knowledge
  - Operations Agent restringido a incident tools
  - creación y búsqueda mediante Operations Agent
  - seguimiento mediante Operations Agent
~~~

---

## 16. Seguridad y control de ejecución

Controles presentes o planificados:

- validación Pydantic de argumentos;
- separación entre consulta y escritura;
- SQLite con foreign keys;
- no versionar credenciales;
- abstención RAG ante evidencia insuficiente;
- max_iterations en AgentState;
- herramientas con responsabilidades acotadas;
- confirmación adicional para futuras acciones sensibles;
- pruebas offline deterministas;
- trazabilidad de tool calls y pasos completados.

---

## 17. Relación con los criterios de EP2

| Área | Evidencia actual | Estado |
|---|---|---|
| Herramientas de consulta | KnowledgeRAGTool / search_knowledge | Implementado |
| Herramientas de escritura | create_incident / search_incidents / append_incident_note | Implementado |
| Framework agentic | roles desacoplados preparados para adaptación CrewAI | Parcial |
| Memoria de contenido | ShortTermMemory + LongTermMemoryStore | Implementado |
| Recuperación semántica de contexto | RAG + SemanticMemory por similitud coseno | Implementado |
| Planificación | RuleBasedPlanner + AgentState + selección de tools | Implementado |
| Decisiones adaptativas | abstención, aclaración y bloqueo de escrituras según observaciones | Implementado |
| README y arquitectura | este documento + documentación heredada | En progreso |
| Pruebas | 217 pruebas offline | Implementado |
| Demo agentic end-to-end | escenarios definidos | Pendiente |

Esta tabla se actualizará a medida que los hitos de EP2 se completen.

---

## 18. Roadmap EP2

~~~text
[✓] Migrar Knowledge-RAG a KnowledgeFlow-Agent
[✓] Preservar baseline EP1
[✓] 158 pruebas heredadas verdes
[✓] AgentState
[✓] max_iterations
[✓] SQLite
[✓] Incident / IncidentNote
[✓] schemas tipados
[✓] KnowledgeRAGTool
[✓] integración offline EP1 → EP2
[✓] 179 pruebas verdes
[✓] IncidentTools ejecutables
[✓] 184 pruebas verdes
[✓] short-term memory
[✓] long-term memory
[✓] recuperación semántica de memoria
[✓] 195 pruebas verdes
[✓] planner determinista consciente de memoria
[✓] 203 pruebas verdes
[✓] orquestador adaptativo
[✓] decisiones adaptativas end-to-end sobre tools locales
[✓] 211 pruebas verdes
[✓] Manager Agent
[✓] Knowledge Agent
[✓] Operations Agent
[✓] separación de responsabilidades por tools
[✓] 217 pruebas verdes

[ ] CrewAI
[ ] orquestación jerárquica
[ ] decisiones adaptativas end-to-end
[ ] UI agentic / trace
[ ] evidencia de demo
[ ] informe EP2
[ ] presentación EP2
~~~

---

## 19. Documentación heredada de EP1

La documentación técnica de KnowledgeFlow RAG se conserva porque constituye la base del nuevo sistema:

- docs/architecture/architecture.md
- docs/architecture/architecture.mmd
- docs/evidence/implementation-evidence.md
- docs/evidence/evaluation-evidence.md
- docs/evidence/demo-runbook.md
- docs/report/report-outline.md
- docs/presentation/presentation-outline.md

Estos documentos corresponden a la etapa RAG y serán complementados con documentación específica de agentes, memoria, planificación y orquestación durante EP2.

---

## 20. Datos demo

> **Aviso académico:** NovaTech SpA y los documentos del corpus son ficticios y fueron creados con fines pedagógicos para ISY0101. No representan infraestructura, políticas ni información de una organización real.

---

## 21. Estado del proyecto

**Rama de desarrollo EP2:** feat/ep2-agent-foundation

**Baseline EP1 heredada:** 6dfdc57

**Fundación de estado/persistencia:** 2701cbf

**RAG expuesto como herramienta agentic:** f2fb796

**IncidentTools ejecutables:** d3eaf25

**Memoria de corto/largo plazo y recuperación semántica:** cfcfea8

**Planner determinista consciente de memoria:** eef07f3

**Orquestador adaptativo:** c0ff5cd

**Roles Manager/Knowledge/Operations:** 61a04da

**Suite actual:** 217 pruebas aprobadas.

El siguiente hito técnico es integrar CrewAI de forma controlada sobre los perfiles y componentes ya probados, manteniendo la lógica de dominio independiente del framework.
