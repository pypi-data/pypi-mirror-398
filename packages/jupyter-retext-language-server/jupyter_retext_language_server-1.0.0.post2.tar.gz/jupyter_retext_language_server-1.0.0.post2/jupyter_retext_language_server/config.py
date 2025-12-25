from traitlets.config import SingletonConfigurable
from traitlets import Instance

import json
import pathlib
import tempfile


class ConfigServer(SingletonConfigurable):
    path = Instance(pathlib.Path, allow_none=True)

    async def handle_lsp_message(self, scope, message, language_server, manager):
        if language_server != "retext-language-server":
            return

        if scope == "server" and message.get("method") == "window/logMessage":
            session = manager.sessions[language_server]
            session.log.warning(message["params"]["message"])
        elif (
            scope == "client"
            and message.get("method") == "workspace/didChangeConfiguration"
        ):
            settings = message.get("params", {}).get("settings", {}).get("retext", {})
            self.sync_config(settings)

    def start(self):
        self.path = pathlib.Path(
            tempfile.mktemp(suffix=".json", prefix="retext-language-server")
        )

    def sync_config(self, config):
        self.log.debug(f"Pushing config to LSP process {config}")
        with open(self.path, "w") as f:
            json.dump(config, f)
