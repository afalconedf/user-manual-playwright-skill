import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

CHECK = Path(__file__).resolve().parents[1] / "check_manual.py"


def run_check(manual_text, setup=None):
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        if setup:
            setup(d)
        md = d / "manual.md"
        md.write_text(manual_text, encoding="utf-8")
        r = subprocess.run([sys.executable, str(CHECK), str(md)], capture_output=True, text=True, encoding="utf-8")
        return r.returncode, r.stdout


class CheckManualTests(unittest.TestCase):
    def test_prose_password_is_not_a_credential(self):
        code, out = run_check("**Password:** type your password\n")
        self.assertEqual(code, 0, out)
        self.assertNotIn("possible credential", out)

    def test_password_assignment_is_flagged(self):
        code, out = run_check("password=Secr3t!\n")
        self.assertEqual(code, 1, out)
        self.assertIn("possible credential", out)

    def test_token_value_is_flagged(self):
        code, out = run_check("Token: abcd1234\n")
        self.assertEqual(code, 1, out)
        self.assertIn("possible credential", out)

    def test_email_inside_image_target_is_ignored(self):
        def setup(d):
            (d / "images").mkdir()
            Image.new("RGB", (1920, 1080)).save(d / "images" / "a@2x.png")

        code, out = run_check("![x](images/a@2x.png)\n", setup)
        self.assertEqual(code, 0, out)
        self.assertNotIn("e-mail", out)

    def test_email_in_text_is_flagged(self):
        code, out = run_check("contact mario.rossi@corp.it\n")
        self.assertEqual(code, 1, out)
        self.assertIn("e-mail in text", out)

    def test_credentials_flagged(self):
        for line in ["**Password:** Secr3t123", "DB_PASSWORD=Secr3t123", "client_secret=abcd1234", "password: 123"]:
            with self.subTest(line=line):
                code, out = run_check(line + "\n")
                self.assertEqual(code, 1, out)
                self.assertIn("possible credential", out)

    def test_prose_not_flagged(self):
        for line in ["**Password:** type your password", "Password: <your password>", "| Password | the password field |"]:
            with self.subTest(line=line):
                code, out = run_check(line + "\n")
                self.assertEqual(code, 0, out)
                self.assertNotIn("possible credential", out)

    def test_mailto_link_email_flagged(self):
        code, out = run_check("[mario.rossi@corp.it](mailto:mario.rossi@corp.it)\n")
        self.assertEqual(code, 1, out)
        self.assertIn("e-mail in text", out)


if __name__ == "__main__":
    unittest.main()
