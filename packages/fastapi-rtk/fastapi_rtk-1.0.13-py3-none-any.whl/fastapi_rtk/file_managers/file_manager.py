import os
import os.path as op
import shutil

from ..bases.file_manager import AbstractFileManager
from ..setting import Setting
from ..utils import lazy, secure_filename, smart_run

__all__ = ["FileManager"]


class FileManager(AbstractFileManager):
    """
    FileManager that handles file operations such as saving, retrieving, and deleting files from the application's upload folder.
    """

    base_path = lazy(lambda: Setting.UPLOAD_FOLDER)
    allowed_extensions = lazy(lambda: Setting.FILE_ALLOWED_EXTENSIONS)

    def post_init(self):
        if not self.base_path:
            raise ValueError("UPLOAD_FOLDER not set in config.")
        if not op.exists(self.base_path):
            os.makedirs(self.base_path, self.permission)

    def get_path(self, filename):
        return op.join(self.base_path, filename)

    def get_file(self, filename):
        _, path = self.generate_secure_filename(filename)
        with open(path, "rb") as f:
            return f.read()

    async def stream_file(self, filename):
        _, path = self.generate_secure_filename(filename)
        with open(path, "rb") as f:
            while chunk := await smart_run(f.read, 8192):
                yield chunk

    def save_file(self, file_data, filename):
        _, path = self.generate_secure_filename(filename)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file_data.file, buffer)
        return path

    def save_content_to_file(self, content, filename):
        _, path = self.generate_secure_filename(filename)
        with open(path, "wb") as buffer:
            buffer.write(content)
        return path

    def delete_file(self, filename):
        _, path = self.generate_secure_filename(filename)
        if op.exists(path):
            os.remove(path)

    def file_exists(self, filename):
        _, path = self.generate_secure_filename(filename)
        return op.exists(path)

    def generate_secure_filename(self, filename):
        """
        Generates a secure filename by using the `secure_filename` function from the Werkzeug library.

        Also creates the directory where the file will be saved if it doesn't exist.

        Args:
            filename (str): The original filename.

        Returns:
            tuple: A tuple containing the secured filename and the path where the file will be saved.
        """
        secured_filename = secure_filename(filename)
        path = self.get_path(secured_filename)
        if not op.exists(op.dirname(path)):
            os.makedirs(os.path.dirname(path), self.permission)
        return secured_filename, path
