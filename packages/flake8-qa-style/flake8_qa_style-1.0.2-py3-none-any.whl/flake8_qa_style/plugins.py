import argparse
import ast
from typing import Callable, List, Optional

from flake8.options.manager import OptionManager
from flake8_plugin_utils import Plugin, Visitor

from flake8_qa_style.checkers.line_checkers import FileStartChecker
from flake8_qa_style.checkers.node_visitors import (
    AnnotationVisitor,
    AssertVisitor,
    FunctionCallVisitor
)

from .config import Config


def str_to_bool(string):
    return string.lower() in ('true', 'yes', 't', '1')


class QAStylePlugin(Plugin):
    name = 'flake8_qa_style'
    version = '1.0.2'

    visitors = [
        AnnotationVisitor,
        FunctionCallVisitor,
        AssertVisitor,
    ]

    line_checkers = [
        FileStartChecker
    ]

    def __init__(self, tree: ast.AST, filename: str, lines: list[str]):
        super().__init__(tree)
        self.filename = filename
        self.lines = lines

    def run(self):
        for line_checker_cls in self.line_checkers:
            line_checker = line_checker_cls(filename=self.filename, lines=self.lines)
            line_checker.check()
            for error in line_checker.errors:
                yield self._error(error)

        for visitor_cls in self.visitors:
            visitor = self._create_visitor(visitor_cls, filename=self.filename)
            visitor.visit(self._tree)
            for error in visitor.errors:
                yield self._error(error)

    @classmethod
    def _create_visitor(cls, visitor_cls: Callable, filename: Optional[str] = None) -> Visitor:
        if cls.config is None:
            return visitor_cls(filename=filename)

        return visitor_cls(config=cls.config, filename=filename)

    @classmethod
    def add_options(cls, option_manager: OptionManager):
        option_manager.add_option(
            '--skip-property-return-annotation',
            type=str,
            default='false',
            parse_from_config=True,
            help='Flag to skip return value annotation check. '
                 '(Default: False)',
        )

    @classmethod
    def parse_options_to_config(
        cls, option_manager: OptionManager, options: argparse.Namespace, args: List[str]
    ) -> Config:
        return Config(
            skip_property_return_annotation=str_to_bool(options.skip_property_return_annotation),
        )
