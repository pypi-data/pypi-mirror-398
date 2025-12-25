import json
from importlib import import_module

import jsonschema
from pytest import fixture
from ts_sdk import schemas


@fixture
def config():
    with open("./config.json", encoding="utf-8") as file:
        return json.load(file)


def test_config_schema(config):
    jsonschema.validate(config, schemas.config)


def test_config_functions(config):
    for function_config in config["functions"]:
        compound_name = function_config["function"]
        module_name, function_name = compound_name.split(".")
        assert hasattr(
            import_module(module_name), function_name
        ), f"unable to find function {compound_name}"
        assert function_name == function_config["slug"]
