use core::ops::{Add, Mul, Neg, Sub};

/// Represents a 2D vector with floating-point coordinates.
///
/// Unlike [`crate::geo::Vertex`] (which uses integers), `Vector2` is used for physics calculations,
/// direction vectors, and GJK internal math where sub-pixel precision is required.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Vector2 {
    x: f64,
    y: f64,
}

impl Vector2 {
    /// Creates a new vector.
    pub const fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    /// Returns the X component.
    pub const fn x(&self) -> f64 {
        self.x
    }

    /// Returns the Y component.
    pub const fn y(&self) -> f64 {
        self.y
    }

    /// Calculates the magnitude (length) of the vector.
    ///
    /// $|v| = \sqrt{x^2 + y^2}$
    pub fn mag(&self) -> f64 {
        (self.x).hypot(self.y)
    }

    /// Calculates the squared magnitude of the vector.
    ///
    /// $|v|^2 = x^2 + y^2$
    ///
    /// This is computationally cheaper than `mag()` because it avoids the square root.
    /// Use this for comparisons (e.g., checking if length > threshold).
    pub fn mag_sq(&self) -> f64 {
        (self.y).mul_add(self.y, (self.x).powi(2))
    }

    /// Computes the dot product with another vector.
    ///
    /// $A \cdot B = A_x B_x + A_y B_y$
    ///
    /// # Geometric Interpretation
    /// * $> 0$: Vectors point in generally the same direction.
    /// * $< 0$: Vectors point in generally opposite directions.
    /// * $= 0$: Vectors are perpendicular (orthogonal).
    pub fn dot(&self, other: &Self) -> f64 {
        self.x.mul_add(other.x, self.y * other.y)
    }

    /// Computes the 2D pseudo-cross product (determinant).
    ///
    /// $A \times B = A_x B_y - A_y B_x$
    ///
    /// This returns a scalar value representing the signed magnitude of the Z-component
    /// if these were 3D vectors.
    pub fn cross(&self, other: &Self) -> f64 {
        self.x.mul_add(other.y, -(self.y * other.x))
    }

    /// Computes the Vector Triple Product: $(A \times B) \times C$.
    ///
    /// This is critical for the GJK algorithm to find a new search direction perpendicular
    /// to a line segment $AB$ towards the Origin.
    ///
    /// # Algorithm
    ///
    /// Uses the vector identity (Lagrange's formula):
    /// $$(A \times B) \times C = B(A \cdot C) - A(B \cdot C)$$
    pub fn triple_product(&self, b: &Self, c: &Self) -> Self {
        let ac = self.dot(c);
        let bc = b.dot(c);
        // Using vector identity: (A x B) x C = B(A.C) - A(B.C)
        Self {
            x: b.x.mul_add(ac, -(self.x * bc)),
            y: b.y.mul_add(ac, -(self.y * bc)),
        }
    }
}

/// Vector Addition: $A + B$
impl Add for Vector2 {
    type Output = Self;

    fn add(self, other: Self) -> Self {
        Self::new(self.x + other.x, self.y + other.y)
    }
}

/// Vector Negation: $-A$
impl Neg for Vector2 {
    type Output = Self;

    fn neg(self) -> Self {
        Self::new(-self.x, -self.y)
    }
}

/// Vector Subtraction: $A - B$
impl Sub for Vector2 {
    type Output = Self;

    fn sub(self, other: Self) -> Self {
        Self::new(self.x - other.x, self.y - other.y)
    }
}

/// Scalar Multiplication: $A \cdot k$
impl Mul<f64> for Vector2 {
    type Output = Self;

    fn mul(self, scalar: f64) -> Self {
        Self::new(self.x * scalar, self.y * scalar)
    }
}
