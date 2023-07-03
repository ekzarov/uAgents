import hashlib
from typing import Type, Union, Dict

from pydantic import BaseModel
from pydantic.schema import model_schema, default_ref_template


class Model(BaseModel):
    @staticmethod
    def _remove_descriptions(
        model: Type["Model"], orig_descriptions: Dict[str, Union[str, Dict]]
    ):
        for _, field in model.__fields__.items():
            if field.field_info and field.field_info.description:
                orig_descriptions[field.name] = field.field_info.description
                field.field_info.description = None
            elif issubclass(field.type_, Model):
                orig_descriptions[field.name] = {}
                Model._remove_descriptions(field.type_, orig_descriptions[field.name])

    @staticmethod
    def _restore_descriptions(
        model: Type["Model"], orig_descriptions: Dict[str, Union[str, Dict]]
    ):
        for _, field in model.__fields__.items():
            if (
                field.field_info
                and field.name in orig_descriptions
                and not issubclass(field.type_, Model)
            ):
                field.field_info.description = orig_descriptions[field.name]
            elif issubclass(field.type_, Model):
                Model._restore_descriptions(field.type_, orig_descriptions[field.name])

    @staticmethod
    def _refresh_schema_cache(model: Type["Model"]):
        schema = model_schema(model, True, default_ref_template)
        model.__schema_cache__[(True, default_ref_template)] = schema

    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        orig_descriptions: Dict[str, Union[str, Dict]] = {}
        obj_for_descr_remove = model if isinstance(model, type) else model.__class__
        Model._remove_descriptions(obj_for_descr_remove, orig_descriptions)
        digest = (
            hashlib.sha256(
                model.schema_json(indent=None, sort_keys=True).encode("utf8")
            )
            .digest()
            .hex()
        )
        Model._restore_descriptions(obj_for_descr_remove, orig_descriptions)
        Model._refresh_schema_cache(obj_for_descr_remove)
        return f"model:{digest}"


class ErrorMessage(Model):
    error: str
