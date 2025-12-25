# =============================================================================
# Copyright (C) 2025 Commissariat a l'energie atomique et aux energies alternatives (CEA)
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the names of CEA, nor the names of the contributors may be used to
#   endorse or promote products derived from this software without specific
#   prior written  permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# =============================================================================
from typing import Protocol, Any, Callable, List, Union, Tuple, Literal

import dask.array as da
import numpy as np


class SupportsSlidingWindow(Protocol):
    class Callback(Protocol):
        def __call__(self, *window: List[da.Array], timestep: int) -> None: ...

    class ExceptionHandler(Protocol):
        def __call__(self, array_name: str, exception: BaseException) -> None: ...

    def register_sliding_window_callback(self,
                                         callback: Callback,
                                         array_name: str, window_size: int,
                                         exception_handler: ExceptionHandler) -> str: ...

    def register_sliding_window_callbacks(self,
                                          callback: Callback,
                                          *callback_args: Union[str, Tuple[str], Tuple[str, int]],
                                          exception_handler: ExceptionHandler,
                                          when: Literal['AND', 'OR'] = 'AND') -> str: ...

    def unregister_sliding_window_callback(self, *array_names: Union[str, Tuple[str]]) -> None: ...


class SupportsGetArray(Protocol):
    def get_array(self, array_name: str, timeout=None) -> tuple[da.Array, int]: ...


class IDeisa(SupportsSlidingWindow, SupportsGetArray, Protocol):

    def __init__(self, get_connection_info: Callable[[], Any], *args, **kwargs): ...

    def set(self, name: str, data: object, chunked: bool) -> None: ...

    def delete(self, key: str) -> None: ...

    def close(self) -> None: ...


class IBridge(Protocol):
    def __init__(self, id: int, arrays_metadata: dict[str, dict], system_metadata: dict[str, Any], *args, **kwargs): ...

    def send(self, array_name: str, data: np.ndarray, timestep: int, chunked: bool) -> None: ...

    def get(self, key: str, default: Any, chunked: bool, delete: bool) -> Any: ...
