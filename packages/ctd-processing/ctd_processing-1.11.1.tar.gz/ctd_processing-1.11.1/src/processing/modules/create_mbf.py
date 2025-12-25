from pathlib import Path

import numpy as np
from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QPushButton,
)

import processing.modules.create_bottlefile as cb


def main(file: Path):
    app = QApplication([])

    window = main_window()
    window.show()

    app.exec()


def read_bottle_file(input):
    ending = str(Path(input[0]).suffix)

    if ending == ".bl":
        btl_file = cb.get_bottle_file(input[0], save=False)
    elif ending == ".btl":
        file = open(input[0], "r")
        btl_file = file.read()
        file.close
    else:
        pass

    Data = False
    headerlist = []
    data_lines = []
    # for line in btl_file.split("\n"):
    #     print(line)
    for line in btl_file.split("\n"):
        if Data:
            if ord(line[10]) > 57:
                headerlist = [x for x in line.strip().split(" ") if x != ""]
                continue

            data_lines.append([x for x in line.strip().split(" ") if x != ""])
        if "*END*" in line:
            Data = True

    return headerlist, data_lines


class main_window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("my App")
        button = QPushButton("File Browser")
        button.clicked.connect(
            self.get_filename_on_click
        )  # Dienstag um 9 im IOW
        self.setCentralWidget(button)

    def get_filename_on_click(self):
        self.filename = QFileDialog.getOpenFileName(
            self, "Select Bottlefile", filter="bottle files (*.btl *.bl *.mbf)"
        )

        self.headerlist, self.data_lines = read_bottle_file(self.filename)

        self.headerlist = np.array(self.headerlist)
        self.data_lines = np.array(self.data_lines)
        print(self.headerlist)
        print(self.data_lines)


class TableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]


if __name__ == "__main__":
    file = Path(
        r"E:\Arbeit\Processing\processing\src\processing\bottlefiles\test.btl"
    )
    main(file)
