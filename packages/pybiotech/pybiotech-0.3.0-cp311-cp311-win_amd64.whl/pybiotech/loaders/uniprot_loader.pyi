from _typeshed import Incomplete
from pathlib import Path
from pybiotech.classes.uniprot.https.uniprot.org.uniprot import Entry as Entry
from typing import Iterator

class UniProtLoader:
    expected_ns: str
    parser: Incomplete
    def __init__(self, xml_input: Path | str | bytes) -> None: ...
    def iterate_entries(self) -> Iterator[Entry]: ...
    @staticmethod
    def detect_namespace(xml_input: Path | str | bytes) -> tuple[str, str]: ...
