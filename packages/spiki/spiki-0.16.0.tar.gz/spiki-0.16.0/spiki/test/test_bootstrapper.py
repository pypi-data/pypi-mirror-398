#!/usr/bin/env python
#   encoding: utf-8

# Copyright (C) 2025 D E Haynes
# This file is part of spiki.

# Spiki is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Spiki is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with spiki.
# If not, see <https://www.gnu.org/licenses/>.

import importlib.resources
import pathlib
import tempfile
import textwrap
import tomllib
import unittest

import spiki
from spiki.plugin import Phase
from spiki.renderer import Renderer
from spiki.visitor import Visitor


class VisitorTests(unittest.TestCase):

    def test_example_atom(self):
        plugin_types = [
            "spiki.plugins.bootstrapper:Bootstrapper",
            "spiki.plugins.writer:Writer",
        ]
        examples = importlib.resources.files("spiki.examples")
        witness = []
        with (
            tempfile.TemporaryDirectory() as output_name,
            Visitor(*plugin_types) as visitor,
        ):
            visitor.options = dict(
                output=pathlib.Path(output_name).resolve(),
                paths=[examples.joinpath("atom")],
            )

            self.assertFalse(visitor.state)
            for change in visitor.walk(*visitor.options["paths"]):
                witness.append(change)

            output_path = pathlib.Path(output_name)
            files = list(output_path.glob("*.py"))

            self.assertEqual(len(files), 1)
            text = files[0].read_text()

            pyz = output_path.with_suffix(".pyz")
            self.assertTrue(pyz.exists())

        self.assertEqual(len(visitor.state), 1, visitor.state)
        path = list(visitor.state)[0]
        self.assertEqual("__main__.py", path.name)

        check = visitor.state[path].text
        self.assertIsInstance(check, str)
        self.assertIn("import argparse", check)
        self.assertIn("class Bootstrapper", check)
        self.assertIn("def main(args):", check)
        self.assertEqual(check.count("run()"), 2)

        self.assertEqual(len([i for i in witness if i.phase == Phase.EXTEND]), 1)
        self.assertEqual(files[0].name, "__main__.py")
        self.assertEqual(text, check)
