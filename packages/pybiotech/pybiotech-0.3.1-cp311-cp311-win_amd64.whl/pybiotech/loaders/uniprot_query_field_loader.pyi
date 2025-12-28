from pathlib import Path
from pybiotech.classes.uniprot.https.uniprot.org.uniprot_query_field import QueryField as QueryField

class UniProtQueryFieldLoader:
    @staticmethod
    def load_query_fields(json_input: Path | str | bytes) -> list[QueryField]: ...
    @staticmethod
    def build_query(field: QueryField, value: str) -> str: ...
    @staticmethod
    def find_field_by_term(fields: list[QueryField], term: str) -> QueryField | None: ...
