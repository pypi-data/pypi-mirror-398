import pytest
from mat3ra.mode import Method, MethodFactory, PseudopotentialMethod

LOCALORBITAL_POPLE_CONFIG = {"type": "localorbital", "subtype": "pople"}
PSEUDOPOTENTIAL_US_CONFIG = {"type": "pseudopotential", "subtype": "us"}
PSEUDOPOTENTIAL_NC_CONFIG = {"type": "pseudopotential", "subtype": "nc"}

BASIC_METHOD_CONFIGS = [LOCALORBITAL_POPLE_CONFIG]
PSEUDOPOTENTIAL_CONFIGS = [PSEUDOPOTENTIAL_US_CONFIG, PSEUDOPOTENTIAL_NC_CONFIG]


@pytest.mark.parametrize("config", BASIC_METHOD_CONFIGS)
def test_create_basic_method(config):
    method = MethodFactory.create(config)

    assert isinstance(method, Method)
    assert method.type == config["type"]


@pytest.mark.parametrize("config", PSEUDOPOTENTIAL_CONFIGS)
def test_create_pseudopotential_method(config):
    method = MethodFactory.create(config)

    assert isinstance(method, PseudopotentialMethod)
    assert method.type == "pseudopotential"

