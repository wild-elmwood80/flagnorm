import unittest

from flagnorm import (
    FlagFormatError,
    format_flags,
    normalize_flags,
    normalize_key,
    normalize_value,
)

# Each case is (raw_input, expected_output). Cases marked with expected=None
# and error=True are expected to raise FlagFormatError.

KEY_CASES = [
    ("feature_flag", "feature_flag"),
    ("Feature-Flag", "feature_flag"),
    ("feature.flag", "feature_flag"),
    ("feature/flag", "feature_flag"),
    ("  feature flag  ", "feature_flag"),
    ("feature__flag", "feature_flag"),
    ("feature---flag", "feature_flag"),
    ("FEATURE_FLAG", "feature_flag"),
    ("_feature_flag_", "feature_flag"),
    ("new-checkout-flow", "new_checkout_flow"),
    ("new checkout.flow", "new_checkout_flow"),
]

KEY_ERROR_CASES = [
    "",
    "   ",
    "---",
    "123flag",
    "flag!",
    "flag@name",
    123,
    None,
]

VALUE_CASES = [
    (True, True),
    (False, False),
    ("true", True),
    ("True", True),
    ("TRUE", True),
    ("1", True),
    ("yes", True),
    ("Y", True),
    ("on", True),
    ("enabled", True),
    ("  true  ", True),
    ("false", False),
    ("False", False),
    ("0", False),
    ("no", False),
    ("n", False),
    ("off", False),
    ("disabled", False),
    ("  false  ", False),
]

VALUE_ERROR_CASES = [
    "",
    "   ",
    "maybe",
    "2",
    "-1",
    None,
    1,
    0,
    [],
    "truthy",
]


class NormalizeKeyTests(unittest.TestCase):
    def test_known_keys_normalize_as_expected(self):
        for raw, expected in KEY_CASES:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_key(raw), expected)

    def test_bad_keys_raise(self):
        for raw in KEY_ERROR_CASES:
            with self.subTest(raw=raw):
                with self.assertRaises(FlagFormatError):
                    normalize_key(raw)


class NormalizeValueTests(unittest.TestCase):
    def test_known_values_normalize_as_expected(self):
        for raw, expected in VALUE_CASES:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_value(raw), expected)

    def test_bad_values_raise(self):
        for raw in VALUE_ERROR_CASES:
            with self.subTest(raw=raw):
                with self.assertRaises(FlagFormatError):
                    normalize_value(raw)


class NormalizeFlagsTests(unittest.TestCase):
    def test_mixed_messy_dict_normalizes(self):
        raw = {
            "Feature-Flag": "yes",
            "new_checkout.flow": "0",
            "  Dark Mode  ": True,
        }
        expected = {
            "feature_flag": True,
            "new_checkout_flow": False,
            "dark_mode": True,
        }
        self.assertEqual(normalize_flags(raw), expected)

    def test_colliding_keys_raise(self):
        raw = {"feature-flag": "true", "feature_flag": "false"}
        with self.assertRaises(FlagFormatError):
            normalize_flags(raw)

    def test_empty_dict_normalizes_to_empty_dict(self):
        self.assertEqual(normalize_flags({}), {})

    def test_first_bad_entry_still_raises(self):
        raw = {"good-flag": "true", "bad flag!": "true"}
        with self.assertRaises(FlagFormatError):
            normalize_flags(raw)


class FormatFlagsTests(unittest.TestCase):
    def test_output_is_sorted_and_canonical(self):
        raw = {"Zebra-Flag": "on", "aardvark.flag": "0"}
        self.assertEqual(format_flags(raw), "aardvark_flag=false\nzebra_flag=true")

    def test_empty_input_gives_empty_string(self):
        self.assertEqual(format_flags({}), "")


if __name__ == "__main__":
    unittest.main()
