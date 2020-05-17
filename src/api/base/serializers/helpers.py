ALL_FIELDS = '__all__'


def check_model_meta(f):
    def wrapper(self, *args, **kwargs):
        assert hasattr(self, 'Meta'), (
            'Class {serializer_class} missing "Meta" attribute'.format(
                serializer_class=self.__class__.__name__
            )
        )

        assert hasattr(self.Meta, 'model'), (
            'Class {serializer_class} missing "Meta.model" attribute'.format(
                serializer_class=self.__class__.__name__
            )
        )

        if self.Meta.model._meta.abstract:
            raise ValueError(
                'Cannot use ModelSerializer with Abstract Models.'
            )

        fields = getattr(self.Meta, 'fields', None)
        exclude = getattr(self.Meta, 'exclude', None)
        if fields and fields != ALL_FIELDS and not isinstance(fields, (list, tuple)):
            raise TypeError(
                'The `fields` option must be a list or tuple or "__all__". '
                'Got %s.' % type(fields).__name__
            )

        if exclude and not isinstance(exclude, (list, tuple)):
            raise TypeError(
                'The `exclude` option must be a list or tuple. Got %s.' %
                type(exclude).__name__
            )

        assert not (fields and exclude), (
            "Cannot set both 'fields' and 'exclude' options on "
            "serializer {serializer_class}.".format(
                serializer_class=self.__class__.__name__
            )
        )

        assert not (fields is None and exclude is None), (
            "Creating a ModelSerializer without either the 'fields' attribute "
            "or the 'exclude' attribute has been deprecated since 3.3.0, "
            "and is now disallowed. Add an explicit fields = '__all__' to the "
            "{serializer_class} serializer.".format(
                serializer_class=self.__class__.__name__
            ),
        )
        return f(self, *args, **kwargs)

    return wrapper


def get_field_class_from_model(field_name, model_field_classes):
    return model_field_classes.get(field_name, None)


def get_field_kwargs_from_model(field_name, model_field_kwargs):
    return model_field_kwargs.get(field_name, {})


def get_kwargs_from_model_field_kwargs(filed_kwargs):
    return {
        'name': filed_kwargs['name'],
        'nullable': filed_kwargs['nullable'],
        'unique': filed_kwargs['unique'],
        'default': filed_kwargs['default']
    }


def include_extra_kwargs(kwargs, extra_kwargs):
    if extra_kwargs.get('read_only', False):
        for attr in [
            'required', 'default', 'allow_blank', 'allow_null',
            'min_length', 'max_length', 'min_value', 'max_value',
            'validators', 'queryset'
        ]:
            kwargs.pop(attr, None)

    if extra_kwargs.get('default') and kwargs.get('required') is False:
        kwargs.pop('required')

    if extra_kwargs.get('read_only', kwargs.get('read_only', False)):
        extra_kwargs.pop('required', None)  # Read only fields should always omit the 'required' argument.

    kwargs.update(extra_kwargs)

    return kwargs
