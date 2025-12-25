Dynamo Dao

## Description

This is a simple DynamoDB Dao that can be used to interact with DynamoDB. It is a simple wrapper around the AWS SDK for DynamoDB.

## Installation

```bash
pip install finalsa-dynamo-dao
```

## Usage

```python
from finalsa.dynamo.dao import DynamoDao

# Create a new model and its dao

class MyModelDao(DynamoDao):
    id:str
    name:str
    age:int
    created_at:datetime

class MyModelDao(DynamoDao):
    PK:str
    name:str
    age:int
    created_at:datetime
    ttl:int

# Create a mapper
def my_mapper(item:dict) -> MyModelDao:
    return MyModelDao(**item)

# Create a reverse mapper

def my_reverse_mapper(model:MyModelDao) -> dict:
    return model.dict()

```
