from _typeshed import Incomplete
from enum import Enum
from pydantic import BaseModel

class EInputType(str, Enum):
    CID = 'cid'
    SMILES = 'smiles'
    INCHI = 'InChI'

class EOperationType(str, Enum):
    RECORD = 'record'
    CIDS = 'cids'
    SIDS = 'sids'

class EOutputType(str, Enum):
    SDF = 'SDF'
    JSON = 'JSON'
    XML = 'XML'
    ASNB = 'ASNB'
    ASNT = 'ASNT'
    TXT = 'TXT'
    PNG = 'PNG'

class ALNPConformer(BaseModel):
    PUBCHEM_COMPOUND_CID: str
    PUBCHEM_CONFORMER_ID: str
    ROW: str
    model_config: Incomplete
    def convert_pubchem_cid(cls, v): ...

class ALNPCompound(BaseModel):
    PUBCHEM_COMPOUND_CID: str
    ROW: str
    CONFORMER_ID: list[str] | None
    CONFORMERS: dict[str, ALNPConformer] | None
    model_config: Incomplete
    def convert_pubchem_cid(cls, v): ...
