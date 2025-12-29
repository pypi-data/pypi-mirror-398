# StateManager - Guía de Uso Completa

## Descripción

El `StateManager` integra el sistema oficial de AutoGen (`save_state`/`load_state`) con persistencia en disco (JSON) y auto-guardado periódico.

## Flujo Correcto de Uso

### 1. Guardar Estado (Persistencia Completa)

```python
from src.managers.state_manager import StateManager

# Inicializar StateManager
state_manager = StateManager(
    state_dir=None,  # Usa ~/.daveagent/state por defecto
    auto_save_enabled=True,
    auto_save_interval=300  # 5 minutos
)

# Iniciar sesión
session_id = state_manager.start_session(
    title="Mi sesión de desarrollo",
    tags=["python", "autogen"],
    description="Trabajando en feature X"
)

# Crear team de AutoGen
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent

assistant = AssistantAgent(
    name="assistant",
    model_client=model_client,
    system_message="You are a helpful assistant"
)

team = RoundRobinGroupChat(
    [assistant],
    termination_condition=MaxMessageTermination(max_messages=10)
)

# Ejecutar conversación
result = await team.run(task="Write a poem about AI")

# PASO 1: Guardar estado del team (llama a team.save_state())
await state_manager.save_team_state(
    team_name="main_team",
    team=team,
    metadata={"task": "poetry generation"}
)

# PASO 2: Persistir a disco (guarda el cache en JSON)
await state_manager.save_to_disk()

print(f"✅ Estado guardado en: {state_manager.get_session_path()}")
```

### 2. Cargar Estado (Restauración Completa)

```python
from src.managers.state_manager import StateManager

# Nuevo StateManager (simula nueva ejecución del programa)
state_manager = StateManager()

# Listar sesiones disponibles
sessions = state_manager.list_sessions()
for session in sessions:
    print(f"📁 {session['session_id']}: {session['title']}")
    print(f"   Messages: {session['total_messages']}, Teams: {session['num_teams']}")

# PASO 1: Cargar desde disco (carga JSON al cache)
loaded = await state_manager.load_from_disk(session_id="20250204_143022")

if loaded:
    # Crear NUEVO team (mismo tipo)
    new_team = RoundRobinGroupChat(
        [assistant],
        termination_condition=MaxMessageTermination(max_messages=10)
    )

    # PASO 2: Restaurar estado (llama a team.load_state())
    await state_manager.load_team_state(
        team_name="main_team",
        team=new_team
    )

    # El team ahora tiene el historial completo
    result = await new_team.run(task="What was the last line of the poem?")

    # ✅ El team responderá con el último verso del poema anterior
```

## Métodos del StateManager

### Gestión de Sesiones

```python
# Iniciar nueva sesión
session_id = state_manager.start_session(
    title="Feature Development",
    tags=["backend", "api"],
    description="Implementing REST endpoints"
)

# Listar todas las sesiones
sessions = state_manager.list_sessions()

# Obtener metadata de una sesión
metadata = state_manager.get_session_metadata(session_id)

# Obtener historial de conversación
history = state_manager.get_session_history(session_id)
for msg in history:
    print(f"[{msg['agent']}] {msg['content']}")

# Eliminar sesión
await state_manager.delete_session(session_id)
```

### Guardado de Estados

```python
# Guardar estado de un agente individual
await state_manager.save_agent_state(
    agent_name="coder_agent",
    agent=coder_agent,
    metadata={"role": "code_generation"}
)

# Guardar estado de un team (incluye todos los agentes)
await state_manager.save_team_state(
    team_name="dev_team",
    team=dev_team,
    metadata={"project": "ecommerce"}
)

# Persistir TODO a disco
path = await state_manager.save_to_disk()
print(f"💾 Saved to: {path}")
```

### Carga de Estados

```python
# Cargar TODO desde disco
loaded = await state_manager.load_from_disk(session_id="20250204_150000")

# Cargar estado en un agente
await state_manager.load_agent_state(
    agent_name="coder_agent",
    agent=new_coder_agent
)

# Cargar estado en un team
await state_manager.load_team_state(
    team_name="dev_team",
    team=new_dev_team
)
```

### Auto-Guardado

```python
# Auto-guardado está habilitado por defecto (cada 5 minutos)

# Cambiar intervalo
state_manager.enable_auto_save(interval=120)  # 2 minutos

# Deshabilitar
state_manager.disable_auto_save()

# Re-habilitar
state_manager.enable_auto_save()
```

