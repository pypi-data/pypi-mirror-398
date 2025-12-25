from finalsa.dynamo.dao import BaseDao
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


class UserBaseDao(BaseDao):
    PK: str = "test"
    SK: str = "test"
    name: str


def test_pk():
    dao = UserBaseDao(
        PK="test",
        SK="test",
    )
    assert dao.PK == "test"

    d = dao.dict()

    assert d['PK'] == {"S": "test"}


def test_missing_attribute():
    dao = UserBaseDao(
        PK="test",
        SK="test",
    )
    assert dao.name is None

    d = dao.dict()

    assert d['PK'] == {"S": "test"}
    assert 'name' not in d


def test_extra_attribute():
    dao = UserBaseDao(
        PK="test",
        SK="test",
        test="test",
    )
    assert dao.name is None

    d = dao.dict()

    assert d['PK'] == {"S": "test"}
    assert 'test' in d
