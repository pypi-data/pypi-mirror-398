import json


class LocaleAccessor:
  _i18n = None

  @classmethod
  def _set_i18n(cls, i18n):
    cls._i18n = i18n

  @classmethod
  def get(cls):
    if cls._i18n is None:
      return None
    return cls._i18n.locale

  @classmethod
  def set(cls, value):
    if cls._i18n is not None:
      cls._i18n.set(value)


class I18N:
  _current = None
  locale = LocaleAccessor

  @classmethod
  def set_current(cls, i18n_obj):
    cls._current = i18n_obj
    LocaleAccessor._set_i18n(i18n_obj)

  @classmethod
  def t(cls, key, params=None):
    if cls._current is None:
      return key
    if params is None:
      return cls._current.t(key)
    return cls._current.t(key, json.dumps(params))
