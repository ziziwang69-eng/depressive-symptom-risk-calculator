from __future__ import annotations

import re
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def rendered_markdown(app: AppTest) -> str:
    return "\n".join(item.value for item in app.markdown)


def needle_rotation(markdown: str) -> float:
    match = re.search(r'transform: rotate\(([0-9.]+)deg\)', markdown)
    if match is None:
        raise AssertionError("The probability gauge needle was not rendered.")
    return float(match.group(1))


class StreamlitAppTests(unittest.TestCase):
    def test_probability_and_gauge_update_together(self):
        app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.selectbox), 18)
        self.assertEqual(len(app.button), 1)

        initial = rendered_markdown(app)
        self.assertIn('<div class="result-value">—</div>', initial)
        self.assertIsNone(re.search(r'transform: rotate\([0-9.]+deg\)', initial))

        app.button[0].click().run(timeout=20)
        self.assertEqual(len(app.exception), 0)
        first = rendered_markdown(app)
        self.assertIn("Estimated 2-year probability", first)
        self.assertIn("Incident depressive symptoms", first)
        first_rotation = needle_rotation(first)

        mobility = next(widget for widget in app.selectbox if widget.key == "mobility")
        mobility.set_value(2).run(timeout=20)
        changed_without_calculation = rendered_markdown(app)
        self.assertIn('<div class="result-value">—</div>', changed_without_calculation)
        self.assertIsNone(re.search(r'transform: rotate\([0-9.]+deg\)', changed_without_calculation))

        app.button[0].click().run(timeout=20)
        self.assertEqual(len(app.exception), 0)
        second = rendered_markdown(app)
        second_rotation = needle_rotation(second)
        self.assertNotEqual(first_rotation, second_rotation)


if __name__ == "__main__":
    unittest.main()
