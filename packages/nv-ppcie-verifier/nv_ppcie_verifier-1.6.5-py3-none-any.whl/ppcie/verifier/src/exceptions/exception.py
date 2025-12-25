# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module declares the generic base exceptions and inherited
exceptions for PPCIE interactions"""

from ..utils.logging import get_logger

logger = get_logger()


class PpcieVerifierException(Exception):
    """PpcieVerifierException is thrown when the user faces issues
    while using the ppcie-verifier to verify the GPUs/Nvswitches"""


class GpuPreChecksException(PpcieVerifierException):
    """GpuPreChecksException is thrown when the user faces issues
    while using the ppcie-verifier to verify the TNVL mode of the GPUs"""


class SwitchPreChecksException(PpcieVerifierException):
    """SwitchPreChecksException is thrown when the user faces issues
    while using the ppcie-verifier to verify the TNVL/LOCK mode of the Switches"""


class GpuAttestationException(PpcieVerifierException):
    """GpuAttestationException is thrown when the user faces issues
    while using the ppcie-verifier to attest the GPUs"""


class SwitchAttestationException(PpcieVerifierException):
    """SwitchAttestationException is thrown when the user faces issues
    while using the ppcie-verifier to attest the Switches"""
