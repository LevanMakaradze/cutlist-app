from Models import PartSpec, SheetSpec, LayoutResult
from GuillotineLayoutEngine import GuillotineLayoutEngine
from GuillotineRotationAwareEngine import GuillotineRotationAwareEngine
from GuillotineLookAheadEngine import GuillotineLookAheadEngine

ALGORITHMS = {
    GuillotineLayoutEngine.name: GuillotineLayoutEngine,
    GuillotineRotationAwareEngine.name: GuillotineRotationAwareEngine,
    GuillotineLookAheadEngine.name: GuillotineLookAheadEngine
}

SETTINGS = {
    # guillotine, guillotine rotation aware, guillotine look-ahead
    "algorithm": "guillotine look-ahead",
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
    PartSpec(name="Door", width=760, height=420, quantity=4),
    PartSpec(name="Back", width=900, height=700, quantity=2, can_rotate=False),
    PartSpec(name="Drawer", width=500, height=180, quantity=8),
]

def run_layout(parts: list[PartSpec], sheets: list[SheetSpec], settings: dict) -> LayoutResult:
    algorithm_name = settings.get("algorithm", "simple heuristic")
    try:
        engine = ALGORITHMS[algorithm_name]()
    except KeyError as exc:
        available = ", ".join(sorted(ALGORITHMS))
        raise ValueError(f"Unknown algorithm {algorithm_name!r}. Available: {available}") from exc
    return engine.layout(parts, sheets, settings)

print(run_layout(PARTS,SHEETS,SETTINGS))
