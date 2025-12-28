from typing import Any, Dict

from mat3ra.standata.model_tree import ModelTreeStandata

from ..model import Model
from .dft import DFTModel


class ModelFactory:
    DFTModel = DFTModel
    Model = Model

    @classmethod
    def create(cls, config: Dict[str, Any]) -> Model:
        model_type = config.get("type", "")

        if model_type == "dft":
            return cls.DFTModel.create(config)

        return cls.Model.create(config)

    @classmethod
    def create_from_application(cls, config: Dict[str, Any]) -> Model:
        application = config.get("application")
        if not application:
            raise ValueError("ModelFactory.create_from_application: application is required")

        model_type = ModelTreeStandata().get_default_model_type_for_application(application)
        if not model_type:
            raise ValueError(f"ModelFactory.create_from_application: cannot determine model type: {model_type}")

        return cls.create({**config, "type": model_type})
