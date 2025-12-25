use std::collections::HashMap;

use crate::{
    geo::{Boundary, Shape},
    library::{Layer, Library, instance::Instance, layer::LayerId},
};

/// A unique identifier for a Cell definition within the library.
///
/// This acts as a handle to look up `Cell` structs. Using a strongly-typed wrapper
/// prevents mixing up `LayerId`s and `CellId`s.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct CellId(pub usize);

/// Represents a fundamental unit of design reuse (e.g., a Logic Gate or IP Block).
///
/// A `Cell` is the primary container in hierarchical layouts. It contains:
/// 1.  **Geometry:** Shapes distributed across different physical [`Layer`]s.
/// 2.  **Hierarchy:** [`Instance`]s of other cells (allowing for nested designs).
/// 3.  **Boundaries:** A calculated geometric footprint used for placement and DRC checks.
///
/// # Architecture
///
/// ```text
/// Cell
/// ├── Layers (HashMap)
/// │   ├── Metal1: [Rect, Rect, Path...]
/// │   └── Poly:   [Polygon...]
/// └── Instances (Vec)
///     ├── Instance(AND_GATE) @ (0,0)
///     └── Instance(OR_GATE)  @ (10000,0)
/// ```
#[derive(Clone)]
pub struct Cell {
    /// The human-readable name of the cell (e.g., "NAND2_X1").
    name: String,
    /// The unique internal identifier.
    cell_id: CellId,
    /// A collection of geometric layers, indexed by their ID.
    layers: HashMap<LayerId, Layer>,
    /// A list of child instances placed within this cell.
    instances: Vec<Instance>,
    /// The cached geometric boundary of the entire cell (including all layers/instances and their
    /// DRC padding).
    cell_boundary: Boundary,
}

impl Cell {
    /// Creates a new, empty Cell definition.
    ///
    /// # Example
    ///
    /// ```rust
    /// use alg_core::library::{Cell, CellId};
    ///
    /// let inverter = Cell::new("INV_X1".to_string(), CellId(1));
    /// ```
    // TODO Add Impl From for for cellID and name
    pub fn new(name: String, cell_id: CellId) -> Self {
        Self {
            name,
            cell_id,
            layers: HashMap::new(),
            instances: Vec::new(),
            cell_boundary: Boundary::new(),
        }
    }

    /// Returns the cell's name.
    pub const fn name(&self) -> &String {
        &self.name
    }

    /// Returns the unique ID of this cell.
    pub const fn cell_id(&self) -> CellId {
        self.cell_id
    }

    /// Retrieves a reference to a specific layer, if it exists.
    ///
    /// Returns `None` if no shapes have been added to this layer yet.
    pub fn get_layer(&self, layer_id: &LayerId) -> Option<&Layer> {
        self.layers.get(layer_id)
    }

    pub const fn layers(&self) -> &HashMap<LayerId, Layer> {
        &self.layers
    }

    /// Returns the list of child instances.
    pub const fn instances(&self) -> &Vec<Instance> {
        &self.instances
    }

    /// Returns the cached outer boundary of the cell.
    pub const fn cell_boundary(&self) -> &Boundary {
        &self.cell_boundary
    }

    /// Explicitly adds a pre-constructed Layer object.
    ///
    /// *Note:* In most cases, you should use [`Cell::add_shape`], which handles layer creation automatically.
    pub fn add_layer(&mut self, layer: Layer, layer_id: LayerId) {
        self.layers.insert(layer_id, layer);
    }

    /// Adds an instance of another cell into this cell.
    ///
    /// This builds the design hierarchy.
    ///
    /// # Parameters
    ///
    /// * `instance`: The instance to add.
    /// * 'cell_library`: Reference to the cell library where the instance is from.'
    pub fn add_instance(&mut self, instance: Instance, library: &Library) {
        // Infer the initial cell boundary from the instance's cellID
        let cell_id = instance.cell_id();

        // Use cell_id to lookup the boundary from the library and add error handling
        match library.get_cell(cell_id) {
            Some(master_cell) => {
                let master_boundary = master_cell.cell_boundary();
                let transformed_boundary = master_boundary.transform(instance.translation());
                self.cell_boundary.merge(&transformed_boundary);
            }
            None => {
                // Handle the error case where the cell_id does not exist in the library
                eprintln!("Warning: Instance refers to unknown CellId {:?}", cell_id);
            }
        }

        self.instances.push(instance);
    }

    /// Adds a primitive shape to a specific [Layer].
    ///
    /// This method uses a on-demand instantiation:
    /// 1. Checks if the [`Layer` corresponding to `layer_id` exists.
    /// 2. If not, it creates a new empty `Layer`.
    /// 3. Adds the shape to that layer.
    ///
    /// When the shape is added to the layer, the layer's internal [Boundary] is updated
    /// to reflect the new geometry.
    ///
    /// This ensures we only store `Layer` objects for layers that actually contain geometry.
    ///
    /// # Example
    ///
    /// ```rust
    /// use alg_core::geo::{Shape, Rectangle, Vertex};
    /// use alg_core::library::{Cell, CellId, LayerId};
    ///
    /// let mut cell = Cell::new("Test".to_string(), CellId(0));
    /// let m1_id = LayerId(1);
    /// let rect = Shape::Rectangle(Rectangle::new(Vertex::new(0,0), Vertex::new(10,10)));
    ///
    /// // Automatically creates the Metal1 layer and adds the rect
    /// cell.add_shape(m1_id, rect);
    /// ```    
    //TODO add impl From for LayerId from u8
    pub fn add_shape(&mut self, layer_id: LayerId, shape: Shape) {
        self.layers
            .entry(layer_id)
            .or_insert_with(|| Layer::new(layer_id))
            .add_shape(shape.clone());

        // Update the cell's AABB
        self.cell_boundary.from_shape(&shape);
    }
}
