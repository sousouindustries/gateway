from gateway.mixins import ICommandProcessor


class ICommandHandlerMeta(type):
    pass



class ICommandHandler(ICommandProcessor, metaclass=ICommandHandlerMeta):
    pass
