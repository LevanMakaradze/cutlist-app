from concurrent.futures import ProcessPoolExecutor, as_completed
from engine.models import PartSpec, SheetSpec, LayoutResult, LayoutResultCollection
from engine.guillotine_engine import ALL_VARIANTS

def _run_variant(args) -> LayoutResult:
    variant_class, parts, sheets, settings = args
    return variant_class().layout(parts, sheets, settings)

def run_all_parallel(parts: list[PartSpec], sheets: list[SheetSpec], settings: dict) -> LayoutResultCollection:
    results = []
    errors = []
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
                errors.append(f"{variant.name}: {e}")

    # If all variants fail, raise an error to inform the UI rather instead of returning empty lists
    if not results and errors:
        raise RuntimeError("გამოთვლის ყველა ალგორითმის შეცდომა:\n" + "\n".join(errors))

    return LayoutResultCollection(results)