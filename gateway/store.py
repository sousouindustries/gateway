import json

from gateway.mixins import ICommandProcessor


class ICommandStore(ICommandProcessor):
    """Provides a layer of abstraction for the command storage
    backend.
    """
    STATE_PENDING = 'pending'
    STATE_FAILED = 'failed'
    STATE_DONE = 'done'

    def dump_params(self, params):
        return params

    def persist(self, command):
        """Persists a command in the storage backend and returns
        a context guard.
        """
        ident = self._persist(command)
        command.set_command_id(ident)
        return self.CommandTransaction(self, ident, command)

    def _persist(self, *args, **kwargs):
        raise NotImplementedError

    def set_status(self, command_id, status):
        raise NotImplementedError

    class CommandTransaction:

        def __init__(self, store, ident, command):
            self.command = command
            self.store = store
            self.ident = ident

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, exc_tb):
            if exc is not None:
                self.store.set_status(self.ident, self.store.STATE_FAILED)
