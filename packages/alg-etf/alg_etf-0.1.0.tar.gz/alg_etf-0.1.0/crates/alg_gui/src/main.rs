use alg_core::geo::{Rectangle, Shape, Vertex};
use alg_core::library::Library;
use alg_core::library::cell::{Cell, CellId};
use alg_core::library::instance::{Instance, Orientation, Translate};
use alg_core::library::layer::LayerId;
use alg_core::project::{Design, Technology};
use alg_core::project::{FillStyle, LayerStyle};

use alg_gui::viewer::LayoutViewer;
use eframe::egui::Color32;

fn main() -> eframe::Result<()> {
    // 1. Setup Technology
    let mut tech = Technology::new();

    // Define Layers
    let l_nwell = LayerId(1);
    let l_active = LayerId(2);
    let l_poly = LayerId(3);
    let l_nplus = LayerId(4);
    let l_pplus = LayerId(5);
    let l_contact = LayerId(6);
    let l_metal1 = LayerId(7);

    tech.add_layer_def(
        l_metal1,
        "Metal1".to_string(),
        LayerStyle {
            color: Color32::from_rgb(0, 0, 255), // Blue
            visible: true,
            fill: FillStyle::Solid,
            name: "Metal1".to_string(),
        },
    );
    tech.add_layer_def(
        l_contact,
        "Contact".to_string(),
        LayerStyle {
            color: Color32::from_rgb(50, 50, 50), // Dark Grey
            visible: true,
            fill: FillStyle::Solid,
            name: "Contact".to_string(),
        },
    );
    tech.add_layer_def(
        l_pplus,
        "P-Plus".to_string(),
        LayerStyle {
            color: Color32::from_rgb(165, 42, 42), // Brown
            visible: true,
            fill: FillStyle::Solid,
            name: "P-Plus".to_string(),
        },
    );
    tech.add_layer_def(
        l_nplus,
        "N-Plus".to_string(),
        LayerStyle {
            color: Color32::from_rgb(255, 165, 0), // Orange
            visible: true,
            fill: FillStyle::Solid,
            name: "N-Plus".to_string(),
        },
    );
    tech.add_layer_def(
        l_poly,
        "Poly".to_string(),
        LayerStyle {
            color: Color32::from_rgb(255, 0, 0), // Red
            visible: true,
            fill: FillStyle::Solid,
            name: "Poly".to_string(),
        },
    );

    tech.add_layer_def(
        l_active,
        "Active".to_string(),
        LayerStyle {
            color: Color32::from_rgb(0, 255, 0), // Green
            visible: true,
            fill: FillStyle::Diagonal,
            name: "Active".to_string(),
        },
    );

    tech.add_layer_def(
        l_nwell,
        "N-Well".to_string(),
        LayerStyle {
            color: Color32::from_rgb(255, 255, 0), // Yellow
            visible: true,
            fill: FillStyle::DiagonalBack,
            name: "N-Well".to_string(),
        },
    );

    // 2. Setup Library
    let mut lib = Library::new("MyLib".to_string());

    // --- NMOS Cell ---
    // W = 1000nm, L = 180nm.
    // Active: 980 x 1000
    // Poly: 180 x 1400 (extends 200 up/down)
    let nmos_id = CellId(1);
    let mut nmos = Cell::new("NMOS_180n_1u".to_string(), nmos_id);

    // Active
    nmos.add_shape(
        l_active,
        Shape::Rectangle(Rectangle::new(Vertex::new(0, 0), Vertex::new(980, 1000))),
    );

    // Poly Gate
    nmos.add_shape(
        l_poly,
        Shape::Rectangle(Rectangle::new(
            Vertex::new(400, -200),
            Vertex::new(580, 1200),
        )),
    );

    // N-Plus (Covering Active)
    nmos.add_shape(
        l_nplus,
        Shape::Rectangle(Rectangle::new(
            Vertex::new(-100, -100),
            Vertex::new(1080, 1100),
        )),
    );

    // Contacts (Source and Drain)
    // Source Contact (Left)
    nmos.add_shape(
        l_contact,
        Shape::Rectangle(Rectangle::new(
            Vertex::new(100, 400),
            Vertex::new(300, 600), // 200x200 contact
        )),
    );
    // Drain Contact (Right)
    nmos.add_shape(
        l_contact,
        Shape::Rectangle(Rectangle::new(Vertex::new(680, 400), Vertex::new(880, 600))),
    );

    lib.add_cell(nmos);

    // --- PMOS Cell ---
    // Similar to NMOS but with N-Well and P-Plus
    let pmos_id = CellId(2);
    let mut pmos = Cell::new("PMOS_180n_1u".to_string(), pmos_id);

    // N-Well (Large container)
    pmos.add_shape(
        l_nwell,
        Shape::Rectangle(Rectangle::new(
            Vertex::new(-500, -500),
            Vertex::new(1500, 1500),
        )),
    );

    // Active
    pmos.add_shape(
        l_active,
        Shape::Rectangle(Rectangle::new(Vertex::new(0, 0), Vertex::new(980, 1000))),
    );

    // Poly Gate
    pmos.add_shape(
        l_poly,
        Shape::Rectangle(Rectangle::new(
            Vertex::new(400, -200),
            Vertex::new(580, 1200),
        )),
    );

    // P-Plus
    pmos.add_shape(
        l_pplus,
        Shape::Rectangle(Rectangle::new(
            Vertex::new(-100, -100),
            Vertex::new(1080, 1100),
        )),
    );

    // Contacts
    pmos.add_shape(
        l_contact,
        Shape::Rectangle(Rectangle::new(Vertex::new(100, 400), Vertex::new(300, 600))),
    );
    pmos.add_shape(
        l_contact,
        Shape::Rectangle(Rectangle::new(Vertex::new(680, 400), Vertex::new(880, 600))),
    );

    lib.add_cell(pmos);

    // --- Top Cell (Inverter-ish) ---
    let top_id = CellId(3);
    let mut top = Cell::new("Top_Level".to_string(), top_id);

    // Instance NMOS at (0, 0)
    top.add_instance(
        Instance::new(
            "M1_NMOS".to_string(),
            nmos_id,
            Translate::new(Vertex::new(0, 0), Orientation::R0),
        ),
        &lib,
    );

    // Instance PMOS at (0, 2000)
    top.add_instance(
        Instance::new(
            "M2_PMOS".to_string(),
            pmos_id,
            Translate::new(Vertex::new(0, 2000), Orientation::R0),
        ),
        &lib,
    );

    // Instance NMOS rotated 90 degrees to show transformation capability
    // Placed at (2000, 1000)
    top.add_instance(
        Instance::new(
            "M3_NMOS_MX90".to_string(),
            nmos_id,
            Translate::new(Vertex::new(4000, 2000), Orientation::MX90),
        ),
        &lib,
    );

    top.add_instance(
        Instance::new(
            "M5_NMOS_R180".to_string(),
            nmos_id,
            Translate::new(Vertex::new(3000, 4000), Orientation::MX180),
        ),
        &lib,
    );

    // Instance PMOS rotated 90 degrees
    top.add_instance(
        Instance::new(
            "M4_PMOS_R90".to_string(),
            pmos_id,
            Translate::new(Vertex::new(4000, 5000), Orientation::R90),
        ),
        &lib,
    );

    // Metal1 Wire connecting them (Simulated)
    top.add_shape(
        l_metal1,
        Shape::Rectangle(Rectangle::new(
            Vertex::new(400, 1000),
            Vertex::new(580, 2000),
        )),
    );

    lib.add_cell(top);

    // 3. Create Design
    let design = Design::new(tech, lib);

    // 4. Launch Viewer
    let options = eframe::NativeOptions {
        viewport: eframe::egui::ViewportBuilder::default().with_inner_size([1200.0, 800.0]),
        ..Default::default()
    };

    eframe::run_native(
        "GDS Layout Viewer (Beta, but looks nice)",
        options,
        Box::new(|_cc| Ok(Box::new(LayoutViewer::new(design)))),
    )
}
