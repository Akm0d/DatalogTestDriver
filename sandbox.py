#!/usr/bin/env python3
import logging
import sys

from argparse import ArgumentParser
from os import path
from typing import List
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from subprocess import check_output

import lexical_analyzer
import datalog_parser
import relational_database
from tokens import TokenError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)

temp_file = path.join(path.abspath('.'), '.input.tmp')


class Sandbox(QWidget):
    PAUSED = "Paused"
    RUNNING = "Running"

    def __init__(self, input_files: List[str] = None,
                 lab1_binary: str = None, lab2_binary: str = None, lab3_binary: str = None):
        self.binary_lab1 = lab1_binary if path.isfile(str(lab1_binary)) else None
        self.binary_lab2 = lab2_binary if path.isfile(str(lab2_binary)) else None
        self.binary_lab3 = lab3_binary if path.isfile(str(lab3_binary)) else None
        # Set up QT5
        self.state = self.RUNNING
        self.app = QApplication(sys.argv)
        super(Sandbox, self).__init__()
        self.title = "Datalog Program Sandbox"
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.margin = 20
        self.initUI()
        self.analyzeInput()

        # TODO import each file as a datalog program and add it to the master datalog program
        input_datalog = None
        for i in input_files:
            tokens = lexical_analyzer.scan(i)
            try:
                new_datalog = datalog_parser.DatalogProgram(tokens)
                if input_datalog is None:
                    input_datalog = new_datalog
                else:
                    input_datalog += new_datalog
            except TokenError as t:
                logger.debug(t)
        self.textbox_input.appendPlainText(input_datalog.print_datalog_file() if input_datalog else '')

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Create Textboxes
        splitter_text = QSplitter(Qt.Horizontal)
        # TODO add line numbers to the left side
        # TODO use vim keybindings
        self.textbox_input = QPlainTextEdit(self)
        self.textbox_input.textChanged.connect(self.analyzeInput)

        # TODO have a generator or something that combines each text widget with a label
        self.output_lab1 = QTextEdit()
        self.output_lab1.setReadOnly(True)
        self.output_lab1.setFrameStyle(QFrame.Sunken)

        self.output_lab2 = QTextEdit()
        self.output_lab2.setReadOnly(True)
        self.output_lab2.setFrameStyle(QFrame.Sunken)

        self.output_lab3 = QTextEdit()
        self.output_lab3.setReadOnly(True)
        self.output_lab3.setFrameStyle(QFrame.Sunken)

        self.student_output_lab1 = QTextEdit()
        self.student_output_lab1.setReadOnly(True)
        self.student_output_lab1.setFrameStyle(QFrame.Sunken)

        self.student_output_lab2 = QTextEdit()
        self.output_lab2.setReadOnly(True)
        self.output_lab2.setFrameStyle(QFrame.Sunken)

        self.student_output_lab3 = QTextEdit()
        self.output_lab3.setReadOnly(True)
        self.output_lab3.setFrameStyle(QFrame.Sunken)

        splitter_text.addWidget(self.textbox_input)
        splitter_text.addWidget(self.output_lab1)
        splitter_text.addWidget(self.student_output_lab1)
        splitter_text.addWidget(self.output_lab2)
        splitter_text.addWidget(self.student_output_lab2)
        splitter_text.addWidget(self.output_lab3)
        splitter_text.addWidget(self.student_output_lab3)
        splitter_text.setSizes([200, 50, 100, 100])

        # Check boxes
        check_boxes = QListWidget()
        lab_boxes = QListWidget()
        self.check_whitespace = QListWidgetItem("Ignore Whitespace")
        self.check_comments = QListWidgetItem("Ignore Comments")

        self.check_whitespace.setCheckState(Qt.Unchecked)
        self.check_comments.setCheckState(Qt.Unchecked)

        check_boxes.addItem(self.check_comments)
        check_boxes.addItem(self.check_whitespace)

        check_boxes.clicked.connect(self.analyzeInput)
        check_boxes.setMaximumHeight(60)

        self.check_lab1 = QListWidgetItem("Lexical Analyzer")
        self.check_lab2 = QListWidgetItem("Datalog Parser")
        self.check_lab3 = QListWidgetItem("Relational Database")

        self.check_lab1.setCheckState(Qt.Checked)
        self.check_lab2.setCheckState(Qt.Checked)
        self.check_lab3.setCheckState(Qt.Checked)

        lab_boxes.addItem(self.check_lab1)
        lab_boxes.addItem(self.check_lab2)
        lab_boxes.addItem(self.check_lab3)

        lab_boxes.clicked.connect(self.showHideLabs)
        lab_boxes.setMaximumHeight(60)

        # Create buttons
        button_row = QSplitter(Qt.Horizontal)
        # TODO have an evaluate rules and optimize rules button, they can be heavy
        # TODO Or just time them out if they run too long
        self.button_toggle = QPushButton(self.state, self)
        self.button_toggle.clicked.connect(self.toggleParse)

        button_save = QPushButton('Save', self)
        button_save.clicked.connect(self.saveDatalog)

        button_row.addWidget(lab_boxes)
        button_row.addWidget(check_boxes)
        button_row.addWidget(self.button_toggle)
        button_row.addWidget(button_save)

        # Main
        splitter_main = QSplitter(Qt.Vertical)

        splitter_main.addWidget(splitter_text)
        splitter_main.addWidget(button_row)

        hbox = QHBoxLayout(self)
        hbox.addWidget(splitter_main)
        self.setLayout(hbox)

        self.show()

    def showHideLabs(self):
        if self.check_lab1.checkState():
            self.output_lab1.show()
            self.student_output_lab1.show()
        else:
            self.output_lab1.hide()
            self.student_output_lab1.hide()
        if self.check_lab2.checkState():
            self.output_lab2.show()
            self.student_output_lab2.show()
        else:
            self.output_lab2.hide()
            self.student_output_lab2.hide()
        if self.check_lab3.checkState():
            self.output_lab3.show()
            self.student_output_lab3.show()
        else:
            self.output_lab3.hide()
            self.student_output_lab3.hide()

    def analyzeInput(self):
        if self.state == self.RUNNING:
            # Get input textbox
            textbox_value = self.textbox_input.toPlainText()
            with open(temp_file, 'w+') as temp:
                temp.write(textbox_value)

            # Run the lexical analyzer and print output
            # TODO Have checkboxes for ignoring whitespace and comments
            tokens = lexical_analyzer.scan(
                textbox_value,
                ignore_whitespace=self.check_whitespace.checkState(),
                ignore_comments=self.check_comments.checkState()
            )

            self.output_lab1.clear()
            self.output_lab1.append("\n".join(str(t) for t in tokens))
            self.output_lab1.append("Total Tokens = %s\n" % len(tokens))
            result_lab3 = ''

            self.student_output_lab1.clear()
            self.student_output_lab1.append(
                str(check_output("%s %s" % (self.binary_lab1, temp_file), shell=True, timeout=2), 'utf-8')
            )

            # Run the datalog parser and print output
            if self.check_lab2.checkState() or self.check_lab3.checkState():
                result_lab2 = "Success!\n"
                tokens = lexical_analyzer.scan(textbox_value, ignore_comments=True, ignore_whitespace=True)
                try:
                    datalog = datalog_parser.DatalogProgram(tokens)
                    result_lab2 += str(datalog)
                    # Create a relational database and print output
                    if self.check_lab3.checkState():
                        rdbms = relational_database.RDBMS(datalog)

                        for datalog_query in datalog.queries.queries:
                            rdbms.rdbms[datalog_query] = rdbms.evaluate_query(datalog_query)

                        result_lab3 = str(rdbms)

                except TokenError as t:
                    result_lab2 = 'Failure!\n  {}'.format(t)
                    result_lab3 = 'Failure!\n  {}'.format(t)
                self.output_lab2.clear()
                self.output_lab2.append(result_lab2)

                self.output_lab3.clear()
                self.output_lab3.append(result_lab3)

    def toggleParse(self):
        if self.state == self.PAUSED:
            self.state = self.RUNNING
            self.button_toggle.setText(self.RUNNING)
            self.analyzeInput()
        elif self.state == self.RUNNING:
            self.state = self.PAUSED
            self.button_toggle.setText(self.PAUSED)

    def saveDatalog(self):
        name = QFileDialog.getSaveFileName(
            self, "QFileDialog.getSaveFileName()", "", "All Files (*);;Text Files (*.txt)"
        )[0]

        if not name:
            return

        logger.debug("Saving file to {}".format(name))
        with open(name, 'w+') as save_file:
            save_file.write("tacos")

    def run(self) -> int:
        """
        :return: The exit status of Qt5
        """
        return self.app.exec_()


if __name__ == '__main__':
    # Parse command line options
    arg = ArgumentParser(description="Experiment with Datalog")
    arg.add_argument('-d', '--debug', help="The logging debug level to use", default=logging.NOTSET, metavar='LEVEL')
    arg.add_argument('--lab-1', help="Path to a lexical analyzer binary", default=None)
    arg.add_argument('--lab-2', help="Path to a datalog parser binary", default=None)
    arg.add_argument('--lab-3', help="Path to a relational database binary", default=None)
    arg.add_argument('--lab-4', help="Path to a datalog interpeter binary", default=None)
    arg.add_argument('--lab-5', help="Path to a rule optimizer binary", default=None)
    arg.add_argument("test_files", nargs="*", help="The files that will be used in this test")
    args = arg.parse_args()

    # Setup debugger
    logger.setLevel(int(args.debug))

    # Start application
    sandbox = Sandbox(input_files=args.test_files, lab1_binary=args.lab_1, lab2_binary=args.lab_2,
                      lab3_binary=args.lab_3)
    exit(sandbox.run())
