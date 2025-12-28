import argparse
import unittest
from collections import namedtuple
from pathlib import Path
from unittest import mock

from comexdown import cli
from comexdown.tables import AUX_TABLES


class TestCliFunctions(unittest.TestCase):

    def test_set_parser(self):
        parser = cli.set_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)

    def test_expand_years(self):
        years = cli.expand_years(["2010:2019", "2000:2005"])
        self.assertListEqual(
            years,
            [y for y in range(2010, 2020)] + [y for y in range(2000, 2006)]
        )
        years = cli.expand_years(["2000:2005", "2010:2019"])
        self.assertListEqual(
            years,
            [y for y in range(2000, 2006)] + [y for y in range(2010, 2020)]
        )
        years = cli.expand_years(["2000:2005", "2010"])
        self.assertListEqual(
            years,
            [y for y in range(2000, 2006)] + [2010]
        )
        years = cli.expand_years(["2010", "2000:2005"])
        self.assertListEqual(
            years,
            [2010] + [y for y in range(2000, 2006)]
        )
        years = cli.expand_years(["2010", "2005:2000"])
        self.assertListEqual(
            years,
            [2010] + [2005, 2004, 2003, 2002, 2001, 2000]
        )

    @mock.patch("comexdown.cli.set_parser")
    def test_main(self, mock_set_parser):
        cli.main()
        mock_set_parser.assert_called()
        parser = mock_set_parser.return_value
        parser.parse_args.assert_called()
        args = parser.parse_args.return_value
        args.func.assert_called()


class TestCliDownloadTrade(unittest.TestCase):

    def setUp(self):
        self.parser = cli.set_parser()
        self.Args = namedtuple("Args", ["exp", "imp", "mun"])
        self.o = "./data"


class TestCliDownloadCode(unittest.TestCase):

    def setUp(self):
        self.parser = cli.set_parser()
        self.o = Path(".", "data")

    @mock.patch("comexdown.cli.print_code_tables")
    def test_download_table_print_code_tables(self, mock_print_code_tables):
        self.args = self.parser.parse_args(
            [
                "table",
            ]
        )
        self.args.func(self.args)
        mock_print_code_tables.assert_called()


if __name__ == "__main__":
    unittest.main()
