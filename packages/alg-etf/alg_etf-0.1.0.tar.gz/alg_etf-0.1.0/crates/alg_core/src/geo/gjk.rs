use crate::geo::Vector2;

pub const GJK_TOLERANCE: f64 = 1e-4;

/// Describes the spatial separation between two non-intersecting shapes.
///
/// This struct contains both the minimum Euclidean distance/vector and the
/// axis-aligned clearance values (how far the shapes can move before touching).
///
/// # Fields
///
/// * `distance`: The minimum Euclidean distance between the closest points on the two shapes.
/// * `vector`: The vector representing the shortest path between the closest points.
/// * `x_clearance`: The distance Shape A can move along the X-axis before colliding with Shape B.
/// * `y_clearance`: The distance Shape A can move along the Y-axis before colliding with Shape B.
///
/// # Notes
///
/// * **Precision:** Values are stored as floating-point to handle geometries that are not
///   integer-aligned. While input vertices may be integers, the resulting separation lines
///   are continuous.
/// * **Manufacturing:** For manufacturing purposes, these floating-point results may need
///   to be snapped or aligned to a specific pixel grid or tolerance.
/// * **Unbounded Clearance:** An infinite value (`f64::INFINITY`) for `x_clearance` or
///   `y_clearance` indicates that the shapes are unbounded relative to each other in that
///   direction (i.e., they will never collide if moved along that axis).
/// * **Directionality:** A negative clearance value indicates that Shape A can move in the
///   negative direction (left for X, down for Y) before collision.

#[derive(Debug, Clone, Copy)]
pub struct Separation {
    pub distance: f64,
    pub vector: Vector2,
    pub x_clearance: f64,
    pub y_clearance: f64,
}

/// Represents the spatial proximity relationship between two geometric shapes.
///
/// This enum indicates whether two shapes are entirely disjoint or if they share
/// any common points (touching or overlapping).
#[derive(Debug, Clone, Copy)]
pub enum Proximity {
    /// The shapes are disjoint (not intersecting).
    ///
    /// This variant contains a [`Separation`] struct with detailed information,
    /// including the minimum Euclidean distance and axis-aligned clearance values.
    Separated(Separation),

    /// The shapes are intersecting, overlapping, or touching at the boundary.
    ///
    /// In this state, the distance between the shapes is considered zero.
    Intersecting,
}

impl Proximity {
    /// Combines two proximity results to find the closest relationship.
    ///
    /// This method is typically used when merging results from multiple shape pairs
    /// to determine the overall proximity of a complex object.
    ///
    /// # Behavior
    ///
    /// * **Intersection Precedence:** If either `self` or `other` is [`Proximity::Intersecting`],
    ///   the result is immediately `Intersecting` (implying a distance of 0).
    /// * **Merging Separations:** If both are [`Separated`](Proximity::Separated), a new separation
    ///   is calculated:
    ///     * `distance` and `vector` are taken from the pair with the smaller Euclidean distance.
    ///     * `x_clearance` and `y_clearance` are calculated as the independent minimums
    ///       of both inputs. This ensures the clearance values represent the tightest
    ///       constraint across all checked shapes.
    pub fn min(self, other: Self) -> Self {
        match (self, other) {
            // If either is intersecting, the result is intersecting (distance 0)
            (Self::Intersecting, _) => Self::Intersecting,
            (_, Self::Intersecting) => Self::Intersecting,

            // If both are separated, merge the results
            (Self::Separated(a), Self::Separated(b)) => {
                // Determine which object provides the primary distance & vector
                // We keep the vector coupled to the distance it represents.
                let (closest, _furthest) = if a.distance < b.distance {
                    (a, b)
                } else {
                    (b, a)
                };

                Self::Separated(Separation {
                    // The physical closest point dictates the distance and normal vector
                    distance: closest.distance,
                    vector: closest.vector,

                    // The x and y clearances are not coupled to the distance/vector.
                    // They should be the minimum values from both separations (the tightest fit).
                    x_clearance: a.x_clearance.min(b.x_clearance),
                    y_clearance: a.y_clearance.min(b.y_clearance),
                })
            }
        }
    }
    /// Returns a sentinel `Proximity` value representing maximum separation.
    ///
    /// This value acts as an identity element for minimization processes. It can be used
    /// to initialize a variable before iterating over multiple shape pairs to find
    /// the closest proximity.
    ///
    /// # Returns
    ///
    /// A `Separated` variant with `distance` set to `f64::MAX` and clearances set to `f64::INFINITY`.
    pub const fn max_value() -> Self {
        Self::Separated(Separation {
            distance: f64::MAX,
            x_clearance: f64::INFINITY,
            y_clearance: f64::INFINITY,
            vector: Vector2::new(f64::MAX, f64::MAX),
        })
    }
}

