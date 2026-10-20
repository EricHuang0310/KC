// Validate a graph-schema JSON file the way Neo4j's own tooling reads it:
//   1. JSON Schema check against @neo4j/graph-json-schema
//   2. Parse with @neo4j/graph-schema-utils (resolves every $ref) and round-trip back to JSON
//
// Usage: npm install && npm run validate   (or: node validate.mjs <path-to-graph_model.json>)

import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { isDeepStrictEqual } from "node:util";
import { validateSchema, SchemaValidationError, formatters } from "@neo4j/graph-schema-utils";

const require = createRequire(import.meta.url);
const jsonSchemaPath = require.resolve("@neo4j/graph-json-schema/json-schema.json");

const modelPath = process.argv[2] ?? "../output/graph_model.json";
const modelText = readFileSync(modelPath, "utf8");

try {
  validateSchema(readFileSync(jsonSchemaPath, "utf8"), modelText);
} catch (err) {
  if (err instanceof SchemaValidationError) {
    console.error("JSON Schema validation failed:");
    for (const m of err.messages) console.error(`  ${m.instancePath} ${m.message}`);
    process.exit(1);
  }
  throw err;
}

const schema = formatters.json.fromJson(modelText);

// toJsonStruct sorts some arrays by $id, so compare with every array keyed by $id.
const byId = (value) =>
  Array.isArray(value)
    ? Object.fromEntries(value.map((v, i) => [v?.$id ?? i, byId(v)]))
    : value && typeof value === "object"
      ? Object.fromEntries(Object.entries(value).map(([k, v]) => [k, byId(v)]))
      : value;

const original = JSON.parse(modelText).graphSchemaRepresentation.graphSchema;
const roundTripped = formatters.json.toJsonStruct(schema).graphSchemaRepresentation.graphSchema;
if (!isDeepStrictEqual(byId(original), byId(roundTripped))) {
  console.error("Round-trip through @neo4j/graph-schema-utils changed the model (unsupported field or dangling $ref).");
  process.exit(1);
}

console.log(
  `OK: ${schema.nodeObjectTypes.length} node types, ` +
    `${schema.relationshipTypes.length} relationship types, ` +
    `${schema.relationshipObjectTypes.length} relationship patterns, ` +
    `${schema.constraints.length} constraints`,
);
