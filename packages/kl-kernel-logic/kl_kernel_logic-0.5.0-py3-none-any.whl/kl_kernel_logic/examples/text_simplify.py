"""
Example: simple text simplification under KL.

This module can be run directly:
    python -m kl_kernel_logic.examples.text_simplify
"""

from typing import Any, Dict

from kl_kernel_logic import PsiDefinition, Kernel


def simplify_text(text: str) -> str:
    """
    Very small stand in for an AI operation.

    In a real system this could call an LLM or a specialised service.
    """
    return " ".join(text.strip().split()).lower()


def run_example() -> Dict[str, Any]:
    psi = PsiDefinition(
        psi_type="application.text_simplify",
        name="simplify",
    )

    input_text = "  This Is   A DEMO Text   with   Irregular   spacing. "

    kernel = Kernel()
    trace = kernel.execute(psi=psi, task=simplify_text, text=input_text)

    return {
        "psi": psi.describe(),
        "success": trace.success,
        "output": trace.output,
        "runtime_ms": trace.runtime_ms,
    }


if __name__ == "__main__":
    from pprint import pprint

    pprint(run_example())
