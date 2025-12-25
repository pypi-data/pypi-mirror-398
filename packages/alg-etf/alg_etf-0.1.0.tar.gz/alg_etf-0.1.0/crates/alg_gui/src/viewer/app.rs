use std::collections::HashSet;

use super::style::ViewConfig;
use super::viewport::Viewport;
use alg_core::geo::{AABB, Shape, Vertex};
use alg_core::library::cell::CellId;
use alg_core::library::instance::{Orientation, Translate};
use alg_core::library::layer::LayerId;
use alg_core::project::Design;
use alg_core::project::style::FillStyle;
use eframe::egui;
use eframe::egui::{Color32, Stroke};
use egui::StrokeKind;

// Simple cache: Layer ID -> World Space Shape
type RenderCache = Vec<(i16, Shape)>;

pub struct LayoutViewer {
    design: Design,
    selected_cell_id: Option<CellId>,
    viewport: Viewport,
    config: ViewConfig,
    show_boundary: bool,
    show_instance_origins: bool,
    last_frame_time: f32,

    // Cache of transformed shapes ready for rendering
    render_cache: RenderCache,
}

impl LayoutViewer {
    pub fn new(design: Design) -> Self {
        let mut viewer = Self {
            design,
            selected_cell_id: None,
            viewport: Viewport::new(),
            config: ViewConfig::new(),
            show_boundary: true,
            show_instance_origins: true,
            last_frame_time: 0.0,
            render_cache: Vec::new(),
        };

        // Select the first cell found, if any
        if let Some(id) = viewer.design.library().cells().keys().next() {
            viewer.set_selected_cell(*id);
        }

        viewer
    }

    pub fn set_selected_cell(&mut self, cell_id: CellId) {
        self.selected_cell_id = Some(cell_id);
        self.ensure_styles_initialized(cell_id);
        self.rebuild_cache(cell_id);
    }

    fn ensure_styles_initialized(&mut self, root_cell_id: CellId) {
        let mut stack = vec![root_cell_id];
        let mut visited = HashSet::new();

        while let Some(cell_id) = stack.pop() {
            if !visited.insert(cell_id) {
                continue;
            }

            if let Some(cell) = self.design.library().get_cell(cell_id) {
                for layer_id in cell.layers().keys() {
                    let lid = LayerId(layer_id.0);
                    if let Some(def) = self.design.technology().get_layer_def(lid) {
                        self.config
                            .styles
                            .entry(layer_id.0 as i16)
                            .or_insert(def.layer_style.clone());
                    } else {
                        self.config.get_or_create(layer_id.0 as i16);
                    }
                }
                for instance in cell.instances() {
                    stack.push(instance.cell_id());
                }
            }
        }
    }

    fn rebuild_cache(&mut self, cell_id: CellId) {
        self.render_cache.clear();
        let identity = Translate::new(Vertex::new(0, 0), Orientation::R0);
        self.recursive_build_cache(cell_id, &identity);
    }

    /// Recursively flattens the cell hierarchy into the render cache.
    /// This is done ONLY when the selection changes, not every frame.
    fn recursive_build_cache(&mut self, cell_id: CellId, transform: &Translate) {
        let instances: Vec<_> = if let Some(cell) = self.design.library().get_cell(cell_id) {
            // 1. Process Shapes
            for (layer_id, layer) in cell.layers() {
                let lid = layer_id.0 as i16;
                for shape in layer.shapes() {
                    // Transform to world space and cache
                    let global_shape = shape.transform(transform);
                    self.render_cache.push((lid, global_shape));
                }
            }
            // Collect instances to avoid holding borrow of self
            cell.instances()
                .iter()
                .map(|i| (i.cell_id(), *i.translation()))
                .collect()
        } else {
            return;
        };
        if self.show_instance_origins {
            // 2. Process Instances (Recursion)
            for (child_id, instance_transform) in instances {
                // Compose Transforms: parent + child
                let new_transform = *transform + instance_transform;

                self.recursive_build_cache(child_id, &new_transform);
            }
        }
    }

