from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class Settings:
    workspace: Path
    admin_token: str = ''
    private: bool = False

    @classmethod
    def from_env(cls):
        token = os.getenv('ONCO_ADMIN_TOKEN', '')
        private = os.getenv('ONCO_PRIVATE', '0') == '1'
        if token and len(token) < 24:
            raise ValueError('ONCO_ADMIN_TOKEN doit contenir au moins 24 caractères.')
        if private and not token:
            raise ValueError('Mode privé : ONCO_ADMIN_TOKEN obligatoire.')
        return cls(Path(os.getenv('ONCO_WORKSPACE', 'workspace')).resolve(), token, private)
