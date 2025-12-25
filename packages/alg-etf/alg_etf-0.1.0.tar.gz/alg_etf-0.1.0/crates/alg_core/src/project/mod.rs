//! # Project Management Module
//!
//! This module defines the high-level structures that represent a complete physical design project.
//!
//! It serves as the container that binds the **"How"** (Technology/PDK constraints) with the
//! **"What"** (Design/Library data).
//!
//! ## Core Components
//!
//! * **[`Design`]:** The root object representing the current state of the work.
//! * **[`Technology`]:** The set of manufacturing rules, layer definitions, and
//!   physical constraints (often loaded from a PDK).
pub mod design;
pub mod style;
pub mod technology;

pub use design::Design;
pub use style::{FillStyle, LayerStyle};
pub use technology::Technology;
