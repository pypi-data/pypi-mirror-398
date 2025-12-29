def require_non_zero(value: float, name: str) -> None:
    if value == 0:
        raise ValueError(f"{name} must be non-zero")
