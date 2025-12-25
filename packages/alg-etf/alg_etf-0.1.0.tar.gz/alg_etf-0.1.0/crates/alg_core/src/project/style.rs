use eframe::egui::Color32;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum FillStyle {
    Solid,
    NoFill,
    Diagonal,     // 45 degrees
    DiagonalBack, // -45 degrees
    Horizontal,
    Vertical,
}

#[derive(Clone)]
pub struct LayerStyle {
    pub color: Color32,
    pub visible: bool,
    pub fill: FillStyle,
    pub name: String,
}
