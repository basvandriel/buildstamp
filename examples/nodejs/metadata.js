import fs from "node:fs";
import path from "node:path";

export function loadBuildMetadata(metadataFile = "./buildstamp/_build.json") {
  const resolved = path.resolve(process.cwd(), metadataFile);
  const raw = fs.readFileSync(resolved, "utf8");
  const metadata = JSON.parse(raw);

  return {
    ...metadata,
    buildDate: new Date(metadata.build_date),
  };
}
