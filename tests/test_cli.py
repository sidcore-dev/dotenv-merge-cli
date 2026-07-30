import contextlib
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from dotenv_merge_cli.cli import main


class TestCli(unittest.TestCase):
    def test_merge_two_files_to_stdout(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.env"
            override = Path(tmp) / "override.env"
            base.write_text("FOO=bar\nBAZ=qux\n")
            override.write_text("FOO=newval\n")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([str(base), str(override)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue(), "FOO=newval\nBAZ=qux\n")

    def test_out_writes_file(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.env"
            override = Path(tmp) / "override.env"
            out = Path(tmp) / "merged.env"
            base.write_text("FOO=bar\n")
            override.write_text("NEWKEY=1\n")

            exit_code = main([str(base), str(override), "--out", str(out)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                out.read_text(),
                "FOO=bar\n\n# --- from override.env ---\nNEWKEY=1\n",
            )

    def test_out_refuses_to_overwrite_existing_file(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.env"
            override = Path(tmp) / "override.env"
            out = Path(tmp) / "merged.env"
            base.write_text("FOO=bar\n")
            override.write_text("FOO=baz\n")
            out.write_text("existing contents\n")

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                exit_code = main([str(base), str(override), "--out", str(out)])

            self.assertNotEqual(exit_code, 0)
            self.assertIn("already exists", stderr.getvalue())
            self.assertEqual(out.read_text(), "existing contents\n")

    def test_out_force_overwrites_existing_file(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.env"
            override = Path(tmp) / "override.env"
            out = Path(tmp) / "merged.env"
            base.write_text("FOO=bar\n")
            override.write_text("FOO=baz\n")
            out.write_text("existing contents\n")

            exit_code = main([str(base), str(override), "--out", str(out), "--force"])

            self.assertEqual(exit_code, 0)
            self.assertEqual(out.read_text(), "FOO=baz\n")

    def test_fewer_than_two_files_is_an_error(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.env"
            base.write_text("FOO=bar\n")

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                exit_code = main([str(base)])

            self.assertNotEqual(exit_code, 0)
            self.assertIn("at least two", stderr.getvalue())

    def test_missing_file_reports_error(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.env"
            missing = Path(tmp) / "does_not_exist.env"
            base.write_text("FOO=bar\n")

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                exit_code = main([str(base), str(missing)])

            self.assertNotEqual(exit_code, 0)
            self.assertIn("cannot read", stderr.getvalue())

    def test_merge_three_files(self) -> None:
        with TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.env"
            second = Path(tmp) / "second.env"
            third = Path(tmp) / "third.env"
            first.write_text("FOO=one\nBAR=keep\n")
            second.write_text("FOO=two\n")
            third.write_text("FOO=three\n")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([str(first), str(second), str(third)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue(), "FOO=three\nBAR=keep\n")


if __name__ == "__main__":
    unittest.main()
