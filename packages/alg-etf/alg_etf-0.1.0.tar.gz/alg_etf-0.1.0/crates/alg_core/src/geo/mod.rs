//! # Geometry and Collision Detection Module
//!
//! This module provides a collection of the 2D geometric primitives and algorithms
//! needed for layout design in the style of GDSII, with a strong emphasis on robust collision
//! detection
//!
//! ## Core Features
//!
//! * **Primitives:**
//!     * [`Rectangle`]: Axis-aligned rectangles.
//!     * [`Polygon`]: Supports both convex and concave shapes (automatically triangulated).
//!     * [`Path`]: Thickened lines/wires with configurable end-caps (Butt, Square, Round).
//!     * [`Shape`]: A unified wrapper allowing heterogeneous collections of the above.
//!     * [`Boundary`]: The boundary representation for a layer or cell, composed of one or more
//!       polygons.
//!     
//! * **Coordinate System:**
//!     * [`Vertex`]: Integer-based coordinates for precise grid/pixel alignment (needed for GDSII).
//!     * [`Vector2`]: Floating-point vectors for collision calculations and direction vectors.
//!
//! * **Collision Detection & Proximity:**
//!     * **Broad Phase:** [`AABB`] (Axis-Aligned Bounding Box) for fast rejection tests.
//!     * **Narrow Phase:** Gilbert-Johnson-Keerthi ([`gjk`]) algorithm for robust convex shape analysis.
//!     * **Proximity Analysis:** Unlike simple boolean checks, the `distance` methods return detailed [`gjk::Proximity`] data:
//!         * **Intersecting:** Indicates shapes are touching or overlapping.
//!         * **Separated:** Provides precise metrics for disjoint shapes, including:
//!             * **Distance:** Minimum Euclidean distance between the shapes.
//!             * **Vector:** The shortest vector connecting the shapes.
//!             * **Clearance:** Axis-aligned (X/Y) distances indicating how far shapes can move before collision.
//!
//! * **Algorithms:**
//!     * [`triangulate_polygon`]: Decomposes complex polygons into triangles using Ear Clipping.
//!     * [`is_convex`]: Validates geometric properties.
//!
//! ## Example Usage
//!
//! ```rust
//! use alg_core::geo::{Rectangle, Polygon, Vertex, Shape};
//! use alg_core::geo::gjk;
//!
//! // 1. Create a Rectangle
//! let rect = Rectangle::new(Vertex::new(0, 0), Vertex::new(10, 10));
//!
//! // 2. Create a Triangle (Polygon)
//! let poly = Polygon::new(vec![
//!     Vertex::new(5, 5),
//!     Vertex::new(15, 5),
//!     Vertex::new(10, 15),
//! ]);
//!
//! // 3. Wrap them in the generic Shape enum
//! let shape_a = Shape::Rectangle(rect);
//! let shape_b = Shape::Polygon(poly);
//!
//! // 4. Check for intersection
//! if shape_a.intersects(&shape_b) {
//!     println!("Shapes are colliding!");
//! }
//!
//! // 5. Analyze Proximity
//! match shape_a.distance(&shape_b) {
//!     gjk::Proximity::Intersecting => {
//!         println!("Shapes are colliding!");
//!     },
//!     gjk::Proximity::Separated(info) => {
//!         println!("Shapes are {:.2} units apart.", info.distance);
//!         println!("Vector to close gap: {:?}", info.vector);
//!         println!("Clearance X: {}, Y: {}", info.x_clearance, info.y_clearance);
//!     }
//! }
//! ```

pub mod aabb;
pub mod boundary;
pub mod gjk;
pub mod path;
pub mod polygon;
pub mod rectangle;
pub mod shape;
pub mod triangulation;
pub mod vector2;
pub mod vertex;

pub use aabb::AABB;
pub use boundary::Boundary;
pub use gjk::Support;
pub use path::Path;
pub use polygon::Polygon;
pub use rectangle::Rectangle;
pub use shape::Shape;
pub use triangulation::{is_convex, triangulate_polygon};
pub use vector2::Vector2;
pub use vertex::Vertex;
