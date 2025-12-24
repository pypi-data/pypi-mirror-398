class PawserNode:
    def __init__(self, typeName, attrs=None):
        self.type = typeName
        self.attrs = attrs or {}
        self.children = []


class PawserTextNode:
    def __init__(self, content):
        self.type = "text"
        self.content = content
        self.children = []


def parsePawml(filePath):
    with open(filePath, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    # First line must be #pawml
    for line in lines:
        if line.strip():
            firstLine = line.strip()
            break
    else:
        raise ValueError("Error: File is empty")
    if firstLine != "#pawml":
        raise ValueError("Error: File must start with #pawml")

    # Last line must be #pawml
    for line in reversed(lines):
        if line.strip():
            lastLine = line.strip()
            break
    else:
        raise ValueError("Error: File is empty")
    if lastLine != "#pawml":
        raise ValueError("Error: File must end with #pawml")

    root = PawserNode("pawml")
    stack = [(root, -1)]
    allowedTags = ["h1", "h2", "h3", "li", "it", "plt", "ol", "p"]

    for lineNo, line in enumerate(lines[1:-1], start=2):
        if not line.strip():
            continue

        indent = 0
        while line.startswith("\t"):
            indent += 1
            line = line[1:]

        if line == "#pawml":
            break  # middle block, ignore

        if line.startswith("#mdata"):
            try:
                parts = line[6:].strip().split("=", 1)
                if len(parts) != 2:
                    raise ValueError
                key = parts[0].strip()
                value = parts[1].strip().strip('"')
                if not value:
                    raise ValueError(f"Error: mdata {key} missing value on line {lineNo}")
                node = PawserNode("mdata")
                node.children.append(PawserNode(key, attrs={}))
                node.children[-1].children.append(PawserTextNode(value))
            except:
                raise ValueError(f"Error: Invalid mdata on line {lineNo}: '{line}'")
        elif line.startswith("#"):
            parts = line[1:].split(" ", 1)
            tag = parts[0]
            rest = parts[1] if len(parts) > 1 else None

            if tag not in allowedTags:
                raise ValueError(f"Error: Unknown tag '{tag}' on line {lineNo}")

            node = PawserNode(tag)

            if tag == "plt" and rest:
                restParts = rest.split(" ", 1)
                linkPart = restParts[0]
                if linkPart.startswith("link="):
                    node.attrs["link"] = linkPart[5:].strip('"')
                    if len(restParts) > 1:
                        node.children.append(PawserTextNode(restParts[1]))
                else:
                    node.children.append(PawserTextNode(rest))
            elif rest:
                node.children.append(PawserTextNode(rest))
        else:
            node = PawserTextNode(line)

        while stack and stack[-1][1] >= indent:
            stack.pop()
        if not stack:
            raise ValueError(f"Error: Invalid indentation on line {lineNo}")
        parent = stack[-1][0]
        parent.children.append(node)
        stack.append((node, indent))

    return root


def printTree(node, indent=0):
    space = "    " * indent

    if node.type == "text":
        print(space + f'"{node.content}"')
        return
    attrs = f" {node.attrs}" if node.attrs else ""
    print(space + node.type + attrs)
    for child in node.children:
        printTree(child, indent + 1)


def pawml2domtree(filePath):
    """
    Parse a PawML file and return its DOM tree.

    Args:
        filePath (str): Path to the .pawml file

    Returns:
        PawserNode: The root node of the parsed DOM tree
    """
    try:
        tree = parsePawml(filePath)
        return tree  # return the DOM tree instead of printing
    except Exception as e:
        print(e)
        return None
