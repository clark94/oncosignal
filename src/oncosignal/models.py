from datetime import datetime, timezone
import hashlib
import json
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


class Record(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(min_length=1, max_length=120)
    source: Literal['clinicaltrials', 'pubmed', 'demo']
    source_id: str
    title: str = Field(min_length=3, max_length=10000)
    text: str = Field(max_length=200000)
    url: str
    kind: Literal['trial', 'publication']
    updated: str = ''
    retrieved_at: str = Field(default_factory=now)
    drugs: list[str] = Field(default_factory=list)
    indications: list[str] = Field(default_factory=list)
    phase: str = ''
    status: str = ''
    sponsor: str = ''
    nct_ids: list[str] = Field(default_factory=list)
    doi: str = ''
    demo: bool = False
    review: Literal['pending', 'approved', 'rejected'] = 'pending'
    rights: str = 'Vérifier les conditions de réutilisation de la source.'

    @field_validator('url')
    @classmethod
    def safe_url(cls, value):
        if not value.startswith('https://'):
            raise ValueError('URL HTTPS requise')
        return value

    def scientific_content(self):
        return self.model_dump(exclude={'retrieved_at', 'review'})

    @property
    def content_hash(self):
        return digest(self.scientific_content())
