import ioc

from gateway.exc import GatewayException
from gateway.mixins import ICommandProcessor


class Gateway(ICommandProcessor):
    """The gateway to which commands are issued."""
    handlers = ioc.instance('CommandHandlersProvider')
    runner = ioc.instance('CommandRunner')
    store = ioc.instance('CommandStore')
    readonly_message = None

    def is_readonly_mode(self):
        """Return a boolean indicating if the system is in readonly mode."""
        return False

    def issue(self, command, principal=None, authenticated_by=None):
        """Invoke the handler for the given command.
        
        Args:
            command: a :class:`gateway.dto.CommandRequestDTO` instance.
            principal: identifies the principal that issued the command.
            authenticated_by: identifies the principal that authenticated
                the issuer.

        Returns:
            gateway.dto.CommandResponseDTO
        """
        if self.is_readonly_mode():
            raise self.ReadOnlyMode(reason=self.readonly_message)

        # Validate the command parameters. If the parameters could not be
        # validated, the command is immediately rejected. Commands are
        # only persisted when their parameters are valid. Thus, the validate()
        # method of the command runner is expected to raise a CommandRejected
        # exception if there are validation errors.
        command = self.handlers.validate(command)

        # If the command is valid, it should be persisted in the command store.
        with self.store.persist(command, principal, authenticated_by) as tx:
            result, created, failed = self.runner.run(command)
            if failed:
                tx.failed()
            else:
                tx.done()

            response = CommandResponseDTO(
                command_id=tx.command_id,
                result=result,
                success=not failed
            )

        return response


