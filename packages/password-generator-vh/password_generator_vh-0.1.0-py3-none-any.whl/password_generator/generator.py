import random
import string

class PasswordGenerator:
    def __init__(
        self,
        length=12,
        use_uppercase=True,
        use_lowercase=True,
        use_digits=True,
        use_symbols=True
    ):
        self.length = length
        self.characters = ""

        if use_uppercase:
            self.characters += string.ascii_uppercase
        if use_lowercase:
            self.characters += string.ascii_lowercase
        if use_digits:
            self.characters += string.digits
        if use_symbols:
            self.characters += string.punctuation

        if not self.characters:
            raise ValueError("At least one character type must be selected")

    def generate(self):
        return "".join(random.choice(self.characters) for _ in range(self.length))
