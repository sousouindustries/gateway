import importlib
import inspect
import logging

from gateway.mixins import ICommandProcessor
from gateway.handler import ICommandHandler


import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class CommandHandlersProvider(ICommandProcessor):
    logger = logging.getLogger('gateway.environment')

    def __init__(self):
        self.__handlers = {}
        self.register_module('gateway.test')

    def register_module(self, module_path):
        """Registers all command handlers in a module identified by `module_path`,
        that is all classes inheriting from :class:`gateway.handler.ICommandHandler`.
        """
        success = False
        handlers = {}
        try:
            module = importlib.import_module(module_path)
            for attname, value in module.__dict__.items():
                if not inspect.isclass(value)\
                or not issubclass(value, ICommandHandler):
                    continue

                command_type = value.command_type
                if command_type in self.__handlers:
                    raise self.HandlerAlreadyRegistered

                handlers[value.command_type] = value()
                self.logger.info("Succesfully registered " + command_type)

            success = True
        except ImportError:
            self.logger.warning(
                "Unable to import handlers from module " + module_path)
        except Exception:
            self.logger.exception(
                "Caught exception while importing " + module_path)

        if success:
            self.__handlers.update(handlers)

        return success

    def validate(self, command):
        """Validates the command parameters. Raises
        :class:`gateway.exc.CommandRejected`  if the parameters are
        not valid.
        """
        handler = self.get(command.command)
        params = handler.validate(command.params)
        for key in list(command.params.keys()):
            value = command.params.pop(key)
            if key in params:
                command.params[key] = params[key]
        return command

    def get(self, command_type):
        """Get the handler for the command of type `command_type`."""
        try:
            return self.__handlers[command_type]
        except KeyError:
            raise self.CommandRejected(reason="Unknown command: " + command_type)
