from CutNode import CutNode
from LayoutEngine import *

class GuillotineRotationAwareEngine(LayoutEngine):
    """
    Best Fit Decreasing guillotine packer with better rotation selection.

    Same as GuillotineLayoutEngine, but both orientations of every part
    are evaluated simultaneously and the one with the better fit score
    is chosen.
    """
    
    name = "guillotine rotation aware"

    def layout(self, parts: list[PartSpec], sheets: list[SheetSpec], settings: dict) -> LayoutResult:
        kerf = float(settings.get("kerf", 4.4))
        vertical_first = settings.get("first_cut", "length") == "width"

        part_instances = expand_parts(parts)
        part_instances.sort(key=lambda p: (p.width * p.height, max(p.width, p.height)), reverse=True)

        sheet_layouts = expand_sheets(sheets)
        roots = [CutNode(0, 0, layout.sheet.width, layout.sheet.height) for layout in sheet_layouts]
        unplaced: list[PartInstance] = []

        for part in part_instances:
            best_part, best_result = self._best_orientation(part, roots)

            if best_result is None:
                unplaced.append(part)
                continue

            sheet_index, node = best_result
            placement = node.insert(best_part, kerf, vertical_first)
            sheet_layouts[sheet_index].placements.append(placement)

        self.record_remaining_parts(sheet_layouts, roots)
        return LayoutResult(sheets=sheet_layouts, unplaced=unplaced, algorithm=self.name)

    def _best_orientation(
        self,
        part: PartInstance,
        roots: list[CutNode],
    ) -> tuple[PartInstance, tuple[int, CutNode] | None]:
        
        candidates: list[tuple[PartInstance, tuple[float, float, float, int], int, CutNode]] = []

        normal_result = self._find_best_position(part, roots)
        if normal_result is not None:
            sheet_index, node = normal_result
            score = self._score(part, node, sheet_index)
            candidates.append((part, score, sheet_index, node))

        can_try_rotated = (
            part.spec.can_rotate
            and part.width != part.height
        )
        
        if can_try_rotated:
            rotated = part.rotated_copy()
            rotated_result = self._find_best_position(rotated, roots)
            if rotated_result is not None:
                sheet_index, node = rotated_result
                score = self._score(rotated, node, sheet_index)
                candidates.append((rotated, score, sheet_index, node))

        if not candidates:
            return part, None

        best_part, _, best_sheet, best_node = min(candidates, key=lambda c: c[1])
        return best_part, (best_sheet, best_node)

    def _find_best_position(
        self,
        part: PartInstance,
        roots: list[CutNode],
    ) -> tuple[int, CutNode] | None:
        best: tuple[tuple[float, float, float, int], int, CutNode] | None = None
        for sheet_index, root in enumerate(roots):
            for node in root.free_nodes():
                if not node.can_fit(part):
                    continue
                score = self._score(part, node, sheet_index)
                if best is None or score < best[0]:
                    best = (score, sheet_index, node)
        if best is None:
            return None
        return best[1], best[2]

    def _score(
        self,
        part: PartInstance,
        node: CutNode,
        sheet_index: int,
    ) -> tuple[float, float, float, int]:
        area_waste = (node.width * node.height) - (part.width * part.height)
        short_side_waste = min(node.width - part.width, node.height - part.height)
        long_side_waste = max(node.width - part.width, node.height - part.height)
        return (area_waste, short_side_waste, long_side_waste, sheet_index)
