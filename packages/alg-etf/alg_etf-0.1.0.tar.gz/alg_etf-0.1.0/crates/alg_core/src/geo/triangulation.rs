use crate::geo::Vertex;

/// Decomposes a simple polygon into a list of triangles using the Ear Clipping algorithm.
///
/// This function handles both convex and concave polygons. It returns a list of triangles,
/// where each triangle is represented as a `Vec<Vertex>` of size 3.
///
/// # Algorithm: Ear Clipping
///
/// An "ear" of a polygon is a triangle formed by three consecutive vertices $V_{i-1}, V_i, V_{i+1}$
/// such that:
/// 1.  The triangle is convex (interior angle < 180°).
/// 2.  No other vertices of the polygon lie inside this triangle.
///
/// The algorithm iteratively finds an ear, adds it to the output list, and removes the "ear tip"
/// vertex ($V_i$) from the polygon. This process repeats until only 3 vertices remain, which
/// form the final triangle.
///
/// # Requirements
///
/// * **Simple Polygon:** The input must be a simple polygon (no self-intersections).
/// * **Winding Order:** The function automatically enforces Counter-Clockwise (CCW) winding.
///   If the input is Clockwise, it will be reversed internally.
///
/// # Time Complexity
///
/// $O(V^2)$
///
/// Where $V$ is the number of vertices. In the worst case (e.g., specific zigzag shapes),
/// checking for ears takes $O(V)$ and is done $V$ times.
pub fn triangulate_polygon(vertices: &[Vertex]) -> Vec<Vec<Vertex>> {
    let mut triangles = Vec::new();
    let mut poly = vertices.to_vec();

    // 1. Sanitize: Ensure we have enough points
    if poly.len() < 3 {
        return triangles;
    }

    // 2. Sanitize: Enforce Counter-Clockwise (CCW) winding.
    // Ear clipping relies on "left turns" being convex.
    if signed_area(&poly) < 0 {
        poly.reverse();
    }

    // 3. Ear Clipping Loop
    while poly.len() > 3 {
        let mut ear_found = false;
        let len = poly.len();

        for i in 0..len {
            // get indices wrapped around
            let prev_idx = if i == 0 { len - 1 } else { i - 1 };
            let curr_idx = i;
            let next_idx = (i + 1) % len;

            let prev = poly[prev_idx];
            let curr = poly[curr_idx];
            let next = poly[next_idx];

            if is_ear(prev, curr, next, &poly) {
                // ear found!
                triangles.push(vec![prev, curr, next]);

                // remove the ear tip (current vertex)
                poly.remove(curr_idx);
                ear_found = true;

                // restart loop since indices shifted
                break;
            }
        }

        // safety: if we looped through all points and found no ears,
        // the polygon is likely degenerate (self-intersecting) or math failed.
        if !ear_found {
            eprintln!("triangulation failed: no ear found. polygon might be self-intersecting.");
            break;
        }
    }

    // 4. the remaining 3 vertices form the final triangle
    if poly.len() == 3 {
        triangles.push(poly);
    }

    triangles
}

/// Determines if a polygon is convex.
///
/// A polygon is convex if all its interior angles are less than or equal to 180 degrees.
/// In terms of boundary traversal, this means every turn must be in the same direction
/// (either all left turns or all right turns).
///
/// # Algorithm
///
/// The function iterates through every triplet of consecutive vertices and calculates the
/// 2D cross product.
/// * A positive cross product indicates a "left turn".
/// * A negative cross product indicates a "right turn".
///
/// If the polygon contains both left and right turns, it is concave.
///
/// # Returns
///
/// * `true` if the polygon is convex (or degenerate with fewer than 4 vertices).
/// * `false` if the polygon is concave.
///
/// # Time Complexity
///
/// $O(V)$
///
/// Where $V$ is the number of vertices. The function performs a single linear pass.
pub fn is_convex(vertices: &[Vertex]) -> bool {
    let n = vertices.len();
    // Base cases: A point, line segment, or triangle cannot be concave.
    if n < 4 {
        return true;
    }

    let mut is_positive = false;
    let mut is_negative = false;

    for i in 0..n {
        let p1 = vertices[i];
        let p2 = vertices[(i + 1) % n];
        let p3 = vertices[(i + 2) % n];

        let cp = cross_product_2d(p1, p2, p3);

        if cp > 0 {
            is_positive = true;
        }
        if cp < 0 {
            is_negative = true;
        }

        // If we have both left and right turns, it's concave.
        if is_positive && is_negative {
            return false;
        }
    }

    true
}

/// Determines if the vertex `curr` forms a valid "Ear" of the polygon.
///
/// An ear is defined by three consecutive vertices $(V_{prev}, V_{curr}, V_{next})$ that satisfy two conditions:
/// 1.  **Convexity:** The internal angle at $V_{curr}$ is less than 180 degrees (it forms a "convex corner").
/// 2.  **Emptiness:** No other vertex of the polygon lies strictly inside the triangle formed by these three points.
///
/// # Parameters
///
/// * `prev`: The vertex preceding `curr` in the polygon ring.
/// * `curr`: The candidate "ear tip" vertex.
/// * `next`: The vertex following `curr` in the polygon ring.
/// * `polygon`: The list of all vertices in the current (reduced) polygon.
///
/// # Returns
///
/// `true` if `curr` is an ear tip, `false` otherwise.
///
/// # Time Complexity
///
/// $O(V)$
///
/// It performs a constant-time convexity check followed by a linear scan of all other vertices
/// to ensure none are inside the triangle.
fn is_ear(prev: Vertex, curr: Vertex, next: Vertex, polygon: &[Vertex]) -> bool {
    // 1. Convexity Check: The angle must be convex (left turn in CCW).
    // Cross product > 0 means left turn.
    if cross_product_2d(prev, curr, next) <= 0 {
        return false;
    }

    // 2. Empty Triangle Check: No other vertex can be inside this triangle.
    // If any other vertex is inside, cutting this "ear" would intersect the polygon boundary.
    for &v in polygon {
        // Skip the vertices that make up the triangle itself
        if v == prev || v == curr || v == next {
            continue;
        }

        if is_inside_triangle(prev, curr, next, v) {
            return false;
        }
    }

    true
}

