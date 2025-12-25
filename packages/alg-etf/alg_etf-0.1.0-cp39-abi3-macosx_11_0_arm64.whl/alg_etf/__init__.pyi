from enum import Enum
from typing import List, Optional

class Vertex:
    """Represents a 2D point with integer coordinates.
    
    Used for precise grid/pixel alignment in layout design.
    """
    def __init__(self, x: int, y: int) -> None: ...
    def x(self) -> int: ...
    def y(self) -> int: ...

class LayerId:
    """An identifier for a physical layer (e.g., Metal1, Poly)."""
    def __init__(self, id: int) -> None: ...

class CellId:
    """A unique identifier for a Cell definition within a library."""
    def __init__(self, id: int) -> None: ...

class Orientation(Enum):
    """The 8 possible axis-aligned orientations for 2D geometry."""
    R0 = 0
    R90 = 1
    R180 = 2
    R270 = 3
    MX = 4
    MX90 = 5
    MX180 = 6
    MX270 = 7

class FillStyle(Enum):
    """Defines the visual fill pattern for a layer."""
    Solid = 0
    NoFill = 1
    Diagonal = 2
    DiagonalBack = 3
    Horizontal = 4
    Vertical = 5

class LayerStyle:
    """Visual style for a layer, including color and fill pattern."""
    def __init__(self, r: int, g: int, b: int, visible: bool, fill: FillStyle, name: str) -> None: ...

class Technology:
    """Represents the 'PDK' or technology constraints.
    
    Acts as the single source of truth for manufacturing rules and layer styles.
    """
    def __init__(self) -> None: ...
    def add_layer_def(self, layer_id: LayerId, name: str, style: LayerStyle) -> None: ...

class Library:
    """A collection of unique Cells; the top-level container for design data."""
    def __init__(self, name: str) -> None: ...
    def add_cell(self, cell: Cell) -> None: ...

class Shape:
    """A geometric primitive."""
    @staticmethod
    def rectangle(p1: Vertex, p2: Vertex) -> Shape:
        """Creates an axis-aligned rectangle from two vertices."""
        ...

class Instance:
    """A hierarchical reference to another cell placed within the current cell."""
    def __init__(self, name: str, cell_id: CellId, x: int, y: int, orientation: Orientation) -> None: ...

class Cell:
    """A reusable design block containing geometry and child instances."""
    def __init__(self, name: str, id: CellId) -> None: ...
    def add_shape(self, layer_id: LayerId, shape: Shape) -> None: ...
    def add_instance(self, instance: Instance, library: Library) -> None: ...

class Design:
    """A complete design project, unifying Technology (rules) and Library (data)."""
    def __init__(self, tech: Technology, lib: Library) -> None: ...

def launch_viewer(design: Design) -> None:
    """Launches the interactive GDS Layout Viewer GUI."""
    ...