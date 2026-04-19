from Models import (PartSpec,PartInstance,Placement,SheetSpec,SheetLayout,LayoutResult,expand_parts,expand_sheets)

class LayoutEngine:
    name = "base"

    def layout(self, parts: list[PartSpec], sheets: list[SheetSpec], settings: dict) -> LayoutResult:
        raise NotImplementedError