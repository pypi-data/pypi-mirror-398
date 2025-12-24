use crate::elements::Element;
use crate::renderer::render_to_html;
use parking_lot::Mutex;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::Arc;
use wry::WebViewBuilder;
use tao::event_loop::EventLoopProxy;

#[cfg(target_os = "linux")]
use {
    gtk::prelude::*,
    gtk::{Box as GtkBox, Orientation},
    wry::WebViewBuilderExtUnix,
};

#[cfg(not(target_os = "linux"))]
use {
    tao::event::{Event, WindowEvent},
    tao::event_loop::{ControlFlow, EventLoop, EventLoopBuilder},
    tao::window::WindowBuilder,
};

/// Custom events we can send to the event loop
#[derive(Debug, Clone)]
pub enum UserEvent {
    UpdateRoot(String),            // HTML content for full root replacement
    UpdateElement(String, String), // (element_id, html) for partial update
    SetTitle(String),
    Close,
}

/// Shared state between Python and the webview
struct WebViewState {
    callbacks: HashMap<String, Py<PyAny>>,
    pending_html: Option<String>,
    pending_title: Option<String>,
    pending_element_updates: Vec<(String, String)>, // (id, html) pairs
    should_close: bool,
}

impl WebViewState {
    fn new() -> Self {
        WebViewState {
            callbacks: HashMap::new(),
            pending_html: None,
            pending_title: None,
            pending_element_updates: Vec::new(),
            should_close: false,
        }
    }
}

/// Main window class exposed to Python
#[pyclass]
pub struct UiWindow {
    title: String,
    width: u32,
    height: u32,
    event_proxy: Arc<Mutex<Option<EventLoopProxy<UserEvent>>>>,
    state: Arc<Mutex<WebViewState>>,
    is_running: Arc<Mutex<bool>>,
    background_color: (u8, u8, u8, u8),
}

#[pymethods]
impl UiWindow {
    /// Create a new window.
    ///
    /// Args:
    ///     title: Window title. Defaults to "Python App".
    ///     width: Window width in pixels. Defaults to 800.
    ///     height: Window height in pixels. Defaults to 600.
    ///     background_color: Background color as hex string (e.g., "#1a1a1a"). Defaults to dark gray.
    #[new]
    #[pyo3(signature = (title = None, width = None, height = None, background_color = None), text_signature = "(title=None, width=None, height=None, background_color=None)")]
    fn new(
        title: Option<String>,
        width: Option<u32>,
        height: Option<u32>,
        background_color: Option<String>,
    ) -> Self {
        let bg = background_color
            .and_then(|c| parse_hex_color(&c))
            .unwrap_or((26, 26, 26, 255)); // Default: #1a1a1a

        UiWindow {
            title: title.unwrap_or_else(|| "Python App".to_string()),
            width: width.unwrap_or(800),
            height: height.unwrap_or(600),
            event_proxy: Arc::new(Mutex::new(None)),
            state: Arc::new(Mutex::new(WebViewState::new())),
            is_running: Arc::new(Mutex::new(false)),
            background_color: bg,
        }
    }

    /// Set the root element and update the webview.
    ///
    /// This updates what's displayed in the window. Can be called before or after run().
    ///
    /// Args:
    ///     element: The root Element to display.
    #[pyo3(text_signature = "(self, element)")]
    fn set_root(&self, element: &Element) -> PyResult<()> {
        // Register callbacks from element
        let html = {
            let mut state = self.state.lock();
            for (id, callback) in element.collect_callbacks() {
                state.callbacks.insert(id, callback);
            }

            // Render element to HTML
            let html = render_to_html(&element.def);

            // Store as pending if not running yet
            state.pending_html = Some(html.clone());
            html
        };

        // Send update to webview if already running
        if let Some(proxy) = self.event_proxy.lock().as_ref() {
            let _ = proxy.send_event(UserEvent::UpdateRoot(html));
        }

        Ok(())
    }

    /// Change the window title.
    ///
    /// Args:
    ///     title: The new title to display in the window header.
    #[pyo3(text_signature = "(self, title)")]
    fn set_title(&self, title: String) -> PyResult<()> {
        // Store in state for polling (used on Linux)
        self.state.lock().pending_title = Some(title.clone());

        // Also send via event proxy if available (used on other platforms)
        if let Some(proxy) = self.event_proxy.lock().as_ref() {
            let _ = proxy.send_event(UserEvent::SetTitle(title));
        }
        Ok(())
    }

