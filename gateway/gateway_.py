from gateway.exc import GatewayException


class Gateway:
    """The gateway to which commands are issued."""
    DuplicateEntity = type('DuplicateEntity', (GatewayException,), {})
    CommandRejected = type('CommandRejected', (GatewayException,), {})
    ReadOnlyMode = type('ReadOnlyMode', (GatewayException,), {})
    UpstreamFailure = type('UpstreamFailure', (GatewayException,), {})
    NotAuthorized = type('NotAuthorized', (GatewayException,), {})
