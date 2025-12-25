# Termella

**Termella** is a Python library designed to make terminal output rich, colorful, and beautifully formatted with minimal effort.

![Version](https://img.shields.io/badge/version-0.0.5-blue.svg)
![Licence](https://img.shields.io/badge/license-MIT-green.svg)

## 📦 New in v0.0.5

* **Layouts**: Place widgets side-by-side with `columns`.
* **Grids**: Automatically arrange items into rows and columns with `grid`.
* **Trees**: Visualize nested data or directories with `tree`.
* **Composition**: Nest widgets inside other widgets (e.g., a Tree inside a Panel).
* **Smart Alignment**: Layouts handle colored text perfecty without breaking alignment.

## 🛠 Installation

```bash
pip install termella
```
```bash
git clone https://github.com/codewithzaqar/termella.git
cd termella
pip install .
```
# Quick Start
## Basic Color Printing
The `cprint` function is the quickest way to output stylvd text.

```python
from termella import cprint

cprint("Operation Successful", color="green", styles="bold")
cprint("System Failure", color="white", bg="bg_red", styles=["blink", "bold"])
```
## The `Text` Object
For more control, use the `Text` class. It allows for method chaining and string concatenation.
```python
from termella import Text

# Create styled parts
prefix = Text("[INFO] ").style(color="blue", styles="bold")
message = Text("Server is running...").style(color="white")

# Combine and print
print(prefix + message)
```
## UI Components
Create professional-looking output using widgets.
```python
from termella import panel

content = "Termella v0.0.1\nStatus: Online\nPort: 8080"
panel(content, color="cyan", title="Server Status")
```
## Documentation
For detailed usage, please see the `docs/` folder:

1. [API Reference](docs/api.md) - Details on classes and functions.
2. [Colors & Styles](docs/colors.md) - A cheat sheet of all available options.

## License
This project is licensed under the [MIT License](LICENSE).