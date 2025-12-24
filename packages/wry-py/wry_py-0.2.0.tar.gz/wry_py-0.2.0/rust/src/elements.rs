use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Mutex;

/// Option for select dropdowns.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SelectOption {
    pub value: String,
    pub label: String,
}

/// Serializable element definition sent to frontend.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ElementDef {
    pub id: String,              // Internal UUID
    pub element_type: String,

    // User-facing identification
    #[serde(skip_serializing_if = "Option::is_none")]
    pub user_id: Option<String>, // User-specified ID for targeting
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub class_names: Vec<String>, // User-specified CSS classes

    // Layout
    #[serde(skip_serializing_if = "Option::is_none")]
    pub width: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub height: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub min_width: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_width: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub min_height: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_height: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub flex_direction: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub align_items: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub justify_content: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub gap: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub flex_wrap: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub flex_grow: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub flex_shrink: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub flex_basis: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub align_self: Option<String>,

    // Grid layout
    pub display_grid: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub grid_template_columns: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub grid_template_rows: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub grid_column: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub grid_row: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub place_items: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub padding: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub padding_top: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub padding_right: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub padding_bottom: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub padding_left: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub margin_top: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub margin_right: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub margin_bottom: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub margin_left: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub margin: Option<f32>,
    pub size_full: bool,

    // Styling
    #[serde(skip_serializing_if = "Option::is_none")]
    pub background_color: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub text_color: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_radius: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_radius_top_left: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_radius_top_right: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_radius_bottom_right: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_radius_bottom_left: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_width: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_width_top: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_width_right: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_width_bottom: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_width_left: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_color: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_color_top: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_color_right: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_color_bottom: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub border_color_left: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub overflow: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub text_align: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub word_wrap: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub position: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub top: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub right: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub bottom: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub left: Option<f32>,

    // Text
    #[serde(skip_serializing_if = "Option::is_none")]
    pub text_content: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub font_size: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub font_weight: Option<String>,

    // Transitions
    #[serde(skip_serializing_if = "Option::is_none")]
    pub transition: Option<String>,

    // Opacity
    #[serde(skip_serializing_if = "Option::is_none")]
    pub opacity: Option<f32>,

    // Cursor
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
    // Raw CSS styles
    #[serde(skip_serializing_if = "Option::is_none")]
    pub style: Option<String>,

    // Hover styles
    #[serde(skip_serializing_if = "Option::is_none")]
    pub hover_bg: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub hover_text_color: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub hover_border_color: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub hover_opacity: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub hover_scale: Option<f32>,

    // Focus styles
    #[serde(skip_serializing_if = "Option::is_none")]
    pub focus_bg: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub focus_text_color: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub focus_border_color: Option<String>,

    // Image properties
    #[serde(skip_serializing_if = "Option::is_none")]
    pub alt: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub object_fit: Option<String>,

    // Interactivity
    #[serde(skip_serializing_if = "Option::is_none")]
    pub on_click: Option<String>, // callback ID
    #[serde(skip_serializing_if = "Option::is_none")]
    pub on_input: Option<String>, // callback ID for input changes
    #[serde(skip_serializing_if = "Option::is_none")]
    pub on_mouse_enter: Option<String>, // callback ID for mouse enter
    #[serde(skip_serializing_if = "Option::is_none")]
    pub on_mouse_leave: Option<String>, // callback ID for mouse leave
    #[serde(skip_serializing_if = "Option::is_none")]
    pub on_mouse_down: Option<String>, // callback ID for mouse down
    #[serde(skip_serializing_if = "Option::is_none")]
    pub on_mouse_up: Option<String>, // callback ID for mouse up
    #[serde(skip_serializing_if = "Option::is_none")]
    pub value: Option<String>, // input value
    #[serde(skip_serializing_if = "Option::is_none")]
    pub placeholder: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub on_change: Option<String>, // callback ID for checkbox/radio/select changes
    #[serde(skip_serializing_if = "Option::is_none")]
    pub checked: Option<bool>, // for checkbox/radio
    #[serde(skip_serializing_if = "Option::is_none")]
    pub radio_group: Option<String>, // name attribute for radio buttons
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub options: Vec<SelectOption>, // for select dropdowns
    #[serde(skip_serializing_if = "Option::is_none")]
    pub selected: Option<String>, // selected option value for select
    #[serde(skip_serializing_if = "Option::is_none")]
    pub label: Option<String>, // label text for checkbox/radio

    // Children
    #[serde(default)]
    pub children: Vec<ElementDef>,
}

