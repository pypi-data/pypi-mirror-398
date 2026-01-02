"""
Plugin System - Dynamic node loading

Allows loading nodes from:
- A Python file
- A plugins folder
- An installed module

Usage:
    from nanobot.plugins import load_node, load_nodes_from_dir

    # Load a node from file
    MyNode = load_node("plugins/my_node.py")
    engine.add_node(MyNode())

    # Load all nodes from a folder
    nodes = load_nodes_from_dir("plugins/")
    for node_class in nodes:
        engine.add_node(node_class())
"""

import os
import sys
import importlib.util
from typing import List, Type, Optional
from .core import Node


def load_node(filepath: str, class_name: Optional[str] = None) -> Type[Node]:
    """
    Load a Node class from a Python file.

    Args:
        filepath: Path to the .py file
        class_name: Name of the class to load (auto-detected if None)

    Returns:
        The Node class

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If no Node found in file
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Plugin not found: {filepath}")

    # Load the module
    module_name = os.path.basename(filepath).replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Look for the Node class
    if class_name:
        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            if isinstance(cls, type) and issubclass(cls, Node) and cls is not Node:
                return cls
        raise ValueError(f"Class {class_name} not found or not a Node")

    # Auto-detection: find any class inheriting from Node
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, Node) and obj is not Node:
            return obj

    raise ValueError(f"No Node class found in {filepath}")


def load_nodes_from_dir(dirpath: str) -> List[Type[Node]]:
    """
    Load all nodes from a folder.

    Args:
        dirpath: Path to plugins folder

    Returns:
        List of Node classes found
    """
    nodes = []

    if not os.path.isdir(dirpath):
        return nodes

    for filename in os.listdir(dirpath):
        if filename.endswith(".py") and not filename.startswith("_"):
            filepath = os.path.join(dirpath, filename)
            try:
                node_class = load_node(filepath)
                nodes.append(node_class)
            except (ValueError, Exception) as e:
                print(f"Warning: Could not load {filename}: {e}")

    return nodes


def load_node_from_module(module_path: str, class_name: str) -> Type[Node]:
    """
    Load a Node from an installed module.

    Args:
        module_path: Module path (e.g., "my_plugins.custom_nodes")
        class_name: Node class name

    Returns:
        The Node class
    """
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)

    if not isinstance(cls, type) or not issubclass(cls, Node):
        raise ValueError(f"{class_name} is not a Node class")

    return cls
