import json

from qcio.models import Files


def test_binary_file(test_data_dir, tmp_path):
    input_filepath = test_data_dir / "file_inputs" / "c0"
    mixin = Files()
    mixin.open_file(input_filepath)
    assert isinstance(mixin.files[input_filepath.name], bytes)
    mixin.save_files(tmp_path)
    # Round trip of file is lossless
    assert (tmp_path / "c0").read_bytes() == input_filepath.read_bytes()


def test_str_file(test_data_dir, tmp_path):
    input_filepath = test_data_dir / "file_inputs" / "tc.in"
    mixin = Files()
    mixin.open_file(input_filepath)
    assert isinstance(mixin.files[input_filepath.name], str)
    mixin.save_files(tmp_path)
    # Round trip of file is lossless
    assert (tmp_path / "tc.in").read_text() == input_filepath.read_text()


def test_file_b64(test_data_dir):
    input_filepath = test_data_dir / "file_inputs" / "c0"
    mixin = Files()
    mixin.open_file(input_filepath)
    assert isinstance(mixin.files[input_filepath.name], bytes)
    json_str = mixin.model_dump_json()
    json_dict = json.loads(json_str)
    assert json_dict["files"][input_filepath.name].startswith("base64:")
    mixin_new = mixin.model_validate_json(json_str)
    # Round trip of file is lossless
    assert mixin_new.files["c0"] == input_filepath.read_bytes()


def test_dump_files(test_data_dir, tmp_path):
    data_dir = test_data_dir / "file_inputs"
    mixin = Files()
    mixin.open_file(data_dir / "c0")
    mixin.open_file(data_dir / "tc.in")
    mixin.save_files(tmp_path)

    assert (tmp_path / "c0").read_bytes() == (data_dir / "c0").read_bytes()
    assert (tmp_path / "tc.in").read_text() == (data_dir / "tc.in").read_text()


def test_files_recursive(test_data_dir, tmp_path):
    data_dir = test_data_dir / "file_inputs"
    mixin = Files()
    mixin.open_files(data_dir, recursive=True)
    mixin.save_files(tmp_path)

    for filename in mixin.files.keys():
        assert (tmp_path / filename).exists()
        assert (tmp_path / filename).read_bytes() == (data_dir / filename).read_bytes()
