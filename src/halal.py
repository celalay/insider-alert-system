DEFINITELY_HARAM_KEYWORDS = [
    "financial services",
    "bank",
    "banks",
    "insurance",
    "credit services",
    "capital markets",
    "asset management",
    "gambling",
    "alcohol",
    "tobacco",
    "adult entertainment",
    "porn",
]


def evaluate_halal(sector):
    if not sector:
        return {
            "is_halal": True,
            "status": "needs_to_be_validate",
            "reason": "Sector unavailable: manual Shariah review required",
        }

    normalized_sector = sector.strip().lower()

    for keyword in DEFINITELY_HARAM_KEYWORDS:
        if keyword in normalized_sector:
            return {
                "is_halal": False,
                "status": "most_probably_no",
                "reason": f"Most probably NO: clearly prohibited exposure in {sector}",
            }

    return {
        "is_halal": True,
        "status": "needs_to_be_validate",
        "reason": f"Needs review: {sector} is not in definitive-haram list",
    }


def is_halal(sector):
    return evaluate_halal(sector)["is_halal"]