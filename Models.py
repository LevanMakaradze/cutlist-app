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
        
class SheetLayout:
    def __init__(
        self,
        sheet: SheetSpec,
        sheet_number: int,
        placements: list[Placement] = None,
        remaining_parts: list[RemainingPiece] = None,
    ):
        self.sheet = sheet
        self.sheet_number = sheet_number
        self.placements = placements if placements is not None else []
        self.remaining_parts = remaining_parts if remaining_parts is not None else []

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
        self.unplaced = unplaced
        self.algorithm = algorithm

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
    
    def __repr__(self):
        return f"Algorithm: {self.algorithm}\n Sheets: {self.sheets}\n Unplaced Parts: {self.unplaced}"


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
