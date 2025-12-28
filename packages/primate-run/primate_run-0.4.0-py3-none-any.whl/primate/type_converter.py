from js import Array, Object  # type: ignore


def convert_from_js(value, helpers):
  js_type = str(helpers.type(value))

  if js_type == "integer":
    return int(value)
  elif js_type == "float":
    return float(value)
  elif js_type == "boolean":
    return bool(value)
  elif js_type == "string":
    return str(value)
  elif js_type == "nil":
    return None
  elif js_type == "array":
    as_array = Array.from_(value)
    return [
      convert_from_js(as_array[i], helpers) for i in range(as_array.length)
    ]
  elif js_type == "object":
    entries = Object.entries(value)
    result = {}
    for i in range(entries.length):
      key = str(entries[i][0])
      val = convert_from_js(entries[i][1], helpers)
      result[key] = val
    return result

  return value
