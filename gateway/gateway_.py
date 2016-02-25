import logging

from eda import dto
import ioc

from gateway.dto import CommandResponseDTO
from gateway.exc import GatewayException
from gateway.mixins import ICommandProcessor


class Gateway(ICommandProcessor):
    """The gateway to which commands are issued."""
    handlers = ioc.instance('CommandHandlersProvider')
    runner = ioc.instance('CommandRunner')
    store = ioc.instance('CommandStore')
    readonly_message = None
    logger = logging.getLogger('gateway')

    class schema_class(dto.Adapter):
    
        class Meta:
            fields = ['command_id','timestamp','status',
                'host','command_type','issuer','authenticated_by']

    def __init__(self):
        self.schema = self.schema_class(many=True, strict=True)

    def get_commands(self, *args, **kwargs):
        """Return a list containing the issued commands using the
        specified criteria.
        """
        result, errors = self.schema.dump(self.store.get_commands(*args, **kwargs))
        return result

    def is_readonly_mode(self):
        """Return a boolean indicating if the system is in readonly mode."""
        return False

    def issue(self, command):
        """Invoke the handler for the given command.
        
        Args:
            command: a :class:`gateway.dto.CommandRequestDTO` instance.

        Returns:
            gateway.dto.CommandResponseDTO
        """
        if self.is_readonly_mode():
            raise self.ReadOnlyMode(reason=self.readonly_message)

        command = self.validate(command)

        # If the command is valid, it should be persisted in the command store.
        with self.store.persist(command) as tx:
            assert command.id is not None
            try:
                result = self.runner.execute(command)
            except self.CommandFailed:
                self.logger.exception(
                    "Caught fatal exception during handling of command (id: {0})."\
                        .format(tx.ident)
                )
                raise

        response = CommandResponseDTO(tx.ident, *result)
        if response.done:
            self.store.set_status(response.command_id, self.store.STATE_DONE)

        return response

    def validate(self, command):
        # Validate the command parameters. If the parameters could not be
        # validated, the command is immediately rejected. Commands are
        # only persisted when their parameters are valid. Thus, the validate()
        # method of the command runner is expected to raise a CommandRejected
        # exception if there are validation errors.
        return self.handlers.validate(command)
