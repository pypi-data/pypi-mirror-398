from typing import Optional


def td_create_client_id() -> int:
    """Returns an opaque identifier of a new TDLib instance"""

def td_send(client_id: int, request: bytes) -> None:
    """Sends request to the TDLib client. May be called from any thread"""

def td_receive(timeout: float) -> Optional[bytes]:
    """
    Receives incoming updates and request responses. Must not be called simultaneously from two different threads
    """

def td_execute(request: bytes) -> Optional[bytes]:
    """Synchronously executes a TDLib request"""
