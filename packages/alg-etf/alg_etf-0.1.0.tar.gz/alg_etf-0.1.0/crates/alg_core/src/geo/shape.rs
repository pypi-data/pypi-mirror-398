use crate::geo::gjk;
use crate::geo::polygon::PolygonType;
use crate::geo::{AABB, Path, Polygon, Rectangle};
use crate::library::instance::Translate;

/// A unified wrapper for all supported geometric primitives.
///
/// This enum allows heterogeneous collections of shapes (e.g., `Vec<Shape>`) to be processed
/// uniformly for collision detection and distance queries.
#[derive(Debug, Clone)]
pub enum Shape {
    Path(Path),
    Polygon(Polygon),
    Rectangle(Rectangle),
}

impl Shape {
    /// Returns the cached Axis-Aligned Bounding Box (AABB) for the shape.
    ///
    /// This method delegates to the underlying variant's implementation.
    pub const fn aabb(&self) -> &AABB {
        match self {
            Self::Path(p) => p.aabb(),
            Self::Polygon(p) => p.aabb(),
            Self::Rectangle(r) => r.aabb(),
        }
    }

    /// Determines if this shape intersects with another.
    ///
    /// This method implements a two-phase collision detection pipeline:
    /// 1.  **Broad Phase:** Fast AABB intersection test. If this fails, returns `false` immediately.
    /// 2.  **Narrow Phase:** Dispatches to the specific GJK algorithm or recursive decomposition logic
    ///     appropriate for the pair of shapes.
    ///
    /// # Logic
    ///
    /// * **Convex Shapes:** Direct GJK intersection test.
    /// * **Concave Shapes:** Iterates through sub-triangles; returns `true` if *any* triangle intersects.
    /// * **Paths:** Decomposes into segments on-the-fly; returns `true` if *any* segment intersects.
    ///
    /// # Time Complexity
    ///
    /// Dependent on shape complexity.
    /// * aabb non-intersection: $O(1)$
    /// * Simple Convex: $O(V_A + V_B)$
    /// * Concave/Path: $O(N \cdot M \cdot (V_{sub} + V_{other}))$ where N, M are the number of sub-components.
    pub fn intersects(&self, other: &Self) -> bool {
        // Broad Phase
        if !self.aabb().intersects(other.aabb()) {
            return false;
        }

        match (self, other) {
            // --- Atomic vs Atomic ---
            (Self::Rectangle(a), Self::Rectangle(b)) => gjk::convex_intersects(a, b),

            // Polygon handling
            (Self::Rectangle(r), Self::Polygon(p)) => rect_vs_poly_intersect(r, p),
            (Self::Polygon(p), Self::Rectangle(r)) => rect_vs_poly_intersect(r, p),
            (Self::Polygon(a), Self::Polygon(b)) => poly_vs_poly_intersect(a, b),

            // If we hit a Path, we effectively turn it into a list of Polygons on the fly
            // and check if ANY of those polygons intersect the other shape.
            (Self::Path(path), other_shape) => path
                .decompose()
                .any(|poly_segment| Self::Polygon(poly_segment).intersects(other_shape)),

            (other_shape, Self::Path(path)) => path
                .decompose()
                .any(|poly_segment| Self::Polygon(poly_segment).intersects(other_shape)),
        }
    }

