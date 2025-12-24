# Pawser

**Pawser** is a lightweight Python parser for PAWML (Pawso Markup Language).  
It allows you to read, parse, and traverse `.pawml` files as a tree of nodes.

## Installation

**Install via pip through PyPI**

```bash
pip install pawser
```
This is the most common method, however if you do not have pip and/or would like to download this without or for other reasons, you can;

**Clone the repository and install locally:**

```bash
git clone https://github.com/komoriiwakura/pawser
cd pawser
pip install -e .
```

## Example

```python
from pawser import parsePawml, printTree, pawml2domtree

# Parse and print the PAWML file
tree = parsePawml("example.pawml")
printTree(tree)

# Get the DOM tree for programmatic use
dom = pawml2domtree("example.pawml")
```

