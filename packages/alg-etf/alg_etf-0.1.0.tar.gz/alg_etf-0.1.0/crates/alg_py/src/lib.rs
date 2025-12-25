use alg_core::geo::{Rectangle, Shape, Vertex};
use alg_core::library::Library;
use alg_core::library::cell::{Cell, CellId};
use alg_core::library::instance::{Instance, Orientation, Translate};
use alg_core::library::layer::LayerId;
use alg_core::project::style::{FillStyle, LayerStyle};
use alg_core::project::{Design, Technology};
use alg_gui::viewer::LayoutViewer;
use eframe::egui::Color32;
use pyo3::prelude::*;

/// Represents a 2D point with integer coordinates.
#[pyclass(name = "Vertex")]
#[derive(Clone)]
pub struct PyVertex(pub Vertex);

#[pymethods]
impl PyVertex {
    #[new]
    pub fn new(x: i32, y: i32) -> Self {
        PyVertex(Vertex::new(x, y))
    }
}

#[pyclass(name = "LayerId")]
#[derive(Clone)]
pub struct PyLayerId(pub LayerId);

#[pymethods]
impl PyLayerId {
    #[new]
    pub fn new(id: u8) -> Self {
        PyLayerId(LayerId(id))
    }
}

#[pyclass(name = "CellId")]
#[derive(Clone)]
pub struct PyCellId(pub CellId);

#[pymethods]
impl PyCellId {
    #[new]
    pub fn new(id: usize) -> Self {
        PyCellId(CellId(id))
    }
}

#[pyclass(name = "Orientation", eq, eq_int)]
#[derive(Clone, PartialEq)]
pub enum PyOrientation {
    R0,
    R90,
    R180,
    R270,
    MX,
    MX90,
    MX180,
    MX270,
}

impl From<PyOrientation> for Orientation {
    fn from(o: PyOrientation) -> Self {
        match o {
            PyOrientation::R0 => Orientation::R0,
            PyOrientation::R90 => Orientation::R90,
            PyOrientation::R180 => Orientation::R180,
            PyOrientation::R270 => Orientation::R270,
            PyOrientation::MX => Orientation::MX,
            PyOrientation::MX90 => Orientation::MX90,
            PyOrientation::MX180 => Orientation::MX180,
            PyOrientation::MX270 => Orientation::MX270,
        }
    }
}

#[pyclass(name = "FillStyle", eq, eq_int)]
#[derive(Clone, PartialEq)]
pub enum PyFillStyle {
    Solid,
    NoFill,
    Diagonal,
    DiagonalBack,
    Horizontal,
    Vertical,
}

impl From<PyFillStyle> for FillStyle {
    fn from(f: PyFillStyle) -> Self {
        match f {
            PyFillStyle::Solid => FillStyle::Solid,
            PyFillStyle::NoFill => FillStyle::NoFill,
            PyFillStyle::Diagonal => FillStyle::Diagonal,
            PyFillStyle::DiagonalBack => FillStyle::DiagonalBack,
            PyFillStyle::Horizontal => FillStyle::Horizontal,
            PyFillStyle::Vertical => FillStyle::Vertical,
        }
    }
}

#[pyclass(name = "LayerStyle")]
#[derive(Clone)]
pub struct PyLayerStyle {
    pub inner: LayerStyle,
}

#[pymethods]
impl PyLayerStyle {
    #[new]
    pub fn new(r: u8, g: u8, b: u8, visible: bool, fill: PyFillStyle, name: String) -> Self {
        PyLayerStyle {
            inner: LayerStyle {
                color: Color32::from_rgb(r, g, b),
                visible,
                fill: fill.into(),
                name,
            },
        }
    }
}

#[pyclass(name = "Technology")]
#[derive(Clone)]
pub struct PyTechnology {
    pub inner: Technology,
}

#[pymethods]
impl PyTechnology {
    #[new]
    pub fn new() -> Self {
        PyTechnology {
            inner: Technology::new(),
        }
    }

    pub fn add_layer_def(&mut self, layer_id: &PyLayerId, name: String, style: &PyLayerStyle) {
        self.inner
            .add_layer_def(layer_id.0, name, style.inner.clone());
    }
}

#[pyclass(name = "Library")]
#[derive(Clone)]
pub struct PyLibrary {
    pub inner: Library,
}

#[pymethods]
impl PyLibrary {
    #[new]
    pub fn new(name: String) -> Self {
        PyLibrary {
            inner: Library::new(name),
        }
    }

    pub fn add_cell(&mut self, cell: &PyCell) {
        self.inner.add_cell(cell.inner.clone());
    }
}

#[pyclass(name = "Cell")]
#[derive(Clone)]
pub struct PyCell {
    pub inner: Cell,
}

#[pymethods]
impl PyCell {
    #[new]
    pub fn new(name: String, id: &PyCellId) -> Self {
        PyCell {
            inner: Cell::new(name, id.0),
        }
    }

    pub fn add_shape(&mut self, layer_id: &PyLayerId, shape: &PyShape) {
        self.inner.add_shape(layer_id.0, shape.0.clone());
    }

    pub fn add_instance(&mut self, instance: &PyInstance, library: &PyLibrary) {
        self.inner.add_instance(instance.0.clone(), &library.inner);
    }
}

#[pyclass(name = "Shape")]
#[derive(Clone)]
pub struct PyShape(pub Shape);

#[pymethods]
impl PyShape {
    #[staticmethod]
    pub fn rectangle(p1: PyVertex, p2: PyVertex) -> Self {
        PyShape(Shape::Rectangle(Rectangle::new(p1.0, p2.0)))
    }
}

#[pyclass(name = "Instance")]
#[derive(Clone)]
pub struct PyInstance(pub Instance);

#[pymethods]
impl PyInstance {
    #[new]
    pub fn new(
        name: String,
        cell_id: &PyCellId,
        x: i32,
        y: i32,
        orientation: PyOrientation,
    ) -> Self {
        let translate = Translate::new(Vertex::new(x, y), orientation.into());
        PyInstance(Instance::new(name, cell_id.0, translate))
    }
}

#[pyclass(name = "Design")]
#[derive(Clone)]
pub struct PyDesign {
    pub inner: Design,
}

#[pymethods]
impl PyDesign {
    #[new]
    pub fn new(tech: &PyTechnology, lib: &PyLibrary) -> Self {
        PyDesign {
            inner: Design::new(tech.inner.clone(), lib.inner.clone()),
        }
    }
}

#[pyfunction]
pub fn launch_viewer(design: PyDesign) -> PyResult<()> {
    let options = eframe::NativeOptions {
        viewport: eframe::egui::ViewportBuilder::default().with_inner_size([1200.0, 800.0]),
        ..Default::default()
    };

    eframe::run_native(
        "GDS Layout Viewer (via Python)",
        options,
        Box::new(|_cc| Ok(Box::new(LayoutViewer::new(design.inner)))),
    )
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(launch_viewer, m)?)?;
    m.add_class::<PyVertex>()?;
    m.add_class::<PyLayerId>()?;
    m.add_class::<PyCellId>()?;
    m.add_class::<PyOrientation>()?;
    m.add_class::<PyFillStyle>()?;
    m.add_class::<PyLayerStyle>()?;
    m.add_class::<PyTechnology>()?;
    m.add_class::<PyLibrary>()?;
    m.add_class::<PyCell>()?;
    m.add_class::<PyShape>()?;
    m.add_class::<PyInstance>()?;
    m.add_class::<PyDesign>()?;
    Ok(())
}
