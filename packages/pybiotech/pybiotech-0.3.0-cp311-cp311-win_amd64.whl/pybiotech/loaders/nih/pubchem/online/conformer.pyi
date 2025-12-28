from _typeshed import Incomplete
from pybiotech.loaders.nih.pubchem.online.utils import __get_base_url__ as __get_base_url__, __get_optimal_chunk_size__ as __get_optimal_chunk_size__, __get_sliced_list__ as __get_sliced_list__, __get_url_conformers_limit__ as __get_url_conformers_limit__
from pybiotech.loaders.sdf_loader import SDFLoader as SDFLoader
from pybiotech.type.nih.pubchem import ALNPConformer as ALNPConformer

logger: Incomplete

def get_conformer(conformer_ids: list[str], ignore_error: bool = False) -> dict[str, ALNPConformer]: ...
