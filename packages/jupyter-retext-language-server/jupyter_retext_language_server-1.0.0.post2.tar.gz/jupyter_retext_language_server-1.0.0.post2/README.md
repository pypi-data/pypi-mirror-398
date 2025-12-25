# jupyter-retext-language-server

A [retext] language server for [Jupyter LSP]. This builds upon the [unified-language-server] by exposing a simple configuration mechanism.

## Plugins

By default, the jupyter-retext-language-server ships with pre-installed with the `retext-spell` plugin out of the box.

## Extending

New retext plugins can be defined through Python entry points, e.g.

```toml
[project.entry-points.jupyter_retext_language_server_plugin_v1]
retext-spell = "jupyter_retext_language_server.plugins:retext_spell"
```

The `retext_spell` name in the `jupyter_retext_language_server.plugins` module has the following form:

### Entry points

```python
retext_spell = {
    "path": /path/to/retext-spell.mjs",
    "properties_schema": {
        "retext.plugins.retext-spell.enabled": {
            "type": "boolean",
            "default": True,
            "description": "Enable retext-spell plugin.",
        },
        // ... etc
    }
}

```

It is through this entry point that the settings schema and path to the ESM module can be defined.

### ESM plugin

The ESM plugin exposed by the Python entry point must define two named exports, e.g.

```javascript
export const name = "retext-spell";

export async function plugin(spellConfig) {
  // Plugin impl
  return (tree, file, next) => {};
}
```

These define the name (which maps to the plugin name in the properties schema), and the plugin implementation that is invoked by the plugin manager.

## Future development ideas

- Generalise the project to allow multiple ecosystems (unified, retext, etc).
- Add proper schema merging.
- Validate plugin subschemas
- Validate plugin ESM modules
- Implement upstream fixes to expose the config — https://github.com/unifiedjs/unified-language-server/issues/69

[unified-language-server]: https://github.com/unifiedjs/unified-language-server
[retext]: https://github.com/retextjs/retext
[retext-spell]: https://github.com/retextjs/retext-spell
[jupyter lsp]: https://github.com/jupyter-lsp/jupyterlab-lsp
