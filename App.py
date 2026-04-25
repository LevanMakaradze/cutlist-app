from Models import PartSpec, SheetSpec, LayoutResult
from GuillotineEngine import ALL_VARIANTS

SETTINGS = {
    # guillotine rotation aware
    "algorithm": "guillotine rotation aware",
    "kerf": 1.0,
    # "length" means first split creates a horizontal row.
    # "width" means first split creates a vertical column.
    "first_cut": "length",
}

SHEETS = [
    SheetSpec(name="MDF", width=2800, height=2070, quantity=2),
]

PARTS = [
    PartSpec(name="Side", width=720, height=560, quantity=4),
    PartSpec(name="Shelf", width=680, height=520, quantity=6),
    PartSpec(name="Door", width=760, height=420, quantity=8),
    PartSpec(name="Back", width=900, height=700, quantity=4, can_rotate=False),
    PartSpec(name="Drawer", width=500, height=180, quantity=8),
]

def run_layout(parts: list[PartSpec], sheets: list[SheetSpec], settings: dict) -> LayoutResult:
    algorithm_name = settings.get("algorithm", "simple heuristic")
    try:
        engine = ALL_VARIANTS[0]()
    except KeyError as exc:
        raise ValueError(f"Unknown algorithm {algorithm_name}") from exc
    return engine.layout(parts, sheets, settings)

print(run_layout(PARTS,SHEETS,SETTINGS))
