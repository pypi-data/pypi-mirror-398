from pydantic import BaseModel
from typing import Optional, Literal, List

class CreateNode(BaseModel):
    human_rep: str
    lean_rep: str 
    verification: Optional[int] 
    tags: List[str] = []

class CreateStatement(CreateNode):
    category: Literal['Definition', 'Theorem', 'Axiom', 'Lemma']

class CreateImplication(CreateNode):
    logic_op: Optional[Literal['AND', 'OR']]
    premises_ids: list[str]
    concludes_ids: list[str]

class NodePatchRequest(BaseModel):
    human_rep: Optional[str] = None
    lean_rep: Optional[str] = None
    verification: Optional[int] = None
