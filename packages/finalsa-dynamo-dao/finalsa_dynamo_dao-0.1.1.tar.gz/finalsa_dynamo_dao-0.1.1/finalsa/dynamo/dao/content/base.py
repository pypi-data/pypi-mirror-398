from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from datetime import datetime, date
from decimal import Context
from uuid import UUID


def clean_list(items: list):
    result = []
    for v in items:
        if not v:
            continue
        result.append(v)
    return result


def is_valid_property(k: str):
    if k.startswith('_'):
        return False
    if k == 'id':
        return False
    return True


def translate_model_to_dynamo_model(dict: dict):
    serializer = TypeSerializer()

    def to_supported_type(v):
        if isinstance(v, datetime):
            return v.isoformat()
        if isinstance(v, float):
            r =  Context(prec=10).create_decimal_from_float(v)
            return r
        if isinstance(v, date):
            return v.isoformat()
        if isinstance(v, UUID):
            return str(v)
        return v
    return {k: serializer.serialize(to_supported_type(v)) for k, v in dict.items()}


def tranlate_dynamo_model_to_model(dict: dict):
    serializer = TypeDeserializer()
    return {k: serializer.deserialize(v) for k, v in dict.items()}


def get_valid_value_from_annotation(annotation):
    if annotation == str:
        return None
    if annotation == int:
        return 0
    return None
