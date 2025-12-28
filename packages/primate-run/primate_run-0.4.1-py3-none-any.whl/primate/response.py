from typing import Any


class Response:
  @staticmethod
  def view(
    name: str,
    props: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
  ) -> dict[str, Any]:
    """
    Create a view response.

    Args:
        name: The view template name
        props: Props to pass to the view
        options: Additional view options

    Returns:
        Response object for the Primate framework
    """
    return {
      "__PRMT__": "view",
      "name": name,
      "props": props or {},
      "options": options or {},
    }

  @staticmethod
  def redirect(location: str, status: int | None = None) -> dict[str, Any]:
    """
    Create a redirect response.

    Args:
        location: URL to redirect to
        status: HTTP status code (optional)

    Returns:
        Response object for the Primate framework
    """
    options = {}
    if status is not None:
      options["status"] = status

    return {"__PRMT__": "redirect", "location": location, "options": options}

  @staticmethod
  def error(options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create an error response

    Args:
        options: dict with body, status, page keys (optional)
    """
    return {"__PRMT__": "error", "options": options or {}}
