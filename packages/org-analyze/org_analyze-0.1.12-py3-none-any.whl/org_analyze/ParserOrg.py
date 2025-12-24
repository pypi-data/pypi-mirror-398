"""
Very small Org-mode table/header parser.

Improvements over the original:
- Class is now `ParserOrg` and supports passing either a filename or a file-like object.
- Context manager support (use `with ParserOrg(...) as p:`).
- Safer parsing of headers, tables, list and variables.
- Returns parsed items from `parse()`.
"""

import logging
import re
from sqlite3 import DateFromTicks
from typing import IO, List, Sequence, Tuple, Union, Optional
import os
from .Formatter import MarkdownFormatter


class OrgHeader:
    """Represents an org-mode header (a line starting with one or more '*')."""
    header_re = re.compile(r"^(\*+)\s+(?:TODO\s+|DONE\s+)?(.*)")

    def __init__(self, line: str) -> None:
        m = self.header_re.match(line)
        if m:
            self.level = len(m.group(1))
            self.name = m.group(2) or ""
        else: # fallback: treat whole line as name with level 0
            self.level = 0
            self.name = line.strip()

    def __repr__(self) -> str:
        return f"<H{self.level} {self.name!r}>"

class OrgClock:
    """Represents a CLOCK entry."""
    clock_re = re.compile(r"CLOCK: \[(\d{4}-\d{2}-\d{2}) [^\]]+\]--\[.*?\] =>\s+([\d:]+)")
    clk_re = re.compile(
        r"^\#\+CLK:\s*\[(\d{4}-\d{2}-\d{2})\s+[A-Za-z]{3}\s+(\d{1,2}:\d{2})\]"
    )
    def __init__(self, line: str) -> None:
        m = self.clock_re.match(line)
        if not m:
            m = self.clk_re.match(line)
            if not m:
                raise ValueError(f"Invalid CLOCK line: {line}")
        self.start = m.groups(1)[0]  # YYYY-MM-DD
        self.duration = m.groups(1)[1]  # HH:MM

    def __repr__(self) -> str:
        return f"<Clock {self.start} {self.duration}>"

class OrgTable:
    """Simple container for table rows. Rows are lists of cell strings."""
    def __init__(self, row: Sequence[str]) -> None:
        self.rows: List[List[str]] = [list(row)]

    def add_row(self, row: Sequence[str]) -> None:
        self.rows.append(list(row))

    def getDictRows(self) -> List[dict]:
        """Return table rows as list of dicts, using the first row as keys."""
        if not self.rows:
            return []
        keys = self.rows[0]
        dict_rows = []
        for row in self.rows[1:]:
            row_dict = {keys[i]: row[i] if i < len(row) else "" for i in range(len(keys))}
            dict_rows.append(row_dict)
        return dict_rows
    
    def __repr__(self) -> str:
        return f"<Table rows={len(self.rows)}>"

class OrgSourceBlock:
    """Represents a source code block."""
    def __init__(self, line: str) -> None:
        self.lines = []
        self.language = line.strip(" ").split()[1] if (line and (" " in line)) else "text"

    def add(self, line: str) -> None:
        self.lines.append(line)

    def __repr__(self) -> str:
        return f"<SourceBlock lang={self.language} lines={len(self.lines)}>"

class OrgText:
    """Represents a plain text paragraph."""
    def __init__(self, line: str) -> None:
        self.line = line

    def __repr__(self) -> str:
        return f"<Text '{self.line}'>"

class OrgMath:
    """Represents a math block."""
    def __init__(self) -> None:
        self.lines = []

    def add(self, line: str) -> None:
        self.lines.append(line)

    def __repr__(self) -> str:
        return f"<Math lines={len(self.lines)}>"

class OrgProperties:
    """Represents a PROPERTIES block."""
    property_re = re.compile(r"^:([a-zA-Z0-9_\-]+):\s*(.*)")
    def __init__(self) -> None:
        self.values = {}

    def add(self, line: str) -> None:
        m = self.property_re.match(line)
        if m:
            key = m.group(1).strip().lower()
            value = m.group(2).strip()
            self.values[key] = value
            # setattr(self, key, value)

    def __repr__(self) -> str:
        return f"<Properties lines={len(self.values.keys())}>"

class OrgList:
    """Represents a list item."""
    def __init__(self, line: str) -> None:
        self.lines = [line]
        self.ordered = False

    def add(self, line: str) -> None:
        self.lines.append(line)

    def __repr__(self) -> str:
        return f"<List '{self.lines}'>"

class OrgDefList:
    """Represents a list item."""
    def __init__(self, term: str, definition: str) -> None:
        self.items = [[term, definition]]

    def add(self, term: str, definition: str) -> None:
        self.items.append([term, definition])

    def __repr__(self) -> str:
        return f"<DefList '{self.items}'>"

