import builtins


class ValidationError(Exception):
  pass


class Field:
  def parse(self, _value, _coerce=False):
    raise NotImplementedError("Subclasses must implement parse")


class StringType(Field):
  def parse(self, value, coerce=False):
    if isinstance(value, builtins.str):
      return value

    if coerce:
      return builtins.str(value)

    raise ValidationError(f"expected string, got {type(value).__name__}")


class BooleanType(Field):
  def parse(self, value, coerce=False):
    if isinstance(value, builtins.bool):
      return value

    if coerce:
      if isinstance(value, builtins.str):
        if not value:  # empty string
          return False
        value_lower = value.lower()
        if value_lower in ("true", "1", "yes", "on"):
          return True
        elif value_lower in ("false", "0", "no", "off"):
          return False
        else:
          raise ValidationError(f"cannot parse '{value}' as boolean")
      else:
        raise ValidationError(
          f"cannot coerce {type(value).__name__} to boolean"
        )

    raise ValidationError(f"expected boolean, got {type(value).__name__}")


class IntType(Field):
  def parse(self, value, coerce=False):
    if isinstance(value, builtins.int) and not isinstance(value, builtins.bool):
      return value

    if coerce:
      if isinstance(value, builtins.float):
        return builtins.int(value)
      elif isinstance(value, builtins.str):
        if not value:  # empty string
          return 0
        try:
          return builtins.int(value)
        except ValueError:
          raise ValidationError(f"cannot parse '{value}' as integer") from None

    raise ValidationError(f"expected integer, got {type(value).__name__}")


class FloatType(Field):
  def parse(self, value, coerce=False):
    if isinstance(value, builtins.float):
      return value

    if coerce:
      if isinstance(value, (builtins.int, builtins.bool)):
        return builtins.float(value)
      elif isinstance(value, builtins.str):
        if not value:  # empty string
          return 0.0
        try:
          return builtins.float(value)
        except ValueError:
          raise ValidationError(f"cannot parse '{value}' as float") from None
      else:
        raise ValidationError(f"cannot coerce {type(value).__name__} to float")

    raise ValidationError(f"expected float, got {type(value).__name__}")


class Schema:
  def __init__(self, fields):
    self.fields = fields

  def parse(self, data, coerce=False):
    result = {}

    for name, field in self.fields.items():
      value = data.get(name, "")

      try:
        result[name] = field.parse(value, coerce)
      except ValidationError as e:
        raise ValidationError(
          f"parsing failed for field '{name}': {e}"
        ) from None

    return result


# Module-level functions (matching Ruby API)
def string():
  return StringType()


def boolean():
  return BooleanType()


def int():
  return IntType()


def float():
  return FloatType()


def schema(fields):
  return Schema(fields)


class PemaModule:
  ValidationError = ValidationError

  @staticmethod
  def string():
    return StringType()

  @staticmethod
  def boolean():
    return BooleanType()

  @staticmethod
  def int():
    return IntType()

  @staticmethod
  def float():
    return FloatType()

  @staticmethod
  def schema(fields):
    return Schema(fields)


pema = PemaModule()
