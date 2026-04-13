# Node.js example for buildstamp metadata

This example shows how a Node.js API can consume the `_build.json` metadata file produced by buildstamp.

## Generate metadata

Use the `buildstamp` CLI to write the metadata file before your Node.js build/run step:

```sh
buildstamp write --root . --version-file VERSION --metadata-file your_package/_build.json
```

If you want to use a package-local output path, update the path accordingly.

## Load metadata in Node.js

```js
import { loadBuildMetadata } from "./metadata.js";

const meta = loadBuildMetadata("your_package/_build.json");
console.log(meta.version);
console.log(meta.quality);
console.log(meta.commit);
console.log(meta.buildDate.toISOString());
```

## Example API

```js
import express from "express";
import { loadBuildMetadata } from "./metadata.js";

const app = express();

app.get("/api/build-info", (req, res) => {
  res.json(loadBuildMetadata("your_package/_build.json"));
});

app.listen(3000, () => {
  console.log("listening on http://localhost:3000");
});
```

## Notes

- `buildstamp` is language-agnostic in this mode: it just writes JSON.
- Your Node.js project can read that JSON file directly, no Python runtime required.
- Keep `your_package/_build.json` in `.gitignore` if it is a generated artifact.
