use crate::geo::AABB;
use crate::geo::Support;
use crate::geo::Vector2;
use crate::geo::Vertex;
use crate::geo::is_convex;
use crate::geo::triangulate_polygon;
use crate::library::instance::Translate;

/// Represents a 2D polygon defined by a list of vertices.
///
/// This struct handles both convex and concave shapes. Upon creation, it automatically
/// analyzes the geometry:
/// 1.  Calculates the Axis-Aligned Bounding Box ([`AABB`]).
/// 2.  Checks for convexity using [`is_convex`].
/// 3.  If concave, it decomposes the shape into triangles using [`triangulate_polygon`].
#[derive(Debug, Clone)]
pub struct Polygon {
    vertices: Vec<Vertex>, // List of vertices defining the polygon
    type_: PolygonType,    // Convex or Concave (with triangles if concave)
    aabb: AABB,            // Axis-aligned bounding box (min, max)
}

/// Classification of a polygon's geometric nature.
///
/// This enum determines how the polygon is handled in collision detection algorithms.
/// * **Convex:** The polygon is processed as a single entity using GJK.
/// * **Concave:** The polygon is decomposed into a set of convex triangles. Algorithms must
///   iterate over these sub-polygons.
#[derive(Debug, Clone)]
pub enum PolygonType {
    /// A simple convex polygon.
    Convex,
    /// A concave polygon represented by a list of convex triangles.
    Concave(Vec<Polygon>),
}

impl Polygon {
    /// Creates a new polygon from a list of vertices.
    ///
    /// This constructor performs significant initialization work:
    /// 1.  Computes the AABB ($O(V)$).
    /// 2.  Checks convexity ($O(V)$).
    /// 3.  If concave, triangulates the polygon ($O(V^2)$).
    ///
    /// # Parameters
    ///
    /// * `vertices`: A list of vertices defining the boundary.
    pub fn new(vertices: Vec<Vertex>) -> Self {
        let aabb = AABB::from_vertices(&vertices);

        if is_convex(&vertices) {
            Self {
                vertices,
                type_: PolygonType::Convex,
                aabb,
            }
        } else {
            // Decompose the concave polygon into convex triangles
            let triangulated_polygons = triangulate_polygon(&vertices);

            // Recursively create Polygon instances for each triangle.
            // Note: Triangles are guaranteed to be convex
            let triangles: Vec<Self> = triangulated_polygons.into_iter().map(Self::new).collect();

            Self {
                vertices,
                type_: PolygonType::Concave(triangles),
                aabb,
            }
        }
    }

    /// Returns a reference to the vertices defining the polygon.
    pub const fn vertices(&self) -> &Vec<Vertex> {
        &self.vertices
    }

    /// Returns the geometric classification (Convex or Concave).
    pub const fn polygon_type(&self) -> &PolygonType {
        &self.type_
    }

    /// Returns the cached Axis-Aligned Bounding Box (AABB).
    pub const fn aabb(&self) -> &AABB {
        &self.aabb
    }

    // TODO: Implement and test min_width for Polygon and all other shapes
    pub fn min_width(&self) -> u32 {
        todo!("Polygon min_width not yet implemented and tested");
        // let mut min_width = u32::MAX;
        // let n = self.vertices.len();
        //
        // for i in 0..n {
        //     let v1 = &self.vertices[i];
        //     let v2 = &self.vertices[(i + 1) % n]; // Wrap around to the first vertex
        //
        //     let width: u32 = if v2.x() > v1.x() {
        //         (v2.x() - v1.x()).try_into().unwrap()
        //     } else {
        //         (v2.x() - v1.x()).try_into().unwrap()
        //     };
        //
        //     if width < min_width {
        //         min_width = width;
        //     }
        // }
        //
        // min_width
    }

    // TODO: Expands the polygon outward by a specified amount.
    pub fn expand(&self, _amount: i32) -> Self {
        // Placeholder: Returning self to allow compilation.
        // Real geometric buffering requires complex Minkowski sum logic.
        self.clone()
    }

    /// Transforms the polygon using the given `Translate` (orientation + offset).
    pub fn transform(&self, t: &Translate) -> Self {
        let new_verts: Vec<Vertex> = self
            .vertices
            .iter()
            .map(|v| t.transform_vertex(*v))
            .collect();
        Self::new(new_verts)
    }
}

/// Implements the GJK Support mapping for a Polygon.
///
/// Finds the vertex that is furthest in the given direction.
///
/// # Note on Concavity
///
/// This implementation treats the polygon effectively as its **Convex Hull**.
/// If called on a concave polygon, it returns the furthest point on the outer boundary,
/// effectively ignoring the concavity "dents".
///
/// * For GJK intersection tests against a concave polygon, you must iterate over
///   the triangles in `PolygonType::Concave`.
/// * For broad-phase or convex-hull approximations, this method is sufficient.
///
/// # Time Complexity
///
/// $O(V)$ (Linear scan of all vertices)
impl Support for Polygon {
    fn support(&self, dir: &Vector2) -> Vector2 {
        self.vertices
            .iter()
            .map(|v| Vector2::new(v.x() as f64, v.y() as f64))
            .max_by(|a, b| a.dot(dir).partial_cmp(&b.dot(dir)).unwrap())
            .unwrap_or_else(|| Vector2::new(0.0, 0.0))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geo::Vertex;

    #[test]
    fn test_new_polygon() {
        let points = vec![Vertex::new(0, 0), Vertex::new(1, 0), Vertex::new(0, 1)];
        let polygon = Polygon::new(points.clone());

        assert_eq!(polygon.vertices.len(), 3, "Polygon should have 3 vertices");
        assert_eq!(polygon.vertices, points)
    }

    #[test]
    fn test_getters_polygon() {
        let points = vec![Vertex::new(2, 3), Vertex::new(4, 5), Vertex::new(6, 7)];
        let polygon = Polygon::new(points.clone());

        assert_eq!(
            polygon.vertices(),
            &points,
            "Vertices should match the input points"
        );
    }

    #[test]
    fn test_polygon_with_no_vertices() {
        let polygon = Polygon::new(vec![]);
        assert_eq!(
            polygon.vertices().len(),
            0,
            "Polygon should have no vertices"
        );
    }

    #[test]
    fn test_aabb_of_polygon() {
        let points = vec![Vertex::new(1, 2), Vertex::new(3, 4), Vertex::new(0, 5)];
        let polygon = Polygon::new(points);

        let aabb = polygon.aabb();
        assert_eq!(aabb.min, Vertex::new(0, 2), "AABB min should be (0,2)");
        assert_eq!(aabb.max, Vertex::new(3, 5), "AABB max should be (3,5)");
    }
}
