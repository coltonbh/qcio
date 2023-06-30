from qcio import SinglePointSuccessfulOutput


def test_serialization_to_disk_json(sp_successful_output, tmp_path):
    """Test serialization to disk json"""

    filename = tmp_path / "sp_output.json"
    sp_successful_output.save(filename)
    reopened = SinglePointSuccessfulOutput.open(filename)
    assert sp_successful_output == reopened

    # No filename or other extension to json by default
    filename = tmp_path / "sp_output.whatever"
    sp_successful_output.save(filename)
    reopened = SinglePointSuccessfulOutput.open(filename)
    assert sp_successful_output == reopened


def test_serialization_to_disk_yaml(sp_successful_output, tmp_path):
    """Test serialization to disk yaml"""

    filename = tmp_path / "sp_output.yaml"
    sp_successful_output.save(filename)
    reopened = SinglePointSuccessfulOutput.open(filename)
    assert sp_successful_output == reopened

    filename = tmp_path / "sp_output.yml"
    sp_successful_output.save(filename)
    reopened = SinglePointSuccessfulOutput.open(filename)
    assert sp_successful_output == reopened


def test_serialization_to_disk_toml(sp_successful_output, tmp_path):
    """Test serialization to disk toml"""

    filename = tmp_path / "sp_output.toml"
    sp_successful_output.save(filename)
    reopened = SinglePointSuccessfulOutput.open(filename)
    assert sp_successful_output == reopened
