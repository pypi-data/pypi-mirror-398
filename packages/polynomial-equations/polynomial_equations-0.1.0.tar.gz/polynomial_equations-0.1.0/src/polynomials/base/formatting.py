def format_equation(terms: list[str]) -> str:
    expr = " ".join(terms).replace("+ -", "- ")
    return expr.strip()
