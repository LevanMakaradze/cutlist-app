import math


class PartSpec:
    def __init__(
        self,
        name: str,
        width: int,
        height: int,
        quantity: int = 1,
        can_rotate: bool = True,
    ):
        self.name = name
        self.width = width
        self.height = height
        self.quantity = quantity
        self.can_rotate = can_rotate

class SheetSpec:
    def __init__(
        self, 
        name: str, 
        width: int,
        height: int,
        quantity: int = 1
    ):
        self.name = name
        self.width = width
        self.height = height
        self.quantity = quantity
        
class PartInstance:
    def __init__(
        self,
        spec: PartSpec,
        instance: int,
        width: int,
        height: int,
        rotated: bool = False,
    ):
        self.spec = spec
        self.instance = instance
        self.width = width
        self.height = height
        self.rotated = rotated

    def get_label(self):
        if self.spec.quantity > 1:
            return f"{self.spec.name}-{self.instance + 1}"
        return self.spec.name

    def rotated_copy(self):
        return PartInstance(
            self.spec,
            self.instance,
            self.height,
            self.width,
            not self.rotated,
        )
        
    def __repr__(self):
        return f"{self.get_label()} ({self.width} x {self.height})"
                    
class Placement:
    def __init__(
        self,
        part: PartInstance,
        x: float,
        y: float,
        width: int,
        height: int,
    ):
        self.part = part
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def __repr__(self):
        return f"Part:{self.part} X:{self.x}, Y:{self.y}\n"

class RemainingPiece:
    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self):
        return f"Remaining X:{self.x}, Y:{self.y}, {self.width} x {self.height}\n"
        
class CutDifficulty:
    def __init__(
        self,
        total_cuts: int,
        direction_changes: int,
    ):
        self.total_cuts = total_cuts
        self.direction_changes = direction_changes
    
class SheetLayout:
    def __init__(
        self,
        sheet: SheetSpec,
        sheet_number: int,
        placements: list[Placement] = None,
        remaining_parts: list[RemainingPiece] = None,
        root = None,
    ):
        self.sheet = sheet
        self.sheet_number = sheet_number
        self.placements = placements if placements is not None else []
        self.remaining_parts = remaining_parts if remaining_parts is not None else []
        self.root = root

    def get_used_area(self):
        return sum(
            placement.width * placement.height
            for placement in self.placements
        )

    def get_area(self):
        return self.sheet.width * self.sheet.height

    def get_utilization(self):
        area = self.get_area()

        if area == 0:
            return 0.0

        return (self.get_used_area() / area) * 100.0
    
    def get_cut_difficulty(self) -> CutDifficulty:
        """
        Counts simple total guillotine cuts by traversing the split tree.
        """
        if self.root is None:
            return CutDifficulty(0, 0)

        total_cuts = 0

        def count_splits(node):
            nonlocal total_cuts
            if node is None or node.is_leaf:
                return
            if node.split_axis is not None:
                total_cuts += 1
            count_splits(node.left)
            count_splits(node.right)

        count_splits(self.root)
        return CutDifficulty(total_cuts, 0)
        
    def __repr__(self):
        return (
            f"{self.sheet.name} #{self.sheet_number} ({self.sheet.width} x {self.sheet.height}): "
            f"Placed: {self.placements} Remaining: {self.remaining_parts}\n\n"
        )

