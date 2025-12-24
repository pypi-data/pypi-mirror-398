#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import argparse
import builtins
import io
import os
import sys
import threading

try:
    from PyQt6 import QtWidgets, QtGui
    from PyQt6.QtCore import QTimer, QMetaObject, Qt, Q_ARG, pyqtSignal, QObject

    PYQT = True
except ImportError:
    PYQT = False

import shlex

from chgksuite.common import (
    DefaultNamespace,
    get_lastdir,
    get_source_dirs,
)
from chgksuite.version import __version__
from chgksuite.cli import ArgparseBuilder, single_action

LANGS = ["by", "by_tar", "en", "kz_cyr", "ru", "sr", "ua", "uz", "uz_cyr"] + ["custom"]

debug = False


class InputRequester(QObject):
    """Helper to request input from main thread via signal."""
    input_requested = pyqtSignal(str)

    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.response = None
        self.event = threading.Event()
        self.input_requested.connect(self._show_dialog)

    def _show_dialog(self, prompt):
        text, ok = QtWidgets.QInputDialog.getText(
            self.parent_window, "Input Required", prompt
        )
        self.response = text if ok else ""
        self.event.set()

    def request_input(self, prompt=""):
        self.event.clear()
        self.response = None
        self.input_requested.emit(prompt)
        self.event.wait()  # Block until dialog is closed
        return self.response


class VarWrapper(object):
    def __init__(self, name, var):
        self.name = name
        self.var = var


class QString:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class RadioGroupVar:
    def __init__(self):
        self.radio_buttons = []

    def append(self, rb, value):
        self.radio_buttons.append((value, rb))

    def get(self):
        for val, rb in self.radio_buttons:
            if rb.isChecked():
                return val
            

def init_layout(frame, layout, spacing=0):
    layout.setSpacing(spacing)
    layout.setContentsMargins(spacing, spacing, spacing, spacing)


class OpenFileDialog(object):
    def __init__(self, label, var, folder=False, lastdir=None, filetypes=None):
        self.label = label
        self.var = var
        self.folder = folder
        self.lastdir = lastdir
        self.filetypes = filetypes

    def __call__(self):
        if self.folder:
            output = QtWidgets.QFileDialog.getExistingDirectory(
                None, "Select Folder", self.lastdir or ""
            )
        else:
            output, _ = QtWidgets.QFileDialog.getOpenFileName(
                None,
                "Select File",
                self.lastdir or "",
                ";;".join(
                    [
                        "{} ({})".format(ft[0], " ".join(ft[1]))
                        for ft in (self.filetypes or [])
                    ]
                ),
            )
        self.var.set(output or "")
        self.label.setText(os.path.basename(output or ""))


