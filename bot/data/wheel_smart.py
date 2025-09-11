# bot/data/wheel_smart.py
from .wheel_catalog import CATALOG

def _filter_catalog(ctx):
    """Фильтруем каталог по уже выбранным параметрам."""
    r   = ctx.get("wheel_r")
    j   = ctx.get("wheel_j")
    pcd = ctx.get("wheel_pcd")
    et  = ctx.get("wheel_et")
    dia = ctx.get("wheel_dia")

    res = []
    for row in CATALOG:
        if r   and int(r) != int(row["r"]):         continue
        if j   and float(j) != float(row["j"]):     continue
        if pcd and pcd != row["pcd"]:               continue
        if et  and int(et) != int(row["et"]):       continue
        if dia and dia != row["dia"]:               continue
        res.append(row)
    return res

def smart_wheel_r(ctx):
    rows = _filter_catalog(ctx | {"wheel_r": None})
    return sorted({row["r"] for row in rows})

def smart_wheel_j(ctx):
    rows = _filter_catalog(ctx | {"wheel_j": None})
    return sorted({row["j"] for row in rows})

def smart_wheel_pcd(ctx):
    rows = _filter_catalog(ctx | {"wheel_pcd": None})
    return sorted({row["pcd"] for row in rows})

def smart_wheel_et(ctx):
    rows = _filter_catalog(ctx | {"wheel_et": None})
    return sorted({row["et"] for row in rows})

def smart_wheel_dia(ctx):
    rows = _filter_catalog(ctx | {"wheel_dia": None})
    return sorted({row["dia"] for row in rows})
