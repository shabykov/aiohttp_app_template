"""
Base serializers
"""

import copy
import traceback
from collections import OrderedDict
from typing import (
    Dict, List, Iterable
)

from tortoise import (
    models, queryset
)

from . import (
    fields, exceptions, helpers
)

AbstractModel = models.Model


class BaseSerializer(fields.Field):
    """
    Базовый сериализатор входных данных
    """

    def __init__(self, instance=None, data=None, **kwargs):
        self.instance = instance
        if data is not None:
            self.initial_data = data

        self.partial = kwargs.pop('partial', False)
        self._context = kwargs.pop('context', {})

        kwargs.pop('many', None)
        super().__init__(**kwargs)

    def __new__(cls, *args, **kwargs):
        if kwargs.pop('many', False):
            return cls.many_init(*args, **kwargs)
        return super().__new__(cls)

    @classmethod
    def many_init(cls, *args, **kwargs):
        allow_empty = kwargs.pop('allow_empty', None)
        list_kwargs = {
            'child': cls(*args, **kwargs)
        }
        if allow_empty is not None:
            list_kwargs['allow_empty'] = allow_empty

        list_kwargs.update(kwargs)

        meta = getattr(cls, 'Meta', None)
        list_serializer_class = getattr(meta, 'list_serializer_class', ListSerializer)
        return list_serializer_class(**list_kwargs)

    async def is_valid(self, raise_error=False):
        validated_data = await self.to_internal_value(self.initial_data)
        if self.errors:
            if raise_error:
                raise exceptions.ValidationError(self.errors)
            return False

        setattr(self, '_validated_data', validated_data)
        return True

    async def save(self):
        assert hasattr(self, '_validated_data'), (
            'You must call `.is_valid()` before calling `.save()`.'
        )

        assert not hasattr(self, '_errors'), (
            'You must call `.is_valid()` before calling `.save()`.'
        )

        assert not self.errors, (
            'You cannot call `.save()` on a serializer with invalid data.'
        )

        if self.instance is not None:
            self.instance = await self.update(self.instance, self.validated_data)
            assert self.instance is not None, (
                '`update()` did not return an object instance.'
            )
        else:
            self.instance = await self.create(self.validated_data)
            assert self.instance is not None, (
                '`create()` did not return an object instance.'
            )
        return self.instance

    async def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')

    async def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    async def get_initial(self):
        """
        Return a value to use when the field is being returned as a primitive
        value, without any object instance.
        """
        if callable(self.initial):
            return self.initial()
        return self.initial

    async def to_internal_value(self, data):
        raise NotImplementedError('`to_internal_value()` must be implemented.')

    async def to_representation(self, instance):
        raise NotImplementedError('`to_representation()` must be implemented.')

    @property
    async def data(self):
        if hasattr(self, 'initial_data') and not hasattr(self, '_validated_data'):
            msg = (
                'When a serializer is passed a `data` keyword argument you '
                'must call `.is_valid()` before attempting to access the '
                'serialized `.data` representation.\n'
                'You should either call `.is_valid()` first, '
                'or access `.initial_data` instead.'
            )
            raise AssertionError(msg)

        if not hasattr(self, '_data'):
            if self.instance is not None and not getattr(self, '_errors', None):
                setattr(self, '_data', await self.to_representation(self.instance))

            elif hasattr(self, '_validated_data') and not getattr(self, '_errors', None):
                setattr(self, '_data', await self.to_representation(self.validated_data))

            else:
                setattr(self, '_data', await self.get_initial())

        return getattr(self, '_data', {})

    @property
    def validated_data(self):
        return getattr(self, '_validated_data')

    @property
    def errors(self):
        return self._errors if hasattr(self, '_errors') else None


class SerializerMeta(type):
    """
    Интерфейс создания сериализваторов
    """

    def __new__(mcs, name, bases, attrs, **kwargs):
        # словарь для стандартных и пользовательских атрибутов
        default_attrs = {}

        # словарь для задекларированных арибутов
        declared_attrs = {}
        for field_name, attr in attrs.items():
            if isinstance(attr, fields.Field):
                setattr(attr, 'name', field_name)
                declared_attrs[field_name] = attr
            else:
                default_attrs[field_name] = attr

        # необходимо передать задекларированные атрибуты в классы сериализаторов,
        # для дальнейшей проверки входных данных по заданным форматам атрибутов
        default_attrs['_declared_fields'] = declared_attrs
        return super().__new__(mcs, name, bases, default_attrs)


