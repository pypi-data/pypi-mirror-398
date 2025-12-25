use crate::{library::Library, project::Technology};

/// The top-level container for a complete design project.
///
/// A `Design` unifies the "rules" (Technology) with the "designed cells" (Library).
///
/// # Components
///
/// * **[`Technology`]:** Contains the set constraints (Layer definitions, DRC Rules,
///   GDSII mappings). This essentially represents the PDK (Process Design Kit).
/// * **[`Library`]:** Contains the actual design data (Cells, Instances, Shapes).
///
/// # Example
///
/// ```rust
/// use alg_core::project::{Design, Technology};
/// use alg_core::library::Library;
///
/// // 1. Load Technology (e.g., from a PDK config)
/// let tech = Technology::default();
///
/// // 2. Create an empty Library for your chip
/// let lib = Library::new("My_Analog_Design".to_string());
///
/// // 3. Combine into a unified Design object
/// let design = Design::new(tech, lib);
///
/// // Now you can pass `&design` to DRC or Routing engines
/// ```
#[derive(Clone)]
pub struct Design {
    /// The immutable technology definitions (Layers, Rules, Manufacturing constraints).
    technology: Technology,
    /// The database containing all cells, shapes, and hierarchy.
    library: Library,
}

impl Design {
    /// Creates a new Design by combining a technology definition with a cell library.
    pub const fn new(technology: Technology, library: Library) -> Self {
        Self {
            technology,
            library,
        }
    }
    /// Returns a reference to the cell library.
    pub const fn library(&self) -> &Library {
        &self.library
    }

    /// Returns a reference to the technology definition
    pub const fn technology(&self) -> &Technology {
        &self.technology
    }
}
