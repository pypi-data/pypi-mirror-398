import unittest

import ddt

from iker.common.utils.dtutils import dt_utc
from iker.common.utils.strutils import is_blank, is_empty, is_none
from iker.common.utils.strutils import make_params_string, parse_params_string
from iker.common.utils.strutils import parse_bool, parse_float_or, parse_int_or
from iker.common.utils.strutils import str_conv
from iker.common.utils.strutils import strip_margin
from iker.common.utils.strutils import trim_to_empty, trim_to_none


@ddt.ddt
class StrUtilsTest(unittest.TestCase):
    data_is_none = [
        (None, True),
        ("", False),
        (" ", False),
        ("\t", False),
        ("dummy", False),
    ]

    @ddt.idata(data_is_none)
    @ddt.unpack
    def test_is_none(self, data, expect):
        self.assertEqual(expect, is_none(data))

    data_is_empty = [
        (None, True),
        ("", True),
        (" ", False),
        ("\t", False),
        ("dummy", False),
    ]

    @ddt.idata(data_is_empty)
    @ddt.unpack
    def test_is_empty(self, data, expect):
        self.assertEqual(expect, is_empty(data))

    data_is_blank = [
        (None, True),
        ("", True),
        (" ", True),
        ("  ", True),
        ("\t", True),
        ("\n", True),
        ("dummy", False),
    ]

    @ddt.idata(data_is_blank)
    @ddt.unpack
    def test_is_blank(self, data, expect):
        self.assertEqual(expect, is_blank(data))

    data_trim_to_none = [
        (None, None, None),
        ("", None, None),
        (" ", None, None),
        ("\n", None, None),
        ("\t", None, None),
        (" dummy!", None, "dummy!"),
        ("dummy! ", None, "dummy!"),
        (" dummy!", "!", " dummy"),
        ("dummy! ", "!", "dummy! "),
    ]

    @ddt.idata(data_trim_to_none)
    @ddt.unpack
    def test_trim_to_none(self, data, chars, expect):
        self.assertEqual(expect, trim_to_none(data, chars))

    data_trim_to_empty = [
        (None, None, ""),
        ("", None, ""),
        (" ", None, ""),
        ("\n", None, ""),
        ("\t", None, ""),
        (" dummy!", None, "dummy!"),
        ("dummy! ", None, "dummy!"),
        (" dummy!", "!", " dummy"),
        ("dummy! ", "!", "dummy! "),
    ]

    @ddt.idata(data_trim_to_empty)
    @ddt.unpack
    def test_trim_to_empty(self, data, chars, expect):
        self.assertEqual(expect, trim_to_empty(data, chars))

    data_parse_bool = [
        (None, False),
        (0, False),
        (1, True),
        (2, True),
        (0.0, False),
        (1.0, True),
        (2.0, True),
        ("", False),
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("yes", True),
        ("Yes", True),
        ("YES", True),
        ("on", True),
        ("On", True),
        ("ON", True),
        ("1", True),
        ("y", True),
        ("Y", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("no", False),
        ("No", False),
        ("NO", False),
        ("off", False),
        ("Off", False),
        ("OFF", False),
        ("0", False),
        ("n", False),
        ("N", False),
        (True, True),
        (False, False),
    ]

    @ddt.idata(data_parse_bool)
    @ddt.unpack
    def test_parse_bool(self, data, expect):
        self.assertEqual(expect, parse_bool(data))

    data_parse_int_or = [
        (False, 0),
        (True, 1),
        (0, 0),
        (1, 1),
        (-1, -1),
        (0.0, 0),
        (1.0, 1),
        (-1.0, -1),
        (0.0e0, 0),
        (+1.0e+0, 1),
        (-1.0e-0, -1),
        ("0", 0),
        ("1", 1),
        ("-1", -1),
        ("0xFF", 0xFF),
        ("0xF0", 0xF0),
        ("0o77", 0o77),
        ("0o70", 0o70),
        ("0b11", 0b11),
        ("0b10", 0b10),
    ]

    @ddt.idata(data_parse_int_or)
    @ddt.unpack
    def test_parse_int_or(self, data, expect):
        self.assertEqual(expect, parse_int_or(data))

    data_parse_float_or = [
        (False, 0.0),
        (True, 1.0),
        (0, 0.0),
        (1, 1.0),
        (-1, -1.0),
        (0.0, 0.0),
        (1.0, 1.0),
        (-1.0, -1.0),
        (0.0e0, 0.0),
        (+1.0e+0, 1.0),
        (-1.0e-0, -1.0),
        ("0", 0.0),
        ("1", 1.0),
        ("-1", -1.0),
        ("0.0", 0.0),
        ("1.0", 1.0),
        ("-1.0", -1.0),
        ("0.0e0", 0.0),
        ("+1.0e+0", 1.0),
        ("-1.0e-0", -1.0),
    ]

    @ddt.idata(data_parse_float_or)
    @ddt.unpack
    def test_parse_float_or(self, data, expect):
        self.assertEqual(expect, parse_float_or(data))

    data_str_conv = [
        (1, 1),
        (0, 0),
        (-1, -1),
        (1.0, 1.0),
        (1.0e10, 1.0e10),
        (0.0, 0.0),
        (-1.0e-10, -1.0e-10),
        (True, True),
        (False, False),
        (dt_utc(1970, 1, 1, 0, 0, 0), dt_utc(1970, 1, 1, 0, 0, 0)),
        (dt_utc(2020, 12, 31, 23, 59, 59), dt_utc(2020, 12, 31, 23, 59, 59)),
        ("1", 1),
        ("0", 0),
        ("-1", -1),
        ("1.0", 1.0),
        ("1.0e10", 1.0e10),
        ("0.0", 0.0),
        ("-1.0", -1.0),
        ("-1.0e-10", -1.0e-10),
        ("True", True),
        ("False", False),
        ("1970-01-01T00:00:00", dt_utc(1970, 1, 1, 0, 0, 0)),
        ("2020-12-31T23:59:59", dt_utc(2020, 12, 31, 23, 59, 59)),
        ("dummy", "dummy"),
    ]

    @ddt.idata(data_str_conv)
    @ddt.unpack
    def test_str_conv(self, data, expect):
        self.assertEqual(expect, str_conv(data))

    data_parse_params_string = [
        ("", {}),
        (" \t", {}),
        (",-,", {}),
        ("foo=bar", {"foo": "bar"}),
        (
            "dummy_key_1=dummy_value_1,dummy_key_2=dummy_value_2",
            {"dummy_key_1": "dummy_value_1", "dummy_key_2": "dummy_value_2"},
        ),
        (
            "dummy_key_1=dummy_value_1,dummy_key_2=dummy_value_2,dummy_key_3,-dummy_key_4",
            {
                "dummy_key_1": "dummy_value_1",
                "dummy_key_2": "dummy_value_2",
                "dummy_key_3": True,
                "dummy_key_4": False,
            },
        ),
        (
            "dummy_key_1=dummy_value_1,dummy_key_2=dummy_value_2,dummy_key_3=do not use spaces in strings CLI",
            {
                "dummy_key_1": "dummy_value_1",
                "dummy_key_2": "dummy_value_2",
                "dummy_key_3": "do not use spaces in strings CLI",
            },
        ),
        (
            "dummy_key_1=dummy_value_1_key=dummy_value_1_value,dummy_key_2=dummy_value_2_key=dummy_value_2_value",
            {
                "dummy_key_1": "dummy_value_1_key=dummy_value_1_value",
                "dummy_key_2": "dummy_value_2_key=dummy_value_2_value",
            },
        ),
    ]

    @ddt.idata(data_parse_params_string)
    @ddt.unpack
    def test_parse_params_string(self, data, expect):
        self.assertDictEqual(expect, parse_params_string(data))
        self.assertDictEqual(expect, parse_params_string(make_params_string(parse_params_string(data))))

    data_make_params_string = [
        (None, ""),
        ({}, ""),
        ({"foo": "bar"}, "foo=bar"),
        (
            {"dummy_key_1": "dummy_value_1", "dummy_key_2": "dummy_value_2"},
            "dummy_key_1=dummy_value_1,dummy_key_2=dummy_value_2",
        ),
        (
            {"dummy_key_1": "dummy_value_1", "dummy_key_2": "dummy_value_2", "dummy_key_3": True, "dummy_key_4": False},
            "dummy_key_1=dummy_value_1,dummy_key_2=dummy_value_2,dummy_key_3,-dummy_key_4",
        ),
        (
            {
                "dummy_key_1": "dummy_value_1",
                "dummy_key_2": "dummy_value_2",
                "dummy_key_3": "do not use spaces in strings CLI",
            },
            "dummy_key_1=dummy_value_1,dummy_key_2=dummy_value_2,dummy_key_3=do not use spaces in strings CLI",
        ),
        (
            {
                "dummy_key_1": "dummy_value_1_key=dummy_value_1_value",
                "dummy_key_2": "dummy_value_2_key=dummy_value_2_value",
            },
            "dummy_key_1=dummy_value_1_key=dummy_value_1_value,dummy_key_2=dummy_value_2_key=dummy_value_2_value",
        ),
    ]

    @ddt.idata(data_make_params_string)
    @ddt.unpack
    def test_make_params_string(self, data, expect):
        self.assertEqual(expect, make_params_string(data))
        self.assertEqual(expect, make_params_string(parse_params_string(make_params_string(data))))

    data_strip_margin = [
        (
            """""",
            [
                "",
            ]
        ),
        (
            """|""",
            [
                "",
            ]
        ),
        (
            """||""",
            [
                "|",
            ]
        ),
        (
            """| |""",
            [
                " |",
            ]
        ),
        (
            """Lorem ipsum dolor sit amet, consectetur adipiscing elit.""",
            [
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            ]
        ),
        (
            """   Lorem ipsum dolor sit amet, consectetur adipiscing elit.   """,
            [
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit.   ",
            ]
        ),
        (
            """|   Lorem ipsum dolor sit amet, consectetur adipiscing elit.""",
            [
                "   Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            ]
        ),
        (
            """   |   Lorem ipsum dolor sit amet, consectetur adipiscing elit.""",
            [
                "   Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            ]
        ),
        (
            """
            """,
            [
                "",
                "",
            ]
        ),
        (
            """
            |""",
            [
                "",
                "",
            ]
        ),
        (
            """
            |
            """,
            [
                "",
                "",
                "",
            ]
        ),
        (
            """
            |
            ||
            |||
            ||||
            |||||
            """,
            [
                "",
                "| || ||| ||||",
                "",
            ]
        ),
        (
            """
                |
               ||
              |||
             ||||
            |||||
            """,
            [
                "",
                "| || ||| ||||",
                "",
            ]
        ),
        (
            """
            |Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam consectetur cursus purus sed dictum. Mauris
            |dui nibh, ullamcorper ac consequat nec, venenatis a tortor. Sed est arcu, aliquam at vestibulum quis,
            |tincidunt ac urna. Nullam lectus ipsum, tincidunt sodales porttitor vitae, feugiat sed risus. Vivamus
            |sollicitudin suscipit condimentum. Vestibulum odio tellus, suscipit at ipsum quis, molestie placerat quam.
            |Etiam accumsan, purus eu tristique hendrerit, magna urna lobortis neque, sed imperdiet mi sapien id diam.
            |Donec suscipit pretium finibus. Maecenas vel placerat sem.
            |
            |
            |Etiam a dapibus velit. Fusce porttitor vestibulum ultricies. Donec gravida ipsum ac dictum pretium. Mauris
            |vitae sem a diam condimentum hendrerit. Donec ut tristique neque, id pretium leo. Nulla lobortis tortor ut
            |convallis consequat. Maecenas ut ligula laoreet, feugiat arcu at, interdum ipsum. Pellentesque ornare leo
            |augue. Phasellus scelerisque ex ac pellentesque interdum.
            |
            |
            |Donec et erat vel mi dapibus lobortis. Suspendisse in fringilla nunc. Fusce venenatis, ex nec aliquam
            |faucibus, dolor mi dignissim nulla, vel dictum massa dolor vitae purus. Ut ullamcorper arcu non nulla
            |eleifend malesuada. Curabitur massa est, volutpat ornare pulvinar ut, elementum in felis. Interdum et
            |malesuada fames ac ante ipsum primis in faucibus. Integer magna erat, ullamcorper eget tristique eu,
            |interdum vitae nulla. Nulla facilisi.""",
            [
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam consectetur cursus purus sed dictum. Mauris dui nibh, ullamcorper ac consequat nec, venenatis a tortor. Sed est arcu, aliquam at vestibulum quis, tincidunt ac urna. Nullam lectus ipsum, tincidunt sodales porttitor vitae, feugiat sed risus. Vivamus sollicitudin suscipit condimentum. Vestibulum odio tellus, suscipit at ipsum quis, molestie placerat quam. Etiam accumsan, purus eu tristique hendrerit, magna urna lobortis neque, sed imperdiet mi sapien id diam. Donec suscipit pretium finibus. Maecenas vel placerat sem.",
                "",
                "Etiam a dapibus velit. Fusce porttitor vestibulum ultricies. Donec gravida ipsum ac dictum pretium. Mauris vitae sem a diam condimentum hendrerit. Donec ut tristique neque, id pretium leo. Nulla lobortis tortor ut convallis consequat. Maecenas ut ligula laoreet, feugiat arcu at, interdum ipsum. Pellentesque ornare leo augue. Phasellus scelerisque ex ac pellentesque interdum.",
                "",
                "Donec et erat vel mi dapibus lobortis. Suspendisse in fringilla nunc. Fusce venenatis, ex nec aliquam faucibus, dolor mi dignissim nulla, vel dictum massa dolor vitae purus. Ut ullamcorper arcu non nulla eleifend malesuada. Curabitur massa est, volutpat ornare pulvinar ut, elementum in felis. Interdum et malesuada fames ac ante ipsum primis in faucibus. Integer magna erat, ullamcorper eget tristique eu, interdum vitae nulla. Nulla facilisi.",
            ]
        ),
        (
            """
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam consectetur cursus purus sed dictum. Mauris
            dui nibh, ullamcorper ac consequat nec, venenatis a tortor. Sed est arcu, aliquam at vestibulum quis,
            tincidunt ac urna. Nullam lectus ipsum, tincidunt sodales porttitor vitae, feugiat sed risus. Vivamus
            sollicitudin suscipit condimentum. Vestibulum odio tellus, suscipit at ipsum quis, molestie placerat quam.
            Etiam accumsan, purus eu tristique hendrerit, magna urna lobortis neque, sed imperdiet mi sapien id diam.
            Donec suscipit pretium finibus. Maecenas vel placerat sem.


            Etiam a dapibus velit. Fusce porttitor vestibulum ultricies. Donec gravida ipsum ac dictum pretium. Mauris
            vitae sem a diam condimentum hendrerit. Donec ut tristique neque, id pretium leo. Nulla lobortis tortor ut
            convallis consequat. Maecenas ut ligula laoreet, feugiat arcu at, interdum ipsum. Pellentesque ornare leo
            augue. Phasellus scelerisque ex ac pellentesque interdum.


            Donec et erat vel mi dapibus lobortis. Suspendisse in fringilla nunc. Fusce venenatis, ex nec aliquam
            faucibus, dolor mi dignissim nulla, vel dictum massa dolor vitae purus. Ut ullamcorper arcu non nulla
            eleifend malesuada. Curabitur massa est, volutpat ornare pulvinar ut, elementum in felis. Interdum et
            malesuada fames ac ante ipsum primis in faucibus. Integer magna erat, ullamcorper eget tristique eu,
            interdum vitae nulla. Nulla facilisi.""",
            [
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam consectetur cursus purus sed dictum. Mauris dui nibh, ullamcorper ac consequat nec, venenatis a tortor. Sed est arcu, aliquam at vestibulum quis, tincidunt ac urna. Nullam lectus ipsum, tincidunt sodales porttitor vitae, feugiat sed risus. Vivamus sollicitudin suscipit condimentum. Vestibulum odio tellus, suscipit at ipsum quis, molestie placerat quam. Etiam accumsan, purus eu tristique hendrerit, magna urna lobortis neque, sed imperdiet mi sapien id diam. Donec suscipit pretium finibus. Maecenas vel placerat sem.",
                "",
                "Etiam a dapibus velit. Fusce porttitor vestibulum ultricies. Donec gravida ipsum ac dictum pretium. Mauris vitae sem a diam condimentum hendrerit. Donec ut tristique neque, id pretium leo. Nulla lobortis tortor ut convallis consequat. Maecenas ut ligula laoreet, feugiat arcu at, interdum ipsum. Pellentesque ornare leo augue. Phasellus scelerisque ex ac pellentesque interdum.",
                "",
                "Donec et erat vel mi dapibus lobortis. Suspendisse in fringilla nunc. Fusce venenatis, ex nec aliquam faucibus, dolor mi dignissim nulla, vel dictum massa dolor vitae purus. Ut ullamcorper arcu non nulla eleifend malesuada. Curabitur massa est, volutpat ornare pulvinar ut, elementum in felis. Interdum et malesuada fames ac ante ipsum primis in faucibus. Integer magna erat, ullamcorper eget tristique eu, interdum vitae nulla. Nulla facilisi.",
            ]
        ),
        (
            """
            中天山果水灵方宫林道理星飞鸟腾云下山，奇梦海园恬意鸟鸣群风神奇岁月。
            绿水青山画笔天际风景苍松古道日月行空。
            树影斜阳天高地阔，烟雾缭绕草原湖泊动情。
            年华似水时间错落，云卷云舒风起时长。
            """,
            [
                "中天山果水灵方宫林道理星飞鸟腾云下山，奇梦海园恬意鸟鸣群风神奇岁月。绿水青山画笔天际风景苍松古道日月行空。树影斜阳天高地阔，烟雾缭绕草原湖泊动情。年华似水时间错落，云卷云舒风起时长。",
                "",
            ],
            ""
        ),
        (
            """
            |中天山果水灵方宫林道理星飞鸟腾云下山，奇梦海园恬意鸟鸣群风神奇岁月。
            |绿水青山画笔天际风景苍松古道日月行空。
            |树影斜阳天高地阔，烟雾缭绕草原湖泊动情。
            |年华似水时间错落，云卷云舒风起时长。
            """,
            [
                "中天山果水灵方宫林道理星飞鸟腾云下山，奇梦海园恬意鸟鸣群风神奇岁月。绿水青山画笔天际风景苍松古道日月行空。树影斜阳天高地阔，烟雾缭绕草原湖泊动情。年华似水时间错落，云卷云舒风起时长。",
                "",
            ],
            ""
        ),
    ]

    @ddt.idata(data_strip_margin)
    @ddt.unpack
    def test_strip_margin(self, data, expect, line_concat: str = " "):
        self.assertEqual(strip_margin(data, line_concat=line_concat), "\n".join(expect))
