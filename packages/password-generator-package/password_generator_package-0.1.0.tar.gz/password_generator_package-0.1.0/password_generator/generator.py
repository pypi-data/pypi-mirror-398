"""
Core password generator module.
"""

import random
import string
import secrets


class PasswordGenerator:
    """
    A class for generating secure random passwords with various options.
    """

    def __init__(
        self,
        length: int = 12,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_special: bool = True,
        exclude_ambiguous: bool = False,
        custom_special: str = None
    ):
        """
        Initialize the password generator with configuration options.

        Args:
            length: Length of the password (default: 12)
            use_uppercase: Include uppercase letters (default: True)
            use_lowercase: Include lowercase letters (default: True)
            use_digits: Include digits (default: True)
            use_special: Include special characters (default: True)
            exclude_ambiguous: Exclude ambiguous characters like 0, O, l, 1 (default: False)
            custom_special: Custom special characters to use (default: None)
        """
        if length < 4:
            raise ValueError("Password length must be at least 4 characters")

        if not any([use_uppercase, use_lowercase, use_digits, use_special]):
            raise ValueError("At least one character type must be enabled")

        self.length = length
        self.use_uppercase = use_uppercase
        self.use_lowercase = use_lowercase
        self.use_digits = use_digits
        self.use_special = use_special
        self.exclude_ambiguous = exclude_ambiguous
        self.custom_special = custom_special

    def _get_character_pool(self) -> str:
        """
        Build the character pool based on configuration.

        Returns:
            String containing all available characters for password generation
        """
        pool = ""

        if self.use_lowercase:
            lowercase = string.ascii_lowercase
            if self.exclude_ambiguous:
                lowercase = lowercase.replace('l', '')
            pool += lowercase

        if self.use_uppercase:
            uppercase = string.ascii_uppercase
            if self.exclude_ambiguous:
                uppercase = uppercase.replace('O', '').replace('I', '')
            pool += uppercase

        if self.use_digits:
            digits = string.digits
            if self.exclude_ambiguous:
                digits = digits.replace('0', '').replace('1', '')
            pool += digits

        if self.use_special:
            if self.custom_special:
                pool += self.custom_special
            else:
                pool += string.punctuation

        return pool

    def generate(self) -> str:
        """
        Generate a secure random password.

        Returns:
            A randomly generated password as a string
        """
        char_pool = self._get_character_pool()

        if not char_pool:
            raise ValueError("Character pool is empty. Check your configuration.")

        # Use secrets module for cryptographically strong random password
        password = ''.join(secrets.choice(char_pool) for _ in range(self.length))

        return password

    def generate_multiple(self, count: int = 5) -> list[str]:
        """
        Generate multiple passwords.

        Args:
            count: Number of passwords to generate (default: 5)

        Returns:
            List of generated passwords
        """
        return [self.generate() for _ in range(count)]

    def generate_memorable(self, num_words: int = 4, separator: str = "-") -> str:
        """
        Generate a memorable password using random words pattern.

        Args:
            num_words: Number of word-like segments (default: 4)
            separator: Character to separate segments (default: "-")

        Returns:
            A memorable password string
        """
        # Create pronounceable segments
        consonants = "bcdfghjklmnprstvwxyz"
        vowels = "aeiou"
        
        if self.exclude_ambiguous:
            consonants = consonants.replace('l', '')
            vowels = vowels.replace('o', '')

        segments = []
        for _ in range(num_words):
            segment_length = random.randint(3, 5)
            segment = ""
            for i in range(segment_length):
                if i % 2 == 0:
                    segment += secrets.choice(consonants)
                else:
                    segment += secrets.choice(vowels)
            
            # Capitalize some segments randomly
            if self.use_uppercase and secrets.choice([True, False]):
                segment = segment.capitalize()
            
            segments.append(segment)

        password = separator.join(segments)

        # Add digits at the end if enabled
        if self.use_digits:
            password += str(secrets.randbelow(100))

        # Add special character if enabled
        if self.use_special:
            special_chars = self.custom_special if self.custom_special else "!@#$%"
            password += secrets.choice(special_chars)

        return password


def generate_password(
    length: int = 12,
    use_uppercase: bool = True,
    use_lowercase: bool = True,
    use_digits: bool = True,
    use_special: bool = True,
    exclude_ambiguous: bool = False,
    custom_special: str = None
) -> str:
    """
    Convenience function to generate a single password.

    Args:
        length: Length of the password (default: 12)
        use_uppercase: Include uppercase letters (default: True)
        use_lowercase: Include lowercase letters (default: True)
        use_digits: Include digits (default: True)
        use_special: Include special characters (default: True)
        exclude_ambiguous: Exclude ambiguous characters (default: False)
        custom_special: Custom special characters to use (default: None)

    Returns:
        A randomly generated password as a string
    """
    generator = PasswordGenerator(
        length=length,
        use_uppercase=use_uppercase,
        use_lowercase=use_lowercase,
        use_digits=use_digits,
        use_special=use_special,
        exclude_ambiguous=exclude_ambiguous,
        custom_special=custom_special
    )
    return generator.generate()
