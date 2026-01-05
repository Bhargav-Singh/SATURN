from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class AuthContext:
    auth_type: str
    company_id: str
    user_id: Optional[str]
    role: Optional[str]
    scopes: List[str]