### Limpieza

```python
# Limpiar cache en memoria (NO borra archivos)
state_manager.clear_cache()

# Limpiar sesión actual (preserva metadata)
state_manager.clear_current_session()

# Cerrar StateManager (guarda estado final)
await state_manager.close()
```

## Formato del Archivo JSON

El StateManager guarda los estados en formato JSON compatible con AutoGen:

```json
{
  "session_id": "20250204_143022",
  "saved_at": "2025-02-04T14:35:12.123456",
  "session_metadata": {
    "title": "Mi sesión",
    "tags": ["python"],
    "description": "...",
    "created_at": "2025-02-04T14:30:22.000000",
    "last_interaction": "2025-02-04T14:35:12.000000"
  },
  "team_states": {
    "main_team": {
      "state": {
        "type": "TeamState",
        "version": "1.0.0",
        "agent_states": {
          "assistant/uuid": {
            "type": "AssistantAgentState",
            "llm_messages": [
              {"content": "...", "source": "user", "type": "UserMessage"},
              {"content": "...", "source": "assistant", "type": "AssistantMessage"}
            ]
          }
        }
      },
      "metadata": {"task": "poetry"},
      "saved_at": "2025-02-04T14:35:12.000000"
    }
  },
  "agent_states": {},
  "metadata": {
    "auto_save_enabled": true,
    "auto_save_interval": 300
  }
}
```

## Ejemplo Completo: Sesión Multi-Turno

```python
import asyncio
from src.managers.state_manager import StateManager
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    # Setup
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    state_manager = StateManager(auto_save_enabled=True)

    # Session 1: Crear conversación inicial
    session_id = state_manager.start_session(title="Poetry Session")

    assistant = AssistantAgent("poet", model_client=model_client)
    team = RoundRobinGroupChat([assistant])

    await team.run(task="Write a haiku about coding")

    # Guardar
    await state_manager.save_team_state("poetry_team", team)
    await state_manager.save_to_disk()

    print(f"✅ Session saved: {session_id}")
    await state_manager.close()

    # --- SIMULAR REINICIO DEL PROGRAMA ---

    # Session 2: Continuar conversación
    new_state_manager = StateManager()
    await new_state_manager.load_from_disk(session_id=session_id)

    new_assistant = AssistantAgent("poet", model_client=model_client)
    new_team = RoundRobinGroupChat([new_assistant])

    await new_state_manager.load_team_state("poetry_team", new_team)

    # El team recuerda la conversación anterior
    await new_team.run(task="Now write a sonnet expanding on that haiku")

    # Guardar progreso
    await new_state_manager.save_team_state("poetry_team", new_team)
    await new_state_manager.save_to_disk()

    await new_state_manager.close()
    await model_client.close()

asyncio.run(main())
```

## Diferencias con Documentación de AutoGen

La documentación oficial de AutoGen muestra:

```python
# AutoGen directo
team_state = await team.save_state()
with open("team_state.json", "w") as f:
    json.dump(team_state, f)

# Cargar
with open("team_state.json", "r") as f:
    team_state = json.load(f)
await new_team.load_state(team_state)
```

**StateManager añade:**
- ✅ Gestión de múltiples sesiones
- ✅ Metadata enriquecida (title, tags, timestamps)
- ✅ Auto-guardado periódico
- ✅ Historial de conversaciones
- ✅ Estadísticas y búsqueda
- ✅ Limpieza segura de sesiones

## Integración con main.py

En `main.py`, el StateManager se usa así:

```python
# Al finalizar conversación
if self.team and self.state_manager:
    await self.state_manager.save_team_state(
        team_name="coding_team",
        team=self.team
    )
    await self.state_manager.save_to_disk()

# Al cargar sesión previa
if session_id:
    await self.state_manager.load_from_disk(session_id)
    # Después de crear team
    await self.state_manager.load_team_state("coding_team", self.team)
```

## Conclusión

El StateManager **YA está usando correctamente** `save_state()` y `load_state()` de AutoGen. La clave es:

1. **Llamar a `save_team_state()`** → Esto invoca `team.save_state()` internamente
2. **Llamar a `save_to_disk()`** → Persiste el cache en JSON
3. **Llamar a `load_from_disk()`** → Carga JSON al cache
4. **Llamar a `load_team_state()`** → Esto invoca `team.load_state()` internamente

**No hay que modificar nada**, solo usar los métodos en el orden correcto.
