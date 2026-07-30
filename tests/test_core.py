import unittest

from dotenv_merge_cli.core import (
    is_comment_or_blank,
    merge_env_files,
    parse_env_file,
    split_value_and_trailer,
)


class TestParseEnvFile(unittest.TestCase):
    def test_basic_pairs(self) -> None:
        text = "FOO=bar\nBAZ=qux\n"
        self.assertEqual(parse_env_file(text), {"FOO": "bar", "BAZ": "qux"})

    def test_ignores_comments_and_blanks(self) -> None:
        text = "# a comment\n\nFOO=bar\n   \n# another\nBAZ=qux\n"
        self.assertEqual(parse_env_file(text), {"FOO": "bar", "BAZ": "qux"})

    def test_export_prefix(self) -> None:
        text = "export FOO=bar\n"
        self.assertEqual(parse_env_file(text), {"FOO": "bar"})

    def test_quoted_values(self) -> None:
        text = 'FOO="hello world"\nBAR=\'single quoted\'\n'
        self.assertEqual(
            parse_env_file(text), {"FOO": '"hello world"', "BAR": "'single quoted'"}
        )

    def test_inline_comment_stripped_from_value(self) -> None:
        text = "FOO=bar # trailing note\n"
        self.assertEqual(parse_env_file(text), {"FOO": "bar"})


class TestHelpers(unittest.TestCase):
    def test_is_comment_or_blank(self) -> None:
        self.assertTrue(is_comment_or_blank(""))
        self.assertTrue(is_comment_or_blank("   "))
        self.assertTrue(is_comment_or_blank("# comment"))
        self.assertTrue(is_comment_or_blank("  # indented comment"))
        self.assertFalse(is_comment_or_blank("FOO=bar"))

    def test_split_value_and_trailer_unquoted(self) -> None:
        self.assertEqual(split_value_and_trailer("bar"), ("bar", ""))
        self.assertEqual(
            split_value_and_trailer("bar # note"), ("bar", " # note")
        )

    def test_split_value_and_trailer_quoted(self) -> None:
        self.assertEqual(
            split_value_and_trailer('"hello world" # note'),
            ('"hello world"', " # note"),
        )


class TestMergeEnvFiles(unittest.TestCase):
    def test_override_existing_key(self) -> None:
        base = ("base.env", "FOO=bar\nBAZ=qux\n")
        override = ("override.env", "FOO=newval\n")
        result = merge_env_files([base, override])
        self.assertEqual(result, "FOO=newval\nBAZ=qux\n")

    def test_preserves_comments_and_blank_lines_from_base(self) -> None:
        base = (
            "base.env",
            "# header comment\nFOO=bar\n\n# section\nBAZ=qux\n",
        )
        override = ("override.env", "FOO=newval\n")
        result = merge_env_files([base, override])
        self.assertEqual(
            result,
            "# header comment\nFOO=newval\n\n# section\nBAZ=qux\n",
        )

    def test_new_key_appended_and_grouped_by_source_file(self) -> None:
        base = ("base.env", "FOO=bar\n")
        override = ("override.env", "FOO=bar\nNEWKEY=hello\n")
        result = merge_env_files([base, override])
        self.assertEqual(
            result,
            "FOO=bar\n\n# --- from override.env ---\nNEWKEY=hello\n",
        )

    def test_multiple_override_files_last_wins(self) -> None:
        base = ("base.env", "FOO=one\n")
        second = ("second.env", "FOO=two\n")
        third = ("third.env", "FOO=three\n")
        result = merge_env_files([base, second, third])
        self.assertEqual(result, "FOO=three\n")

    def test_unchanged_lines_are_left_verbatim(self) -> None:
        base = ("base.env", "FOO = bar  # keep spacing\n")
        override = ("override.env", "BAZ=qux\n")
        result = merge_env_files([base, override])
        self.assertIn("FOO = bar  # keep spacing\n", result)

    def test_inline_comment_preserved_when_value_changes(self) -> None:
        base = ("base.env", "FOO=bar # important note\n")
        override = ("override.env", "FOO=newval\n")
        result = merge_env_files([base, override])
        self.assertEqual(result, "FOO=newval # important note\n")

    def test_export_prefix_preserved_when_value_changes(self) -> None:
        base = ("base.env", "export FOO=bar\n")
        override = ("override.env", "FOO=newval\n")
        result = merge_env_files([base, override])
        self.assertEqual(result, "export FOO=newval\n")

    def test_new_keys_from_multiple_files_grouped_separately(self) -> None:
        base = ("base.env", "FOO=bar\n")
        second = ("second.env", "SECOND_KEY=2\n")
        third = ("third.env", "THIRD_KEY=3\n")
        result = merge_env_files([base, second, third])
        self.assertEqual(
            result,
            "FOO=bar\n"
            "\n"
            "# --- from second.env ---\n"
            "SECOND_KEY=2\n"
            "\n"
            "# --- from third.env ---\n"
            "THIRD_KEY=3\n",
        )

    def test_single_file_returned_unchanged(self) -> None:
        base = ("base.env", "FOO=bar\n")
        result = merge_env_files([base])
        self.assertEqual(result, "FOO=bar\n")


if __name__ == "__main__":
    unittest.main()
