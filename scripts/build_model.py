"""Build one model: models/<slug>/build.py -> public/models/<slug>/{fbx,glb,thumb.png,meta.json}

Run through scripts/build.sh (it picks pip `bpy` or a Blender install):
    bash scripts/build.sh <slug> [--check]

--check also renders front/side/back/top views into .check/<slug>/ (git-ignored)
so you can look at the result from several angles before committing.
"""

import datetime
import json
import os
import runpy
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, "scripts", "lib"), os.path.join(ROOT, "scripts")]

import lowpoly  # noqa: E402
from update_manifest import update_manifest  # noqa: E402

CHECK_VIEWS = [(0, 10), (90, 10), (180, 10), (0, 89), (35, 25), (215, 30)]


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    flags = {a for a in args if a.startswith("--")}
    slugs = [a for a in args if not a.startswith("--")]
    if len(slugs) != 1:
        sys.exit("usage: build.sh <slug> [--check]")
    slug = slugs[0]

    src = os.path.join(ROOT, "models", slug, "build.py")
    if not os.path.exists(src):
        sys.exit(f"missing {src}")
    out_dir = os.path.join(ROOT, "public", "models", slug)

    lowpoly.reset_scene()
    ns = runpy.run_path(src, run_name="model")
    if "build" not in ns:
        sys.exit(f"{src} must define build()")
    ns["build"]()

    stats = lowpoly.finalize(slug, smooth=ns.get("SMOOTH", False))
    lowpoly.export(slug, out_dir)
    lowpoly.render_views(slug, os.path.join(out_dir, "thumb.png"))
    if "--check" in flags:
        check_dir = os.path.join(ROOT, ".check", slug)
        os.makedirs(check_dir, exist_ok=True)
        lowpoly.render_views(slug, os.path.join(check_dir, "view.png"), CHECK_VIEWS, size=384)

    meta_path = os.path.join(out_dir, "meta.json")
    created = None
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            created = json.load(f).get("created")
    today = datetime.date.today().isoformat()
    meta = {
        "slug": slug,
        "name": ns.get("NAME", slug.replace("-", " ").title()),
        "category": ns.get("CATEGORY", "prop"),
        "description": ns.get("DESCRIPTION", ""),
        "created": created or today,
        "updated": today,
        **stats,
        "files": {"fbx": f"{slug}.fbx", "glb": f"{slug}.glb", "thumb": "thumb.png"},
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")

    update_manifest()
    print(f"\nBUILT {slug}: {stats['tris']} tris, {stats['verts']} verts, "
          f"size {stats['size_m']} m")
    for m in stats["materials"]:
        print(f"  material {m['name']:<16} {m['color']}  {m['tris']} tris")
    print(f"  -> public/models/{slug}/")
    if "--check" in flags:
        print(f"  -> check renders in .check/{slug}/ (front, right, back, top, 3/4, 3/4 rear)")


if __name__ in ("__main__", "<run_path>"):
    main()
