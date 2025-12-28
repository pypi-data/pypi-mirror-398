import { o as onDestroy, a as attr, x as ensure_array_like, v as escape_html, i as stringify, c as bind_props } from './error.svelte-DOTZbGc-.js';
import { B as Button } from './button-ChiBJf5X.js';
import { P as ProjectWorkspace } from './ProjectWorkspace-buzBVCPi.js';
import { w as workspace } from './workspace-C36GNT6i.js';
import './WsWellPlot-CHO-dE21.js';
import './DepthFilterStatus-C1J1t2oq.js';

function WsReservoirSummary($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let filtered;
    let projectId = $$props["projectId"];
    let wellName = $$props["wellName"];
    const API_BASE = "http://localhost:6312";
    let loading = false;
    let error = null;
    let fullRows = [];
    let ressumRows = [];
    let minPhit = 0.01;
    let maxSwt = 0.99;
    let maxVclay = 0.4;
    let dtInstance = null;
    onDestroy(() => {
      try {
        if (dtInstance) dtInstance.destroy();
      } catch (e) {
      }
      dtInstance = null;
    });
    async function loadWellData() {
      if (!projectId || !wellName) return;
      loading = true;
      error = null;
      try {
        const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/wells/${encodeURIComponent(String(wellName))}/merged`);
        if (!res.ok) throw new Error(await res.text());
        const fd = await res.json();
        const rows = fd && fd.data ? fd.data : fd;
        if (!Array.isArray(rows)) throw new Error("Unexpected data format from backend");
        fullRows = rows;
      } catch (e) {
        console.warn("Failed to load well data", e);
        error = String(e?.message ?? e);
      } finally {
        loading = false;
      }
    }
    function buildRessumPayload() {
      const filteredRows = Array.isArray(fullRows) ? fullRows : [];
      const mappedRows = [];
      for (const r of filteredRows) {
        const depth = Number(r.depth ?? r.tvdss ?? r.TVD ?? r.TVDSS ?? r.DEPTH ?? NaN);
        const vclay = Number(r.vclay ?? r.VCLAY ?? NaN);
        const phit = Number(r.phit ?? r.PHIT ?? NaN);
        const swt = Number(r.swt ?? r.SWT ?? NaN);
        const perm = Number(r.perm ?? r.PERM ?? r.permeability ?? NaN);
        let zones = r.zones ?? r.ZONES ?? r.zone ?? r.ZONE ?? null;
        if (zones == null || String(zones).trim() === "") {
          const anyZones = fullRows.some((rr) => {
            const z = rr.zones ?? rr.ZONES ?? rr.zone ?? rr.ZONE;
            return z != null && String(z).trim() !== "";
          });
          if (!anyZones) {
            zones = "ALL";
          } else {
            zones = "UNKNOWN";
          }
        } else {
          zones = String(zones);
        }
        if (isNaN(depth) || isNaN(vclay) || isNaN(phit) || isNaN(swt) || isNaN(perm)) {
          continue;
        }
        mappedRows.push({ depth, vclay, phit, swt, perm, zones });
      }
      return mappedRows;
    }
    async function generateReport() {
      error = null;
      if (!projectId || !wellName) {
        error = "Select a project and well before generating a report";
        return;
      }
      const dataRows = buildRessumPayload();
      const attempted = fullRows.length;
      const valid = dataRows.length;
      const skipped = attempted - valid;
      if (!dataRows.length) {
        error = "No valid well rows available to compute reservoir summary (missing required numeric fields)";
        return;
      }
      loading = true;
      try {
        const payload = { data: dataRows, cut_offs: {} };
        if (minPhit != null) payload.cut_offs.PHIT = Number(minPhit);
        if (maxSwt != null) payload.cut_offs.SWT = Number(maxSwt);
        if (maxVclay != null) payload.cut_offs.VSHALE = Number(maxVclay);
        const res = await fetch(`${API_BASE}/quick_pp/ressum`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(await res.text());
        const out = await res.json();
        ressumRows = Array.isArray(out) ? out : [];
        if (skipped > 0) {
          console.warn(`Skipped ${skipped} / ${attempted} rows because they lacked required numeric values (depth, vclay, phit, swt, perm).`);
          error = `Report generated. Note: skipped ${skipped} row(s) with missing numeric values.`;
        }
      } catch (e) {
        console.warn("Ressum error", e);
        error = String(e?.message ?? e);
        ressumRows = [];
      } finally {
        loading = false;
      }
    }
    filtered = ressumRows ?? [];
    if (projectId && wellName) loadWellData();
    $$renderer2.push(`<div class="ws-reservoir-summary"><div class="mb-2"><div class="font-semibold">Reservoir Summary</div> <div class="text-sm text-muted-foreground">High-level reservoir summary and exportable reports.</div></div> `);
    if (wellName) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="bg-panel rounded p-3"><div class="grid grid-cols-2 gap-3 mb-3"><div><label class="text-sm" for="minPhitInput">Min PHIT (cutoff)</label> <input id="minPhitInput" type="number" class="input w-full" placeholder="min phit"${attr("value", minPhit)}/></div> <div><label class="text-sm" for="maxSwtInput">Max SWT (cutoff)</label> <input id="maxSwtInput" type="number" class="input w-full" placeholder="max swt"${attr("value", maxSwt)}/></div> <div><label class="text-sm" for="maxVclayInput">Max VCLAY (cutoff)</label> <input id="maxVclayInput" type="number" class="input w-full" placeholder="max vclay"${attr("value", maxVclay)}/></div> <div class="flex items-end gap-2">`);
      Button($$renderer2, {
        class: "btn btn-primary",
        onclick: generateReport,
        disabled: loading,
        style: loading ? "opacity:0.6; pointer-events:none;" : "",
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Generate Report`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----></div></div> `);
      if (error) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="text-sm text-red-600 mb-2">Error: ${escape_html(error)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <div class="overflow-x-auto">`);
      if (filtered && filtered.length) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<table class="min-w-full table-auto border-collapse"><thead><tr class="bg-muted text-left"><!--[-->`);
        const each_array = ensure_array_like(Object.keys(filtered[0]));
        for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
          let col = each_array[$$index];
          $$renderer2.push(`<th class="px-2 py-1 text-xs font-medium"><div class="whitespace-nowrap font-medium">${escape_html(col)}</div> <div class="mt-1"><input class="dt-filter-input input w-full" type="text"${attr("placeholder", `Filter ${stringify(col)}`)}${attr("data-col", col)}/></div></th>`);
        }
        $$renderer2.push(`<!--]--></tr></thead><tbody><!--[-->`);
        const each_array_1 = ensure_array_like(filtered);
        for (let $$index_2 = 0, $$length = each_array_1.length; $$index_2 < $$length; $$index_2++) {
          let row = each_array_1[$$index_2];
          $$renderer2.push(`<tr class="border-t odd:bg-white even:bg-surface"><!--[-->`);
          const each_array_2 = ensure_array_like(Object.keys(filtered[0]));
          for (let $$index_1 = 0, $$length2 = each_array_2.length; $$index_1 < $$length2; $$index_1++) {
            let col = each_array_2[$$index_1];
            $$renderer2.push(`<td class="px-2 py-1 text-sm">${escape_html(row[col])}</td>`);
          }
          $$renderer2.push(`<!--]--></tr>`);
        }
        $$renderer2.push(`<!--]--></tbody></table>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="text-sm text-muted-foreground">No results. Click "Generate Report" to compute reservoir summary for the selected well.</div>`);
      }
      $$renderer2.push(`<!--]--></div></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="text-sm text-muted-foreground">Select a well to view reservoir summary.</div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    bind_props($$props, { projectId, wellName });
  });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let selectedProject = null;
    let selectedWell = null;
    const unsubscribe = workspace.subscribe((w) => {
      selectedProject = w?.project ?? null;
      selectedWell = w?.selectedWell ?? null;
    });
    onDestroy(() => unsubscribe());
    ProjectWorkspace($$renderer2, {
      selectedWell,
      project: selectedProject,
      $$slots: {
        left: ($$renderer3) => {
          $$renderer3.push(`<div slot="left">`);
          WsReservoirSummary($$renderer3, {
            projectId: selectedProject?.project_id ?? "",
            wellName: selectedWell?.name ?? ""
          });
          $$renderer3.push(`<!----></div>`);
        }
      }
    });
  });
}

export { _page as default };
//# sourceMappingURL=_page.svelte-Bw27nbzL.js.map
