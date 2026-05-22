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
        self.split_axis: str | None = None

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
