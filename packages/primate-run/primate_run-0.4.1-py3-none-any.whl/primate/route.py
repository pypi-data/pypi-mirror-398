from __future__ import annotations

import inspect
from collections.abc import Callable

from .request import Request
from .response import Response
from .session import Session, SessionInstance


class Route:
  _scopes: dict[str, dict[str, Callable]] = {}
  _current_scope: str = "__default__"

  Request = Request

  @classmethod
  def scope(cls, name: str) -> None:
    """Select which bucket new decorators should write into."""
    cls._current_scope = name
    cls._scopes.setdefault(name, {})

  @classmethod
  def current_scope(cls) -> str:
    return cls._current_scope

  @classmethod
  def clear(cls, name: str | None = None) -> None:
    """Clear routes for a scope (used by dev hot reload)."""
    if name is None:
      cls._scopes.clear()
      cls._current_scope = "__default__"
      return

    cls._scopes.pop(name, None)
    if cls._current_scope == name:
      cls._current_scope = "__default__"

  @classmethod
  def _bucket(cls, name: str | None = None) -> dict[str, Callable]:
    key = name or cls._current_scope
    return cls._scopes.setdefault(key, {})

  @classmethod
  def get(cls, func: Callable) -> Callable:
    cls._bucket()["GET"] = func
    return func

  @classmethod
  def post(cls, func: Callable) -> Callable:
    cls._bucket()["POST"] = func
    return func

  @classmethod
  def put(cls, func: Callable) -> Callable:
    cls._bucket()["PUT"] = func
    return func

  @classmethod
  def patch(cls, func: Callable) -> Callable:
    cls._bucket()["PATCH"] = func
    return func

  @classmethod
  def delete(cls, func: Callable) -> Callable:
    cls._bucket()["DELETE"] = func
    return func

  @classmethod
  def head(cls, func: Callable) -> Callable:
    cls._bucket()["HEAD"] = func
    return func

  @classmethod
  def options(cls, func: Callable) -> Callable:
    cls._bucket()["OPTIONS"] = func
    return func

  @classmethod
  def connect(cls, func: Callable) -> Callable:
    cls._bucket()["CONNECT"] = func
    return func

  @classmethod
  def trace(cls, func: Callable) -> Callable:
    cls._bucket()["TRACE"] = func
    return func

  @classmethod
  def registry(cls, name: str | None = None) -> dict[str, Callable]:
    """Return the verbs for the given scope (or current scope)."""
    return cls._bucket(name).copy()

  @classmethod
  def set_session(cls, session_obj, helpers) -> None:
    session_instance = SessionInstance(session_obj, helpers)
    Session.set_current(session_instance)

  @classmethod
  def call_route(
    cls,
    method: str,
    request,
    scope: str | None = None,
  ):
    bucket = cls._bucket(scope)
    handler = bucket.get(method.upper())
    if handler is None:
      return Response.error({"status": 404})
    return handler(request)

  @classmethod
  async def call_js(
    cls,
    scope: str,
    method: str,
    js_request,
    helpers_obj,
    session_obj,
  ):
    cls.set_session(session_obj, helpers_obj)
    req = cls.Request(js_request, helpers_obj)
    result = cls.call_route(method, req, scope)
    if inspect.isawaitable(result):
      result = await result
    return result
