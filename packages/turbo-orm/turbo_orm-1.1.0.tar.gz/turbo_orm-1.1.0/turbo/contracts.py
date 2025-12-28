"""
Model Contracts - Smart Validation Rules

Define declarative validation rules that auto-enforce business logic.
Prevents invalid states and ensures data integrity.
"""

import functools


class ContractViolation(Exception):
    """Raised when a model contract is violated"""

    pass


def ensure(message):
    """
    Decorator for contract methods

    Usage:
        class User(Model):
            class Contract:
                @ensure("Email must be unique")
                def unique_email(self, db):
                    return User.count(db, email=self.email) <= 1
    """

    def decorator(func):
        func._contract_message = message
        func._is_contract = True
        return func

    return decorator


class ContractMeta(type):
    """Metaclass to process contracts"""

    def __new__(cls, name, bases, attrs):
        # Collect contracts from Contract inner class
        contracts = []

        if "Contract" in attrs:
            contract_class = attrs["Contract"]
            for attr_name in dir(contract_class):
                attr = getattr(contract_class, attr_name)
                if hasattr(attr, "_is_contract"):
                    contracts.append((attr_name, attr, attr._contract_message))

        # Store contracts
        attrs["_contracts"] = contracts

        # Create new class
        new_class = super().__new__(cls, name, bases, attrs)

        return new_class


class ContractModel:
    """Mixin to add contract validation"""

    def validate_contracts(self, db):
        """Validate all contracts"""
        if not hasattr(self, "_contracts"):
            return True

        violations = []

        for name, contract_method, message in self._contracts:
            try:
                result = contract_method(self, db)
                if not result:
                    violations.append(message)
            except Exception as e:
                violations.append(f"{message} (Error: {e})")

        if violations:
            raise ContractViolation(
                f"Contract violations for {self.__class__.__name__}:\n"
                + "\n".join(f"  • {v}" for v in violations)
            )

        return True

    def save(self, db):
        """Override save to validate contracts"""
        # Validate contracts before saving
        self.validate_contracts(db)

        # Call parent save
        super().save(db)


def add_contracts_to_model():
    """Add contract functionality to Model"""
    from .model import Model

    # Add ContractModel to Model's bases if not already there
    original_save = Model.save

    def save_with_contracts(self, db):
        """Save with contract validation"""
        # Check if model has contracts
        if hasattr(self, "_contracts") and self._contracts:
            # Validate
            violations = []
            for name, contract_method, message in self._contracts:
                try:
                    result = contract_method(self, db)
                    if not result:
                        violations.append(message)
                except Exception as e:
                    violations.append(f"{message} (Error: {e})")

            if violations:
                raise ContractViolation(
                    f"Contract violations:\n"
                    + "\n".join(f"  • {v}" for v in violations)
                )

        # Call original save
        return original_save(self, db)

    Model.save = save_with_contracts


# Helper functions for common contract patterns


def days_ago(n):
    """Helper: Get datetime N days ago"""
    import datetime

    return datetime.datetime.now() - datetime.timedelta(days=n)


def is_valid_email(email):
    """Helper: Basic email validation"""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_in_range(value, min_val, max_val):
    """Helper: Check if value is in range"""
    return min_val <= value <= max_val
