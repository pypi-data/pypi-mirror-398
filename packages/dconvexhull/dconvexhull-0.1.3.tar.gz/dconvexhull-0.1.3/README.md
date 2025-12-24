# dconvexhull

An educational Python package that provides a simple API for computing the **convex hull** of a 2D point set.  
This package wraps a C++ module for efficient computation and offers Python-friendly interfaces for students, researchers, and developers.

---

## ✨ Features
- Compute convex hulls for **2D point sets**.
- Input formats:
  - Python 2D lists (`[[x1, y1], [x2, y2], ...]`)
  - CSV files containing 2D coordinates
- Output:
  - A **PDF file** that visualizes the convex hull and highlights the vertices.
- Educational purpose: designed to help Python users understand convex hull algorithms and visualization workflows.
- First edition: **only supports 2D data**.

---

## 📦 Installation

You can install the package directly from PyPI (after publishing):

```bash
pip install dconvexhull

```

Or install locally for development:

```bash
git clone https://github.com/yourusername/dconvexhull.git
cd dconvexhull
pip install .
```

---
## 🚀 USAGE

After installation, you can import and use the package as follows:
Example 1: Using a Python 2D list

```Python
from dconvexhull import convxHull
# Define a set of points
ptc = [[0, 0], [1, 1], [2, 0], [2, 2], [0, 2]]

# Draw convex hull from array input
convxHull.draw_convxHull_from_arr(ptc)
```

Example 2: Using a CSV fil

```Python
from dconvexhull import operations
operations.compute_convex_hull("points.csv")
```

This will generate a PDF file () that shows the convex hull polygon and its vertices.

---


## 📖 Educational Notes
• 	Convex Hull: The smallest convex polygon that contains all points in a set.
• 	This package demonstrates how Python can interface with C++ modules for computational geometry.
• 	Visualization is handled with matplotlib, making results easy to interpret for students and researchers.

---
## ⚙️ Dependencies
- matplotlib (for visualization and PDF export)

---
## 🧑‍🏫 Target Audience
• 	Python learners exploring computational geometry
• 	Students studying convex hull algorithms
• 	Developers interested in Python–C++ integration