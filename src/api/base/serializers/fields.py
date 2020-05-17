"""
Base fields
"""
import datetime
import json
import uuid
from collections import OrderedDict
from typing import (
    List, Iterable
)

from tortoise import exceptions as orm_exceptions

from . import (
    validators as base_validators, exceptions as base_exceptions
)


class Field(object):
    """
    Базовое поле описывающее формат входных атрибутов
    """

    def __init__(self,
                 name=None,
                 python_type=str,
                 read_only=False,
                 write_only=False,
                 required=True,
                 initial=None,
                 nullable=False,
                 min_length=0,
                 max_length=255,
                 many=False,
                 choices=None,
                 validators=None,
                 **kwargs):

        self.name = name
        self.python_type = python_type
        self.read_only = read_only
        self.write_only = write_only
        self.required = required
        self.nullable = nullable
        self.max_length = max_length
        self.min_length = min_length
        self.validators = validators if validators else []
        self.choices = choices
        self.initial = initial
        self.many = many

    async def get_initial(self):
        """
        Return a value to use when the field is being returned as a primitive
        value, without any object instance.
        """
        if callable(self.initial):
            return self.initial()

        return self.initial

    async def to_internal_value(self, data):
        # validate specific options
        await self.validate(data)
        return data

    async def validate(self, data):
        """
        метод валидации данных
        """
        if data is None:
            if self.required and not self.nullable:
                raise base_exceptions.ValidationError('Must be not null')

        if self.python_type and data:
            if not isinstance(data, self.python_type):
                raise base_exceptions.ValidationError("Must be a {}".format(self.python_type))

        if self.validators:
            for validator in self.validators:
                validator.validate(data)

    async def to_representation(self, attr):
        raise NotImplementedError('`to_representation()` must be implemented.')


class IntegerField(Field):
    """
    Поле принимает данные в формате int
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = int

    async def to_representation(self, attr):
        return self.python_type(attr)


class CharField(Field):
    """
    Поле принимает данные в формате строк
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = str

    async def validate(self, data):
        await super().validate(data)

        if self.max_length and data:
            base_validators.MaxLengthValidator(self.max_length).validate(data)

        if self.min_length and data:
            base_validators.MinLengthValidator(self.min_length).validate(data)

    async def to_representation(self, attr):
        return self.python_type(attr)


class BinaryField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = bytes

    async def to_representation(self, attr):
        return self.python_type(attr)


class NumberField(Field):
    """
    Поле принимает данные в формате чисел
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = int
        self.min_length = None
        self.max_length = None

    async def to_representation(self, data):
        if not self.required:
            return data

        return self.python_type(data)


class FloatField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = float
        self.min_length = None
        self.max_length = None

    async def to_representation(self, attr):
        return self.python_type(attr)


class ListField(Field):
    """
    Поле принимает данные в формате список
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = List
        self.min_length = None
        self.max_length = None

    async def to_internal_value(self, data):
        return [await super().to_internal_value(val) for val in data if val]

    async def to_representation(self, attr):
        if attr and isinstance(attr, Iterable):
            return [val for val in attr]
        return []


class URLField(CharField):
    """
    Поле принимает данные в формате url
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = str
        self.min_length = 3
        self.max_length = 255

    async def to_representation(self, attr):
        return self.python_type(attr)


class BooleanField(Field):
    """
    Поле принимает данные в формате boolean
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = bool
        self.min_length = None
        self.max_length = None

    async def to_representation(self, attr):
        return self.python_type(attr)


class ChoiceField(CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def validate(self, data):
        await super().validate(data)

        if data not in self.choices:
            raise base_exceptions.ValidationError('Must be one of declared values {}'.format(self.choices))

    async def to_representation(self, attr):
        return self.python_type(attr)


class DateField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = datetime.date

    async def to_internal_value(self, data):
        dt = datetime.datetime.strptime(data, '%Y-%m-%D')
        return await super().to_internal_value(dt.date())

    async def to_representation(self, attr):
        return attr.isoformat()


class DateTimeField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = datetime.datetime

    async def to_internal_value(self, data):
        dt = datetime.datetime.strptime(data, '%Y-%m-%DT%H:%M:%S')
        return await super().to_internal_value(dt.date())

    async def to_representation(self, attr):
        return attr.isoformat()


class DecimalField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = float

    async def to_representation(self, attr):
        return self.python_type(attr)


class TimeField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = float

    async def to_representation(self, attr):
        return self.python_type(attr)


class UUIDField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = uuid.UUID

    async def validate(self, data):
        """
        метод валидации базовых опций
        """

        if data is None:
            if self.required and not self.nullable:
                raise base_exceptions.ValidationError('Must be not null')

        if self.python_type and data:
            if not isinstance(data, self.python_type):
                raise base_exceptions.ValidationError("Must be a {}".format(self.python_type))

    async def to_internal_value(self, data):
        try:
            data = uuid.UUID(data)
        except ValueError:
            raise base_exceptions.ValidationError('{data} is badly formed hexadecimal UUID string'.format(data=data))

        return await super().to_internal_value(data)

    async def to_representation(self, attr):
        return str(attr)


class JSONField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = dict

    async def to_internal_value(self, data):
        try:
            data = json.dumps(data)
        except json.JSONDecodeError:
            raise base_exceptions.ValidationError('{data} must be json format'.format(data=data))
        return await super().to_internal_value(data)

    async def to_representation(self, attr):
        return json.loads(attr)


class ModelField(Field):

    def __init__(self, model_class, lookup_field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = model_class
        self.model_class = model_class
        self.lookup_field = lookup_field

    async def to_internal_value(self, data):
        try:
            instance = await self.model_class.get(**{self.lookup_field: data})
        except orm_exceptions.DoesNotExist as e:
            raise base_exceptions.ValidationError('Incorrect lookup value: {err}'.format(err=e))
        except orm_exceptions.FieldError as e:
            raise base_exceptions.ValidationError('Incorrect lookup field: {err}'.format(err=e))

        return instance

    async def to_representation(self, attr):
        """
        Object instance -> Dict of primitive python data.
        """
        if isinstance(attr, Iterable):
            return [item.pk for item in attr]
        return attr.pk



class PrimaryKeyField(ModelField):
    def __init__(self, model_class, lookup_field='pk', *args, **kwargs):
        super().__init__(model_class=model_class, lookup_field=lookup_field, *args, **kwargs)
        self.python_type = model_class


class ModelMultiPrimaryKeyField(ModelField):
    def __init__(self, model_class, lookup_field='id', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.python_type = model_class
        self.model_class = model_class
        self.lookup_field = lookup_field

    async def to_internal_value(self, data):
        instances = []
        for pk in data:
            try:
                instance = await self.model_class.get(lookup_field=pk)
            except orm_exceptions.DoesNotExist:
                raise base_exceptions.ValidationError('')

            instances.append(instance)

        return await super().to_internal_value(instances)

    async def to_representation(self, instances):
        data = []
        for instance in instances:
            data.append(instance.values())
        return data
