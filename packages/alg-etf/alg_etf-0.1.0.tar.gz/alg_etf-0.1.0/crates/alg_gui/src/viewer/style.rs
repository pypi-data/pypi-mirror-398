use alg_core::project::{FillStyle, LayerStyle};
use eframe::egui::Color32;
use std::collections::HashMap;

pub struct ViewConfig {
    pub styles: HashMap<i16, LayerStyle>,
}

impl Default for ViewConfig {
    fn default() -> Self {
        Self::new()
    }
}

impl ViewConfig {
    pub fn new() -> Self {
        Self {
            styles: HashMap::new(),
        }
    }

    // Helper to generate random-ish nice colors for new layers
    pub fn get_or_create(&mut self, layer_id: i16) -> &mut LayerStyle {
        self.styles.entry(layer_id).or_insert_with(|| {
            // Simple hash to pick a stable color based on ID
            let r = (layer_id as u64 * 100) % 255;
            let g = (layer_id as u64 * 50 + 100) % 255;
            let b = (layer_id as u64 * 20 + 200) % 255;

            LayerStyle {
                color: Color32::from_rgb(r as u8, g as u8, b as u8),
                visible: true,
                fill: FillStyle::Solid,
                name: format!("Layer {}", layer_id),
            }
        })
    }
}
