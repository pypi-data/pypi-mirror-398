WEATHER_DATA = {
    "rome": {"temp_c": 26, "summary": "Sunny"},
    "milan": {"temp_c": 22, "summary": "Cloudy"},
    "zurich": {"temp_c": 18, "summary": "Rain"},
    "london": {"temp_c": 16, "summary": "Windy"},
}

SUPPORTED_CITIES = tuple(sorted(WEATHER_DATA.keys()))


def normalize_city(city: str) -> str:
    return (city or "").strip().lower()


def is_supported_city(city: str) -> bool:
    return normalize_city(city) in WEATHER_DATA


def get_current(city: str):
    return WEATHER_DATA.get(normalize_city(city))


def get_forecast(city: str):
    current = get_current(city)
    if not current:
        return None
    return [
        {"day": "Today", "temp_c": current["temp_c"], "summary": current["summary"]},
        {
            "day": "Tomorrow",
            "temp_c": current["temp_c"] + 1,
            "summary": current["summary"],
        },
        {
            "day": "Next day",
            "temp_c": current["temp_c"] - 1,
            "summary": current["summary"],
        },
    ]


def get_current_for_location(latitude: float, longitude: float):
    """Deterministic demo weather for a location (no external API)."""
    try:
        lat = float(latitude)
        lon = float(longitude)
    except Exception:
        return None

    seed = int(abs(lat * 10) + abs(lon * 10)) % 4
    summaries = ["Sunny", "Cloudy", "Rain", "Windy"]
    summary = summaries[seed]
    temp_c = 16 + (seed * 3)
    return {"temp_c": temp_c, "summary": summary}