class Serializer(BaseSerializer, metaclass=SerializerMeta):

    async def create(self, validated_data):
        return await super().create(validated_data)

    async def update(self, instance, validated_data):
        return await super().update(instance, validated_data)

    async def get_initial(self):
        if hasattr(self, 'initial_data'):

            if not isinstance(self.initial_data, Dict):
                return OrderedDict()

            return OrderedDict([
                (name, self.initial_data.get(name))
                for name, field in self.fields.items() if not self.initial_data.get(name) and not field.read_only
            ])

        return OrderedDict([
            (name, await field.get_initial()) for name, field in self.fields.items() if not field.read_only
        ])

    async def to_internal_value(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        if not isinstance(data, Dict):
            raise exceptions.ValidationError()

        errors = OrderedDict()
        validated_data = OrderedDict()
        for field_name, field in self.writable_fields.items():
            if self.partial and not self.initial_data.get(field_name, None):
                continue

            primitive_value = self.initial_data[field_name]
            if isinstance(field, BaseSerializer):
                serializer = field(data=primitive_value)
                if await serializer.is_valid():
                    validated_data[field_name] = serializer.validated_data
                else:
                    errors[field_name] = serializer.errors

            if isinstance(field, fields.Field):
                try:
                    validated_data[field_name] = await field.to_internal_value(primitive_value)
                except exceptions.ValidationError as e:
                    errors[field_name] = e.message

        if errors:
            setattr(self, '_errors', errors)

        return validated_data

    async def to_representation(self, instance):
        """
        Object instance -> Dict of primitive python data.
        """
        ret = OrderedDict()
        for field_name, field in self.readable_fields.items():
            attr = getattr(instance, field_name)
            if isinstance(attr, queryset.QuerySet):
                attr = await attr.all()
            ret[field_name] = await field.to_representation(attr)
        return ret

    @property
    def fields(self):
        if not hasattr(self, '_fields'):
            setattr(self, '_fields', OrderedDict(**self.get_fields()))
        return getattr(self, '_fields', {})

    @property
    def writable_fields(self):
        return OrderedDict([(name, field) for name, field in self.fields.items() if not field.read_only])

    @property
    def readable_fields(self):
        return OrderedDict([(name, field) for name, field in self.fields.items() if not field.write_only])

    def get_fields(self):
        """
        Returns a dictionary of {field_name: field_instance}.
        """
        return copy.deepcopy(self._declared_fields)


class ListSerializer(BaseSerializer):
    child = None
    many = True

    def __init__(self, **kwargs):
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        self.allow_empty = kwargs.pop('allow_empty', True)
        assert self.child is not None, '`child` is a required argument.'
        super().__init__(**kwargs)

    async def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')

    async def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    async def get_initial(self):
        if hasattr(self, 'initial_data') and isinstance(self.initial_data, List):
            return await self.to_representation(self.initial_data)
        return []

    async def to_internal_value(self, data):
        """
        List of object primitive datatypes -> List of instances.
        """
        return [
            await self.child.to_internal_value(item) for item in data
        ]

    async def to_representation(self, instances):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        return [
            await self.child.to_representation(instance) for instance in instances
        ]


class ModelSerializer(Serializer):
    model_field_mapping = {
        'IntField': fields.IntegerField,
        'BigIntField': fields.IntegerField,
        'BinaryField': fields.BinaryField,
        'BooleanField': fields.BooleanField,
        'CharField': fields.CharField,
        'DateField': fields.DateField,
        'DatetimeField': fields.DateTimeField,
        'DecimalField': fields.DecimalField,
        'Field': fields.Field,
        'FloatField': fields.FloatField,
        'TextField': fields.CharField,
        'TimeDeltaField': fields.TimeField,
        'UUIDField': fields.UUIDField,
        'SmallIntField': fields.IntegerField,
        'JSONField': fields.JSONField,
        'ForeignKeyField': fields.PrimaryKeyField,
        'ForeignKeyFieldInstance': fields.PrimaryKeyField,
        'OneToOneField': fields.PrimaryKeyField,
        'OneToOneFieldInstance': fields.PrimaryKeyField,
        'ManyToManyField': fields.ModelMultiPrimaryKeyField
    }

    class Meta:
        model = AbstractModel

    async def create(self, validated_data):
        model_class = self.Meta.model
        model_info = model_class.describe()

        many_to_many = {}
        for field in model_info['m2m_fields']:
            if field['name'] in validated_data:
                many_to_many[field['name']] = validated_data.pop(field['name'])

        try:
            instance = await model_class.create(**validated_data)
        except TypeError:
            tb = traceback.format_exc()
            msg = (
                    'Got a `TypeError` when calling `%s.create()`. '
                    'This may be because you have a writable field on the '
                    'serializer class that is not a valid argument to '
                    '`%s.create()`. You may need to make the field '
                    'read-only, or override the %s.create() method to handle '
                    'this correctly.\nOriginal exception was:\n %s' %
                    (
                        model_class.__name__,
                        model_class.__name__,
                        self.__class__.__name__,
                        tb
                    )
            )
            raise TypeError(msg)

        if many_to_many:
            for field_name, value in many_to_many.items():
                if hasattr(instance, field_name):
                    field = getattr(instance, field_name)
                    field.clear()
                    for item in value:
                        field.add(item)

        return instance

    async def update(self, instance, validated_data):
        model_class = self.Meta.model
        model_info = model_class.describe()
        m2m_fields = [field['name'] for field in model_info['m2m_fields']]

        for field_name, value in validated_data.items():
            if field_name in m2m_fields:
                if hasattr(instance, field_name):
                    field = getattr(instance, field_name)
                    field.clear()
                    for item in value:
                        field.add(item)
            else:
                setattr(instance, field_name, value)

        await instance.save()
        return instance

    @helpers.check_model_meta
    def get_fields(self):
        model_info = self.Meta.model.describe()
        model_field_classes, model_field_kwargs = self._get_model_fields(model_info)
        declared_fields = copy.deepcopy(getattr(self, '_declared_fields'))

        # получаем список полей,
        # поля могу быть получены из мета класса или из задекларированиых в модели полей
        field_names = self._get_field_names(declared_fields, model_field_classes)

        # получаем аргументы полей
        extra_kwargs = self._get_extra_kwargs()

        # Поля будут использованы
        fields = OrderedDict()
        for field_name in field_names:

            if field_name in declared_fields:
                # Если поле задекларировано
                fields[field_name] = declared_fields[field_name]
                # то переходим к следующей
                continue
            else:
                # иначе поле должно строится из
                extra_field_kwargs = extra_kwargs.get(field_name, {})
                field_class = helpers.get_field_class_from_model(field_name, model_field_classes)
                if field_class:
                    field_kwargs = helpers.include_extra_kwargs(
                        helpers.get_field_kwargs_from_model(field_name, model_field_kwargs),
                        extra_field_kwargs
                    )

                    # Create the serializer field.
                    fields[field_name] = field_class(**field_kwargs)

        return fields

    def _get_field_names(self, declared_fields, model_field_classes):
        field_names = getattr(self.Meta, 'fields', None)
        exclude_field_names = getattr(self.Meta, 'exclude', None)
        if field_names and isinstance(field_names, Iterable):
            required_field_names = set(declared_fields)
            for cls in self.__class__.__bases__:
                required_field_names -= set(getattr(cls, '_declared_fields', []))

            for field_name in required_field_names:
                assert field_name in field_names, (
                    "The field '{field_name}' was declared on serializer "
                    "{serializer_class}, but has not been included in the "
                    "'fields' option.".format(
                        field_name=field_name,
                        serializer_class=self.__class__.__name__
                    )
                )
            return field_names

        # Use the default set of field names if `Meta.fields` is not specified.
        field_names = model_field_classes.keys()
        if exclude_field_names is not None:
            # If `Meta.exclude` is included, then remove those fields.
            for field_name in exclude_field_names:
                assert field_name not in declared_fields, (
                    "Cannot both declare the field '{field_name}' and include "
                    "it in the {serializer_class} 'exclude' option. Remove the "
                    "field or, if inherited from a parent serializer, disable "
                    "with `{field_name} = None`.".format(
                        field_name=field_name,
                        serializer_class=self.__class__.__name__
                    )
                )

                assert field_name in fields, (
                    "The field '{field_name}' was included on serializer "
                    "{serializer_class} in the 'exclude' option, but does "
                    "not match any model field.".format(
                        field_name=field_name,
                        serializer_class=self.__class__.__name__
                    )
                )
                field_names.remove(field_name)

        return field_names

    def _get_model_fields(self, model_info):
        model_field_classes = {}
        model_field_kwargs = {}
        pk_field = model_info['pk_field']

        model_field_classes[pk_field['name']] = self.model_field_mapping[pk_field['field_type']]
        model_field_kwargs[pk_field['name']] = helpers.get_kwargs_from_model_field_kwargs(pk_field)

        for field in model_info['data_fields'] + model_info['fk_fields'] + model_info['o2o_fields'] + model_info[
            'm2m_fields']:
            model_field_classes[field['name']] = self.model_field_mapping[field['field_type']]
            model_field_kwargs[field['name']] = helpers.get_kwargs_from_model_field_kwargs(field)

        assert (model_field_classes and model_field_kwargs), (
            'Model must have fields'
        )

        return model_field_classes, model_field_kwargs

    def _get_extra_kwargs(self):
        extra_kwargs = copy.deepcopy(getattr(self.Meta, 'extra_kwargs', {}))
        read_only_fields = getattr(self.Meta, 'read_only_fields', None)
        if read_only_fields is not None:
            if not isinstance(read_only_fields, (list, tuple)):
                raise TypeError(
                    'The `read_only_fields` option must be a list or tuple. '
                    'Got %s.' % type(read_only_fields).__name__
                )
            for field_name in read_only_fields:
                kwargs = extra_kwargs.get(field_name, {})
                kwargs['read_only'] = True
                extra_kwargs[field_name] = kwargs

        else:
            assert not hasattr(self.Meta, 'readonly_fields'), (
                    'Serializer `%s.%s` has field `readonly_fields`; '
                    'the correct spelling for the option is `read_only_fields`.' %
                    (self.__class__.__module__, self.__class__.__name__)
            )
        return extra_kwargs
