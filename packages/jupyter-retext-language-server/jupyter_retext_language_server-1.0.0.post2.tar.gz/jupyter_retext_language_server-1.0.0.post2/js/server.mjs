import { retext } from "retext";
import fsPromises from "node:fs/promises";
import { createUnifiedLanguageServer } from "unified-language-server";

process.title = "retext-spell-language-server";

class PluginManager {
  constructor(path) {
    this.pluginFactories = new Map();
    this.configuredPlugins = new Map();

    this.configPath = path;
    this.configMtime = undefined;
    this.config = undefined;
  }

  addPlugin(name, impl) {
    this.pluginFactories.set(name, impl);
  }

  async rebuildPlugins() {
    const config = this.config;
    const pluginConfigs = config.plugins ?? {};

    for (const [name, factory] of this.pluginFactories) {
      const config = pluginConfigs[name];
      const impl = config?.enabled ? await factory(config) : undefined;
      this.configuredPlugins.set(name, impl);
    }
  }

  async run(tree, file, next) {
    // Check config before run through
    const stat = await fsPromises.stat(this.configPath);
    if (stat.mtimeMs !== this.mtime) {
      const content = await fsPromises.readFile(this.configPath, {
        encoding: "utf-8",
      });
      this.config = JSON.parse(content);
      this.mtime = stat.mtimeMs;

      // Apply the changes
      await this.rebuildPlugins();
    }

    for (const [name, impl] of this.configuredPlugins) {
      if (impl === undefined) {
        continue;
      }
      try {
        await impl(tree, file, next);
      } catch (error) {
        file.fail(`${name} failed with ${error}`);
      }
    }
    console.error("Processed retext plugins");
  }
}

const pluginManager = new PluginManager(process.env.RETEXT_CONFIG_PATH);

const mainPlugin = () => {
  return async (tree, file, next) => await pluginManager.run(tree, file, next);
};

const pluginPaths = process.env.RETEXT_PLUGIN_PATHS.split(":");
async function main() {
  await Promise.all(
    pluginPaths.map(async (path) => {
      const { name, plugin } = await import(path);
      pluginManager.addPlugin(name, plugin);
    }),
  );

  createUnifiedLanguageServer({
    ignoreName: ".retextignore",
    pluginPrefix: "retext",
    processorName: "retext",
    processorSpecifier: "retext",
    defaultProcessor: retext,
    plugins: [[mainPlugin, {}]],
  });
}
main();
