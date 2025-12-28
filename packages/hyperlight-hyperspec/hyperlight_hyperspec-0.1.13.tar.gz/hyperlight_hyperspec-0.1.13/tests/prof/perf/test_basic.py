import pytest

from benchmarks.bench_validation import bench_hyperspec


@pytest.mark.benchmark(group="roundtrip")
class TestRoundtrip:
    def test_encode(self, bench, filesystem_data, shared_data):
        data = filesystem_data()
        encoded = bench(bench_hyperspec.encode, data)
        shared_data["encoded"] = encoded

    def test_decode(self, bench, shared_data):
        if shared_data["encoded"] is None:
            raise ValueError(
                "test_encode must run before test_decode to provide encoded data"
            )

        bench(bench_hyperspec.decode, shared_data["encoded"])
