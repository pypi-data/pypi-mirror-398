from .ParserOrg import ParserOrg, OrgHeader, OrgClock, OrgTable, OrgSourceBlock, OrgText, OrgMath, OrgProperties, OrgList
from .Formatter import MarkdownFormatter
from typing import List, Sequence, Tuple, Union, Optional

def link_converter(link: str, name: str) -> str:
    if link.startswith("id:"):
        return f"[[{name}]]"
    return f"[{name}]({link})"

def export_markdown(orgfile: str, lnconv=None) -> List[str]:
    result: List[str] = []
    if lnconv is None:
        lnconv = link_converter
    formatter = MarkdownFormatter()
    with ParserOrg(orgfile, lnconv, formatter) as p:
        for item in p.parse():
            if isinstance(item, OrgHeader):
                result.append(formatter(item.name, item.level))
            elif isinstance(item, OrgProperties):
                print(item.values)
            elif isinstance(item, OrgClock):
                pass # do nothing for now
            elif isinstance(item, OrgTable):
                for row in item.rows:
                    result.append("| " + " | ".join(row) + " |")
                result.append("")  # add an empty line after the table
            elif isinstance(item, OrgSourceBlock):
                result.append(formatter.code(item.lines, item.language))
            elif isinstance(item, OrgText):
                result.append(item.line)
            elif isinstance(item, OrgMath):
                result.append(formatter.code(item.lines, 'math'))
            elif isinstance(item, OrgList):
                result.append(formatter.list(item.lines, item.ordered))

    return result
