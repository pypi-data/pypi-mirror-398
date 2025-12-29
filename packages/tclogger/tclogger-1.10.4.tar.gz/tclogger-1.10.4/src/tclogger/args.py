import argparse


class MergedArgParser:
    """Usage:
    ```python
    arg_parser = MergedArgParser(ParserClass1, ParserClass2, ...)
    arg_parser = add_parser_class(ParserClass3, ...)
    args = arg_parser.parse_args()
    ```
    """

    def __init__(self, *parser_classes):
        self.parser_classes = parser_classes
        self.construct_parsers()

    def construct_parsers(self):
        self.parsers = [cls(add_help=False) for cls in self.parser_classes]

    def add_parser_class(self, *args):
        self.parser_classes += args
        self.construct_parsers()

    def parse_args(self, args=None):
        self.args = argparse.ArgumentParser(parents=self.parsers).parse_args()
        return self.args
