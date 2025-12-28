from enum import Enum
from pydantic import BaseModel

class ENUMDomain(str, Enum):
    substance = 'substance'
    compound = 'compound'
    assay = 'assay'
    gene = 'gene'
    protein = 'protein'
    pathway = 'pathway'
    taxonomy = 'taxonomy'
    cell = 'cell'
    sources = 'sources'
    sourcetable = 'sourcetable'
    conformers = 'conformers'
    annotations = 'annotations'
    classification = 'classification'
    standardize = 'standardize'
    periodictable = 'periodictable'

class DomainModel(BaseModel):
    value: ENUMDomain
    def __init__(self, value: str) -> None: ...
    @classmethod
    def validate_domain(cls, v): ...
    def as_url_part(self): ...
