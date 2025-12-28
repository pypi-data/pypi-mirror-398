from .readable import Readable
from .type_converter import convert_from_js
from .uploaded_file import UploadedFile


class RequestBody:
  def __init__(self, body, helpers):
    self.body = body
    self.helpers = helpers

  def json(self):
    return convert_from_js(self.body.json(), self.helpers)

  def text(self):
    return self.body.text()

  def form(self):
    return convert_from_js(self.body.form(), self.helpers)

  def files(self):
    files_array = self.body.files()
    files = []

    for i in range(files_array.length):
      f = files_array[i]
      uploaded_file = UploadedFile(
        field=str(f.field),
        name=str(f.name),
        type=str(f.type),
        size=int(f.size),
        bytes_data=f.bytes,
      )
      files.append(uploaded_file)

    return files

  def binary(self):
    binary = self.body.binary()
    return Readable(binary.buffer, str(binary.mime))
