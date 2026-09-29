"""Deterministic planning foundation for KnowledgeFlow Agent."""

import re
import unicodedata
from enum import Enum

from pydantic import BaseModel, Field

from app.agentic.state import AgentState
from app.memory.semantic import SemanticMemory
from app.memory.short_term import ShortTermMemory


class PlanningIntent(str, Enum):
    """High-level intents supported by the deterministic planner."""

    KNOWLEDGE_QUERY = "knowledge_query"
    INCIDENT_CREATE = "incident_create"
    INCIDENT_SEARCH = "incident_search"
    INCIDENT_NOTE = "incident_note"


class PlanDecision(BaseModel):
    """Structured planning result without exposing chain-of-thought."""

    intent: PlanningIntent
    steps: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)

    requires_clarification: bool = False
    clarification_question: str | None = None

    incident_id: str | None = None


class RuleBasedPlanner:
    """Deterministic planner used as the initial EP2 planning layer.

    The planner produces only an operational plan: intent, tool sequence and
    clarification requirements. It does not expose private reasoning traces.

    This deterministic implementation provides a reproducible baseline before
    introducing LLM/CrewAI-based planning.
    """

    INCIDENT_ID_PATTERN = re.compile(
        r"\bINC-\d{5}\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        short_term_memory: ShortTermMemory | None = None,
        semantic_memory: SemanticMemory | None = None,
        semantic_top_k: int = 3,
    ) -> None:
        if semantic_top_k < 1:
            raise ValueError("semantic_top_k must be at least 1")

        self.short_term_memory = short_term_memory
        self.semantic_memory = semantic_memory
        self.semantic_top_k = semantic_top_k

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for deterministic keyword classification."""
        normalized = unicodedata.normalize(
            "NFKD",
            text.lower(),
        )

        return "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

    def hydrate_memory_context(self, state: AgentState) -> None:
        """Load relevant short- and long-term memories into AgentState."""
        # Preserve context that may already have been injected into AgentState
        # by an orchestrator or a previous workflow step.
        context: list[dict] = list(state.memory_context)

        if self.short_term_memory is not None:
            for message in self.short_term_memory.get_messages(
                state.conversation_id
            ):
                context.append(
                    {
                        "memory_kind": "short_term",
                        "role": message.role.value,
                        "content": message.content,
                    }
                )

        if self.semantic_memory is not None:
            try:
                semantic_results = self.semantic_memory.search(
                    query=state.user_request,
                    conversation_id=state.conversation_id,
                    top_k=self.semantic_top_k,
                    min_similarity=0.0,
                )

                for result in semantic_results:
                    context.append(
                        {
                            "memory_kind": "long_term",
                            "memory_id": result.memory.public_id,
                            "memory_type": result.memory.memory_type.value,
                            "content": result.memory.content,
                            "metadata": result.memory.metadata,
                            "score": result.score,
                        }
                    )
            except Exception as exc:
                state.observations.append(
                    {
                        "component": "semantic_memory",
                        "status": "unavailable",
                        "error_type": type(exc).__name__,
                    }
                )

        state.memory_context = context

    def _find_incident_id(
        self,
        state: AgentState,
    ) -> str | None:
        """Resolve an incident ID from request, state or loaded memories."""
        match = self.INCIDENT_ID_PATTERN.search(
            state.user_request
        )

        if match:
            return match.group(0).upper()

        if state.incident_id:
            return state.incident_id.upper()

        for memory in state.memory_context:
            searchable = " ".join(
                [
                    str(memory.get("content", "")),
                    str(memory.get("metadata", "")),
                ]
            )

            match = self.INCIDENT_ID_PATTERN.search(searchable)

            if match:
                return match.group(0).upper()

        return None

    def _classify_intent(
        self,
        request: str,
        *,
        has_incident_context: bool = False,
    ) -> PlanningIntent:
        """Classify the request into one supported planning intent."""
        text = self._normalize(request)

        incident_present = "incidente" in text

        note_markers = (
            "nota",
            "seguimiento",
            "comentario",
            "actualiza",
            "actualizar",
            "agrega",
            "agregar",
            "anade",
            "anadir",
        )

        create_markers = (
            "crea",
            "crear",
            "registra",
            "registrar",
            "abre",
            "abrir",
            "reporta",
            "reportar",
        )

        search_markers = (
            "busca",
            "buscar",
            "consulta",
            "consultar",
            "lista",
            "listar",
            "encuentra",
            "encontrar",
            "muestra",
            "mostrar",
            "cual",
            "que incidente",
        )

        if (incident_present or has_incident_context) and any(
            marker in text
            for marker in note_markers
        ):
            return PlanningIntent.INCIDENT_NOTE

        if incident_present and any(
            marker in text
            for marker in create_markers
        ):
            return PlanningIntent.INCIDENT_CREATE

        if incident_present and any(
            marker in text
            for marker in search_markers
        ):
            return PlanningIntent.INCIDENT_SEARCH

        return PlanningIntent.KNOWLEDGE_QUERY

    def plan(
        self,
        state: AgentState,
    ) -> PlanDecision:
        """Build and persist an operational plan for the current request."""
        state.register_iteration()

        self.hydrate_memory_context(state)

        incident_id = self._find_incident_id(state)

        intent = self._classify_intent(
            state.user_request,
            has_incident_context=incident_id is not None,
        )

        if intent == PlanningIntent.INCIDENT_CREATE:
            decision = PlanDecision(
                intent=intent,
                steps=[
                    "Consultar conocimiento aplicable",
                    "Validar información mínima del incidente",
                    "Crear incidente",
                ],
                required_tools=[
                    "search_knowledge",
                    "create_incident",
                ],
            )

        elif intent == PlanningIntent.INCIDENT_SEARCH:
            decision = PlanDecision(
                intent=intent,
                steps=[
                    "Buscar incidentes relacionados",
                ],
                required_tools=[
                    "search_incidents",
                ],
                incident_id=incident_id,
            )

        elif intent == PlanningIntent.INCIDENT_NOTE:
            if incident_id is None:
                decision = PlanDecision(
                    intent=intent,
                    steps=[
                        "Solicitar identificador del incidente",
                    ],
                    required_tools=[],
                    requires_clarification=True,
                    clarification_question=(
                        "¿A qué incidente deseas agregar el seguimiento?"
                    ),
                )
            else:
                decision = PlanDecision(
                    intent=intent,
                    steps=[
                        "Localizar incidente",
                        "Agregar nota de seguimiento",
                    ],
                    required_tools=[
                        "search_incidents",
                        "append_incident_note",
                    ],
                    incident_id=incident_id,
                )

        else:
            decision = PlanDecision(
                intent=PlanningIntent.KNOWLEDGE_QUERY,
                steps=[
                    "Consultar base de conocimiento",
                ],
                required_tools=[
                    "search_knowledge",
                ],
            )

        state.intent = decision.intent.value
        state.plan = list(decision.steps)
        state.required_tools = list(
            decision.required_tools
        )
        state.requires_clarification = (
            decision.requires_clarification
        )
        state.clarification_question = (
            decision.clarification_question
        )

        if decision.incident_id:
            state.incident_id = decision.incident_id

        return decision
