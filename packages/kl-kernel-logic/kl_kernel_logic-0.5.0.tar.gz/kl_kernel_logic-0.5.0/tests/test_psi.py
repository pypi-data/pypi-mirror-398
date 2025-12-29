# Tests for PsiDefinition

from kl_kernel_logic import PsiDefinition


def test_psi_creation():
    psi = PsiDefinition(psi_type="text", name="uppercase")

    assert psi.psi_type == "text"
    assert psi.name == "uppercase"
    assert psi.metadata == {}


def test_psi_with_metadata():
    psi = PsiDefinition(
        psi_type="io",
        name="read_file",
        metadata={"path": "/tmp/test.txt"},
    )

    assert psi.metadata["path"] == "/tmp/test.txt"


def test_psi_describe():
    psi = PsiDefinition(psi_type="test", name="example")
    data = psi.describe()

    assert data["psi_type"] == "test"
    assert data["name"] == "example"
    assert "metadata" in data


def test_psi_is_frozen():
    psi = PsiDefinition(psi_type="test", name="frozen")

    try:
        psi.name = "changed"
        assert False, "Should raise"
    except Exception:
        pass  # expected

