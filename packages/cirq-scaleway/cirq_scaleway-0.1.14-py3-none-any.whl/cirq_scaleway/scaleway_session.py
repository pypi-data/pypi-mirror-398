# Copyright 2024 Scaleway
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
# limitations under the License.
import time
import cirq
import httpx

from typing import Union, Optional, List

from qio.core import (
    QuantumProgram,
    QuantumProgramSerializationFormat,
    QuantumProgramResult,
    QuantumComputationModel,
    QuantumComputationParameters,
    BackendData,
    ClientData,
)

from scaleway_qaas_client.v1alpha1 import (
    QaaSClient,
    QaaSJobResult,
)

from cirq_scaleway.versions import USER_AGENT


_DEFAULT_FETCH_INTERVAL = 2  # in second
_DEFAULT_TIMEOUT = 60 * 360  # in second


class ScalewaySession(cirq.work.Sampler):
    def __init__(
        self,
        device,
        client: QaaSClient,
        name: Optional[str],
        deduplication_id: Optional[str],
        max_duration: Union[int, str],
        max_idle_duration: Union[int, str],
    ):
        self.__id = None
        self.__device = device
        self.__client = client
        self.__name = name
        self.__deduplication_id = deduplication_id
        self.__max_duration = max_duration
        self.__max_idle_duration = max_idle_duration

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.stop()
        return False

    def __repr__(self) -> str:
        return f"<ScalewaySession(name={self.__name},dedup_id={self.__deduplication_id},id={self.__id}),status={self.status}>"

    @property
    def status(self) -> str:
        """Returns the current status of the device session.

        Returns:
            str: the current status of the session. Can be either: starting, runnng, stopping, stopped
        """
        if not self.__id:
            return "unknown_status"

        session = self.__client.get_session(session_id=self.__id)

        return session.status

    @property
    def id(self) -> str:
        """The unique identifier of the device session.

        Returns:
            str: The UUID of the current session.
        """
        return self.__id

    @property
    def name(self) -> str:
        """Name of the device session.

        Returns:
            str: the session's name.
        """
        return self.__name

    def start(self) -> "ScalewaySession":
        """Starts a new device session to run job against it.

        Args:
            name (str): name of the session. Used only for convenient purpose.
            deduplication_id (str): an identifier you can use to clearly identify a session.
                The deduplication_id allows to retrieve a same session and to share it among people
            max_duration (str, int): the maximum duration before the session is automatically killed.
                Can be either a string like 1h, 20m15s or an int representing seconds
            max_idle_duration (str, int): the maximum duration without job before the session is automatically killed.
                Can be either a string like 1h, 20m15s or an int representing seconds
        Returns:
            ScalewaySession: a new freshly starting QPU session
        """
        if self.__id:
            raise Exception("session already started")

        self.__id = self.__client.create_session(
            name=self.__name,
            platform_id=self.__device.id,
            deduplication_id=self.__deduplication_id,
            max_duration=self.__max_duration,
            max_idle_duration=self.__max_idle_duration,
        ).id

        return self

    def stop(self) -> "ScalewaySession":
        """Stops to the running device session.
        All attached jobs and their results will are kept up to 7 days before total deletion.
        """
        if not self.__id:
            raise Exception("session not started")

        self.__client.terminate_session(session_id=self.__id)

        return self

    def delete(self) -> None:
        """Immediately stop and delete to the running device session.
        All attached jobs and their results will be purged from Scaleway service.
        """
        if not self.__id:
            raise Exception("session not started")

        self.__client.delete_session(session_id=self.__id)

    def run_sweep(
        self,
        program: cirq.AbstractCircuit,
        params: cirq.study.Sweepable,
        repetitions: int = 1,
    ) -> List[cirq.study.Result]:
        """Samples from the given Circuit.

        This allows for sweeping over different parameter values,
        unlike the `run` method.  The `params` argument will provide a
        mapping from `sympy.Symbol`s used within the circuit to a set of
        values.  Unlike the `run` method, which specifies a single
        mapping from symbol to value, this method allows a "sweep" of
        values.  This allows a user to specify execution of a family of
        related circuits efficiently.

        Args:
            program: The circuit to sample from.
            params: Parameters to run with the program.
            repetitions: The number of times to sample.

        Returns:
            Result list for this run; one for each possible parameter resolver.
        """
        trial_results = []

        if not self.__id:
            raise Exception("session not started")

        # Keep Cirq format by default for qsim backends
        default_format = (
            QuantumProgramSerializationFormat.CIRQ_CIRCUIT_JSON_V1
            if "qsim" in self.__device.name.lower()
            else QuantumProgramSerializationFormat.QASM_V3
        )

        for param_resolver in cirq.study.to_resolvers(params):
            circuit = cirq.protocols.resolve_parameters(program, param_resolver)
            program = QuantumProgram.from_cirq_circuit(circuit, default_format)

            results = self._submit(program, repetitions, self.__id, params)
            trial_results.append(results)

        return trial_results

    def _extract_payload_from_response(
        self, job_result: QaaSJobResult
    ) -> QuantumProgramResult:
        result = job_result.result

        if result is None or result == "":
            url = job_result.url

            if url is not None:
                resp = httpx.get(url)
                resp.raise_for_status()
                result = resp.text
            else:
                raise RuntimeError("Got result with empty data and url fields")

        return QuantumProgramResult.from_json_str(result)

    def _wait_for_result(
        self,
        job_id: str,
        fetch_interval: int,
        timeout: Optional[int] = None,
    ) -> List[QaaSJobResult] | None:
        start_time = time.time()

        while True:
            time.sleep(fetch_interval)

            elapsed = time.time() - start_time

            if timeout is not None and elapsed >= timeout:
                raise RuntimeError("Timed out waiting for result")

            job = self.__client.get_job(job_id)

            if job.status == "completed":
                return self.__client.list_job_results(job_id)

            if job.status in ["error", "unknown_status"]:
                raise RuntimeError(f"Job failed: {job.progress_message}")

    def _submit(
        self, program: QuantumProgram, shots: int, session_id: str, params
    ) -> cirq.study.Result:
        backend_data = BackendData(
            name=self.__device.name,
            version=self.__device.version,
        )

        client_data = ClientData(
            user_agent=USER_AGENT,
        )

        computation_model_json = QuantumComputationModel(
            programs=[program],
            backend=backend_data,
            client=client_data,
        ).to_json_str()

        computation_parameters_json = QuantumComputationParameters(
            shots=shots,
        ).to_json_str()

        model = self.__client.create_model(
            payload=computation_model_json,
        )

        if not model:
            raise RuntimeError("Failed to push circuit data")

        job_id = self.__client.create_job(
            session_id=session_id,
            model_id=model.id,
            parameters=computation_parameters_json,
        ).id

        job_results = self._wait_for_result(
            job_id, _DEFAULT_FETCH_INTERVAL, _DEFAULT_TIMEOUT
        )

        if len(job_results) != 1:
            raise RuntimeError("Expected a single result for Cirq job")

        result = self._extract_payload_from_response(job_results[0]).to_cirq_result(
            params=params
        )

        return result