    /// Calculates the minimum distance and separation details between two shapes.
    ///
    /// Unlike `intersects`, this method returns a [`gjk::Proximity`] enum which contains detailed
    /// information about the separation (distance vector, clearance) or intersection status.
    ///
    /// # Logic
    ///
    /// * **Convex Shapes:** Direct GJK distance calculation.
    /// * **Concave Shapes/Paths:** Iterates through all sub-components, calculates the distance
    ///   for each pair, and reduces the results using [`gjk::Proximity::min`] to find the
    ///   global minimum separation.
    ///
    /// # Time Complexity
    ///
    /// Dependent on shape complexity.
    /// * Simple Convex: $O(V_A + V_B)$
    /// * **Concave / Path:** $O(N \cdot M \cdot (V_{subA} + V_{subB}))$
    ///   * Where $N$ and $M$ are the number of sub-components (triangles or segments) in shapes A and B.
    ///   * Because every sub-component of A is checked against every sub-component of B,
    ///     this can be computationally expensive for complex shapes ($O(N^2)$ behavior).
    pub fn distance(&self, other: &Self) -> gjk::Proximity {
        match (self, other) {
            // --- Atomic vs Atomic ---
            (Self::Rectangle(a), Self::Rectangle(b)) => gjk::convex_distance(a, b),

            // --- Rect vs Polygon ---
            (Self::Rectangle(r), Self::Polygon(p)) => rect_vs_poly_distance(r, p),
            (Self::Polygon(p), Self::Rectangle(r)) => rect_vs_poly_distance(r, p),

            // --- Polygon vs Polygon ---
            (Self::Polygon(a), Self::Polygon(b)) => poly_vs_poly_distance(a, b),

            // --- Path Handling ---
            // Decompose, calculate proximity for each segment, and keep the minimum.
            (Self::Path(path), other_shape) | (other_shape, Self::Path(path)) => {
                path.decompose()
                    .map(|segment| {
                        // Treat the segment as a Polygon
                        let poly_segment = Self::Polygon(segment);
                        poly_segment.distance(other_shape)
                    })
                    // Fold/Reduce to find the single closest proximity
                    .fold(gjk::Proximity::max_value(), |closest, current| {
                        closest.min(current)
                    })
            }
        }
    }

    pub fn transform(&self, translate: &Translate) -> Self {
        match self {
            Self::Path(p) => Self::Path(p.transform(translate)),
            Self::Polygon(p) => Self::Polygon(p.transform(translate)),
            Self::Rectangle(r) => Self::Rectangle(r.transform(translate)),
        }
    }
}

// --- Internal Helpers ---

/// Helper: Intersection between Rectangle and Polygon (handles Concave polygons).
fn rect_vs_poly_intersect(r: &Rectangle, p: &Polygon) -> bool {
    if !r.aabb().intersects(p.aabb()) {
        return false;
    }
    match p.polygon_type() {
        PolygonType::Convex => gjk::convex_intersects(r, p),
        PolygonType::Concave(parts) => parts
            .iter()
            .any(|triangle| gjk::convex_intersects(r, triangle)),
    }
}

/// Helper: Intersection between two Polygons (handles recursive Concave checks).
fn poly_vs_poly_intersect(a: &Polygon, b: &Polygon) -> bool {
    match (&a.polygon_type(), &b.polygon_type()) {
        (PolygonType::Convex, PolygonType::Convex) => gjk::convex_intersects(a, b),
        // Recursive handling for Concave
        // Note: We call this same function recursively
        (PolygonType::Concave(parts), _) => {
            parts.iter().any(|part| gjk::convex_intersects(part, b))
        }

        (_, PolygonType::Concave(parts)) => {
            parts.iter().any(|part| gjk::convex_intersects(a, part))
        }
    }
}

/// Helper: Distance between Rectangle and Polygon (handles Concave polygons).
fn rect_vs_poly_distance(r: &Rectangle, p: &Polygon) -> gjk::Proximity {
    match &p.polygon_type() {
        PolygonType::Convex => {
            // Atomic check
            gjk::convex_distance(r, p)
        }
        PolygonType::Concave(parts) => {
            // Aggregate all parts, finding the closest one
            parts
                .iter()
                .map(|part| rect_vs_poly_distance(r, part))
                .fold(gjk::Proximity::max_value(), |closest, current| {
                    closest.min(current)
                })
        }
    }
}

