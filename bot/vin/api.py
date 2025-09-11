# bot/vin/api.py
from .mock import MOCK_VIN

def get_sizes_by_vin(vin: str) -> list[str]:
    vin = (vin or "").strip().upper()
    rec = MOCK_VIN.get(vin)
    return (rec or {}).get("tires", [])
