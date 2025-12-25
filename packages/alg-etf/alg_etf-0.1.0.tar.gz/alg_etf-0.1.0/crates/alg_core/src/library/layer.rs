use std::collections::HashMap;

use crate::{
    drc::DRCRule,
    geo::{AABB, Boundary, Shape},
};

/// An identifier for a physical layer (e.g., "Metal1", "Poly", "Diffusion") based on
/// layer number.
///
/// Using a wrapper around `u8` prevents accidental confusion between
/// layer IDs and standard integers or indices.
///
/// # Layer Numbering
/// The layer number corresponds to the physical layer as defined in
/// [`crate::project::technology::Technology`]
///
/// # Example
///
/// ```rust
/// use alg_core::library::LayerId;
///
/// let m1 = LayerId(1);
/// let m2 = LayerId(2);
/// assert_ne!(m1, m2);
/// ```
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct LayerId(pub u8);

// TODO: Implement Rule application logic
#[expect(dead_code)]
pub struct Rule {
    rule: DRCRule,
    zone: Vec<Shape>,
}

// TODO: Implement ConstraintZone logic
#[expect(dead_code)]
pub struct ConstraintZone {
    aabb: AABB,
    rules: Vec<Rule>,
}

/// Represents a single physical layer in the design (e.g., Metal1).
///
/// This struct acts as the primary container for geometry and manages spatial acceleration
/// structures for efficient Design Rule Checking (DRC).
///
/// # Logic
///
/// * **Geometry Storage:** Raw shapes are stored in `shapes`.
/// * **Broad Phase:** A [`Boundary`] is maintained (the union of all shapes including the DRC
///   boundary for every layer) to allow O(1)
///   checks against other layers. If `layer.boundary` does not intersect `other_layer.boundary`,
///   no further spacing checks are needed.
/// * **Caching:** The `interaction_cache` stores derived geometric data relative to other layers,
///   minimizing re-computation during routing or placement.
#[derive(Clone)]
pub struct Layer {
    /// Unique identifier for this layer.
    layer_id: LayerId,

    /// The raw geometric [Shape]s (Rectangles, Polygons, Paths) assigned to this layer.
    shapes: Vec<Shape>,

    /// The geometric boundary of this layer.
    ///
    /// This is automatically updated when shapes are added and is used for fast
    /// intersection/spacing rejection tests.
    ///
    /// This boundary represents the union of all shapes and their DRC-expanded footprints on each
    /// layer.
    boundary: Boundary,

    /// A cache of spatial relationships with other layers.
    ///
    /// # Key-Value Mapping
    /// * **Key:** The [`LayerId`] of another layer.
    /// * **Value:** A [`Boundary`] representing the relevant geometry of that other layer
    ///   (potentially expanded/bloated for spacing checks) tailored for interactions with *this* layer.
    interaction_cache: HashMap<LayerId, Boundary>,
}

impl Layer {
    /// Creates a new, empty layer with the specified ID.
    ///
    /// The `shapes` vector, `boundary`, and `interaction_cache` are initialized to empty states.
    ///
    /// # Example
    ///
    /// ```rust
    /// use alg_core::library::{Layer, LayerId};
    ///
    /// let metal1 = Layer::new(LayerId(1));
    /// ```
    //TODO: Implement Into trait for LayerId from u8 and
    pub fn new(layer_id: LayerId) -> Self {
        Self {
            layer_id,
            shapes: Vec::new(),
            boundary: Boundary::new(),
            interaction_cache: HashMap::new(),
        }
    }

    /// Returns the unique identifier for this layer.
    pub const fn id(&self) -> LayerId {
        self.layer_id
    }

    /// Returns a reference to the raw list of geometric shapes.
    pub const fn shapes(&self) -> &Vec<Shape> {
        &self.shapes
    }

    /// Returns the geometric boundary of the layer.
    ///
    /// This boundary is maintained as shapes are added and is used for
    /// fast broad-phase intersection checks against other layers.
    pub const fn boundary(&self) -> &Boundary {
        &self.boundary
    }

    /// Returns the current cache of spatial interactions with other layers.
    pub const fn interaction_cache(&self) -> &HashMap<LayerId, Boundary> {
        &self.interaction_cache
    }

    /// Adds a shape to the layer and updates the geometric boundary.
    ///
    /// This method ensures the [Boundary] remains synchronized with the `shapes` list,
    /// allowing for immediate broad-phase checks after insertion.
    ///
    /// # Logic
    ///
    /// 1.  **Validation (TODO):** Checks strictly local rules (e.g., MinWidth) before acceptance.
    /// 2.  **Storage:** Appends the shape to the `shapes` vector.
    /// 3.  **Boundary Update:** Incrementally updates the layer's [`Boundary`] AABB and polygon list.
    pub fn add_shape(&mut self, shape: Shape) {
        // first check if the shape itself is valid (eg min width)
        // TODO: Implement shape validation logic here.

        // Add shape to the Layer
        self.shapes.push(shape.clone());

        // Add shape to the Boundary
        self.boundary.from_shape(&shape);

        // TODO: Update interaction_cache if necessary by checking DRC rules.
    }
}
