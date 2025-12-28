import { o as onDestroy, ak as fallback, c as bind_props, m as attr_class, v as escape_html, i as stringify, x as ensure_array_like, a as attr } from './error.svelte-DOTZbGc-.js';
import { B as Button } from './button-ChiBJf5X.js';
import { D as DepthFilterStatus } from './DepthFilterStatus-C1J1t2oq.js';
import { w as workspace, b as applyZoneFilter } from './workspace-C36GNT6i.js';
import { P as ProjectWorkspace } from './ProjectWorkspace-buzBVCPi.js';
import './WsWellPlot-CHO-dE21.js';

function WsPermTransform($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let projectId = fallback($$props["projectId"], null);
    let loading = false;
    let message = null;
    let dataLoading = false;
    let dataError = null;
    let data = null;
    let fits = null;
    let zoneFilter = { enabled: false, zones: [] };
    let lastProjectId = null;
    const unsubscribe = workspace.subscribe((w) => {
      if (w?.zoneFilter && (zoneFilter.enabled !== w.zoneFilter.enabled || JSON.stringify(zoneFilter.zones) !== JSON.stringify(w.zoneFilter.zones))) {
        zoneFilter = { ...w.zoneFilter };
      }
    });
    onDestroy(() => unsubscribe());
    function getFilteredData() {
      if (!data) return null;
      const rows = data.phit.map((phit, i) => ({
        phit,
        perm: data.perm[i],
        zone: data.zones[i],
        well_name: data.well_names[i],
        depth: data.depths[i],
        rock_flag: data.rock_flags[i]
      }));
      const visibleRows = applyZoneFilter(rows, zoneFilter);
      console.log("Applying zone filter:", rows.length, zoneFilter, visibleRows.length);
      return {
        phit: visibleRows.map((r) => r.phit),
        perm: visibleRows.map((r) => r.perm),
        zones: visibleRows.map((r) => r.zone),
        well_names: visibleRows.map((r) => r.well_name),
        depths: visibleRows.map((r) => r.depth),
        rock_flags: visibleRows.map((r) => r.rock_flag)
      };
    }
    const API_BASE = "http://localhost:6312";
    async function loadData() {
      if (!projectId) return;
      dataLoading = true;
      dataError = null;
      try {
        const url = `${API_BASE}/quick_pp/database/projects/${projectId}/fzi_data`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(await res.text());
        data = await res.json();
        console.log("Loaded data:", data);
        const fitsUrl = `${API_BASE}/quick_pp/database/projects/${projectId}/poroperm_fits`;
        const fitsRes = await fetch(fitsUrl);
        if (!fitsRes.ok) throw new Error(await fitsRes.text());
        const fitsData = await fitsRes.json();
        fits = fitsData.fits;
        console.log("Loaded fits:", fits);
      } catch (e) {
        dataError = e.message || "Failed to load data";
        data = null;
        fits = null;
      } finally {
        dataLoading = false;
      }
    }
    function plotPorePerm() {
      getFilteredData();
      return;
    }
    async function savePermTrans() {
      if (!data || !fits || !projectId) return;
      loading = true;
      message = null;
      try {
        const permTransPairs = data.phit.map((phit, i) => {
          const rockFlag = data.rock_flags[i];
          let permTrans = null;
          if (rockFlag !== null && fits && fits[rockFlag.toFixed(1)]) {
            const { a, b } = fits[rockFlag.toFixed(1)];
            permTrans = a * Math.pow(phit, b);
          }
          return {
            well_name: data.well_names[i],
            depth: data.depths[i],
            perm_trans: permTrans
          };
        });
        const url = `${API_BASE}/quick_pp/database/projects/${projectId}/save_perm_trans`;
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ perm_trans_pairs: permTransPairs })
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
      loadData();
    }
    if (data && fits && zoneFilter) {
      plotPorePerm();
    }
    $$renderer2.push(`<div class="ws-perm-transform"><div class="mb-2"><div class="font-semibold">Permeability Transform</div> <div class="text-sm text-muted-foreground">Fit poro-perm curves per ROCK_FLAG and calculate transformed permeability.</div></div> `);
    DepthFilterStatus($$renderer2);
    $$renderer2.push(`<!----> <div class="bg-panel rounded p-3 mb-3"><div class="flex-1"><div class="flex gap-2 items-end">`);
    Button($$renderer2, {
      onclick: savePermTrans,
      disabled: loading || !data,
      children: ($$renderer3) => {
        if (loading) {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<span>Saving...</span>`);
        } else {
          $$renderer3.push("<!--[!-->");
          $$renderer3.push(`<span>Save Perm Transforms</span>`);
        }
        $$renderer3.push(`<!--]-->`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!----></div> `);
    if (message) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div${attr_class(`text-sm ${stringify(message.startsWith("Error") ? "text-red-600" : "text-green-600")}`)}>${escape_html(message)}</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (fits) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="font-semibold mb-2">Fitted Parameters</div> <div class="text-sm text-muted-foreground mb-3">Edit a and b parameters to update the fitted curves.</div> <div class="bg-surface rounded p-3"><table class="w-full border-collapse border border-border"><thead><tr class="bg-muted"><th class="border border-border p-2 text-left">Rock Flag</th><th class="border border-border p-2 text-left">a</th><th class="border border-border p-2 text-left">b</th></tr></thead><tbody><!--[-->`);
      const each_array = ensure_array_like(Object.keys(fits).sort((a, b) => parseInt(a) - parseInt(b)));
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let rf = each_array[$$index];
        $$renderer2.push(`<tr><td class="border border-border p-2">${escape_html(rf)}</td><td class="border border-border p-2"><input type="number" step="0.01" class="w-full px-2 py-1 border border-border rounded"${attr("value", fits[rf].a)}/></td><td class="border border-border p-2"><input type="number" step="0.01" class="w-full px-2 py-1 border border-border rounded"${attr("value", fits[rf].b)}/></td></tr>`);
      }
      $$renderer2.push(`<!--]--></tbody></table></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="font-semibold mb-2">Poro-Perm Crossplot with Fitted Curves</div> <div class="text-sm text-muted-foreground mb-3">Plot porosity vs permeability with fitted curves per ROCK_FLAG.</div> `);
    if (dataLoading) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-sm text-blue-600 mb-3">Loading data...</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      if (dataError) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="text-sm text-red-600 mb-3">${escape_html(dataError)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--> <div class="bg-surface rounded p-3 min-h-[400px]"><div class="w-full h-[500px] mx-auto"></div></div></div></div>`);
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
          WsPermTransform($$renderer3, { projectId: selectedProject?.project_id ?? null });
          $$renderer3.push(`<!----></div>`);
        }
      }
    });
  });
}

export { _page as default };
//# sourceMappingURL=_page.svelte-C3AhSUZ1.js.map
