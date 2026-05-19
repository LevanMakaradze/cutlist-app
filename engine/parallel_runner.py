from Models import PartSpec, SheetSpec, LayoutResult, LayoutResultCollection
from concurrent.futures import ProcessPoolExecutor, as_completed
from GuillotineEngine import ALL_VARIANTS, GuillotineEngine

def _run_variant(args) -> LayoutResult:
    variant_class, parts, sheets, settings = args
    return variant_class().layout(parts, sheets, settings)

def run_all_parallel(parts: list[PartSpec], sheets: list[SheetSpec], settings: dict) -> LayoutResultCollection:
    results = []
    with ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(_run_variant, (variant, parts, sheets, settings)): variant
            for variant in ALL_VARIANTS
        }
        for future in as_completed(futures):
            variant = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"  {variant.name} failed: {e}")

    return LayoutResultCollection(results)

if __name__ == "__main__":
    result_collection = run_all_parallel()
    print(f"Total: {len(result_collection)}")
    print(f"Best: {result_collection.best().algorithm}")