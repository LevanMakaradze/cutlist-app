from Models import PartSpec, SheetSpec, LayoutResult
from concurrent.futures import ProcessPoolExecutor, as_completed
from GuillotineEngine import ALL_VARIANTS, GuillotineEngine

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

def _run_variant(variant_class: type[GuillotineEngine]) -> LayoutResult:
    """Runs a single variant. Must be a top-level function for pickling."""
    return variant_class().layout(PARTS, SHEETS, SETTINGS)

def run_all_parallel() -> list[LayoutResult]:
    results = []
    with ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(_run_variant, variant): variant
            for variant in ALL_VARIANTS
        }
        for future in as_completed(futures):
            variant = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"  {variant.name} failed: {e}")

    return results
        
if __name__ == "__main__":
    results = run_all_parallel()
    print(results)