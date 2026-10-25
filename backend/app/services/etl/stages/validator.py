"""Stage 1: Validate the file before parsing."""

from pathlib import Path


class ValidationResult:
    def __init__(self, valid: bool = True, errors: list[str] | None = None):
        self.valid = valid
        self.errors = errors or []


def validate_file(file_path: str, allowed_extensions: set[str] | None = None) -> ValidationResult:
    if allowed_extensions is None:
        allowed_extensions = {".csv", ".xlsx", ".xls"}

    path = Path(file_path)

    if not path.exists():
        return ValidationResult(valid=False, errors=["File not found"])

    if path.stat().st_size == 0:
        return ValidationResult(valid=False, errors=["Empty file"])

    ext = path.suffix.lower()
    if ext not in allowed_extensions:
        return ValidationResult(
            valid=False,
            errors=[f"Format '{ext}' not supported. Use: {', '.join(allowed_extensions)}"],
        )

    return ValidationResult()