class OrgPropValue:
    """Represents a property value (outside property block)"""
    property_re = re.compile(r"^:([a-zA-Z0-9_\-]+):\s*(.*)")
    def __init__(self) -> None:
        self.values = {}

    def add(self, line: str) -> None:
        m = self.property_re.match(line)
        if m:
            key = m.group(1).strip().lower()
            value = m.group(2).strip()
            self.values[key] = value
            # setattr(self, key, value)

    def __repr__(self) -> str:
        return f"<Properties lines={len(self.values.keys())}>"

#-------------------------------------------------------------------------------------------------
class OrgElementParser:
    def __init__(self, cb_parse_links) -> None:
        self.parse_links = cb_parse_links
    def can_parse(self, line: str) -> bool:
        raise NotImplementedError
    def can_cont(self, line: str, obj) -> Tuple[bool, bool]:  # continue, line consumed
        return False, False
    def parse(self, line: str, file) -> object:
        raise NotImplementedError

    def replace_inline_code(self, line: str) -> str:
        # Replace ~...~ with `...`
        def repl(m):
            return self.formatter.inline_code(m.group(1))
        return re.sub(r'~([^~]+)~', repl, line)

    def replace_bold(self, line: str) -> str:
        # Replace *bold* with **bold**, but not at the start of the line (to avoid headers)
        def repl(m):
            return self.formatter.bold(m.group(1))
        return re.sub(r'\*(\S(?:.*?\S)?)\*(?!\*)', repl, line)

    def parse_line(self, line: str) -> str:
        """Parse a single line and return the processed line."""
        return self.replace_bold(self.replace_inline_code(line))

class OrgHeaderParser(OrgElementParser):
    def __init__(self, cb_parse_links):
        super().__init__(cb_parse_links)
    def can_parse(self, line): return line.startswith("*")
    def parse(self, line):     return OrgHeader(self.parse_links(line))

class OrgClockParser(OrgElementParser):
    def __init__(self, cb_parse_links):
        super().__init__(cb_parse_links)
    def can_parse(self, line): return line.startswith("CLOCK:") or line.startswith("#+CLK:")
    def parse(self, line):     return OrgClock(line)

class OrgCodeParser(OrgElementParser):
    def __init__(self, cb_parse_links):
        super().__init__(cb_parse_links)
    def can_parse(self, line): return line.lower().startswith("#+begin_src")
    def parse(self, line):     return OrgSourceBlock(line)
    def can_cont(self, line, obj):
        if line.lower().startswith("#+end_src"):
            return False,True
        else:
            obj.add(line)
            return True,True

class OrgMathParser(OrgElementParser):
    def __init__(self, cb_parse_links):
        super().__init__(cb_parse_links)
    def can_parse(self, line): return line.strip() == "\\["
    def parse(self, _):        return OrgMath()
    def can_cont(self, line, obj):
        if line.strip() == "\\]":
            return False,True
        else:
            obj.add(line)
            return True,True

class OrgPropertiesParser(OrgElementParser):
    def __init__(self, cb_parse_links):
        super().__init__(cb_parse_links)
    def can_parse(self, line): return line.strip() == ":PROPERTIES:"
    def parse(self, _):        return OrgProperties()
    def can_cont(self, line, obj):
        if line.strip() == ":END:":
            return False,True
        else:
            obj.add(line)
            return True,True

class OrgListParser(OrgElementParser):
    def __init__(self, cb_parse_links, formatter):
        super().__init__(cb_parse_links)
        self.formatter = formatter
    def can_parse(self, line): return line.startswith("- ") or line.startswith("+ ")
    def parse(self, line):        return OrgList(self.parse_line(self.parse_links(line[2:])))
    def can_cont(self, line, obj):
        if line.startswith("- "):
            obj.add(self.parse_line(self.parse_links(line[2:])))
            return True,True
        else:
            return False,False

class OrgDefListParser(OrgElementParser):
    def __init__(self, cb_parse_links, formatter):
        super().__init__(cb_parse_links)
        self.formatter = formatter
    def can_parse(self, line): return (line.startswith("- ") or line.startswith("+ ")) and (" :: " in line)
    def parse(self, line):
        term, definition = self._parse_term(line[2:]) 
        return OrgDefList(term, definition)
    def can_cont(self, line, obj):
        if (line.startswith("- ") or line.startswith("+ ")) and (" :: " in line):
            term, definition = self._parse_term(line[2:])
            obj.add(term, definition)
            return True,True
        else:
            return False,False
    def _parse_term(self, line: str) -> str:
        if "::" in line:
            term, definition = line.split(" :: ", 1)
            return term, self.parse_line(self.parse_links(definition))
        return "", line.strip()