class ParserWrapper(object):
    def __init__(self, parser, parent=None, lastdir=None):
        self.parent = parent
        self.lastdir = lastdir if not parent else parent.lastdir
        if self.parent:
            self.parent.children.append(self)
            self.frame = QtWidgets.QWidget(self.parent.frame)
            self.layout = QtWidgets.QVBoxLayout(self.frame)
            init_layout(self.frame, self.layout)
            self.parent.layout.addWidget(self.frame)
            self.frame.hide()
            self.advanced_frame = QtWidgets.QWidget(self.parent.advanced_frame)
            self.advanced_layout = QtWidgets.QVBoxLayout(self.advanced_frame)
            init_layout(self.advanced_frame, self.advanced_layout)
            self.parent.advanced_layout.addWidget(self.advanced_frame)
            self.advanced_frame.hide()
        else:
            self.init_qt()
        self.parser = parser
        self.subparsers_var = None
        self.cmdline_call = None
        self.children = []
        self.vars = []

    def _list_vars(self):
        result = []
        for var in self.vars:
            result.append((var.name, var.var.get()))
        if self.subparsers_var:
            chosen_parser_name = self.subparsers_var.get()

            chosen_parser = [
                x
                for x in self.subparsers.parsers
                if x.parser.prog.split()[-1] == chosen_parser_name
            ][0]
            result.append(("", chosen_parser_name))
            result.extend(chosen_parser._list_vars())
        return result

    def build_command_line_call(self):
        result = []
        result_to_print = []
        for tup in self._list_vars():
            to_append = None
            if tup[0].startswith("--"):
                if tup[1] == "true":
                    to_append = tup[0]
                elif not tup[1] or tup[1] == "false":
                    continue
                else:
                    to_append = [tup[0], str(tup[1])]
            else:
                to_append = tup[1]
            if isinstance(to_append, list):
                result.extend(to_append)
                if "password" in tup[0]:
                    result_to_print.append(tup[0])
                    result_to_print.append("********")
                else:
                    result_to_print.extend(to_append)
            else:
                result.append(to_append)
                result_to_print.append(to_append)
        print("Command line call: {}".format(shlex.join(result_to_print)))
        return result

    def ok_button_press(self):
        self.cmdline_call = self.build_command_line_call()
        if not self.cmdline_call:
            return

        # Clear output and disable button
        self.output_text.clear()
        self.ok_button.setEnabled(False)

        # Capture stdout/stderr in a thread
        self.output_buffer = io.StringIO()
        self.worker_done = False

        # Create input requester for GUI input dialogs
        self.input_requester = InputRequester(self.window)

        def worker():
            old_stdout, old_stderr = sys.stdout, sys.stderr
            old_input = builtins.input
            sys.stdout = sys.stderr = self.output_buffer
            builtins.input = self.input_requester.request_input
            try:
                _, resourcedir = get_source_dirs()
                args = DefaultNamespace(self.parser.parse_args(self.cmdline_call))
                single_action(args, False, resourcedir)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr
                builtins.input = old_input
                self.worker_done = True

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()
        self.poll_output()

    def poll_output(self):
        content = self.output_buffer.getvalue()
        if content:
            self.output_text.setPlainText(content)
            self.output_text.verticalScrollBar().setValue(
                self.output_text.verticalScrollBar().maximum()
            )
        if not self.worker_done:
            QTimer.singleShot(100, self.poll_output)
        else:
            self.ok_button.setEnabled(True)
            self.output_text.append("\n--- Готово ---")

    def toggle_advanced_frame(self):
        value = self.advanced_checkbox_var.isChecked()
        if value:
            self.advanced_frame.show()
        else:
            self.advanced_frame.hide()
        self.window.resize(self.window.minimumSizeHint())

    def init_qt(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.window = QtWidgets.QWidget()
        self.window.setWindowTitle("chgksuite v{}".format(__version__))
        self.window_layout = QtWidgets.QVBoxLayout(self.window)
        init_layout(self.window, self.window_layout, spacing=10)
        self.frame = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(self.frame)
        init_layout(self.frame, self.layout)
        self.button_frame = QtWidgets.QWidget()
        self.button_layout = QtWidgets.QVBoxLayout(self.button_frame)
        init_layout(self.button_frame, self.button_layout)
        self.advanced_frame = QtWidgets.QWidget()
        self.advanced_layout = QtWidgets.QVBoxLayout(self.advanced_frame)
        init_layout(self.advanced_frame, self.advanced_layout)
        self.window_layout.addWidget(self.frame)
        self.window_layout.addWidget(self.button_frame)
        self.window_layout.addWidget(self.advanced_frame)
        self.ok_button = QtWidgets.QPushButton("Запустить")
        self.ok_button.clicked.connect(self.ok_button_press)
        self.button_layout.addWidget(self.ok_button)
        self.advanced_checkbox_var = QtWidgets.QCheckBox("Показать дополнительные настройки")
        self.advanced_checkbox_var.stateChanged.connect(self.toggle_advanced_frame)
        self.button_layout.addWidget(self.advanced_checkbox_var)
        self.advanced_frame.hide()

        # Output text widget
        self.output_text = QtWidgets.QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QtGui.QFont("Courier", 10))
        self.output_text.setMinimumHeight(150)
        self.window_layout.addWidget(self.output_text)

    def add_argument(self, *args, **kwargs):
        if kwargs.pop("advanced", False):
            frame = self.advanced_frame
            layout = self.advanced_layout
        else:
            frame = self.frame
            layout = self.layout

        if kwargs.pop("hide", False):
            self.parser.add_argument(*args, **kwargs)
            return

        caption = kwargs.pop("caption", None) or args[0]
        argtype = kwargs.pop("argtype", None)
        filetypes = kwargs.pop("filetypes", None)

        if not argtype:
            if kwargs.get("action") == "store_true":
                argtype = "checkbutton"
            elif args[0] in {"filename", "folder"}:
                argtype = args[0]
            else:
                argtype = "entry"

        if argtype == "checkbutton":
            var = QString()
            var.set("false")
            innerframe = QtWidgets.QWidget(frame)
            innerlayout = QtWidgets.QHBoxLayout(innerframe)
            init_layout(innerframe, innerlayout)
            checkbutton = QtWidgets.QCheckBox(caption, innerframe)
            innerlayout.addWidget(checkbutton)
            layout.addWidget(innerframe)
            checkbutton.stateChanged.connect(
                lambda state, var=var: var.set("true" if state else "false")
            )
            self.vars.append(VarWrapper(name=args[0], var=var))

        elif argtype == "radiobutton":
            var = QString()
            var.set(kwargs["default"])
            innerframe = QtWidgets.QWidget(frame)
            innerlayout = QtWidgets.QHBoxLayout(innerframe)
            init_layout(innerframe, innerlayout)
            label = QtWidgets.QLabel(caption, innerframe)
            innerlayout.addWidget(label)
            button_group = QtWidgets.QButtonGroup(innerframe)
            for ch in kwargs["choices"]:
                radio = QtWidgets.QRadioButton(ch, innerframe)
                if ch == kwargs["default"]:
                    radio.setChecked(True)
                button_group.addButton(radio)
                radio.toggled.connect(
                    lambda checked, var=var, ch=ch: var.set(ch) if checked else None
                )
                innerlayout.addWidget(radio)
            layout.addWidget(innerframe)
            self.vars.append(VarWrapper(name=args[0], var=var))

        elif argtype in {"filename", "folder"}:
            text = "(имя файла)" if argtype == "filename" else "(имя папки)"
            button_text = "Открыть файл" if argtype == "filename" else "Открыть папку"
            var = QString()
            innerframe = QtWidgets.QWidget(frame)
            innerlayout = QtWidgets.QHBoxLayout(innerframe)
            init_layout(innerframe, innerlayout)
            label = QtWidgets.QLabel(caption, innerframe)
            innerlayout.addWidget(label)
            label = QtWidgets.QLabel(text, innerframe)
            innerlayout.addWidget(label)
            button = QtWidgets.QPushButton(button_text, innerframe)
            button.clicked.connect(
                OpenFileDialog(
                    label,
                    var,
                    folder=argtype == "folder",
                    lastdir=self.lastdir,
                    filetypes=filetypes,
                )
            )
            innerlayout.addWidget(button)
            layout.addWidget(innerframe)
            self.vars.append(VarWrapper(name=args[0], var=var))

        elif argtype == "entry":
            var = QString()
            var.set(kwargs.get("default") or "")
            innerframe = QtWidgets.QWidget(frame)
            innerlayout = QtWidgets.QHBoxLayout(innerframe)
            init_layout(innerframe, innerlayout)
            label = QtWidgets.QLabel(caption, innerframe)
            innerlayout.addWidget(label)
            entry_show = "*" if "password" in args[0] else ""
            entry = QtWidgets.QLineEdit(innerframe)
            entry.setText(str(var.get()))
            if entry_show:
                entry.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            innerlayout.addWidget(entry)
            layout.addWidget(innerframe)
            entry.textChanged.connect(var.set)
            self.vars.append(VarWrapper(name=args[0], var=var))
        self.parser.add_argument(*args, **kwargs)

    def add_subparsers(self, *args, **kwargs):
        subparsers = self.parser.add_subparsers(*args, **kwargs)
        self.subparsers_var = RadioGroupVar()
        self.subparsers = SubparsersWrapper(subparsers, parent=self)
        return self.subparsers

    def show_frame(self):
        for child in self.parent.children:
            child.frame.hide()
            child.advanced_frame.hide()
        self.frame.show()
        self.advanced_frame.show()
        parent = self.parent
        while parent.parent:
            parent = parent.parent
        parent.window.resize(parent.window.minimumSizeHint())

    def parse_args(self, *args, **kwargs):
        argv = sys.argv[1:]
        if not argv:
            self.window.show()
            self.app.exec()
            # Window closed by user, exit cleanly
            sys.exit(0)
        return self.parser.parse_args(*args, **kwargs)