    fn draw_shape(
        &self,
        painter: &egui::Painter,
        shape: &Shape,
        base_color: Color32,
        fill_style: FillStyle,
    ) {
        // Pixel Culling: Skip shapes that are too small to see (< 0.5 pixels in both dimensions)
        let aabb = shape.aabb();
        let w_px = (aabb.max.x() - aabb.min.x()) as f64 * self.viewport.zoom;
        let h_px = (aabb.max.y() - aabb.min.y()) as f64 * self.viewport.zoom;

        if w_px < 0.5 && h_px < 0.5 {
            return;
        }

        let stroke = Stroke::new(1.0, base_color);
        // Calculate fill color based on style
        let fill_color = match fill_style {
            FillStyle::Solid => base_color.linear_multiply(0.3),
            _ => Color32::TRANSPARENT,
        };

        match shape {
            Shape::Rectangle(r) => {
                let p1 = self.viewport.gds_to_viewpoort(r.lower_left());
                let p2 = self.viewport.gds_to_viewpoort(r.upper_right());
                let rect = egui::Rect::from_two_pos(p1, p2);

                painter.rect(rect, 0.0, fill_color, stroke, StrokeKind::Middle);

                // Hatching
                if fill_style != FillStyle::Solid && fill_style != FillStyle::NoFill {
                    self.draw_hatching(painter, rect, fill_style, base_color);
                }
            }
            Shape::Polygon(p) => {
                let points: Vec<egui::Pos2> = p
                    .vertices()
                    .iter()
                    .map(|v| self.viewport.gds_to_viewpoort(v))
                    .collect();

                painter.add(egui::Shape::convex_polygon(points, fill_color, stroke));

                // For Polygons, we just hatch the bounding box clipped to the polygon is hard,
                // so we skip detailed hatching for now or could hatch the AABB.
                // Simpler: Just rely on outline for non-rectangles or implement full scanline later.
                // User requirement "style the shapes... stripped".
                // Let's at least try to hatch the bounding box if it's large enough?
                // No, that looks ugly if lines go outside.
                // We'll stick to Outline for Polygons for now unless they are Solid.
            }
            Shape::Path(p) => {
                let points: Vec<egui::Pos2> = p
                    .vertices()
                    .iter()
                    .map(|v| self.viewport.gds_to_viewpoort(v))
                    .collect();
                let width_px = p.width() as f64 * self.viewport.zoom;
                painter.add(egui::Shape::line(
                    points,
                    Stroke::new(width_px as f32, base_color),
                ));
            }
        }
    }