class OrgTextParser(OrgElementParser):
    def __init__(self, cb_parse_links, formatter):
        super().__init__(cb_parse_links)
        self.formatter = formatter
    def can_parse(self, line): return True
    def parse(self, line):     return OrgText(self.parse_line(self.parse_links(line)))
    def can_cont(self, line: str, obj) -> Tuple[bool, bool]:  # continue, line consumed
        return False, False


class OrgTableParser(OrgElementParser):
    def __init__(self, cb_parse_links):
        super().__init__(cb_parse_links)
    def can_parse(self, line):  return line.lstrip().startswith("|")
    def parse(self, line):      return OrgTable(self.parse_row(line))

    def can_cont(self, line, obj) -> Tuple[bool, bool]:
        if line.strip().startswith("|"):
            text = line.strip()
            if not text.startswith("|-") and len(text) > 1:
                obj.add_row(self.parse_row(text))
            return True, True
        else:
            return False, False

    def parse_row(self, line):
        # remove leading and trailing pipe if present
        if line.endswith("|"):
            core = line[1:-1]
        else:
            core = line[1:]
        return [self.parse_links(c.strip()) for c in core.split("|")]

class OrgPropertyLineParser(OrgElementParser):
    def __init__(self, cb_parse_links):
        super().__init__(cb_parse_links)
        self.vars = {}

    def can_parse(self, line):  return line.startswith("#+")
    def parse(self, line):
        tail = line[2:]
        if ":" in tail:
            name, value = tail.split(":", 1)
            self.vars[name.strip().lower()] = value.strip()
        return None

#-------------------------------------------------------------------------------------------------
class ParserOrg:
    """Parser for a tiny subset of Emacs org-mode used by this project.

    Usage:
      p = ParserOrg(path_or_file)
      p.parse()
      items = p.items

    or as a context manager:
      with ParserOrg(path) as p:
          items = p.parse()

    The parser focuses on headers (lines starting with '*'), tables (lines
    beginning with '|') and file-local variables (lines starting with '#+').
    """

    org_link_re = re.compile(r"\[\[([^\[\]]+)\](?:\[([^\[\]]+)\])?\]")

    def __init__(self, source: Union[str, os.PathLike, IO[str]], link_converter=None, formatter=None) -> None:
        if isinstance(source, (str, os.PathLike)):
            # open file ourselves
            self._f = open(str(source), "rt", encoding="utf-8", errors="replace")
            self._own_file = True
        else:
            # assume file-like object
            self._f = source
            self._own_file = False

        self.items: List[object] = []
        self.link_converter = link_converter
        self.formatter = formatter or MarkdownFormatter()

    def __enter__(self) -> "ParserOrg":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if getattr(self, "_own_file", False):
            try:
                self._f.close()
            except Exception:
                logging.exception("Failed to close org file")

    def parse_links(self, line: str) -> str:
        """Parse org-mode links in the given line using the link_converter."""
        if self.link_converter is None:
            return line

        def repl(m: re.Match) -> str:
            link = m.group(1)
            name = m.group(2) if m.group(2) is not None else link

            link2, name2 = self.link_converter(link, name)
            return self.formatter.link(link2, name2)

        return self.org_link_re.sub(repl, line)

    def parse(self) -> List[object]:
        """Parse the opened file and return a list of top-level items.

        Items are instances of OrgHeader (which has .items) or OrgTable.
        File-local variables are stored in `self.vars`.
        """
        # Reset state
        self.items = []
        self.parsers = [
            OrgHeaderParser(self.parse_links),
            OrgClockParser(self.parse_links),
            OrgCodeParser(self.parse_links),
            OrgMathParser(self.parse_links),
            OrgPropertiesParser(self.parse_links),
            OrgDefListParser(self.parse_links, self.formatter),
            OrgListParser(self.parse_links, self.formatter),
            OrgTableParser(self.parse_links),
            OrgPropertyLineParser(self.parse_links),
            OrgTextParser(self.parse_links, self.formatter)  # this must be last
        ]   

        active_parser = None
        while True:
            line = self._f.readline()
            if line is None or len(line)==0:
                break
            line = line.rstrip("\n")

            if active_parser is not None:
                cont, consumed = active_parser.can_cont(line, self.items[-1])
                if not cont:
                    active_parser = None
                    if consumed:
                        line = self._f.readline().rstrip("\n")
                else:
                    continue  # do not change parser

            for parser in self.parsers:
                if parser.can_parse(line):
                    active_parser = parser

                    data = parser.parse(line)
                    if data is not None:
                        self.items.append(data)
                    break
        self.close()
        return self.items
