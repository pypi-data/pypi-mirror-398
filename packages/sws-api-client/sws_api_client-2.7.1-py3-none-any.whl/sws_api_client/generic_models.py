from typing import List, Optional
from pydantic import BaseModel


class Multilanguage(BaseModel):
    en: str
    fr: Optional[str] = None
    es: Optional[str] = None
    ar: Optional[str] = None
    ru: Optional[str] = None
    zh: Optional[str] = None

class Code(BaseModel, extra="allow"):
    id: str
    label: Multilanguage
    children: Optional[List[str]] = []

class Flag(BaseModel, extra="allow"):
    value: str
    description: str