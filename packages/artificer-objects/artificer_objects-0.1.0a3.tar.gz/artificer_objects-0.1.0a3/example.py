from pathlib import Path

from fastmcp import FastMCP
from pydantic import BaseModel

from artificer.objects import Object

mcp = FastMCP()


class FileSystemObjectModel(BaseModel):
    """Schema for file system objects."""

    name: str
    content: str


class FileSystemObject(Object):
    """Object store backed by the file system."""

    model = FileSystemObjectModel

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def read(self, name: str) -> FileSystemObjectModel:
        """Read an object from the filesystem."""
        file_path = self.path / f"{name}.json"
        with open(file_path, "r") as f:
            data = f.read()
        return FileSystemObjectModel.model_validate_json(data)

    def write(self, name: str, data: FileSystemObjectModel) -> None:
        """Write an object to the filesystem."""
        file_path = self.path / f"{name}.json"
        with open(file_path, "w") as f:
            f.write(data.model_dump_json())

    def delete(self, name: str) -> None:
        """Delete an object from the filesystem."""
        file_path = self.path / f"{name}.json"
        file_path.unlink()

    def exists(self, name: str) -> bool:
        """Check if an object exists in the filesystem."""
        file_path = self.path / f"{name}.json"
        return file_path.exists()

    def list_objects(self) -> list[str]:
        """List all objects in the store."""
        return [f.stem for f in self.path.glob("*.json")]


if __name__ == "__main__":
    # Register the object type with MCP
    # This adds generic tools: read_object, write_object, list_objects, etc.
    # Using default=True means this type is used when object_type is not specified
    FileSystemObject.register(mcp, FileSystemObject("/tmp/objects"), default=True)
    mcp.run()
