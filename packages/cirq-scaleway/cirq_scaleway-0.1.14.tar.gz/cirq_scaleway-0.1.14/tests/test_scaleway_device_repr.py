from cirq_scaleway.scaleway_device import ScalewayDevice


class _FakePlatform:
    def __init__(self):
        self.id = "p-123"
        self.name = "qsim_test"
        self.version = "0.0"
        self.max_qubit_count = 5


class _FakeClient:
    pass


def test_scaleway_device_repr():
    dev = ScalewayDevice(client=_FakeClient(), platform=_FakePlatform())
    s = repr(dev)
    assert "ScalewayDevice" in s
    assert "name=qsim_test" in s
    assert "num_qubits=5" in s
    assert "platform_id=p-123" in s
