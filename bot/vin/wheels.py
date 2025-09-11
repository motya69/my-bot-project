# bot/actions/vin/wheels.py
from typing import Dict, Any

# моковая БД VIN → варианты дисков
VIN_WHEELS_DB = {
    "WBA8D9G56GNT12345": [
        {"r": "17", "j": "7.5", "pcd": "5x120",  "et": "34", "dia": "72.6"},
        {"r": "18", "j": "8.0", "pcd": "5x120",  "et": "35", "dia": "72.6"},
    ],
    "JTMHFREV20D123456": [
        {"r": "16", "j": "6.5", "pcd": "5x114.3","et": "39", "dia": "60.1"},
        {"r": "17", "j": "7.0", "pcd": "5x114.3","et": "40", "dia": "60.1"},
    ],
}

def wheels_params_from_vin(bot, chat_id: int, ctx: Dict[str, Any]) -> None:
    vin = (ctx.get("vin") or "").strip().upper()
    items = VIN_WHEELS_DB.get(vin, [])
    # красивый лейбл каждой комплектации
    labels = [
        f'R{i["r"]} · {i["j"]}J · {i["pcd"]} · ET{i["et"]} · DIA {i["dia"]}'
        for i in items
    ]
    ctx["wheel_options"] = labels
