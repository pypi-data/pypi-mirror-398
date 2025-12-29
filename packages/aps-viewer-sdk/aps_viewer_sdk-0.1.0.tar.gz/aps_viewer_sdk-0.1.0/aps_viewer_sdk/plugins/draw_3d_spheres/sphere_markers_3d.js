(function () {
  const EXT_ID = "My.SphereMarkers";
  const TOOL_DRAW = "My.SphereMarkers.DrawTool";
  const TOOL_REMOVE = "My.SphereMarkers.RemoveTool";
  const OVERLAY = "my-spheremarkers-overlay";

  const SVG = {
    draw: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="9" stroke="#fff" stroke-width="1.8"/>
      <line x1="12" y1="7" x2="12" y2="17" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>
      <line x1="7" y1="12" x2="17" y2="12" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>
    </svg>`,
    remove: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="9" stroke="#fff" stroke-width="1.8"/>
      <line x1="8" y1="8" x2="16" y2="16" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>
      <line x1="16" y1="8" x2="8" y2="16" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>
    </svg>`,
    size: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="5" stroke="#fff" stroke-width="1.8"/>
      <circle cx="12" cy="12" r="9" stroke="#fff" stroke-width="1.8" stroke-dasharray="3 2"/>
    </svg>`,
    clear: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
      <path d="M5 7h14" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>
      <path d="M9 7V5h6v2" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M7 7l1 12h8l1-12" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`,
  };

  function is3d(viewer) {
    const m = viewer && viewer.model;
    return !(m && typeof m.is2d === "function" && m.is2d());
  }

  function waitForToolbar(viewer) {
    const tb = viewer.getToolbar && viewer.getToolbar();
    if (tb) return Promise.resolve(tb);

    return new Promise((resolve) => {
      const onCreated = () => {
        viewer.removeEventListener(Autodesk.Viewing.TOOLBAR_CREATED_EVENT, onCreated);
        resolve(viewer.getToolbar());
      };
      viewer.addEventListener(Autodesk.Viewing.TOOLBAR_CREATED_EVENT, onCreated);
    });
  }

  function svgDataUrl(svg) {
    return (
      "data:image/svg+xml," +
      encodeURIComponent(svg).replace(/'/g, "%27").replace(/"/g, "%22")
    );
  }

  function applySvgIcon(btn, svg) {
    if (!btn || !btn.container) return;
    const iconEl = btn.container.querySelector(".adsk-button-icon");
    if (!iconEl) return;

    iconEl.style.backgroundImage = `url("${svgDataUrl(svg)}")`;
    iconEl.style.backgroundRepeat = "no-repeat";
    iconEl.style.backgroundPosition = "center";
    iconEl.style.backgroundSize = "20px 20px";
    iconEl.style.backgroundColor = "transparent";
    iconEl.style.width = "24px";
    iconEl.style.height = "24px";
    iconEl.style.fontSize = "0";
    iconEl.style.lineHeight = "0";
  }

  function setButtonState(btn, active) {
    if (!btn || !btn.setState) return;
    const S = Autodesk.Viewing.UI.Button.State;
    btn.setState(active ? S.ACTIVE : S.INACTIVE);
  }

  function ensureUiStyles(viewer) {
    const doc = viewer.container.ownerDocument;
    const id = "my-spheremarkers-styles";
    if (doc.getElementById(id)) return;

    const style = doc.createElement("style");
    style.id = id;
    style.textContent = `
      .my-spheremarkers-flyout{
        position:absolute;
        z-index:9999;
        font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
        font-size:12px;
        line-height:1.25;
        color:rgba(255,255,255,.92);
        background:rgba(33,36,40,.92);
        border:1px solid rgba(255,255,255,.10);
        border-radius:12px;
        box-shadow:0 10px 24px rgba(0,0,0,.34);
        backdrop-filter:blur(6px);
        -webkit-backdrop-filter:blur(6px);
        user-select:none;
      }

      /* ===== Context menu (Remove | Cancel) ===== */
      .my-spheremarkers-menu{
        display:none;
        padding:8px;
        gap:8px;
        width:208px;
        align-items:stretch;
      }
      .my-spheremarkers-menu button{
        appearance:none;
        border:1px solid rgba(255,255,255,.14);
        background:rgba(45,50,56,.92);
        color:rgba(255,255,255,.95);
        height:30px;
        padding:0 12px;
        border-radius:10px;
        cursor:pointer;
        font-weight:700;
        letter-spacing:.1px;
        flex:1;
        transition:background 120ms ease,border-color 120ms ease,transform 80ms ease,box-shadow 120ms ease;
      }
      .my-spheremarkers-menu button:hover{
        background:rgba(55,61,68,.96);
        border-color:rgba(255,255,255,.24);
      }
      .my-spheremarkers-menu button:active{ transform:translateY(1px); }
      .my-spheremarkers-menu button:focus-visible{
        outline:none;
        box-shadow:0 0 0 2px rgba(255,255,255,.10);
        border-color:rgba(255,255,255,.28);
      }

      /* ===== Minimal Sphere size panel ===== */
      .my-spheremarkers-size{
        display:none;
        right:12px;
        top:12px;
        width:165px;
        padding:8px;
      }

      .my-spheremarkers-size .header{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:8px;
        margin-bottom:6px;
      }

      .my-spheremarkers-size .title{
        font-weight:700;
        font-size:11px;
        color:rgba(255,255,255,.92);
        margin:0;
      }

      .my-spheremarkers-size input[type="number"]{
        width:48px;
        height:22px;
        padding:0 6px;
        border-radius:8px;
        border:none;
        background:transparent;
        color:rgba(255,255,255,.95);
        outline:none;
        text-align:right;
        font-size:11px;
      }
      .my-spheremarkers-size input[type="number"]:focus{
        outline:none;
      }
      .my-spheremarkers-size input[type="number"]::-webkit-outer-spin-button,
      .my-spheremarkers-size input[type="number"]::-webkit-inner-spin-button{
        -webkit-appearance:none;
        margin:0;
      }
      .my-spheremarkers-size input[type="number"]{ -moz-appearance:textfield; }

      .my-spheremarkers-size .slider{
        width:100%;
        height:16px;
        background:transparent;
        -webkit-appearance:none;
        appearance:none;
        cursor:pointer;
        display:block;
      }

      .my-spheremarkers-size .slider::-webkit-slider-runnable-track{
        height:2px;
        background:rgba(255,255,255,.28);
        border-radius:999px;
      }
      .my-spheremarkers-size .slider::-webkit-slider-thumb{
        -webkit-appearance:none;
        appearance:none;
        width:10px;
        height:10px;
        margin-top:-4px;
        border-radius:50%;
        background:#fff;
        box-shadow:0 2px 8px rgba(0,0,0,.3);
        border:1px solid rgba(0,0,0,.12);
      }

      .my-spheremarkers-size .slider::-moz-range-track{
        height:2px;
        background:rgba(255,255,255,.28);
        border-radius:999px;
      }
      .my-spheremarkers-size .slider::-moz-range-thumb{
        width:10px;
        height:10px;
        border-radius:50%;
        background:#fff;
        box-shadow:0 2px 8px rgba(0,0,0,.3);
        border:1px solid rgba(0,0,0,.12);
      }

      .my-spheremarkers-size .hint{
        margin-top:4px;
        font-size:10px;
        color:rgba(255,255,255,.60);
      }
    `;
    doc.head.appendChild(style);
  }

  function ensureOverlay(viewer) {
    const impl = viewer.impl;
    if (!impl.overlayScenes || !impl.overlayScenes[OVERLAY]) {
      impl.createOverlayScene(OVERLAY);
    }
  }

  function getThree(viewer) {
    return (
      (viewer && viewer.impl && viewer.impl.THREE) ||
      (Autodesk && Autodesk.Viewing && Autodesk.Viewing.Private && Autodesk.Viewing.Private.THREE) ||
      window.THREE ||
      null
    );
  }

  function pickModelPoint(viewer, event) {
    const res = viewer.impl.hitTest(event.canvasX, event.canvasY, true);
    if (res && res.intersectPoint) return res;
    return null;
  }

  function dist2(ax, ay, bx, by) {
    const dx = ax - bx;
    const dy = ay - by;
    return dx * dx + dy * dy;
  }

  function createContextMenu(viewer) {
    ensureUiStyles(viewer);
    const doc = viewer.container.ownerDocument;

    const menu = doc.createElement("div");
    menu.className = "my-spheremarkers-flyout my-spheremarkers-menu";

    const removeBtn = doc.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "Remove";

    const cancelBtn = doc.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.textContent = "Cancel";

    menu.appendChild(removeBtn);
    menu.appendChild(cancelBtn);

    viewer.container.style.position = viewer.container.style.position || "relative";
    viewer.container.appendChild(menu);

    function show(x, y) {
      menu.style.left = `${x}px`;
      menu.style.top = `${y}px`;
      menu.style.display = "flex";
    }
    function hide() {
      menu.style.display = "none";
    }

    return { el: menu, removeBtn, cancelBtn, show, hide };
  }

  function createSizePanel(viewer, state) {
    ensureUiStyles(viewer);
    const doc = viewer.container.ownerDocument;

    const panel = doc.createElement("div");
    panel.className = "my-spheremarkers-flyout my-spheremarkers-size";
    panel.style.position = "absolute";
    panel.style.zIndex = "9999";

    const header = doc.createElement("div");
    header.className = "header";

    const title = doc.createElement("div");
    title.textContent = "Sphere size";
    title.className = "title";

    const number = doc.createElement("input");
    number.type = "number";
    number.min = "0.1";
    number.step = "0.1";
    number.value = String(state.radius);

    header.appendChild(title);
    header.appendChild(number);

    const slider = doc.createElement("input");
    slider.className = "slider";
    slider.type = "range";
    slider.min = "0.1";
    slider.max = "50";
    slider.step = "0.1";
    slider.value = String(state.radius);

    const unitHint = doc.createElement("div");
    unitHint.textContent = "Units = model units";
    unitHint.className = "hint";

    function setRadius(v) {
      const n = Number(v);
      if (!Number.isFinite(n) || n <= 0) return;
      state.radius = n;
      slider.value = String(n);
      number.value = String(n);
    }

    slider.addEventListener("input", () => setRadius(slider.value));
    number.addEventListener("input", () => setRadius(number.value));

    panel.appendChild(header);
    panel.appendChild(slider);
    panel.appendChild(unitHint);

    viewer.container.appendChild(panel);

    function isHidden() {
      const cs = doc.defaultView ? doc.defaultView.getComputedStyle(panel) : null;
      const display = panel.style.display || (cs ? cs.display : "");
      return display === "none" || display === "";
    }

    return {
      show() { panel.style.display = "block"; },
      hide() { panel.style.display = "none"; },
      toggle() { panel.style.display = isHidden() ? "block" : "none"; },
      el: panel,
    };
  }

  class DrawSphereTool {
    constructor(viewer, api) {
      this.viewer = viewer;
      this.api = api;
    }
    getNames() {
      return [TOOL_DRAW];
    }
    getName() {
      return TOOL_DRAW;
    }
    getPriority() {
      return 0;
    }
    activate() {
      return true;
    }
    deactivate() {
      return true;
    }

    handleSingleClick(event) {
      if (!is3d(this.viewer)) return false;
      const res = pickModelPoint(this.viewer, event);
      if (!res) return false;
      this.api.addSphere(res);
      return true;
    }
  }

  class RemoveSphereTool {
    constructor(viewer, api) {
      this.viewer = viewer;
      this.api = api;
    }
    getNames() {
      return [TOOL_REMOVE];
    }
    getName() {
      return TOOL_REMOVE;
    }
    getPriority() {
      return 0;
    }
    activate() {
      return true;
    }
    deactivate() {
      this.api.hideRemoveMenu();
      return true;
    }

    handleSingleClick(event) {
      if (!is3d(this.viewer)) return false;
      const hit = this.api.pickSphere(event);
      if (!hit) return false;
      this.api.showRemoveMenuForHit(hit, event);
      return true;
    }
  }

  class SphereMarkersExtension extends Autodesk.Viewing.Extension {
    constructor(viewer, options) {
      super(viewer, options);

      this._group = null;
      this._btnDraw = null;
      this._btnRemove = null;
      this._btnSize = null;
      this._btnClear = null;

      this._sizePanel = null;
      this._menu = null;

      this._toolDraw = null;
      this._toolRemove = null;

      this.spheres = [];
      this._sphereById = new Map();

      const opt = options || {};
      const initRadius = Number(opt.initialRadius);
      const initColor = typeof opt.color === "string" ? opt.color : "#ff0000";

      this.state = {
        radius: Number.isFinite(initRadius) && initRadius > 0 ? initRadius : 2.0,
        color: initColor,
        nextId: 1,
        selectedId: null,
      };
    }

    async load() {
      ensureOverlay(this.viewer);

      this._menu = createContextMenu(this.viewer);
      this._menu.cancelBtn.addEventListener("click", () => this.hideRemoveMenu());
      this._menu.removeBtn.addEventListener("click", () => {
        if (this.state.selectedId != null) this.removeSphere(this.state.selectedId);
        this.hideRemoveMenu();
      });

      this._sizePanel = createSizePanel(this.viewer, this.state);

      this._toolDraw = new DrawSphereTool(this.viewer, this);
      this._toolRemove = new RemoveSphereTool(this.viewer, this);
      this.viewer.toolController.registerTool(this._toolDraw);
      this.viewer.toolController.registerTool(this._toolRemove);

      await waitForToolbar(this.viewer);
      this._createToolbar();

      return true;
    }

    unload() {
      this.clearAll();

      if (this._menu && this._menu.el && this._menu.el.parentNode) {
        this._menu.el.parentNode.removeChild(this._menu.el);
      }
      if (this._sizePanel && this._sizePanel.el && this._sizePanel.el.parentNode) {
        this._sizePanel.el.parentNode.removeChild(this._sizePanel.el);
      }

      const tc = this.viewer.toolController;
      tc.deactivateTool(TOOL_DRAW);
      tc.deactivateTool(TOOL_REMOVE);
      if (this._toolDraw) tc.deregisterTool(this._toolDraw);
      if (this._toolRemove) tc.deregisterTool(this._toolRemove);

      const tb = this.viewer.getToolbar && this.viewer.getToolbar();
      if (tb && this._group) tb.removeControl(this._group);

      this._group = null;
      return true;
    }

    _createToolbar() {
      const tb = this.viewer.getToolbar();
      const groupId = "my-spheremarkers-group";
      this._group =
        tb.getControl(groupId) || new Autodesk.Viewing.UI.ControlGroup(groupId);
      if (!tb.getControl(groupId)) tb.addControl(this._group);

      this._btnDraw = new Autodesk.Viewing.UI.Button("my-spheremarkers-draw");
      this._btnDraw.setToolTip("Draw spheres");
      this._btnDraw.onClick = () => this._activateMode("draw");
      this._group.addControl(this._btnDraw);

      this._btnRemove = new Autodesk.Viewing.UI.Button("my-spheremarkers-remove");
      this._btnRemove.setToolTip("Remove spheres (click sphere -> Remove)");
      this._btnRemove.onClick = () => this._activateMode("remove");
      this._group.addControl(this._btnRemove);

      this._btnSize = new Autodesk.Viewing.UI.Button("my-spheremarkers-size");
      this._btnSize.setToolTip("Sphere size");
      this._btnSize.onClick = () => this._sizePanel.toggle();
      this._group.addControl(this._btnSize);

      this._btnClear = new Autodesk.Viewing.UI.Button("my-spheremarkers-clear");
      this._btnClear.setToolTip("Clear all spheres");
      this._btnClear.onClick = () => this.clearAll();
      this._group.addControl(this._btnClear);

      requestAnimationFrame(() => {
        applySvgIcon(this._btnDraw, SVG.draw);
        applySvgIcon(this._btnRemove, SVG.remove);
        applySvgIcon(this._btnSize, SVG.size);
        applySvgIcon(this._btnClear, SVG.clear);
      });

      this._activateMode("draw");
    }

    _activateMode(mode) {
      const tc = this.viewer.toolController;

      this.hideRemoveMenu();

      tc.deactivateTool(TOOL_DRAW);
      tc.deactivateTool(TOOL_REMOVE);

      if (mode === "draw") {
        tc.activateTool(TOOL_DRAW);
        setButtonState(this._btnDraw, true);
        setButtonState(this._btnRemove, false);
      } else {
        tc.activateTool(TOOL_REMOVE);
        setButtonState(this._btnDraw, false);
        setButtonState(this._btnRemove, true);
      }
    }

    getSpheres() {
      return this.spheres.slice();
    }

    _parseHexColor(hex) {
      const s = String(hex || "").trim();
      if (s.startsWith("#") && s.length === 7) {
        return parseInt(s.slice(1), 16);
      }
      if (s.startsWith("0x") && s.length === 8) {
        return parseInt(s.slice(2), 16);
      }
      return 0xff0000;
    }

    addSphere(hitRes) {
      if (!is3d(this.viewer)) return;

      const THREE = getThree(this.viewer);
      if (!THREE) return;

      ensureOverlay(this.viewer);

      const p = hitRes.intersectPoint;
      const id = this.state.nextId++;
      const radius = this.state.radius;

      const geom = new THREE.SphereGeometry(radius, 24, 18);
      const mat = new THREE.MeshPhongMaterial({
        color: this._parseHexColor(this.state.color),
        transparent: true,
        opacity: 0.35,
        depthTest: false,
        depthWrite: false,
      });

      const mesh = new THREE.Mesh(geom, mat);
      mesh.position.set(p.x, p.y, p.z);
      mesh.userData.sphereId = id;

      this.viewer.impl.addOverlay(OVERLAY, mesh);

      const data = { id, x: p.x, y: p.y, z: p.z, radius };
      this.spheres.push(data);
      this._sphereById.set(id, { data, mesh });

      this.viewer.impl.invalidate(true, true, true);
    }

    removeSphere(id) {
      const entry = this._sphereById.get(id);
      if (!entry) return;

      const { mesh } = entry;

      this.viewer.impl.removeOverlay(OVERLAY, mesh);

      if (mesh.geometry) mesh.geometry.dispose();
      if (mesh.material) mesh.material.dispose();

      this._sphereById.delete(id);
      this.spheres = this.spheres.filter((s) => s.id !== id);

      this.viewer.impl.invalidate(true, true, true);
    }

    clearAll() {
      for (const [, entry] of this._sphereById.entries()) {
        const mesh = entry.mesh;
        this.viewer.impl.removeOverlay(OVERLAY, mesh);
        if (mesh.geometry) mesh.geometry.dispose();
        if (mesh.material) mesh.material.dispose();
      }
      this._sphereById.clear();
      this.spheres = [];
      this.state.selectedId = null;

      this.hideRemoveMenu();
      this.viewer.impl.invalidate(true, true, true);
    }

    pickSphere(event) {
      if (!is3d(this.viewer)) return null;

      const THREE = getThree(this.viewer);
      if (!THREE) return null;

      const clickX = event.canvasX;
      const clickY = event.canvasY;

      let best = null;
      let bestD2 = Infinity;

      for (const [, entry] of this._sphereById.entries()) {
        const { data, mesh } = entry;

        const c2 = this.viewer.impl.worldToClient(mesh.position.clone());

        const edgeWorld = mesh.localToWorld(new THREE.Vector3(data.radius, 0, 0));
        const e2 = this.viewer.impl.worldToClient(edgeWorld);

        const rPx = Math.hypot(e2.x - c2.x, e2.y - c2.y);
        const thresh = Math.max(12, rPx);

        const d2 = dist2(clickX, clickY, c2.x, c2.y);
        if (d2 <= thresh * thresh && d2 < bestD2) {
          bestD2 = d2;
          best = mesh;
        }
      }

      return best ? { object: best } : null;
    }

    showRemoveMenuForHit(hit, event) {
      const sphereId =
        hit.object && hit.object.userData ? hit.object.userData.sphereId : null;
      if (sphereId == null) return;

      this.state.selectedId = sphereId;

      const rect = this.viewer.container.getBoundingClientRect();
      const x = event.clientX - rect.left + 8;
      const y = event.clientY - rect.top + 8;

      this._menu.show(x, y);
    }

    hideRemoveMenu() {
      this.state.selectedId = null;
      if (this._menu) this._menu.hide();
    }
  }

  Autodesk.Viewing.theExtensionManager.registerExtension(EXT_ID, SphereMarkersExtension);
})();
