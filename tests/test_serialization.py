from qcio import SinglePointResult


def test_serialization_to_disk_json(sp_result, tmp_path):
    """Test serialization to disk json"""

    filename = tmp_path / "sp_output.json"
    sp_result.save(filename)
    reopened = SinglePointResult.open(filename)
    assert sp_result == reopened

    # No filename or other extension to json by default
    filename = tmp_path / "sp_output.whatever"
    sp_result.save(filename)
    reopened = SinglePointResult.open(filename)
    assert sp_result == reopened


def test_serialization_to_disk_yaml(sp_result, tmp_path):
    """Test serialization to disk yaml"""

    filename = tmp_path / "sp_output.yaml"
    sp_result.save(filename)
    reopened = SinglePointResult.open(filename)
    assert sp_result == reopened

    filename = tmp_path / "sp_output.yml"
    sp_result.save(filename)
    reopened = SinglePointResult.open(filename)
    assert sp_result == reopened


def test_serialization_to_disk_toml(sp_result, tmp_path):
    """Test serialization to disk toml"""

    filename = tmp_path / "sp_output.toml"
    sp_result.save(filename)
    reopened = SinglePointResult.open(filename)
    assert sp_result == reopened
