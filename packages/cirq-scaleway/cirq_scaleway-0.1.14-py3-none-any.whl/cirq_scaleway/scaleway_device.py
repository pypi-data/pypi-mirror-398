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
import cirq

from typing import Union, Optional

from scaleway_qaas_client.v1alpha1 import QaaSClient, QaaSPlatform

from cirq_scaleway.scaleway_session import ScalewaySession


class ScalewayDevice(cirq.devices.Device):
    def __init__(
        self,
        client: QaaSClient,
        platform: QaaSPlatform,
    ) -> None:
        self.__client = client
        self.__platform = platform

    def __repr__(self) -> str:
        return f"<ScalewayDevice(name={self.name},num_qubits={self.num_qubits},platform_id={self.id})>"

    @property
    def id(self) -> str:
        """The unique identifier of the platform.

        Returns:
            str: The UUID of the platform.
        """
        return self.__platform.id

    @property
    def availability(self) -> str:
        """Returns the current status of the platform.

        Returns:
            str: the current availability statys of the session. Can be either: available, shortage or scarce
        """
        platform = self.__client.get_platform(self.__platform.id)

        return platform.availability

    @property
    def name(self) -> str:
        """Name of the platform.

        Returns:
            str: the name of the platform.
        """
        return self.__platform.name

    @property
    def num_qubits(self) -> int:
        """Estimated maximum number of qubit handle of the platform.
        Estimation is done by using Quantum Volume benchmark.

        Returns:
            int: the estimated amount of maximum number of runnable qubits.
        """
        return self.__platform.max_qubit_count

    @property
    def version(self):
        """Version of the platform

        Returns:
            str: the platform's version.
        """
        return self.__platform.version

    def create_session(
        self,
        name: Optional[str] = "qsim-session-from-cirq",
        deduplication_id: Optional[str] = None,
        max_duration: Union[int, str] = "59m",
        max_idle_duration: Union[int, str] = "59m",
    ) -> ScalewaySession:
        """Create a new device session to run job against.

        Args:
            name (str): name of the session. Used only for convenient purpose.
            deduplication_id (str): an identifier you can use to clearly identify a session.
                The deduplication_id allows to retrieve a same session and to share it among people
            max_duration (str, int): the maximum duration before the session is automatically killed.
                Can be either a string like 1h, 20m15s or an int representing seconds
            max_idle_duration (str, int): the maximum duration without job before the session is automatically killed.
                Can be either a string like 1h, 20m15s or an int representing seconds
        Returns:
            ScalewaySession: a new QPU session that can be started/stopped once
        """
        return ScalewaySession(
            client=self.__client,
            device=self,
            name=name,
            deduplication_id=deduplication_id,
            max_duration=max_duration,
            max_idle_duration=max_idle_duration,
        )
