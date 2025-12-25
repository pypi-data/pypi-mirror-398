// Your bundler file
import esbuild from "esbuild";

await esbuild.build({
  entryPoints: ["js/server.mjs"],
  bundle: true,
  platform: "node",
  format: "cjs",
  outfile: "jupyter_retext_language_server/dist/server.cjs",
});

await esbuild.build({
  entryPoints: ["js/retext-spell.mjs"],
  bundle: true,
  platform: "node",
  format: "cjs",
  outfile: "jupyter_retext_language_server/dist/retext-spell.cjs",
});
