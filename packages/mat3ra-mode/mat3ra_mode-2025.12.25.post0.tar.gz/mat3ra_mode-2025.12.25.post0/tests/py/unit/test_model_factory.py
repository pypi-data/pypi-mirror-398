import pytest
from mat3ra.mode import DFTModel, Model, ModelFactory

ML_RE_CONFIG = {"type": "ml", "subtype": "re"}
DFT_GGA_CONFIG = {"type": "dft", "subtype": "gga"}

BASIC_MODEL_CONFIGS = [ML_RE_CONFIG]
DFT_MODEL_CONFIGS = [DFT_GGA_CONFIG]


@pytest.mark.parametrize("config", BASIC_MODEL_CONFIGS)
def test_create_basic_model(config):
    model = ModelFactory.create(config)

    assert isinstance(model, Model)
    assert model.type == config["type"]


@pytest.mark.parametrize("config", DFT_MODEL_CONFIGS)
def test_create_dft_model(config):
    model = ModelFactory.create(config)

    assert isinstance(model, DFTModel)
    assert model.type == "dft"


@pytest.mark.parametrize("config", DFT_MODEL_CONFIGS)
def test_create_from_application_requires_application(config):
    with pytest.raises(ValueError, match="application is required"):
        ModelFactory.create_from_application(config)

