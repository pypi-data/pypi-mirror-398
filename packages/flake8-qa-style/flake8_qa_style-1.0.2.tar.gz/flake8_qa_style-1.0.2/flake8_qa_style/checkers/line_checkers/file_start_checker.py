from flake8_qa_style.checkers.line_checkers._checker_with_lines import (
    CheckerWithLines
)
from flake8_qa_style.errors import NoBlankFileStart


class FileStartChecker(CheckerWithLines):
    def check(self) -> None:
        if not self.lines:
            return

        if not self.lines[0].strip():
            self.errors.append(NoBlankFileStart(lineno=1, col_offset=0))
