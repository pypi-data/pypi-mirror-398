from pydantic import BaseModel
from typing import Literal, List, Union
from datetime import datetime
from polymath_schemas.graph import VerificationLevel
from polymath_schemas.node_work import NodePatchRead, NodeCommentRead

class PolymathBaseRead(BaseModel):
    uid: str
    author_id: int
    created_at: datetime
    updated_at: datetime
    human_rep: str | None = None
    lean_rep: str | None = None
    verification: VerificationLevel

class StatementRead(PolymathBaseRead):
    node_type: Literal["Statement"] = "Statement"  # Discriminator
    category: str

class ImplicationRead(PolymathBaseRead):
    node_type: Literal["Implication"] = "Implication" # Discriminator
    logic_operator: str

class UnifiedNodeResponse(BaseModel):
    node_data: Union[StatementRead, ImplicationRead] 
    patches: List[NodePatchRead]
    comments: List[NodeCommentRead]