from enum import Enum
from pydantic import BaseModel

class FastSearchType(str, Enum):
    fastidentity = 'fastidentity'
    fastsimilarity_2d = 'fastsimilarity_2d'
    fastsimilarity_3d = 'fastsimilarity_3d'
    fastsubstructure = 'fastsubstructure'
    fastsuperstructure = 'fastsuperstructure'

class FastSearchSubType(str, Enum):
    smiles = 'smiles'
    smarts = 'smarts'
    inchi = 'inchi'
    sdf = 'sdf'
    cid = 'cid'

FASTFORMULA: str

class StructureSearchType(str, Enum):
    substructure = 'substructure'
    superstructure = 'superstructure'
    similarity = 'similarity'
    identity = 'identity'

class StructureSearchSubType(str, Enum):
    smiles = 'smiles'
    inchi = 'inchi'
    sdf = 'sdf'
    cid = 'cid'

class FastSearchType(str, Enum):
    fastidentity = 'fastidentity'
    fastsimilarity_2d = 'fastsimilarity_2d'
    fastsimilarity_3d = 'fastsimilarity_3d'
    fastsubstructure = 'fastsubstructure'
    fastsuperstructure = 'fastsuperstructure'

class FastSearchSubType(str, Enum):
    smiles = 'smiles'
    smarts = 'smarts'
    inchi = 'inchi'
    sdf = 'sdf'
    cid = 'cid'

class XrefSubType(str, Enum):
    RegistryID = 'RegistryID'
    RN = 'RN'
    PubMedID = 'PubMedID'
    MMDBID = 'MMDBID'
    ProteinGI = 'ProteinGI'
    NucleotideGI = 'NucleotideGI'
    TaxonomyID = 'TaxonomyID'
    MIMID = 'MIMID'
    GeneID = 'GeneID'
    ProbeID = 'ProbeID'
    PatentID = 'PatentID'

class MassType(str, Enum):
    molecular_weight = 'molecular_weight'
    exact_mass = 'exact_mass'
    monoisotopic_mass = 'monoisotopic_mass'

class MassMode(str, Enum):
    equals = 'equals'
    range = 'range'

class StructureSearch(BaseModel):
    prefix: StructureSearchType
    subtype: StructureSearchSubType
    @classmethod
    def from_string(cls, s: str) -> StructureSearch: ...

class FastSearch(BaseModel):
    prefix: FastSearchType | None
    subtype: FastSearchSubType | None
    fastformula: bool
    @classmethod
    def from_string(cls, s: str) -> FastSearch: ...

class Xref(BaseModel):
    prefix: str
    subtype: XrefSubType
    @classmethod
    def from_string(cls, s: str) -> Xref: ...

class Mass(BaseModel):
    mass_type: MassType
    mode: MassMode
    value_1: float
    value_2: float | None
    @classmethod
    def check_value_2(cls, v, info): ...
    @classmethod
    def from_string(cls, s: str) -> Mass: ...
