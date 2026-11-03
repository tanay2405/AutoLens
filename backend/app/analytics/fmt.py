def billions(x: float) -> str:
    sign = "-" if x < 0 else ""
    return f"{sign}${abs(x) / 1e9:,.1f}B"