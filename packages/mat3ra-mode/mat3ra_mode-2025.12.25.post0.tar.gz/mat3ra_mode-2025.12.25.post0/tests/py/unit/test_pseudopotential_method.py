import pytest
from mat3ra.mode import PseudopotentialMethod

PSEUDOPOTENTIAL_US_CONFIG = {"type": "pseudopotential", "subtype": "us"}
PSEUDOPOTENTIAL_NC_CONFIG = {"type": "pseudopotential", "subtype": "nc"}

TEST_CONFIGS = [PSEUDOPOTENTIAL_US_CONFIG, PSEUDOPOTENTIAL_NC_CONFIG]

TEST_PSEUDO_DATA = {"pseudo": [{"element": "Si"}]}
TEST_ALL_PSEUDO_DATA = {"allPseudo": [{"element": "Si"}, {"element": "O"}]}
TEST_COMBINED_PSEUDO_DATA = {
    "pseudo": [{"element": "Si"}],
    "allPseudo": [{"element": "Si"}, {"element": "O"}],
}


@pytest.mark.parametrize("config", TEST_CONFIGS)
def test_can_be_created(config):
    method = PseudopotentialMethod.create(config)
    assert method.type == "pseudopotential"


@pytest.mark.parametrize("config", TEST_CONFIGS)
def test_pseudo_property(config):
    config_with_data = {**config, "data": TEST_PSEUDO_DATA}
    method = PseudopotentialMethod.create(config_with_data)

    pseudo = method.pseudo
    assert isinstance(pseudo, list)
    assert len(pseudo) == 1
    assert pseudo[0]["element"] == "Si"


@pytest.mark.parametrize("config", TEST_CONFIGS)
def test_all_pseudo_property(config):
    config_with_data = {**config, "data": TEST_ALL_PSEUDO_DATA}
    method = PseudopotentialMethod.create(config_with_data)

    all_pseudo = method.all_pseudo
    assert isinstance(all_pseudo, list)
    assert len(all_pseudo) == 2


@pytest.mark.parametrize("config", TEST_CONFIGS)
def test_to_dict_excludes_all_pseudo(config):
    config_with_data = {**config, "data": TEST_COMBINED_PSEUDO_DATA}
    method = PseudopotentialMethod.create(config_with_data)

    json_data = method.to_dict()
    assert "allPseudo" not in json_data["data"]
    assert "pseudo" in json_data["data"]

