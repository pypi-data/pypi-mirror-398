# Wry Py

Python bindings for [Wry](https://github.com/tauri-apps/wry) for building desktop apps with webviews.

## Install

```bash
pip install wry_py
```

Linux needs GTK/WebKitGTK:

```bash
# Debian/Ubuntu
sudo apt install libgtk-3-dev libwebkit2gtk-4.1-dev

# Arch
sudo pacman -S gtk3 webkit2gtk-4.1
```

## Quick Start

```python
from wry_py import UiWindow, div, text, button

count = 0

def increment():
    global count
    count += 1
    render()

def render():
    root = (
        div()
        .size_full()
        .v_flex()
        .items_center()
        .justify_center()
        .gap(20)
        .child_builder(text(f"Count: {count}").text_size(32))
        .child_builder(
            button("Increment")
            .padding(10, 20)
            .bg("#3b82f6")
            .text_color("#fff")
            .on_click(increment)
        )
        .build()
    )
    window.set_root(root)

window = UiWindow(title="Counter", width=400, height=300)
render()
window.run()
```

## Local assets

If your webview blocks `file://` access, register binary assets (images, fonts)
from Python using `AssetCatalog` and reference them with the `asset:` prefix
when creating an image. This embeds the bytes as `data:` URIs so the webview
can load them without filesystem permissions.

```python
from wry_py import AssetCatalog, image

catalog = AssetCatalog()
with open("examples/local_image/assets/logo.png", "rb") as f:
    catalog.add("logo.png", f.read())

image("asset:logo.png").width(120).height(120)
```

## Examples

```bash
# Counter
python -m examples.counter

# Todo list with dialogs
python -m examples.todo_list

# Hover, focus, and transitions
python -m examples.styles

# Partial updates (efficient UI updates)
python -m examples.partial_update

# Multi-step form with all form elements
python -m examples.form_demo
```

## Development

```bash
git clone https://github.com/Jacob-Walton/wry_py.git
cd wry_py
pip install maturin
maturin develop --release
```

## Docs

<https://jacob-walton.github.io/wry_py/>

## License

MIT
