from .type_converter import convert_from_js


class RequestBag:
  def __init__(self, data, helpers):
    self.data = convert_from_js(data, helpers)

  def get(self, key):
    if not isinstance(self.data, dict) or not self.has(key):
      raise KeyError(f"RequestBag has no key {key}")
    return str(self.data[key])

  def __getitem__(self, key):
    return self.get(key)

  def try_get(self, key):
    return (
      str(self.data[key])
      if isinstance(self.data, dict) and self.has(key)
      else None
    )

  def has(self, key):
    return (
      isinstance(self.data, dict)
      and key in self.data
      and self.data[key] is not None
    )

  def parse(self, schema, coerce=False):
    return schema.parse(self.data, coerce)

  def to_dict(self):
    if isinstance(self.data, dict):
      return self.data.copy()
    else:
      return {}

  def __len__(self):
    if isinstance(self.data, (dict, list, str)):
      return len(self.data)
    else:
      return 0
