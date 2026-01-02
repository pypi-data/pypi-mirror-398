import getpass
import time
from .validators import *

class Ask:

    def _loop(self, fn):
        while True:
            try:
                return fn()
            except ValueError as e:
                print(f"Error: {e}")

    def int(self, prompt, min=None, max=None):
        return self._loop(lambda: validate_int(input(f"{prompt}: "), min, max))

    def float(self, prompt, min=None, max=None):
        return self._loop(lambda: validate_float(input(f"{prompt}: "), min, max))

    def string(self, prompt, min_len=None, max_len=None):
        return self._loop(lambda: validate_str(input(f"{prompt}: "), min_len, max_len))

    def email(self, prompt):
        return self._loop(lambda: validate_email(input(f"{prompt}: ")))

    def password(self, prompt):
        return getpass.getpass(f"{prompt}: ")

    def password_strong(self, prompt, min_len=8):
        return self._loop(lambda: validate_password_strength(
            getpass.getpass(f"{prompt}: "), min_len
        ))

    def confirm(self, prompt):
        return self._loop(lambda: validate_confirm(input(f"{prompt} (y/n): ")))

    def confirm_phrase(self, prompt, phrase):
        return self._loop(lambda: (
            input(f"{prompt} (type '{phrase}'): ") == phrase
        ) or (_ for _ in ()).throw(ValueError("phrase mismatch")))

    def choice(self, prompt, choices):
        print(f"{prompt}:")
        for i, c in enumerate(choices, 1):
            print(f"  {i}. {c}")

        return self._loop(lambda: choices[
            validate_int(input("Select option: "), 1, len(choices)) - 1
        ])

    def pattern(self, prompt, regex, message="invalid format"):
        return self._loop(lambda: validate_pattern(
            input(f"{prompt}: "), regex, message
        ))

    def multi(self, prompt, separator=","):
        return self._loop(lambda: [
            v.strip() for v in input(f"{prompt} (sep: '{separator}'): ").split(separator)
            if v.strip()
        ])

    def timed(self, prompt, timeout=5):
        print(f"{prompt} (you have {timeout}s)")
        start = time.time()
        value = input("> ")
        if time.time() - start > timeout:
            raise TimeoutError("input timed out")
        return value

ask = Ask()