/// The fundamental trait for GJK-compatible geometric shapes.
///
/// Any shape (Polygon, Path, Rectangle, etc.) that implements this trait can be used
/// with the GJK intersection and distance algorithms.
///
/// The `support` method implements the "support mapping" function $S_A(d)$,
/// which finds the extreme point of the shape in a given direction.
pub trait Support {
    /// Returns the point on the shape that is furthest in the given `direction`.
    ///
    /// This point is guaranteed to be on the perimeter of the shape.
    /// If multiple points are equally far in that direction (e.g., an edge is perpendicular
    /// to the direction), any one of those points may be returned.
    ///
    /// # Parameters
    ///
    /// * `direction`: A vector indicating the search direction. It does not need to be normalized.
    fn support(&self, direction: &Vector2) -> Vector2;
}

/// Determines whether two convex shapes intersect using the Gilbert-Johnson-Keerthi (GJK) algorithm.
///
/// This function is optimized specifically for a boolean intersection test. It returns `true`
/// immediately if an intersection is found, without calculating the exact penetration depth
/// or separation distance.
///
/// # Algorithm Background
///
/// The GJK algorithm determines intersection by analyzing the **Minkowski Difference** of two shapes
/// ($A \ominus B$). The Minkowski Difference is formed by subtracting every point in shape $B$
/// from every point in shape $A$.
///
/// * If the shapes intersect, their Minkowski Difference contains the origin $(0, 0)$.
/// * If they do not intersect, the origin lies outside the Minkowski Difference.
///
/// Instead of computing the full geometry of the Minkowski Difference (which is computationally
/// expensive), GJK iteratively builds a **Simplex** (a point, line segment, or triangle) inside
/// the Minkowski Difference. It tries to enclose the origin within this simplex.
///
/// # Returns
///
/// * `true` if the shapes overlap or touch.
/// * `false` if the shapes are strictly separated.
///
/// # Time Complexity
///
/// $O(V_A + V_B)$
///
/// Where $V_A$ and $V_B$ are the number of vertices in shape A and B respectively.
/// The algorithm typically converges in a very small, constant number of iterations for 2D convex shapes,
/// making it extremely efficient.
pub fn convex_intersects<A: Support, B: Support>(shape_a: &A, shape_b: &B) -> bool {
    let mut dir = Vector2::new(1.0, 0.0);
    let mut simplex: Vec<Vector2> = Vec::with_capacity(3);

    // 1. Get the first point on the Minkowski Difference
    let c = minkowski_diff(shape_a, shape_b, &dir);
    simplex.push(c);

    // 2. Search towards the origin
    dir = -c;

    loop {
        // 3. Get the next point in the search direction
        let a = minkowski_diff(shape_a, shape_b, &dir);

        // 4. Check if we passed the origin
        if a.dot(&dir) < -GJK_TOLERANCE {
            return false;
        }

        simplex.push(a);

        // 5. Check if the simplex contains the origin
        if simplex_contains_origin(&mut simplex, &mut dir) {
            return true;
        }
    }
}

