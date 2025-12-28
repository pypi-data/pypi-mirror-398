# Graphica

**The simplest Python GUI library ever created.**

Graphica makes building desktop applications incredibly easy. No complex setup, no confusing APIs - just clean, intuitive Python code that anyone can understand.

## Installation

```bash
pip install graphica
```

## Quick Start

```python
import graphica as gui

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

## Why Graphica?

✨ **Simple Syntax** - Create widgets in one line with intuitive parameters

🚀 **Fast Development** - Build complete applications in minutes, not hours

📚 **Easy to Learn** - If you know basic Python, you already know Graphica

🎨 **Clean Code** - Your GUI code is readable and maintainable

## Examples

### Calculator

```python
import graphica as gui

app = gui.Window("Calculator", width=300, height=400)

display = gui.TextArea(app, x=20, y=20, width=260, height=60)
display.set("0")

def add_digit(digit):
    current = display.get().strip()
    display.set(current + str(digit) if current != "0" else str(digit))

# Create number buttons
for i in range(10):
    row = 2 - (i - 1) // 3 if i > 0 else 3
    col = (i - 1) % 3 if i > 0 else 0
    x = 20 + col * 70
    y = 100 + row * 60
    gui.Button(app, str(i), command=lambda d=i: add_digit(d), x=x, y=y)

app.run()
```

### Text Editor

```python
import graphica as gui

app = gui.Window("Text Editor", width=600, height=500)

text_area = gui.TextArea(app, x=10, y=50, width=580, height=400)

def save_file():
    content = text_area.get()
    with open("document.txt", "w") as f:
        f.write(content)
    gui.alert("File saved!", "Success")

gui.Button(app, "Save", command=save_file, x=10, y=10)

app.run()
```

## Documentation

Full documentation is available at: [https://yourusername.github.io/graphica](https://yourusername.github.io/graphica)

## Requirements

- Python 3.6 or higher
- tkinter (usually comes pre-installed with Python)

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- **GitHub**: https://github.com/yourusername/graphica
- **Documentation**: https://yourusername.github.io/graphica
- **PyPI**: https://pypi.org/project/graphica/
- **Issues**: https://github.com/yourusername/graphica/issues

---

*Built with ❤️ for Python developers everywhere*