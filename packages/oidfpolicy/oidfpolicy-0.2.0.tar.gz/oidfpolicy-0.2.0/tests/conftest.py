import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def tapolicy0():
    return (DATA_DIR / "tapolicy0.json").read_text()


@pytest.fixture
def tapolicy1():
    return (DATA_DIR / "tapolicy1.json").read_text()


@pytest.fixture
def iapolicy0():
    data = json.loads((DATA_DIR / "iapolicy0.json").read_text())
    return json.dumps(data["metadata_policy"])


@pytest.fixture
def iapolicy1():
    data = json.loads((DATA_DIR / "iapolicy1.json").read_text())
    return json.dumps(data["metadata_policy"])


@pytest.fixture
def policymerge0():
    return json.loads((DATA_DIR / "policymerge0.json").read_text())


@pytest.fixture
def policymerge1():
    return json.loads((DATA_DIR / "policymerge1.json").read_text())


@pytest.fixture
def merged_policy0():
    return (DATA_DIR / "mergedpolicy0.json").read_text()


@pytest.fixture
def metadata0():
    return (DATA_DIR / "metadata0.json").read_text()


@pytest.fixture
def applied_metadata0():
    return json.loads((DATA_DIR / "appliedmetadata0.json").read_text())
