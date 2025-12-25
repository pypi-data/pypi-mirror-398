import os
import pathlib
import tempfile
import unittest

import ddt

from iker.common.utils.shutils import copy, listfile
from iker.common.utils.shutils import expanded_path, path_depth
from iker.common.utils.shutils import extension, extensions, stem
from iker.common.utils.shutils import glob_match
from iker.common.utils.testutils import norm_path
from iker_tests import resources_directory

work_dir = pathlib.Path.cwd
home_dir = pathlib.Path.home


@ddt.ddt
class ShUtilsTest(unittest.TestCase):
    data_extension = [
        (".", ""),
        ("..", ""),
        ("...", ""),
        (".ignored", ""),
        (".ignored.", "."),
        (".git.ignored", ".ignored"),
        ("..git.ignored", ".ignored"),
        ("..git..ignored", ".ignored"),
        ("git.ignored", ".ignored"),
        ("git.scrappy.ignored", ".ignored"),
        ("~/git.scrappy.ignored", ".ignored"),
        ("./git.scrappy.ignored", ".ignored"),
        ("../git.scrappy.ignored", ".ignored"),
        ("/~/git.scrappy.ignored", ".ignored"),
        ("/./git.scrappy.ignored", ".ignored"),
        ("/../git.scrappy.ignored", ".ignored"),
        ("/foo/bar/git.scrappy.ignored", ".ignored"),
        ("/foo/bar/~/git.scrappy.ignored", ".ignored"),
        ("/foo/bar/./git.scrappy.ignored", ".ignored"),
        ("/foo/bar/../git.scrappy.ignored", ".ignored"),
        ("/foo/bar/git.scrappy.ignored..baz.", "."),
        ("http://domain/foo/bar/git.scrappy.ignored", ".ignored"),
        ("s3://bucket/foo/bar/git.scrappy.ignored", ".ignored"),
    ]

    @ddt.idata(data_extension)
    @ddt.unpack
    def test_extension(self, data, expect):
        self.assertEqual(expect, extension(data))

    data_stem = [
        (".", "."),
        ("..", ".."),
        ("...", "..."),
        (".ignored", ".ignored"),
        (".ignored.", ".ignored"),
        (".git.ignored", ".git"),
        ("..git.ignored", "..git"),
        ("..git..ignored", "..git."),
        ("git.ignored", "git"),
        ("git.scrappy.ignored", "git.scrappy"),
        ("~/git.scrappy.ignored", "git.scrappy"),
        ("./git.scrappy.ignored", "git.scrappy"),
        ("../git.scrappy.ignored", "git.scrappy"),
        ("/~/git.scrappy.ignored", "git.scrappy"),
        ("/./git.scrappy.ignored", "git.scrappy"),
        ("/../git.scrappy.ignored", "git.scrappy"),
        ("/foo/bar/git.scrappy.ignored", "git.scrappy"),
        ("/foo/bar/~/git.scrappy.ignored", "git.scrappy"),
        ("/foo/bar/./git.scrappy.ignored", "git.scrappy"),
        ("/foo/bar/../git.scrappy.ignored", "git.scrappy"),
        ("/foo/bar/git.scrappy.ignored..baz.", "git.scrappy.ignored..baz"),
        ("http://domain/foo/bar/git.scrappy.ignored", "git.scrappy"),
        ("s3://bucket/foo/bar/git.scrappy.ignored", "git.scrappy"),
    ]

    @ddt.idata(data_stem)
    @ddt.unpack
    def test_stem(self, data, expect):
        self.assertEqual(expect, stem(data))

    data_stem__minimal = [
        (".", "."),
        ("..", ".."),
        ("...", "..."),
        (".ignored", ".ignored"),
        (".ignored.", ".ignored"),
        (".git.ignored", ".git"),
        ("..git.ignored", "..git"),
        ("..git..ignored", "..git"),
        ("git.ignored", "git"),
        ("git.scrappy.ignored", "git"),
        ("~/git.scrappy.ignored", "git"),
        ("./git.scrappy.ignored", "git"),
        ("../git.scrappy.ignored", "git"),
        ("/~/git.scrappy.ignored", "git"),
        ("/./git.scrappy.ignored", "git"),
        ("/../git.scrappy.ignored", "git"),
        ("/foo/bar/git.scrappy.ignored", "git"),
        ("/foo/bar/~/git.scrappy.ignored", "git"),
        ("/foo/bar/./git.scrappy.ignored", "git"),
        ("/foo/bar/../git.scrappy.ignored", "git"),
        ("/foo/bar/git.scrappy.ignored..baz.", "git"),
        ("http://domain/foo/bar/git.scrappy.ignored", "git"),
        ("s3://bucket/foo/bar/git.scrappy.ignored", "git"),
    ]

    @ddt.idata(data_stem__minimal)
    @ddt.unpack
    def test_stem__minimal(self, data, expect):
        self.assertEqual(expect, stem(data, minimal=True))

    data_extensions = [
        (".", []),
        ("..", []),
        ("...", []),
        (".ignored", []),
        (".ignored.", ["."]),
        (".git.ignored", [".ignored"]),
        ("..git.ignored", [".ignored"]),
        ("..git..ignored", [".ignored", "..ignored"]),
        ("git.ignored", [".ignored"]),
        ("git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
        ("~/git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
        ("./git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
        ("../git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
        ("/~/git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
        ("/./git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
        ("/../git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
        ("/foo/bar/git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
        ("/foo/bar/~/git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
        ("/foo/bar/./git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
        ("/foo/bar/../git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
        ("/foo/bar/git.scrappy.ignored..baz.", [".", ".baz.", "..baz.", ".ignored..baz.", ".scrappy.ignored..baz."]),
        ("http://domain/foo/bar/git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
        ("s3://bucket/foo/bar/git.scrappy.ignored", [".ignored", ".scrappy.ignored"]),
    ]

    @ddt.idata(data_extensions)
    @ddt.unpack
    def test_extensions(self, data, expect):
        self.assertEqual(expect, extensions(data))

    data_expanded_path = [
        (".", f"{work_dir()}"),
        ("./", f"{work_dir()}"),
        ("./foo", f"{work_dir()}/foo"),
        ("./foo.bar", f"{work_dir()}/foo.bar"),
        ("./foo/..", f"{work_dir()}"),
        ("./foo/../bar", f"{work_dir()}/bar"),
        ("./foo/../bar/..", f"{work_dir()}"),
        ("~", f"{home_dir()}"),
        ("~/", f"{home_dir()}"),
        ("~/foo", f"{home_dir()}/foo"),
        ("~/foo.bar", f"{home_dir()}/foo.bar"),
        ("~/foo/..", f"{home_dir()}"),
        ("~/foo/../bar", f"{home_dir()}/bar"),
        ("~/foo/../bar/..", f"{home_dir()}"),
        ("", f"{work_dir()}"),
        ("/", f"/"),
        ("/foo", f"/foo"),
        ("/foo.bar", f"/foo.bar"),
        ("/foo/..", f"/"),
        ("/foo/../bar", f"/bar"),
        ("/foo/../bar/..", f"/"),
        ("${DUMMY_ENV_PARAM}", f"{work_dir()}/dummy_parent"),
        ("${DUMMY_ENV_PARAM}/", f"{work_dir()}/dummy_parent"),
        ("${DUMMY_ENV_PARAM}/foo", f"{work_dir()}/dummy_parent/foo"),
        ("${DUMMY_ENV_PARAM}/foo.bar", f"{work_dir()}/dummy_parent/foo.bar"),
        ("${DUMMY_ENV_PARAM}/foo/..", f"{work_dir()}/dummy_parent"),
        ("${DUMMY_ENV_PARAM}/foo/../bar", f"{work_dir()}/dummy_parent/bar"),
        ("${DUMMY_ENV_PARAM}/foo/../bar/..", f"{work_dir()}/dummy_parent"),
        ("${LOST_ENV_PARAM}", f"{work_dir()}/${{LOST_ENV_PARAM}}"),
        ("${LOST_ENV_PARAM}/", f"{work_dir()}/${{LOST_ENV_PARAM}}"),
        ("${LOST_ENV_PARAM}/foo", f"{work_dir()}/${{LOST_ENV_PARAM}}/foo"),
        ("${LOST_ENV_PARAM}/foo.bar", f"{work_dir()}/${{LOST_ENV_PARAM}}/foo.bar"),
        ("${LOST_ENV_PARAM}/foo/..", f"{work_dir()}/${{LOST_ENV_PARAM}}"),
        ("${LOST_ENV_PARAM}/foo/../bar", f"{work_dir()}/${{LOST_ENV_PARAM}}/bar"),
        ("${LOST_ENV_PARAM}/foo/../bar/..", f"{work_dir()}/${{LOST_ENV_PARAM}}"),
        ("${EMPTY_ENV_PARAM}", f"{work_dir()}"),
        ("${EMPTY_ENV_PARAM}/", f"/"),
        ("${EMPTY_ENV_PARAM}/foo", f"/foo"),
        ("${EMPTY_ENV_PARAM}/foo.bar", f"/foo.bar"),
        ("${EMPTY_ENV_PARAM}/foo/..", f"/"),
        ("${EMPTY_ENV_PARAM}/foo/../bar", f"/bar"),
        ("${EMPTY_ENV_PARAM}/foo/../bar/..", f"/"),
    ]

    @ddt.idata(data_expanded_path)
    @ddt.unpack
    def test_expanded_path(self, data, expect):
        os.environ["DUMMY_ENV_PARAM"] = "dummy_parent"
        os.environ["EMPTY_ENV_PARAM"] = ""
        self.assertEqual(norm_path(expect), norm_path(expanded_path(data)))

    data_path_depth = [
        (".", ".", 0),
        ("..", "..", 0),
        ("/..", "/", 0),
        ("/", "/..", 0),
        ("foo/..", "bar/..", 0),
        ("/foo/bar/../..", "/foo/../bar/..", 0),
        ("/foo/../bar/..", "/foo/bar/../..", 0),
        ("././././.", "", 0),
        ("", "././././.", 0),
        ("foo/bar/baz", "foo/bar/baz/", 0),
        ("foo/bar/baz/", "foo/bar/baz", 0),

        ("foo", "foo/bar", 1),
        ("foo", "foo/bar/baz", 2),
        ("foo", "foo/bar/../baz", 1),
        ("foo", "foo/bar/../baz/..", 0),
        ("/foo", "/foo/bar", 1),
        ("/foo", "/foo/bar/baz", 2),
        ("/foo", "/foo/bar/../baz", 1),
        ("/foo", "/foo/bar/../baz/..", 0),

        ("foo", "bar", -1),
        ("foo/bar", "foo/baz", -1),
    ]

    @ddt.idata(data_path_depth)
    @ddt.unpack
    def test_path_depth(self, root, child, expect):
        self.assertEqual(path_depth(root, child), expect)

    data_glob_match = [
        (
            ["file.foo", "file.bar", "file.baz", "file.foo.bar", "file.foo.baz", "file.bar.baz", "file.foo.bar.baz"],
            ["*.foo", "*.bar"],
            ["*.foo.bar"],
            ["file.foo", "file.bar"],
        ),
        (
            ["file.foo", "file.bar", "file.baz", "file.foo.bar", "file.foo.baz", "file.bar.baz", "file.foo.bar.baz"],
            [],
            ["*.foo.bar"],
            ["file.foo", "file.bar", "file.baz", "file.foo.baz", "file.bar.baz", "file.foo.bar.baz"],
        ),
        (
            ["file.foo", "file.bar", "file.baz", "file.foo.bar", "file.foo.baz", "file.bar.baz", "file.foo.bar.baz"],
            ["*.foo"],
            [],
            ["file.foo"],
        ),
        (
            ["file.foo", "file.bar", "file.baz", "file.foo.bar", "file.foo.baz", "file.bar.baz", "file.foo.bar.baz"],
            ["*.foo"],
            ["*.foo"],
            [],
        ),
        (
            ["file.foo", "file.bar", "file.baz", "file.foo.bar", "file.foo.baz", "file.bar.baz", "file.foo.bar.baz"],
            [],
            [],
            ["file.foo", "file.bar", "file.baz", "file.foo.bar", "file.foo.baz", "file.bar.baz", "file.foo.bar.baz"],
        ),
        (
            ["file.foo", "file.bar", "file.baz", "file.foo.bar", "file.foo.baz", "file.bar.baz", "file.foo.bar.baz"],
            [".foo"],
            [],
            [],
        ),
        (
            ["file.foo", "file.bar", "file.baz", "file.foo.bar", "file.foo.baz", "file.bar.baz", "file.foo.bar.baz"],
            [],
            [".foo"],
            ["file.foo", "file.bar", "file.baz", "file.foo.bar", "file.foo.baz", "file.bar.baz", "file.foo.bar.baz"],
        ),
    ]

    @ddt.idata(data_glob_match)
    @ddt.unpack
    def test_glob_match(self, names, include_patterns, exclude_patterns, expect):
        self.assertSetEqual(set(map(norm_path, glob_match(names, include_patterns, exclude_patterns))),
                            set(map(norm_path, expect)))

    data_listfile = [
        (
            "unittest/shutils",
            [],
            [],
            0,
            [
                "unittest/shutils/dir.baz/file.foo.bar",
                "unittest/shutils/dir.baz/file.foo.baz",
                "unittest/shutils/dir.baz/file.bar.baz",
                "unittest/shutils/dir.foo/file.bar",
                "unittest/shutils/dir.foo/file.baz",
                "unittest/shutils/dir.foo/file.foo",
                "unittest/shutils/dir.foo/dir.foo.bar/file.foo.bar",
                "unittest/shutils/dir.foo/dir.foo.bar/file.foo.baz",
                "unittest/shutils/dir.foo/dir.foo.bar/file.bar.baz",
                "unittest/shutils/dir.foo/dir.foo.bar/dir.foo.bar.baz/file.foo.bar.baz",
            ],
        ),
        (
            "unittest/shutils/dir.foo",
            [],
            [],
            0,
            [
                "unittest/shutils/dir.foo/file.bar",
                "unittest/shutils/dir.foo/file.baz",
                "unittest/shutils/dir.foo/file.foo",
                "unittest/shutils/dir.foo/dir.foo.bar/file.foo.bar",
                "unittest/shutils/dir.foo/dir.foo.bar/file.foo.baz",
                "unittest/shutils/dir.foo/dir.foo.bar/file.bar.baz",
                "unittest/shutils/dir.foo/dir.foo.bar/dir.foo.bar.baz/file.foo.bar.baz",
            ],
        ),
        (
            "unittest/shutils/dir.baz",
            [],
            [],
            0,
            [
                "unittest/shutils/dir.baz/file.foo.bar",
                "unittest/shutils/dir.baz/file.foo.baz",
                "unittest/shutils/dir.baz/file.bar.baz",
            ],
        ),
        (
            "unittest/shutils",
            ["*.foo", "*.bar"],
            ["*.foo.bar"],
            0,
            [
                "unittest/shutils/dir.foo/file.bar",
                "unittest/shutils/dir.foo/file.foo",
            ],
        ),
        (
            "unittest/shutils",
            ["*.foo", "*.bar"],
            [],
            0,
            [
                "unittest/shutils/dir.baz/file.foo.bar",
                "unittest/shutils/dir.foo/file.bar",
                "unittest/shutils/dir.foo/file.foo",
                "unittest/shutils/dir.foo/dir.foo.bar/file.foo.bar",
            ],
        ),
        (
            "unittest/shutils",
            [],
            ["*.baz"],
            0,
            [
                "unittest/shutils/dir.baz/file.foo.bar",
                "unittest/shutils/dir.foo/file.bar",
                "unittest/shutils/dir.foo/file.foo",
                "unittest/shutils/dir.foo/dir.foo.bar/file.foo.bar",
            ],
        ),
        (
            "unittest/shutils",
            [],
            [],
            2,
            [
                "unittest/shutils/dir.baz/file.foo.bar",
                "unittest/shutils/dir.baz/file.foo.baz",
                "unittest/shutils/dir.baz/file.bar.baz",
                "unittest/shutils/dir.foo/file.bar",
                "unittest/shutils/dir.foo/file.baz",
                "unittest/shutils/dir.foo/file.foo",
            ],
        ),
        (
            "unittest/shutils/dir.foo/file.bar",
            [],
            [],
            0,
            [
                "unittest/shutils/dir.foo/file.bar",
            ],
        ),
        (
            "unittest/shutils/dir.foo/file.bar",
            [],
            [],
            2,
            [
                "unittest/shutils/dir.foo/file.bar",
            ],
        ),
        (
            "unittest/shutils/dir.foo/file.bar",
            ["*.foo", "*.bar"],
            ["*.baz"],
            0,
            [
                "unittest/shutils/dir.foo/file.bar",
            ],
        ),
        (
            "unittest/shutils/dir.foo/file.bar",
            ["*.foo"],
            [],
            0,
            [],
        ),
        (
            "unittest/shutils/dir.foo/file.bar",
            [],
            ["*.bar"],
            0,
            [],
        ),
    ]

    @ddt.idata(data_listfile)
    @ddt.unpack
    def test_listfile(self, path, include_patterns, exclude_patterns, depth, expect):
        self.assertSetEqual(set(map(norm_path, listfile(os.path.join(resources_directory, path),
                                                        include_patterns=include_patterns,
                                                        exclude_patterns=exclude_patterns,
                                                        depth=depth))),
                            set(map(norm_path, map(lambda x: os.path.join(resources_directory, x), expect))))

    data_copy = [
        (
            "unittest/shutils",
            "unittest/shutils",
            [],
            [],
            0,
            [
                "unittest/shutils/dir.baz/file.foo.bar",
                "unittest/shutils/dir.baz/file.foo.baz",
                "unittest/shutils/dir.baz/file.bar.baz",
                "unittest/shutils/dir.foo/file.bar",
                "unittest/shutils/dir.foo/file.baz",
                "unittest/shutils/dir.foo/file.foo",
                "unittest/shutils/dir.foo/dir.foo.bar/file.foo.bar",
                "unittest/shutils/dir.foo/dir.foo.bar/file.foo.baz",
                "unittest/shutils/dir.foo/dir.foo.bar/file.bar.baz",
                "unittest/shutils/dir.foo/dir.foo.bar/dir.foo.bar.baz/file.foo.bar.baz",
            ],
        ),
        (
            "unittest/shutils/dir.foo",
            "unittest/shutils/dir.foo",
            [],
            [],
            0,
            [
                "unittest/shutils/dir.foo/file.bar",
                "unittest/shutils/dir.foo/file.baz",
                "unittest/shutils/dir.foo/file.foo",
                "unittest/shutils/dir.foo/dir.foo.bar/file.foo.bar",
                "unittest/shutils/dir.foo/dir.foo.bar/file.foo.baz",
                "unittest/shutils/dir.foo/dir.foo.bar/file.bar.baz",
                "unittest/shutils/dir.foo/dir.foo.bar/dir.foo.bar.baz/file.foo.bar.baz",
            ],
        ),
        (
            "unittest/shutils/dir.baz",
            "unittest/shutils/dir.baz",
            [],
            [],
            0,
            [
                "unittest/shutils/dir.baz/file.foo.bar",
                "unittest/shutils/dir.baz/file.foo.baz",
                "unittest/shutils/dir.baz/file.bar.baz",
            ],
        ),
        (
            "unittest/shutils",
            "unittest/shutils",
            ["*.foo", "*.bar"],
            ["*.foo.bar"],
            0,
            [
                "unittest/shutils/dir.foo/file.bar",
                "unittest/shutils/dir.foo/file.foo",
            ],
        ),
        (
            "unittest/shutils",
            "unittest/shutils",
            ["*.foo", "*.bar"],
            [],
            0,
            [
                "unittest/shutils/dir.baz/file.foo.bar",
                "unittest/shutils/dir.foo/file.bar",
                "unittest/shutils/dir.foo/file.foo",
                "unittest/shutils/dir.foo/dir.foo.bar/file.foo.bar",
            ],
        ),
        (
            "unittest/shutils",
            "unittest/shutils",
            [],
            ["*.baz"],
            0,
            [
                "unittest/shutils/dir.baz/file.foo.bar",
                "unittest/shutils/dir.foo/file.bar",
                "unittest/shutils/dir.foo/file.foo",
                "unittest/shutils/dir.foo/dir.foo.bar/file.foo.bar",
            ],
        ),
        (
            "unittest/shutils",
            "unittest/shutils",
            [],
            [],
            2,
            [
                "unittest/shutils/dir.baz/file.foo.bar",
                "unittest/shutils/dir.baz/file.foo.baz",
                "unittest/shutils/dir.baz/file.bar.baz",
                "unittest/shutils/dir.foo/file.bar",
                "unittest/shutils/dir.foo/file.baz",
                "unittest/shutils/dir.foo/file.foo",
            ],
        ),
        (
            "unittest/shutils/dir.foo/file.bar",
            "unittest/shutils/dir.foo/file.bar",
            [],
            [],
            0,
            [
                "unittest/shutils/dir.foo/file.bar",
            ],
        ),
        (
            "unittest/shutils/dir.foo/file.bar",
            "unittest/shutils/dir.foo/file.bar",
            [],
            [],
            2,
            [
                "unittest/shutils/dir.foo/file.bar",
            ],
        ),
        (
            "unittest/shutils/dir.foo/file.bar",
            "unittest/shutils/dir.foo/file.bar",
            ["*.foo", "*.bar"],
            ["*.baz"],
            0,
            [
                "unittest/shutils/dir.foo/file.bar",
            ],
        ),
        (
            "unittest/shutils/dir.foo/file.bar",
            "unittest/shutils/dir.foo/file.bar",
            ["*.foo"],
            [],
            0,
            [],
        ),
        (
            "unittest/shutils/dir.foo/file.bar",
            "unittest/shutils/dir.foo/file.bar",
            [],
            ["*.bar"],
            0,
            [],
        ),
    ]

    @ddt.idata(data_copy)
    @ddt.unpack
    def test_copy(self, src, dst, include_patterns, exclude_patterns, depth, expect):
        with tempfile.TemporaryDirectory() as temp_directory:
            copy(os.path.join(resources_directory, src),
                 os.path.join(temp_directory, dst),
                 include_patterns=include_patterns,
                 exclude_patterns=exclude_patterns,
                 depth=depth)

            self.assertSetEqual(set(map(norm_path, listfile(os.path.join(temp_directory, dst)))),
                                set(map(norm_path, map(lambda x: os.path.join(temp_directory, x), expect))))