    fn draw_hatching(
        &self,
        painter: &egui::Painter,
        rect: egui::Rect,
        style: FillStyle,
        color: Color32,
    ) {
        // World Space Hatching: Spacing scales with zoom
        // 250 DB Units spacing (approx 1/4 of a typical 1000 unit cell width)
        let world_step = 250.0;
        let step = world_step * self.viewport.zoom as f32;

        // Prevent infinite loop or excessive rendering if zoom is very small
        if step < 2.0 {
            return;
        }

        let stroke = Stroke::new(1.0, color.linear_multiply(0.5));

        // Anchor pattern to viewport pan (World 0,0)
        let offset_x = self.viewport.pan.x;
        let offset_y = self.viewport.pan.y;

        const EPSILON: f32 = 1e-4;

        // Helper to draw segment from points
        let draw_segment = |points: &Vec<egui::Pos2>| {
            if points.len() < 2 {
                return;
            }
            if points.len() == 2 {
                painter.line_segment([points[0], points[1]], stroke);
            } else {
                // Find pair with max distance
                let mut p1 = points[0];
                let mut p2 = points[1];
                let mut max_d2 = p1.distance_sq(p2);

                for i in 0..points.len() {
                    for j in (i + 1)..points.len() {
                        let d2 = points[i].distance_sq(points[j]);
                        if d2 > max_d2 {
                            max_d2 = d2;
                            p1 = points[i];
                            p2 = points[j];
                        }
                    }
                }
                painter.line_segment([p1, p2], stroke);
            }
        };

        match style {
            FillStyle::Horizontal => {
                // y = offset_y + k * step
                let k_min = ((rect.min.y - offset_y - EPSILON) / step).ceil() as i32;
                let k_max = ((rect.max.y - offset_y + EPSILON) / step).floor() as i32;

                for k in k_min..=k_max {
                    let y = (k as f32).mul_add(step, offset_y);
                    // Clamp to edges to avoid floating point overshoot
                    let x_min = rect.min.x;
                    let x_max = rect.max.x;
                    painter.line_segment([egui::pos2(x_min, y), egui::pos2(x_max, y)], stroke);
                }
            }
            FillStyle::Vertical => {
                // x = offset_x + k * step
                let k_min = ((rect.min.x - offset_x - EPSILON) / step).ceil() as i32;
                let k_max = ((rect.max.x - offset_x + EPSILON) / step).floor() as i32;

                for k in k_min..=k_max {
                    let x = (k as f32).mul_add(step, offset_x);
                    let y_min = rect.min.y;
                    let y_max = rect.max.y;
                    painter.line_segment([egui::pos2(x, y_min), egui::pos2(x, y_max)], stroke);
                }
            }
            FillStyle::Diagonal => {
                // x - y = C
                let c_global = offset_x - offset_y;
                let min_c = rect.min.x - rect.max.y;
                let max_c = rect.max.x - rect.min.y;

                let k_min = ((min_c - c_global - EPSILON) / step).ceil() as i32;
                let k_max = ((max_c - c_global + EPSILON) / step).floor() as i32;

                for k in k_min..=k_max {
                    let c = (k as f32).mul_add(step, c_global);
                    let mut points = Vec::new();

                    // y = x - c
                    let y1 = rect.min.x - c;
                    if y1 >= rect.min.y - EPSILON && y1 <= rect.max.y + EPSILON {
                        points.push(egui::pos2(rect.min.x, y1));
                    }

                    let y2 = rect.max.x - c;
                    if y2 >= rect.min.y - EPSILON && y2 <= rect.max.y + EPSILON {
                        points.push(egui::pos2(rect.max.x, y2));
                    }

                    let x1 = rect.min.y + c;
                    if x1 >= rect.min.x - EPSILON && x1 <= rect.max.x + EPSILON {
                        points.push(egui::pos2(x1, rect.min.y));
                    }

                    let x2 = rect.max.y + c;
                    if x2 >= rect.min.x - EPSILON && x2 <= rect.max.x + EPSILON {
                        points.push(egui::pos2(x2, rect.max.y));
                    }

                    draw_segment(&points);
                }
            }
            FillStyle::DiagonalBack => {
                // x + y = C
                let c_global = offset_x + offset_y;
                let min_c = rect.min.x + rect.min.y;
                let max_c = rect.max.x + rect.max.y;

                let k_min = ((min_c - c_global - EPSILON) / step).ceil() as i32;
                let k_max = ((max_c - c_global + EPSILON) / step).floor() as i32;

                for k in k_min..=k_max {
                    let c = (k as f32).mul_add(step, c_global);
                    let mut points = Vec::new();

                    // y = -x + c
                    let y1 = c - rect.min.x;
                    if y1 >= rect.min.y - EPSILON && y1 <= rect.max.y + EPSILON {
                        points.push(egui::pos2(rect.min.x, y1));
                    }

                    let y2 = c - rect.max.x;
                    if y2 >= rect.min.y - EPSILON && y2 <= rect.max.y + EPSILON {
                        points.push(egui::pos2(rect.max.x, y2));
                    }

                    let x1 = c - rect.min.y;
                    if x1 >= rect.min.x - EPSILON && x1 <= rect.max.x + EPSILON {
                        points.push(egui::pos2(x1, rect.min.y));
                    }

                    let x2 = c - rect.max.y;
                    if x2 >= rect.min.x - EPSILON && x2 <= rect.max.x + EPSILON {
                        points.push(egui::pos2(x2, rect.max.y));
                    }

                    draw_segment(&points);
                }
            }
            _ => {}
        }
    }

