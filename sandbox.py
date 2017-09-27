#!/usr/bin/env python3
import logging
import sys

from argparse import ArgumentParser
from typing import List
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

import lexical_analyzer
import datalog_parser
import relational_database
from tokens import TokenError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)


# TODO Add a 'sandbox mode' where you get a shell and can add queries facts, schemes, or whatever on the fly
# Make a query to immediately get back a response
# Type a fact to add a fact
# Save your sandbox to a text file that can be used for tests
# Load sandbox
# The sand box can use py-qt so that it is super friendly, or have the gui be an option or something


# noinspection PyAttributeOutsideInit
class Sandbox(QWidget):
    PAUSED = "Paused"
    RUNNING = "Running"

    def __init__(self, input_files: List[str] = None):
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

        # TODO Initialize Datalog Program

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Create Textbox
        # TODO add line numbers to the left side
        # TODO use vim keybindings
        self.textbox_input = QPlainTextEdit(self)
        self.textbox_input.textChanged.connect(self.analyzeInput)

        # Output box
        self.output_lab1 = QTextEdit()
        self.output_lab1.setReadOnly(True)
        self.output_lab1.setFrameStyle(QFrame.Sunken)

        self.output_lab2 = QTextEdit()
        self.output_lab2.setReadOnly(True)
        self.output_lab2.setFrameStyle(QFrame.Sunken)

        self.output_lab3 = QTextEdit()
        self.output_lab3.setReadOnly(True)
        self.output_lab3.setFrameStyle(QFrame.Sunken)

        # Create buttons
        # TODO have an evaluate rules and optimize rules button, they can be heavy
        self.button_toggle = QPushButton(self.state, self)
        self.button_toggle.clicked.connect(self.toggleParse)

        button_save = QPushButton('Save', self)
        button_save.clicked.connect(self.saveDatalog)

        # Configure Layout
        h_splitter = QSplitter(Qt.Horizontal)
        v_splitter = QSplitter(Qt.Vertical)
        button_row = QSplitter(Qt.Horizontal)

        v_splitter.addWidget(h_splitter)
        h_splitter.addWidget(self.textbox_input)
        h_splitter.addWidget(self.output_lab1)
        h_splitter.addWidget(self.output_lab2)
        h_splitter.addWidget(self.output_lab3)
        h_splitter.setSizes([200, 50, 100, 100])

        v_splitter.addWidget(button_row)
        button_row.addWidget(self.button_toggle)
        button_row.addWidget(button_save)

        hbox = QHBoxLayout(self)
        hbox.addWidget(v_splitter)
        self.setLayout(hbox)

        self.show()

    def analyzeInput(self):
        if self.state == self.RUNNING:
            # Get input textbox
            textbox_value = self.textbox_input.toPlainText()

            # Run the lexical analyzer and print output
            tokens = lexical_analyzer.scan(
                textbox_value, ignore_whitespace=False, ignore_comments=False
            )
            self.output_lab1.clear()
            self.output_lab1.append("\n".join(str(t) for t in tokens))

            # Run the datalog parser and print output
            result_lab2 = "Success!\n"
            tokens = lexical_analyzer.scan(textbox_value, ignore_comments=True, ignore_whitespace=True)
            try:
                datalog = datalog_parser.DatalogProgram(tokens)
                result_lab2 += str(datalog)
                # Create a relational database and print output
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
    arg.add_argument("test_files", nargs="*", help="The files that will be used in this test")
    args = arg.parse_args()

    # Setup debugger
    logger.setLevel(int(args.debug))

    # Start application
    sandbox = Sandbox(input_files=args.test_files)
    exit(sandbox.run())
