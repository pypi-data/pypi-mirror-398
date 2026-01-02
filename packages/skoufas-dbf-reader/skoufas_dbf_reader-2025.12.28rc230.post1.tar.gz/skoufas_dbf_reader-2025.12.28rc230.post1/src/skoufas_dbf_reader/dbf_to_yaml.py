"""Convert dbf files to human readable yaml"""

from __future__ import annotations

import sys

import dbfread
import yaml


def convert_dbf_to_yaml(from_dbf_file: str, to_yaml_file: str):
    """Convert dbf files to human readable yaml"""
    entries: list[dict[int, str | int]] = []
    with dbfread.DBF(filename=from_dbf_file, encoding="CP737") as dbf:
        count: int
        record: dict[str, str]
        for count, record in enumerate(dbf):
            entry: dict[int, str | int] = {}
            entry[0] = count + 1
            for name, value in record.items():
                if not value:
                    continue
                idx = int(name.replace("A", ""))
                entry[idx] = value
            entries.append(entry)

    data = {"entries": entries}
    with open(to_yaml_file, "w", encoding="utf-8") as outfile:
        yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)


def main():
    """Convert the dbf file passed to the first argument to a yaml file in the file passed as the second argument"""
    convert_dbf_to_yaml(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
