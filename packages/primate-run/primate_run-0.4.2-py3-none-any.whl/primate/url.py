class URL:
  def __init__(self, url_obj):
    self.href = str(url_obj.href)
    self.origin = str(url_obj.origin)
    self.protocol = str(url_obj.protocol)
    self.username = str(getattr(url_obj, "username", ""))
    self.password = str(getattr(url_obj, "password", ""))
    self.host = str(getattr(url_obj, "host", ""))
    self.hostname = str(url_obj.hostname)
    self.port = str(url_obj.port)
    self.pathname = str(url_obj.pathname)
    self.search = str(url_obj.search)
    self.hash = str(url_obj.hash)
