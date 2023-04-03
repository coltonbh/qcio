import json

from qcio import File


def test_binary_file(test_data_dir, tmp_path):
    input_filepath = test_data_dir / "generic_inputs" / "c0"
    file = File.from_disk(input_filepath)
    assert isinstance(file.data, bytes)
    file.to_disk(tmp_path / "c0")
    # Round trip of file is lossless
    assert (tmp_path / "c0").read_bytes() == input_filepath.read_bytes()


def test_str_file(test_data_dir, tmp_path):
    input_filepath = test_data_dir / "generic_inputs" / "tc.in"
    file = File.from_disk(input_filepath)
    assert isinstance(file.data, str)
    file.to_disk(tmp_path / "tc.in")
    # Round trip of file is lossless
    assert (tmp_path / "tc.in").read_text() == input_filepath.read_text()


def test_file_b64(test_data_dir):
    input_filepath = test_data_dir / "generic_inputs" / "c0"
    file = File.from_disk(input_filepath)
    assert isinstance(file.data, bytes)
    json_str = file.json()
    json_dict = json.loads(json_str)
    assert json_dict["data"].startswith("base64:")
    file = File.parse_raw(json_str)
    # v2
    # file = File.model_validate_json(json_dict["data"])
    # Round trip of file is lossless
    assert file.data == input_filepath.read_bytes()
