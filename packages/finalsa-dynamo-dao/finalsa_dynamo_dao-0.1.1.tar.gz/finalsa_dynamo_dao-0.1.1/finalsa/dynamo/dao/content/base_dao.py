from .base import (
    is_valid_property, clean_list,
    translate_model_to_dynamo_model, tranlate_dynamo_model_to_model,
    get_valid_value_from_annotation)


def parse_dao_to_dict(v):
    if isinstance(v, BaseDao):
        return None
    elif isinstance(v, list):
        helper = clean_list([parse_dao_to_dict(v) for v in v])
        if len(helper) == 0:
            return None
        return helper
    elif isinstance(v, dict):
        result = {}
        for k, val in v.items():
            value = parse_dao_to_dict(val)
            if value is not None:
                result[k] = value
        if len(result) == 0:
            return None
        return result
    else:
        return v


class BaseDao():

    def __init__(self, **kwargs) -> None:
        for attribute, annotation in self.__class__.__annotations__.items():
            if is_valid_property(attribute):
                setattr(self, attribute, get_valid_value_from_annotation(annotation))
        for key, val in kwargs.items():
            setattr(self, key, val)

    def dict(self):
        result_items = {}
        for k, v in self.__dict__.items():
            if not is_valid_property(k):
                continue
            value = parse_dao_to_dict(v)
            if value is None:
                continue
            result_items[k] = value
        r = translate_model_to_dynamo_model(result_items)
        return r

    def reverse(self, ):
        d = self.dict()
        sk = d['SK']
        d['SK'] = d['PK']
        d['PK'] = sk
        return d

    @classmethod
    def from_dynamo_model(cls, dict: dict, **kwargs):
        d = tranlate_dynamo_model_to_model(dict)
        d = {**d, **kwargs}
        return cls(**d)

    def __str__(self) -> str:
        return str(self.dict())
