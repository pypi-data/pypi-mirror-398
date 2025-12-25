from jupyter_lsp.types import SpecBase
from jupyter_lsp.schema import SPEC_VERSION

import importlib.metadata
import importlib.resources
import json
import os

from .config import ConfigServer
from .utils import get_shared_data_path
from . import schemas


def load_plugins():
    entry_points = importlib.metadata.entry_points()
    plugins = entry_points.select(group="jupyter_retext_language_server_plugin_v1")
    return [p.load() for p in plugins]


class RetextLanguageServer(SpecBase):
    key = "retext-language-server"
    args = ["--stdio"]
    languages = ["markdown", "ipythongfm", "gfm"]
    spec = dict(
        version=SPEC_VERSION,
        display_name=key,
        mime_types=["text/x-gfm", "text/x-ipythongfm", "text/x-markdown"],
    )

    def __call__(self, mgr):
        spec = dict(self.spec)

        plugins = load_plugins()
        plugin_js_paths = ":".join(p["path"] for p in plugins)
        plugin_schema = json.loads(
            (importlib.resources.files(schemas) / "config.schema.json").read_text()
        )
        for plugin in plugins:
            plugin_schema["properties"].update(plugin["properties_schema"])

        assert ConfigServer.initialized()
        config_server = ConfigServer.instance()

        return {
            self.key: {
                "argv": [
                    mgr.nodejs,
                    os.fspath(
                        get_shared_data_path()
                        / "jupyter-retext-language-server"
                        / "bin"
                        / "server.cjs"
                    ),
                    *self.args,
                ],
                "languages": self.languages,
                "version": SPEC_VERSION,
                "config_schema": plugin_schema,
                "env": {
                    "RETEXT_CONFIG_PATH": os.fspath(config_server.path),
                    "RETEXT_PLUGIN_PATHS": plugin_js_paths,
                },
                **spec,
            }
        }


retext = RetextLanguageServer()
