"""Rebuild public/models.json from every public/models/*/meta.json (newest first)."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def update_manifest():
    models_dir = os.path.join(ROOT, "public", "models")
    entries = []
    if os.path.isdir(models_dir):
        for slug in sorted(os.listdir(models_dir)):
            meta = os.path.join(models_dir, slug, "meta.json")
            if os.path.exists(meta):
                with open(meta) as f:
                    entries.append(json.load(f))
    entries.sort(key=lambda m: (m.get("updated", ""), m["slug"]), reverse=True)
    with open(os.path.join(ROOT, "public", "models.json"), "w") as f:
        json.dump({"models": entries}, f, indent=2)
        f.write("\n")
    return entries


if __name__ == "__main__":
    print(f"{len(update_manifest())} models in public/models.json")
