HARAM_SECTORS = [
    "Financial Services",
    "Banks",
    "Insurance",
    "Gambling",
    "Alcohol",
    "Tobacco",
    "Adult Entertainment"
]


def is_halal(sector):
    if not sector:
        return False

    for haram in HARAM_SECTORS:
        if haram.lower() in sector.lower():
            return False

    return True