"""Password Generator - Generate strong passwords."""

import argparse
import random
import string


class PasswordGenerator:
    def __init__(
        self,
        length: int = 12,
        use_digits: bool = True,
        use_specials: bool = True,
    ):
        self.length = length
        self.use_digits = use_digits
        self.use_specials = use_specials

    def generate(self) -> str:
        chars = string.ascii_letters
        if self.use_digits:
            chars += string.digits
        if self.use_specials:
            chars += "!@#$%^&*()-_=+[]{};:,.<>?/"

        return "".join(random.choice(chars) for _ in range(self.length))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a random password.")
    parser.add_argument("-l", "--length", type=int, default=12, help="Password length")
    parser.add_argument("--no-digits", action="store_true", help="Exclude digits")
    parser.add_argument("--no-specials", action="store_true", help="Exclude special characters")
    args = parser.parse_args()

    generator = PasswordGenerator(
        length=args.length,
        use_digits=not args.no_digits,
        use_specials=not args.no_specials,
    )
    print(generator.generate())


if __name__ == "__main__":
    main()
