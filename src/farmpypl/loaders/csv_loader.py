import csv
from pathlib import Path
from typing import Union
from farmpypl.data_validation import FarmProfileInput
from pydantic import ValidationError


class CSVLoadingError(Exception):
    """Custom exception raised when CSV loading or validation fails."""
    pass


def load_profiles(file_path: Union[str, Path]) -> list[FarmProfileInput]:
    """Read a farm profile CSV and return one checked profile per data row."""

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found at: {file_path}")

    with file_path.open(newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))

    profiles: list[FarmProfileInput] = []

    for row_num, row in enumerate(rows, start=2):
        try:
            profiles.append(FarmProfileInput.model_validate(row))
        except ValidationError as err:
            raise CSVLoadingError(f"Row {row_num} of {file_path.name}: {err}") from err
    
    return profiles