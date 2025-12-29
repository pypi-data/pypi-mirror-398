from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from service_forge.service import Service

_current_service: Service | None = None

def set_service(service: Service) -> None:
    global _current_service
    _current_service = service

def get_service() -> Service | None:
    return _current_service