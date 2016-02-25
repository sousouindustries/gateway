from collections import namedtuple


CommandResponseDTO = namedtuple('CommandResponseDTO', [
    'command_id','ident', 'result','done','created','error'])


class CommandRequestDTO:
    fields = ['id','command','asynchronous', 'params','issuer','authenticated_by','host']

    def __init__(self, id, command, asynchronous, params, issuer, authenticated_by, host):
        self.id = id
        self.command = command
        self.asynchronous = asynchronous
        self.params = params
        self.issuer = issuer
        self.authenticated_by = authenticated_by
        self.host = host

    def set_command_id(self, ident):
        self.id = ident
