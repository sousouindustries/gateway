from collections import namedtuple


CommandRequestDTO = namedtuple('CommandRequestDTO', ['command','asynchronous','params'])
CommandResponseDTO = namedtuple('CommandResponseDTO', [
    'command_id','result'])
