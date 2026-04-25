from CutNode import CutNode
from LayoutEngine import *

class GuillotineLayoutEngine(LayoutEngine):
    """
    Best Fit Decreasing guillotine packer.

    Parts are sorted largest to smallest, then placed one by one into the
    free node with the least wasted area. Rotation is tried only when
    a part cannot fit in its original orientation.
    """
    
    name = "guillotine"

    def layout(self, parts: list[PartSpec], sheets: list[SheetSpec], settings: dict) -> LayoutResult:
        kerf = float(settings.get("kerf", 4.4))
        vertical_first = settings.get("first_cut", "length") == "width"

        part_instances = expand_parts(parts)
        part_instances.sort(key=lambda part: (part.width * part.height, max(part.width, part.height)), reverse=True)

        sheet_layouts = expand_sheets(sheets)
        roots = [CutNode(0, 0, layout.sheet.width, layout.sheet.height) for layout in sheet_layouts]
        unplaced: list[PartInstance] = []

        for part in part_instances:
            best = self._find_best_position(part, roots)
            if best is None and part.spec.can_rotate and part.width != part.height:
                rotated = part.rotated_copy()
                best = self._find_best_position(rotated, roots)
                if best is not None:
                    part = rotated

            if best is None:
                unplaced.append(part)
                continue

            sheet_index, node = best
            placement = node.insert(part, kerf, vertical_first)
            sheet_layouts[sheet_index].placements.append(placement)

        return LayoutResult(sheets=sheet_layouts, unplaced=unplaced, algorithm=self.name)

    def _find_best_position(self, part: PartInstance, roots: list[CutNode]) -> tuple[int, CutNode] | None:
        best: tuple[tuple[float, float, float, int], int, CutNode] | None = None
        for sheet_index, root in enumerate(roots):
            for node in root.free_nodes():
                if not node.can_fit(part):
                    continue
                area_waste = (node.width * node.height) - (part.width * part.height)
                short_side_waste = min(node.width - part.width, node.height - part.height)
                long_side_waste = max(node.width - part.width, node.height - part.height)
                score = (area_waste, short_side_waste, long_side_waste, sheet_index)
                if best is None or score < best[0]:
                    best = (score, sheet_index, node)
        if best is None:
            return None
        return best[1], best[2]