impl Default for ElementDef {
    fn default() -> Self {
        Self {
            id: uuid(),
            element_type: "div".to_string(),
            user_id: None,
            class_names: Vec::new(),
            width: None,
            height: None,
            min_width: None,
            max_width: None,
            min_height: None,
            max_height: None,
            flex_direction: None,
            align_items: None,
            justify_content: None,
            gap: None,
            flex_wrap: None,
            flex_grow: None,
            flex_shrink: None,
            flex_basis: None,
            align_self: None,
            display_grid: false,
            grid_template_columns: None,
            grid_template_rows: None,
            grid_column: None,
            grid_row: None,
            place_items: None,
            padding: None,
            padding_top: None,
            padding_right: None,
            padding_bottom: None,
            padding_left: None,
            margin_top: None,
            margin_right: None,
            margin_bottom: None,
            margin_left: None,
            margin: None,
            size_full: false,
            background_color: None,
            text_color: None,
            border_radius: None,
            border_radius_top_left: None,
            border_radius_top_right: None,
            border_radius_bottom_right: None,
            border_radius_bottom_left: None,
            border_width: None,
            border_width_top: None,
            border_width_right: None,
            border_width_bottom: None,
            border_width_left: None,
            border_color: None,
            border_color_top: None,
            border_color_right: None,
            border_color_bottom: None,
            border_color_left: None,
            overflow: None,
            text_align: None,
            word_wrap: None,
            position: None,
            top: None,
            right: None,
            bottom: None,
            left: None,
            text_content: None,
            font_size: None,
            font_weight: None,
            transition: None,
            opacity: None,
            cursor: None,
            style: None,
            hover_bg: None,
            hover_text_color: None,
            hover_border_color: None,
            hover_opacity: None,
            hover_scale: None,
            focus_bg: None,
            focus_text_color: None,
            focus_border_color: None,
            alt: None,
            object_fit: None,
            on_click: None,
            on_input: None,
            on_mouse_enter: None,
            on_mouse_leave: None,
            on_mouse_down: None,
            on_mouse_up: None,
            value: None,
            placeholder: None,
            on_change: None,
            checked: None,
            radio_group: None,
            options: Vec::new(),
            selected: None,
            label: None,
            children: Vec::new(),
        }
    }
}

fn uuid() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    static COUNTER: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
    let count = COUNTER.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    format!("el_{:x}_{}", nanos, count)
}

// Global callback store
static CALLBACK_STORE: Mutex<Option<HashMap<String, Py<PyAny>>>> = Mutex::new(None);

fn init_callback_store() {
    let mut store = CALLBACK_STORE.lock().unwrap();
    if store.is_none() {
        *store = Some(HashMap::new());
    }
}

fn store_callback(id: String, callback: Py<PyAny>) {
    init_callback_store();
    let mut store = CALLBACK_STORE.lock().unwrap();
    if let Some(ref mut map) = *store {
        map.insert(id, callback);
    }
}

pub fn take_callbacks() -> HashMap<String, Py<PyAny>> {
    init_callback_store();
    let mut store = CALLBACK_STORE.lock().unwrap();
    store.take().unwrap_or_default()
}

/// Python Element class
#[pyclass]
#[derive(Clone)]
pub struct Element {
    pub def: ElementDef,
    callback_ids: Vec<String>,
}

#[pymethods]
impl Element {
    /// Create a new element.
    ///
    /// Args:
    ///     element_type: The HTML element type (e.g., "div", "button"). Defaults to "div".
    #[new]
    #[pyo3(text_signature = "(element_type=None)")]
    fn new(element_type: Option<String>) -> Self {
        let mut def = ElementDef::default();
        if let Some(t) = element_type {
            def.element_type = t;
        }
        Element {
            def,
            callback_ids: Vec::new(),
        }
    }

    /// Convert the element to a JSON string.
    ///
    /// Returns:
    ///     JSON representation of the element and all its properties.
    #[pyo3(text_signature = "($self)")]
    fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(&self.def)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    fn __repr__(&self) -> String {
        format!(
            "Element(type='{}', children={})",
            self.def.element_type,
            self.def.children.len()
        )
    }
}

impl Element {
    pub fn collect_callbacks(&self) -> HashMap<String, Py<PyAny>> {
        take_callbacks()
    }
}

/// Builder pattern for creating elements
#[pyclass]
#[derive(Clone)]
pub struct ElementBuilder {
    element: Element,
}

#[pymethods]
impl ElementBuilder {
    /// Create a div element (generic container).
    #[staticmethod]
    #[pyo3(text_signature = "()")]
    fn div() -> Self {
        ElementBuilder {
            element: Element::new(Some("div".to_string())),
        }
    }

    /// Create a text element.
    ///
    /// Args:
    ///     content: The text to display.
    #[staticmethod]
    #[pyo3(text_signature = "(content)")]
    fn text(content: String) -> Self {
        let mut element = Element::new(Some("text".to_string()));
        element.def.text_content = Some(content);
        ElementBuilder { element }
    }

    /// Create a button element.
    ///
    /// Args:
    ///     label: The text to display on the button.
    #[staticmethod]
    #[pyo3(text_signature = "(label)")]
    fn button(label: String) -> Self {
        let mut element = Element::new(Some("button".to_string()));
        element.def.text_content = Some(label);
        ElementBuilder { element }
    }

    /// Create an image element.
    ///
    /// Args:
    ///     src: The image source URL or path.
    #[staticmethod]
    #[pyo3(text_signature = "(src)")]
    fn image(src: String) -> Self {
        let mut element = Element::new(Some("image".to_string()));
        element.def.text_content = Some(src);
        ElementBuilder { element }
    }

    /// Create an input field element.
    #[staticmethod]
    #[pyo3(text_signature = "()")]
    fn input() -> Self {
        ElementBuilder {
            element: Element::new(Some("input".to_string())),
        }
    }

    /// Create a checkbox element.
    #[staticmethod]
    #[pyo3(text_signature = "(label=None)")]
    fn checkbox(label: Option<String>) -> Self {
        let mut element = Element::new(Some("checkbox".to_string()));
        element.def.label = label;
        ElementBuilder { element }
    }

