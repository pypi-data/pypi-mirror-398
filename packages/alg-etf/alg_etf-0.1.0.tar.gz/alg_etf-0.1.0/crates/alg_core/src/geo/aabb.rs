use crate::geo::{Shape, Vertex};

/// Represents an Axis-Aligned Bounding Box (AABB).
///
/// An AABB is a rectangle whose edges are parallel to the coordinate axes (X and Y).
/// It is defined by its minimum (bottom-left) and maximum (top-right) corners.
///
/// # Use Cases
///
/// AABBs are primarily used in **Broad-Phase Collision Detection**. Because intersection tests
/// between AABBs are computationally trivial ($O(1)$), they serve as an excellent first pass
/// to quickly rule out shapes that are definitely not colliding, before running expensive
/// algorithms like GJK (Narrow-Phase).
#[derive(Debug, Clone)]
pub struct AABB {
    /// The corner with the smallest X and Y coordinates.
    pub min: Vertex,
    /// The corner with the largest X and Y coordinates.
    pub max: Vertex,
}

impl AABB {
    /// Creates an "empty" AABB that contains no space.
    ///
    /// The bounds are initialized to inverted extremes:
    /// * `min`: `(i32::MAX, i32::MAX)`
    /// * `max`: `(i32::MIN, i32::MIN)`
    ///
    /// This state is useful as an identity element for accumulation algorithms (e.g., growing
    /// a bounding box to fit a sequence of points).
    pub const fn empty() -> Self {
        Self {
            min: Vertex::new(i32::MAX, i32::MAX),
            max: Vertex::new(i32::MIN, i32::MIN),
        }
    }

    /// Computes the AABB that tightly encloses a set of vertices.
    ///
    /// This function iterates through all vertices to find the minimum and maximum X and Y coordinates.
    ///
    /// # Parameters
    ///
    /// * `vertices`: A slice of vertices to enclose.
    ///
    /// # Returns
    ///
    /// * A valid `AABB` enclosing the points.
    /// * If the input slice is empty, returns [`AABB::empty()`].
    ///
    /// # Time Complexity
    ///
    /// $O(V)$ where $V$ is the number of vertices.
    pub fn from_vertices(vertices: &[Vertex]) -> Self {
        if vertices.is_empty() {
            return Self::empty();
        }

        let (min, max) = vertices.iter().fold(
            (
                Vertex::new(i32::MAX, i32::MAX),
                Vertex::new(i32::MIN, i32::MIN),
            ),
            |(current_min, current_max): (Vertex, Vertex), &v| {
                (current_min.min(&v), current_max.max(&v))
            },
        );

        Self { min, max }
    }
    /// Creates a new AABB expanded uniformly in all directions.
    ///
    /// # Parameters
    ///
    /// * `amount`: The integer value to add to the `max` coords and subtract from the `min` coords.
    ///
    /// # Safety
    ///
    /// If the AABB is in the `empty` state (uninitialized), this function returns a clone of the
    /// empty AABB without modification to prevent integer overflow/underflow wrapping.
    pub fn expand(&self, amount: i32) -> Self {
        // Safety check: If the AABB is in its "empty/invalid" state
        // (min=MAX, max=MIN), do not expand it, or it will wrap around.
        if self.min.x() == i32::MAX {
            return self.clone();
        }

        Self {
            min: Vertex::new(self.min.x() - amount, self.min.y() - amount),
            max: Vertex::new(self.max.x() + amount, self.max.y() + amount),
        }
    }

    /// Checks if this AABB intersects with another AABB.
    ///
    /// This uses the **Separating Axis Theorem** logic simplified for axis-aligned rectangles:
    /// two rectangles do *not* intersect if they are separated along either the X axis OR the Y axis.
    ///
    /// # Returns
    ///
    /// * `true` if the boxes overlap or touch.
    /// * `false` if they are strictly disjoint.
    ///
    /// # Time Complexity
    ///
    /// $O(1)$
    pub const fn intersects(&self, other: &Self) -> bool {
        if self.max.x() < other.min.x() || self.min.x() > other.max.x() {
            return false;
        }

        if self.max.y() < other.min.y() || self.min.y() > other.max.y() {
            return false;
        }

        true
    }

    /// Computes the AABB that encloses a collection of generic shapes.
    ///
    /// This function is useful for calculating the bounding box of a mixed layer
    /// containing Rectangles, Polygons, and Paths.
    ///
    /// # Parameters
    ///
    /// * `shapes`: A slice of shapes to enclose.
    ///
    /// # Returns
    ///
    /// * A new `AABB` covering all input shapes.
    /// * Returns [`AABB::empty()`] if the input slice is empty.
    ///
    /// # Time Complexity
    ///
    /// $O(N)$ where $N$ is the number of shapes.
    pub fn from_shapes(shapes: &[Shape]) -> Self {
        if shapes.is_empty() {
            return Self::empty();
        }

        let (min, max) = shapes.iter().fold(
            (
                Vertex::new(i32::MAX, i32::MAX),
                Vertex::new(i32::MIN, i32::MIN),
            ),
            |(acc_min, acc_max), shape| {
                let shape_aabb = shape.aabb();
                (acc_min.min(&shape_aabb.min), acc_max.max(&shape_aabb.max))
            },
        );

        Self { min, max }
    }

    pub fn union(&self, other: &Self) -> Self {
        Self {
            min: self.min.min(&other.min),
            max: self.max.max(&other.max),
        }
    }
}
