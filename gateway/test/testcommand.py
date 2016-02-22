from libsousou.meta import hybrid_property

from gateway.handler import ICommandHandler


class TestCommand:
    pass


class TestCommandHandler(ICommandHandler):

    @hybrid_property
    def command_type(self):
        return 'gateway.test.TestCommand'

    def validate(self, params):
        params, errors = self.schema.load(params)
        if errors:
            raise self.CommandRejected(
                reason="Invalid command parameters.",
                context=errors
            )
        return params

    class Meta:
        command = TestCommand
