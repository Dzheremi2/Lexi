# pylint: disable-all
def export_database(path: str) -> None: ...
def import_database(zip_path: str) -> None: ...
def proof_of_content(zip_path: str) -> bool: ...
def incorrect_archive_panic(*_args) -> None: ...
