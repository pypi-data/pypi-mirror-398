from .request_bag import RequestBag
from .request_body import RequestBody
from .url import URL


class Request:
  def __init__(self, request_obj, helpers):
    self.url = URL(request_obj.url)
    self.body = RequestBody(request_obj.body, helpers)
    self.path = RequestBag(request_obj.path, helpers)
    self.query = RequestBag(request_obj.query, helpers)
    self.headers = RequestBag(request_obj.headers, helpers)
    self.cookies = RequestBag(request_obj.cookies, helpers)
