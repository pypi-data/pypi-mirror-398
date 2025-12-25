from flake8_qa_style.checkers.line_checkers import FileStartChecker


def test_empty_file() -> None:
    line_checker = FileStartChecker(None, [])
    line_checker.check()
    assert len(line_checker.errors) == 0


def test_file_with_blank_line() -> None:
    line_checker = FileStartChecker(None, ["\n"])
    line_checker.check()
    assert len(line_checker.errors) == 1


def test_file_without_blank_line() -> None:
    line_checker = FileStartChecker(None, ["print('Hello world')"])
    line_checker.check()
    assert len(line_checker.errors) == 0
