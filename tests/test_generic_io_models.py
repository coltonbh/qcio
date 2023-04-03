import json

from qcio import GenericFileInput


def test_from_directory(test_data_dir):
    generic_inp = GenericFileInput.from_directory(
        directory=test_data_dir / "generic_inputs",
        program="terachem",
        extras={"my_extra": "123"},
    )

    assert generic_inp.specification.program == "terachem"
    assert generic_inp.extras == {"my_extra": "123"}
    for filename, file in generic_inp.specification.files.items():
        data = (test_data_dir / "generic_inputs" / filename).read_bytes()
        try:
            str_data = data.decode("utf-8")
        except UnicodeDecodeError:
            assert file.data == data
        else:
            assert file.data == str_data


def test_to_directory(test_data_dir, tmp_path):
    generic_inp = GenericFileInput.from_directory(
        directory=test_data_dir / "generic_inputs",
        program="terachem",
        extras={"my_extra": "123"},
    )
    generic_inp.to_directory(tmp_path)
    for filename in generic_inp.specification.files:
        # Ensure files were written
        assert (tmp_path / filename).exists()
        # Ensure files are identical to input files
        assert (tmp_path / filename).read_bytes() == (
            test_data_dir / "generic_inputs" / filename
        ).read_bytes()


def test_to_from_file_with_binary_data(test_data_dir, tmp_path):
    generic_inp = GenericFileInput.from_directory(
        directory=test_data_dir / "generic_inputs",
        program="terachem",
        extras={"my_extra": "123"},
    )
    # Ensure that we have binary data
    assert isinstance(generic_inp.specification.files["c0"].data, bytes)
    # Write GenericInput to disk using .json() serialization
    generic_inp.to_file(tmp_path / "generic_input.json")
    # Ensure data was properly json serialized
    data = json.loads((tmp_path / "generic_input.json").read_text())
    assert data["specification"]["files"]["c0"]["data"].startswith("base64:")
    # Parse GenericInput from disk using deserialization
    generic_inp_reloaded = GenericFileInput.from_file(tmp_path / "generic_input.json")
    # Assure all data returned to correct bytes or str representation
    assert generic_inp_reloaded == generic_inp