class LayoutResult:
    def __init__(
        self,
        sheets: list[SheetLayout],
        unplaced: list[PartInstance],
        algorithm: str,
    ):
        self.sheets = sheets
        self.algorithm = algorithm

        # Converts list of PartInstance to structured list of PartSpec with correct quantities
        if unplaced and isinstance(unplaced[0], PartInstance):
            self.unplaced = self._aggregate_unplaced(unplaced)
        else:
            self.unplaced = unplaced
            
        # Internal cache for complexity metrics
        self._xml_no_count = None
        self._xml_part_count = None
    
    def get_xml_metrics(self, kerf=4.4) -> tuple[int, int]:
        """
        Returns cached XML tree metrics: (no_elements_count, part_elements_count)
        """
        if self._xml_no_count is None or self._xml_part_count is None:
            from services.layout_exporter import generate_xml_project_tree
            try:
                _, no_count, part_count = generate_xml_project_tree(self, kerf)
                self._xml_no_count = no_count
                self._xml_part_count = part_count
            except Exception:
                # Fallback defaults in case of unbuilt/empty sheets
                self._xml_no_count = 999
                self._xml_part_count = 999

        return self._xml_no_count, self._xml_part_count

    def _aggregate_unplaced(self, unplaced_instances: list[PartInstance]) -> list[PartSpec]:
        """Groups identical unplaced part instances into unified specs with quantities."""
        counts = {}
        for pi in unplaced_instances:
            spec = pi.spec
            key = (spec.name, spec.width, spec.height, spec.can_rotate)
            if key not in counts:
                counts[key] = {"spec": spec, "count": 0}
            counts[key]["count"] += 1
            
        aggregated = []
        for key, val in counts.items():
            orig_spec = val["spec"]
            aggregated.append(PartSpec(
                name=orig_spec.name,
                width=orig_spec.width,
                height=orig_spec.height,
                quantity=val["count"],
                can_rotate=orig_spec.can_rotate
            ))
        return aggregated

    def get_unplaced_count(self) -> int:
        return sum(p.quantity for p in self.unplaced)

    def get_used_sheets(self):
        count = 0

        for sheet in self.sheets:
            if sheet.placements:
                count += 1

        return count

    def get_total_sheets(self):
        return len(self.sheets)

    def get_placed_count(self):
        total = 0

        for sheet in self.sheets:
            total += len(sheet.placements)

        return total

    def get_total_utilization(self):
        total_area = 0
        used_area = 0

        for sheet in self.sheets:
            if sheet.placements:
                total_area += sheet.get_area()

            used_area += sheet.get_used_area()

        if total_area == 0:
            return 0.0

        return (used_area / total_area) * 100.0
    
    def get_total_cut_difficulty(self) -> CutDifficulty:
        """
        Aggregates simple split cut counts across all sheets.
        """
        total_cuts = sum(sheet.get_cut_difficulty().total_cuts for sheet in self.sheets)
        return CutDifficulty(total_cuts, 0)
    
    def get_remaining_quality_value(self) -> float:
        """
        Calculates a quality score for the remaining (unused) pieces. 
        Favors fewer, larger pieces (using squared area) and square-like
        shapes over long narrow stripes (using aspect ratio).
        """
        score = 0.0
        for sheet in self.sheets:
            for piece in sheet.remaining_parts:
                area = piece.width * piece.height
                if area <= 0:
                    continue
                # Aspect ratio is between 0.0 and 1.0 (1.0 being a perfect square)
                aspect_ratio = min(piece.width, piece.height) / max(piece.width, piece.height)
                # Squaring the area heavily penalizes splitting waste into smaller fragments
                score += (area ** 2) * aspect_ratio
        return score
    
    def __repr__(self):
        return f"Algorithm: {self.algorithm}\n Sheets: {self.sheets}\n Unplaced Parts: {self.unplaced}"

