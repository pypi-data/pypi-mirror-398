from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Protocol


class Cacheable(Protocol):
    name: str
    coreData: Any
    isVersionRequire: ClassVar[bool]
    dataVersion: int | None
    payload: Dict[str, Any] | None


@dataclass
class GithubTemplateReference(Cacheable):
    name: str
    coreData: str
    isVersionRequire: ClassVar[bool] = False
    dataVersion: int | None = None
    payload: Dict[str, Any] | None = None

@dataclass
class GithubTemplate(Cacheable):
    name: str
    coreData: bytes
    isVersionRequire: ClassVar[bool] = True
    dataVersion: int | None
    payload: Dict[str,Any] | None
