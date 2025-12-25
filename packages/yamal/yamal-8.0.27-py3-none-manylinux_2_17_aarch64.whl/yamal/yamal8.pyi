"""
    COPYRIGHT (c) 2025 by Featuremine Corporation.
    This software has been provided pursuant to a License Agreement
    containing restrictions on its use. This software contains valuable
    trade secrets and proprietary information of Featuremine Corporation
    and is protected by law. It may not be copied or distributed in any
    form or medium, disclosed to third parties, reverse engineered or used
    in any manner not provided for in said License Agreement except with
    the prior written authorization from Featuremine Corporation.
"""

from typing import Tuple

class stream:
    ''' Yamal Stream '''

    def id(self) -> int:
        ''' Stream id '''
        pass

    def seqno(self) -> int:
        ''' Stream seqno '''
        pass

    def peer(self) -> str:
        ''' Stream peer '''
        pass

    def channel(self) -> str:
        ''' Stream channel '''
        pass

    def encoding(self) -> str:
        ''' Stream encoding '''
        pass

    def write(self, time: int, data: bytes) -> None:
        ''' Write data to stream '''
        pass


class streams:
    ''' Yamal Streams '''

    def announce(self, peer: str, channel: str, encodingdata: str) -> 'stream':
        ''' Announce stream '''
        pass

    def lookup(self, peer: str, channel: str) -> Tuple[stream, str]:
        ''' Lookup for a stream '''
        pass

class yamal:
    ''' Yamal'''

    def __init__(self, path: str, readonly: bool, enable_thread: bool, closable: bool) -> None: ...

    def data(self) -> 'data':
        ''' Obtain data object '''
        pass
    
    def streams(self) -> 'streams':
        ''' Obtain streams object '''
        pass

    def announcement(self, stream: 'stream') -> Tuple[int, str, str, str]:    
        ''' Obtain the announcement details for the desired stream '''
    
class data:
    ''' Data '''

    def closable(self) -> bool:
        ''' Check if data is closable '''
        pass

    def close(self) -> None:
        ''' Close data '''
        pass

    def closed(self) -> bool:
        ''' Check if data is closed '''
        pass

    def __reversed__(self) -> 'data_reverse_iterator':
        ''' Obtain reverse iterator '''
        pass

    def seek(self, offset: int) -> 'data_iterator':
        ''' Obtain the iterator for the desired position '''
        pass

class data_iterator:
    ''' Data iterator '''    

    def __iter__(self) -> "data_iterator":
        pass

    def __reversed__(self) -> 'data_reverse_iterator':
        ''' Obtain reverse iterator '''
        pass

    def __iternext__(self) -> Tuple[int, int, 'stream', bytes]:
        pass

class data_reverse_iterator:
    ''' Data reversed iterator '''    
    pass
