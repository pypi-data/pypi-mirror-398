import abc
from _typeshed import Incomplete
from abc import abstractmethod
from enum import Enum
from pybiotech.classes.nih.https.pubchem.section.domain import ENUMDomain as ENUMDomain
from pydantic import BaseModel

class ENUNameSpace(str, Enum):
    cid = 'cid'
    name = 'name'
    smiles = 'smiles'
    inchi = 'inchi'
    sdf = 'sdf'
    inchikey = 'inchikey'
    formula = 'formula'
    listkey = 'listkey'

DOMAIN_NAMESPACE_MAP: Incomplete

class NamespaceModel(BaseModel, metaclass=abc.ABCMeta):
    value: str
    domain: ENUMDomain
    @abstractmethod
    def validate_namespace_and_domain(self): ...
    def as_url_part(self): ...
