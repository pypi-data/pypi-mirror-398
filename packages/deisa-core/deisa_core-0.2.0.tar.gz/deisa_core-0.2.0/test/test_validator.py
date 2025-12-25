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

import pytest

from common import dask_env, ray_env
from deisa.core import validate_system_metadata, validate_arrays_metadata


@pytest.mark.parametrize("env_setup", [dask_env.__name__, ray_env.__name__])
class TestSystemMetadata:
    def test_valid_metadata(self, request, env_setup):
        conn, _ = request.getfixturevalue(env_setup)
        metadata = {"connection": conn, "nb_bridges": 3}
        assert validate_system_metadata(metadata) == metadata

    def test_not_a_dict(self, request, env_setup):
        with pytest.raises(TypeError):
            validate_system_metadata("not a dict")

    def test_missing_connection_key(self, request, env_setup):
        metadata = {"nb_bridges": 1}
        with pytest.raises(ValueError):
            validate_system_metadata(metadata)

    def test_wrong_connection_type(self, request, env_setup):
        metadata = {"connection": 123, "nb_bridges": 1}
        with pytest.raises(ValueError):
            validate_system_metadata(metadata)

    def test_missing_nb_bridges_key(self, request, env_setup):
        conn, _ = request.getfixturevalue(env_setup)
        metadata = {"connection": conn}
        with pytest.raises(ValueError):
            validate_system_metadata(metadata)

    def test_wrong_nb_bridges_type(self, request, env_setup):
        conn, _ = request.getfixturevalue(env_setup)
        metadata = {"connection": conn, "nb_bridges": "not-an-int"}
        with pytest.raises(ValueError):
            validate_system_metadata(metadata)


class TestArraysMetadata:
    def test_valid_arrays_metadata(self):
        metadata = {
            'global_t': {
                'size': [20, 20],
                'subsize': [10, 10]
            },
            'global_p': {
                'size': [100, 100],
                'subsize': [50, 50]
            }
        }

        assert validate_arrays_metadata(metadata) == metadata

    def test_not_a_dict(self):
        with pytest.raises(TypeError):
            validate_arrays_metadata("not-a-dict")

    def test_key_not_string(self):
        metadata = {
            42: {
                'size': [1, 1],
                'subsize': [1, 1]
            }
        }
        with pytest.raises(TypeError):
            validate_arrays_metadata(metadata)

    def test_value_not_dict(self):
        metadata = {
            'global_t': "not-a-dict"
        }
        with pytest.raises(TypeError):
            validate_arrays_metadata(metadata)

    def test_missing_required_keys(self):
        metadata = {
            'global_t': {
                'size': [10, 10]
            }
        }
        with pytest.raises(ValueError):
            validate_arrays_metadata(metadata)

    def test_extra_keys(self):
        metadata = {
            'global_t': {
                'size': [10, 10],
                'subsize': [5, 5],
                'foo': 123
            }
        }
        with pytest.raises(ValueError):
            validate_arrays_metadata(metadata)

    def test_size_not_iterable(self):
        metadata = {
            'global_t': {
                'size': 123,
                'subsize': [5, 5]
            }
        }
        with pytest.raises(TypeError):
            validate_arrays_metadata(metadata)

    def test_subsize_not_iterable(self):
        metadata = {
            'global_t': {
                'size': [10, 10],
                'subsize': 123
            }
        }
        with pytest.raises(TypeError):
            validate_arrays_metadata(metadata)

    def test_size_contains_non_int(self):
        metadata = {
            'global_t': {
                'size': [10, "x"],
                'subsize': [5, 5]
            }
        }
        with pytest.raises(TypeError):
            validate_arrays_metadata(metadata)

    def test_subsize_contains_non_int(self):
        metadata = {
            'global_t': {
                'size': [10, 10],
                'subsize': ["a", 5]
            }
        }
        with pytest.raises(TypeError):
            validate_arrays_metadata(metadata)

    def test_size_subsize_mismatch(self):
        metadata = {
            'global_t': {
                'size': [10, 10, 10],
                'subsize': [5, 5]
            }
        }
        with pytest.raises(ValueError):
            validate_arrays_metadata(metadata)
