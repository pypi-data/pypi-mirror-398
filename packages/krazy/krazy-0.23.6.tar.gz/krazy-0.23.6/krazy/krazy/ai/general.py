from pydantic import BaseModel, Field, field_validator, create_model
from typing import Dict, Any, List, Optional
import pandas as pd
import keyring as kr

def chunk_list(lst, chunk_size):
    """
    Splits a list into smaller chunks of specified size.

    Args:
        lst (list): The original list to chunk.
        chunk_size (int): The number of items per chunk.

    Returns:
        Generator[list]: Yields chunks of the list.
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def chunk_dict(d: dict, chunk_size: int):
    """
    Splits a dictionary into smaller dictionaries with specified number of items.

    Args:
        d (dict): The original dictionary to chunk.
        chunk_size (int): The number of key-value pairs per chunk.

    Returns:
        Generator[dict]: Yields chunks of the dictionary.
    """
    items = list(d.items())
    for i in range(0, len(items), chunk_size):
        yield dict(items[i:i + chunk_size])

def chunk_dataframe(df: pd.DataFrame, chunk_size: int):
    """
    Splits a DataFrame into smaller chunks of specified row size.

    Args:
        df (pd.DataFrame): The original DataFrame to chunk.
        chunk_size (int): The number of rows per chunk.

    Returns:
        Generator[pd.DataFrame]: Yields chunked DataFrames.
    """
    for i in range(0, len(df), chunk_size):
        yield df.iloc[i:i + chunk_size]

def extract_dynamic_schema(model: BaseModel) -> Dict[str, Any]:
    model_schema = model.model_json_schema()
    top_field_name, top_field_props = list(model_schema['properties'].items())[0]

    item_ref = top_field_props['items']['$ref'].split('/')[-1]
    item_schema = model_schema['$defs'][item_ref]['properties']

    # Map types into your expected output
    def map_type(prop: Dict[str, Any]) -> Dict[str, str]:
        return {
            'type': prop.get('type', 'str'),
            'title': prop.get('title', ''),
            'description': prop.get('description', '')
        }

    item_fields = {
        k: map_type(v)
        for k, v in item_schema.items()
    }

    return {
        top_field_name: {
            'type': 'list',
            'items': item_fields
        }
    }

class QueryRequest(BaseModel):
    query: str
    output_schema: Optional[Dict[str, Any]] = None
    use_memory: Optional[bool] = True
    save_chat_history: Optional[bool] = True
    llm: Optional[str] = "azure"

def build_dynamic_schema_recursive(name: str, schema_def: Dict[str, Any]) -> BaseModel:
    type_map = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict
    }

    fields = {}

    for field_name, spec in schema_def.items():
        if isinstance(spec, dict) and "type" in spec:
            field_type_str = spec["type"]
            if field_type_str == "list" and "items" in spec:
                item_spec = spec["items"]
                if isinstance(item_spec, dict):
                    sub_model = build_dynamic_schema_recursive(f"{name}_{field_name}_Item", item_spec)
                    field_type = List[sub_model]
                else:
                    field_type = List[type_map.get(item_spec, str)]
            elif field_type_str == "dict" and "keys" in spec:
                field_type = Dict[str, type_map.get(spec["keys"], str)]
            else:
                field_type = type_map.get(field_type_str, str)

            field_args: Dict[str, Any] = {}
            if "title" in spec:
                field_args["title"] = spec["title"]
            if "description" in spec:
                field_args["description"] = spec["description"]
            default = spec.get("default", ...)

            fields[field_name] = (field_type, Field(default, **field_args))

        elif isinstance(spec, dict):
            sub_model = build_dynamic_schema_recursive(f"{name}_{field_name}", spec)
            fields[field_name] = (sub_model, ...)
        else:
            fields[field_name] = (type_map.get(spec, str), ...)

    return create_model(name, **fields)

def credentials()->List[Dict[str, str]]:
    postgres_user = kr.get_password('postgres_user', 'user')
    tavily_username = 'api_key_' + str(kr.get_password('tavily', 'user'))

    credentials_dict = {
        'open_ai_api_key': kr.get_password('pxv_open_ai', 'api_key'),
        'azure_version': kr.get_password('pxv_open_ai', 'azure_version'),
        'azure_endpoint': kr.get_password('pxv_open_ai', 'endpoint'),
        'embedding_model': 'text-embedding-ada-002',
        'model': 'gpt-4o',
        'model_32k': 'gpt-4-32k',
        'postgres_dbname': 'postgres',
        'postgres_host': kr.get_password('pxv_postgres', 'host'),
        'postgres_password': kr.get_password('aws-postgres', str(postgres_user)),
        'postgres_port': '5432',
        'postgres_user': postgres_user,
        'summary_azure_model': 'gpt-35-turbo-16k',
        'tavily_api_key': kr.get_password('tavily', tavily_username)
        }
    postgres_params = {
        'dbname': credentials_dict['postgres_dbname'],
        'host': credentials_dict['postgres_host'],
        'password': credentials_dict['postgres_password'],
        'port': credentials_dict['postgres_port'],
        'user': credentials_dict['postgres_user']
    }
    return [credentials_dict, postgres_params]