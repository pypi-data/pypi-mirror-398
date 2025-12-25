import re


def normalize_city_name(city: str) -> str:
    if not isinstance(city, str):
        return city
    city = city.strip()
    city = re.sub(r"\b(Boro|Borough|Twp|Township|City|Village|Vlg)\b", "", city, flags=re.IGNORECASE)
    city = re.sub(r"\s+", " ", city).strip()
    return city
