import os.path
import unittest

import ddt

from iker.common.utils.config import Config, ConfigVisitor
from iker_tests import resources_directory


@ddt.ddt
class ConfigTest(unittest.TestCase):

    def test_builtin_init(self):
        config = Config()
        self.assertEqual(len(config), 0)

    def test_set(self):
        config = Config()

        tuples = [
            ("dummy_section_1", "dummy_option_1", "True"),
            ("dummy_section_1", "dummy_option_2", "False"),
            ("dummy_section_1", "dummy_option_3", "1"),
            ("dummy_section_1", "dummy_option_4", "-1"),
            ("dummy_section_1", "dummy_option_5", "1.0"),
            ("dummy_section_1", "dummy_option_6", "-1.0"),
            ("dummy_section_1", "dummy_option_7", "1.e+0"),
            ("dummy_section_1", "dummy_option_8", "-1.e-0"),
            ("dummy_section_1", "dummy_option_9", "dummy_value_alpha"),
        ]

        for section, option, value in tuples:
            config.set(section, option, value)

        for section, option, value in tuples:
            self.assertTrue(config.has_section(section))
            self.assertTrue(config.has(section, option))
            self.assertEqual(config.get(section, option), value)

    def test_update(self):
        config = Config()

        tuples = [
            ("dummy_section_1", "dummy_option_1", "True"),
            ("dummy_section_1", "dummy_option_2", "False"),
            ("dummy_section_1", "dummy_option_3", "1"),
            ("dummy_section_1", "dummy_option_4", "-1"),
            ("dummy_section_1", "dummy_option_5", "1.0"),
            ("dummy_section_1", "dummy_option_6", "-1.0"),
            ("dummy_section_1", "dummy_option_7", "1.e+0"),
            ("dummy_section_1", "dummy_option_8", "-1.e-0"),
            ("dummy_section_1", "dummy_option_9", "dummy_value"),
            ("dummy_section_2", "dummy_option_1", "True"),
            ("dummy_section_2", "dummy_option_2", "False"),
            ("dummy_section_2", "dummy_option_3", "1"),
            ("dummy_section_2", "dummy_option_4", "-1"),
            ("dummy_section_2", "dummy_option_5", "1.0"),
            ("dummy_section_2", "dummy_option_6", "-1.0"),
            ("dummy_section_2", "dummy_option_7", "1.e+0"),
            ("dummy_section_2", "dummy_option_8", "-1.e-0"),
            ("dummy_section_2", "dummy_option_9", "dummy_value"),
        ]

        config.update(tuples)

        self.assertEqual(config.get("dummy_section_1", "dummy_option_1"), "True")
        self.assertEqual(config.get("dummy_section_1", "dummy_option_2"), "False")
        self.assertEqual(config.get("dummy_section_1", "dummy_option_3"), "1")
        self.assertEqual(config.get("dummy_section_1", "dummy_option_4"), "-1")
        self.assertEqual(config.get("dummy_section_1", "dummy_option_5"), "1.0")
        self.assertEqual(config.get("dummy_section_1", "dummy_option_6"), "-1.0")
        self.assertEqual(config.get("dummy_section_1", "dummy_option_7"), "1.e+0")
        self.assertEqual(config.get("dummy_section_1", "dummy_option_8"), "-1.e-0")
        self.assertEqual(config.get("dummy_section_1", "dummy_option_9"), "dummy_value")
        self.assertEqual(config.get("dummy_section_2", "dummy_option_1"), "True")
        self.assertEqual(config.get("dummy_section_2", "dummy_option_2"), "False")
        self.assertEqual(config.get("dummy_section_2", "dummy_option_3"), "1")
        self.assertEqual(config.get("dummy_section_2", "dummy_option_4"), "-1")
        self.assertEqual(config.get("dummy_section_2", "dummy_option_5"), "1.0")
        self.assertEqual(config.get("dummy_section_2", "dummy_option_6"), "-1.0")
        self.assertEqual(config.get("dummy_section_2", "dummy_option_7"), "1.e+0")
        self.assertEqual(config.get("dummy_section_2", "dummy_option_8"), "-1.e-0")
        self.assertEqual(config.get("dummy_section_2", "dummy_option_9"), "dummy_value")

        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_1"), True)
        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_2"), False)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_3"), 1)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_4"), -1)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_5"), 1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_6"), -1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_7"), 1.e+0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_8"), -1.e-0)
        self.assertEqual(config.get("dummy_section_1", "dummy_option_9"), "dummy_value")
        self.assertEqual(config.getboolean("dummy_section_2", "dummy_option_1"), True)
        self.assertEqual(config.getboolean("dummy_section_2", "dummy_option_2"), False)
        self.assertEqual(config.getint("dummy_section_2", "dummy_option_3"), 1)
        self.assertEqual(config.getint("dummy_section_2", "dummy_option_4"), -1)
        self.assertEqual(config.getfloat("dummy_section_2", "dummy_option_5"), 1.0)
        self.assertEqual(config.getfloat("dummy_section_2", "dummy_option_6"), -1.0)
        self.assertEqual(config.getfloat("dummy_section_2", "dummy_option_7"), 1.e+0)
        self.assertEqual(config.getfloat("dummy_section_2", "dummy_option_8"), -1.e-0)
        self.assertEqual(config.get("dummy_section_2", "dummy_option_9"), "dummy_value")

        self.assertIsNone(config.getboolean("dummy_section_1", "miss_dummy_option_1"))
        self.assertIsNone(config.getboolean("dummy_section_1", "miss_dummy_option_2"))
        self.assertIsNone(config.getint("dummy_section_1", "miss_dummy_option_3"))
        self.assertIsNone(config.getint("dummy_section_1", "miss_dummy_option_4"))
        self.assertIsNone(config.getfloat("dummy_section_1", "miss_dummy_option_5"))
        self.assertIsNone(config.getfloat("dummy_section_1", "miss_dummy_option_6"))
        self.assertIsNone(config.getfloat("dummy_section_1", "miss_dummy_option_7"))
        self.assertIsNone(config.getfloat("dummy_section_1", "miss_dummy_option_8"))
        self.assertIsNone(config.get("dummy_section_1", "miss_dummy_option_9"))
        self.assertIsNone(config.getboolean("dummy_section_3", "dummy_option_1"))
        self.assertIsNone(config.getboolean("dummy_section_3", "dummy_option_2"))
        self.assertIsNone(config.getint("dummy_section_3", "dummy_option_3"))
        self.assertIsNone(config.getint("dummy_section_3", "dummy_option_4"))
        self.assertIsNone(config.getfloat("dummy_section_3", "dummy_option_5"))
        self.assertIsNone(config.getfloat("dummy_section_3", "dummy_option_6"))
        self.assertIsNone(config.getfloat("dummy_section_3", "dummy_option_7"))
        self.assertIsNone(config.getfloat("dummy_section_3", "dummy_option_8"))
        self.assertIsNone(config.get("dummy_section_3", "dummy_option_9"))
        self.assertEqual(config.getboolean("dummy_section_1", "miss_dummy_option_1", True), True)
        self.assertEqual(config.getboolean("dummy_section_1", "miss_dummy_option_2", False), False)
        self.assertEqual(config.getint("dummy_section_1", "miss_dummy_option_3", 1), 1)
        self.assertEqual(config.getint("dummy_section_1", "miss_dummy_option_4", -1), -1)
        self.assertEqual(config.getfloat("dummy_section_1", "miss_dummy_option_5", 1.0), 1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "miss_dummy_option_6", -1.0), -1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "miss_dummy_option_7", 1.e+0), 1.e+0)
        self.assertEqual(config.getfloat("dummy_section_1", "miss_dummy_option_8", -1.e-0), -1.e-0)
        self.assertEqual(config.get("dummy_section_1", "miss_dummy_option_9", "dummy_value"), "dummy_value")
        self.assertEqual(config.getboolean("dummy_section_3", "dummy_option_1", True), True)
        self.assertEqual(config.getboolean("dummy_section_3", "dummy_option_2", False), False)
        self.assertEqual(config.getint("dummy_section_3", "dummy_option_3", 1), 1)
        self.assertEqual(config.getint("dummy_section_3", "dummy_option_4", -1), -1)
        self.assertEqual(config.getfloat("dummy_section_3", "dummy_option_5", 1.0), 1.0)
        self.assertEqual(config.getfloat("dummy_section_3", "dummy_option_6", -1.0), -1.0)
        self.assertEqual(config.getfloat("dummy_section_3", "dummy_option_7", 1.e+0), 1.e+0)
        self.assertEqual(config.getfloat("dummy_section_3", "dummy_option_8", -1.e-0), -1.e-0)
        self.assertEqual(config.get("dummy_section_3", "dummy_option_9", "dummy_value"), "dummy_value")

        self.assertEqual(config.tuples(), tuples)
        self.assertEqual(config.sections(), ["dummy_section_1", "dummy_section_2"])
        self.assertEqual(config.options("dummy_section_1"),
                         [
                             "dummy_option_1",
                             "dummy_option_2",
                             "dummy_option_3",
                             "dummy_option_4",
                             "dummy_option_5",
                             "dummy_option_6",
                             "dummy_option_7",
                             "dummy_option_8",
                             "dummy_option_9",
                         ])
        self.assertEqual(config.options("dummy_section_2"),
                         [
                             "dummy_option_1",
                             "dummy_option_2",
                             "dummy_option_3",
                             "dummy_option_4",
                             "dummy_option_5",
                             "dummy_option_6",
                             "dummy_option_7",
                             "dummy_option_8",
                             "dummy_option_9",
                         ])
        self.assertEqual(config.options("dummy_section_3"), [])

    def test_update__overwrite_allowed(self):
        config = Config()

        tuples = [
            ("dummy_section_1", "dummy_option_1", "True"),
            ("dummy_section_1", "dummy_option_2", "False"),
            ("dummy_section_1", "dummy_option_3", "1"),
            ("dummy_section_1", "dummy_option_4", "-1"),
            ("dummy_section_1", "dummy_option_5", "1.0"),
            ("dummy_section_1", "dummy_option_6", "-1.0"),
            ("dummy_section_1", "dummy_option_7", "1.e+0"),
            ("dummy_section_1", "dummy_option_8", "-1.e-0"),
            ("dummy_section_1", "dummy_option_9", "dummy_value_alpha"),
        ]

        config.update(tuples)

        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_1"), True)
        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_2"), False)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_3"), 1)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_4"), -1)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_5"), 1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_6"), -1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_7"), 1.e+0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_8"), -1.e-0)
        self.assertEqual(config.get("dummy_section_1", "dummy_option_9"), "dummy_value_alpha")

        tuples = [
            ("dummy_section_1", "dummy_option_1", "False"),
            ("dummy_section_1", "dummy_option_2", "True"),
            ("dummy_section_1", "dummy_option_3", "-1"),
            ("dummy_section_1", "dummy_option_4", "1"),
            ("dummy_section_1", "dummy_option_5", "-1.0"),
            ("dummy_section_1", "dummy_option_6", "1.0"),
            ("dummy_section_1", "dummy_option_7", "-1.e-0"),
            ("dummy_section_1", "dummy_option_8", "1.e+0"),
            ("dummy_section_1", "dummy_option_9", "dummy_value_beta"),
        ]

        config.update(tuples, overwrite=True)

        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_1"), False)
        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_2"), True)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_3"), -1)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_4"), 1)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_5"), -1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_6"), 1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_7"), -1.e-0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_8"), 1.e+0)
        self.assertEqual(config.get("dummy_section_1", "dummy_option_9"), "dummy_value_beta")

    def test_update__overwrite_prohibited(self):
        config = Config()

        tuples = [
            ("dummy_section_1", "dummy_option_1", "True"),
            ("dummy_section_1", "dummy_option_2", "False"),
            ("dummy_section_1", "dummy_option_3", "1"),
            ("dummy_section_1", "dummy_option_4", "-1"),
            ("dummy_section_1", "dummy_option_5", "1.0"),
            ("dummy_section_1", "dummy_option_6", "-1.0"),
            ("dummy_section_1", "dummy_option_7", "1.e+0"),
            ("dummy_section_1", "dummy_option_8", "-1.e-0"),
            ("dummy_section_1", "dummy_option_9", "dummy_value_alpha"),
        ]

        config.update(tuples)

        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_1"), True)
        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_2"), False)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_3"), 1)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_4"), -1)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_5"), 1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_6"), -1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_7"), 1.e+0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_8"), -1.e-0)
        self.assertEqual(config.get("dummy_section_1", "dummy_option_9"), "dummy_value_alpha")

        tuples = [
            ("dummy_section_1", "dummy_option_1", "False"),
            ("dummy_section_1", "dummy_option_2", "True"),
            ("dummy_section_1", "dummy_option_3", "-1"),
            ("dummy_section_1", "dummy_option_4", "1"),
            ("dummy_section_1", "dummy_option_5", "-1.0"),
            ("dummy_section_1", "dummy_option_6", "1.0"),
            ("dummy_section_1", "dummy_option_7", "-1.e-0"),
            ("dummy_section_1", "dummy_option_8", "1.e+0"),
            ("dummy_section_1", "dummy_option_9", "dummy_value_beta"),
        ]

        config.update(tuples, overwrite=False)

        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_1"), True)
        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_2"), False)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_3"), 1)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_4"), -1)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_5"), 1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_6"), -1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_7"), 1.e+0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_8"), -1.e-0)
        self.assertEqual(config.get("dummy_section_1", "dummy_option_9"), "dummy_value_alpha")

    def test_restore(self):
        config = Config()

        tuples = [
            ("dummy_section_1", "dummy_option_1", "True"),
            ("dummy_section_1", "dummy_option_2", "False"),
            ("dummy_section_1", "dummy_option_3", "1"),
            ("dummy_section_1", "dummy_option_4", "-1"),
            ("dummy_section_1", "dummy_option_5", "1.0"),
            ("dummy_section_1", "dummy_option_6", "-1.0"),
            ("dummy_section_1", "dummy_option_7", "1.e+0"),
            ("dummy_section_1", "dummy_option_8", "-1.e-0"),
            ("dummy_section_1", "dummy_option_9", "dummy_value_alpha"),
        ]

        config.update(tuples)

        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_1"), True)
        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_2"), False)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_3"), 1)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_4"), -1)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_5"), 1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_6"), -1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_7"), 1.e+0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_8"), -1.e-0)
        self.assertEqual(config.get("dummy_section_1", "dummy_option_9"), "dummy_value_alpha")

        self.assertFalse(config.restore())
        self.assertEqual(len(config), 0)

    def test_restore__from_file(self):
        config = Config(os.path.join(resources_directory, "unittest/config/config.cfg"))

        tuples = [
            ("dummy_section_1", "dummy_option_1", "True"),
            ("dummy_section_1", "dummy_option_2", "False"),
            ("dummy_section_1", "dummy_option_3", "1"),
            ("dummy_section_1", "dummy_option_4", "-1"),
            ("dummy_section_1", "dummy_option_5", "1.0"),
            ("dummy_section_1", "dummy_option_6", "-1.0"),
            ("dummy_section_1", "dummy_option_7", "1.e+0"),
            ("dummy_section_1", "dummy_option_8", "-1.e-0"),
            ("dummy_section_1", "dummy_option_9", "dummy_value_alpha"),
        ]

        self.assertTrue(config.restore())
        self.assertEqual(len(config), len(tuples))

        for section, option, value in tuples:
            self.assertTrue(config.has_section(section))
            self.assertTrue(config.has(section, option))
            self.assertEqual(config.get(section, option), value)

    def test_restore__file_not_found(self):
        config = Config(os.path.join(resources_directory, "unittest/config/missing_config.cfg"))

        self.assertFalse(config.restore())
        self.assertEqual(len(config), 0)

    def test_persist(self):
        config = Config()

        tuples = [
            ("dummy_section_1", "dummy_option_1", "True"),
            ("dummy_section_1", "dummy_option_2", "False"),
            ("dummy_section_1", "dummy_option_3", "1"),
            ("dummy_section_1", "dummy_option_4", "-1"),
            ("dummy_section_1", "dummy_option_5", "1.0"),
            ("dummy_section_1", "dummy_option_6", "-1.0"),
            ("dummy_section_1", "dummy_option_7", "1.e+0"),
            ("dummy_section_1", "dummy_option_8", "-1.e-0"),
            ("dummy_section_1", "dummy_option_9", "dummy_value_alpha"),
        ]

        config.update(tuples)

        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_1"), True)
        self.assertEqual(config.getboolean("dummy_section_1", "dummy_option_2"), False)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_3"), 1)
        self.assertEqual(config.getint("dummy_section_1", "dummy_option_4"), -1)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_5"), 1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_6"), -1.0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_7"), 1.e+0)
        self.assertEqual(config.getfloat("dummy_section_1", "dummy_option_8"), -1.e-0)
        self.assertEqual(config.get("dummy_section_1", "dummy_option_9"), "dummy_value_alpha")

        self.assertFalse(config.persist())
        self.assertEqual(len(config), len(tuples))


