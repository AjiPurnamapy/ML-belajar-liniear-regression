def convert_ym_to_years(ym: float) -> float:
    years = int(ym)
    months = round((ym - years) * 10)
    return round(years + months / 12, 4)