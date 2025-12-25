use crate::{
    geo::{AABB, Polygon, Support, Vector2, Vertex},
    library::instance::Translate,
};

/// Represents an axis-aligned rectangle defined by two corner vertices.
///
/// While similar to an [`AABB`], this struct represents a concrete geometric shape in the world,
/// whereas `AABB` is typically used as an optimization construct (bounding volume).
#[derive(Debug, Clone)]
pub struct Rectangle {
    lower_left: Vertex,
    upper_right: Vertex,
    aabb: AABB,
}

impl Rectangle {
    /// Creates a new rectangle from two diagonal corners.
    ///
    /// The constructor automatically initializes the internal AABB.
    ///
    /// # Parameters
    ///
    /// * `lower_left`: The vertex with the minimum X and Y coordinates.
    /// * `upper_right`: The vertex with the maximum X and Y coordinates.
    pub const fn new(lower_left: Vertex, upper_right: Vertex) -> Self {
        Self {
            lower_left,
            upper_right,
            aabb: AABB {
                min: lower_left,
                max: upper_right,
            },
        }
    }

    /// Calculates the area of the rectangle.
    ///
    /// # Returns
    ///
    /// * `Ok(u32)`: The calculated area.
    /// * `Err(&str)`: If the area calculation overflows (result exceeds `u32::MAX`) or is negative (invalid coords).
    pub fn area(&self) -> Result<u32, &'static str> {
        let width = self.upper_right.x() - self.lower_left.x();
        let height = self.upper_right.y() - self.lower_left.y();

        (width * height)
            .try_into()
            .map_err(|_| "Area calculation overflowed")
    }

    /// Returns a reference to the lower-left corner (min X, min Y).
    pub const fn lower_left(&self) -> &Vertex {
        &self.lower_left
    }

    /// Returns a reference to the upper-right corner (max X, max Y).
    pub const fn upper_right(&self) -> &Vertex {
        &self.upper_right
    }

    /// Returns the Axis-Aligned Bounding Box (AABB) of the rectangle.
    ///
    /// For a `Rectangle`, the AABB is identical to the shape itself.
    pub const fn aabb(&self) -> &AABB {
        &self.aabb
    }

    /// Returns the minimum width of the rectangle.
    ///
    /// This is the smaller of the width and height dimensions.
    pub fn min_width(&self) -> u32 {
        let width = self.upper_right.x() - self.lower_left.x();
        let height = self.upper_right.y() - self.lower_left.y();
        width.min(height) as u32
    }

    /// Converts this `Rectangle` into an equivalent 4-vertex `Polygon`.
    ///
    /// This is useful when you need to perform operations that are only implemented
    /// for polygons (e.g., rotation, non-axis-aligned transformations) or when
    /// unifying a collection of shapes into a single type.
    ///
    /// The resulting polygon vertices are ordered counter-clockwise starting from the lower-left:
    /// 1. Lower-Left $(x_{min}, y_{min})$
    /// 2. Lower-Right $(x_{max}, y_{min})$
    /// 3. Upper-Right $(x_{max}, y_{max})$
    /// 4. Upper-Left $(x_{min}, y_{max})$
    ///
    /// # Example
    ///
    /// ```
    /// use alg_core::geo::{Rectangle, Vertex};
    ///
    /// let rect = Rectangle::new(Vertex::new(0, 0), Vertex::new(10, 20));
    /// let poly = rect.to_polygon();
    ///
    /// assert_eq!(poly.vertices().len(), 4);
    /// ```
    pub fn to_polygon(&self) -> Polygon {
        Polygon::new(vec![
            Vertex::new(self.lower_left.x(), self.lower_left.y()),
            Vertex::new(self.upper_right.x(), self.lower_left.y()),
            Vertex::new(self.upper_right.x(), self.upper_right.y()),
            Vertex::new(self.lower_left.x(), self.upper_right.y()),
        ])
    }

    pub const fn transform(&self, translate: &Translate) -> Self {
        let (min_x, min_y) = translate.transform_point((self.lower_left.x(), self.lower_left.y()));
        let (max_x, max_y) =
            translate.transform_point((self.upper_right.x(), self.upper_right.y()));

        Self::new(Vertex::new(min_x, min_y), Vertex::new(max_x, max_y))
    }
}

/// Implements the GJK Support mapping for a Rectangle.
///
/// Because a rectangle is axis-aligned, the furthest point in any direction is always
/// one of the four corners. The selection logic is purely based on the signs of the
/// direction vector components.
///
/// # Time Complexity
///
/// $O(1)$
impl Support for Rectangle {
    fn support(&self, direction: &Vector2) -> Vector2 {
        let x = if direction.x() >= 0.0 {
            self.upper_right.x()
        } else {
            self.lower_left.x()
        };

        let y = if direction.y() >= 0.0 {
            self.upper_right.y()
        } else {
            self.lower_left.y()
        };

        // Convert the chosen integer coordinates to a float Vector2
        Vector2::new(x as f64, y as f64)
    }
}
