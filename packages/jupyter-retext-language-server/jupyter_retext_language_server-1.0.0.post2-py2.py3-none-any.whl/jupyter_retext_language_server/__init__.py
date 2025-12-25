from .config import ConfigServer

from jupyter_lsp import lsp_message_listener


async def debug_lsp_message(scope, message, language_server, manager):
    if language_server != "retext-language-server":
        return

    if scope == "server" and message.get("method") == "window/logMessage":
        session = manager.sessions[language_server]
        session.log.warning(message["params"]["message"])


def _load_jupyter_server_extension(app):
    register = lsp_message_listener("all")

    config_server = ConfigServer.instance(parent=app)
    config_server.start()

    register(config_server.handle_lsp_message)
    register(debug_lsp_message)


def _jupyter_server_extension_points():
    """
    Returns a list of dictionaries with metadata describing
    where to find the `_load_jupyter_server_extension` function.
    """
    return [{"module": "jupyter_retext_language_server"}]
