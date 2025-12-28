import { al as writable, t as derived$1, am as get$2 } from './error.svelte-DOTZbGc-.js';

const projects = writable([]);
const wellStatsCache = writable(/* @__PURE__ */ new Map());
function getStatsCache(projectId, wellName) {
  const cache = get$2(wellStatsCache);
  return cache.get(`${projectId}-${wellName}`);
}
function setStatsCache(projectId, wellName, data) {
  wellStatsCache.update((cache) => {
    cache.set(`${projectId}-${wellName}`, { data, timestamp: Date.now() });
    return cache;
  });
}
function clearStatsCache(projectId, wellName) {
  if (projectId && wellName) {
    wellStatsCache.update((cache) => {
      cache.delete(`${projectId}-${wellName}`);
      return cache;
    });
  } else {
    wellStatsCache.set(/* @__PURE__ */ new Map());
  }
}
const workspace = writable({
  title: "QPP - Petrophysical Analysis",
  subtitle: void 0,
  project: null,
  depthFilter: {
    enabled: false,
    minDepth: null,
    maxDepth: null
  },
  zoneFilter: {
    enabled: false,
    zones: []
  }
});
const depthFilter = derived$1(workspace, ($workspace) => $workspace.depthFilter);
const zoneFilter = derived$1(workspace, ($workspace) => $workspace.zoneFilter);
derived$1(workspace, ($workspace) => $workspace.project);
derived$1(workspace, ($workspace) => ({ title: $workspace.title, subtitle: $workspace.subtitle }));
function selectProject(project) {
  workspace.update((s) => {
    const curId = s.project && s.project.project_id != null ? String(s.project.project_id) : null;
    const newId = project && project.project_id != null ? String(project.project_id) : null;
    const curName = s.project && s.project.name ? s.project.name : null;
    let incomingName = null;
    if (project && project.name) incomingName = project.name;
    else if (project && project.project_id) {
      try {
        const list = get$2(projects) || [];
        const found = list.find((p) => String(p.project_id) === String(project.project_id));
        if (found && found.name) incomingName = found.name;
      } catch (e) {
      }
    }
    const newName = incomingName;
    if (curId === newId && curName === newName) return s;
    const projToSet = project ? { ...project, ...newName ? { name: newName } : {} } : null;
    return { ...s, project: projToSet, title: projToSet ? projToSet.name ?? "QPP - Petrophysical Analysis" : "QPP - Petrophysical Analysis" };
  });
}
async function selectProjectAndLoadWells(project) {
  if (!project || !project.project_id) {
    selectProject(null);
    return;
  }
  selectProject(project);
  const API_BASE = "http://localhost:6312";
  try {
    const res = await fetch(`${API_BASE}/quick_pp/database/projects/${project.project_id}/wells`);
    if (res.ok) {
      const data = await res.json();
      const wells = data.wells || [];
      workspace.update((s) => {
        if (s.project && String(s.project.project_id) === String(project.project_id)) {
          return { ...s, project: { ...s.project, wells } };
        }
        return s;
      });
    }
  } catch (err) {
    console.error("Failed to load wells for project", project.project_id, err);
  }
}
function selectWell(well) {
  workspace.update((s) => ({ ...s, selectedWell: well }));
}
function applyDepthFilter(rows, depthFilter2) {
  if (!depthFilter2?.enabled || !depthFilter2.minDepth && !depthFilter2.maxDepth) {
    return rows;
  }
  return rows.filter((row) => {
    const depth = Number(row.depth ?? row.DEPTH ?? row.Depth ?? NaN);
    if (isNaN(depth)) return false;
    if (depthFilter2.minDepth !== null && depth < depthFilter2.minDepth) return false;
    if (depthFilter2.maxDepth !== null && depth > depthFilter2.maxDepth) return false;
    return true;
  });
}
function extractZoneValue(row) {
  if (!row || typeof row !== "object") return null;
  const candidates = ["name", "zone", "Zone", "ZONE", "formation", "formation_name", "formationName", "FORMATION", "formation_top", "formationTop"];
  for (const k of candidates) {
    if (k in row && row[k] !== null && row[k] !== void 0 && String(row[k]).trim() !== "") {
      return String(row[k]);
    }
  }
  for (const k of Object.keys(row)) {
    if (/zone|formation/i.test(k) && row[k] !== null && row[k] !== void 0 && String(row[k]).trim() !== "") {
      return String(row[k]);
    }
  }
  return null;
}
function applyZoneFilter(rows, zoneFilter2) {
  if (!zoneFilter2?.enabled || !zoneFilter2.zones || zoneFilter2.zones.length === 0) return rows;
  const allowed = new Set(zoneFilter2.zones.map((z) => String(z)));
  return rows.filter((row) => {
    const val = extractZoneValue(row);
    if (val === null) return false;
    return allowed.has(val);
  });
}

export { selectWell as a, applyZoneFilter as b, applyDepthFilter as c, depthFilter as d, setStatsCache as e, clearStatsCache as f, getStatsCache as g, projects as p, selectProjectAndLoadWells as s, workspace as w, zoneFilter as z };
//# sourceMappingURL=workspace-C36GNT6i.js.map