    fn draw_boundaries(
        &self,
        painter: &egui::Painter,
        viewport_rect: egui::Rect,
        visible_bounds: &alg_core::geo::AABB,
    ) {
        if !self.show_boundary {
            return;
        }

        let cell_id = match self.selected_cell_id {
            Some(id) => id,
            None => return,
        };

        let cell = match self.design.library().get_cell(cell_id) {
            Some(c) => c,
            None => return,
        };

        // 1. Draw Main Cell Boundary
        let boundary = cell.cell_boundary();
        let aabb = boundary.aabb();
        if aabb.min.x() != i32::MAX && aabb.intersects(visible_bounds) {
            self.draw_aabb_label(
                painter,
                viewport_rect,
                aabb,
                cell.name(),
                Color32::WHITE,
                true,
            );
        }

        // 2. Draw Instance Boundaries
        for instance in cell.instances() {
            if let Some(child_cell) = self.design.library().get_cell(instance.cell_id()) {
                let child_boundary = child_cell.cell_boundary();
                let trans_boundary = child_boundary.transform(instance.translation());
                let aabb = trans_boundary.aabb();

                if aabb.min.x() != i32::MAX && aabb.intersects(visible_bounds) {
                    // Label: "InstName - CellName"
                    self.draw_aabb_label(
                        painter,
                        viewport_rect,
                        aabb,
                        &instance.name().to_string(),
                        Color32::WHITE,
                        true,
                    );
                    self.draw_aabb_label(
                        painter,
                        viewport_rect,
                        aabb,
                        &child_cell.name().to_string(),
                        Color32::GRAY,
                        false,
                    );

                    // Instance Origin Dot
                    let origin_screen = self
                        .viewport
                        .gds_to_viewpoort(instance.translation().offset());
                    let radius = 4.0 * self.viewport.zoom.clamp(0.5, 2.0);
                    if self
                        .viewport
                        .screen_rect(viewport_rect)
                        .expand(radius as f32)
                        .contains(origin_screen)
                    {
                        painter.circle_filled(origin_screen, radius as f32, Color32::YELLOW);
                    }
                }
            }
        }
    }

    fn draw_aabb_label(
        &self,
        painter: &egui::Painter,
        viewport_rect: egui::Rect,
        aabb: &AABB,
        text: &str,
        color: Color32,
        is_main: bool,
    ) {
        let min = self.viewport.gds_to_viewpoort(&aabb.min);
        let max = self.viewport.gds_to_viewpoort(&aabb.max);
        let rect = egui::Rect::from_two_pos(min, max);

        let stroke_color = if is_main {
            Color32::WHITE
        } else {
            Color32::from_gray(180)
        };
        painter.rect_stroke(
            rect,
            0.0,
            Stroke::new(1.0, stroke_color),
            StrokeKind::Middle,
        );

        if is_main {
            let origin_screen = self.viewport.gds_to_viewpoort(&Vertex::new(0, 0));
            // Only draw origin if reasonably close to screen
            if self
                .viewport
                .screen_rect(viewport_rect)
                .expand(50.0)
                .contains(origin_screen)
            {
                let radius = 4.0 * self.viewport.zoom.clamp(0.5, 2.0);
                painter.circle_filled(origin_screen, radius as f32, Color32::WHITE);
            }
        }

        let world_height = (aabb.max.y() - aabb.min.y()) as f64;
        let scale = 0.025;
        // Clamp font size to reasonable limits (0px to 128px) to prevent lag
        let font_size = (world_height * scale * self.viewport.zoom).clamp(0.0, 128.0) as f32;

        let text_pos = if is_main {
            rect.left_top()
        } else {
            rect.right_top()
        };

        let align = if is_main {
            egui::Align2::LEFT_BOTTOM
        } else {
            egui::Align2::RIGHT_BOTTOM
        };

        // Only draw text if the position is within/near the screen bounds
        if self
            .viewport
            .screen_rect(viewport_rect)
            .expand(font_size * 2.0)
            .contains(text_pos)
        {
            painter.text(
                text_pos,
                align,
                text,
                egui::FontId::proportional(font_size),
                color,
            );
        }
    }
}

impl eframe::App for LayoutViewer {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        let start_time = std::time::Instant::now();