/// Determines if a point `p` lies inside or on the boundary of the triangle defined by $A, B, C$.
///
/// This function uses the **Edge-Side (Half-Plane)** test. For a triangle defined in
/// Counter-Clockwise (CCW) order, a point is inside if it lies to the left (or on the line)
/// of all three edges $AB$, $BC$, and $CA$.
///
/// # Requirements
///
/// * **Winding Order:** The vertices $A, B, C$ **must** be ordered Counter-Clockwise.
///   If they are Clockwise, the logic must be inverted (or the inputs swapped).
///
/// # Returns
///
/// * `true` if `p` is strictly inside the triangle or lies exactly on an edge/vertex.
/// * `false` if `p` is outside.
///
/// # Time Complexity
///
/// $O(1)$
const fn is_inside_triangle(a: Vertex, b: Vertex, c: Vertex, p: Vertex) -> bool {
    // Calculate the 2D cross product for the point relative to each edge.
    // A non-negative result means the point is to the "left" of the edge vector.

    let cp1 = cross_product_2d(a, b, p);
    let cp2 = cross_product_2d(b, c, p);
    let cp3 = cross_product_2d(c, a, p);

    // If the point is to the left (or on) every edge, it must be inside the triangle.
    cp1 >= 0 && cp2 >= 0 && cp3 >= 0
}

/// Computes the 2D cross product (Z-component) of vectors $AB$ and $AC$.
///
/// This function calculates the scalar value equivalent to the determinant of the matrix formed
/// by the vectors $(B - A)$ and $(C - A)$.
///
/// # Geometric Interpretation
///
/// * **Value > 0:** $C$ is to the **left** of the directed line $AB$ (Counter-Clockwise turn).
/// * **Value < 0:** $C$ is to the **right** of the directed line $AB$ (Clockwise turn).
/// * **Value = 0:** Points $A, B$, and $C$ are **collinear**.
///
/// # Magnitude
///
/// The absolute value of the result is equal to twice the signed area of the triangle $ABC$.
///
/// # Time Complexity
///
/// $O(1)$
const fn cross_product_2d(a: Vertex, b: Vertex, c: Vertex) -> i64 {
    let dx1 = (b.x() - a.x()) as i64;
    let dy1 = (b.y() - a.y()) as i64;
    let dx2 = (c.x() - a.x()) as i64;
    let dy2 = (c.y() - a.y()) as i64;

    dx1 * dy2 - dy1 * dx2
}

/// Calculates twice the signed area of a polygon using the Shoelace Formula.
///
/// This function computes the area by summing the cross products of consecutive vertices
/// relative to the origin.
///
/// # Returns
///
/// An `i64` representing **2 × Area**.
/// * **Positive:** The vertices are ordered Counter-Clockwise (CCW).
/// * **Negative:** The vertices are ordered Clockwise (CW).
/// * **Zero:** The polygon has no area (degenerate or self-intersecting in a way that cancels out).
///
/// # Note
///
/// The result is not divided by 2 to avoid integer division truncation and to maintain precision
/// for winding order checks.
///
/// # Time Complexity
///
/// $O(V)$
fn signed_area(vertices: &[Vertex]) -> i64 {
    let mut area = 0;
    for i in 0..vertices.len() {
        let curr = vertices[i];
        let next = vertices[(i + 1) % vertices.len()];
        // Shoelace formula term: (x1 * y2 - x2 * y1)
        area += (curr.x() as i64 * next.y() as i64) - (next.x() as i64 * curr.y() as i64);
    }
    area
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geo::Polygon;
    use crate::geo::Vertex;

    #[test]
    fn test_triangulate_convex_square() {
        let square = vec![
            Vertex::new(0, 0),
            Vertex::new(1, 0),
            Vertex::new(1, 1),
            Vertex::new(0, 1),
        ];
        let triangles = triangulate_polygon(&square);
        assert_eq!(
            triangles.len(),
            2,
            "Square should be triangulated into 2 triangles"
        );
        assert!(is_convex(&square), "Square should be convex");
    }
    #[test]
    fn test_triangulate_concave_star() {
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

        assert!(
            !is_convex(poly_star.vertices()),
            "Star polygon should be concave"
        );
        let triangles = triangulate_polygon(poly_star.vertices());
        assert!(
            !triangles.is_empty(),
            "Star polygon should be triangulatable"
        );
        println!("Star polygon triangulated into {:?}.", triangles);
    }

    #[test]
    fn test_triangulate_concave_c_shape() {
        let poly_c_shape = Polygon::new(vec![
            Vertex::new(2, 0), // V1: Bottom-Left
            Vertex::new(8, 0), // V2: Bottom-Right
            Vertex::new(8, 6), // V3: Top-Right
            Vertex::new(2, 6), // V4: Top-Left
            Vertex::new(4, 4), // V5: Start of the inward cut (Concave angle)
            Vertex::new(4, 2), // V6: The inner corner (Concave angle)
        ]);

        assert!(
            !is_convex(poly_c_shape.vertices()),
            "C-shape polygon should be concave"
        );
        let triangles = triangulate_polygon(poly_c_shape.vertices());
        assert!(
            !triangles.is_empty(),
            "C-shape polygon should be triangulatable"
        );
        println!("C-shape polygon triangulated into {:?}.", triangles);
    }
}
