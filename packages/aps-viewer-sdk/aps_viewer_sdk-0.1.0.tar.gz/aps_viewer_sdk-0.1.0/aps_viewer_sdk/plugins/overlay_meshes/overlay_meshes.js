(function () {
  const EXT_ID = "My.OverlayMeshes";
  const DEFAULT_SCENE = "overlay_meshes";

  function clamp01(x) {
    return Math.max(0, Math.min(1, x));
  }

  function parseColor(color) {
    if (typeof color !== "string") {
      return 0x00ff00;
    }
    const c = color.trim().toLowerCase();
    if (c.startsWith("#") && (c.length === 7 || c.length === 4)) {
      const hex =
        c.length === 4
          ? "#" + c[1] + c[1] + c[2] + c[2] + c[3] + c[3]
          : c;
      return parseInt(hex.slice(1), 16);
    }
    if (c.startsWith("0x")) {
      return parseInt(c, 16);
    }
    return 0x00ff00;
  }

  function getThree() {
    return (
      (window.Autodesk &&
        Autodesk.Viewing &&
        Autodesk.Viewing.Private &&
        Autodesk.Viewing.Private.THREE) ||
      window.THREE
    );
  }

  function createMaterial(color, opacity, THREE_REF) {
    const transparent = opacity < 1;
    return new THREE_REF.MeshPhongMaterial({
      color: parseColor(color),
      opacity: clamp01(opacity),
      transparent,
      depthWrite: !transparent,
      side: THREE_REF.DoubleSide,
    });
  }

  function createMeshFromSpec(spec, THREE_REF) {
    if (!spec || typeof spec !== "object") return null;
    const type = spec.type;
    const opacity = typeof spec.opacity === "number" ? spec.opacity : 1.0;
    const color = spec.color || "#00ff00";
    let geometry = null;

    if (type === "box") {
      const w = parseFloat(spec.width) || 1;
      const h = parseFloat(spec.height) || 1;
      const d = parseFloat(spec.depth) || 1;
      geometry = new THREE_REF.BoxGeometry(w, h, d);
    } else if (type === "sphere") {
      const radius = parseFloat(spec.radius) || 1;
      const segments = parseInt(spec.segments, 10) || 16;
      geometry = new THREE_REF.SphereGeometry(radius, segments, segments);
    } else if (type === "cone") {
      const radius = parseFloat(spec.radius) || 1;
      const height = parseFloat(spec.height) || 1;
      const segments = parseInt(spec.radialSegments, 10) || 18;
      const radiusTop = Math.max(1e-3, radius * 0.05);
      const radiusBottom = radius;
      geometry = new THREE_REF.CylinderGeometry(
        radiusTop,
        radiusBottom,
        height,
        segments
      );
    }

    if (!geometry) return null;

    const material = createMaterial(color, opacity, THREE_REF);
    const mesh = new THREE_REF.Mesh(geometry, material);
    const pos = Array.isArray(spec.position) ? spec.position : [0, 0, 0];
    mesh.position.set(
      parseFloat(pos[0]) || 0,
      parseFloat(pos[1]) || 0,
      parseFloat(pos[2]) || 0
    );

    if (spec.alignToWorldUp) {
      mesh.rotateX(Math.PI / 2);
    }

    mesh.updateMatrix();
    mesh.matrixAutoUpdate = true;
    return mesh;
  }

  function ensureOverlayScene(viewer, sceneId) {
    const impl = viewer && viewer.impl;
    if (!impl) return false;
    const overlays = impl.overlayScenes || null;
    if (overlays && overlays[sceneId]) {
      return true;
    }
    impl.createOverlayScene(sceneId);
    return true;
  }

  class OverlayMeshesExtension extends Autodesk.Viewing.Extension {
    constructor(viewer, options) {
      super(viewer, options);

      const opt = options || {};
      this._items = Array.isArray(opt.items) ? opt.items : [];
      this._sceneMeshes = new Map();
    }

    load() {
      this._addMeshes();
      return true;
    }

    unload() {
      this._clearMeshes();
      return true;
    }

    _addMeshes() {
      if (!this.viewer || !Array.isArray(this._items) || !this._items.length) {
        return;
      }

      const THREE_REF = getThree();
      if (!THREE_REF) {
        console.warn("[OverlayMeshes] THREE not available");
        return;
      }

      const initialized = new Set();

      for (let i = 0; i < this._items.length; i++) {
        const spec = this._items[i];
        const sceneId = (spec && spec.sceneId) || DEFAULT_SCENE;

        if (!initialized.has(sceneId)) {
          ensureOverlayScene(this.viewer, sceneId);
          initialized.add(sceneId);
        }

        const mesh = createMeshFromSpec(spec, THREE_REF);
        if (!mesh) continue;

        this.viewer.impl.addOverlay(sceneId, mesh);

        if (!this._sceneMeshes.has(sceneId)) {
          this._sceneMeshes.set(sceneId, []);
        }
        this._sceneMeshes.get(sceneId).push(mesh);
      }

      this.viewer.impl.invalidate(true, true, true);
    }

    _clearMeshes() {
      if (!this.viewer || !this.viewer.impl) return;

      for (const [sceneId, meshes] of this._sceneMeshes.entries()) {
        for (let i = 0; i < meshes.length; i++) {
          const mesh = meshes[i];
          this.viewer.impl.removeOverlay(sceneId, mesh);
          if (mesh.geometry) mesh.geometry.dispose();
          if (mesh.material) mesh.material.dispose();
        }
      }

      this._sceneMeshes.clear();
      this.viewer.impl.invalidate(true, true, true);
    }
  }

  Autodesk.Viewing.theExtensionManager.registerExtension(
    EXT_ID,
    OverlayMeshesExtension
  );
})();
