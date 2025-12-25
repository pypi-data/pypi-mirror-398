use std::f64;

use crate::{
    geo::{AABB, Polygon, Vector2, Vertex},
    library::instance::Translate,
};

/// Represents a "thickened" wire or trace defined by a central skeleton and a width.
///
/// A `Path` is geometrically more complex than a [`Polygon`]. While defined by a simple
/// list of points, its physical presence is determined by sweeping a shape along that line.
///
/// # Collision Detection
///
/// For collision detection purposes, a `Path` is typically **decomposed** into a series
/// of convex polygons (segments) using the [`Path::decompose`] method.
#[derive(Debug, Clone)]
pub struct Path {
    /// The width of the path in integer units.
    width: u32,
    /// The list of vertices defining the central "skeleton" of the path.
    vertices: Vec<Vertex>,
    /// The style of the path endpoints.
    endstyle: EndStyle,
    /// The pre-calculated bounding box covering the entire thickened path.
    aabb: AABB,
}

/// Defines how the endpoints of a [`Path`] are rendered.
///
/// These styles correspond directly to the standard GDSII Path Types.
#[derive(Debug, Clone, Copy)]
pub enum EndStyle {
    Butt,   // GDSII Pathtype 0 (Flush)
    Round,  // GDSII Pathtype 1 (Round)
    Square, // GDSII Pathtype 2 (Extended)
}

impl Path {
    /// Creates a new Path.
    ///
    /// This constructor calculates the required bounding box padding immediately.
    ///
    /// # Parameters
    ///
    /// * `vertices`: The center-line points.
    /// * `width`: The total width of the path.
    /// * `endstyle`: How to handle the start and end points.
    pub fn new(vertices: Vec<Vertex>, width: u32, endstyle: EndStyle) -> Self {
        let skeleton_aabb = AABB::from_vertices(&vertices);

        // Calculate the "padding" needed around the skeleton to cover thickness/caps
        let padding = Self::calculate_padding(width, endstyle);

        // Expand the skeleton AABB by this padding
        let aabb = skeleton_aabb.expand(padding);

        Self {
            width,
            vertices,
            endstyle,
            aabb,
        }
    }

    pub const fn width(&self) -> u32 {
        self.width
    }

    pub const fn vertices(&self) -> &Vec<Vertex> {
        &self.vertices
    }

    pub const fn endstyle(&self) -> &EndStyle {
        &self.endstyle
    }

    /// Returns the cached Axis-Aligned Bounding Box (AABB).
    pub const fn aabb(&self) -> &AABB {
        &self.aabb
    }

    /// Decomposes the Path into an iterator of convex [`Polygon`]s.
    ///
    /// This is essential for GJK-based collision detection. The iterator yields a
    /// `Polygon` for every segment of the path.
    pub fn decompose(&self) -> impl Iterator<Item = Polygon> + '_ {
        self.vertices
            .windows(2)
            .map(move |w| self.create_segment_polygon(w[0], w[1]))
    }

    pub fn transform(&self, translate: &Translate) -> Self {
        let transformed_vertices: Vec<Vertex> = self
            .vertices
            .iter()
            .map(|v| translate.transform_vertex(*v))
            .collect();

        Self::new(transformed_vertices, self.width, self.endstyle)
    }

    /// Calculates the maximum distance from the center-line to the edge of the path.
    ///
    /// This is used to expand the skeleton AABB.
    /// * **Butt/Round:** The extent is exactly `width / 2`.
    /// * **Square:** The corners of the square cap extend diagonally, requiring `width / 2 * sqrt(2)`.
    fn calculate_padding(width: u32, style: EndStyle) -> i32 {
        let half_width = width as f64 / 2.0;

        let extension = match style {
            EndStyle::Butt | EndStyle::Round => half_width,
            EndStyle::Square => half_width * f64::consts::SQRT_2,
        };

        // Round up to ensure we cover every integer pixel
        extension.ceil() as i32
    }

    /// Generates a single convex polygon for a path segment defined by `p1` and `p2`.
    fn create_segment_polygon(&self, p1: Vertex, p2: Vertex) -> Polygon {
        let half_width = self.width as f64 / 2.0;

        // 1. Vector Setup
        let v1 = Vector2::new(p1.x() as f64, p1.y() as f64);
        let v2 = Vector2::new(p2.x() as f64, p2.y() as f64);

        let dir = v2 - v1;
        let len = dir.mag_sq().sqrt();

        // Handle tiny segments safely
        if len < 1e-4 {
            // Small constant is fine here, it's not GJK_TOLERANCE related
            return self.create_point_poly(p1, half_width);
        }

        // 2. Calculate Normal (Perpendicular vector)
        let unit_dir = dir * (1.0 / len);
        let normal = Vector2::new(-unit_dir.y(), unit_dir.x()) * half_width;

        match self.endstyle {
            // Path Type 0: Flush at endpoints.
            // Vertices are simply shifted out by the normal.
            EndStyle::Butt => {
                let c1 = v1 + normal;
                let c2 = v1 - normal;
                let c3 = v2 - normal;
                let c4 = v2 + normal;

                Polygon::new(vec![
                    Self::to_vertex(c1),
                    Self::to_vertex(c2),
                    Self::to_vertex(c3),
                    Self::to_vertex(c4),
                ])
            }

            // Pathtype 1: Round endpoints
            // TODO: Requires creating a polygon with enough vertices to approximate a semi-circle.
            EndStyle::Round => {
                todo!("Round endstyle polygon generation not implemented yet");
            }

            // Path Type 2: Extend endpoints by half_width.
            // We move the start/end points outward along the direction vector before applying the normal.
            EndStyle::Square => {
                let extension = unit_dir * half_width;
                let s = v1 - extension; // Start extended back
                let e = v2 + extension; // End extended forward

                let c1 = s + normal;
                let c2 = s - normal;
                let c3 = e - normal;
                let c4 = e + normal;

                Polygon::new(vec![
                    Self::to_vertex(c1),
                    Self::to_vertex(c2),
                    Self::to_vertex(c3),
                    Self::to_vertex(c4),
                ])
            }
        }
    }

    /// Helper to create a tiny square polygon for degenerate segments (points).
    fn create_point_poly(&self, p: Vertex, r: f64) -> Polygon {
        let ri = r.ceil() as i32;
        // Tiny square
        Polygon::new(vec![
            Vertex::new(p.x() - ri, p.y() - ri),
            Vertex::new(p.x() + ri, p.y() - ri),
            Vertex::new(p.x() + ri, p.y() + ri),
            Vertex::new(p.x() - ri, p.y() + ri),
        ])
    }
    /// Converts a floating-point `Vector2` to an integer `Vertex` by rounding.
    const fn to_vertex(v: Vector2) -> Vertex {
        Vertex::new(v.x().round() as i32, v.y().round() as i32)
    }
}
