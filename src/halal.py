HARAM_SECTORS = [
    "Banking",
    "Gambling",
    "Alcohol",
    "Tobacco",
    "Adult Entertainment"
]

def is_halal(sector):
    return sector not in HARAM_SECTORS