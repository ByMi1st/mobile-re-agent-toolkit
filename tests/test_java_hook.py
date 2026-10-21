import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mrat.cli import main
from mrat.java_hook import generate_java_hook
from mrat.model import JavaMethodSpec, ProbeContext


class JavaHookGeneratorTest(unittest.TestCase):
    def test_requires_qualified_class_name(self) -> None:
        with self.assertRaises(ValueError):
            JavaMethodSpec("RequestBuilder", "addHeader")

    def test_generates_exact_overload_and_structured_event(self) -> None:
        source = generate_java_hook(
            JavaMethodSpec(
                "okhttp3.Request$Builder",
                "addHeader",
                ("java.lang.String", "java.lang.String"),
            ),
            ProbeContext("feed", "req-1", "natural"),
        )
        self.assertIn(
            '.overload("java.lang.String", "java.lang.String")', source
        )
        self.assertIn("event: 'java_method_invocation'", source)
        self.assertIn('scene_id: "feed"', source)
        self.assertIn('request_id: "req-1"', source)
        self.assertIn("invocation_id: invocationId", source)
        self.assertIn("Process.getCurrentThreadId()", source)

    def test_no_stack_option(self) -> None:
        source = generate_java_hook(
            JavaMethodSpec("example.Target", "run", ()), include_stack=False
        )
        self.assertIn("stack: null", source)
        self.assertNotIn("getStackTraceString", source)

    def test_cli_writes_script(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "probe.js"
            exit_code = main(
                [
                    "generate-java-hook",
                    "--class",
                    "example.Target",
                    "--method",
                    "run",
                    "--overload",
                    "java.lang.String",
                    "--out",
                    str(output),
                ]
            )
            self.assertEqual(exit_code, 0)
            self.assertTrue(output.is_file())
            self.assertIn("example.Target", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
