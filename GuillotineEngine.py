from CutNode import CutNode
from LayoutEngine import *

class GuillotineEngine(LayoutEngine):
    """
    Abstract base class for all guillotine variants.

    Checks both orientations of every part and chooses better fit. 
    
    Subclasses must define _score() and _split_vertical() to specify the scoring and split heuristics.

    Scoring heuristics:
        BSSF - Best Short Side Fit: minimize the shorter leftover side.
        BLSF - Best Long Side Fit: minimize the longer leftover side.
        BAF  - Best Area Fit: minimize total leftover area.

    Split heuristics:
        MAXAS - Maximize Area of Smaller rectangle: split so the smaller child is as large as possible.
        MINAS - Minimize Area of Smaller rectangle: split so the smaller child is as small as possible.
        SLAS - Shorter Leftover Axis Split: split along whichever leftover dimension is shorter.
        LLAS - Longer Leftover Axis Split: split along the longer leftover dimension. Opposite of SLAS.
    """
    
    name = "guillotine"

    def layout(self, parts: list[PartSpec], sheets: list[SheetSpec], settings: dict) -> LayoutResult:
        kerf = float(settings.get("kerf", 4.4))

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
            placement = self._insert(node, best_part, kerf)
            sheet_layouts[sheet_index].placements.append(placement)

        for i in range(len(sheet_layouts)):
            sheet_layouts[i].root = roots[i]
    
        self.record_remaining_parts(sheet_layouts, roots)
        return LayoutResult(sheets=sheet_layouts, unplaced=unplaced, algorithm=self.name)

    def _best_orientation(
        self,
        part: PartInstance,
        roots: list[CutNode],
    ) -> tuple[PartInstance, tuple[int, CutNode] | None]:
        candidates: list[tuple[PartInstance, tuple, int, CutNode]] = []

        for orientation in self._all_orientations(part):
            result = self._find_best_node(orientation, roots)
            if result is not None:
                sheet_index, node = result
                score = self._score(orientation, node, sheet_index)
                candidates.append((orientation, score, sheet_index, node))

        if not candidates:
            return part, None

        best_part, _, best_sheet, best_node = min(candidates, key=lambda c: c[1])
        return best_part, (best_sheet, best_node)

    def _find_best_node(
        self,
        part: PartInstance,
        roots: list[CutNode],
    ) -> tuple[int, CutNode] | None:
        best: tuple[tuple, int, CutNode] | None = None
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

    def _all_orientations(self, part: PartInstance) -> list[PartInstance]:
        orientations = [part]
        if part.spec.can_rotate and part.width != part.height:
            orientations.append(part.rotated_copy())
        return orientations

    # abstract interface

    def _score(self, part: PartInstance, node: CutNode, sheet_index: int) -> tuple:
        raise NotImplementedError

    def _split_vertical(self, remaining_w: float, remaining_h: float) -> bool:
        raise NotImplementedError

    # insertation

    def _insert(self, node: CutNode, part: PartInstance, kerf: float) -> Placement:
        if not node.can_fit(part):
            raise ValueError(f"Part {part.get_label()} does not fit selected node")

        node.part = part
        remaining_w = node.width - part.width
        remaining_h = node.height - part.height

        right_w  = max(0.0, remaining_w - kerf) if remaining_w > kerf else 0.0
        bottom_h = max(0.0, remaining_h - kerf) if remaining_h > kerf else 0.0

        if self._split_vertical(remaining_w, remaining_h):
            if right_w > 0:
                node.left  = CutNode(node.x + part.width + kerf, node.y, right_w, node.height)
            if bottom_h > 0:
                node.right = CutNode(node.x, node.y + part.height + kerf, part.width, bottom_h)
        else:
            if bottom_h > 0:
                node.left  = CutNode(node.x, node.y + part.height + kerf, node.width, bottom_h)
            if right_w > 0:
                node.right = CutNode(node.x + part.width + kerf, node.y, right_w, part.height)

        return Placement(part=part, x=node.x, y=node.y, width=part.width, height=part.height)


# scoring heuristics

class _BssfMixin:
    def _score(self, part: PartInstance, node: CutNode, sheet_index: int) -> tuple:
        short_side = min(node.width - part.width, node.height - part.height)
        long_side  = max(node.width - part.width, node.height - part.height)
        return (short_side, long_side, sheet_index)

class _BlsfMixin:
    def _score(self, part: PartInstance, node: CutNode, sheet_index: int) -> tuple:
        short_side = min(node.width - part.width, node.height - part.height)
        long_side  = max(node.width - part.width, node.height - part.height)
        return (long_side, short_side, sheet_index)

class _BafMixin:
    def _score(self, part: PartInstance, node: CutNode, sheet_index: int) -> tuple:
        area_waste = (node.width - part.width) * node.height + (node.height - part.height) * part.width
        short_side = min(node.width - part.width, node.height - part.height)
        return (area_waste, short_side, sheet_index)


# split heuristics

class _MaxasMixin:
    def _split_vertical(self, remaining_w: float, remaining_h: float) -> bool:
        return remaining_w > remaining_h

class _MinasMixin:
    def _split_vertical(self, remaining_w: float, remaining_h: float) -> bool:
        return remaining_w < remaining_h

class _SlasMixin:
    def _split_vertical(self, remaining_w: float, remaining_h: float) -> bool:
        return remaining_w < remaining_h

class _LlasMixin:
    def _split_vertical(self, remaining_w: float, remaining_h: float) -> bool:
        return remaining_w > remaining_h


# variants

class GuillotineBssfMaxas(_BssfMixin, _MaxasMixin, GuillotineEngine):
    name = "guillotine bssf maxas"

class GuillotineBssfMinas(_BssfMixin, _MinasMixin, GuillotineEngine):
    name = "guillotine bssf minas"

class GuillotineBssfSlas(_BssfMixin, _SlasMixin, GuillotineEngine):
    name = "guillotine bssf slas"

class GuillotineBssfLlas(_BssfMixin, _LlasMixin, GuillotineEngine):
    name = "guillotine bssf llas"



class GuillotineBlsfMaxas(_BlsfMixin, _MaxasMixin, GuillotineEngine):
    name = "guillotine blsf maxas"

class GuillotineBlsfMinas(_BlsfMixin, _MinasMixin, GuillotineEngine):
    name = "guillotine blsf minas"

class GuillotineBlsfSlas(_BlsfMixin, _SlasMixin, GuillotineEngine):
    name = "guillotine blsf slas"

class GuillotineBlsfLlas(_BlsfMixin, _LlasMixin, GuillotineEngine):
    name = "guillotine blsf llas"



class GuillotineBafMaxas(_BafMixin, _MaxasMixin, GuillotineEngine):
    name = "guillotine baf maxas"

class GuillotineBafMinas(_BafMixin, _MinasMixin, GuillotineEngine):
    name = "guillotine baf minas"

class GuillotineBafSlas(_BafMixin, _SlasMixin, GuillotineEngine):
    name = "guillotine baf slas"

class GuillotineBafLlas(_BafMixin, _LlasMixin, GuillotineEngine):
    name = "guillotine baf llas"


ALL_VARIANTS: list[type[GuillotineEngine]] = [
    GuillotineBssfMaxas,
    GuillotineBssfMinas,
    GuillotineBssfSlas,
    GuillotineBssfLlas,
    GuillotineBlsfMaxas,
    GuillotineBlsfMinas,
    GuillotineBlsfSlas,
    GuillotineBlsfLlas,
    GuillotineBafMaxas,
    GuillotineBafMinas,
    GuillotineBafSlas,
    GuillotineBafLlas,
]