/// Computes the detailed spatial separation between two convex shapes.
///
/// This function performs a complete proximity analysis. It determines if the shapes are
/// intersecting, and if not, calculates exactly how far apart they are and how much
/// clearance exists along the principal axes.
///
/// # Algorithm Overview
///
/// The function operates in two phases:
///
/// 1.  **GJK Distance Algorithm:**
///     It iteratively evolves a simplex on the Minkowski Difference to find the point closest
///     to the Origin. The vector from this point to the Origin represents the minimum translation
///     vector required to bring the shapes into contact.
///
/// 2.  **Axis Casting (Clearance):**
///     Once the separation vector is known, the function performs a binary search (ray cast)
///     along the X and Y axes. This determines the maximum distance `shape_a` can move along
///     those axes before colliding with `shape_b`.
///
/// # Returns
///
/// * [`Proximity::Intersecting`]: If the shapes are touching or overlapping.
/// * [`Proximity::Separated`]: If the shapes are disjoint. This variant contains:
///     * `distance`: The minimum Euclidean distance.
///     * `vector`: The translation vector to bring the shapes together.
///     * `x_clearance` / `y_clearance`: The allowable movement along the axes.
///
/// # Time Complexity
///
/// $O(V_A + V_B)$
///
/// Although this function performs more iterations than `convex_intersects` (due to the ray casting phase),
/// the number of iterations $k$ is capped by a constant, keeping the
/// overall complexity linear with respect to the number of vertices.
pub fn convex_distance<A: Support, B: Support>(shape_a: &A, shape_b: &B) -> Proximity {
    let mut dir = Vector2::new(1.0, 0.0);

    // First, check for intersection quickly
    if convex_intersects(shape_a, shape_b) {
        return Proximity::Intersecting;
    }

    // --- Phase 1: GJK Distance ---
    // Initialize the simplex with a single point on the Minkowski Difference
    let c = minkowski_diff(shape_a, shape_b, &dir);
    let mut simplex: Vec<Vector2> = Vec::with_capacity(3);
    simplex.push(c);

    let mut closest = c;
    dir = -c; // Search towards the origin

    const MAX_ITER: usize = 20;

    // Iteratively update the simplex to find the point on the MD closest to the origin
    for _ in 0..MAX_ITER {
        let a = minkowski_diff(shape_a, shape_b, &dir);

        let delta = a - closest;
        // Convergence check: if we aren't moving closer to the origin, we are done
        if delta.dot(&dir) <= GJK_TOLERANCE {
            break;
        }

        simplex.push(a);

        // Reduce simplex to the feature closest to the origin and update direction
        closest = simplex_closest_point(&mut simplex, &mut dir);
    }

    let dist = closest.mag_sq().sqrt();
    let separation_vector = -closest;

    // --- Phase 2: Cast ---
    // Determine which direction we should cast the ray based on the separation vector
    let cast_dir_x = if separation_vector.x() >= 0.0 {
        1.0
    } else {
        -1.0
    };
    let cast_dir_y = if separation_vector.y() >= 0.0 {
        1.0
    } else {
        -1.0
    };

    // Calculate how far we can slide along X and Y before collision
    let x_limit = cast_axis(shape_a, shape_b, Vector2::new(cast_dir_x, 0.0), dist);
    let y_limit = cast_axis(shape_a, shape_b, Vector2::new(0.0, cast_dir_y), dist);

    // Helper to restore the sign to the calculated magnitude
    let sign_val = |val: f64, dir: f64| {
        if val.is_infinite() {
            f64::INFINITY * dir
        } else {
            val * dir
        }
    };

    Proximity::Separated(Separation {
        distance: dist,
        vector: separation_vector,
        x_clearance: sign_val(x_limit, cast_dir_x),
        y_clearance: sign_val(y_limit, cast_dir_y),
    })
}

/// Updates the simplex and search direction to determine if the Origin is enclosed.
///
/// This helper function is the core logic of the `convex_intersects` loop. It analyzes the
/// current simplex (which can be a line segment or a triangle) relative to the Origin.
///
/// # Logic
///
/// 1.  **Triangle Case (3 points):**
///     It checks the regions outside the edges $AB$ and $AC$.
///     * If the Origin lies outside $AB$, point $C$ is removed, and the search direction is set perpendicular to $AB$.
///     * If the Origin lies outside $AC$, point $B$ is removed, and the search direction is set perpendicular to $AC$.
///     * If the Origin is inside both, the simplex contains the Origin, and the function returns `true`.
///
/// 2.  **Line Segment Case (2 points):**
///     It computes the vector perpendicular to the line segment $AB$ pointing towards the Origin.
///     This becomes the new search direction.
///
/// # Returns
///
/// * `true` if the simplex contains the Origin (Intersection found).
/// * `false` if the Origin is still outside, and the simplex/direction have been updated for the next iteration.
///
/// # Time Complexity
///
/// $O(1)$
///
/// Operations are performed on a fixed set of 2 or 3 vertices.
fn simplex_contains_origin(simplex: &mut Vec<Vector2>, dir: &mut Vector2) -> bool {
    let a = *simplex.last().unwrap();
    let ao = -a;

    if simplex.len() == 3 {
        let b = simplex[1];
        let c = simplex[0];

        let ab = b - a;
        let ac = c - a;

        // Normal of AB pointing away from C
        let ab_perp = ac.triple_product(&ab, &ab);
        // Normal of AC pointing away from B
        let ac_perp = ab.triple_product(&ac, &ac);

        if ab_perp.dot(&ao) > GJK_TOLERANCE {
            // Origin is outside AB region
            simplex.remove(0); // Remove C
            *dir = ab_perp;
        } else if ac_perp.dot(&ao) > GJK_TOLERANCE {
            simplex.remove(1); // Remove B
            *dir = ac_perp;
        } else {
            // Origin is inside the triangle
            return true;
        }
    } else {
        // Line segment case (Simplex has 2 points)
        let b = simplex[0];
        let ab = b - a;
        // Find vector perp to AB pointing toward Origin
        *dir = ab.triple_product(&ao, &ab);
    }
    false
}