class LayoutResultCollection:
    def __init__(self, results: list[LayoutResult]):
        self.results = self._distinct(results)
        self.results = self._filter_unplaced_if_perfect_exists(self.results)
        self.results = self._sort(self.results)

    def _distinct(self, results: list[LayoutResult]) -> list[LayoutResult]:
        distinct_results = []

        for result in results:
            is_duplicate = False

            for seen in distinct_results:
                if self._same_placements(result, seen):
                    is_duplicate = True
                    break

            if not is_duplicate:
                distinct_results.append(result)

        return distinct_results

    def _same_placements(self, a: LayoutResult, b: LayoutResult) -> bool:
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
    
    def _filter_unplaced_if_perfect_exists(self, results: list[LayoutResult]) -> list[LayoutResult]:
        """
        If there is at least one layout result where all parts are successfully placed,
        filter out all other layout results containing unplaced parts.
        """
        has_perfect = any(r.get_unplaced_count() == 0 for r in results)
        if has_perfect:
            return [r for r in results if r.get_unplaced_count() == 0]
        return results

    def _sort(self, results: list[LayoutResult]) -> list[LayoutResult]:
        # 1. Pre-calculate the baseline minimum cuts/parts for each (unplaced, sheets) group
        baselines = {}
        for r in results:
            key = (r.get_unplaced_count(), r.get_used_sheets())
            no_val, part_val = r.get_xml_metrics()
            if key not in baselines:
                baselines[key] = {"no": [], "part": []}
            baselines[key]["no"].append(no_val)
            baselines[key]["part"].append(part_val)

        baseline_mins = {
            key: (min(data["no"]), min(data["part"]))
            for key, data in baselines.items()
        }

        # 2. Helper to calculate dynamic sliding-scale tier value (0 = Green, 1 = Yellow, 2 = Red)
        def get_tier_value(r: LayoutResult) -> int:
            if r.get_unplaced_count() > 0:
                return 2  # Always Red if parts are left over
                
            key = (r.get_unplaced_count(), r.get_used_sheets())
            no_min, part_min = baseline_mins[key]
            my_no, my_part = r.get_xml_metrics()

            # Sliding-scale limits
            green_no_limit = no_min + 3 + (0.10 * no_min)
            green_part_limit = part_min + 5 + (0.10 * part_min)

            yellow_no_limit = no_min + 10 + (0.40 * no_min)
            yellow_part_limit = part_min + 15 + (0.40 * part_min)

            if my_no <= green_no_limit and my_part <= green_part_limit:
                return 0  # Green
            elif my_no <= yellow_no_limit and my_part <= yellow_part_limit:
                return 1  # Yellow
            else:
                return 2  # Red

        # 3. Perform sorting
        def sort_key(result: LayoutResult):
            no_count, part_count = result.get_xml_metrics()
            tier_val = get_tier_value(result)
            return (
                result.get_unplaced_count(),           # 1. Minimize unplaced count
                result.get_used_sheets(),              # 2. Minimize sheets used
                tier_val,                              # 3. Dynamic Tier rank (Green=0, Yellow=1, Red=2)
                -result.get_remaining_quality_value(), # 4. Maximize offcut quality when tiers are equal
                no_count,                              # 5. Tiebreaker: Minimize primary cut bands
                part_count,                            # 6. Tiebreaker: Minimize cut operations
            )

        return sorted(results, key=sort_key)
    
    def best(self) -> LayoutResult:
        return self.results[0]

    def __len__(self):
        return len(self.results)

    def __iter__(self):
        return iter(self.results)

    def __getitem__(self, index):
        return self.results[index]

def expand_parts(parts: list[PartSpec]) -> list[PartInstance]:
    """ 
    Expands part specifications into individual part instances.
    
    Multiple identical parts --> Individual part instances
    """
    
    expanded = []

    for spec in parts:
        for instance in range(spec.quantity):
            expanded.append(
                PartInstance(
                    spec=spec,
                    instance=instance,
                    width=spec.width,
                    height=spec.height,
                )
            )

    return expanded


def expand_sheets(sheets: list[SheetSpec]) -> list[SheetLayout]:
    """ 
    Expands sheet specifications into individual sheet instances.
    
    Multiple identical sheets --> Individual sheet instances
    """
    expanded = []

    for spec in sheets:
        for instance in range(spec.quantity):
            expanded.append(
                SheetLayout(
                    sheet=spec,
                    sheet_number=instance + 1,
                )
            )

    return expanded
