# core/validator.py
from pydantic import BaseModel, Field, field_validator
from typing import Literal
import yaml

class ResourceSpec(BaseModel):
    cpu: str
    memory: str
    replicas: int = Field(..., ge=1, le=20)

class NetworkSpec(BaseModel):
    port: int = Field(..., ge=1, le=65535)
    protocol: Literal["TCP", "UDP", "HTTP", "HTTPS", "GRPC"]
    expose: bool = False

class NFSpec(BaseModel):
    name: str = Field(..., min_length=2, max_length=64)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    nf_type: Literal["VNF", "CNF", "PNF"]
    environment: Literal["dev", "staging", "prod"]
    owner: str = Field(..., min_length=2)
    description: str = Field(default="")
    resources: ResourceSpec
    network: NetworkSpec
    tags: list = []

    @field_validator("name")
    @classmethod
    def name_must_be_slug(cls, v):
        import re
        if not re.match(r"^[a-z0-9\-]+$", v):
            raise ValueError("name must be lowercase, hyphens only")
        return v

def validate_spec(file_path):
    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
        spec = NFSpec(**data)
        return True, spec, "OK"
    except FileNotFoundError:
        return False, None, f"File not found: {file_path}"
    except yaml.YAMLError as e:
        return False, None, f"YAML error: {e}"
    except Exception as e:
        return False, None, f"Validation error: {e}"

def validate_spec_dict(data):
    try:
        spec = NFSpec(**data)
        return True, spec, "OK"
    except Exception as e:
        return False, None, str(e)