    /// Create a radio button element.
    #[staticmethod]
    #[pyo3(text_signature = "(label=None)")]
    fn radio(label: Option<String>) -> Self {
        let mut element = Element::new(Some("radio".to_string()));
        element.def.label = label;
        ElementBuilder { element }
    }

    /// Create a select dropdown element.
    #[staticmethod]
    #[pyo3(text_signature = "()")]
    fn select() -> Self {
        ElementBuilder {
            element: Element::new(Some("select".to_string())),
        }
    }

    // User-facing identification

    /// Set a user-facing ID for targeting this element. Used for partial updates.
    #[pyo3(text_signature = "($self, id)")]
    fn id(mut slf: PyRefMut<'_, Self>, id: String) -> PyRefMut<'_, Self> {
        slf.element.def.user_id = Some(id);
        slf
    }

    /// Add a CSS class name to this element.
    #[pyo3(text_signature = "($self, name)")]
    fn class_name(mut slf: PyRefMut<'_, Self>, name: String) -> PyRefMut<'_, Self> {
        slf.element.def.class_names.push(name);
        slf
    }

    /// Add multiple CSS class names to this element.
    #[pyo3(text_signature = "($self, names)")]
    fn classes(mut slf: PyRefMut<'_, Self>, names: Vec<String>) -> PyRefMut<'_, Self> {
        slf.element.def.class_names.extend(names);
        slf
    }

    /// Set width in pixels. Returns self for chaining.
    #[pyo3(text_signature = "($self, w)")]
    fn width(mut slf: PyRefMut<'_, Self>, w: f32) -> PyRefMut<'_, Self> {
        slf.element.def.width = Some(w);
        slf
    }

    /// Set height in pixels. Returns self for chaining.
    #[pyo3(text_signature = "($self, h)")]
    fn height(mut slf: PyRefMut<'_, Self>, h: f32) -> PyRefMut<'_, Self> {
        slf.element.def.height = Some(h);
        slf
    }

    /// Set both width and height in pixels. Returns self for chaining.
    #[pyo3(text_signature = "($self, w, h)")]
    fn size(mut slf: PyRefMut<'_, Self>, w: f32, h: f32) -> PyRefMut<'_, Self> {
        slf.element.def.width = Some(w);
        slf.element.def.height = Some(h);
        slf
    }

    /// Make element fill available space
    #[pyo3(text_signature = "($self)")]
    fn size_full(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.size_full = true;
        slf
    }

    /// Set width to 100%
    #[pyo3(text_signature = "($self)")]
    fn full_width(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.style = Some(
            slf.element.def.style.clone().unwrap_or_default() + "width: 100%;"
        );
        slf
    }

    /// Set height to 100%
    #[pyo3(text_signature = "($self)")]
    fn full_height(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.style = Some(
            slf.element.def.style.clone().unwrap_or_default() + "height: 100%;"
        );
        slf
    }

    /// Set minimum width in pixels
    #[pyo3(text_signature = "($self, w)")]
    fn min_width(mut slf: PyRefMut<'_, Self>, w: f32) -> PyRefMut<'_, Self> {
        slf.element.def.min_width = Some(w);
        slf
    }

    /// Set maximum width in pixels
    #[pyo3(text_signature = "($self, w)")]
    fn max_width(mut slf: PyRefMut<'_, Self>, w: f32) -> PyRefMut<'_, Self> {
        slf.element.def.max_width = Some(w);
        slf
    }

    /// Set minimum height in pixels
    #[pyo3(text_signature = "($self, h)")]
    fn min_height(mut slf: PyRefMut<'_, Self>, h: f32) -> PyRefMut<'_, Self> {
        slf.element.def.min_height = Some(h);
        slf
    }

    /// Set maximum height in pixels
    #[pyo3(text_signature = "($self, h)")]
    fn max_height(mut slf: PyRefMut<'_, Self>, h: f32) -> PyRefMut<'_, Self> {
        slf.element.def.max_height = Some(h);
        slf
    }

    /// Use vertical (column) flex layout. Returns self for chaining.
    #[pyo3(text_signature = "($self)")]
    fn v_flex(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.flex_direction = Some("column".to_string());
        slf
    }

    /// Use horizontal (row) flex layout. Returns self for chaining.
    #[pyo3(text_signature = "($self)")]
    fn h_flex(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.flex_direction = Some("row".to_string());
        slf
    }

    /// Center child items perpendicular to flex direction. Returns self for chaining.
    #[pyo3(text_signature = "($self)")]
    fn items_center(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.align_items = Some("center".to_string());
        slf
    }

    /// Center content along the flex direction. Returns self for chaining.
    #[pyo3(text_signature = "($self)")]
    fn justify_center(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.justify_content = Some("center".to_string());
        slf
    }

    /// Distribute children evenly with space between them. Returns self for chaining.
    #[pyo3(text_signature = "($self)")]
    fn justify_between(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.justify_content = Some("space-between".to_string());
        slf
    }

    /// Set spacing between child elements in pixels. Returns self for chaining.
    #[pyo3(text_signature = "($self, g)")]
    fn gap(mut slf: PyRefMut<'_, Self>, g: f32) -> PyRefMut<'_, Self> {
        slf.element.def.gap = Some(g);
        slf
    }

    /// Allow flex items to wrap to multiple lines
    #[pyo3(text_signature = "($self)")]
    fn flex_wrap(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.flex_wrap = Some("wrap".to_string());
        slf
    }

    /// Prevent flex items from wrapping
    #[pyo3(text_signature = "($self)")]
    fn flex_nowrap(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.flex_wrap = Some("nowrap".to_string());
        slf
    }

    /// Set flex grow factor
    #[pyo3(text_signature = "($self, value)")]
    fn flex_grow(mut slf: PyRefMut<'_, Self>, value: f32) -> PyRefMut<'_, Self> {
        slf.element.def.flex_grow = Some(value);
        slf
    }

    /// Set flex shrink factor
    #[pyo3(text_signature = "($self, value)")]
    fn flex_shrink(mut slf: PyRefMut<'_, Self>, value: f32) -> PyRefMut<'_, Self> {
        slf.element.def.flex_shrink = Some(value);
        slf
    }

    /// Set flex basis (initial size before growing/shrinking)
    #[pyo3(text_signature = "($self, value)")]
    fn flex_basis(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.flex_basis = Some(value);
        slf
    }

    /// Shorthand: flex-grow: 1
    #[pyo3(text_signature = "($self)")]
    fn flex_1(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.flex_grow = Some(1.0);
        slf.element.def.flex_shrink = Some(1.0);
        slf.element.def.flex_basis = Some("0%".to_string());
        slf
    }

    /// Align this item differently from siblings
    #[pyo3(text_signature = "($self, value)")]
    fn align_self(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.align_self = Some(value);
        slf
    }

    // Grid layout methods

    /// Use CSS grid layout
    #[pyo3(text_signature = "($self)")]
    fn grid(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.display_grid = true;
        slf
    }

    /// Set grid template columns (e.g., "1fr 1fr 1fr" or "repeat(3, 1fr)")
    #[pyo3(text_signature = "($self, value)")]
    fn grid_cols(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.display_grid = true;
        slf.element.def.grid_template_columns = Some(value);
        slf
    }

    /// Set grid template rows (e.g., "auto 1fr auto")
    #[pyo3(text_signature = "($self, value)")]
    fn grid_rows(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.display_grid = true;
        slf.element.def.grid_template_rows = Some(value);
        slf
    }

    /// Set which column(s) this item spans (e.g., "1 / 3" or "span 2")
    #[pyo3(text_signature = "($self, value)")]
    fn col(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.grid_column = Some(value);
        slf
    }

    /// Set which row(s) this item spans (e.g., "1 / 3" or "span 2")
    #[pyo3(text_signature = "($self, value)")]
    fn row(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.grid_row = Some(value);
        slf
    }

    /// Set place-items (align and justify items)
    #[pyo3(text_signature = "($self, value)")]
    fn place_items(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.place_items = Some(value);
        slf
    }

    /// Center grid items both horizontally and vertically
    #[pyo3(text_signature = "($self)")]
    fn place_center(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.place_items = Some("center".to_string());
        slf
    }

    /// Set padding in pixels. With one arg, applies to all sides. With two args, (vertical, horizontal).
    #[pyo3(signature = (y, x = None), text_signature = "($self, y, x=None)")]
    fn padding(mut slf: PyRefMut<'_, Self>, y: f32, x: Option<f32>) -> PyRefMut<'_, Self> {
        match x {
            Some(h) => {
                slf.element.def.padding_top = Some(y);
                slf.element.def.padding_bottom = Some(y);
                slf.element.def.padding_left = Some(h);
                slf.element.def.padding_right = Some(h);
            }
            None => {
                slf.element.def.padding = Some(y);
            }
        }
        slf
    }

    /// Alias for padding
    #[pyo3(signature = (y, x = None), text_signature = "($self, y, x=None)")]
    fn p(mut slf: PyRefMut<'_, Self>, y: f32, x: Option<f32>) -> PyRefMut<'_, Self> {
        match x {
            Some(h) => {
                slf.element.def.padding_top = Some(y);
                slf.element.def.padding_bottom = Some(y);
                slf.element.def.padding_left = Some(h);
                slf.element.def.padding_right = Some(h);
            }
            None => {
                slf.element.def.padding = Some(y);
            }
        }
        slf
    }

    /// Set padding top
    #[pyo3(text_signature = "($self, p)")]
    fn pt(mut slf: PyRefMut<'_, Self>, p: f32) -> PyRefMut<'_, Self> {
        slf.element.def.padding_top = Some(p);
        slf
    }

    /// Set padding right
    #[pyo3(text_signature = "($self, p)")]
    fn pr(mut slf: PyRefMut<'_, Self>, p: f32) -> PyRefMut<'_, Self> {
        slf.element.def.padding_right = Some(p);
        slf
    }

    /// Set padding bottom
    #[pyo3(text_signature = "($self, p)")]
    fn pb(mut slf: PyRefMut<'_, Self>, p: f32) -> PyRefMut<'_, Self> {
        slf.element.def.padding_bottom = Some(p);
        slf
    }

    /// Set padding left
    #[pyo3(text_signature = "($self, p)")]
    fn pl(mut slf: PyRefMut<'_, Self>, p: f32) -> PyRefMut<'_, Self> {
        slf.element.def.padding_left = Some(p);
        slf
    }

    /// Set padding x (left and right)
    #[pyo3(text_signature = "($self, p)")]
    fn px(mut slf: PyRefMut<'_, Self>, p: f32) -> PyRefMut<'_, Self> {
        slf.element.def.padding_left = Some(p);
        slf.element.def.padding_right = Some(p);
        slf
    }

    /// Set padding y (top and bottom)
    #[pyo3(text_signature = "($self, p)")]
    fn py(mut slf: PyRefMut<'_, Self>, p: f32) -> PyRefMut<'_, Self> {
        slf.element.def.padding_top = Some(p);
        slf.element.def.padding_bottom = Some(p);
        slf
    }

    /// Set margin on all sides in pixels. Returns self for chaining.
    #[pyo3(text_signature = "($self, m)")]
    fn margin(mut slf: PyRefMut<'_, Self>, m: f32) -> PyRefMut<'_, Self> {
        slf.element.def.margin = Some(m);
        slf
    }

    /// Alias for margin
    #[pyo3(text_signature = "($self, m)")]
    fn m(mut slf: PyRefMut<'_, Self>, m: f32) -> PyRefMut<'_, Self> {
        slf.element.def.margin = Some(m);
        slf
    }

    /// Set margin top
    #[pyo3(text_signature = "($self, m)")]
    fn mt(mut slf: PyRefMut<'_, Self>, m: f32) -> PyRefMut<'_, Self> {
        slf.element.def.margin_top = Some(m);
        slf
    }

    /// Set margin right
    #[pyo3(text_signature = "($self, m)")]
    fn mr(mut slf: PyRefMut<'_, Self>, m: f32) -> PyRefMut<'_, Self> {
        slf.element.def.margin_right = Some(m);
        slf
    }

    /// Set margin bottom
    #[pyo3(text_signature = "($self, m)")]
    fn mb(mut slf: PyRefMut<'_, Self>, m: f32) -> PyRefMut<'_, Self> {
        slf.element.def.margin_bottom = Some(m);
        slf
    }

    /// Set margin left
    #[pyo3(text_signature = "($self, m)")]
    fn ml(mut slf: PyRefMut<'_, Self>, m: f32) -> PyRefMut<'_, Self> {
        slf.element.def.margin_left = Some(m);
        slf
    }

    /// Set margin x (left and right)
    #[pyo3(text_signature = "($self, m)")]
    fn mx(mut slf: PyRefMut<'_, Self>, m: f32) -> PyRefMut<'_, Self> {
        slf.element.def.margin_left = Some(m);
        slf.element.def.margin_right = Some(m);
        slf
    }

    /// Set margin y (top and bottom)
    #[pyo3(text_signature = "($self, m)")]
    fn my(mut slf: PyRefMut<'_, Self>, m: f32) -> PyRefMut<'_, Self> {
        slf.element.def.margin_top = Some(m);
        slf.element.def.margin_bottom = Some(m);
        slf
    }

    /// Set background color. Accepts hex strings like "#ff0000" or CSS colors like "rgb(255,0,0)". Returns self for chaining.
    #[pyo3(text_signature = "($self, color)")]
    fn bg(mut slf: PyRefMut<'_, Self>, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.background_color = Some(color);
        slf
    }

    /// Set text color. Returns self for chaining.
    #[pyo3(text_signature = "($self, color)")]
    fn text_color(mut slf: PyRefMut<'_, Self>, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.text_color = Some(color);
        slf
    }

    /// Set border radius (rounded corners)
    #[pyo3(text_signature = "($self, radius)")]
    fn rounded(mut slf: PyRefMut<'_, Self>, radius: f32) -> PyRefMut<'_, Self> {
        slf.element.def.border_radius = Some(radius);
        slf
    }

    /// Set border radius for top-left corner
    #[pyo3(text_signature = "($self, radius)")]
    fn rounded_tl(mut slf: PyRefMut<'_, Self>, radius: f32) -> PyRefMut<'_, Self> {
        slf.element.def.border_radius_top_left = Some(radius);
        slf
    }

    /// Set border radius for top-right corner
    #[pyo3(text_signature = "($self, radius)")]
    fn rounded_tr(mut slf: PyRefMut<'_, Self>, radius: f32) -> PyRefMut<'_, Self> {
        slf.element.def.border_radius_top_right = Some(radius);
        slf
    }

    /// Set border radius for bottom-right corner
    #[pyo3(text_signature = "($self, radius)")]
    fn rounded_br(mut slf: PyRefMut<'_, Self>, radius: f32) -> PyRefMut<'_, Self> {
        slf.element.def.border_radius_bottom_right = Some(radius);
        slf
    }

    /// Set border radius for bottom-left corner
    #[pyo3(text_signature = "($self, radius)")]
    fn rounded_bl(mut slf: PyRefMut<'_, Self>, radius: f32) -> PyRefMut<'_, Self> {
        slf.element.def.border_radius_bottom_left = Some(radius);
        slf
    }

    /// Set border with width and color. Returns self for chaining.
    #[pyo3(text_signature = "($self, width, color)")]
    fn border(mut slf: PyRefMut<'_, Self>, width: f32, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.border_width = Some(width);
        slf.element.def.border_color = Some(color);
        slf
    }

    /// Set border on top side
    #[pyo3(text_signature = "($self, width, color)")]
    fn border_top(mut slf: PyRefMut<'_, Self>, width: f32, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.border_width_top = Some(width);
        slf.element.def.border_color_top = Some(color);
        slf
    }

    /// Set border on right side
    #[pyo3(text_signature = "($self, width, color)")]
    fn border_right(mut slf: PyRefMut<'_, Self>, width: f32, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.border_width_right = Some(width);
        slf.element.def.border_color_right = Some(color);
        slf
    }

    /// Set border on bottom side
    #[pyo3(text_signature = "($self, width, color)")]
    fn border_bottom(mut slf: PyRefMut<'_, Self>, width: f32, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.border_width_bottom = Some(width);
        slf.element.def.border_color_bottom = Some(color);
        slf
    }

    /// Set border on left side
    #[pyo3(text_signature = "($self, width, color)")]
    fn border_left(mut slf: PyRefMut<'_, Self>, width: f32, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.border_width_left = Some(width);
        slf.element.def.border_color_left = Some(color);
        slf
    }

    /// Short alias for border (1px solid color)
    #[pyo3(text_signature = "($self, color)")]
    fn b(mut slf: PyRefMut<'_, Self>, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.border_width = Some(1.0);
        slf.element.def.border_color = Some(color);
        slf
    }

    /// Set overflow to hidden
    #[pyo3(text_signature = "($self)")]
    fn overflow_hidden(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.overflow = Some("hidden".to_string());
        slf
    }

    /// Set overflow
    #[pyo3(text_signature = "($self, value)")]
    fn overflow(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.overflow = Some(value);
        slf
    }

    /// Set text alignment
    #[pyo3(text_signature = "($self, align)")]
    fn text_align(mut slf: PyRefMut<'_, Self>, align: String) -> PyRefMut<'_, Self> {
        slf.element.def.text_align = Some(align);
        slf
    }

    /// Center text
    #[pyo3(text_signature = "($self)")]
    fn text_center(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.text_align = Some("center".to_string());
        slf
    }

    /// Set word wrap
    #[pyo3(text_signature = "($self, value)")]
    fn word_wrap(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.word_wrap = Some(value);
        slf
    }

    /// Set CSS transition (raw value for advanced use)
    #[pyo3(text_signature = "($self, value)")]
    fn transition(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.transition = Some(value);
        slf
    }

    /// Transition all properties with given duration in seconds
    #[pyo3(text_signature = "($self, seconds)")]
    fn transition_all(mut slf: PyRefMut<'_, Self>, seconds: f32) -> PyRefMut<'_, Self> {
        slf.element.def.transition = Some(format!("all {}s ease", seconds));
        slf
    }

    /// Transition colors (background, text, border) with given duration
    #[pyo3(text_signature = "($self, seconds)")]
    fn transition_colors(mut slf: PyRefMut<'_, Self>, seconds: f32) -> PyRefMut<'_, Self> {
        slf.element.def.transition = Some(format!(
            "background-color {}s ease, color {}s ease, border-color {}s ease",
            seconds, seconds, seconds
        ));
        slf
    }

    /// Transition transform (scale, etc.) with given duration
    #[pyo3(text_signature = "($self, seconds)")]
    fn transition_transform(mut slf: PyRefMut<'_, Self>, seconds: f32) -> PyRefMut<'_, Self> {
        slf.element.def.transition = Some(format!("transform {}s ease", seconds));
        slf
    }

    /// Set opacity (0.0 to 1.0)
    #[pyo3(text_signature = "($self, value)")]
    fn opacity(mut slf: PyRefMut<'_, Self>, value: f32) -> PyRefMut<'_, Self> {
        slf.element.def.opacity = Some(value);
        slf
    }

    /// Set cursor style (e.g., "pointer", "grab", "not-allowed")
    #[pyo3(text_signature = "($self, value)")]
    fn cursor(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.cursor = Some(value);
        slf
    }

    /// Append raw CSS styles to the element. Multiple calls will append.
    #[pyo3(text_signature = "($self, css)")]
    fn style(mut slf: PyRefMut<'_, Self>, css: String) -> PyRefMut<'_, Self> {
        match slf.element.def.style.as_mut() {
            Some(existing) => {
                // Ensure a semicolon separator between appended blocks
                if !existing.ends_with(';') {
                    existing.push(';');
                }
                existing.push_str(&css);
            }
            None => {
                slf.element.def.style = Some(css);
            }
        }
        slf
    }

    // Hover styles

    /// Set background color on hover
    #[pyo3(text_signature = "($self, color)")]
    fn hover_bg(mut slf: PyRefMut<'_, Self>, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.hover_bg = Some(color);
        slf
    }

    /// Set text color on hover
    #[pyo3(text_signature = "($self, color)")]
    fn hover_text_color(mut slf: PyRefMut<'_, Self>, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.hover_text_color = Some(color);
        slf
    }

    /// Set border color on hover
    #[pyo3(text_signature = "($self, color)")]
    fn hover_border_color(mut slf: PyRefMut<'_, Self>, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.hover_border_color = Some(color);
        slf
    }

    /// Set opacity on hover (0.0 to 1.0)
    #[pyo3(text_signature = "($self, value)")]
    fn hover_opacity(mut slf: PyRefMut<'_, Self>, value: f32) -> PyRefMut<'_, Self> {
        slf.element.def.hover_opacity = Some(value);
        slf
    }

    /// Set scale on hover (e.g., 1.05 for 5% larger)
    #[pyo3(text_signature = "($self, value)")]
    fn hover_scale(mut slf: PyRefMut<'_, Self>, value: f32) -> PyRefMut<'_, Self> {
        slf.element.def.hover_scale = Some(value);
        slf
    }

    // Focus styles

    /// Set background color on focus
    #[pyo3(text_signature = "($self, color)")]
    fn focus_bg(mut slf: PyRefMut<'_, Self>, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.focus_bg = Some(color);
        slf
    }

    /// Set text color on focus
    #[pyo3(text_signature = "($self, color)")]
    fn focus_text_color(mut slf: PyRefMut<'_, Self>, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.focus_text_color = Some(color);
        slf
    }

    /// Set border color on focus
    #[pyo3(text_signature = "($self, color)")]
    fn focus_border_color(mut slf: PyRefMut<'_, Self>, color: String) -> PyRefMut<'_, Self> {
        slf.element.def.focus_border_color = Some(color);
        slf
    }

    // Image properties

    /// Set alt text for images
    #[pyo3(text_signature = "($self, text)")]
    fn alt(mut slf: PyRefMut<'_, Self>, text: String) -> PyRefMut<'_, Self> {
        slf.element.def.alt = Some(text);
        slf
    }

    /// Set object-fit for images (cover, contain, fill, none, scale-down)
    #[pyo3(text_signature = "($self, value)")]
    fn object_fit(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.object_fit = Some(value);
        slf
    }

    /// Set position
    #[pyo3(text_signature = "($self, value)")]
    fn position(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.position = Some(value);
        slf
    }

    /// Set position to absolute
    #[pyo3(text_signature = "($self)")]
    fn absolute(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.position = Some("absolute".to_string());
        slf
    }

    /// Set position to relative
    #[pyo3(text_signature = "($self)")]
    fn relative(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.element.def.position = Some("relative".to_string());
        slf
    }

    /// Set top position
    #[pyo3(text_signature = "($self, value)")]
    fn top(mut slf: PyRefMut<'_, Self>, value: f32) -> PyRefMut<'_, Self> {
        slf.element.def.top = Some(value);
        slf
    }

    /// Set right position
    #[pyo3(text_signature = "($self, value)")]
    fn right(mut slf: PyRefMut<'_, Self>, value: f32) -> PyRefMut<'_, Self> {
        slf.element.def.right = Some(value);
        slf
    }

    /// Set bottom position
    #[pyo3(text_signature = "($self, value)")]
    fn bottom(mut slf: PyRefMut<'_, Self>, value: f32) -> PyRefMut<'_, Self> {
        slf.element.def.bottom = Some(value);
        slf
    }

    /// Set left position
    #[pyo3(text_signature = "($self, value)")]
    fn left(mut slf: PyRefMut<'_, Self>, value: f32) -> PyRefMut<'_, Self> {
        slf.element.def.left = Some(value);
        slf
    }

    /// Set font size
    #[pyo3(text_signature = "($self, size)")]
    fn text_size(mut slf: PyRefMut<'_, Self>, size: f32) -> PyRefMut<'_, Self> {
        slf.element.def.font_size = Some(size);
        slf
    }

    /// Set font weight ("normal", "bold", "100"-"900")
    #[pyo3(text_signature = "($self, weight)")]
    fn text_weight(mut slf: PyRefMut<'_, Self>, weight: String) -> PyRefMut<'_, Self> {
        slf.element.def.font_weight = Some(weight);
        slf
    }

    /// Add a child element
    #[pyo3(text_signature = "($self, child)")]
    fn child(&mut self, child: &Element) -> Self {
        self.element.def.children.push(child.def.clone());
        self.element.callback_ids.extend(child.callback_ids.clone());
        self.clone()
    }

    /// Add a child from a builder
    #[pyo3(text_signature = "($self, child)")]
    fn child_builder(&mut self, child: &ElementBuilder) -> Self {
        self.element.def.children.push(child.element.def.clone());
        self.element.callback_ids.extend(child.element.callback_ids.clone());
        self.clone()
    }

    /// Add text child (convenience)
    #[pyo3(text_signature = "($self, text)")]
    fn child_text(mut slf: PyRefMut<'_, Self>, text: String) -> PyRefMut<'_, Self> {
        let mut text_def = ElementDef::default();
        text_def.element_type = "text".to_string();
        text_def.text_content = Some(text);
        slf.element.def.children.push(text_def);
        slf
    }

    /// Register a callback function to run when the element is clicked. Returns self for chaining.
    #[pyo3(text_signature = "($self, callback)")]
    fn on_click(&mut self, callback: Py<PyAny>) -> Self {
        let callback_id = uuid();
        self.element.def.on_click = Some(callback_id.clone());
        self.element.callback_ids.push(callback_id.clone());
        store_callback(callback_id, callback);
        self.clone()
    }

    /// Set input value
    #[pyo3(text_signature = "($self, val)")]
    fn value(mut slf: PyRefMut<'_, Self>, val: String) -> PyRefMut<'_, Self> {
        slf.element.def.value = Some(val);
        slf
    }

    /// Set placeholder text
    #[pyo3(text_signature = "($self, text)")]
    fn placeholder(mut slf: PyRefMut<'_, Self>, text: String) -> PyRefMut<'_, Self> {
        slf.element.def.placeholder = Some(text);
        slf
    }

    /// Set checked state for checkbox/radio
    #[pyo3(text_signature = "($self, checked)")]
    fn checked(mut slf: PyRefMut<'_, Self>, checked: bool) -> PyRefMut<'_, Self> {
        slf.element.def.checked = Some(checked);
        slf
    }

    /// Set radio button group name
    #[pyo3(text_signature = "($self, name)")]
    fn group(mut slf: PyRefMut<'_, Self>, name: String) -> PyRefMut<'_, Self> {
        slf.element.def.radio_group = Some(name);
        slf
    }

    /// Add an option to a select element
    #[pyo3(text_signature = "($self, value, label)")]
    fn option(mut slf: PyRefMut<'_, Self>, value: String, label: String) -> PyRefMut<'_, Self> {
        slf.element.def.options.push(SelectOption { value, label });
        slf
    }

    /// Set the selected option value for a select element
    #[pyo3(text_signature = "($self, value)")]
    fn selected(mut slf: PyRefMut<'_, Self>, value: String) -> PyRefMut<'_, Self> {
        slf.element.def.selected = Some(value);
        slf
    }

    /// Register a callback for checkbox/radio/select change events. Callback receives the new value.
    #[pyo3(text_signature = "($self, callback)")]
    fn on_change(&mut self, callback: Py<PyAny>) -> Self {
        let callback_id = uuid();
        self.element.def.on_change = Some(callback_id.clone());
        self.element.callback_ids.push(callback_id.clone());
        store_callback(callback_id, callback);
        self.clone()
    }

    /// Register a callback function to run when the input value changes. Callback receives the new value as a string argument. Returns self for chaining.
    #[pyo3(text_signature = "($self, callback)")]
    fn on_input(&mut self, callback: Py<PyAny>) -> Self {
        let callback_id = uuid();
        self.element.def.on_input = Some(callback_id.clone());
        self.element.callback_ids.push(callback_id.clone());
        store_callback(callback_id, callback);
        self.clone()
    }

    /// Register a callback for when the mouse enters the element.
    #[pyo3(text_signature = "($self, callback)")]
    fn on_mouse_enter(&mut self, callback: Py<PyAny>) -> Self {
        let callback_id = uuid();
        self.element.def.on_mouse_enter = Some(callback_id.clone());
        self.element.callback_ids.push(callback_id.clone());
        store_callback(callback_id, callback);
        self.clone()
    }

    /// Register a callback for when the mouse leaves the element.
    #[pyo3(text_signature = "($self, callback)")]
    fn on_mouse_leave(&mut self, callback: Py<PyAny>) -> Self {
        let callback_id = uuid();
        self.element.def.on_mouse_leave = Some(callback_id.clone());
        self.element.callback_ids.push(callback_id.clone());
        store_callback(callback_id, callback);
        self.clone()
    }

    /// Register a callback for when the mouse button is pressed on the element.
    #[pyo3(text_signature = "($self, callback)")]
    fn on_mouse_down(&mut self, callback: Py<PyAny>) -> Self {
        let callback_id = uuid();
        self.element.def.on_mouse_down = Some(callback_id.clone());
        self.element.callback_ids.push(callback_id.clone());
        store_callback(callback_id, callback);
        self.clone()
    }

    /// Register a callback for when the mouse button is released on the element.
    #[pyo3(text_signature = "($self, callback)")]
    fn on_mouse_up(&mut self, callback: Py<PyAny>) -> Self {
        let callback_id = uuid();
        self.element.def.on_mouse_up = Some(callback_id.clone());
        self.element.callback_ids.push(callback_id.clone());
        store_callback(callback_id, callback);
        self.clone()
    }

    /// Build and return the final Element. Call this after configuring all properties.
    #[pyo3(text_signature = "($self)")]
    fn build(&self) -> Element {
        self.element.clone()
    }

    fn __repr__(&self) -> String {
        format!("ElementBuilder({})", self.element.__repr__())
    }
}

// Convenience functions at module level for quick element creation.
/// Create a div element (generic container). Shorthand for ElementBuilder.div().
#[pyfunction]
#[pyo3(text_signature = "()")]
pub fn div() -> ElementBuilder {
    ElementBuilder::div()
}

/// Create a text element. Shorthand for ElementBuilder.text(content).
#[pyfunction]
#[pyo3(text_signature = "(content)")]
pub fn text(content: String) -> ElementBuilder {
    ElementBuilder::text(content)
}

/// Create a button element. Shorthand for ElementBuilder.button(label).
#[pyfunction]
#[pyo3(text_signature = "(label)")]
pub fn button(label: String) -> ElementBuilder {
    ElementBuilder::button(label)
}

/// Create an input field element. Shorthand for ElementBuilder.input().
#[pyfunction]
#[pyo3(text_signature = "()")]
pub fn input() -> ElementBuilder {
    ElementBuilder::input()
}

/// Create an image element. Shorthand for ElementBuilder.image(src).
#[pyfunction]
#[pyo3(text_signature = "(src)")]
pub fn image(src: String) -> ElementBuilder {
    ElementBuilder::image(src)
}

/// Create a checkbox element. Shorthand for ElementBuilder.checkbox(label).
#[pyfunction]
#[pyo3(signature = (label = None), text_signature = "(label=None)")]
pub fn checkbox(label: Option<String>) -> ElementBuilder {
    ElementBuilder::checkbox(label)
}

/// Create a radio button element. Shorthand for ElementBuilder.radio(label).
#[pyfunction]
#[pyo3(signature = (label = None), text_signature = "(label=None)")]
pub fn radio(label: Option<String>) -> ElementBuilder {
    ElementBuilder::radio(label)
}

/// Create a select dropdown element. Shorthand for ElementBuilder.select().
#[pyfunction]
#[pyo3(text_signature = "()")]
pub fn select() -> ElementBuilder {
    ElementBuilder::select()
}
