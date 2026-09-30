import tempfile
import unittest
from pathlib import Path

from flagnorm import FlagFormatError, format_flags, load_flags, load_raw_flags
from flagnorm.loader import parse_json, parse_lines


class ParseJsonTests(unittest.TestCase):
    def test_object_parses(self):
        self.assertEqual(parse_json('{"a-b": "yes", "c": false}'), {"a-b": "yes", "c": False})

    def test_non_object_raises(self):
        for text in ("[]", '"x"', "3", "null"):
            with self.subTest(text=text):
                with self.assertRaises(FlagFormatError):
                    parse_json(text)

    def test_invalid_json_raises(self):
        with self.assertRaises(FlagFormatError):
            parse_json("{not json")

    def test_duplicate_key_raises(self):
        with self.assertRaises(FlagFormatError):
            parse_json('{"a": true, "a": false}')


class ParseLinesTests(unittest.TestCase):
    def test_lines_comments_and_blanks(self):
        text = "# header\n\nfeature-flag = yes\n  dark_mode=0  \n"
        self.assertEqual(parse_lines(text), {"feature-flag": "yes", "dark_mode": "0"})

    def test_splits_on_first_equals_only(self):
        self.assertEqual(parse_lines("a=b=c"), {"a": "b=c"})

    def test_missing_equals_raises(self):
        with self.assertRaises(FlagFormatError) as ctx:
            parse_lines("ok=true\nbroken")
        self.assertIn("line 2", str(ctx.exception))

    def test_duplicate_key_raises(self):
        with self.assertRaises(FlagFormatError):
            parse_lines("a=true\na=false")


class LoadFlagsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_json_file_is_normalized(self):
        path = self.write("flags.json", '{"Feature-Flag": "yes", "Dark Mode": true}')
        self.assertEqual(load_flags(path), {"feature_flag": True, "dark_mode": True})

    def test_line_file_is_normalized(self):
        path = self.write("flags.conf", "Feature-Flag = yes\nDark Mode=off\n")
        self.assertEqual(load_flags(str(path)), {"feature_flag": True, "dark_mode": False})

    def test_format_flags_output_round_trips(self):
        raw = {"Zebra-Flag": "on", "aardvark.flag": "0"}
        path = self.write("out.flags", format_flags(raw))
        self.assertEqual(load_flags(path), {"zebra_flag": True, "aardvark_flag": False})

    def test_yaml_is_rejected(self):
        path = self.write("flags.yaml", "a: true\n")
        with self.assertRaises(FlagFormatError):
            load_raw_flags(path)

    def test_error_names_the_file(self):
        path = self.write("bad.json", "[]")
        with self.assertRaises(FlagFormatError) as ctx:
            load_flags(path)
        self.assertIn("bad.json", str(ctx.exception))

    def test_collision_across_file_keys_raises(self):
        path = self.write("flags.json", '{"a-b": true, "a_b": false}')
        with self.assertRaises(FlagFormatError):
            load_flags(path)

    def test_non_utf8_raises(self):
        path = self.dir / "flags.conf"
        path.write_bytes(b"a=\xff\xfe\n")
        with self.assertRaises(FlagFormatError):
            load_raw_flags(path)


if __name__ == "__main__":
    unittest.main()
