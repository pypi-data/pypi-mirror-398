"""
pyillion
========
This module helps you convert integers into long-form *-illion* notation
(e.g. million, billion, trillion).

Functions
---------
e(number)
    Return ``1000 ** number``.

d(a, b, r=3)
    Divide ``a`` by ``b`` and keep ``r`` decimal digits.

il(n, bl=False)
    Return the *-illion* name corresponding to ``n``.
    If ``bl`` is True, return ``1000 ** n`` instead.

illionify(n, r=3)
    Convert a large integer into *-illion* long form.

Examples
--------
>>> e(7)
1000000000000000000000

>>> d(215, 11, 4)
19.5454

>>> il(7)
'sextillion'

>>> illionify(1234567890, 4)
'1.2345 billion'
"""

from .illionifyer import e, d, il, illionify
__all__ = ["e", "d", "il", "illionify"]
__version__ = "1.2"
