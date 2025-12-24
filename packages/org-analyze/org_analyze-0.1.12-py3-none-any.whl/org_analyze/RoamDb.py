import sqlite3
import os
import re
from typing import List, Tuple
import pandas as pd

def unquote(s: str) -> str:
    if s.startswith("\"") and s.endswith("\""):
        return s[1:-1]
    return s

class RoamNode:
    def __init__(self, id: str, title: str, file: str, properties: str, tags: str):
        self.id = id[1:-1]
        self.title = unquote(title)
        self.file = unquote(file)
        self.properties = self.parse_properties(properties)
        self.tags = [unquote(tag) for tag in tags.split(",")] if tags else []
        self.category = self.properties.get("CATEGORY", "")

    def base_name(self) -> str:
        return os.path.splitext(os.path.basename(self.file))[0]

    def get_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "file": self.file,
            "properties": self.properties,
            "tags": self.tags,
            "category": self.category
        }

    def parse_properties(self, text: str) -> dict:
        # Match pairs like ("KEY" . "VALUE")
        pattern = re.compile(r'\("([^"]+)"\s*\.\s*("(?:[^"\\]|\\.)*"|#\([^)]+\)|[^\s)]+)\)')
        props = {}
        for match in pattern.finditer(text):
            key = match.group(1)
            value = match.group(2)
            # Remove surrounding quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            props[key] = value
        return props

    def __str__(self):
        return f"Node(id='{self.id}', title='{self.title}', file='{self.file}')"

class RoamLink:
    def __init__(self, source: str, destination: str, type: str):
        self.source = unquote(source)
        self.destination = unquote(destination)
        self.type = type


class RoamDB:
    def __init__(self, org_path: str):
        self.nodes: List[RoamNode] = []
        self.files: List[str] = []
        self.links: List[RoamLink] = []
        self.org_path = org_path

    def getNodesDf(self):
        data = [node.get_dict() for node in self.nodes]
        return pd.DataFrame(data)

    def load(self, db_path: str):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nodes.id, nodes.title, nodes.file, nodes.properties, GROUP_CONCAT(tags.tag) as tags FROM nodes LEFT JOIN tags ON nodes.id=tags.node_id GROUP BY nodes.id;")
            rows = cursor.fetchall()
            self.nodes = [RoamNode(row[0], row[1], self.convert_filename(unquote(row[2])), row[3], row[4]) for row in rows]

            cursor.execute("SELECT file FROM files;")
            rows = cursor.fetchall()
            self.files = [self.convert_filename(unquote(row[0])) for row in rows]

            cursor.execute("SELECT source, dest, type FROM links;")
            rows = cursor.fetchall()
            self.links = [RoamLink(row[0], row[1], row[2]) for row in rows]

    def get_files(self):
        return [fname for fname in self.files]

    def get_files_by_tag(self, tag: str) -> List[Tuple[str, str]]:
        return [(node.file, node.title) for node in self.nodes if tag in node.tags]

    def filename2id(self, filename: str):
        filename = self.convert_filename(filename)
        return next(
            (node.id for node in self.nodes if node.file == filename or self.convert_filename(node.file) == filename),
            None
        )
    
    def filename2node(self, filename: str):
        nid = self.filename2id(filename)
        return self.id2node(nid) if nid is not None else None

    def id2node(self, node_id: str) -> RoamNode:
        return next((node for node in self.nodes if node.id == node_id), None)

    def get_links(self, filename: str):
        rel_filename = self.convert_filename(filename)
        node_id = self.filename2id(rel_filename)
        if node_id is None:
            return []
        a = [self.id2node(link.destination) for link in self.links if link.source == node_id]
        b = [self.id2node(link.source) for link in self.links if link.destination == node_id]

        a.extend(b)
        return [node for node in a if node is not None]

    def convert_filename(self, filename: str) -> str:
        if filename.lower().startswith(self.org_path.lower()): # for windows needs case insensitive comparison
            return filename[len(self.org_path) :]
        return filename
