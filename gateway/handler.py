from collections import namedtuple

from eda import dto

from gateway.mixins import ICommandProcessor


class ICommandHandlerMeta(type):
    ProgrammingError = type('ProgrammingError', (Exception,), {})

    def __new__(cls, name, bases, attrs):
        super_new = super(ICommandHandlerMeta, cls).__new__
        if name == 'ICommandHandler':
            return super_new(cls, name, bases, attrs)

        meta = attrs.pop('Meta', None)
        if meta is None:
            raise cls.ProgrammingError(
                "ICommandHandler implementations must define an inner Meta class.")
        if not hasattr(meta, 'command'):
            raise cls.ProgrammingError(
                "The inner Meta class must define a `command` attribute.")
        attrs['command'] = meta.command

        fields = {}
        for attname, value in list(attrs.items()):
            if not isinstance(value, dto.Field):
                continue
            fields[attname] = value
            del attrs[attname]

        attrs['dto_class'] = namedtuple('Parameters', fields.keys())
        attrs['schema_class'] = type('CommandSchema', (dto.Adapter,), fields)
        attrs['schema'] = attrs['schema_class']()


        return super_new(cls, name, bases, attrs)


class ICommandHandler(ICommandProcessor, metaclass=ICommandHandlerMeta):
    pass
