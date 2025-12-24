from re import I
from .ParserOrg import OrgDefList, ParserOrg, OrgHeader, OrgClock, OrgTable, OrgSourceBlock, OrgText, OrgMath, OrgProperties, OrgList
from .Formatter import HtmlFormatter
from .PageBuilder import PageBuilder, HtmlPageBuilder
from typing import List, Sequence, Tuple, Union, Optional

def link_converter(link: str, name: str) -> str:
    if link.startswith("id:"):
        return f"<a href=\"{name}.html\">{name}</a>"
    return f"<a href=\"{link}\">{name}</a>"


def html_file(filename: str) -> str:
    return filename.replace(".org", ".html")


def export_html(orgfile: str, lnconv=None, roam=None, formatter=None, builder=None) -> List[str]:
    builder : PageBuilder = builder or HtmlPageBuilder("Org Export")
    if lnconv is None:
        lnconv = link_converter
    formatter = formatter or HtmlFormatter()
    with ParserOrg(orgfile, lnconv, formatter) as p:
        result : List[str] = []
        for item in p.parse():
            if isinstance(item, OrgHeader):
                result.append(formatter.header(item.name, item.level))
            elif isinstance(item, OrgProperties):
                #print(item.values)
                pass
            elif isinstance(item, OrgClock):
                pass # do nothing for now
            elif isinstance(item, OrgTable):
                result.append(formatter.start_table())
                if item.rows:
                    # Table header
                    result.append(formatter.table_row(item.rows[0], True))
                    # Table rows
                    for row in item.rows[1:]:
                        result.append(formatter.table_row(row))
                result.append(formatter.end_table())
            elif isinstance(item, OrgSourceBlock):
                result.append(formatter.code(item.lines, item.language))
            elif isinstance(item, OrgText):
                result.append(formatter.text_line(item.line))
            elif isinstance(item, OrgMath):
                result.append(formatter.code(item.lines, 'math'))
            elif isinstance(item, OrgList):
                result.append(formatter.list(item.lines))
            elif isinstance(item, OrgDefList):
                outlst = [formatter.bold(term) + ": " + definition for term, definition in item.items]
                result.append(formatter.list(outlst))
        builder.add_main_content(result)

        links = []
        tags = []
        if roam is not None:
            for node in roam.get_links(orgfile):
                url = html_file(node.file)
                links.append(formatter.text_line(formatter.link(url, node.title)))
            
            node = roam.filename2node(orgfile)
            if node is not None:
                for t in node.tags:
                    tag_list = [(html_file(items[0]), items[1]) for items in roam.get_files_by_tag(t)]
                    builder.add_tags(t, tag_list)
        builder.side_links.extend(links)
    return builder.render(formatter)

