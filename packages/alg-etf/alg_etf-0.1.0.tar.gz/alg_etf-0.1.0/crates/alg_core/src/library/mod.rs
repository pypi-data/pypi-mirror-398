//! # Layout Database Module
//!
//! This module implements the hierarchical database for storing physical design data.
//! It mimics the structure of standard layout formats like GDSII.
//!
//! ## Core Hierarchy
//!
//! The database is organized as a tree:
//! * **[`Library`]:** The top-level container (database). It holds a collection of unique Cells.
//! * **[`Cell`]:** A reusable design block (e.g., "NAND Gate").
//!     * Contains **[`Layer`]s**: Collections of geometric shapes (Polygons, Rectangles).
//!     * Contains **[`instance::Instance`]s**: References to other Cells (hierarchy).
//!
//! ## Example Workflow
//!
//! ```rust
//! use alg_core::library::{Library, Cell, CellId, LayerId};
//! use alg_core::geo::{Shape, Rectangle, Vertex};
//!
//! // 1. Initialize the Library
//! let mut lib = Library::new("MyChipLib".to_string());
//!
//! // 2. Create a Cell (e.g., a simple Macro)
//! let cell_id = CellId(1);
//! let mut my_cell = Cell::new("Macro_A".to_string(), cell_id);
//!
//! // 3. Add geometry to the Cell
//! let layer_m1 = LayerId(10);
//! let rect = Shape::Rectangle(Rectangle::new(Vertex::new(0,0), Vertex::new(100,100)));
//! my_cell.add_shape(layer_m1, rect);
//!
//! // 4. Register the Cell in the Library
//! lib.add_cell(my_cell);
//! ```
pub mod cell;
pub mod instance;
pub mod layer;

use std::collections::HashMap;

pub use cell::{Cell, CellId};
pub use instance::{Instance, Orientation, Translate};
pub use layer::{Layer, LayerId};

/// Represents a complete Design Library (database).
///
/// The `Library` is the top-level container for all [`Cell`] definitions in a layout.
/// It acts as the central registry, ensuring that every cell has a unique ID and a unique Name.
///
/// # Storage Strategy
///
/// To support fast lookups during parsing (by Name) and efficient processing during
/// DRC/Routing (by ID), the library maintains two internal indices:
/// 1. **`cells`**: The primary storage, mapping unique [`CellId`] -> [`Cell`].
/// 2. **`name_to_id`**: A helper index mapping `String` -> `CellId`.
#[derive(Clone)]
pub struct Library {
    /// The name of the library.
    name: String,
    /// Primary storage: Maps numeric IDs to Cell definitions.
    cells: HashMap<CellId, Cell>,
    /// Lookup Index: Maps human-readable names to numeric IDs.
    name_to_id: HashMap<String, CellId>,
}

impl Library {
    /// Creates a new, empty Library.
    pub fn new(name: String) -> Self {
        Self {
            name,
            cells: HashMap::new(),
            name_to_id: HashMap::new(),
        }
    }
    /// Returns the name of the library.
    pub const fn name(&self) -> &String {
        &self.name
    }

    /// Returns the complete map of all cells in the library.
    pub const fn cells(&self) -> &HashMap<CellId, Cell> {
        &self.cells
    }

    /// Adds a Cell definition to the library.
    ///
    /// This updates both the primary storage and the name lookup index.
    // TODO: Handle duplicate names/IDs gracefully
    pub fn add_cell(&mut self, cell: Cell) {
        let id = cell.cell_id();
        self.name_to_id.insert(cell.name().clone(), id);
        self.cells.insert(id, cell);
    }

    /// Retrieves a reference to a Cell using its unique ID.
    ///
    /// This is the fastest lookup method ($O(1)$) and should be used during
    /// algorithms like DRC or Netlist Extraction where IDs are available.
    pub fn get_cell(&self, id: CellId) -> Option<&Cell> {
        self.cells.get(&id)
    }

    /// Retrieves a reference to a Cell using its name.
    ///
    /// This involves a two-step lookup:
    /// 1. Look up `String` -> `CellId`.
    /// 2. Look up `CellId` -> `&Cell`.
    ///
    /// Useful for parsing or user interaction.
    pub fn get_cell_by_name(&self, name: &str) -> Option<&Cell> {
        self.name_to_id.get(name).and_then(|id| self.cells.get(id))
    }
}
