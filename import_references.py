#!/usr/bin/env python3
# populate db reference table from existing data files

import json
import csv
import re
from pathlib import Path

from submission import create_app
from submission.models import Reference


def main():
    app = create_app()
    with app.app_context():
        for filepath in Path("data").glob("*.json"):
            load_references(filepath)


def load_references(filename):
    with open(filename, "r") as inf:
        if raw := inf.read():
            data = json.loads(raw)
        else:
            print(filename, "has no references")
            return

        refs = set()
        for section in data:
            for field_name, field_value in data[section]:
                if field_name.endswith("references") and field_value:
                    refs.update(next(csv.reader([field_value], skipinitialspace=True)))
        valid_refs = []
        for ref in refs:
            if valid_format(ref):
                valid_refs.append(ref)
            else:
                print(f"{filename}: Skipping invalid ref format: {ref}")
        Reference.load_missing(valid_refs)


def valid_format(ref):
    regex = r"^pubmed:(\d+)$|^doi:10\.\d{4,9}/[-\\._;()/:a-zA-Z0-9]+$|^patent:(.+)$|^url:https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)$"
    if re.match(regex, ref):
        return True
    return False


if __name__ == "__main__":
    main()
