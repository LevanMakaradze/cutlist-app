from engine.models import PartInstance,Placement
 
class CutNode:
    """
    Represents Cut Nodes so guillotine cutting rule always will be applied.
    
    Nodes form a tree where each split creates child nodes
    representing the remaining available space.
    
    """
    
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.part: PartInstance | None = None
        self.left: CutNode | None = None
        self.right: CutNode | None = None

    @property
    def is_leaf(self) -> bool:
        """Returns True if the node has no child nodes."""
        return self.left is None and self.right is None

    @property
    def is_free(self) -> bool:
        """Returns True if the node is empty and can accept a part."""
        return self.is_leaf and self.part is None

    def free_nodes(self) -> list["CutNode"]:
        """Returns all free leaf nodes that can be used for placement."""
        if self.is_free:
            return [self]
        nodes: list[CutNode] = []
        if self.left:
            nodes.extend(self.left.free_nodes())
        if self.right:
            nodes.extend(self.right.free_nodes())
        return nodes

    def can_fit(self, part: PartInstance) -> bool:
        return self.is_free and part.width <= self.width and part.height <= self.height

    def insert(self, part: PartInstance, kerf: float, vertical_first: bool) -> Placement:
        """Place part and split the remaining space into new free nodes"""
        
        if not self.can_fit(part):
            raise ValueError(f"Part {part.get_label()} does not fit selected node")

        self.part = part
        remaining_width = self.width - part.width
        remaining_height = self.height - part.height

        right_width = max(0.0, remaining_width - kerf) if remaining_width > kerf else 0.0
        bottom_height = max(0.0, remaining_height - kerf) if remaining_height > kerf else 0.0

        if vertical_first:
            if right_width > 0:
                self.left = CutNode(self.x + part.width + kerf, self.y, right_width, self.height)
            if bottom_height > 0:
                self.right = CutNode(self.x, self.y + part.height + kerf, part.width, bottom_height)
        else:
            if bottom_height > 0:
                self.left = CutNode(self.x, self.y + part.height + kerf, self.width, bottom_height)
            if right_width > 0:
                self.right = CutNode(self.x + part.width + kerf, self.y, right_width, part.height)

        return Placement(part=part, x=self.x, y=self.y, width=part.width, height=part.height)