/// Updates the simplex to find the feature on the Minkowski Difference closest to the Origin.
///
/// This helper function is used by `convex_distance`. It reduces the simplex (triangle or line)
/// to the sub-feature (vertex or edge) that is physically closest to the Origin $(0,0)$.
///
/// # Logic
///
/// 1.  **Triangle Case:**
///     It projects the Origin onto edges $AB$ and $AC$ to determine which edge is closer.
///     It then discards the furthest vertex ($C$ or $B$).
///
/// 2.  **Reduction & Voronoi Regions:**
///     After identifying the closest edge, it checks where the projection falls on the segment:
///     * If the projection is strictly between endpoints ($0 < t < 1$), the closest feature is the **Edge**. The simplex becomes a line segment.
///     * If the projection is at an endpoint ($t \approx 0$ or $t \approx 1$), the closest feature is a **Vertex**. The simplex becomes a single point.
///
/// # Returns
///
/// The coordinates of the closest point found on the simplex. The `dir` vector is updated
/// to point from this closest point towards the Origin.
///
/// # Time Complexity
///
/// $O(1)$
///
/// Operations are performed on a fixed set of 2 or 3 vertices.
fn simplex_closest_point(simplex: &mut Vec<Vector2>, dir: &mut Vector2) -> Vector2 {
    let a = *simplex.last().unwrap(); // Newest point
    // --- 1. TRIANGLE CASE ---
    if simplex.len() == 3 {
        let b = simplex[1];
        let c = simplex[0];

        // Check Edge AB
        let (p_ab, t_ab) = project_on_segment(a, b);
        let dist_ab = p_ab.mag_sq();

        // Check Edge AC
        let (p_ac, t_ac) = project_on_segment(a, c);
        let dist_ac = p_ac.mag_sq();

        // Compare which edge is closer to origin
        if dist_ab < dist_ac {
            // Keep AB, remove C
            simplex.remove(0);
            // Simplex is now [b, a] (b is at 0, a is at 1)

            if t_ab >= 1.0 - GJK_TOLERANCE {
                simplex.remove(0);
            }
            // Keep A
            else if t_ab <= GJK_TOLERANCE {
                simplex.pop();
            } // Keep B

            *dir = -p_ab;
            return p_ab;
        } else {
            // Keep AC, remove B
            simplex.remove(1);
            // Simplex is now [c, a] (c is at 0, a is at 1)

            if t_ac >= 1.0 - GJK_TOLERANCE {
                simplex.remove(0);
            }
            // Keep A
            else if t_ac <= GJK_TOLERANCE {
                simplex.pop();
            } // Keep C

            *dir = -p_ac;
            return p_ac;
        }
    }
    // --- 2. LINE SEGMENT CASE ---
    if simplex.len() == 2 {
        let b = simplex[0];
        let (closest, t) = project_on_segment(a, b);

        if t >= 1.0 - GJK_TOLERANCE {
            simplex.remove(0);
        }
        // Keep A
        else if t <= GJK_TOLERANCE {
            simplex.pop();
        } // Keep B

        *dir = -closest;
        return closest;
    }

    // --- 3. POINT CASE ---
    *dir = -a;
    a
}

// **********************
// *  Helper Functions  *
// **********************

/// Computes a point on the Minkowski Difference of two shapes.
///
/// The Minkowski Difference $A \ominus B$ is defined as the set of points $\{ a - b \mid a \in A, b \in B \}$.
///
/// To find the extreme point of the Minkowski Difference in a given direction `dir`,
/// we calculate: $S_{A \ominus B}(d) = S_A(d) - S_B(-d)$.
///
/// This means finding the furthest point of Shape A in direction `dir` and subtracting
/// the furthest point of Shape B in the *opposite* direction (`-dir`).
fn minkowski_diff<A: Support, B: Support>(a: &A, b: &B, dir: &Vector2) -> Vector2 {
    a.support(dir) - b.support(&-*dir)
}

