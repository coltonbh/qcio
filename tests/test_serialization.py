from qcio import SinglePointOutput


def test_serialization_to_disk_json(sp_output, tmp_path):
    """Test serialization to disk json"""

    filename = tmp_path / "sp_output.json"
    sp_output.save(filename)
    reopened = SinglePointOutput.open(filename)
    assert sp_output == reopened

    # No filename or other extension to json by default
    filename = tmp_path / "sp_output.whatever"
    sp_output.save(filename)
    reopened = SinglePointOutput.open(filename)
    assert sp_output == reopened


def test_serialization_to_disk_yaml(sp_output, tmp_path):
    """Test serialization to disk yaml"""

    filename = tmp_path / "sp_output.yaml"
    sp_output.save(filename)
    reopened = SinglePointOutput.open(filename)
    assert sp_output == reopened

    filename = tmp_path / "sp_output.yml"
    sp_output.save(filename)
    reopened = SinglePointOutput.open(filename)
    assert sp_output == reopened


def test_serialization_to_disk_toml(sp_output, tmp_path):
    """Test serialization to disk toml"""

    filename = tmp_path / "sp_output.toml"
    sp_output.save(filename)
    reopened = SinglePointOutput.open(filename)
    assert sp_output == reopened
