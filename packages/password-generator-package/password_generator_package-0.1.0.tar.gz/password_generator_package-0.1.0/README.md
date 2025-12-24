# Password Generator Package

Um gerador de senhas simples e seguro em Python com opções personalizáveis.

## 🔐 Características

- Geração de senhas criptograficamente seguras usando o módulo `secrets`
- Opções customizáveis (maiúsculas, minúsculas, dígitos, caracteres especiais)
- Exclusão de caracteres ambíguos (0, O, l, 1, I)
- Geração de senhas memoráveis
- Caracteres especiais customizados
- Geração de múltiplas senhas de uma vez

## 📦 Instalação

```bash
pip install -e .
```

## 🚀 Uso Rápido

### Geração simples

```python
from password_generator import generate_password

# Gerar senha com configurações padrão (12 caracteres)
password = generate_password()
print(password)  # Ex: aB3$xY9#mK2@
```

### Usando a classe PasswordGenerator

```python
from password_generator import PasswordGenerator

# Criar um gerador com configurações customizadas
generator = PasswordGenerator(
    length=16,
    use_uppercase=True,
    use_lowercase=True,
    use_digits=True,
    use_special=True,
    exclude_ambiguous=True
)

# Gerar uma senha
password = generator.generate()
print(password)

# Gerar múltiplas senhas
passwords = generator.generate_multiple(count=5)
for pwd in passwords:
    print(pwd)

# Gerar senha memorável
memorable = generator.generate_memorable(num_words=4, separator="-")
print(memorable)  # Ex: fepo-Wila-sute-Neka42!
```

## 🔧 Opções de Configuração

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `length` | int | 12 | Comprimento da senha |
| `use_uppercase` | bool | True | Incluir letras maiúsculas |
| `use_lowercase` | bool | True | Incluir letras minúsculas |
| `use_digits` | bool | True | Incluir dígitos |
| `use_special` | bool | True | Incluir caracteres especiais |
| `exclude_ambiguous` | bool | False | Excluir caracteres ambíguos (0, O, l, 1, I) |
| `custom_special` | str | None | Caracteres especiais customizados |

## 📝 Exemplos

### Senha apenas alfanumérica

```python
password = generate_password(length=16, use_special=False)
```

### Senha com caracteres especiais customizados

```python
password = generate_password(length=12, custom_special="!@#$%")
```

### PIN numérico

```python
pin = generate_password(
    length=6,
    use_uppercase=False,
    use_lowercase=False,
    use_special=False,
    use_digits=True
)
```

### Senha longa e segura

```python
password = generate_password(length=32, exclude_ambiguous=True)
```

## 🔒 Segurança

Este package utiliza o módulo `secrets` do Python para geração criptograficamente segura de números aleatórios, adequado para gerenciar dados como senhas, autenticação, tokens de segurança e segredos relacionados.

## 📄 Licença

MIT

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## 🧪 Executar Demo

```bash
python main.py
```