@ddt.ddt
class ConfigVisitorTest(unittest.TestCase):

    def test(self):
        config = Config()

        tuples = [
            ("dummy_section", "foo", "dummy_value"),
            ("dummy_section", "foo.bar", "True"),
            ("dummy_section", "foo.baz", "False"),
            ("dummy_section", "bar.foo.baz", "1"),
            ("dummy_section", "bar.baz.foo", "-1"),
            ("dummy_section", "baz.foo.foo", "1.0"),
            ("dummy_section", "baz.bar.bar", "-1.0"),
            ("dummy_section", "baz.bar.foo", "1.e+0"),
            ("dummy_section", "baz.foo.bar", "-1.e-0"),
        ]

        config.update(tuples)

        visitor = ConfigVisitor(config, "dummy_section")

        self.assertEqual(str(visitor.foo), "dummy_value"),
        self.assertEqual(bool(visitor.foo.bar), True),
        self.assertEqual(bool(visitor.foo.baz), False),
        self.assertEqual(int(visitor.bar.foo.baz), 1),
        self.assertEqual(int(visitor.bar.baz.foo), -1),
        self.assertEqual(float(visitor.baz.foo.foo), 1.0),
        self.assertEqual(float(visitor.baz.bar.bar), -1.0),
        self.assertEqual(float(visitor.baz.bar.foo), 1.e+0),
        self.assertEqual(float(visitor.baz.foo.bar), -1.e-0),

        self.assertEqual(str(visitor["foo"]), "dummy_value"),
        self.assertEqual(bool(visitor["foo"]["bar"]), True),
        self.assertEqual(bool(visitor["foo"]["baz"]), False),
        self.assertEqual(int(visitor["bar"]["foo"]["baz"]), 1),
        self.assertEqual(int(visitor["bar"]["baz"]["foo"]), -1),
        self.assertEqual(float(visitor["baz"]["foo"]["foo"]), 1.0),
        self.assertEqual(float(visitor["baz"]["bar"]["bar"]), -1.0),
        self.assertEqual(float(visitor["baz"]["bar"]["foo"]), 1.e+0),
        self.assertEqual(float(visitor["baz"]["foo"]["bar"]), -1.e-0),

    def test__specific_separator(self):
        config = Config()

        tuples = [
            ("dummy_section", "foo", "dummy_value"),
            ("dummy_section", "foo/bar", "True"),
            ("dummy_section", "foo/baz", "False"),
            ("dummy_section", "bar/foo/baz", "1"),
            ("dummy_section", "bar/baz/foo", "-1"),
            ("dummy_section", "baz/foo/foo", "1.0"),
            ("dummy_section", "baz/bar/bar", "-1.0"),
            ("dummy_section", "baz/bar/foo", "1.e+0"),
            ("dummy_section", "baz/foo/bar", "-1.e-0"),
        ]

        config.update(tuples)

        visitor = ConfigVisitor(config, "dummy_section", separator="/")

        self.assertEqual(str(visitor.foo), "dummy_value"),
        self.assertEqual(bool(visitor.foo.bar), True),
        self.assertEqual(bool(visitor.foo.baz), False),
        self.assertEqual(int(visitor.bar.foo.baz), 1),
        self.assertEqual(int(visitor.bar.baz.foo), -1),
        self.assertEqual(float(visitor.baz.foo.foo), 1.0),
        self.assertEqual(float(visitor.baz.bar.bar), -1.0),
        self.assertEqual(float(visitor.baz.bar.foo), 1.e+0),
        self.assertEqual(float(visitor.baz.foo.bar), -1.e-0),

        self.assertEqual(str(visitor["foo"]), "dummy_value"),
        self.assertEqual(bool(visitor["foo"]["bar"]), True),
        self.assertEqual(bool(visitor["foo"]["baz"]), False),
        self.assertEqual(int(visitor["bar"]["foo"]["baz"]), 1),
        self.assertEqual(int(visitor["bar"]["baz"]["foo"]), -1),
        self.assertEqual(float(visitor["baz"]["foo"]["foo"]), 1.0),
        self.assertEqual(float(visitor["baz"]["bar"]["bar"]), -1.0),
        self.assertEqual(float(visitor["baz"]["bar"]["foo"]), 1.e+0),
        self.assertEqual(float(visitor["baz"]["foo"]["bar"]), -1.e-0),
