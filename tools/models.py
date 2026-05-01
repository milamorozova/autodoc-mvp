from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ParameterInfo:
    name: str
    kind: str
    annotation: Optional[str] = None
    default: Optional[str] = None


@dataclass
class SignatureInfo:
    name: str
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_annotation: Optional[str] = None
    is_async: bool = False


@dataclass
class ExceptionInfo:
    name: str
    details: Optional[str] = None


@dataclass
class ApiNode:
    node_type: str  # module | class | function | method
    name: str
    qualname: str
    lineno: int
    end_lineno: int
    file_path: str
    language: str = "python"
    signature: Optional[SignatureInfo] = None
    docstring: Optional[str] = None
    logic: Optional[str] = None          # <-- НОВОЕ: логика работы от LLM
    decorators: List[str] = field(default_factory=list)
    exceptions: List[ExceptionInfo] = field(default_factory=list)
    children: List["ApiNode"] = field(default_factory=list)


@dataclass
class ModuleDocModel:
    component_name: str
    source_path: str
    language: str
    version: str
    status: str
    date: str
    root: ApiNode

    espd_code: str = ""
    cid: str = ""
    marketplace_url: str = ""
    short_description: str = ""
    component_use_category: str = ""
    component_type: str = ""
    tags: str = ""
    authors: List[str] = field(default_factory=list)
    organizations: List[str] = field(default_factory=list)
    links: str = ""

    enriched: bool = False
    enriched_idl: Optional[str] = None