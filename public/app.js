const REPO = "javaleer/3d-claude";
const RAW = `https://raw.githubusercontent.com/${REPO}/main/public/models`;

const $ = (id) => document.getElementById(id);
const gallery = $("gallery");
const detail = $("detail");
const viewer = $("viewer");

let models = [];
let originals = new Map(); // material name -> { base, alpha, emissive }
let selected = null;

async function load() {
  try {
    const res = await fetch("models.json", { cache: "no-cache" });
    models = (await res.json()).models || [];
  } catch {
    models = [];
  }
  $("count").textContent = `${models.length} model${models.length === 1 ? "" : "s"}`;
  renderGallery();
  route();
}

function renderGallery() {
  if (!models.length) {
    gallery.innerHTML = `<p class="empty">No models yet. Send Claude a photo to make the first one.</p>`;
    return;
  }
  gallery.innerHTML = models.map((m) => `
    <a class="card" href="#${m.slug}">
      <img src="models/${m.slug}/${m.files.thumb}" alt="${esc(m.name)}" loading="lazy">
      <div class="meta">
        <div class="title">${esc(m.name)}</div>
        <div class="sub">${m.tris.toLocaleString()} tris · ${m.materials.length} mat</div>
      </div>
    </a>`).join("");
}

function route() {
  const slug = decodeURIComponent(location.hash.slice(1));
  const m = models.find((x) => x.slug === slug);
  gallery.hidden = !!m;
  detail.hidden = !m;
  if (m) showModel(m);
  window.scrollTo(0, 0);
}

function showModel(m) {
  const base = `models/${m.slug}/`;
  document.title = `${m.name} · Low-Poly Assets`;
  $("name").textContent = m.name;
  $("desc").textContent = m.description || "";
  $("tris").textContent = m.tris.toLocaleString();
  $("size").textContent = m.size_m.map((n) => n.toFixed(2)).join(" × ");
  $("matCount").textContent = m.materials.length;
  $("dlFbx").href = base + m.files.fbx;
  $("dlGlb").href = base + m.files.glb;

  $("materials").innerHTML = m.materials.map((mt) => `
    <li><button class="mat" data-name="${esc(mt.name)}" aria-pressed="false">
      <span class="swatch" style="background:${mt.color}"></span>
      <span class="mname">${esc(mt.name)}</span>
      <span class="mhex">${mt.color}</span>
      <span class="mtris">${mt.tris} tris</span>
    </button></li>`).join("");

  $("prompt").textContent =
    `Add the low-poly asset "${m.slug}" from ${REPO} to the game.\n` +
    `FBX: ${RAW}/${m.slug}/${m.files.fbx}\n` +
    `Materials: ${m.materials.map((x) => `${x.name} ${x.color}`).join(", ")}\n` +
    `Follow the asset import rules in CLAUDE.md.`;

  selected = null;
  originals = new Map();
  $("clearSel").hidden = true;
  viewer.alt = m.name;
  viewer.poster = base + m.files.thumb;
  viewer.src = base + m.files.glb;
}

viewer.addEventListener("load", () => {
  originals = new Map();
  for (const mat of viewer.model?.materials || []) {
    const pbr = mat.pbrMetallicRoughness;
    originals.set(mat.name, {
      base: [...pbr.baseColorFactor],
      alpha: mat.getAlphaMode(),
      emissive: [...mat.emissiveFactor],
    });
  }
  if (selected) applyHighlight();
});

function applyHighlight() {
  for (const mat of viewer.model?.materials || []) {
    const o = originals.get(mat.name);
    if (!o) continue;
    const pbr = mat.pbrMetallicRoughness;
    if (!selected || mat.name === selected) {
      pbr.setBaseColorFactor(o.base);
      mat.setAlphaMode(o.alpha);
      // An orange glow (the site accent) marks the chosen material, even dark/grey ones.
      mat.setEmissiveFactor(selected ? [0.55, 0.24, 0.03] : o.emissive);
    } else {
      pbr.setBaseColorFactor([0.35, 0.4, 0.5, 0.08]);
      mat.setAlphaMode("BLEND");
      mat.setEmissiveFactor([0, 0, 0]);
    }
  }
  for (const b of document.querySelectorAll(".mat")) {
    b.setAttribute("aria-pressed", String(b.dataset.name === selected));
  }
  $("clearSel").hidden = !selected;
}

$("materials").addEventListener("click", (e) => {
  const btn = e.target.closest(".mat");
  if (!btn) return;
  selected = selected === btn.dataset.name ? null : btn.dataset.name;
  applyHighlight();
});
$("clearSel").addEventListener("click", () => { selected = null; applyHighlight(); });

$("copyPrompt").addEventListener("click", async () => {
  const btn = $("copyPrompt");
  try {
    await navigator.clipboard.writeText($("prompt").textContent);
    btn.textContent = "Copied";
  } catch {
    btn.textContent = "Copy failed. Long-press the text instead.";
  }
  setTimeout(() => (btn.textContent = "Copy prompt"), 1800);
});

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

window.addEventListener("hashchange", route);
load();
