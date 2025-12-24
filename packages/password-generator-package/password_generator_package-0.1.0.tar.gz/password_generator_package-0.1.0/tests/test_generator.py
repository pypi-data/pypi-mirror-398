"""Unit tests for password generator package."""

import unittest
import string
from password_generator import PasswordGenerator, generate_password


class TestPasswordGenerator(unittest.TestCase):
    """Test cases for PasswordGenerator class."""

    def test_default_password_length(self):
        """Test that default password length is 12."""
        generator = PasswordGenerator()
        password = generator.generate()
        self.assertEqual(len(password), 12)

    def test_custom_length(self):
        """Test custom password length."""
        for length in [8, 16, 20, 32]:
            generator = PasswordGenerator(length=length)
            password = generator.generate()
            self.assertEqual(len(password), length)

    def test_minimum_length_validation(self):
        """Test that minimum length is enforced."""
        with self.assertRaises(ValueError):
            PasswordGenerator(length=3)

    def test_at_least_one_type_required(self):
        """Test that at least one character type must be enabled."""
        with self.assertRaises(ValueError):
            PasswordGenerator(
                use_uppercase=False,
                use_lowercase=False,
                use_digits=False,
                use_special=False
            )

    def test_only_lowercase(self):
        """Test password with only lowercase letters."""
        generator = PasswordGenerator(
            length=50,
            use_uppercase=False,
            use_digits=False,
            use_special=False
        )
        password = generator.generate()
        self.assertTrue(all(c in string.ascii_lowercase for c in password))

    def test_only_uppercase(self):
        """Test password with only uppercase letters."""
        generator = PasswordGenerator(
            length=50,
            use_lowercase=False,
            use_digits=False,
            use_special=False
        )
        password = generator.generate()
        self.assertTrue(all(c in string.ascii_uppercase for c in password))

    def test_only_digits(self):
        """Test password with only digits."""
        generator = PasswordGenerator(
            length=50,
            use_uppercase=False,
            use_lowercase=False,
            use_special=False
        )
        password = generator.generate()
        self.assertTrue(all(c in string.digits for c in password))

    def test_exclude_ambiguous(self):
        """Test that ambiguous characters are excluded."""
        generator = PasswordGenerator(
            length=100,
            exclude_ambiguous=True
        )
        password = generator.generate()
        ambiguous = ['0', 'O', 'l', '1', 'I']
        self.assertFalse(any(c in ambiguous for c in password))

    def test_custom_special_characters(self):
        """Test custom special characters."""
        custom_special = "!@#"
        generator = PasswordGenerator(
            length=50,
            use_uppercase=False,
            use_lowercase=False,
            use_digits=False,
            custom_special=custom_special
        )
        password = generator.generate()
        self.assertTrue(all(c in custom_special for c in password))

    def test_generate_multiple(self):
        """Test generating multiple passwords."""
        generator = PasswordGenerator()
        count = 10
        passwords = generator.generate_multiple(count=count)
        self.assertEqual(len(passwords), count)
        # Check that all passwords are unique (very high probability)
        self.assertEqual(len(set(passwords)), count)

    def test_generate_memorable(self):
        """Test memorable password generation."""
        generator = PasswordGenerator()
        password = generator.generate_memorable(num_words=4, separator="-")
        self.assertIsInstance(password, str)
        self.assertGreater(len(password), 0)
        # Should contain separator
        self.assertIn("-", password)

    def test_password_randomness(self):
        """Test that generated passwords are different."""
        generator = PasswordGenerator(length=16)
        passwords = [generator.generate() for _ in range(100)]
        # All passwords should be unique
        self.assertEqual(len(passwords), len(set(passwords)))


class TestGeneratePasswordFunction(unittest.TestCase):
    """Test cases for generate_password convenience function."""

    def test_default_generation(self):
        """Test default password generation."""
        password = generate_password()
        self.assertEqual(len(password), 12)

    def test_custom_parameters(self):
        """Test password generation with custom parameters."""
        password = generate_password(
            length=20,
            use_special=False,
            exclude_ambiguous=True
        )
        self.assertEqual(len(password), 20)
        ambiguous = ['0', 'O', 'l', '1', 'I']
        self.assertFalse(any(c in ambiguous for c in password))


if __name__ == '__main__':
    unittest.main()
