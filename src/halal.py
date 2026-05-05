HARAM_KEYWORDS = [
    "financial services",
    "banks",
    "insurance",
    "gambling",
    "alcohol",
    "tobacco",
    "adult entertainment",
]

SAFE_SECTORS = {
    "basic materials",
    "consumer defensive",
    "healthcare",
    "industrials",
    "technology",
    "utilities",
}

BLOCKED_SECTORS = {
    "communication services",
    "consumer cyclical",
    "energy",
    "real estate",
}


def evaluate_halal(sector):
    if not sector:
        return {
            "is_halal": False,
            "status": "most_probably_no",
            "reason": "Sector unavailable",
        }

    normalized_sector = sector.strip().lower()

    for keyword in HARAM_KEYWORDS:
        if keyword in normalized_sector:
            return {
                "is_halal": False,
                "status": "most_probably_no",
                "reason": f"Most probably NO: {sector}",
            }

    if normalized_sector in SAFE_SECTORS:
        return {
            "is_halal": True,
            "status": "needs_to_be_validate",
            "reason": f"No obvious prohibited exposure in {sector}",
        }

    if normalized_sector in BLOCKED_SECTORS:
        return {
            "is_halal": False,
            "status": "most_probably_no",
            "reason": f"Most probably NO: {sector}",
        }

    return {
        "is_halal": False,
        "status": "most_probably_no",
        "reason": f"Most probably NO: sector not clearly classified ({sector})",
    }


def is_halal(sector):
    return evaluate_halal(sector)["is_halal"]