    /// Update a single element by its ID without replacing the entire root.
    ///
    /// This is more efficient than set_root() when only a small part of the UI changes.
    /// The element must have an id set via the id() builder method.
    ///
    /// Args:
    ///     element_id: The ID of the element to update (set via id()).
    ///     element: The new Element to replace the existing one.
    #[pyo3(text_signature = "(self, element_id, element)")]
    fn update_element(&self, element_id: String, element: &Element) -> PyResult<()> {
        // Register callbacks from element
        let html = {
            let mut state = self.state.lock();
            for (id, callback) in element.collect_callbacks() {
                state.callbacks.insert(id, callback);
            }

            // Render element to HTML
            let html = render_to_html(&element.def);

            // Store as pending for Linux polling
            state.pending_element_updates.push((element_id.clone(), html.clone()));
            html
        };

        // Send update to webview if already running
        if let Some(proxy) = self.event_proxy.lock().as_ref() {
            let _ = proxy.send_event(UserEvent::UpdateElement(element_id, html));
        }

        Ok(())
    }

    /// Show the window and start the event loop.
    ///
    /// This is blocking and will run until the window is closed. Call set_root() before
    /// or after this to update what's displayed.
    #[pyo3(text_signature = "(self)")]
    fn run(&self, py: Python) -> PyResult<()> {
        let title = self.title.clone();
        let width = self.width;
        let height = self.height;
        let state = self.state.clone();
        let event_proxy_holder = self.event_proxy.clone();
        let is_running = self.is_running.clone();
        let background_color = self.background_color;

        // Release GIL while running the event loop
        #[allow(deprecated)]
        py.allow_threads(|| {
            run_event_loop(title, width, height, state, event_proxy_holder, is_running, background_color)
        })
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Close the window and stop the event loop.
    #[pyo3(text_signature = "(self)")]
    fn close(&self) -> PyResult<()> {
        // Set close flag in state for polling (used on Linux)
        self.state.lock().should_close = true;

        // Also send via event proxy if available (used on other platforms)
        if let Some(proxy) = self.event_proxy.lock().as_ref() {
            let _ = proxy.send_event(UserEvent::Close);
        }
        Ok(())
    }

    /// Check if the window is currently running.
    ///
    /// Returns:
    ///     True if the event loop is active, False otherwise.
    #[pyo3(text_signature = "(self)")]
    fn is_running(&self) -> bool {
        *self.is_running.lock()
    }

    fn __repr__(&self) -> String {
        format!(
            "UiWindow(title='{}', size={}x{})",
            self.title, self.width, self.height
        )
    }
}

#[cfg(target_os = "linux")]
fn run_event_loop(
    title: String,
    width: u32,
    height: u32,
    state: Arc<Mutex<WebViewState>>,
    event_proxy_holder: Arc<Mutex<Option<EventLoopProxy<UserEvent>>>>,
    is_running: Arc<Mutex<bool>>,
    background_color: (u8, u8, u8, u8),
) -> Result<(), String> {
    use gtk::glib;
    use std::cell::RefCell;
    use std::rc::Rc;
    use std::sync::mpsc;

    gtk::init().map_err(|e| format!("Failed to initialize GTK: {:?}", e))?;

    // Create a channel for internal events
    let (event_tx, event_rx) = mpsc::channel::<UserEvent>();
    let event_rx = Rc::new(RefCell::new(event_rx));

    let state_clone = state.clone();

    // Create GTK window
    let window = gtk::Window::new(gtk::WindowType::Toplevel);
    window.set_title(&title);
    window.set_default_size(width as i32, height as i32);

    // Create a box to hold the webview
    let gtk_box = GtkBox::new(Orientation::Vertical, 0);
    gtk_box.set_vexpand(true);
    gtk_box.set_hexpand(true);

    // Get initial HTML
    let initial_content = {
        let state = state_clone.lock();
        state.pending_html.clone()
    };

    let initial_html = get_initial_html(initial_content.as_deref(), background_color);

    // Create IPC handler for callbacks
    let state_for_ipc = state_clone.clone();
    let ipc_handler = move |request: wry::http::Request<String>| {
        let body = request.body();
        if let Ok(event) = serde_json::from_str::<IpcEvent>(body) {
            // Handle click and mouse events (no arguments)
            if matches!(event.event_type.as_str(), "click" | "mouse_enter" | "mouse_leave" | "mouse_down" | "mouse_up") {
                if let Some(ref callback_id) = event.callback_id {
                    let state_for_cb = state_for_ipc.clone();
                    let callback_id = callback_id.clone();
                    #[allow(deprecated)]
                    Python::with_gil(|py| {
                        let callback = {
                            let state = state_for_cb.lock();
                            state.callbacks.get(&callback_id).map(|cb| cb.clone_ref(py))
                        };

                        if let Some(callback) = callback {
                            std::thread::spawn(move || {
                                #[allow(deprecated)]
                                Python::with_gil(|py| {
                                    if let Err(e) = callback.call0(py) {
                                        eprintln!("Callback error: {:?}", e);
                                    }
                                });
                            });
                        }
                    });
                }
            }

            if event.event_type == "input" || event.event_type == "change" {
                if let (Some(callback_id), Some(value)) = (&event.callback_id, event.value) {
                    let state_for_cb = state_for_ipc.clone();
                    let callback_id = callback_id.clone();
                    #[allow(deprecated)]
                    Python::with_gil(|py| {
                        let callback = {
                            let state = state_for_cb.lock();
                            state.callbacks.get(&callback_id).map(|cb| cb.clone_ref(py))
                        };

                        if let Some(callback) = callback {
                            std::thread::spawn(move || {
                                #[allow(deprecated)]
                                Python::with_gil(|py| {
                                    if let Err(e) = callback.call1(py, (value,)) {
                                        eprintln!("Input/change callback error: {:?}", e);
                                    }
                                });
                            });
                        }
                    });
                }
            }
        }
    };

    // Build webview with GTK
    let webview = WebViewBuilder::new()
        .with_html(initial_html)
        .with_ipc_handler(ipc_handler)
        .with_background_color(background_color)
        .build_gtk(&gtk_box)
        .map_err(|e| format!("Failed to build webview: {}", e))?;

    let webview = Rc::new(webview);

    window.add(&gtk_box);

    // Handle window close
    let is_running_for_close = is_running.clone();
    window.connect_delete_event(move |_, _| {
        *is_running_for_close.lock() = false;
        gtk::main_quit();
        glib::Propagation::Stop
    });

    window.show_all();

    *is_running.lock() = true;

    // Set up a polling loop to check for events from Python
    let webview_for_poll = webview.clone();
    let window_for_poll = window.clone();
    let is_running_for_poll = is_running.clone();
    glib::timeout_add_local(std::time::Duration::from_millis(16), move || {
        // Check for events
        while let Ok(event) = event_rx.borrow().try_recv() {
            match event {
                UserEvent::UpdateRoot(html) => {
                    let js = format!(
                        "document.getElementById('root').innerHTML = {};",
                        serde_json::to_string(&html).unwrap()
                    );
                    let _ = webview_for_poll.evaluate_script(&js);
                }
                UserEvent::UpdateElement(id, html) => {
                    let js = format!(
                        "updateElementById({}, {});",
                        serde_json::to_string(&id).unwrap(),
                        serde_json::to_string(&html).unwrap()
                    );
                    let _ = webview_for_poll.evaluate_script(&js);
                }
                UserEvent::SetTitle(title) => {
                    window_for_poll.set_title(&title);
                }
                UserEvent::Close => {
                    *is_running_for_poll.lock() = false;
                    gtk::main_quit();
                    return glib::ControlFlow::Break;
                }
            }
        }
        glib::ControlFlow::Continue
    });

    // Handle Ctrl+C (SIGINT) to close the window gracefully
    let is_running_for_sigint = is_running.clone();
    let window_for_sigint = window.clone();
    glib::unix_signal_add_local(libc::SIGINT, move || {
        *is_running_for_sigint.lock() = false;
        window_for_sigint.close();
        gtk::main_quit();
        glib::ControlFlow::Break
    });

    // Poll the state for pending changes from Python
    // This is needed because EventLoopProxy doesn't work with GTK
    let state_for_poll = state.clone();
    glib::timeout_add_local(std::time::Duration::from_millis(50), move || {
        let mut state = state_for_poll.lock();

        // Check for pending HTML update
        if let Some(html) = state.pending_html.take() {
            let _ = event_tx.send(UserEvent::UpdateRoot(html));
        }

        // Check for pending element updates
        for (id, html) in state.pending_element_updates.drain(..) {
            let _ = event_tx.send(UserEvent::UpdateElement(id, html));
        }

        // Check for pending title update
        if let Some(title) = state.pending_title.take() {
            let _ = event_tx.send(UserEvent::SetTitle(title));
        }

        // Check for close request
        if state.should_close {
            state.should_close = false;
            let _ = event_tx.send(UserEvent::Close);
        }

        glib::ControlFlow::Continue
    });

    gtk::main();
    *is_running.lock() = false;

    // Clear the event proxy
    *event_proxy_holder.lock() = None;

    Ok(())
}

#[cfg(not(target_os = "linux"))]
fn run_event_loop(
    title: String,
    width: u32,
    height: u32,
    state: Arc<Mutex<WebViewState>>,
    event_proxy_holder: Arc<Mutex<Option<EventLoopProxy<UserEvent>>>>,
    is_running: Arc<Mutex<bool>>,
    background_color: (u8, u8, u8, u8),
) -> Result<(), String> {
    // NVIDIA + Wayland workaround (not needed when using GTK backend)
    #[cfg(target_os = "linux")]
    {
        if std::path::Path::new("/dev/dri").exists()
            && std::env::var("WAYLAND_DISPLAY").is_ok()
            && std::env::var("XDG_SESSION_TYPE").unwrap_or_default() == "wayland"
        {
            unsafe {
                std::env::set_var("__NV_DISABLE_EXPLICIT_SYNC", "1");
            }
        }
    }

    let event_loop: EventLoop<UserEvent> = EventLoopBuilder::with_user_event().build();

    // Store the proxy so Python can send events
    *event_proxy_holder.lock() = Some(event_loop.create_proxy());
    *is_running.lock() = true;

    let window = WindowBuilder::new()
        .with_title(&title)
        .with_inner_size(tao::dpi::LogicalSize::new(width, height))
        .build(&event_loop)
        .map_err(|e| e.to_string())?;

    // Get pending HTML or use default
    let initial_content = {
        let state = state.lock();
        state.pending_html.clone()
    };

    let initial_html = get_initial_html(initial_content.as_deref(), background_color);

    // Create IPC handler for callbacks
    let state_clone = state.clone();
    let _proxy_for_callbacks = event_loop.create_proxy();

    let ipc_handler = move |request: wry::http::Request<String>| {
        let body = request.body();
        if let Ok(event) = serde_json::from_str::<IpcEvent>(body) {
            // Handle click and mouse events (no arguments)
            if matches!(event.event_type.as_str(), "click" | "mouse_enter" | "mouse_leave" | "mouse_down" | "mouse_up") {
                if let Some(ref callback_id) = event.callback_id {
                    let state_for_cb = state_clone.clone();
                    let callback_id = callback_id.clone();
                    #[allow(deprecated)]
                    Python::with_gil(|py| {
                        let callback = {
                            let state = state_for_cb.lock();
                            state.callbacks.get(&callback_id).map(|cb| cb.clone_ref(py))
                        };

                        if let Some(callback) = callback {
                            std::thread::spawn(move || {
                                #[allow(deprecated)]
                                Python::with_gil(|py| {
                                    if let Err(e) = callback.call0(py) {
                                        eprintln!("Callback error: {:?}", e);
                                    }
                                });
                            });
                        }
                    });
                }
            }

            if event.event_type == "input" || event.event_type == "change" {
                if let (Some(callback_id), Some(value)) = (&event.callback_id, event.value) {
                    let state_for_cb = state_clone.clone();
                    let callback_id = callback_id.clone();
                    #[allow(deprecated)]
                    Python::with_gil(|py| {
                        let callback = {
                            let state = state_for_cb.lock();
                            state.callbacks.get(&callback_id).map(|cb| cb.clone_ref(py))
                        };

                        if let Some(callback) = callback {
                            std::thread::spawn(move || {
                                #[allow(deprecated)]
                                Python::with_gil(|py| {
                                    if let Err(e) = callback.call1(py, (value,)) {
                                        eprintln!("Input/change callback error: {:?}", e);
                                    }
                                });
                            });
                        }
                    });
                }
            }
        }
    };

    let webview = WebViewBuilder::new()
        .with_html(initial_html)
        .with_ipc_handler(ipc_handler)
        .with_background_color(background_color)
        .build(&window)
        .map_err(|e| e.to_string())?;

    {
        let state = state.lock();
        if let Some(ref html) = state.pending_html {
            let js = format!("document.getElementById('root').innerHTML = `{}`;", html.replace('`', "\\`"));
            let _ = webview.evaluate_script(&js);
        }
    }

    event_loop.run(move |event, _, control_flow| {
        *control_flow = ControlFlow::Wait;

        match event {
            Event::WindowEvent {
                event: WindowEvent::CloseRequested,
                ..
            } => {
                *is_running.lock() = false;
                *control_flow = ControlFlow::Exit;
            }

            Event::UserEvent(user_event) => match user_event {
                UserEvent::UpdateRoot(html) => {
                    let js = format!(
                        "document.getElementById('root').innerHTML = {};",
                        serde_json::to_string(&html).unwrap()
                    );
                    let _ = webview.evaluate_script(&js);
                }
                UserEvent::UpdateElement(id, html) => {
                    let js = format!(
                        "updateElementById({}, {});",
                        serde_json::to_string(&id).unwrap(),
                        serde_json::to_string(&html).unwrap()
                    );
                    let _ = webview.evaluate_script(&js);
                }
                UserEvent::SetTitle(title) => {
                    window.set_title(&title);
                }
                UserEvent::Close => {
                    *is_running.lock() = false;
                    *control_flow = ControlFlow::Exit;
                }
            },

            _ => {}
        }
    });

    #[allow(unreachable_code)]
    {
        *event_proxy_holder.lock() = None;
        Ok(())
    }
}

#[derive(serde::Deserialize)]
struct IpcEvent {
    event_type: String,
    callback_id: Option<String>,
    value: Option<String>,
}

/// Parse a hex color string like "#1a1a1a" or "#1a1a1aff" to RGBA tuple
fn parse_hex_color(hex: &str) -> Option<(u8, u8, u8, u8)> {
    let hex = hex.trim_start_matches('#');
    match hex.len() {
        6 => {
            let r = u8::from_str_radix(&hex[0..2], 16).ok()?;
            let g = u8::from_str_radix(&hex[2..4], 16).ok()?;
            let b = u8::from_str_radix(&hex[4..6], 16).ok()?;
            Some((r, g, b, 255))
        }
        8 => {
            let r = u8::from_str_radix(&hex[0..2], 16).ok()?;
            let g = u8::from_str_radix(&hex[2..4], 16).ok()?;
            let b = u8::from_str_radix(&hex[4..6], 16).ok()?;
            let a = u8::from_str_radix(&hex[6..8], 16).ok()?;
            Some((r, g, b, a))
        }
        _ => None,
    }
}

fn get_initial_html(content: Option<&str>, background_color: (u8, u8, u8, u8)) -> String {
    let root_content = content.unwrap_or(r#"<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#666;">Loading...</div>"#);
    let (r, g, b, _a) = background_color;

    format!(
        r#"<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: rgb({}, {}, {});
            color: #ffffff;
            min-height: 100vh;
        }}
        #root {{
            width: 100%;
            height: 100vh;
        }}
        .size-full {{
            width: 100%;
            height: 100%;
        }}
        .flex-row {{ display: flex; flex-direction: row; }}
        .flex-col {{ display: flex; flex-direction: column; }}
        .items-center {{ align-items: center; }}
        .items-start {{ align-items: flex-start; }}
        .items-end {{ align-items: flex-end; }}
        .justify-center {{ justify-content: center; }}
        .justify-between {{ justify-content: space-between; }}
        .justify-start {{ justify-content: flex-start; }}
        .justify-end {{ justify-content: flex-end; }}
    </style>
</head>
<body>
    <div id="root">{}</div>
    <script>
        function handleClick(callbackId) {{
            window.ipc.postMessage(JSON.stringify({{
                event_type: 'click',
                callback_id: callbackId
            }}));
        }}

        function handleInput(callbackId, value) {{
            window.ipc.postMessage(JSON.stringify({{
                event_type: 'input',
                callback_id: callbackId,
                value: value
            }}));
        }}

        function handleMouseEvent(callbackId, eventType) {{
            window.ipc.postMessage(JSON.stringify({{
                event_type: eventType,
                callback_id: callbackId
            }}));
        }}

        function updateElementById(elementId, html) {{
            var el = document.getElementById(elementId);
            if (el) {{
                el.outerHTML = html;
            }} else {{
                console.warn('Element not found: ' + elementId);
            }}
        }}

        function handleChange(callbackId, value) {{
            window.ipc.postMessage(JSON.stringify({{
                event_type: 'change',
                callback_id: callbackId,
                value: String(value)
            }}));
        }}

    </script>
</body>
</html>"#,
        r, g, b, root_content
    )
}