/// Projects the Origin onto a line segment defined by points A and B.
///
/// This helper finds the point on the segment $AB$ that is closest to the Origin $(0,0)$.
///
/// # Returns
///
/// A tuple containing:
/// 1.  `Vector2`: The coordinates of the closest point on the segment.
/// 2.  `f64`: The projection parameter `t`.
///     * $t = 0.0$ implies the closest point is $A$.
///     * $t = 1.0$ implies the closest point is $B$.
///     * $0.0 < t < 1.0$ implies the closest point lies strictly between $A$ and $B$.
///
/// # Time Complexity
///
/// $O(1)$
///
/// Operations are performed on a fixed set of 2 or 3 vertices.
fn project_on_segment(a: Vector2, b: Vector2) -> (Vector2, f64) {
    let ab = b - a;
    let ao = -a; // Vector from A to Origin

    let ab_len_sq = ab.mag_sq();

    // Avoid division by zero for tiny segments
    if ab_len_sq < GJK_TOLERANCE.powi(2) {
        return (a, 0.0);
    }

    // Project AO onto AB: t = dot(AO, AB) / |AB|^2
    let t = ao.dot(&ab) / ab_len_sq;
    let t_clamped = t.clamp(0.0, 1.0);

    let closest = Vector2::new(a.x() + t_clamped * ab.x(), a.y() + t_clamped * ab.y());

    (closest, t_clamped)
}

