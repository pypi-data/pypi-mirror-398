use alg_core::geo::AABB;
use alg_core::geo::Vertex;
use eframe::egui::{Color32, Painter, Pos2, Rect, Stroke, Vec2};

// 1000 DB units = 1 micron
const DB_PER_MICRON: f64 = 1000.0;

#[derive(Clone, Copy)]
pub struct Viewport {
    pub zoom: f64, // Pixels per DB unit
    pub pan: Vec2, // Screen offset
    pub screen_size: Vec2,
}

impl Default for Viewport {
    fn default() -> Self {
        Self::new()
    }
}

impl Viewport {
    pub const fn new() -> Self {
        Self {
            zoom: 0.1,                    // Start zoomed out
            pan: Vec2::new(400.0, 300.0), // Center
            screen_size: Vec2::new(800.0, 600.0),
        }
    }

    // gds (Integer DB units) -> viewport (Pixels)
    pub fn gds_to_viewpoort(&self, v: &Vertex) -> Pos2 {
        let x = (v.x() as f64).mul_add(self.zoom, self.pan.x as f64);
        // Note: GDS is Y-Up, Screen is Y-Down. We invert Y here.
        let y = (v.y() as f64).mul_add(-self.zoom, self.pan.y as f64);
        Pos2::new(x as f32, y as f32)
    }

    // viewport (Pixels) -> gds (Integer DB units)
    // used for mouse picking / displaying coordinates
    pub fn viewport_to_gds(&self, pos: Pos2) -> Vertex {
        let x = (pos.x - self.pan.x) as f64 / self.zoom;
        let y = (self.pan.y - pos.y) as f64 / self.zoom;
        Vertex::new(x as i32, y as i32)
    }

    /// Calculates the world-space bounds visible in the viewport.
    pub fn get_visible_bounds(&self, bounds: Rect) -> AABB {
        // Top-Left of the visible area
        let tl = self.viewport_to_gds(bounds.min);

        // Bottom-Right of the visible area
        let br = self.viewport_to_gds(bounds.max);

        let min_x = tl.x().min(br.x());
        let max_x = tl.x().max(br.x());
        let min_y = tl.y().min(br.y());
        let max_y = tl.y().max(br.y());

        AABB {
            min: Vertex::new(min_x, min_y),
            max: Vertex::new(max_x, max_y),
        }
    }

    pub const fn screen_rect(&self, bounds: Rect) -> Rect {
        bounds
    }

    // Adaptive Grid Logic
    pub fn draw_grid(&self, painter: &Painter, bounds: Rect) {
        let pixels_per_micron = self.zoom * DB_PER_MICRON;

        // Find a power of 10 step size (0.01, 0.1, 1, 10, 100) that makes sense visually
        // We want grid lines to be at least 50 pixels apart
        let mut grid_step_microns = 0.001;
        while grid_step_microns * pixels_per_micron < 50.0 {
            grid_step_microns *= 10.0;
        }

        let step_db = grid_step_microns * DB_PER_MICRON; // Step in Integer units
        let step_px = step_db * self.zoom;

        // Grid Colors
        let grid_stroke = Stroke::new(1.0, Color32::from_gray(40));
        let axis_stroke = Stroke::new(2.0, Color32::from_gray(80)); // Darker for 0,0

        // Draw Vertical Lines
        // Calculate starting line based on screen bounds and pan offset
        let start_x_idx = ((bounds.min.x as f64 - self.pan.x as f64) / step_px).floor() as i32;
        let end_x_idx = ((bounds.max.x as f64 - self.pan.x as f64) / step_px).ceil() as i32;

        for i in start_x_idx..=end_x_idx {
            let x_world_db = i as f64 * step_db;
            let x_screen = (x_world_db * self.zoom) + self.pan.x as f64;

            let stroke = if i == 0 { axis_stroke } else { grid_stroke };
            painter.line_segment(
                [
                    Pos2::new(x_screen as f32, bounds.min.y),
                    Pos2::new(x_screen as f32, bounds.max.y),
                ],
                stroke,
            );
        }

        // Draw Horizontal Lines
        // Note: Y is inverted in screen space. bounds.min.y is screen-top (World-MaxY), bounds.max.y is screen-bottom (World-MinY)
        // World-Y = (pan.y - screen_y) / zoom
        let start_y_idx = ((self.pan.y as f64 - bounds.max.y as f64) / step_px).floor() as i32;
        let end_y_idx = ((self.pan.y as f64 - bounds.min.y as f64) / step_px).ceil() as i32;

        for i in start_y_idx..=end_y_idx {
            let y_world_db = i as f64 * step_db;
            let y_screen = self.pan.y as f64 - (y_world_db * self.zoom);

            let stroke = if i == 0 { axis_stroke } else { grid_stroke };
            painter.line_segment(
                [
                    Pos2::new(bounds.min.x, y_screen as f32),
                    Pos2::new(bounds.max.x, y_screen as f32),
                ],
                stroke,
            );
        }

        // Draw Text Label
        painter.text(
            bounds.min + Vec2::new(10.0, 10.0),
            eframe::egui::Align2::LEFT_TOP,
            if grid_step_microns >= 1.0 {
                format!("Grid: {} \u{b5}m", grid_step_microns as u32)
            } else {
                format!("Grid: {:.0} nm", grid_step_microns * 1000.0)
            },
            eframe::egui::FontId::monospace(12.0),
            Color32::WHITE,
        );
    }
}
