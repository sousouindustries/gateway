from libsousou.meta import hybrid_property
from eda import dto

from gateway.handler import ICommandHandler


class TestCommand:
    pass


class TestCommandHandler(ICommandHandler):
    foo = dto.Integer(required=True)
    bar = dto.Integer(required=True)
    baz = dto.Integer(required=True)

    @hybrid_property
    def command_type(self):
        return self.command

    def run(self, command):
        """Runs the given command."""
        result = self.handle(self.dto_class(**command.params))
        return None, result, False

    def handle(self, params):
        return None

    def validate(self, params):
        params, errors = self.schema.load(params)
        if errors:
            raise self.CommandRejected(
                reason="Invalid command parameters.",
                context=errors
            )
        return params

    class Meta:
        command = 'gateway.test.TestCommand'