        egui::SidePanel::left("layers_panel").show(ctx, |ui| {
            // --- Cell Selection ---

            ui.label("Cells:");

            let mut new_selection = None;

            ui.push_id("cell_list_scroll", |ui| {
                egui::ScrollArea::vertical()
                    .max_height(200.0)
                    .show(ui, |ui| {
                        for (id, cell) in self.design.library().cells() {
                            let is_selected = self.selected_cell_id == Some(*id);
                            if ui.selectable_label(is_selected, cell.name()).clicked() {
                                new_selection = Some(*id);
                            }
                        }
                    });
            });

            if let Some(id) = new_selection {
                self.set_selected_cell(id);
            }

            ui.separator();
            ui.checkbox(&mut self.show_boundary, "Show DRC Boundaries");
            if ui
                .checkbox(&mut self.show_instance_origins, "Show Instance Origins")
                .changed()
                && let Some(cell_id) = self.selected_cell_id
            {
                self.rebuild_cache(cell_id);
            }

            ui.separator();
            ui.heading("Layers");

            // Iterate over config styles to make checkboxes
            let mut layer_ids: Vec<i16> = self.config.styles.keys().cloned().collect();
            layer_ids.sort(); // Sort by ID

            egui::ScrollArea::vertical().show(ui, |ui| {
                for id in layer_ids {
                    if let Some(style) = self.config.styles.get_mut(&id) {
                        ui.horizontal(|ui| {
                            // Color indicator
                            let (rect, _response) = ui
                                .allocate_exact_size(egui::Vec2::splat(15.0), egui::Sense::hover());
                            ui.painter().rect_filled(rect, 2.0, style.color);

                            // Checkbox
                            ui.checkbox(&mut style.visible, &style.name);
                        });
                    }
                }
            });

            // Instructions
            ui.separator();
            ui.label("Instructions:");
            ui.small("- Right Click: Pan");
            ui.small("- Scroll: Zoom");
        });

        // Main Central Panel
        egui::CentralPanel::default().show(ctx, |ui| {
            let rect = ui.available_rect_before_wrap();
            let painter = ui.painter_at(rect);

            self.viewport.screen_size = rect.size();

            // Interactions
            let response = ui.allocate_rect(rect, egui::Sense::click_and_drag());

            // Pan
            if response.dragged_by(egui::PointerButton::Secondary)
                || response.dragged_by(egui::PointerButton::Middle)
            {
                self.viewport.pan += response.drag_delta();
            }

            // Zoom
            if let Some(hover_pos) = ctx.input(|i| i.pointer.hover_pos()) {
                let scroll = ctx.input(|i| i.raw_scroll_delta.y);
                if scroll != 0.0 {
                    let old_zoom = self.viewport.zoom;
                    let zoom_factor = scroll.mul_add(0.001, 1.0);
                    // Clamp zoom between 0.0001 (zoomed out) and 500.0 (zoomed in - 1nm = 500px)
                    let new_zoom = (old_zoom * zoom_factor as f64).clamp(0.0001, 500.0);

                    // pan is Vec2 (f32)
                    let world_mouse = (hover_pos - self.viewport.pan) / old_zoom as f32;
                    let new_pan = hover_pos - (world_mouse * new_zoom as f32);

                    self.viewport.zoom = new_zoom;
                    self.viewport.pan = new_pan;
                }
            }

            // Draw adaptive grid
            self.viewport.draw_grid(&painter, rect);

            let visible_bounds = self.viewport.get_visible_bounds(rect);

            // Draw Content from Cache
            for (layer_id, shape) in &self.render_cache {
                if let Some(style) = self.config.styles.get(layer_id) {
                    if !style.visible {
                        continue;
                    }

                    // Frustum Culling: Skip shapes outside the viewport
                    if !shape.aabb().intersects(&visible_bounds) {
                        continue;
                    }

                    self.draw_shape(&painter, shape, style.color, style.fill);
                }
            }

            // Draw Overlays
            self.draw_boundaries(&painter, rect, &visible_bounds);

            // Draw Cursor Coordinate
            if let Some(pos) = ctx.input(|i| i.pointer.hover_pos()) {
                let world_pt = self.viewport.viewport_to_gds(pos);
                let dbu = self.design.technology().dbu_uu() as f32;
                let text = format!(
                    "X: {:.3} \u{b5}m\nY: {:.3} \u{b5}m",
                    world_pt.x() as f32 / dbu,
                    world_pt.y() as f32 / dbu,
                );
                painter.text(
                    rect.left_bottom() + egui::Vec2::new(10.0, -30.0),
                    egui::Align2::LEFT_BOTTOM,
                    text,
                    egui::FontId::monospace(14.0),
                    Color32::WHITE,
                );
            }

            // Draw Performance Monitor
            painter.text(
                rect.right_bottom() + egui::Vec2::new(-10.0, -10.0),
                egui::Align2::RIGHT_BOTTOM,
                format!("Frame Time: {:.2} ms", self.last_frame_time),
                egui::FontId::monospace(12.0),
                Color32::GREEN,
            );
        });

        // Calculate frame time and request next frame
        self.last_frame_time = start_time.elapsed().as_secs_f32() * 1000.0;
        ctx.request_repaint();
    }
}