/// Calculates the maximum distance `shape_a` can move along a specific axis before colliding with `shape_b`.
///
/// This function performs a "ray cast" or "linear sweep" test. It effectively answers the question:
/// "If I slide Shape A along `dir`, how far does it go before it hits Shape B?"
///
/// # Algorithm
///
/// 1.  **Exponential Search:**
///     The function first iteratively doubles the distance (`max_t`) until it finds a distance
///     where the shapes intersect. This establishes an upper bound [min_t, max_t].
///
/// 2.  **Binary Search:**
///     It then performs a binary search within that range to pinpoint the exact moment of contact
///     up to `GJK_TOLERANCE`.
///
/// # Returns
///
/// * The distance (scalar) along `dir` to the collision point.
/// * `f64::INFINITY` if no collision is found within a reasonable large bound (approx 50,000 units).
///
/// # Time Complexity
///
/// $O(V_A + V_B)$
///
/// Each iteration performs one boolean GJK intersection test.
fn cast_axis<A: Support, B: Support>(
    shape_a: &A,
    shape_b: &B,
    dir: Vector2,
    _initial_dist: f64,
) -> f64 {
    // Helper struct to treat a modified support function (Shape A + offset) as a new shape.
    // This allows us to re-use `convex_intersects` without cloning or mutating the original shape.
    struct TempShape<F: Fn(&Vector2) -> Vector2>(F);

    impl<F: Fn(&Vector2) -> Vector2> Support for TempShape<F> {
        fn support(&self, d: &Vector2) -> Vector2 {
            self.0(d)
        }
    }

    // Step 1: Find an initial upper bound for max_t (Exponential Search)
    let mut min_t = 0.0;
    let mut max_t = 0.5; // Start with a small step

    loop {
        let offset = dir * max_t;
        // virtual move of shape_a by offset
        let moved_a = TempShape(|d: &Vector2| shape_a.support(d) + offset);
        if convex_intersects(&moved_a, shape_b) {
            break; // Found an upper bound where they intersect
        }
        if max_t > 500000.0 {
            // Arbitrarily large number for practical infinity
            return f64::INFINITY;
        }
        min_t = max_t;
        max_t *= 2.0; // Double the step to find the bound quickly
    }

    // Step 2: Refine the distance (Binary Search)
    for _ in 0..20 {
        // 20 iterations for precision
        let mid_t = (min_t + max_t) / 2.0;
        if max_t - min_t < GJK_TOLERANCE {
            break;
        }

        let offset = dir * mid_t;
        let moved_a = TempShape(|d: &Vector2| shape_a.support(d) + offset);

        let intersects = convex_intersects(&moved_a, shape_b);

        if intersects {
            max_t = mid_t; // Intersection found, try smaller t
        } else {
            min_t = mid_t; // No intersection, try larger t
        }
    }

    // Return max_t because it represents the smallest distance that CAUSES intersection.
    // min_t would be the largest distance that DOES NOT cause intersection.
    max_t
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geo::polygon::Polygon;
    use crate::geo::rectangle::Rectangle;
    use crate::geo::vertex::Vertex;
    #[test]
    fn test_gjk_rectagle_no_intersection() {
        let rect1 = Rectangle::new(Vertex::new(0, 0), Vertex::new(2, 2));
        let rect2 = Rectangle::new(Vertex::new(3, 3), Vertex::new(5, 5));

        assert!(
            !convex_intersects(&rect1, &rect2),
            "Rectangles should not intersect"
        );
    }
    #[test]
    fn test_gjk_rectagle_intersection() {
        let rect1 = Rectangle::new(Vertex::new(0, 0), Vertex::new(3, 3));
        let rect2 = Rectangle::new(Vertex::new(2, 2), Vertex::new(5, 5));

        assert!(
            convex_intersects(&rect1, &rect2),
            "Rectangles should intersect"
        );
    }
    #[test]
    fn test_gjk_polygon_no_intersection() {
        let poly1 = Polygon::new(vec![
            Vertex::new(0, 0),
            Vertex::new(2, 0),
            Vertex::new(1, 2),
        ]);
        let poly2 = Polygon::new(vec![
            Vertex::new(3, 3),
            Vertex::new(5, 3),
            Vertex::new(4, 5),
        ]);

        assert!(
            !convex_intersects(&poly1, &poly2),
            "Polygons should not intersect"
        );
    }
    #[test]
    fn test_gjk_polygon_intersection() {
        // Triangles that overlap (0,0),(2,0),(1,2) and (1,1),(2,3),(3,1)
        let poly1 = Polygon::new(vec![
            Vertex::new(0, 0),
            Vertex::new(2, 0),
            Vertex::new(1, 2),
        ]);
        let poly2 = Polygon::new(vec![
            Vertex::new(1, 1),
            Vertex::new(2, 3),
            Vertex::new(3, 1),
        ]);

        assert!(
            convex_intersects(&poly1, &poly2),
            "Polygons should intersect"
        );
    }
    #[test]
    fn test_gjk_rectangle_polygon_intersection() {
        let rect = Rectangle::new(Vertex::new(0, 0), Vertex::new(3, 3));
        let poly = Polygon::new(vec![
            Vertex::new(2, 2),
            Vertex::new(4, 2),
            Vertex::new(3, 4),
        ]);

        assert!(
            convex_intersects(&rect, &poly),
            "Rectangle and Polygon should intersect"
        );
    }
    #[test]
    fn test_gjk_rectangle_polygon_no_intersection() {
        let rect = Rectangle::new(Vertex::new(0, 0), Vertex::new(2, 2));
        let poly = Polygon::new(vec![
            Vertex::new(3, 3),
            Vertex::new(5, 3),
            Vertex::new(4, 5),
        ]);

        assert!(
            !convex_intersects(&rect, &poly),
            "Rectangle and Polygon should not intersect"
        );
    }
    #[test]
    fn test_gjk_touching_shapes() {
        let rect1 = Rectangle::new(Vertex::new(0, 0), Vertex::new(2, 2));
        let rect2 = Rectangle::new(Vertex::new(2, 0), Vertex::new(4, 2));

        assert!(
            convex_intersects(&rect1, &rect2),
            "Touching rectangles should intersect"
        );
    }
    #[test]
    fn test_gjk_contained_shapes() {
        let rect1 = Rectangle::new(Vertex::new(0, 0), Vertex::new(5, 5));
        let rect2 = Rectangle::new(Vertex::new(1, 1), Vertex::new(4, 4));

        assert!(
            convex_intersects(&rect1, &rect2),
            "Contained rectangle should intersect"
        );
    }
    #[test]
    fn test_gjk_distance_non_intersecting() {
        let rect1 = Rectangle::new(Vertex::new(0, 0), Vertex::new(20, 20));
        let rect2 = Rectangle::new(Vertex::new(10, 30), Vertex::new(30, 50));

        let proximity = convex_distance(&rect1, &rect2);
        let separation = match proximity {
            Proximity::Separated(sep) => sep,
            Proximity::Intersecting => panic!("Shapes should not intersect"),
        };

        assert!(
            !convex_intersects(&rect1, &rect2),
            "Rectangles should not intersect"
        );
        // println!("Separation Info: {:?}", separation);
        assert!(
            separation.x_clearance.is_infinite(),
            "X clearance should be infinite"
        );
        assert_eq!(
            separation.y_clearance, 10.0f64,
            "Y clearance should be 10.0"
        );
        assert_eq!(separation.distance, 10.0f64, "Distance should be 10.0");
        assert_eq!(
            separation.vector,
            Vector2::new(0.0f64, 10.0f64),
            "Separation vector should be (0, 10)"
        );
    }
    #[test]
    fn test_gjk_distance_intersecting() {
        let rect1 = Rectangle::new(Vertex::new(0, 0), Vertex::new(5, 5));
        let rect2 = Rectangle::new(Vertex::new(3, 3), Vertex::new(7, 7));

        let proximity = convex_distance(&rect1, &rect2);

        match proximity {
            Proximity::Separated(sep) => panic!(
                "Shapes should intersect, but got separation info: {:?}",
                sep
            ),
            Proximity::Intersecting => (),
        };
    }
    #[test]
    fn test_gjk_distance_touching() {
        let rect1 = Rectangle::new(Vertex::new(0, 0), Vertex::new(2, 2));
        let rect2 = Rectangle::new(Vertex::new(2, 0), Vertex::new(4, 2));

        let proximity = convex_distance(&rect1, &rect2);

        match proximity {
            Proximity::Separated(sep) => panic!(
                "Shapes should intersect, but got separation info: {:?}",
                sep
            ),
            Proximity::Intersecting => (),
        };
    }

    #[test]
    fn test_gjk_distance_two_pentagons_seperated() {
        // pentagon with the
        let poly1 = Polygon::new(vec![
            Vertex::new(0, 0),
            Vertex::new(20, 0),
            Vertex::new(30, 20),
            Vertex::new(10, 30),
            Vertex::new(-10, 20),
        ]);
        let poly2 = Polygon::new(vec![
            Vertex::new(50, 50),
            Vertex::new(70, 50),
            Vertex::new(80, 70),
            Vertex::new(60, 80),
            Vertex::new(40, 70),
        ]);

        let proximity = convex_distance(&poly1, &poly2);
        let separation = match proximity {
            Proximity::Separated(sep) => sep,
            Proximity::Intersecting => panic!("Shapes should not intersect, but got intersection"),
        };

        assert!(
            !convex_intersects(&poly1, &poly2),
            "Polygons should not intersect"
        );
        // Closest points are (30,20) and (50,50)
        assert_eq!(
            separation.distance,
            ((30.0f64).powi(2) + (20.0f64).powi(2)).sqrt(),
            "Distance should be correct"
        );
        assert!(
            separation.x_clearance.is_infinite(),
            "X clearance should be infinite"
        );
        assert!(
            separation.y_clearance.is_infinite(),
            "Y clearance should be infinite"
        );
    }
    #[test]
    // test the x_clearance of two triangles with [(3, -1), (5, 2), (2, 2)] and [(12, 2), (10, 0), (16, 0)],
    fn test_gjk_distance_triangles_x_clearance() {
        let poly1 = Polygon::new(vec![
            Vertex::new(3, -1),
            Vertex::new(5, 2),
            Vertex::new(2, 2),
        ]);
        let poly2 = Polygon::new(vec![
            Vertex::new(12, 2),
            Vertex::new(10, 0),
            Vertex::new(16, 0),
        ]);

        let proximity = convex_distance(&poly1, &poly2);
        let separation = match proximity {
            Proximity::Separated(sep) => sep,
            Proximity::Intersecting => panic!("Shapes should not intersect, but got intersection"),
        };

        assert!(
            !convex_intersects(&poly1, &poly2),
            "Polygons should not intersect"
        );
        // Closest points are (5,2) and (10,0)
        assert_eq!(
            separation.distance,
            ((5.0f64).powi(2) + (2.0f64).powi(2)).sqrt(),
            "Distance should be correct, got {}, should have been {}",
            separation.distance,
            ((5.0f64).powi(2) + (2.0f64).powi(2)).sqrt()
        );

        // x clearance should be the point crossing the x axis between (5,2) and (3, -1) for poly1
        // so x=3 + (1.0/3.0)*2.0 = 3.0 + 2.0/3.0 = 11.0/3.0 = 3.6666 and (10,0) for poly2
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
