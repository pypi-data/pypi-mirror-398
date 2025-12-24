from org_analyze.ParserOrg import ParserOrg, OrgHeader, OrgClock, OrgProperties
import os
import pandas as pd
from collections import defaultdict

def time_str_to_hours(time_str):
    parts = time_str.split(":")
    if len(parts) == 2:
        hours = int(parts[0])
        minutes = int(parts[1])
        return hours + minutes / 60.0
    return 0.0

class HeaderStack:
    def __init__(self):
        self.stack = [None, None, None, None]
        self.level = 0

    def push(self, level: int, name: str):
        if level < 1 or level > 4:
            return
        self.level = level
        self.stack[level - 1] = name

    def get_header(self, level: int) -> str:
        if level <= self.level:
            return self.stack[level - 1]
        return ""

def read_clockins(directory: str) -> pd.DataFrame:
    """Reads all .org files in the given directory and extracts clock entries.
    Returns a list of rows: [start, duration, head1, head2]
    If there is only head1, head2 is empty.
    """
    rows = []
    for fname in os.listdir(directory):
        if not fname.endswith(".org"):
            continue
        headers = HeaderStack()
        with ParserOrg(directory + "/" + fname) as p:
            for item in p.parse():
                if isinstance(item, OrgHeader):
                    headers.push(item.level, item.name)
                if isinstance(item, OrgClock):
                    rows.append([item.start, time_str_to_hours(item.duration),
                                headers.get_header(1),
                                headers.get_header(2)])
    columns =['start', 'duration', 'head1', 'head2']
    return pd.DataFrame(rows, columns=columns)


def read_estimate(directory: str) -> pd.DataFrame:
    """Reads all .org files in the given directory and extracts estimate entries.
    Returns a list of rows: [duration, head1, head2]
    If there is only head1, head2 is empty.
    """
    rows = []
    for fname in os.listdir(directory):
        if not fname.endswith(".org"):
            continue
        headers = HeaderStack()
        with ParserOrg(directory + "/" + fname) as p:
            for item in p.parse():
                if isinstance(item, OrgHeader):
                    headers.push(item.level, item.name)
                if isinstance(item, OrgProperties):
                    if 'ESTIMATE' in item.values:
                        rows.append([item.values['ESTIMATE'],
                                     headers.get_header(1),
                                     headers.get_header(2)])
    columns =['duration', 'head1', 'head2']
    return pd.DataFrame(rows, columns=columns)
