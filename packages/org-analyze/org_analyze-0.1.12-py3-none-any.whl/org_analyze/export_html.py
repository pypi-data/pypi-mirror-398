# Converts Org-roam database to HTML files.
#
from .org2html import HtmlFormatter, export_html as export
from .RoamDb import RoamDB
import os
from typing import List
import argparse

#EXTENSION = ".md"
EXTENSION = ".html"

def removePrefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

class MarkdownConverter:
    def __init__(self, roam: RoamDB):
        self.roam = roam
        self.current_dir = ""
        self.formatter = HtmlFormatter()

    def setCurrentDir(self, cd):
        self.current_dir = cd
        self.formatter.curdir = cd

    def link_converter(self, link: str, name: str) -> str:
        if link.startswith("id:"):
            _, hash = link.split(":", 1)
            roam_node = self.roam.id2node(hash)
            if roam_node is not None:
                fname = roam_node.file.replace(".org", EXTENSION)
                fname = removePrefix(fname, self.current_dir + "/")
                return fname, name
            return name, None
        return link, name

    def handle_file(self, org_file: str, md_file: str) -> None:
        print(f"Processing file: {org_file} -> {md_file}")
        with open(md_file, "w", encoding="utf-8") as md_file_obj:
            for line in export(org_file, self.link_converter, self.roam, formatter=self.formatter):
                if isinstance(line, list):
                    md_file_obj.write("\n".join(line))
                    md_file_obj.write("\n")
                else:
                    md_file_obj.write(line+"\n")


def create_folders(files: List[str]):
    folders = set([file.split("/")[0] for file in files if ("/" in file)])
    os.makedirs("tmp", exist_ok=True)
    for folder in folders:
        print(f"Creating folder tmp/{folder}...")
        os.makedirs(os.path.join("tmp", folder.lstrip("/")), exist_ok=True)
    return folders

def run_one(org_file, md_file):
    HOME = os.environ.get("HOME", "c:/home/jari").replace("\\", "/")

    parser = argparse.ArgumentParser(
        description="Convert Org-roam database to HTML files. "
                    "This tool reads Org-roam .org files and exports them as HTML, "
                    "preserving internal links and structure."
    )
    parser.add_argument(
        '--org_path',
        type=str,
        default=HOME + "/org-roam/",
        help="Directory containing Org-roam .org files to be converted. "
             "Default: %(default)s"
    )
    parser.add_argument(
        '--html_path',
        type=str,
        #default=HOME + "/OrgAnalyze/tmp/",
        default=HOME + "tmp/",
        help="Destination directory for output HTML files. "
             "Converted files will be placed here. Default: %(default)s"
    )
    parser.add_argument(
        '--roam_db',
        type=str,
        default=HOME + "/.emacs.d/org-roam.db",
        help="Path to the Org-roam SQLite database file. "
             "Used to resolve links and metadata. Default: %(default)s"
    )
    args = parser.parse_args()

    roam_db = RoamDB(args.org_path)
    roam_db.load(args.roam_db)

    converter = MarkdownConverter(roam_db)
    converter.handle_file(org_file, md_file)

def convert_path(path: str) -> str:
    path = path.replace("\\", "/")
    if not path.endswith("/"):
        path += "/"
    return path

def main():
    HOME = os.environ.get("HOME", "c:/home/jari").replace("\\", "/")

    parser = argparse.ArgumentParser(
        description="Convert Org-roam database to HTML files. "
                    "This tool reads Org-roam .org files and exports them as HTML, "
                    "preserving internal links and structure."
    )
    parser.add_argument(
        '--org_path',
        type=str,
        default=HOME + "/org-roam/",
        help="Directory containing Org-roam .org files to be converted. "
             "Default: %(default)s"
    )
    parser.add_argument(
        '--html_path',
        type=str,
        default=HOME + "/OrgAnalyze/tmp/",
        help="Destination directory for output HTML files. "
             "Converted files will be placed here. Default: %(default)s"
    )
    parser.add_argument(
        '--roam_db',
        type=str,
        default=HOME + "/.emacs.d/org-roam.db",
        help="Path to the Org-roam SQLite database file. "
             "Used to resolve links and metadata. Default: %(default)s"
    )
    args = parser.parse_args()
    org_path = convert_path(args.org_path)

    roam_db = RoamDB(org_path)
    roam_db.load(args.roam_db)

    create_folders(roam_db.get_files())
    converter = MarkdownConverter(roam_db)

    for file in roam_db.files:
        curdir = ""
        if "/" in file:
            curdir = file[:file.rindex('/')]
        converter.setCurrentDir(curdir)

        html_filename = os.path.join(args.html_path, file.replace(".org", EXTENSION))
        converter.handle_file(org_path + file, html_filename)


if __name__ == "__main__":
    main()
