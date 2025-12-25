use crate::{
    geo::{AABB, Polygon, Shape, gjk},
    library::instance::Translate,
};

/// Represents the geometric footprint of a Cell or Layer.
///
/// A `Boundary` is a collection of one or more [Polygon]s bounded by a global [AABB].
/// It acts as the primary structure for performing "Correct-by-Design" spacing and
/// overlap checks between different layers or cells.
#[derive(Debug, Clone)]
pub struct Boundary {
    /// The collection of polygons that form this boundary's outline.
    ///
    /// *Note:* In this implementation, disjoint shapes are separate polygons.
    /// Overlapping shapes are currently stored as separate polygons (union is not yet applied).
    // TODO: Implement polygon merging to minimize the polygon list.
    polygons: Vec<Polygon>,
    /// A conservative Axis-Aligned Bounding Box covering all polygons in the list.
    /// Used for O(1) broad-phase rejection.
    bounding_aabb: AABB,
}

impl Default for Boundary {
    fn default() -> Self {
        Self::new()
    }
}

impl Boundary {
    /// Creates a new, empty Boundary with an inverted (empty) AABB.
    pub const fn new() -> Self {
        Self {
            polygons: Vec::new(),
            bounding_aabb: AABB::empty(),
        }
    }

    /// Adds a generic [Shape] to the boundary.
    ///
    /// This method handles geometric decomposition automatically:
    /// * **[Polygon]:** Added directly.
    /// * **[crate::geo::Rectangle]:** Converted to a 4-vertex Polygon.
    /// * **[crate::geo::Path]:** Decomposed into its constituent convex segments, which are all added.
    ///
    /// The [AABB] of the boundary is updated to include the new shape.
    pub fn from_shape(&mut self, shape: &Shape) {
        // Convert Shape to Polygons and add to list
        match shape {
            Shape::Polygon(p) => {
                // If it's a concave polygon, it stays as one "Polygon" struct
                // (which handles its own decomposition during GJK).
                self.polygons.push(p.clone());
            }
            Shape::Rectangle(r) => {
                self.polygons.push(r.to_polygon());
            }
            Shape::Path(p) => {
                // Path decomposes into multiple convex polygons
                self.polygons.extend(p.decompose());
            }
        }

        // Compute AABBs by taking the union of all polygon AABBs
        // The shape itself already has an AABB method we can use.
        self.bounding_aabb = self.bounding_aabb.union(shape.aabb());

        // TODO: This does NOT perform true union of overlapping polygons yet.
        // an algorithm to minimize the polygon list by merging overlapping shapes needs
        // to be implemented here.
        // todo!("Implement true union of overlapping polygons here.");
    }

    /// Checks if *any* [Polygon] in this boundary intersects with *any* polygon in another boundary.
    ///
    /// # Complexity
    ///
    /// * **Best Case:** $O(1)$ (Broad-phase [AABB] rejection).
    /// * **Worst Case:** $O(N \cdot M)$ where N and M are the number of [Polygon]s in each boundary.
    pub fn intersects(&self, other: &Self) -> bool {
        // 1. Broad-phase AABB check
        if !self.bounding_aabb.intersects(&other.bounding_aabb) {
            return false;
        }
        // 2. Narrow-phase polygon checks
        for p1 in &self.polygons {
            for p2 in &other.polygons {
                let shape1 = Shape::Polygon(p1.clone());
                let shape2 = Shape::Polygon(p2.clone());

                if shape1.intersects(&shape2) {
                    return true;
                }
            }
        }
        false
    }

    /// Calculates the minimum Euclidean distance between this boundary and another.
    /// Uses [`gjk::convex_distance`] internally for precise polygon distance checks.
    ///
    /// This iterates over all polygon pairs to find the global minimum separation.
    ///
    /// # Returns
    /// * [`gjk::Proximity::Intersecting`] if they overlap.
    /// * [`gjk::Proximity::Separated`] with distance vector/scalar as well as the x and y
    ///   clearance.
    pub fn distance(&self, other: &Self) -> gjk::Proximity {
        let mut min_proximity = gjk::Proximity::max_value();

        for p1 in &self.polygons {
            for p2 in &other.polygons {
                // TODO: Optimize the .clone by having Shape::Polygon hold a reference
                let shape1 = Shape::Polygon(p1.clone());
                let shape2 = Shape::Polygon(p2.clone());

                min_proximity = min_proximity.min(shape1.distance(&shape2));

                // Optimization: Early exit if we find an intersection,
                // as distance cannot get smaller than 0.
                if matches!(min_proximity, gjk::Proximity::Intersecting) {
                    return gjk::Proximity::Intersecting;
                }
            }
        }
        min_proximity
    }

    /// Creates a new [Boundary] where every constituent polygon is geometrically expanded.
    ///
    /// # Parameters
    ///
    /// * `amount`: The distance (in integer units) to expand the polygon edges.
    ///
    /// # Logic
    ///
    /// This performs an eager geometric expansion:
    /// 1. Iterates over every polygon.
    /// 2. Calls [`Polygon::expand`] to generate offset vertices.
    /// 3. Recalculates the new global AABB.
    ///
    /// *Note: This does not merge overlapping polygons; the number of polygons remains constant.*    
    pub fn expand(&self, amount: i32) -> Self {
        if amount <= 0 {
            return self.clone();
        }
        // First expand the polygons by the given amount
        let expanded_polygons: Vec<Polygon> =
            self.polygons.iter().map(|p| p.expand(amount)).collect();

        // Recalculate the bounding AABB
        let mut expanded_aabb = AABB::empty();
        for p in &expanded_polygons {
            expanded_aabb = expanded_aabb.union(p.aabb());
        }

        // Also expand the AABB explicitly to ensure the bounds cover everything,
        // even if Polygon::expand is a no-op placeholder.
        expanded_aabb = expanded_aabb.expand(amount);

        Self {
            polygons: expanded_polygons,
            bounding_aabb: expanded_aabb,
        }
    }

    /// Transforms the entire boundary by a given translation/rotation.
    pub fn transform(&self, t: &Translate) -> Self {
        let transformed_polys: Vec<Polygon> =
            self.polygons.iter().map(|p| p.transform(t)).collect();

        let mut new_aabb = AABB::empty();
        for p in &transformed_polys {
            new_aabb = new_aabb.union(p.aabb());
        }

        Self {
            polygons: transformed_polys,
            bounding_aabb: new_aabb,
        }
    }

    /// Merges another boundary into this one.
    ///
    /// This adds all polygons from the other boundary to this one and updates the AABB.
    pub fn merge(&mut self, other: &Self) {
        self.polygons.extend(other.polygons.clone());
        self.bounding_aabb = self.bounding_aabb.union(&other.bounding_aabb);
    }

    /// Returns a reference to the list of polygons.
    pub const fn polygons(&self) -> &Vec<Polygon> {
        &self.polygons
    }

    /// Returns the cached broad-phase AABB.
    pub const fn aabb(&self) -> &AABB {
        &self.bounding_aabb
    }
}
