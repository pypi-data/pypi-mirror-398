from ttex.log import capture_snapshot
import os


def test_capture_snapshot():
    file_name = "test_snapshot.json"
    snapshot = capture_snapshot(
        file_name,
        extra_info={"test_key": "test_value"},
        extra_sensitive_keys=["HOSTNAME"],
    )
    assert isinstance(snapshot, dict)
    # Check for some expected keys in the snapshot
    expected_keys = ["cpu", "memory", "compilers", "env_vars"]
    for key in expected_keys:
        assert key in snapshot
    # Check that sensitive environment variables are redacted
    assert snapshot.get("env_vars", {}).get("GPG_KEY") == "<REDACTED>"
    assert snapshot.get("env_vars", {}).get("HOSTNAME") == "<REDACTED>"
    # Check that the extra info is included
    assert snapshot.get("custom_info", {}).get("test_key") == "test_value"
    # Check that the file is created
    assert os.path.exists(file_name)
    os.remove(file_name)
