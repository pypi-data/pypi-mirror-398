# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module containing custom subclasses of decimal.Decimal to represent
Credits and USD values, and to convert between them.

"""
from decimal import Decimal


class Credits(Decimal):
    """Represents a value in Credits, subclassing decimal.Decimal.

    Args:
        value (str or int or float): The initial value for the Credits.
    """

    def __new__(cls, value):  # pylint: disable=signature-differs
        return super().__new__(cls, str(value))

    def __repr__(self):
        """Returns a string representation of the Credits instance."""
        dec_repr = super().__repr__()
        cred_repr = dec_repr.replace("Decimal", "Credits")
        return cred_repr

    def to_usd(self):
        """Converts Credits to USD by dividing the value by 100.

        Returns:
            USD: A USD instance with the value divided by 100.
        """
        return USD(self / Decimal("100"))

    def __eq__(self, other):  # pylint: disable=signature-differs
        """Check equality with other Credits, USD, Decimal, int, or float instances."""
        if isinstance(other, Credits):
            return Decimal(self) == Decimal(other)
        if isinstance(other, USD):
            return Decimal(self) == Decimal(other.to_credits())
        if isinstance(other, (Decimal, int, float)):
            return Decimal(self) == Decimal(str(other))
        return NotImplemented


class USD(Decimal):
    """Represents a value in USD, subclassing decimal.Decimal.

    Args:
        value (str or int or float): The initial value for the USD.
    """

    def __new__(cls, value):  # pylint: disable=signature-differs
        return super().__new__(cls, str(value))

    def __repr__(self):
        """Returns a string representation of the USD instance."""
        dec_repr = super().__repr__()
        usd_repr = dec_repr.replace("Decimal", "USD")
        return usd_repr

    def to_credits(self):
        """Converts USD to Credits by multiplying the value by 100.

        Returns:
            Credits: A Credits instance with the value multiplied by 100.
        """
        return Credits(self * Decimal("100"))

    def __eq__(self, other):  # pylint: disable=signature-differs
        """Check equality with other USD, Credits, Decimal, int, or float instances."""
        if isinstance(other, USD):
            return Decimal(self) == Decimal(other)
        if isinstance(other, Credits):
            return Decimal(self) == Decimal(other.to_usd())
        if isinstance(other, (Decimal, int, float)):
            return Decimal(self) == Decimal(str(other))
        return NotImplemented
