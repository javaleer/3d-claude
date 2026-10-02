# Paste this section into the CLAUDE.md of your Unity game repo

## Importing low-poly assets from javaleer/3d-claude

Models come from the asset gallery repo `javaleer/3d-claude`. Each one lives at
`https://3d-claude.vercel.app/models/<slug>/<slug>.fbx` (the public gallery site),
with metadata (materials, colors, size, triangle count) in `.../<slug>/meta.json`.

When asked to add an asset:
1. Download `<slug>.fbx` and `meta.json` with `curl -fsSL`. If the request only gives a slug,
   build the URL as shown above. If the download is blocked, the cloud environment's network
   access needs `3d-claude.vercel.app` added to its allowed domains.
2. Put the FBX at `Assets/Models/Props/<slug>/<slug>.fbx`. Use `Nature/`, `Buildings/`,
   `Vehicles/`, or `Characters/` instead of `Props/` based on `category` in meta.json.
3. Don't write `.meta` files by hand; Unity generates them on import. The FBX is already Y-up,
   scale 1, with its pivot at bottom-center, so no import-settings changes are needed.
4. If the user asks for a prefab or for it to be placed in a scene, create a prefab at
   `Assets/Prefabs/<slug>.prefab` only when you can do so reliably as YAML. Otherwise, say
   that dragging the FBX into the scene in the Unity editor is the remaining step.
5. Commit with the message `add asset: <slug>`.

Materials are embedded per color (for example `Wood`, `Leaves`) so they can be remapped in
Unity's Model Importer → Materials tab (or Extract Materials) to the game's own materials.
