import pytest
from mat3ra.mode import Method, Model

DFT_GGA_CONFIG = {"type": "dft", "subtype": "gga"}
ML_RE_CONFIG = {"type": "ml", "subtype": "re"}

MODEL_CONFIGS = [DFT_GGA_CONFIG, ML_RE_CONFIG]

PSEUDOPOTENTIAL_NC_METHOD = {"type": "pseudopotential", "subtype": "nc"}
PSEUDOPOTENTIAL_US_METHOD = {"type": "pseudopotential", "subtype": "us"}

METHOD_CONFIGS = [PSEUDOPOTENTIAL_NC_METHOD, PSEUDOPOTENTIAL_US_METHOD]


@pytest.mark.parametrize("config", MODEL_CONFIGS)
def test_can_be_created(config):
    model = Model.create(config)
    assert model.type == config["type"]
    assert model.subtype == config["subtype"]


@pytest.mark.parametrize("config", MODEL_CONFIGS)
def test_type_property(config):
    model = Model.create(config)
    type_value = model.type

    assert isinstance(type_value, str)
    assert type_value == config["type"]


@pytest.mark.parametrize("config", MODEL_CONFIGS)
def test_subtype_property(config):
    model = Model.create(config)
    subtype_value = model.subtype

    assert subtype_value is not None
    assert subtype_value == config["subtype"]


@pytest.mark.parametrize("config", MODEL_CONFIGS)
@pytest.mark.parametrize("method_config", METHOD_CONFIGS)
def test_method_property_returns_method_instance(config, method_config):
    config_with_method = {**config, "method": method_config}
    model = Model.create(config_with_method)

    method_value = model.method

    assert method_value is not None
    assert isinstance(method_value, Method)

    assert hasattr(method_value, "data")
    assert hasattr(method_value, "search_text")


@pytest.mark.parametrize("config", MODEL_CONFIGS)
@pytest.mark.parametrize("method_config", METHOD_CONFIGS)
def test_to_json(config, method_config):
    config_with_method = {**config, "method": method_config}
    model = Model.create(config_with_method)

    json_data = model.to_dict()
    assert json_data["type"] == config["type"]
    assert json_data["subtype"] == config["subtype"]
    assert "method" in json_data
    assert json_data["method"]["type"] == "pseudopotential"


