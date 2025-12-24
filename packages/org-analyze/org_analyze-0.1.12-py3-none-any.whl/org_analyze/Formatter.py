from typing import List

class Formatter:
    def link(self, url: str, name: str) -> str:
        raise NotImplementedError
    def bold(self, text: str) -> str:
        raise NotImplementedError
    def inline_code(self, text: str) -> str:
        raise NotImplementedError
    def header(self, text: str, level: int) -> str:
        raise NotImplementedError
    def list(self, items: List[str], ordered: bool = False) -> str:
        raise NotImplementedError
    def code(self, items: List[str], language: str) -> str:
        raise NotImplementedError
    def text_line(self, text: str) -> str:
        raise NotImplementedError
    def start_table(self) -> str:
        raise NotImplementedError
    def table_row(self, row: List[str], header: bool = False):
        raise NotImplementedError
    def end_table(self) -> str:
        raise NotImplementedError

class MarkdownFormatter(Formatter):
    def link(self, url: str, name: str) -> str:
        if name is None:
            return f"[[{url}]]"
        return f"[{name}]({url})"

    def bold(self, text: str) -> str:
        return f"**{text}**"

    def inline_code(self, text: str) -> str:
        return f"`{text}`"

    def header(self, text: str, level: int) -> str:
        return f"{'#' * level} {text}"

    def list(self, items: List[str], ordered: bool = False) -> str:
        result = []
        for idx, line in enumerate(items):
            prefix = f"{idx + 1}. " if ordered else "- "
            result.append(f"{prefix}{line}")
        return "\n".join(result)

    def code(self, items: List[str], language: str) -> str:
        result = [f"```{language}"]
        result.extend(items)
        result.append("```")
        return "\n".join(result)

    def text_line(self, text: str) -> str:
        return text

    def start_table(self) -> str:
        return None

    def table_row(self, row: List[str], header: bool = False):
        return "| " + (" | ".join(row)) + " |"

    def end_table(self) -> str:
        return None

class HtmlFormatter(Formatter):
    def __init__(self):
        self.curdir=""

    def relativeUrl(self, url: str, curdir:str):
        if len(curdir) == 0:
            return url
        if url.startswith("https://") or url.startswith("http://"):
            return url
        if url.startswith(curdir+"/"):
            return url[len(curdir)+1:]
        if "/" in url:
            return ("../" + url)
        return url

    def link(self, url: str, name: str) -> str:
        if name is None:
            return f"<a href=\"{url}\">{url}</a>"

        url = self.relativeUrl(url, self.curdir)
        return f"<a href=\"{url}\">{name}</a>"

    def bold(self, text: str) -> str:
        return f"<strong>{text}</strong>"

    def inline_code(self, text: str) -> str:
        return f"<code>{text}</code>"

    def header(self, text: str, level: int) -> str:
        return f"<h{level}>{text}</h{level}>"

    def list(self, items: List[str], ordered: bool = False) -> str:
        result = ["<ul>"]
        for line in items:
            result.append(f"<li>{line}</li>")
        result.append("</ul>")
        return "\n".join(result)

    def code(self, items: List[str], language: str) -> str:
        if language == "math":
            result = ['\\[']
            result.extend(items)
            result.append('\\]')
            return "\n".join(result)
        result = [f'<pre><code class="language-{language}">']
        result.extend(items)
        result.append("</code></pre>")
        return "\n".join(result)

    def text_line(self, text: str) -> str:
        return text + "<br>"    

    def start_table(self) -> str:
        return "<table>"

    def table_row(self, row: List[str], header: bool = False):
        tag = "th" if header else "td"
        return "<tr>" + ("".join(f"<{tag}>{cell}</{tag}>" for cell in row)) + "</tr>"

    def end_table(self) -> str:
        return "</table>"
