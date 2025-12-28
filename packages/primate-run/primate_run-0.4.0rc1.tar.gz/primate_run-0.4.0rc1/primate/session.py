class SessionInstance:
  def __init__(self, session, helpers):
    self.session = session
    self.helpers = helpers

  @property
  def id(self):
    return self.session.id

  @property
  def exists(self):
    return bool(self.session.exists)

  def create(self, data):
    self.session.create(data)

  def get(self):
    return self.session.get()

  def try_get(self):
    try:
      return self.session.try_get() or {}
    except AttributeError:
      return {}

  def set(self, data):
    self.session.set(data)

  def destroy(self):
    self.session.destroy()


class Session:
  """Session management singleton"""

  _current = None

  @classmethod
  def set_current(cls, session_instance):
    """Set current session instance (called by framework)"""
    cls._current = session_instance

  @classmethod
  def id(cls):
    """Get session ID"""
    return cls._current.id if cls._current else None

  @classmethod
  def exists(cls):
    """Check if session exists"""
    return cls._current.exists if cls._current else False

  @classmethod
  def create(cls, data):
    """Create new session with data"""
    if cls._current:
      cls._current.create(data)

  @classmethod
  def get(cls):
    """Get session data"""
    return cls._current.get() if cls._current else {}

  @classmethod
  def try_get(cls):
    """Try to get session data"""
    return cls._current.try_get() if cls._current else {}

  @classmethod
  def set(cls, data):
    """Set session data"""
    if cls._current:
      cls._current.set(data)

  @classmethod
  def destroy(cls):
    """Destroy session"""
    if cls._current:
      cls._current.destroy()
