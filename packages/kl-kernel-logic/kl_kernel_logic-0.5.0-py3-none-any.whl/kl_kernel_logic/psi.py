# psi.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class PsiDefinition:
    """
    Minimal logical operation descriptor.

    Contract:
    - Kernel treats PsiDefinition as opaque.
    - No interpretation, no branching, no policy.
    - All fields are descriptive only.
    """

    psi_type: str          # coarse category of the operation
    name: str              # logical name of the operation
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def describe(self) -> Dict[str, Any]:
        """Stable serializable view."""
        items: Dict[str, Any] = {}
        for key in sorted(self.metadata.keys(), key=lambda k: str(k)):
            items[str(key)] = self.metadata[key]
        return {
            "psi_type": self.psi_type,
            "name": self.name,
            "metadata": items,
        }
