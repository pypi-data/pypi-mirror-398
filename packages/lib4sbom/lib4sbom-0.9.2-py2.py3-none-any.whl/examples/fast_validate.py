import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import fastjsonschema

# Use orjson for fast parsing if available
try:
    import orjson


    def load_json_bytes(b: bytes) -> Any:
        return orjson.loads(b)
except ImportError:

    def load_json_bytes(b: bytes) -> Any:
        return json.loads(b.decode('utf-8'))


def load_schema_with_local_refs(schema_file: str, local_dir: str) -> Dict[str, Any]:
    # Load a CycloneDX schema JSON file and rewrite all $refs to point to local schema files.
    schema_file = Path(schema_file)
    local_dir = Path(local_dir)

    with open(schema_file, "r") as f:
        schema = json.load(f)

    def rewrite_refs(obj):
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                # Skip external network refs
                ref_name = Path(ref).name
                local_ref = local_dir / ref_name
                if local_ref.exists():
                    print (f"{local_ref} resolved")
                    obj["$ref"] = str(local_ref.resolve())
            elif "$id" in obj:
                ref = obj["$id"]
                # Skip external network refs
                ref_name = Path(ref).name
                local_ref = local_dir / ref_name
                if local_ref.exists():
                    obj["$id"] = f"file://{str(local_ref.resolve())}"
                    print (f"{local_ref} resolved to {obj['$id']}")
                else:
                    print ("Unable to resolve {local_ref}")
            for v in obj.values():
                rewrite_refs(v)
        elif isinstance(obj, list):
            for i in obj:
                rewrite_refs(i)

    rewrite_refs(schema)
    return schema


def validate_sbom(
        sbom_path: str,
        schema_file: str,
        local_refs_dir: str,
) -> Tuple[bool, str]:
    # Load SBOM
    try:
        sbom_bytes = Path(sbom_path).read_bytes()
        sbom = load_json_bytes(sbom_bytes)
    except Exception as e:
        return False, f"Failed to read/parse SBOM JSON: {e}"

    # Load schema with local refs
    try:
        schema = load_schema_with_local_refs(schema_file, local_refs_dir)
    except Exception as e:
        return False, f"Failed to load schema: {e}"

    # Compile validator
    try:
        print ("\n\n.... STARTING")
        validate = fastjsonschema.compile(schema)
        print ("FINISHED")
    except Exception as e:
        return False, f"Failed to compile schema: {e}"

    # Validate SBOM
    try:
        validate(sbom)
    except fastjsonschema.JsonSchemaException as e:
        return False, f"Schema validation error: {e.message} @ {e.path}"

    # Optional quick header check
    if sbom.get("bomFormat") != "CycloneDX":
        return True, "VALID but warning: bomFormat != 'CycloneDX'"
    if sbom.get("specVersion") != "1.6":
        return True, "VALID but warning: specVersion != '1.6'"
    return True, "VALID: SBOM conforms to CycloneDX 1.6 schema."


def main(argv: Iterable[str] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline CycloneDX 1.6 SBOM JSON validator"
    )

    parser.add_argument("sbom", help="Path to SBOM JSON file")
    parser.add_argument(
        "--schema", required=True, help="Path to local CycloneDX 1.6 schema"
    )
    parser.add_argument(
        "--refs-dir", required=True, help="Directory containing local referenced schemas (spdx, jsf, etc.)"
    )
    args = parser.parse_args(argv)

    valid, msg = validate_sbom(args.sbom, args.schema, args.refs_dir)
    print(msg)
    return 0 if valid else 1

if __name__ == "__main__":
    sys.exit(main())
