import pytest
from pathlib import Path


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).parent.parent.parent.parent / "tests" / "data"


@pytest.fixture
def key_prefix(request):
    return f"pytest:{request.module.__name__}:{request.node.name}:"


@pytest.fixture
def index_name(request):
    return f"pytest_{request.module.__name__}_{request.node.name}"


@pytest.fixture
def fields():
    return [{"type": "text", "name": "title"}]


@pytest.fixture
def redis():
    raise NotImplementedError("Override this fixture in conftest.py")
