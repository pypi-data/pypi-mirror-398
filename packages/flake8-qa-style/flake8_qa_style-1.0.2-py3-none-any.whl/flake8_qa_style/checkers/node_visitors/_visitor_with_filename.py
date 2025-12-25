from typing import Optional

from flake8_plugin_utils import Visitor

from flake8_qa_style.config import Config


class VisitorWithFilename(Visitor):
    def __init__(self, config: Optional[Config] = None, filename: Optional[str] = None):
        super().__init__(config=config)
        self.filename: Optional[str] = filename
