"""
MCP Resource Handlers for Project Management Automation

These modules provide resource access for automation status, history, and metadata.

Resources:
- Static: status, tasks, cache, catalog, history, memories
- Dynamic (templates): tasks://{id}, advisor://{id}, memory://{id}
- Context Primer: automation://context-primer, automation://hints
"""

from .capabilities import (
    CAPABILITIES,
    get_capabilities,
    get_capabilities_summary,
    get_domain_capabilities,
    register_capabilities_resources,
)
from .context_primer import (
    TOOL_HINTS_REGISTRY,
    WORKFLOW_MODE_CONTEXT,
    get_all_hints,
    get_context_primer,
    get_hints_for_mode,
    register_context_primer_resources,
)
from .hint_registry import (
    HintRegistry,
    ToolHint,
    create_hints_directory,
    get_hint,
    get_hint_registry,
    register_hint_registry_resources,
    reload_hints,
)
from .prompt_discovery import (
    PROMPT_CATEGORIES,
    PROMPT_DESCRIPTIONS,
    PROMPT_MODE_MAPPING,
    PROMPT_PERSONA_MAPPING,
    discover_prompts,
    get_prompts_for_category,
    get_prompts_for_mode,
    get_prompts_for_persona,
    register_prompt_discovery_resources,
    register_prompt_discovery_tools,
)
from .templates import (
    get_advisor_consultations,
    get_advisor_info,
    get_memories_by_category,
    get_memory_by_id,
    get_task_by_id,
    get_tasks_by_priority,
    get_tasks_by_status,
    get_tasks_by_tag,
    register_resource_templates,
)

from .session import (
    SessionModeStorage,
    get_session_mode_resource,
    infer_session_mode_tool,
    register_session_resources,
)
__all__ = [
    # Registration
    "register_resource_templates",
    "register_context_primer_resources",
    "register_hint_registry_resources",
    "register_prompt_discovery_resources",
    "register_prompt_discovery_tools",
    # Task resources
    "get_task_by_id",
    "get_tasks_by_status",
    "get_tasks_by_tag",
    "get_tasks_by_priority",
    # Advisor resources
    "get_advisor_consultations",
    "get_advisor_info",
    # Memory resources
    "get_memory_by_id",
    "get_memories_by_category",
    # Context primer
    "TOOL_HINTS_REGISTRY",
    "WORKFLOW_MODE_CONTEXT",
    "get_context_primer",
    "get_hints_for_mode",
    "get_all_hints",
    # Hint registry
    "ToolHint",
    "HintRegistry",
    "get_hint_registry",
    "reload_hints",
    "get_hint",
    "create_hints_directory",
    # Prompt discovery
    "PROMPT_MODE_MAPPING",
    "PROMPT_PERSONA_MAPPING",
    "PROMPT_CATEGORIES",
    "PROMPT_DESCRIPTIONS",
    "get_prompts_for_mode",
    "get_prompts_for_persona",
    "get_prompts_for_category",
    "discover_prompts",
    # Capabilities
    "CAPABILITIES",
    "get_capabilities",
    "get_capabilities_summary",
    "get_domain_capabilities",
    "register_capabilities_resources",
    # Session mode (MODE-002)
    "SessionModeStorage",
    "get_session_mode_resource",
    "infer_session_mode_tool",
    "register_session_resources",
]
