use std::collections::HashMap;

use crate::{drc::DRCRule, library::layer::LayerId, project::style::LayerStyle};

/// Defines the display properties of a specific layer.
///
/// This structure links a physical layer (identified by `LayerId`) to its human-readable name
/// and visual representation style. It is purely metadata and does not contain geometry.
#[derive(Clone)]
pub struct LayerDef {
    pub name: String,
    pub layer_style: LayerStyle,
}

/// A wrapper for the database unit conversion factor.
///
/// Represents how many Database Units (integer coordinates) make up one User Unit (usually 1 micron).
/// For example, a value of 1000 means `1.0` micron is stored as the integer `1000`.
#[derive(Clone)]
struct DbuUu {
    value: u32,
}

/// Represents the "Process Design Kit" (PDK) or technology constraints.
///
/// The `Technology` struct acts as the single source of truth for the manufacturing process.
/// It defines the available layers, their visual styles, global constants (like grid resolution),
/// and the Design Rule Check (DRC) rules that the design must obey.
///
/// # Key Components
///
/// * **Layer Definitions:** Maps raw [LayerId]s to names and colors.
/// * **Resolution (DBU):** Defines the integer grid resolution (e.g., 1000 units = 1 micron).
/// * **DRC Rules:** A collection of geometric constraints (min width, spacing, etc.).
///
/// # Example
///
/// ```rust
/// use alg_core::project::Technology;
/// use alg_core::library::layer::LayerId;
/// use alg_core::project::style::{LayerStyle, FillStyle};
/// use eframe::egui::Color32;
///
/// let mut tech = Technology::new();
///
/// // Define Metal1 (ID 10) as Blue
/// tech.add_layer_def(
///     LayerId(10),
///     "Metal1".to_string(),
///     LayerStyle {
///         color: Color32::from_rgb(0, 0, 255), // Blue
///         visible: true,
///         fill: FillStyle::Solid,
///         name: "Metal1".to_string(),
///     },
/// );
/// ```
#[derive(Clone)]
pub struct Technology {
    /// Maps numeric Layer IDs to their definition (name, style).
    layer_def: HashMap<LayerId, LayerDef>,

    /// Database Units per User Unit.
    /// Standard is often 1000 (1nm resolution if User Unit is 1um).
    dbu_uu: DbuUu,

    /// Helper map for looking up Layer IDs by their string name.
    name_lookup: HashMap<String, LayerId>,

    /// The set of global Design Rules associated with this process.
    drc_rules: Vec<DRCRule>,
}

impl Technology {
    /// Creates a new, empty Technology configuration.
    ///
    /// * Defaults `dbu_uu` to 1000.
    /// * Initializes empty maps for layers and rules.
    pub fn new() -> Self {
        Self {
            layer_def: HashMap::new(),
            dbu_uu: DbuUu { value: 1000 },
            name_lookup: HashMap::new(),
            drc_rules: Vec::new(),
        }
    }

    /// Returns the database unit resolution (Database Units per User Unit).
    ///
    /// E.g., returns `1000` if the internal coordinates are in nanometers and user units are
    /// microns.
    pub const fn dbu_uu(&self) -> u32 {
        self.dbu_uu.value
    }

    /// Sets the database unit resolution.
    ///
    /// **Warning:** Changing this after geometry has been created effectively scales the entire design.
    /// This should typically only be set once during initialization and should be from the PDK.
    pub const fn set_dbu_uu(&mut self, value: u32) {
        self.dbu_uu.value = value;
    }

    /// Registers a new layer definition in the technology.
    ///
    /// This updates both the definition storage and the name lookup table.
    ///
    /// # Parameters
    /// * `layer_id`: The unique numeric identifier.
    /// * `name`: The human-readable name (e.g., "M1").
    /// * `layer_style`: The visual style for rendering.
    pub fn add_layer_def(&mut self, layer_id: LayerId, name: String, layer_style: LayerStyle) {
        self.layer_def.insert(
            layer_id,
            LayerDef {
                name: name.clone(),
                layer_style,
            },
        );
        self.name_lookup.insert(name, layer_id);
    }

    /// Retrieves the definition (name, style) for a given Layer ID.
    pub fn get_layer_def(&self, layer_id: LayerId) -> Option<&LayerDef> {
        self.layer_def.get(&layer_id)
    }

    /// Gets the drc rules defined in this technology.
    pub const fn get_drc_rules(&self) -> &Vec<DRCRule> {
        &self.drc_rules
    }
}

impl Default for Technology {
    fn default() -> Self {
        Self::new()
    }
}
