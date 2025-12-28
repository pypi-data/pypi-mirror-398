import pytest
from mat3ra.mode import DFTModel, Method

DFT_GGA_CONFIG = {"type": "dft", "subtype": "gga"}
DFT_GGA_WITH_FUNCTIONAL = {**DFT_GGA_CONFIG, "functional": "pbe"}
PSEUDOPOTENTIAL_NC_METHOD = {"type": "pseudopotential", "subtype": "nc"}
PSEUDOPOTENTIAL_US_METHOD = {"type": "pseudopotential", "subtype": "us"}

TEST_REFINERS = ["hse"]
TEST_MODIFIERS = ["soc"]


@pytest.mark.parametrize("method_config", [PSEUDOPOTENTIAL_NC_METHOD, PSEUDOPOTENTIAL_US_METHOD])
def test_method_returns_method_instance(method_config):
    config = {**DFT_GGA_WITH_FUNCTIONAL, "method": method_config}
    dft_model = DFTModel.create(config)

    method_value = dft_model.method

    assert method_value is not None
    assert isinstance(method_value, Method)

    assert hasattr(method_value, "data")
    assert hasattr(method_value, "search_text")


def test_functional_property():
    dft_model = DFTModel.create(DFT_GGA_WITH_FUNCTIONAL)

    functional = dft_model.functional
    assert functional is not None


def test_refiners_property():
    config = {**DFT_GGA_WITH_FUNCTIONAL, "refiners": TEST_REFINERS}
    dft_model = DFTModel.create(config)

    refiners = dft_model.refiners
    assert isinstance(refiners, list)
    assert len(refiners) == 1


def test_modifiers_property():
    config = {**DFT_GGA_WITH_FUNCTIONAL, "modifiers": TEST_MODIFIERS}
    dft_model = DFTModel.create(config)

    modifiers = dft_model.modifiers
    assert isinstance(modifiers, list)
    assert len(modifiers) == 1


def test_group_slug():
    dft_model = DFTModel.create(DFT_GGA_CONFIG)

    slug = dft_model.group_slug
    assert isinstance(slug, str)
    assert "dft" in slug
    assert "gga" in slug


def test_to_dict_includes_functional():
    dft_model = DFTModel.create(DFT_GGA_WITH_FUNCTIONAL)

    json_data = dft_model.to_dict()
    assert "functional" in json_data



