#!/usr/bin/env python3
"""Generate Neo4j Document Intelligence model artifacts from ontology.yaml.

Outputs (in kg_model/output/):
  graph_model.json    Neo4j graph-schema JSON (graphSchemaRepresentation) with descriptions
  di_agent_prompt.md  Natural-language model description for the Document Intelligence agent
  model_diagram.md    Mermaid diagram of labels and relationship patterns

Usage:
  python3 kg_model/build_model.py           # regenerate outputs
  python3 kg_model/build_model.py --check   # fail if outputs are stale (for CI)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ONTOLOGY = HERE / "ontology.yaml"
OUTPUT_DIR = HERE / "output"

# graph-schema-json format version emitted by @neo4j/graph-schema-utils
SCHEMA_FORMAT_VERSION = "0.0.1"

PRIMITIVE_TYPES = {"string", "integer", "float", "boolean", "date", "datetime"}
PROPERTY_KEYS = {"name", "type", "nullable", "description"}
RESERVED_LABELS = {"Document", "Chunk", "Entity"}  # created by Document Intelligence's lexical layer
LABEL_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
REL_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
PROP_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def load_ontology(path: Path = ONTOLOGY) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_ontology(onto: dict) -> list[str]:
    """Return a list of human-readable problems; empty means the ontology is consistent."""
    errors: list[str] = []
    labels = [n["label"] for n in onto["nodes"]]
    rel_types = [r["type"] for r in onto["relationships"]]

    for dup in {x for x in labels if labels.count(x) > 1}:
        errors.append(f"duplicate node label: {dup}")
    for dup in {x for x in rel_types if rel_types.count(x) > 1}:
        errors.append(f"duplicate relationship type: {dup}")

    def check_props(owner: str, props: list[dict]) -> None:
        names = [p["name"] for p in props]
        for dup in {x for x in names if names.count(x) > 1}:
            errors.append(f"{owner}: duplicate property {dup}")
        for p in props:
            # An unquoted ASCII comma inside a YAML flow mapping silently splits the description into extra keys.
            if unknown := set(p) - PROPERTY_KEYS:
                errors.append(f"{owner}.{p['name']}: unknown keys {sorted(map(str, unknown))} (quote the description)")
            if not PROP_RE.match(p["name"]):
                errors.append(f"{owner}.{p['name']}: property must be snake_case")
            base = p["type"][:-2] if p["type"].endswith("[]") else p["type"]
            if base not in PRIMITIVE_TYPES:
                errors.append(f"{owner}.{p['name']}: unsupported type {p['type']}")
            if not p.get("description"):
                errors.append(f"{owner}.{p['name']}: missing description")

    for node in onto["nodes"]:
        label = node["label"]
        if not LABEL_RE.match(label):
            errors.append(f"{label}: label must be PascalCase")
        if label in RESERVED_LABELS:
            errors.append(f"{label}: reserved by Document Intelligence lexical layer")
        if not node.get("description"):
            errors.append(f"{label}: missing description")
        props = node.get("properties", [])
        check_props(label, props)
        key = next((p for p in props if p["name"] == node.get("key")), None)
        if key is None:
            errors.append(f"{label}: key '{node.get('key')}' is not one of its properties")
        elif key.get("nullable", False):
            errors.append(f"{label}: key '{key['name']}' must not be nullable")

    used_labels: set[str] = set()
    for rel in onto["relationships"]:
        rtype = rel["type"]
        if not REL_TYPE_RE.match(rtype):
            errors.append(f"{rtype}: relationship type must be UPPER_SNAKE_CASE")
        if not rel.get("description"):
            errors.append(f"{rtype}: missing description")
        check_props(rtype, rel.get("properties", []))
        if not rel.get("patterns"):
            errors.append(f"{rtype}: needs at least one pattern")
        seen = set()
        for src, dst in rel.get("patterns", []):
            for end in (src, dst):
                if end not in labels:
                    errors.append(f"{rtype}: pattern references undefined label {end}")
                used_labels.add(end)
            if (src, dst) in seen:
                errors.append(f"{rtype}: duplicate pattern ({src})->({dst})")
            seen.add((src, dst))

    for label in labels:
        if label not in used_labels:
            errors.append(f"{label}: not connected by any relationship pattern")
    return errors


def property_type(type_name: str) -> dict:
    if type_name.endswith("[]"):
        return {"type": "array", "items": {"type": type_name[:-2]}}
    return {"type": type_name}


def build_graph_schema(onto: dict) -> dict:
    """Build a graph-schema JSON document (the format used by Neo4j Aura import tooling)."""
    prop_seq = 0

    def make_props(props: list[dict]) -> tuple[list[dict], dict[str, str]]:
        nonlocal prop_seq
        out, ids = [], {}
        for p in props:
            pid = f"p:{prop_seq}"
            prop_seq += 1
            ids[p["name"]] = pid
            out.append(
                {
                    "$id": pid,
                    "token": p["name"],
                    "type": property_type(p["type"]),
                    "nullable": bool(p.get("nullable", False)),
                    "description": p["description"],
                }
            )
        return out, ids

    node_labels, node_object_types, constraints, indexes = [], [], [], []
    node_ref: dict[str, str] = {}
    for i, node in enumerate(onto["nodes"]):
        props, prop_ids = make_props(node["properties"])
        node_labels.append({"$id": f"nl:{i}", "token": node["label"], "properties": props})
        node_object_types.append(
            {"$id": f"n:{i}", "labels": [{"$ref": f"#nl:{i}"}], "description": node["description"]}
        )
        node_ref[node["label"]] = f"#n:{i}"

        name = f"{node['label']}_{node['key']}_uniq"
        key_ref = [{"$ref": f"#{prop_ids[node['key']]}"}]
        constraints.append(
            {
                "$id": f"c:{i}",
                "name": name,
                "constraintType": "uniqueness",
                "entityType": "node",
                "nodeLabel": {"$ref": f"#nl:{i}"},
                "properties": key_ref,
            }
        )
        indexes.append(
            {
                "$id": f"i:{i}",
                "name": name,
                "indexType": "default",
                "entityType": "node",
                "nodeLabel": {"$ref": f"#nl:{i}"},
                "properties": key_ref,
            }
        )

    relationship_types, relationship_object_types = [], []
    r_seq = 0
    for i, rel in enumerate(onto["relationships"]):
        props, _ = make_props(rel.get("properties", []))
        relationship_types.append({"$id": f"rt:{i}", "token": rel["type"], "properties": props})
        for src, dst in rel["patterns"]:
            relationship_object_types.append(
                {
                    "$id": f"r:{r_seq}",
                    "type": {"$ref": f"#rt:{i}"},
                    "from": {"$ref": node_ref[src]},
                    "to": {"$ref": node_ref[dst]},
                    "description": rel["description"],
                }
            )
            r_seq += 1

    return {
        "graphSchemaRepresentation": {
            "version": SCHEMA_FORMAT_VERSION,
            "graphSchema": {
                "nodeLabels": node_labels,
                "relationshipTypes": relationship_types,
                "nodeObjectTypes": node_object_types,
                "relationshipObjectTypes": relationship_object_types,
                "constraints": constraints,
                "indexes": indexes,
            },
        }
    }


def build_agent_prompt(onto: dict) -> str:
    """Render the model as instructions for the Document Intelligence agent."""
    lines = [
        f"# {onto['name']} — Graph Model 說明（v{onto['version']}）",
        "",
        "請依照以下 graph model 從文件中抽取實體與關係。只建立下列 node label 與 relationship type，"
        "不要新增其他類型；Document / Chunk 等 lexical layer 由系統自動建立。",
        "",
        "## 抽取規則",
        "",
    ]
    lines += [f"- {rule}" for rule in onto["extraction_rules"]]
    lines += ["", "## Node labels", ""]
    for node in onto["nodes"]:
        lines.append(f"### {node['label']}（key: `{node['key']}`）")
        lines.append("")
        lines.append(node["description"])
        lines.append("")
        for p in node["properties"]:
            flags = "必填" if not p.get("nullable", False) else "選填"
            lines.append(f"- `{p['name']}` ({p['type']}, {flags})：{p['description']}")
        lines.append("")
    lines += ["## Relationship types", ""]
    for rel in onto["relationships"]:
        patterns = "、".join(f"`(:{s})-[:{rel['type']}]->(:{d})`" for s, d in rel["patterns"])
        lines.append(f"- **{rel['type']}**：{rel['description']} 模式：{patterns}")
        for p in rel.get("properties", []):
            lines.append(f"  - 關係屬性 `{p['name']}` ({p['type']})：{p['description']}")
    lines.append("")
    return "\n".join(lines)


def build_mermaid(onto: dict) -> str:
    """Render the model as a Mermaid flowchart (GitHub renders it inline)."""
    lines = [f"# {onto['name']} — Model Diagram", "", "```mermaid", "flowchart LR"]
    for node in onto["nodes"]:
        lines.append(f"    {node['label']}[\"{node['label']}<br/>key: {node['key']}\"]")
    for rel in onto["relationships"]:
        for src, dst in rel["patterns"]:
            lines.append(f"    {src} -->|{rel['type']}| {dst}")
    lines += ["```", ""]
    return "\n".join(lines)


def render_outputs(onto: dict) -> dict[Path, str]:
    graph_json = json.dumps(build_graph_schema(onto), ensure_ascii=False, indent=2) + "\n"
    return {
        OUTPUT_DIR / "graph_model.json": graph_json,
        OUTPUT_DIR / "di_agent_prompt.md": build_agent_prompt(onto),
        OUTPUT_DIR / "model_diagram.md": build_mermaid(onto),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="exit 1 if generated files are out of date")
    args = parser.parse_args(argv)

    onto = load_ontology()
    errors = validate_ontology(onto)
    if errors:
        print("ontology.yaml has problems:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    outputs = render_outputs(onto)
    if args.check:
        stale = [p for p, text in outputs.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
        for p in stale:
            print(f"stale: {p.relative_to(HERE)} (run build_model.py)", file=sys.stderr)
        return 1 if stale else 0

    OUTPUT_DIR.mkdir(exist_ok=True)
    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(HERE)}")
    n_rel_patterns = sum(len(r["patterns"]) for r in onto["relationships"])
    print(
        f"{len(onto['nodes'])} node labels, {len(onto['relationships'])} relationship types, "
        f"{n_rel_patterns} relationship patterns"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
