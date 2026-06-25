import os
import tempfile
from datetime import UTC, datetime
from uuid import uuid4

import pytest


@pytest.fixture
def tmp_dir_root() -> str:
    # Это путь к временной директории, в которой будут создаваться временные директории для тестов
    # Можно заменить на любой другой, который понравится.
    path = "./temdir"
    if not os.path.exists(path):
        os.makedirs(path)
    return path


@pytest.fixture
def run_id() -> str:
    return f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{str(uuid4())}"


@pytest.fixture
def tmpdir(run_id: str, tmp_dir_root: str) -> str:
    return tempfile.mkdtemp(prefix=f"{run_id}", dir=tmp_dir_root)
