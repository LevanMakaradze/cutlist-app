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
    SheetSpec(name="MDF", width=2800, height=2070, quantity=20),
]

PARTS = [
    PartSpec(name="Side", width=720, height=560, quantity=40),
    PartSpec(name="Shelf", width=680, height=520, quantity=60),
    PartSpec(name="Door", width=760, height=420, quantity=80),
    PartSpec(name="Back", width=900, height=700, quantity=40, can_rotate=False),
    PartSpec(name="Drawer", width=500, height=180, quantity=80),
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

def distinct(results: list[LayoutResult]) -> list[LayoutResult]:
    distinct_results = []

    for result in results:
        is_duplicate = False

        for seen in distinct_results:
            if _same_placements(result, seen):
                is_duplicate = True
                break

        if not is_duplicate:
            distinct_results.append(result)

    return distinct_results


def _same_placements(a: LayoutResult, b: LayoutResult) -> bool:
    all_a = []
    for sheet in a.sheets:
        for placement in sheet.placements:
            all_a.append((placement.part.instance, placement.x, placement.y))

    all_b = []
    for sheet in b.sheets:
        for placement in sheet.placements:
            all_b.append((placement.part.instance, placement.x, placement.y))

    if len(all_a) != len(all_b):
        return False

    all_a.sort()
    all_b.sort()

    for i in range(len(all_a)):
        if all_a[i] != all_b[i]:
            return False

    return True

if __name__ == "__main__":
    results = run_all_parallel()
    print(len(results))
    dist_results = distinct(results)
    print(len(dist_results))