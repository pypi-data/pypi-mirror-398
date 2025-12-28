from enum import Enum


class TransportMode(Enum):
    """Transport execution mode"""
    LOCAL = "local"
    REMOTE = "remote"


class Protocol(Enum):
    """Communication protocol"""
    A2A = "a2a"
    IN_PROC = "in-proc"