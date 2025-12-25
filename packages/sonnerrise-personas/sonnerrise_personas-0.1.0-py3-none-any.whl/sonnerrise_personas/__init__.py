"""Sonnerrise Personas - Suno persona definitions module."""

from sonnerrise_personas.models import Persona
from sonnerrise_personas.repository import PersonaRepository
from sonnerrise_personas.schemas import (
    PersonaCreate,
    PersonaRead,
    PersonaUpdate,
    PersonaList,
)

__version__ = "0.1.0"

__all__ = [
    "Persona",
    "PersonaRepository",
    "PersonaCreate",
    "PersonaRead",
    "PersonaUpdate",
    "PersonaList",
    "__version__",
]
