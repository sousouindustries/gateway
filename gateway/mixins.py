from gateway.exc import GatewayException


class ICommandProcessor:
    DuplicateEntity = type('DuplicateEntity', (GatewayException,), {})
    CommandRejected = type('CommandRejected', (GatewayException,), {})
    ReadOnlyMode = type('ReadOnlyMode', (GatewayException,), {})
    UpstreamFailure = type('UpstreamFailure', (GatewayException,), {})
    NotAuthorized = type('NotAuthorized', (GatewayException,), {})
    CommandFailed = type('CommandFailed', (GatewayException,), {})
