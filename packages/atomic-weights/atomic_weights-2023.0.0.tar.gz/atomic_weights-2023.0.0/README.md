# py-atomic-weights: Python Module for Standard atomic weights of the elements

## Features
* [IUPAC Atomic Weights](https://iupac.qmul.ac.uk/AtWt/) in `float` and `decimal.Decimal` formats

## Usage

```
pip install atomic-weights
```

```py
>>> import atomic_weights as atw
>>> print(atw.Fe)
55.845
>>> print(atw.decimal.Fe)
55.845
>>> type(atw.Fe)
<class 'float'>
>>> type(atw.decimal.Fe)
<class 'decimal.Decimal'>
```

```py
import re
import unicodedata

import atomic_weights as atw


def molecular_mass(x: str) -> float:
    """formula -> g/mol"""

    x = unicodedata.normalize("NFKC", x)
    y = 0
    for elem, num in re.findall(r"(?:([A-Z][a-z]*)(\d+)?)", x):
        num = int(num) if num else 1
        y += num * getattr(atw, elem)
    return y

molecular_mass("Al2O3")
# 101.9600768
molecular_mass("Al₂O₃")
# 101.9600768
```
