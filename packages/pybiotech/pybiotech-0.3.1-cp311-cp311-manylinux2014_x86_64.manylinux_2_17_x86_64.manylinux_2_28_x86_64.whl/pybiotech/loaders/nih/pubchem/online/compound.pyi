from _typeshed import Incomplete
from annotated_types import Len as Len
from pybiotech.loaders.nih.pubchem.online.conformer import get_conformer as get_conformer
from pybiotech.loaders.nih.pubchem.online.utils import __get_base_url__ as __get_base_url__, __get_optimal_chunk_size__ as __get_optimal_chunk_size__, __get_sliced_list__ as __get_sliced_list__, __get_url_compound_limit__ as __get_url_compound_limit__, __get_url_conformers_limit__ as __get_url_conformers_limit__
from pybiotech.loaders.sdf_loader import SDFLoader as SDFLoader
from pybiotech.type.nih.pubchem import ALNPCompound as ALNPCompound, ALNPConformer as ALNPConformer, EInputType as EInputType, EOperationType as EOperationType, EOutputType as EOutputType
from typing import Callable

logger: Incomplete
url_compound_limit: int

def __get_compound__(all_cids: list[int | str], ignore_error: bool = False, callback: Callable[[int, int, str], None] | None = None) -> dict[str, ALNPCompound]: ...
def get_compound(cid_list: list[int | str], include_conformer: bool = False, callback: Callable[[int, int, str], None] | None = None, ignor_error: bool = False) -> dict[str, ALNPCompound]: ...
def get_compound_conformer_ids(all_cids: list[int | str], ignore_error: bool = False, callback: Callable[[int, int, str], None] | None = None) -> dict[str, list[str]]: ...
def get_similarity_compound(input: EInputType, value: str | int, operation: EOperationType, output: EOutputType, threshold: int = 90, max_records: int = 10) -> list[str]: ...