class SubparsersWrapper(object):
    def __init__(self, subparsers, parent):
        self.subparsers = subparsers
        self.parent = parent
        self.frame = QtWidgets.QWidget(self.parent.frame)
        self.parent.layout.addWidget(self.frame)
        self.parsers = []
        self.layout = QtWidgets.QHBoxLayout(self.frame)
        init_layout(self.frame, self.layout)

    def add_parser(self, *args, **kwargs):
        caption = kwargs.pop("caption", None) or args[0]
        parser = self.subparsers.add_parser(*args, **kwargs)
        pw = ParserWrapper(parser=parser, parent=self.parent)
        self.parsers.append(pw)
        radio = QtWidgets.QRadioButton(caption, self.frame)
        self.parent.subparsers_var.append(radio, args[0])
        radio.toggled.connect(
            lambda checked, pw=pw: pw.show_frame() if checked else None
        )
        self.layout.addWidget(radio)
        return pw

def app():
    _, resourcedir = get_source_dirs()
    ld = get_lastdir()
    use_wrapper = len(sys.argv) == 1 and PYQT
    if use_wrapper:
        # GUI mode: window stays open, subprocess runs via ok_button_press()
        parser = argparse.ArgumentParser(prog="chgksuite")
        parser = ParserWrapper(parser, lastdir=ld)
        ArgparseBuilder(parser, use_wrapper).build()
        parser.parse_args()  # Shows window, runs event loop until closed
    else:
        # CLI mode: run directly
        parser = argparse.ArgumentParser(prog="chgksuite")
        ArgparseBuilder(parser, use_wrapper).build()
        args = DefaultNamespace(parser.parse_args())
        single_action(args, False, resourcedir)
