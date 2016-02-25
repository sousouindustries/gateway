import logging
import threading 

import ioc

from gateway.runner import ICommandRunner


class CommandRunner(ICommandRunner):
    handlers = ioc.instance('CommandHandlersProvider')
    logger = logging.getLogger('gateway')
    store = ioc.instance('CommandStore')

    def execute(self, command):
        error = False
        try:
            ident, result, created = self.run(command)\
                if not command.asynchronous\
                else self.run_asynchronous(command)
        except Exception as e:
            raise self.CommandFailed

        return ident, result, not command.asynchronous and not error, created, error

    def run(self, command):
        """Run the given command.

        Args:
            command: a :class:`CommandRequestDTO` instance.
        """
        handler = self.handlers.get(command.command)
        return handler.run(command)

    def run_asynchronous(self, command):
        """Run a command asynchronously.

        Args:
            command: a :class:`CommandRequestDTO` instance.
        """
        assert command.id is not None
        handler = self.handlers.get(command.command)
        t = threading.Thread(target=self._async, args=[handler, command])
        t.start()
        return None, None, False

    def _async(self, handler, command):
        try:
            handler.run(command)
            self.store.set_status(command.id, self.store.STATE_DONE)
        except Exception as e:
            self.store.set_status(command.id, self.store.STATE_FAILED)
            self.logger.exception(
                "Caught fatal exception during handling of command (id: {0})."\
                    .format(command.id)
            )
            raise
