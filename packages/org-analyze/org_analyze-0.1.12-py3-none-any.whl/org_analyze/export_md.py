# Converts Org-roam database to Markdown files.
#
from .org2html import export_html as export
from .RoamDb import RoamDB
from .Formatter import MarkdownFormatter
from .PageBuilder import PageBuilder, MarkdownPageBuilder
import os
from typing import List
import argparse

EXTENSION = ".md"

class MarkdownConverter:
    def __init__(self, roam: RoamDB, dest_path: str):
        self.roam = roam
        self.dest_path = dest_path
        self.formatter = MarkdownFormatter()
        self.builder = MarkdownPageBuilder("Title")

    def link_converter(self, link: str, name: str) -> str:
        if link.startswith("id:"):
            _, hash = link.split(":", 1)
            roam_node = self.roam.id2node(hash)
            if roam_node is not None:
                fname = self.dest_path + roam_node.file.replace(".org", EXTENSION)
                return fname, name
            return name, None
        return link, name

    def handle_file(self, org_file: str, md_file: str) -> None:
        print(f"Processing file: {org_file} -> {md_file}")
        self.builder.clear()
        with open(md_file, "w", encoding="utf-8") as md_file_obj:
            for line in export(org_file, self.link_converter, self.roam, self.formatter, self.builder):
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
        default=HOME + "/OrgAnalyze/tmp/",
        help="Destination directory for output MD files. "
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

    converter = MarkdownConverter(roam_db, args.html_path)
    converter.handle_file(org_file, md_file)

def main():
    HOME = os.environ.get("HOME", "c:/home/jari").replace("\\", "/")

    parser = argparse.ArgumentParser(
        description="Convert Org-roam database to MD files. "
                    "This tool reads Org-roam .org files and exports them as MD, "
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
        '--md_path',
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

    roam_db = RoamDB(args.org_path)
    roam_db.load(args.roam_db)

    create_folders(roam_db.get_files())
    converter = MarkdownConverter(roam_db, args.md_path)

    for file in roam_db.files:
        md_filename = os.path.join("tmp", file.replace(".org", EXTENSION))
        converter.handle_file(args.org_path + file, md_filename)


if __name__ == "__main__":
    main()
