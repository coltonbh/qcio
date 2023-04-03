"""Basic file I/O objects for QC calculations."""

from pathlib import Path
from typing import Any, Dict, Union

from typing_extensions import Self

from .abc_io import InputBase, SpecificationBase, SuccessfulResultBase
from .file import File


class GenericFileInput(InputBase):
    """Generic file-based inputs for a calculation."""

    @classmethod
    def from_directory(
        cls,
        *,
        directory: Union[str, Path],
        program: str,
        extras: Dict[str, Any],
    ) -> Self:
        """Create a GenericFileInput from a directory."""
        directory = Path(directory)

        files = {}
        for filepath in directory.glob("*"):
            if filepath.is_file():
                data = filepath.read_bytes()
                try:
                    file = File(data=data.decode("utf-8"))
                except UnicodeDecodeError:
                    file = File(data=data)
                files[filepath.name] = file

        return cls(spec=SpecificationBase(program=program, files=files), extras=extras)

    def to_directory(self, directory: Union[str, Path] = Path(".")) -> None:
        """Write files to a directory."""
        directory = Path(directory)
        directory.mkdir(exist_ok=True)
        for filename, file in self.spec.files.items():
            file.to_disk(directory / filename)


class GenericFileResult(SuccessfulResultBase):
    """Generic result class for pure file based I/O."""

    input_data: GenericFileInput
