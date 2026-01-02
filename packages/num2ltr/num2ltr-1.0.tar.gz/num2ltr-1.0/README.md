# num2ltr

[![es](https://img.shields.io/badge/lang-es-yellow.svg)](https://github.com/DanielMolina33/num2ltr/blob/main/README.es.md)

num2ltr is a simple Python package for converting numbers to words (letters).

It uses Spanish standard nomenclature, which means that most Spanish grammar rules are applied.

This package is still under **testing**, so you may experience inconsistencies.

This is also a personal project to improve my programming skills.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install num2ltr.

```bash
pip install num2ltr
```

Or you can use the test package

```bash
pip install -i https://test.pypi.org/simple/ num2ltr
```

## Usage

```python
import num2ltr

# returns 'treinta y tres'
num2ltr.number_to_letters('33') # input must be a numeric string
```

Or you can use

```python
from num2ltr import number_to_letters

# returns 'treinta y tres'
number_to_letters('33') # input must be a numeric string
```

## Features
- Converts numeric strings to Spanish words
- Supports numbers up to 15 digits (for now)

## Limitations
- No decimal support yet
- No negative numbers
- No scientific notation

## Roadmap
- Decimal number support
- Negative numbers
- Support for larger numbers (up to 50 digits)

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to add or change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)