use core::ops::Add;

use crate::{geo::Vertex, library::cell::CellId};

/// Represents the 8 possible axis-aligned orientations for a 2D geometry on a grid.
///
/// They preserve the integer alignment of the layout.
///
/// # Variants
///
/// The naming convention uses `R` for counter-clockwise rotation and `MX` for mirroring across the X-axis (before rotation).
///
/// * `R0`: No rotation (Identity).
/// * `R90`: Rotate 90° counter-clockwise.
/// * `R180`: Rotate 180°.
/// * `R270`: Rotate 270° counter-clockwise.
/// * `MX`: Mirror across the X-axis (y -> -y).
/// * `MX90`: Mirror across X, then rotate 90° (equivalent to swapping X and Y).
/// * `MX180`: Mirror across X, then rotate 180° (equivalent to Mirror Y).
/// * `MX270`: Mirror across X, then rotate 270°.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Orientation {
    R0,
    R90,
    R180,
    R270,
    MX,
    MX90,
    MX180,
    MX270,
}

/// Represents a transformation restricted to the integer grid.
///
/// This structure combines an [`Orientation`] (rotation/mirror) with a translational offset.
/// It is mainly used to place an [Instance] inside another [crate::library::Cell], transform shapes, or change coordinate systems without
/// snapping errors common in floating-point transforms.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Translate {
    /// The displacement vector added after rotation.
    offset: Vertex,
    /// The rotational/mirror component of the transform.
    orientation: Orientation,
}

/// Represents a hierarchical reference to another cell.
///
/// An `Instance` places a [crate::library::Cell] into the current coordinate system
/// (the `parent` cell). This is fundamental to hierarchical design, allowing logic
/// (like an AND gate) to be defined once and reused thousands of times.
///
/// # Memory Efficiency
/// This struct acts as a lightweight pointer. It stores only the metadata (ID, location, name),
/// not the actual geometry. The geometry remains stored in the definition looked up by `cell_id`.
#[derive(Clone)]
pub struct Instance {
    /// The specific name of this instance.
    name: String,
    /// The unique identifier of the referenced Master Cell definition.
    cell_id: CellId,
    /// The transformation (translation + orientation) applied to the instance.
    translation: Translate,
}

impl Instance {
    /// Creates a new instance of a cell.
    ///
    /// # Example
    ///
    /// ```rust
    /// use alg_core::library::{CellId, Instance, Translate, Orientation};
    /// use alg_core::geo::Vertex;
    ///
    /// // Assume we have a CellId for a "NAND Gate"
    /// let nand_gate_id = CellId(42);
    ///
    /// // Create a transformation to place it at (100, 200) with no rotation
    /// let placement = Translate::new(
    ///     Vertex::new(100, 200),
    ///     Orientation::R0
    /// );
    ///
    /// // Create the instance "nand_1"
    /// let inst = Instance::new(
    ///     "nand_1".to_string(),
    ///     nand_gate_id,
    ///     placement
    /// );
    /// ```    
    pub const fn new(name: String, cell_id: CellId, translation: Translate) -> Self {
        Self {
            name,
            cell_id,
            translation,
        }
    }

    /// Returns the instance name.
    pub const fn name(&self) -> &String {
        &self.name
    }

    /// Returns the ID of the master cell definition.
    pub const fn cell_id(&self) -> CellId {
        self.cell_id
    }

    /// Returns the transformation applied to this instance.
    pub const fn translation(&self) -> &Translate {
        &self.translation
    }
}

/// Creates a new transformation.
impl Translate {
    pub const fn new(offset: Vertex, orientation: Orientation) -> Self {
        Self {
            offset,
            orientation,
        }
    }

    pub const fn offset(&self) -> &Vertex {
        &self.offset
    }

    pub const fn orientation(&self) -> &Orientation {
        &self.orientation
    }

    /// Transforms a local point $(x, y)$ into the parent coordinate system.
    ///
    /// # Order of Operations
    ///
    /// 1. **Orientation:** The point is rotated/mirrored relative to the local origin $(0,0)$.
    /// 2. **Translation:** The `offset` is added to the result.
    ///
    /// $$ P_{parent} = M_{orient} \cdot P_{local} + V_{offset} $$
    pub const fn transform_point(&self, point: (i32, i32)) -> (i32, i32) {
        let (x, y) = self.orientation.apply(point);
        (x + self.offset.x(), y + self.offset.y())
    }

    /// Transforms a Vertex.
    pub const fn transform_vertex(&self, v: Vertex) -> Vertex {
        let (nx, ny) = self.transform_point((v.x(), v.y()));
        Vertex::new(nx, ny)
    }

    /// Composes two transformations: `self` applied AFTER `other`.
    ///
    /// Result(p) = self(other(p))
    ///
    /// New Orientation = self.orientation * other.orientation
    /// New Offset = self.orientation(other.offset) + self.offset
    pub fn compose(&self, other: &Self) -> Self {
        let new_orient = self.orientation.compose(other.orientation);

        let (rotated_other_offset_x, rotated_other_offset_y) =
            self.orientation.apply((other.offset.x(), other.offset.y()));
        let new_offset_x = rotated_other_offset_x + self.offset.x();
        let new_offset_y = rotated_other_offset_y + self.offset.y();

        Self {
            offset: Vertex::new(new_offset_x, new_offset_y),
            orientation: new_orient,
        }
    }
}

impl Orientation {
    /// Applies the rotation/mirroring logic to a 2D point $(x, y)$.
    ///
    /// This is a pure linear map (matrix multiplication) on the integer grid.
    pub const fn apply(&self, point: (i32, i32)) -> (i32, i32) {
        let (x, y) = point;
        match self {
            Self::R0 => (x, y),
            Self::R90 => (-y, x),
            Self::R180 => (-x, -y),
            Self::R270 => (y, -x),
            Self::MX => (x, -y),
            Self::MX90 => (y, x), // MX -> (x, -y) -> R90 -> (-(-y), x) = (y, x)
            Self::MX180 => (-x, y), // MX -> (x, -y) -> R180 -> (-x, -(-y)) = (-x, y)
            Self::MX270 => (-y, -x), // MX -> (x, -y) -> R270 -> (-y, -x)
        }
    }

    /// Composes two orientations: `self` applied AFTER `other`.
    ///
    /// This corresponds to matrix multiplication: M_self * M_other.
    pub fn compose(&self, other: Self) -> Self {
        // We can implement this by applying self to the basis vectors of other,
        // or by simply observing the group table.
        // A simpler hack: Apply 'other' to (1,0) and (0,1), then apply 'self' to those results,
        // then identify the resulting orientation.

        let p_x = (1, 0);
        let p_y = (0, 1);

        let p_x_prime = self.apply(other.apply(p_x));
        let p_y_prime = self.apply(other.apply(p_y));

        match (p_x_prime, p_y_prime) {
            ((1, 0), (0, 1)) => Self::R0,
            ((0, 1), (-1, 0)) => Self::R90,
            ((-1, 0), (0, -1)) => Self::R180,
            ((0, -1), (1, 0)) => Self::R270,

            ((1, 0), (0, -1)) => Self::MX,
            ((0, 1), (1, 0)) => Self::MX90,
            ((-1, 0), (0, 1)) => Self::MX180,
            ((0, -1), (-1, 0)) => Self::MX270,

            _ => unreachable!("Orientation composition produced invalid basis vectors"),
        }
    }
}

impl Add for Translate {
    type Output = Self;

    fn add(self, other: Self) -> Self {
        self.compose(&other)
    }
}
