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
        Counts physical cutting difficulty by traversing the guillotine cut tree.

        If same depth level cuts are parallel they are counted as a single pass.
        A direction change means the sheet must be repositioned.

        Returns a dict with:
            total_cuts - total number of distinct cut passes
            direction_changes - how many times cut direction flips between levels
            cut_sequence - list of cut directions per depth, e.g. ['H', 'V', 'H']
        """
        if self.root is None:
            return CutDifficulty(0,0)

        cuts_by_depth: dict[int, bool] = {}
        self._traverse(self.root, depth=0, cuts_by_depth=cuts_by_depth)

        if not cuts_by_depth:
            return CutDifficulty(0,0)

        # build ordered sequence of cut directions by depth
        cut_sequence = []
        for depth in sorted(cuts_by_depth.keys()):
            is_vertical = cuts_by_depth[depth]
            cut_sequence.append("V" if is_vertical else "H")

        # count direction changes between consecutive depths
        direction_changes = 0
        for i in range(1, len(cut_sequence)):
            if cut_sequence[i] != cut_sequence[i - 1]:
                direction_changes += 1

        return CutDifficulty(len(cut_sequence), direction_changes)


    def _traverse(self, node, depth: int, cuts_by_depth: dict):
        if node is None or node.is_leaf:
            return

        if node.split_axis is not None:
            if depth not in cuts_by_depth:
                cuts_by_depth[depth] = node.split_axis

        self._traverse(node.left, depth + 1, cuts_by_depth)
        self._traverse(node.right, depth + 1, cuts_by_depth)
        
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
    
    def get_total_cut_difficulty(self) -> dict:
        total_cuts = 0
        total_direction_changes = 0

        for sheet in self.sheets:
            if not sheet.placements:
                continue
            difficulty = sheet.get_cut_difficulty()
            total_cuts += difficulty.total_cuts
            total_direction_changes += difficulty.direction_changes

        return CutDifficulty(total_cuts,total_direction_changes)
    
    def __repr__(self):
        return f"Algorithm: {self.algorithm}\n Sheets: {self.sheets}\n Unplaced Parts: {self.unplaced}"

class LayoutResultCollection:
    def __init__(self, results: list[LayoutResult]):
        self.results = self._distinct(results)
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

    def _sort(self, results: list[LayoutResult]) -> list[LayoutResult]:
        def sort_key(result: LayoutResult):
            difficulty = result.get_total_cut_difficulty()
            return (
                len(result.unplaced),
                result.get_used_sheets(),
                difficulty.total_cuts,
                difficulty.direction_changes,
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