/// Helper: Distance between two Polygons (handles recursive Concave checks).
fn poly_vs_poly_distance(a: &Polygon, b: &Polygon) -> gjk::Proximity {
    match (&a.polygon_type(), &b.polygon_type()) {
        // 1. Atomic Base Case: Convex vs Convex
        (PolygonType::Convex, PolygonType::Convex) => gjk::convex_distance(a, b),

        (PolygonType::Concave(parts), _) => parts
            .iter()
            .map(|part| poly_vs_poly_distance(part, b))
            .fold(gjk::Proximity::max_value(), |closest, current| {
                closest.min(current)
            }),

        // 3. Recursive Case: B is Concave (and A is Convex)
        // We iterate ALL parts of B against the atomic shape A.
        (_, PolygonType::Concave(parts)) => parts
            .iter()
            .map(|part| poly_vs_poly_distance(a, part))
            .fold(gjk::Proximity::max_value(), |closest, current| {
                closest.min(current)
            }),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geo::Vertex;
    use crate::geo::gjk::Proximity;

    #[test]
    fn test_intersection_concave() {
        let poly_star = Polygon::new(vec![
            Vertex::new(0, 5),   // V1: Top Outer Point
            Vertex::new(2, 2),   // V2: Inner Dip 1
            Vertex::new(5, 2),   // V3: Outer Point 2
            Vertex::new(3, -1),  // V4: Inner Dip 2
            Vertex::new(4, -4),  // V5: Outer Point 3
            Vertex::new(0, -3),  // V6: Inner Dip 3
            Vertex::new(-4, -4), // V7: Outer Point 4
            Vertex::new(-3, -1), // V8: Inner Dip 4
            Vertex::new(-5, 2),  // V9: Outer Point 5 (Slightly asymmetric but integer)
            Vertex::new(-2, 2),  // V10: Inner Dip 5 (Slightly asymmetric but integer)
        ]);
        let poly_c_shape = Polygon::new(vec![
            Vertex::new(2, 0), // V1: Bottom-Left
            Vertex::new(8, 0), // V2: Bottom-Right
            Vertex::new(8, 6), // V3: Top-Right
            Vertex::new(2, 6), // V4: Top-Left
            Vertex::new(4, 4), // V5: Start of the inward cut (Concave angle)
            Vertex::new(4, 2), // V6: The inner corner (Concave angle)
        ]);

        let proximity =
            Shape::Polygon(poly_star.clone()).distance(&Shape::Polygon(poly_c_shape.clone()));
        // The star and C-shape should intersect
        match proximity {
            Proximity::Separated(sep) => {
                panic!("Shapes should intersect, but got separation: {:?}", sep)
            }
            Proximity::Intersecting => (), // Expected
        };
    }

    #[test]
    fn test_non_intersection_concave() {
        let poly_star = Polygon::new(vec![
            Vertex::new(0, 5),   // V1: Top Outer Point
            Vertex::new(2, 2),   // V2: Inner Dip 1
            Vertex::new(5, 2),   // V3: Outer Point 2
            Vertex::new(3, -1),  // V4: Inner Dip 2
            Vertex::new(4, -4),  // V5: Outer Point 3
            Vertex::new(0, -3),  // V6: Inner Dip 3
            Vertex::new(-4, -4), // V7: Outer Point 4
            Vertex::new(-3, -1), // V8: Inner Dip 4
            Vertex::new(-5, 2),  // V9: Outer Point 5 (Slightly asymmetric but integer)
            Vertex::new(-2, 2),  // V10: Inner Dip 5 (Slightly asymmetric but integer)
        ]);
        let poly_c_shape = Polygon::new(vec![
            Vertex::new(10, 0), // V1: Bottom-Left
            Vertex::new(16, 0), // V2: Bottom-Right
            Vertex::new(16, 6), // V3: Top-Right
            Vertex::new(10, 6), // V4: Top-Left
            Vertex::new(12, 4), // V5: Start of the inward cut (Concave angle)
            Vertex::new(12, 2), // V6: The inner corner (Concave angle)
        ]);
        let shape_star = Shape::Polygon(poly_star.clone());
        let shape_c = Shape::Polygon(poly_c_shape.clone());

        assert!(
            !shape_star.aabb().intersects(shape_c.aabb()),
            "AABBs should not intersect"
        );

        let proximity = shape_star.distance(&shape_c);
        // The star and C-shape should intersect
        let separation = match proximity {
            Proximity::Separated(sep) => sep,
            Proximity::Intersecting => panic!("Shapes should not intersect, but got intersection"),
        };
        // closest points are (5,2) and (10,0)
        assert_eq!(
            separation.distance,
            ((5.0f64).powi(2) + (2.0f64).powi(2)).sqrt(),
            "Distance should be correct, got {}, should have been {}",
            separation.distance,
            ((5.0f64).powi(2) + (2.0f64).powi(2)).sqrt()
        );

        // x clearance should be the point crossing the x axis between (5,2) and (3, -1) for star
        // so x=3 + (2/3)*2 = 3 + 4/3 = 13/3 = 4.3333 and (10,0) for C-shape
        let expected_x_clearance = 10.0f64 - (11.0f64 / 3.0f64);
        assert!(
            (separation.x_clearance - expected_x_clearance).abs() < 1e-4,
            "X clearance should be correct, got {}, should have been {}",
            separation.x_clearance,
            expected_x_clearance
        );
        assert!(
            separation.y_clearance.is_infinite(),
            "Y clearance should be infinite"
        );
    }
}
