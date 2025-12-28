import { o as onDestroy, x as ensure_array_like, v as escape_html, a as attr, m as attr_class, i as stringify, c as bind_props } from './error.svelte-DOTZbGc-.js';
import { B as Button } from './button-ChiBJf5X.js';
import { w as workspace, c as applyDepthFilter, b as applyZoneFilter } from './workspace-C36GNT6i.js';
import { D as DepthFilterStatus } from './DepthFilterStatus-C1J1t2oq.js';
import { P as ProjectWorkspace } from './ProjectWorkspace-buzBVCPi.js';
import './WsWellPlot-CHO-dE21.js';

function WsPerm($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let projectId = $$props["projectId"];
    let wellName = $$props["wellName"];
    const API_BASE = "http://localhost:6312";
    let depthFilter = { enabled: false, minDepth: null, maxDepth: null };
    let zoneFilter = { enabled: false, zones: [] };
    let visibleRows = [];
    let loading = false;
    let error = null;
    let dataLoaded = false;
    let dataCache = /* @__PURE__ */ new Map();
    let saveLoadingPerm = false;
    let saveMessagePerm = null;
    let selectedMethod = "choo";
    let swirr = 0.05;
    let choo_A = 165e5;
    let choo_B = 6;
    let choo_C = 1.78;
    let depthMatching = false;
    let fullRows = [];
    let permResults = [];
    let permChartData = [];
    let cpermData = [];
    const permMethods = [
      {
        value: "choo",
        label: "Choo",
        requires: ["vclay", "vsilt", "phit"],
        params: ["m", "A", "B", "C"]
      },
      { value: "timur", label: "Timur", requires: ["phit", "swirr"] },
      {
        value: "tixier",
        label: "Tixier",
        requires: ["phit", "swirr"]
      },
      {
        value: "coates",
        label: "Coates",
        requires: ["phit", "swirr"]
      },
      {
        value: "kozeny_carman",
        label: "Kozeny-Carman",
        requires: ["phit", "swirr"]
      }
    ];
    async function loadWellData() {
      if (!projectId || !wellName) return;
      const cacheKey = `${projectId}_${wellName}`;
      if (dataCache.has(cacheKey)) {
        fullRows = dataCache.get(cacheKey);
        dataLoaded = true;
        return;
      }
      loading = true;
      error = null;
      try {
        const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/wells/${encodeURIComponent(String(wellName))}/merged`);
        if (!res.ok) throw new Error(await res.text());
        const fd = await res.json();
        const rows = fd && fd.data ? fd.data : fd;
        if (!Array.isArray(rows)) throw new Error("Unexpected data format from backend");
        fullRows = rows;
        dataCache.set(cacheKey, rows);
        dataLoaded = true;
      } catch (e) {
        console.warn("Failed to load well data", e);
        error = String(e?.message ?? e);
      } finally {
        loading = false;
      }
    }
    function extractPermData() {
      const method = permMethods.find((m) => m.value === selectedMethod);
      if (!method) return [];
      const filteredRows = visibleRows;
      const data = [];
      for (const r of filteredRows) {
        const row = {};
        let hasAllData = true;
        for (const field of method.requires) {
          let value;
          if (field === "swirr") {
            value = swirr;
          } else if (field === "vclay") {
            value = Number(r.vclay ?? r.VCLAY ?? r.Vclay ?? NaN);
          } else if (field === "vsilt") {
            value = Number(r.vsilt ?? r.VSILT ?? r.Vsilt ?? NaN);
          } else if (field === "phit") {
            value = Number(r.phit ?? r.PHIT ?? r.Phit ?? NaN);
          } else {
            value = Number(r[field] ?? r[field.toUpperCase()] ?? NaN);
          }
          if (isNaN(value)) {
            hasAllData = false;
            break;
          }
          row[field] = value;
        }
        if (hasAllData) {
          data.push(row);
        }
      }
      return data;
    }
    function extractCpermData() {
      const filteredRows = visibleRows;
      const data = [];
      for (const r of filteredRows) {
        const depth = Number(r.depth ?? r.DEPTH ?? NaN);
        const cperm = Number(r.cperm ?? r.CPERM ?? r.Cperm ?? r.KPERM ?? r.kperm ?? NaN);
        if (!isNaN(depth) && !isNaN(cperm) && cperm > 0) {
          data.push({ depth, CPERM: cperm });
        }
      }
      return data.sort((a, b) => a.depth - b.depth);
    }
    async function computePermeability() {
      const data = extractPermData();
      if (!data.length) {
        error = `No valid data available for ${selectedMethod} permeability calculation`;
        return;
      }
      loading = true;
      error = null;
      try {
        let body = { data };
        if (selectedMethod === "choo") {
          body = { ...body, A: choo_A, B: choo_B, C: choo_C };
        }
        const res = await fetch(`${API_BASE}/quick_pp/permeability/${selectedMethod}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        if (!res.ok) throw new Error(await res.text());
        permResults = await res.json();
        buildPermChart();
      } catch (e) {
        console.warn(`${selectedMethod} permeability error`, e);
        error = String(e?.message ?? e);
      } finally {
        loading = false;
      }
    }
    async function savePerm() {
      if (!projectId || !wellName) {
        error = "Project and well must be selected before saving";
        return;
      }
      if (!permChartData || permChartData.length === 0) {
        error = "No permeability results to save";
        return;
      }
      saveLoadingPerm = true;
      saveMessagePerm = null;
      error = null;
      try {
        const rows = permChartData.map((r) => {
          const row = { DEPTH: r.depth, PERM: Number(r.PERM) };
          return row;
        });
        if (!rows.length) throw new Error("No rows prepared for save");
        const payload = { data: rows };
        const url = `${API_BASE}/quick_pp/database/projects/${projectId}/wells/${encodeURIComponent(String(wellName))}/data`;
        const res = await fetch(url, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(await res.text());
        const resp = await res.json().catch(() => null);
        saveMessagePerm = resp && resp.message ? String(resp.message) : "Permeability saved";
        try {
          window.dispatchEvent(new CustomEvent("qpp:data-updated", { detail: { projectId, wellName, kind: "permeability" } }));
        } catch (e) {
        }
      } catch (e) {
        console.warn("Save permeability error", e);
        saveMessagePerm = null;
        error = String(e?.message ?? e);
      } finally {
        saveLoadingPerm = false;
      }
    }
    function buildPermChart() {
      const filteredRows = visibleRows;
      const rows = [];
      let i = 0;
      for (const r of filteredRows) {
        const depth = Number(r.depth ?? r.DEPTH ?? NaN);
        if (isNaN(depth)) continue;
        const method = permMethods.find((m) => m.value === selectedMethod);
        if (!method) continue;
        let hasValidData = true;
        for (const field of method.requires) {
          let value;
          if (field === "swirr") {
            value = swirr;
          } else if (field === "vclay") {
            value = Number(r.vclay ?? r.VCLAY ?? r.Vclay ?? NaN);
          } else if (field === "vsilt") {
            value = Number(r.vsilt ?? r.VSILT ?? r.Vsilt ?? NaN);
          } else if (field === "phit") {
            value = Number(r.phit ?? r.PHIT ?? r.Phit ?? NaN);
          } else {
            value = Number(r[field] ?? r[field.toUpperCase()] ?? NaN);
          }
          if (isNaN(value)) {
            hasValidData = false;
            break;
          }
        }
        if (hasValidData) {
          const p = permResults[i++] ?? { PERM: null };
          const perm = Math.max(Number(p.PERM ?? 1e-3), 1e-3);
          rows.push({ depth, PERM: perm });
        }
      }
      rows.sort((a, b) => a.depth - b.depth);
      permChartData = rows;
      cpermData = extractCpermData();
    }
    const unsubscribeWorkspace = workspace.subscribe((w) => {
      if (w?.depthFilter) {
        depthFilter = { ...w.depthFilter };
      }
      if (w?.zoneFilter) {
        zoneFilter = { ...w.zoneFilter };
      }
    });
    onDestroy(() => {
      unsubscribeWorkspace();
    });
    let previousWellKey = "";
    permChartData.map((d) => ({ x: d.depth, y: d.PERM }));
    cpermData.map((d) => ({ x: d.depth, y: d.CPERM }));
    visibleRows = (() => {
      let rows = fullRows || [];
      rows = applyDepthFilter(rows, depthFilter);
      rows = applyZoneFilter(rows, zoneFilter);
      return rows;
    })();
    if (permResults && visibleRows) {
      buildPermChart();
    }
    {
      const currentKey = `${projectId}_${wellName}`;
      if (projectId && wellName && currentKey !== previousWellKey) {
        previousWellKey = currentKey;
        if (!dataLoaded || !dataCache.has(currentKey)) {
          loadWellData();
        }
      }
    }
    $$renderer2.push(`<div class="ws-permeability"><div class="mb-2"><div class="font-semibold">Permeability</div> <div class="text-sm text-muted-foreground">Permeability estimation tools.</div></div> `);
    DepthFilterStatus($$renderer2);
    $$renderer2.push(`<!----> `);
    if (wellName) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="bg-panel rounded p-3"><div class="grid grid-cols-3 gap-2 mb-3"><div class="col-span-1 min-w-0"><label class="text-xs" for="perm-method">Permeability method</label> `);
      $$renderer2.select(
        {
          id: "perm-method",
          class: "input w-full",
          value: selectedMethod
        },
        ($$renderer3) => {
          $$renderer3.push(`<!--[-->`);
          const each_array = ensure_array_like(permMethods);
          for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
            let method = each_array[$$index];
            $$renderer3.option({ value: method.value }, ($$renderer4) => {
              $$renderer4.push(`${escape_html(method.label)}`);
            });
          }
          $$renderer3.push(`<!--]-->`);
        }
      );
      $$renderer2.push(`</div> <div class="col-span-2 min-w-0">`);
      {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="grid grid-cols-4 gap-2 w-full min-w-0"><div class="flex flex-col col-span-4" style="min-width: 120px; max-width: 180px;"><label class="text-xs" for="choo-A">Choo A</label> <input id="choo-A" class="input font-mono text-right" style="width:100%; min-width:120px; max-width:180px;" type="number" step="any"${attr("value", choo_A)}/></div></div> <div class="grid grid-cols-2 gap-2 w-full min-w-0 mt-2"><div class="min-w-0 flex flex-col"><label class="text-xs" for="choo-B">Choo B</label> <input id="choo-B" class="input w-full min-w-0 max-w-full" style="min-width:0;" type="number" step="any"${attr("value", choo_B)}/></div> <div class="min-w-0 flex flex-col"><label class="text-xs" for="choo-C">Choo C</label> <input id="choo-C" class="input w-full min-w-0 max-w-full" style="min-width:0;" type="number" step="any"${attr("value", choo_C)}/></div></div>`);
      }
      $$renderer2.push(`<!--]--></div></div> `);
      if (error) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="text-sm text-red-500 mb-2">Error: ${escape_html(error)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <div class="space-y-3"><div><div class="font-medium text-sm mb-1">Permeability</div> <div class="bg-surface rounded p-2">`);
      Button($$renderer2, {
        class: "btn btn-primary",
        onclick: computePermeability,
        disabled: loading,
        style: loading ? "opacity:0.5; pointer-events:none;" : "",
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Estimate Permeability`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----> `);
      Button($$renderer2, {
        class: "btn ml-2 bg-emerald-700",
        onclick: savePerm,
        disabled: loading || saveLoadingPerm,
        style: loading || saveLoadingPerm ? "opacity:0.5; pointer-events:none;" : "",
        children: ($$renderer3) => {
          if (saveLoadingPerm) {
            $$renderer3.push("<!--[-->");
            $$renderer3.push(`Saving...`);
          } else {
            $$renderer3.push("<!--[!-->");
            $$renderer3.push(`Save Permeability`);
          }
          $$renderer3.push(`<!--]-->`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----> <div class="flex items-center ml-2"><input type="checkbox" id="depth-matching" class="mr-2"${attr("checked", depthMatching, true)}${attr("disabled", loading, true)}/> <label for="depth-matching"${attr_class(`text-sm cursor-pointer ${stringify(loading ? "opacity-50" : "")}`)}>Depth Matching</label></div> <div class="h-[260px] w-full overflow-hidden">`);
      if (permChartData.length > 0 || cpermData.length > 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="w-full h-[260px]"></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="flex items-center justify-center h-full text-sm text-gray-500">No permeability data to display. Compute permeability to see the plot.</div>`);
      }
      $$renderer2.push(`<!--]--></div></div></div> <div class="text-xs text-muted-foreground space-y-1">`);
      if (permChartData.length > 0) {
        $$renderer2.push("<!--[-->");
        const perms = permChartData.map((d) => d.PERM);
        const avgPerm = perms.reduce((a, b) => a + b, 0) / perms.length;
        const minPerm = Math.min(...perms);
        const maxPerm = Math.max(...perms);
        $$renderer2.push(`<div><strong>Calculated Perm:</strong> Avg: ${escape_html(avgPerm.toFixed(2))} mD | Min: ${escape_html(minPerm.toFixed(3))} mD | Max: ${escape_html(maxPerm.toFixed(1))} mD | Count: ${escape_html(perms.length)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div><strong>Calculated Perm:</strong> No data</div>`);
      }
      $$renderer2.push(`<!--]--> `);
      if (cpermData.length > 0) {
        $$renderer2.push("<!--[-->");
        const cperms = cpermData.map((d) => d.CPERM);
        const avgCperm = cperms.reduce((a, b) => a + b, 0) / cperms.length;
        const minCperm = Math.min(...cperms);
        const maxCperm = Math.max(...cperms);
        $$renderer2.push(`<div><strong>Core Perm (CPERM):</strong> <span class="inline-block w-2 h-2 bg-red-600 rounded-full"></span> Avg: ${escape_html(avgCperm.toFixed(2))} mD | Min: ${escape_html(minCperm.toFixed(3))} mD | Max: ${escape_html(maxCperm.toFixed(1))} mD | Count: ${escape_html(cperms.length)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="text-gray-500">No core permeability data (CPERM) found</div>`);
      }
      $$renderer2.push(`<!--]--></div></div></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="text-sm">Select a well to view permeability tools.</div>`);
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
          WsPerm($$renderer3, {
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
//# sourceMappingURL=_page.svelte-BLmi_-Mn.js.map
