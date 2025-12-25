use crate::geo::Vector2;
use core::ops::{Add, Sub};

/// Represents a 2D points with integer coordinates.
///
/// While primarily used to represent spatial positions (vertices) in a grid or pixel space,
/// this struct is also implemented for integer-based vector arithmetic
#[derive(Debug, Clone, PartialEq, Eq, Copy)]
pub struct Vertex {
    x: i32,
    y: i32,
}

impl Vertex {
    /// Creates a new vertex with the given coordinates.
    pub const fn new(x: i32, y: i32) -> Self {
        Self { x, y }
    }

    pub const fn x(&self) -> i32 {
        self.x
    }

    pub const fn y(&self) -> i32 {
        self.y
    }

    /// Translates (moves) the vertex by the given delta amounts.
    pub const fn translate(&mut self, dx: i32, dy: i32) {
        self.x += dx;
        self.y += dy;
    }

    /// Calculates the Euclidean distance between this vertex and another.
    ///
    /// # Returns
    ///
    /// The distance as an `f64`.
    pub fn distance_to(&self, other: &Self) -> f64 {
        let dx = (self.x - other.x) as f64;
        let dy = (self.y - other.y) as f64;
        dx.hypot(dy)
    }

    /// Computes the dot product of two integer vectors.
    ///
    /// $A \cdot B = A_x B_x + A_y B_y$
    ///
    /// # Returns
    ///
    /// An `i64` to prevent integer overflow during multiplication.
    pub const fn dot(&self, other: &Self) -> i64 {
        self.x as i64 * other.x as i64 + self.y as i64 * other.y as i64
    }

    /// Computes the 2D pseudo-cross product (determinant).
    ///
    /// $A \times B = A_x B_y - A_y B_x$
    ///
    pub const fn cross(&self, other: &Self) -> i64 {
        self.x as i64 * other.y as i64 - self.y as i64 * other.x as i64
    }

    /// Returns a new Vertex containing the component-wise minimum coordinates.
    ///
    /// Useful for calculating Bounding Boxes.
    pub fn min(&self, other: &Self) -> Self {
        Self {
            x: self.x.min(other.x),
            y: self.y.min(other.y),
        }
    }

    /// Returns a new Vertex containing the component-wise maximum coordinates.
    ///
    /// Useful for calculating Bounding Boxes.
    pub fn max(&self, other: &Self) -> Self {
        Self {
            x: self.x.max(other.x),
            y: self.y.max(other.y),
        }
    }
}

/// Allows adding a floating-point `Vector2` to an integer `Vertex`.
///
/// # Behavior
///
/// The components of the `Vector2` are **rounded** to the nearest integer before addition.
/// This conversion allows moving discrete grid points by continuous physical forces.
impl Add<Vector2> for Vertex {
    type Output = Self;

    fn add(self, other: Vector2) -> Self {
        Self::new(
            self.x + other.x().round() as i32,
            self.y + other.y().round() as i32,
        )
    }
}

/// Allows subtracting two `Vertex` points to get a floating-point `Vector2`.
///
/// # Behavior
///
/// $Result = Self - Other$
///
/// This represents the vector pointing **from** `other` **to** `self`.
impl Sub for Vertex {
    type Output = Vector2;

    fn sub(self, other: Self) -> Vector2 {
        Vector2::new((self.x - other.x) as f64, (self.y - other.y) as f64)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_vertex() {
        let v = Vertex::new(10, 20);

        assert_eq!(v.x, 10);
        assert_eq!(v.y, 20);
    }

    #[test]
    fn test_getters_vertex() {
        let v = Vertex::new(15, 25);

        assert_eq!(v.x(), 15);
        assert_eq!(v.y(), 25);
    }

    #[test]
    fn test_translate_vertex() {
        let mut v = Vertex::new(5, 10);
        v.translate(3, -4);
        assert_eq!(v.x(), 8);
        assert_eq!(v.y(), 6);
    }

    #[test]
    fn test_distance_to_vertexes() {
        let v1 = Vertex::new(0, 0);
        let v2 = Vertex::new(3, 4);
        let distance = v1.distance_to(&v2);

        assert_eq!(distance, 5.0);
    }

    #[test]
    fn test_dot_product_vertexes() {
        let v1 = Vertex::new(2, 3);
        let v2 = Vertex::new(4, 5);

        let dot_product = v1.dot(&v2);
        assert_eq!(dot_product, 23);
    }

    #[test]
    fn test_cross_product_vertexes() {
        let v1 = Vertex::new(2, 3);
        let v2 = Vertex::new(4, 5);
        let cross_product = v1.cross(&v2);
        assert_eq!(cross_product, -2);
    }
}
