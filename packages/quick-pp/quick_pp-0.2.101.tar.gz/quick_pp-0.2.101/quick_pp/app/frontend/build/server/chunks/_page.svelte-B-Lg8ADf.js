import { o as onDestroy, ak as fallback, a as attr, c as bind_props, m as attr_class, v as escape_html, i as stringify } from './error.svelte-DOTZbGc-.js';
import { B as Button } from './button-ChiBJf5X.js';
import { D as DepthFilterStatus } from './DepthFilterStatus-C1J1t2oq.js';
import { w as workspace, b as applyZoneFilter } from './workspace-C36GNT6i.js';
import { P as ProjectWorkspace } from './ProjectWorkspace-buzBVCPi.js';
import './WsWellPlot-CHO-dE21.js';

function WsRockTyping($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let projectId = fallback($$props["projectId"], null);
    let loading = false;
    let message = null;
    let fziLoading = false;
    let fziError = null;
    let fziData = null;
    let zoneFilter = { enabled: false, zones: [] };
    let lastProjectId = null;
    const unsubscribe = workspace.subscribe((w) => {
      if (w?.zoneFilter) {
        zoneFilter = { ...w.zoneFilter };
      }
    });
    onDestroy(() => unsubscribe());
    function getFilteredData() {
      if (!fziData) return null;
      const rows = fziData.phit.map((phit, i) => ({
        phit,
        perm: fziData.perm[i],
        zone: fziData.zones[i],
        well_name: fziData.well_names[i],
        depth: fziData.depths[i]
      }));
      const visibleRows = applyZoneFilter(rows, zoneFilter);
      return {
        phit: visibleRows.map((r) => r.phit),
        perm: visibleRows.map((r) => r.perm),
        zones: visibleRows.map((r) => r.zone),
        well_names: visibleRows.map((r) => r.well_name),
        depths: visibleRows.map((r) => r.depth)
      };
    }
    let cutoffsInput = "0.1, 1.0, 3.0, 6.0";
    const API_BASE = "http://localhost:6312";
    async function loadFZIData() {
      if (!projectId) return;
      fziLoading = true;
      fziError = null;
      try {
        const url = `${API_BASE}/quick_pp/database/projects/${projectId}/fzi_data`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(await res.text());
        fziData = await res.json();
      } catch (e) {
        fziError = e.message || "Failed to load FZI data";
        fziData = null;
      } finally {
        fziLoading = false;
      }
    }
    function plotFZI() {
      getFilteredData();
      return;
    }
    function plotPorePerm() {
      getFilteredData();
      return;
    }
    async function saveRockFlags() {
      if (!fziData || !projectId) return;
      loading = true;
      message = null;
      try {
        const phit = fziData.phit;
        const perm = fziData.perm;
        const wellNames = fziData.well_names;
        const depths = fziData.depths;
        const rqi = phit.map((p, i) => 0.0314 * Math.sqrt(perm[i] / p));
        const phiZ = phit.map((p) => p / (1 - p));
        const fziValues = rqi.map((r, i) => r / phiZ[i]);
        const cutoffs = cutoffsInput.split(",").map((s) => parseFloat(s.trim())).filter((n) => !isNaN(n) && n > 0);
        const rockFlagPairs = fziValues.map((fzi, i) => {
          let rockFlag = null;
          if (!isNaN(fzi) && isFinite(fzi)) {
            rockFlag = cutoffs.length + 1;
            for (let j = cutoffs.length - 1; j >= 0; j--) {
              if (fzi >= cutoffs[j]) {
                rockFlag = cutoffs.length - 1 - j + 1;
                break;
              }
            }
          }
          return {
            well_name: wellNames[i],
            depth: depths[i],
            rock_flag: rockFlag
          };
        });
        const url = `${API_BASE}/quick_pp/database/projects/${projectId}/save_rock_flags`;
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rock_flag_pairs: rockFlagPairs, cutoffs: cutoffsInput })
        });
        if (!res.ok) throw new Error(await res.text());
        const result = await res.json();
        message = `Success: ${result.message}`;
      } catch (e) {
        message = `Error: ${e.message}`;
      } finally {
        loading = false;
      }
    }
    if (projectId && projectId !== lastProjectId) {
      lastProjectId = projectId;
      loadFZIData();
    }
    if (fziData && cutoffsInput && zoneFilter) {
      plotFZI();
      plotPorePerm();
    }
    $$renderer2.push(`<div class="ws-rock-typing"><div class="mb-2"><div class="font-semibold">Rock Typing (Multi-Well)</div> <div class="text-sm text-muted-foreground">Cluster wells into rock types across the project.</div></div> `);
    DepthFilterStatus($$renderer2);
    $$renderer2.push(`<!----> <div class="bg-panel rounded p-3 mb-3"><div class="flex-1"><label for="cutoffs" class="block text-sm font-medium mb-1">FZI Cutoffs (comma-separated)</label> <div class="flex gap-2 items-end"><input id="cutoffs" type="text"${attr("value", cutoffsInput)} class="flex-1 px-3 py-2 border border-border rounded-md bg-background text-foreground" placeholder="e.g., 0.5,1.0,2.0"/> `);
    Button($$renderer2, {
      onclick: saveRockFlags,
      disabled: loading || !fziData,
      children: ($$renderer3) => {
        if (loading) {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<span>Saving...</span>`);
        } else {
          $$renderer3.push("<!--[!-->");
          $$renderer3.push(`<span>Save Rock Types</span>`);
        }
        $$renderer3.push(`<!--]-->`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!----></div></div> `);
    if (message) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div${attr_class(`text-sm ${stringify(message.startsWith("Error") ? "text-red-600" : "text-green-600")}`)}>${escape_html(message)}</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="font-semibold mb-2">FZI Log-Log Plot</div> <div class="text-sm text-muted-foreground mb-3">Plot Flow Zone Indicator (FZI) from porosity and permeability data across all wells.</div> `);
    if (fziLoading) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-sm text-blue-600 mb-3">Loading FZI data...</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      if (fziError) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="text-sm text-red-600 mb-3">${escape_html(fziError)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--> <div class="bg-surface rounded p-3 min-h-[400px]"><div class="w-full max-w-[600px] h-[500px] mx-auto"></div></div> <div class="font-semibold mb-2">Pore-Perm Crossplot</div> <div class="text-sm text-muted-foreground mb-3">Plot porosity vs permeability with FZI cutoff lines and rock type coloring.</div> <div class="bg-surface rounded p-3 min-h-[400px]"><div class="w-full max-w-[600px] h-[500px] mx-auto"></div></div></div></div>`);
    bind_props($$props, { projectId });
  });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let selectedProject = null;
    const unsubscribe = workspace.subscribe((w) => {
      selectedProject = w?.project ?? null;
    });
    onDestroy(() => unsubscribe());
    ProjectWorkspace($$renderer2, {
      project: selectedProject,
      $$slots: {
        left: ($$renderer3) => {
          $$renderer3.push(`<div slot="left">`);
          WsRockTyping($$renderer3, { projectId: selectedProject?.project_id ?? null });
          $$renderer3.push(`<!----></div>`);
        }
      }
    });
  });
}

export { _page as default };
//# sourceMappingURL=_page.svelte-B-Lg8ADf.js.map
