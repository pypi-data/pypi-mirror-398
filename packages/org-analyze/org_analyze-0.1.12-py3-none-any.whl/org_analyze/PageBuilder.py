from types import NotImplementedType
from typing import List, Dict, Sequence, Tuple, Union, Optional

ZENBURN_CSS = [
    "body { background: #3F3F3F; color: #DCDCCC; font-family: 'Segoe UI', 'Arial', sans-serif; }",
    ".container { display: flex; flex-direction: row; }",
    ".main-content { flex: 3; padding: 16px; }",
    ".side-links { flex: 1; padding: 16px; background: #2B2B2B; color: #93E0E3; min-width: 200px; }",
    "h1, h2, h3, h4, h5, h6 { color: #F0DFAF; }",
    "table { background: #4F4F4F; color: #DCDCCC; border-collapse: collapse; }",
    "th, td { border: 1px solid #6F6F6F; padding: 4px 8px; }",
    "th { background: #5F5F5F; color: #F0DFAF; }",
    "pre, code { background: #2B2B2B; color: #CC9393; font-family: 'Fira Mono', 'Consolas', 'Monaco', monospace; }",
    ".math { background: #2B2B2B; color: #DFAF8F; padding: 8px; display: block; }",
    "a { color: #93E0E3; }"
]

class PageBuilder:
    def add_main_content(self, html: List[str]):
        raise NotImplementedError
    def add_side_link(self, html: List[str]):
        raise NotImplementedError
    def render(self, formatter) -> List[str]:
        raise NotImplementedError
    def add_tags(self, name: str, tags: List[Tuple[str,str]]):
        raise NotImplementedType


class HtmlPageBuilder(PageBuilder):
    def __init__(self, title: str, css: Optional[List[str]] = None):
        self.title = title
        self.main_content: List[str] = []
        self.side_links: List[str] = []
        self.tags: Dict[str, List[Tuple[str,str]]] = {}
        self.css = css or ZENBURN_CSS

    def _build_header(self) -> List[str]:
        return [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<meta charset=\"utf-8\">",
            f"<title>{self.title}</title>",
            '<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>',
            "<style>"] + self.css + ["</style>",
            "</head>",
            "<body>",
            '<div class="container">'
        ]

    def _build_footer(self) -> List[str]:
        return [
            "</div>",  # end container
           "</body>",
            "</html>"
        ]

    def add_main_content(self, html: List[str]):
        self.main_content.append(html)

    def add_side_link(self, html: List[str]):
        self.side_links.append(html)

    def add_tags(self, name: str, tags: List[Tuple[str,str]]):
        self.tags[name] = tags

    def render(self, formatter) -> List[str]:
        page = []
        page.extend(self._build_header())
        page.append('<div class="main-content">')
        page.extend(self.main_content)
        page.append('</div>')
        page.append('<div class="side-links">')
        page.append(formatter.header("Links", 2))
        page.extend(self.side_links)
        for name,tags in self.tags.items():
            page.append(formatter.header(name, 2))
            for url,lname in tags:
                page.append(formatter.link(url, lname))
            page.append("<br>")
        page.append('</div>')
        page.extend(self._build_footer())
        return page


class MarkdownPageBuilder(PageBuilder):
    def __init__(self, title: str):
        self.title = title
        self.main_content: List[str] = []
        self.side_links: List[str] = []
        self.tags: Dict[str, List[Tuple[str,str]]] = {}

    def clear(self):
        self.main_content = []
        self.side_links = []

    def add_main_content(self, html: List[str]):
        self.main_content.append(html)

    def add_side_link(self, html: List[str]):
        self.side_links.append(html)

    def add_tags(self, name: str, tags: List[Tuple[str,str]]):
        self.tags[name] = tags

    def render(self, formatter) -> List[str]:
        page = []
        page.extend(self.main_content)
        page.append('')
        page.append('-------------------------------------------------------------')
        page.append('## Links')
        page.extend(self.side_links)
        return page
