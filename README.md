# 3d-claude: low-poly asset factory

Send Claude Code a photo from your phone and get back a low-poly, Unity-ready 3D model
that you can view, inspect per material, and download from a website.

```
phone (Claude app) ──photo──▶ Claude Code cloud session on this repo
                               │ writes models/<slug>/build.py, runs Blender headless,
                               │ checks renders against the photo, pushes a branch + PR
                               ▼
                         Vercel preview URL ──▶ view / tap materials / download FBX or GLB
                               │ merge PR
                               ▼
                         main site ──▶ "Copy prompt" ──▶ Claude session on the game repo adds it
```

## One-time setup

1. **Vercel:** Add New → Project → import `javaleer/3d-claude`. Leave the framework as "Other";
   `vercel.json` already sets the output to `public/`. Deploy.
2. **Claude Code cloud** (claude.ai/code, or Code in the mobile app): connect GitHub, then select
   this repo. Edit its **environment**:
   - Setup script: `bash scripts/setup.sh` (installs Blender as the `bpy` Python module)
   - Network access: **Trusted** (allows pip and GitHub)
3. **Game repo:** copy the section in `docs/unity-game-CLAUDE.md` into your Unity repo's `CLAUDE.md`.

## Daily use

- Phone → Claude app → Code → repo `3d-claude` → attach a photo → "make this, call it `oak-tree`".
- Claude opens a PR and a GitHub Action merges it automatically, so the model appears on
  https://3d-claude.vercel.app a couple of minutes later. Ask for changes in the same session
  ("trunk thicker") and the update publishes the same way.
- To add it to the game: on the model's page, tap **Copy prompt**, start a Claude Code session on
  the game repo, and paste. Claude downloads the FBX from the public site, so you don't have to transfer files.

## Local use

`bash scripts/build.sh wooden-crate --check` uses the installed Blender (macOS app or `bpy`).
Preview the site with `python3 -m http.server -d public`.
