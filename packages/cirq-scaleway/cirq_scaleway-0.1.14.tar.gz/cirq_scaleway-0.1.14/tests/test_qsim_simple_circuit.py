# Copyright 2025 Scaleway
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.from typing import Optional, List, Dict
import os

import cirq

from cirq_scaleway import ScalewayQuantumService


def test_qsim_simple_circuit():
    service = ScalewayQuantumService(
        project_id=os.environ["CIRQ_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["CIRQ_SCALEWAY_SECRET_KEY"],
        url=os.environ["CIRQ_SCALEWAY_API_URL"],
    )

    qsim_simulator = service.device(name="EMU-QSIM-16C-128M")

    assert qsim_simulator is not None

    with qsim_simulator.create_session() as session:
        qubit = cirq.GridQubit(0, 0)
        circuit = cirq.Circuit(cirq.X(qubit) ** 0.5, cirq.measure(qubit, key="m"))

        # Run the circuit on the device
        shots_count = 100
        result = session.run(circuit, repetitions=shots_count)

        assert result is not None
        assert result.repetitions == shots_count
