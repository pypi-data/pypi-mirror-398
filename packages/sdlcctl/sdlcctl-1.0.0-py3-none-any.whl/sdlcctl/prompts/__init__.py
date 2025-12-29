"""
SDLC CLI Prompts Module.
Sprint 52: Vietnamese Domain Prompts
"""

from .vietnamese import (
    DOMAIN_PROMPTS,
    SYSTEM_PROMPT_VI,
    ENTITY_TEMPLATES,
    get_domain_prompt,
    get_entity_template,
)

__all__ = [
    "DOMAIN_PROMPTS",
    "SYSTEM_PROMPT_VI",
    "ENTITY_TEMPLATES",
    "get_domain_prompt",
    "get_entity_template",
]
