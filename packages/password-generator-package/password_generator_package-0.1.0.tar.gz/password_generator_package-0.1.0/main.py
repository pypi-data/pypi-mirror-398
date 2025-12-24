"""
Example usage of the password generator package.
"""

from password_generator import PasswordGenerator, generate_password


def main():
    print("=== Password Generator Demo ===\n")

    # Example 1: Quick password generation
    print("1. Quick password (default settings):")
    password = generate_password()
    print(f"   {password}\n")

    # Example 2: Custom length password
    print("2. Long password (20 characters):")
    password = generate_password(length=20)
    print(f"   {password}\n")

    # Example 3: Only letters and digits
    print("3. Alphanumeric only (no special chars):")
    password = generate_password(use_special=False)
    print(f"   {password}\n")

    # Example 4: Using PasswordGenerator class
    print("4. Generate multiple passwords:")
    generator = PasswordGenerator(length=16, exclude_ambiguous=True)
    passwords = generator.generate_multiple(count=3)
    for i, pwd in enumerate(passwords, 1):
        print(f"   Password {i}: {pwd}")
    print()

    # Example 5: Memorable password
    print("5. Memorable password:")
    generator = PasswordGenerator()
    memorable = generator.generate_memorable(num_words=4, separator="-")
    print(f"   {memorable}\n")

    # Example 6: Custom special characters
    print("6. Password with custom special chars:")
    password = generate_password(length=15, custom_special="!@#$")
    print(f"   {password}\n")

    # Example 7: PIN-like password (digits only)
    print("7. PIN (digits only):")
    password = generate_password(
        length=6,
        use_uppercase=False,
        use_lowercase=False,
        use_special=False,
        use_digits=True
    )
    print(f"   {password}\n")


if __name__ == "__main__":
    main()
