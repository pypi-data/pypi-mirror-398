import glob
import re
from pathlib import Path


def read_files(folder: Path):
    data_part = ""
    combined_header = ""
    operators = []
    get_cruisename = True
    cruisename = ""
    platform = ""
    for filename in glob.iglob(f"{folder}/*.btl"):
        if get_cruisename:
            f = open(filename, "r+")
            for line in f:
                if line[:2] == "**":
                    if "Cruise" in line:
                        cruisename = line[2:].strip()
                    if "Platform" in line:
                        platform = line[2:].strip()
            get_cruisename = False
            f.close
        f = open(filename, "r+")
        data = False
        for line in f:
            if "*END*" in line:
                data = True
                continue
            if not data:
                if (
                    re.search(r"/d/d:/d/d:/d/d", line) is not None
                ):  # does not work >:( regex 1.01? um testen
                    continue
                if line[:2] == "* ":
                    combined_header += line  # lon lat raus / Prossesing Informationen von der ersten file nehmen / sensoren erstmal raus
                if line[:2] == "**":
                    if "Operator" in line:
                        operator = line.split("=")[1].strip()
                        if any(operator in s for s in operators):
                            continue
                        operators.append(operator)
            if line.strip()[0].isalpha():
                continue

            data_part += line
        f.close()
    combined_header += "Operators = "
    for operator in operators:
        combined_header += str(operator)

    # print(data_part)
    print(operators)
    print(platform, cruisename)
    print(combined_header)


if __name__ == "__main__":
    read_files(r"E:\Arbeit\Processing\processing\src\processing\bottlefiles")
