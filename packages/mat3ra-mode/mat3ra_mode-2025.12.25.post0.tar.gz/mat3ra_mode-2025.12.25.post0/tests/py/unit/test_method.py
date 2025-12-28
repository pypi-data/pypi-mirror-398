import pytest
from mat3ra.mode import Method

PSEUDOPOTENTIAL_US_CONFIG = {"type": "pseudopotential", "subtype": "us"}
PSEUDOPOTENTIAL_NC_CONFIG = {"type": "pseudopotential", "subtype": "nc"}
LOCALORBITAL_POPLE_CONFIG = {"type": "localorbital", "subtype": "pople"}

TEST_CONFIGS = [PSEUDOPOTENTIAL_US_CONFIG, PSEUDOPOTENTIAL_NC_CONFIG, LOCALORBITAL_POPLE_CONFIG]

TEST_DATA = {"key": "value"}
TEST_DATA_WITH_SEARCH_TEXT = {"searchText": "test search"}


@pytest.mark.parametrize("config", TEST_CONFIGS)
def test_can_be_created(config):
    method = Method.create(config)
    assert method.type == config["type"]
    assert method.subtype == config["subtype"]


@pytest.mark.parametrize("config", TEST_CONFIGS)
def test_type_property(config):
    method = Method.create(config)
    type_value = method.type

    assert isinstance(type_value, str)
    assert type_value == config["type"]


@pytest.mark.parametrize("config", TEST_CONFIGS)
def test_subtype_property(config):
    method = Method.create(config)
    subtype_value = method.subtype

    assert subtype_value is not None
    assert subtype_value == config["subtype"]


@pytest.mark.parametrize("config", TEST_CONFIGS)
def test_data_property(config):
    config_with_data = {**config, "data": TEST_DATA}
    method = Method.create(config_with_data)

    data = method.data
    assert isinstance(data, dict)
    assert data["key"] == "value"


@pytest.mark.parametrize("config", TEST_CONFIGS)
def test_set_data(config):
    method = Method.create(config)
    method.data = {"test": "data"}

    assert method.data["test"] == "data"


@pytest.mark.parametrize("config", TEST_CONFIGS)
def test_set_search_text(config):
    method = Method.create(config)
    method.data = TEST_DATA_WITH_SEARCH_TEXT

    assert method.search_text == "test search"


@pytest.mark.parametrize("config", TEST_CONFIGS)
def test_to_json(config):
    config_with_data = {**config, "data": TEST_DATA}
    method = Method.create(config_with_data)

    json_data = method.to_dict()
    assert json_data["type"] == config["type"]
    assert json_data["subtype"] == config["subtype"]
    assert "data" in json_data


@pytest.mark.parametrize("config", TEST_CONFIGS)
def test_clone_without_data(config):
    config_with_data = {**config, "data": TEST_DATA}
    method = Method.create(config_with_data)

    cloned = method.clone_without_data()
    assert cloned.type == method.type
    assert cloned.data == {}
