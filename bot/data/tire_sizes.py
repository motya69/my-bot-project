

SIZES = [
    # R13
    "145/80 R13", "155/80 R13", "165/70 R13", "165/80 R13", "175/70 R13", "185/60 R13", "185/70 R13",
    # R14
    "165/65 R14", "175/65 R14", "185/60 R14", "185/65 R14", "195/60 R14", "195/70 R14",
    # R15
    "185/55 R15", "185/60 R15", "195/55 R15", "195/60 R15", "195/65 R15", "205/65 R15", "215/70 R15",
    # R16
    "195/55 R16", "205/55 R16", "205/60 R16", "215/55 R16", "215/60 R16", "225/55 R16", "225/60 R16", "235/60 R16",
    # R17
    "205/50 R17", "215/50 R17", "215/55 R17", "225/45 R17", "225/50 R17", "225/55 R17",
    "235/45 R17", "235/55 R17", "245/45 R17",
    # R18
    "225/45 R18", "225/55 R18", "235/50 R18", "235/55 R18", "235/60 R18", "245/45 R18",
    "245/50 R18", "255/55 R18", "265/60 R18",
    # R19
    "225/45 R19", "235/45 R19", "235/55 R19", "245/45 R19", "255/50 R19", "255/55 R19",
    "275/40 R19", "285/45 R19",
    # R20+
    "255/45 R20", "265/50 R20", "275/45 R20", "285/50 R20", "295/40 R20",
    "275/45 R21", "325/30 R21",
    "265/40 R22", "285/35 R22", "315/30 R22"
]

def _parse(size: str):
    # "205/55 R16" -> ("205", "55", "16")
    s = size.upper().replace(" ", "")
    # теперь "205/55R16"
    width, rest = s.split("/", 1)
    height, diam = rest.split("R", 1)
    return width, height, diam

# SMART_INDEX: width -> height -> set(diameters)
SMART_INDEX = {}
for s in SIZES:
    w, h, d = _parse(s)
    SMART_INDEX.setdefault(w, {}).setdefault(h, set()).add(d)

def smart_widths():
    return sorted(SMART_INDEX.keys(), key=int)

def smart_heights(width: str):
    return sorted((SMART_INDEX.get(width) or {}).keys(), key=int)

def smart_diameters(width: str, height: str):
    return sorted((SMART_INDEX.get(width, {}).get(height) or []), key=int)
