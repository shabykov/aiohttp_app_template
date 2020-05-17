import re
from abc import ABC, abstractmethod

from .exceptions import ValidationError


class Validator(ABC):

    @abstractmethod
    def validate(self, value):
        raise NotImplementedError('Method is not implemented.')


class MaxLengthValidator(Validator):
    message = "{} len is grater than {}"

    def __init__(self, limit_value):
        self.limit_value = limit_value

    def validate(self, value):
        if len(value) > self.limit_value:
            raise ValidationError(self.message.format(value, self.limit_value))


class MinLengthValidator(Validator):
    message = "{} len is less than {}"

    def __init__(self, limit_value):
        self.limit_value = limit_value

    def validate(self, value):
        if len(value) < self.limit_value:
            raise ValidationError(self.message.format(value, self.limit_value))


class EmailValidator(Validator):
    message = '{} is incorrect email address'
    regex = re.compile(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')

    def validate(self, value):
        if not value or '@' not in value:
            raise ValidationError(self.message.format(value))

        if self.regex.match(value) is None:
            raise ValidationError(self.message.format(value))


class DateValidator(Validator):
    message = '{} is incorrect date'
    regex = re.compile(r'^[0-9]{2}[.-/]?[0-9]{2}[.-/]?[0-9]{4}$')

    def validate(self, value):
        if self.regex.match(value) is None:
            raise ValidationError(self.message.format(value))
