# flake8-qa-style

Flake8 based linter with some qa best-practice for writing tests

## Installation

```bash
pip inslall flake8-qa-style
```

## Rules

1. **CS001**: using sleep(1) instead of sleep(var), var - meaningful variable
2. **CS002**: using print()
3. **CS003**: assert same variables: assert var == var
4. **CS004**: assert variable with constant: assert var == 1
5. **CS005**: missing type annotation for argument in function
6. **CS006**: missing function return type annotation
7. **CS007**: file should not start with a blank line

**Rules configuration**
```editorconfig
[flake8]
;for methods with @property decorator skip CS006
skip_property_return_annotation = true
```

## Configuration
Flake8-qa-style is flake8 plugin, so the configuration is the same as [flake8 configuration](https://flake8.pycqa.org/en/latest/user/configuration.html).

You can ignore rules via
- file `setup.cfg`: parameter `ignore`
```editorconfig
[flake8]
ignore = CS001
```
- comment in code `#noqa: CS001`
