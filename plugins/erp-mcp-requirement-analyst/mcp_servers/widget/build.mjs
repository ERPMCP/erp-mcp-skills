import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const result = await build({
  absWorkingDir: root,
  entryPoints: ["./src/main.js"],
  bundle: true,
  format: "iife",
  platform: "browser",
  target: ["es2022"],
  minify: true,
  preserveSymlinks: true,
  write: false,
});

const [template, css] = await Promise.all([
  readFile(resolve(root, "src/index.html"), "utf8"),
  readFile(resolve(root, "src/styles.css"), "utf8"),
]);
const js = result.outputFiles[0].text.replaceAll("</script", "<\\/script");
// Replace both markers in one pass over the untouched template. A second
// replace can accidentally match marker-like text inside the bundled SDK.
const html = template.replace(
  /\/\*__(APP_CSS|APP_JS)__\*\//g,
  (_, kind) => (kind === "APP_CSS" ? css : js),
);
await mkdir(resolve(root, "dist"), { recursive: true });
await writeFile(resolve(root, "dist/index.html"), html, "utf8");
console.log("dist/index.html");
