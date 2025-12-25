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

import os
REMOTE_GPU_VERIFIER_SERVICE_URL = os.getenv("NV_NRAS_GPU_URL", "https://nras.attestation.nvidia.com/v3/attest/gpu")
REMOTE_NVSWITCH_VERIFIER_SERVICE_URL = os.getenv("NV_NRAS_NVSWITCH_URL", "https://nras.attestation.nvidia.com/v3/attest/switch")
RIM_SERVICE_URL = os.getenv("NV_RIM_URL", "https://rim.attestation.nvidia.com/v1/rim/")
OCSP_SERVICE_URL = os.getenv("NV_OCSP_URL", "https://ocsp.ndis.nvidia.com/")
ATTESTATION_SERVICE_KEY = os.getenv("NVIDIA_ATTESTATION_SERVICE_KEY")