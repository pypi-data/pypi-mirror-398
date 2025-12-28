from .readable import Readable


class UploadedFile:
  """Represents an uploaded file"""

  def __init__(self, field, name, type, size, bytes_data):
    self.field = field
    self.filename = name
    self.content_type = type
    self.size = size
    self._io = Readable(bytes_data, type)

  @property
  def io(self):
    """Get the Readable IO object"""
    return self._io
