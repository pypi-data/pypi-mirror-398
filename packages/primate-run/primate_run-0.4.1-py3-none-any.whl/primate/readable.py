class Readable:
  def __init__(self, typed_array, content_type=None):
    self.typed_array = typed_array
    self.content_type = content_type
    self.pos = 0
    self.size = (
      len(typed_array)
      if hasattr(typed_array, "__len__")
      else typed_array.length
    )

  @property
  def size(self):
    return self._size

  @size.setter
  def size(self, value):
    self._size = int(value)

  def eof(self):
    return self.pos >= self.size

  def rewind(self):
    self.pos = 0
    return self

  def read(self, n=None):
    if self.eof():
      return b""

    if n is None:
      n = self.size - self.pos
    else:
      n = min(n, self.size - self.pos)

    data_array = self.typed_array.subarray(self.pos, self.pos + n)
    data = bytes([data_array[i] for i in range(data_array.length)])
    self.pos += n
    return data

  def bytes(self, n=None):
    if self.eof():
      return []

    if n is None:
      n = self.size - self.pos
    else:
      n = min(n, self.size - self.pos)

    data_array = self.typed_array.subarray(self.pos, self.pos + n)
    data = [data_array[i] for i in range(data_array.length)]
    self.pos += n
    return data

  def peek(self, n):
    n = min(n, self.size - self.pos)
    data_array = self.typed_array.subarray(self.pos, self.pos + n)
    return [data_array[i] for i in range(data_array.length)]

  def head(self, n=4):
    n = min(n, self.size)
    data_array = self.typed_array.subarray(0, n)
    return [data_array[i] for i in range(data_array.length)]

  def each_chunk(self, chunk_size=64 * 1024):
    offset = self.pos
    while offset < self.size:
      n = min(chunk_size, self.size - offset)
      data_array = self.typed_array.subarray(offset, offset + n)
      yield bytes([data_array[i] for i in range(data_array.length)])
      offset += n
