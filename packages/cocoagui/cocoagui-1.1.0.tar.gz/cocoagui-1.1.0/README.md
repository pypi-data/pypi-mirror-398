# CocoaGUI

**The simplest Python GUI library ever created.**

CocoaGUI makes building desktop applications incredibly easy. No complex setup, no confusing APIs - just clean, intuitive Python code that anyone can understand.

[![PyPI version](https://badge.fury.io/py/cocoagui.svg)](https://badge.fury.io/py/cocoagui)
[![Python versions](https://img.shields.io/pypi/pyversions/cocoagui.svg)](https://pypi.org/project/cocoagui/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why CocoaGUI?

- **Simple Syntax** - Create widgets in one line with intuitive parameters
- **Fast Development** - Build complete applications in minutes, not hours
- **Easy to Learn** - If you know basic Python, you already know CocoaGUI
- **Clean Code** - Your GUI code is readable and maintainable
- **Zero Dependencies** - Uses only Python's built-in tkinter

## Quick Start

### Installation

```bash
pip install cocoagui
```

### Hello World

```python
import CocoaGUI as gui

# Create a window
app = gui.Window("My App", width=400, height=300)

# Add widgets
gui.Label(app, "Enter your name:", x=20, y=20)
name_input = gui.Input(app, x=20, y=50, width=300)

def greet():
    name = name_input.get()
    gui.alert(f"Hello, {name}!")

gui.Button(app, "Greet", command=greet, x=20, y=90)

# Run the app
app.run()
```

That's it! Just 13 lines to create a working GUI application.

## Features

- **Window** - Create application windows with custom sizes
- **Button** - Interactive buttons with click handlers
- **Label** - Display text with customizable sizes
- **Input** - Single-line text input fields
- **TextArea** - Multi-line text editing
- **CheckBox** - Toggle checkboxes with state management
- **Utilities** - Alert and confirmation dialogs

## Examples

### Calculator

```python
import CocoaGUI as gui

app = gui.Window("Calculator", width=300, height=400)

display = gui.TextArea(app, x=25, y=20, width=250, height=60)
display.set("0")

def add_number(n):
    current = display.get().strip()
    display.set(current + str(n) if current != "0" else str(n))

# Create number buttons
for i, num in enumerate(range(1, 10)):
    row, col = divmod(i, 3)
    gui.Button(app, str(num), command=lambda n=num: add_number(n),
               x=25 + col*70, y=100 + row*50)

app.run()
```

### Text Editor

```python
import CocoaGUI as gui

app = gui.Window("Text Editor", width=600, height=400)

text_area = gui.TextArea(app, x=10, y=40, width=580, height=300)

def save():
    content = text_area.get()
    with open("document.txt", "w") as f:
        f.write(content)
    gui.alert("Saved successfully!")

gui.Button(app, "Save", command=save, x=10, y=10)

app.run()
```

## 📖 Documentation

Full documentation is available at: [CocoaGUI Documentation](https://mochacinno-dev.github.io/Graphica/)

### API Reference

- [Window](https://mochacinno-dev.github.io/Graphica/api/window/) - Main application window
- [Button](https://mochacinno-dev.github.io/Graphica/api/button/) - Clickable buttons
- [Label](https://mochacinno-dev.github.io/Graphica/api/label/) - Text display
- [Input](https://mochacinno-dev.github.io/Graphica/api/input/) - Text input field
- [TextArea](https://mochacinno-dev.github.io/Graphica/api/textarea/) - Multi-line text
- [CheckBox](https://mochacinno-dev.github.io/Graphica/api/checkbox/) - Toggle checkbox

## 🛠️ Requirements

- Python 3.6 or higher
- tkinter (usually comes pre-installed with Python)

## 📝 License

GNU General Public License V3 - see [LICENSE](LICENSE) file for details

## 👩‍💻 Author

**Camila "Mocha" Rose**  
CoffeeShop Development