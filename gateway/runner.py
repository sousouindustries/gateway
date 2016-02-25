from gateway.mixins import ICommandProcessor


class ICommandRunner(ICommandProcessor):

    def run(self, command):
        raise NotImplementedError
