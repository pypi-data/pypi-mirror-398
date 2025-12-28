import { o as onDestroy, a as attr, v as escape_html, c as bind_props } from './error.svelte-DOTZbGc-.js';
import { B as Button } from './button-ChiBJf5X.js';
import { w as workspace, c as applyDepthFilter, b as applyZoneFilter } from './workspace-C36GNT6i.js';
import { D as DepthFilterStatus } from './DepthFilterStatus-C1J1t2oq.js';
import { P as ProjectWorkspace } from './ProjectWorkspace-buzBVCPi.js';
import './WsWellPlot-CHO-dE21.js';

function WsSaturation($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let projectId = $$props["projectId"];
    let wellName = $$props["wellName"];
    const API_BASE = "http://localhost:6312";
    let depthFilter = { enabled: false, minDepth: null, maxDepth: null };
    let zoneFilter = { enabled: false, zones: [] };
    let visibleRows = [];
    let measSystem = "metric";
    let waterSalinity = 35e3;
    let mParam = 2;
    let loading = false;
    let error = null;
    let dataLoaded = false;
    let dataCache = /* @__PURE__ */ new Map();
    let fullRows = [];
    let tempGradResults = [];
    let rwResults = [];
    let archieResults = [];
    let waxmanResults = [];
    let archieChartData = [];
    let waxmanChartData = [];
    let saveLoadingSat = false;
    let saveMessageSat = null;
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
    function extractTVDSSRows() {
      const filteredRows = visibleRows;
      const rows = [];
      for (const r of filteredRows) {
        const tvd = r.tvdss ?? r.TVDSS ?? r.tvd ?? r.TVD ?? r.depth ?? r.DEPTH ?? NaN;
        const tvdNum = Number(tvd);
        if (!isNaN(tvdNum)) rows.push({ tvdss: tvdNum });
      }
      return rows;
    }
    async function estimateTempGradAndRw() {
      const tvdRows = extractTVDSSRows();
      if (!tvdRows.length) {
        error = "No TVD/DEPTH values found in well data";
        return;
      }
      loading = true;
      error = null;
      tempGradResults = [];
      rwResults = [];
      try {
        const tempPayload = { meas_system: measSystem, data: tvdRows };
        const tempRes = await fetch(`${API_BASE}/quick_pp/saturation/temp_grad`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(tempPayload)
        });
        if (!tempRes.ok) throw new Error(await tempRes.text());
        const tvals = await tempRes.json();
        const grads = Array.isArray(tvals) ? tvals.map((d) => Number(d.TEMP_GRAD ?? d.temp_grad ?? d.value ?? NaN)) : [];
        tempGradResults = grads;
        const rwPayload = {
          water_salinity: Number(waterSalinity),
          data: grads.map((g) => ({ temp_grad: g }))
        };
        const rwRes = await fetch(`${API_BASE}/quick_pp/saturation/rw`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(rwPayload)
        });
        if (!rwRes.ok) throw new Error(await rwRes.text());
        const rvals = await rwRes.json();
        rwResults = Array.isArray(rvals) ? rvals.map((d) => Number(d.RW ?? d.rw ?? NaN)) : [];
      } catch (e) {
        console.warn("TempGrad/Rw error", e);
        error = String(e?.message ?? e);
      } finally {
        loading = false;
      }
    }
    async function estimateWaterSaturation() {
      tempGradResults = [];
      rwResults = [];
      archieResults = [];
      waxmanResults = [];
      error = null;
      loading = true;
      try {
        await estimateTempGradAndRw();
        if (error) return;
        await estimateArchieSw();
        if (error) return;
        await estimateWaxmanSw();
      } catch (e) {
        console.warn("Estimate Water Saturation error", e);
        error = String(e?.message ?? e);
      } finally {
        loading = false;
      }
    }
    async function estimateArchieSw() {
      if (!rwResults || rwResults.length === 0) {
        error = "Please compute Rw first";
        return;
      }
      const filteredRows = visibleRows;
      const rows = [];
      const depths = [];
      let idx = 0;
      for (const r of filteredRows) {
        const depth = Number(r.depth ?? r.DEPTH ?? NaN);
        const rt = Number(r.rt ?? r.RT ?? r.Rt ?? r.res ?? r.RES ?? NaN);
        const phit = Number(r.phit ?? r.PHIT ?? r.Phit ?? NaN);
        if (isNaN(rt) || isNaN(phit)) continue;
        const rw = rwResults[idx++] ?? NaN;
        if (isNaN(rw)) continue;
        rows.push({ rt, rw, phit });
        depths.push(depth);
      }
      if (!rows.length) {
        error = "No RT/PHIT rows available for Archie";
        return;
      }
      loading = true;
      error = null;
      archieResults = [];
      try {
        const payload = { data: rows };
        const res = await fetch(`${API_BASE}/quick_pp/saturation/archie`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(await res.text());
        const out = await res.json();
        archieResults = Array.isArray(out) ? out.map((d) => Number(d.SWT ?? d.swt ?? NaN)) : [];
        archieChartData = archieResults.map((v, i) => ({ depth: depths[i], SWT: v })).filter((d) => !isNaN(Number(d.depth)));
      } catch (e) {
        console.warn("Archie error", e);
        error = String(e?.message ?? e);
      } finally {
        loading = false;
      }
    }
    async function estimateWaxmanSw() {
      if (!rwResults || rwResults.length === 0 || !tempGradResults || tempGradResults.length === 0) {
        error = "Please compute Temp Grad and Rw first";
        return;
      }
      const qvnRows = [];
      const shalePoroRows = [];
      const bRows = [];
      const finalRows = [];
      const filteredRows = visibleRows;
      for (const r of filteredRows) {
        const nphi = Number(r.nphi ?? r.NPHI ?? r.Nphi ?? NaN);
        const phit = Number(r.phit ?? r.PHIT ?? r.Phit ?? NaN);
        const vclay = Number(r.vclay ?? r.VCLAY ?? r.vcld ?? r.VCLD ?? NaN);
        if (!isNaN(nphi) && !isNaN(phit)) shalePoroRows.push({ nphi, phit });
        if (!isNaN(vclay) && !isNaN(phit)) qvnRows.push({ vclay, phit });
      }
      for (let i = 0; i < tempGradResults.length; i++) {
        const tg = tempGradResults[i];
        const rw = rwResults[i];
        if (!isNaN(Number(tg)) && !isNaN(Number(rw))) bRows.push({ temp_grad: tg, rw });
      }
      let shalePoroList = [];
      if (shalePoroRows.length) {
        try {
          const payload = { data: shalePoroRows };
          const res = await fetch(`${API_BASE}/quick_pp/porosity/shale_porosity`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
          if (!res.ok) throw new Error(await res.text());
          const out = await res.json();
          shalePoroList = Array.isArray(out) ? out.map((d) => Number(d.PHIT_SH ?? d.phit_sh ?? NaN)) : [];
        } catch (e) {
          console.warn("Shale porosity error", e);
        }
      }
      let qvnList = [];
      if (qvnRows.length && shalePoroList.length) {
        try {
          const qvnPayloadData = qvnRows.map((row, i) => ({
            vclay: row.vclay,
            phit: row.phit,
            phit_clay: shalePoroList[i]
          }));
          const payload = { data: qvnPayloadData };
          const res = await fetch(`${API_BASE}/quick_pp/saturation/estimate_qvn`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
          if (!res.ok) throw new Error(await res.text());
          const out = await res.json();
          qvnList = Array.isArray(out) ? out.map((d) => Number(d.QVN ?? d.qvn ?? NaN)) : [];
        } catch (e) {
          console.warn("Qvn error", e);
        }
      }
      let bList = [];
      if (bRows.length) {
        try {
          const payload = { data: bRows };
          const res = await fetch(`${API_BASE}/quick_pp/saturation/b_waxman_smits`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
          if (!res.ok) throw new Error(await res.text());
          const out = await res.json();
          bList = Array.isArray(out) ? out.map((d) => Number(d.B ?? d.b ?? NaN)) : [];
        } catch (e) {
          console.warn("B estimation error", e);
        }
      }
      let qi = 0;
      let bi = 0;
      let ri = 0;
      const depthsFinal = [];
      for (const r of filteredRows) {
        const depth = Number(r.depth ?? r.DEPTH ?? NaN);
        const rt = Number(r.rt ?? r.RT ?? r.res ?? r.RES ?? NaN);
        const phit = Number(r.phit ?? r.PHIT ?? r.Phit ?? NaN);
        if (isNaN(rt) || isNaN(phit)) continue;
        const rw = rwResults[ri++] ?? NaN;
        const qv = qvnList[qi++] ?? NaN;
        const b = bList[bi++] ?? NaN;
        if (isNaN(rw) || isNaN(qv) || isNaN(b)) continue;
        finalRows.push({ rt, rw, phit, qv, b, m: Number(mParam) });
        depthsFinal.push(depth);
      }
      if (!finalRows.length) {
        error = "Insufficient data to run Waxman-Smits (need rt, phit, rw, qvn, b)";
        return;
      }
      loading = true;
      error = null;
      waxmanResults = [];
      try {
        const payload = { data: finalRows };
        const res = await fetch(`${API_BASE}/quick_pp/saturation/waxman_smits`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(await res.text());
        const out = await res.json();
        waxmanResults = Array.isArray(out) ? out.map((d) => Number(d.SWT ?? d.swt ?? NaN)) : [];
        waxmanChartData = waxmanResults.map((v, i) => ({ depth: depthsFinal[i], SWT: v })).filter((d) => !isNaN(Number(d.depth)));
      } catch (e) {
        console.warn("Waxman-Smits error", e);
        error = String(e?.message ?? e);
      } finally {
        loading = false;
      }
    }
    async function saveSaturationResults() {
      if (!projectId || !wellName) {
        error = "Project and well must be selected before saving";
        return;
      }
      const archMap = /* @__PURE__ */ new Map();
      for (const a of archieChartData) {
        const d = Number(a.depth);
        if (!isNaN(d)) archMap.set(d, Number(a.SWT));
      }
      const waxMap = /* @__PURE__ */ new Map();
      for (const w of waxmanChartData) {
        const d = Number(w.depth);
        if (!isNaN(d)) waxMap.set(d, Number(w.SWT));
      }
      const depths = Array.from(/* @__PURE__ */ new Set([...archMap.keys(), ...waxMap.keys()])).sort((a, b) => a - b);
      if (!depths.length) {
        error = "No saturation results to save";
        return;
      }
      const rows = depths.map((d) => {
        const row = { DEPTH: d };
        if (archMap.has(d)) row.SWT_ARCHIE = archMap.get(d);
        if (waxMap.has(d)) row.SWT = waxMap.get(d);
        return row;
      });
      saveLoadingSat = true;
      saveMessageSat = null;
      error = null;
      try {
        const payload = { data: rows };
        const url = `${API_BASE}/quick_pp/database/projects/${projectId}/wells/${encodeURIComponent(String(wellName))}/data`;
        const res = await fetch(url, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(await res.text());
        const resp = await res.json().catch(() => null);
        saveMessageSat = resp && resp.message ? String(resp.message) : "Saturation results saved";
        try {
          window.dispatchEvent(new CustomEvent("qpp:data-updated", { detail: { projectId, wellName, kind: "saturation" } }));
        } catch (e) {
        }
      } catch (e) {
        console.warn("Save saturation error", e);
        saveMessageSat = null;
        error = String(e?.message ?? e);
      } finally {
        saveLoadingSat = false;
      }
    }
    function computeStats(arr) {
      const clean = arr.filter((v) => !isNaN(v));
      const count = clean.length;
      if (count === 0) return null;
      const sum = clean.reduce((a, b) => a + b, 0);
      const mean = sum / count;
      const min = Math.min(...clean);
      const max = Math.max(...clean);
      const sorted = clean.slice().sort((a, b) => a - b);
      const median = (sorted[Math.floor((count - 1) / 2)] + sorted[Math.ceil((count - 1) / 2)]) / 2;
      const variance = clean.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / count;
      const std = Math.sqrt(variance);
      return { count, mean, min, max, median, std };
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
    visibleRows = (() => {
      let rows = fullRows || [];
      rows = applyDepthFilter(rows, depthFilter);
      rows = applyZoneFilter(rows, zoneFilter);
      return rows;
    })();
    {
      const currentKey = `${projectId}_${wellName}`;
      if (projectId && wellName && currentKey !== previousWellKey) {
        previousWellKey = currentKey;
        if (!dataLoaded || !dataCache.has(currentKey)) {
          loadWellData();
        }
      }
    }
    $$renderer2.push(`<div class="ws-saturation"><div class="mb-2"><div class="font-semibold">Water Saturation</div> <div class="text-sm text-muted-foreground">Water saturation calculations and displays.</div></div> `);
    DepthFilterStatus($$renderer2);
    $$renderer2.push(`<!----> `);
    if (wellName) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="bg-panel rounded p-3"><div class="grid grid-cols-2 gap-2 mb-3"><div><label class="text-sm" for="meas-system">Measurement system</label> `);
      $$renderer2.select({ id: "meas-system", value: measSystem, class: "input" }, ($$renderer3) => {
        $$renderer3.option({ value: "metric" }, ($$renderer4) => {
          $$renderer4.push(`Metric`);
        });
        $$renderer3.option({ value: "imperial" }, ($$renderer4) => {
          $$renderer4.push(`Imperial`);
        });
      });
      $$renderer2.push(`</div> <div><label class="text-sm" for="water-salinity">Water salinity</label> <input id="water-salinity" type="number" class="input"${attr("value", waterSalinity)}/></div> <div><label class="text-sm" for="m-param">Archie/Waxman m parameter</label> <input id="m-param" type="number" class="input"${attr("value", mParam)}/></div></div> <div class="mb-3 flex gap-2 items-center">`);
      Button($$renderer2, {
        class: "btn btn-primary",
        onclick: estimateWaterSaturation,
        disabled: loading,
        style: loading ? "opacity:0.5; pointer-events:none;" : "",
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Estimate Water Saturation`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----> `);
      Button($$renderer2, {
        class: "btn ml-2 bg-emerald-700",
        onclick: saveSaturationResults,
        disabled: loading || saveLoadingSat,
        style: loading || saveLoadingSat ? "opacity:0.5; pointer-events:none;" : "",
        children: ($$renderer3) => {
          if (saveLoadingSat) {
            $$renderer3.push("<!--[-->");
            $$renderer3.push(`Saving...`);
          } else {
            $$renderer3.push("<!--[!-->");
            $$renderer3.push(`Save Saturation`);
          }
          $$renderer3.push(`<!--]-->`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----> `);
      if (saveMessageSat) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="text-xs text-green-600 ml-3">${escape_html(saveMessageSat)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div> `);
      if (error) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="text-sm text-red-500 mb-2">Error: ${escape_html(error)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <div class="space-y-3"><div><div class="font-medium text-sm mb-1">Temp Gradient</div> `);
      if (tempGradResults.length) {
        $$renderer2.push("<!--[-->");
        const s = computeStats(tempGradResults);
        if (s) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="text-sm">Avg: ${escape_html(s.mean.toFixed(2))} | Min: ${escape_html(s.min.toFixed(2))} | Max: ${escape_html(s.max.toFixed(2))} | Median: ${escape_html(s.median.toFixed(2))} | Std: ${escape_html(s.std.toFixed(2))} | Count: ${escape_html(s.count)}</div>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]-->`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="text-sm text-gray-500">No temp gradient computed</div>`);
      }
      $$renderer2.push(`<!--]--></div> <div><div class="font-medium text-sm mb-1">Estimated Rw</div> `);
      if (rwResults.length) {
        $$renderer2.push("<!--[-->");
        const s2 = computeStats(rwResults);
        if (s2) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="text-sm">Avg: ${escape_html(s2.mean.toFixed(3))} | Min: ${escape_html(s2.min.toFixed(3))} | Max: ${escape_html(s2.max.toFixed(3))} | Median: ${escape_html(s2.median.toFixed(3))} | Std: ${escape_html(s2.std.toFixed(3))} | Count: ${escape_html(s2.count)}</div>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]-->`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="text-sm text-gray-500">No Rw computed</div>`);
      }
      $$renderer2.push(`<!--]--></div> <div><div class="font-medium text-sm mb-1">Saturation Plot (Archie vs Waxman-Smits)</div> <div class="bg-surface rounded p-2"><div class="h-[220px] w-full overflow-hidden"><div class="w-full h-[220px]"></div></div></div> <div class="text-xs text-muted-foreground-foreground space-y-1 mt-3">`);
      if (archieResults.length > 0) {
        $$renderer2.push("<!--[-->");
        const aVals = archieResults;
        const avgA = aVals.reduce((a, b) => a + b, 0) / aVals.length;
        const minA = Math.min(...aVals);
        const maxA = Math.max(...aVals);
        $$renderer2.push(`<div><strong>Archie SWT:</strong> Avg: ${escape_html(avgA.toFixed(2))} | Min: ${escape_html(minA.toFixed(2))} | Max: ${escape_html(maxA.toFixed(2))} | Count: ${escape_html(aVals.length)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div><strong>Archie SWT:</strong> No data</div>`);
      }
      $$renderer2.push(`<!--]--> `);
      if (waxmanResults.length > 0) {
        $$renderer2.push("<!--[-->");
        const wVals = waxmanResults;
        const avgW = wVals.reduce((a, b) => a + b, 0) / wVals.length;
        const minW = Math.min(...wVals);
        const maxW = Math.max(...wVals);
        $$renderer2.push(`<div><strong>Waxman-Smits SWT:</strong> Avg: ${escape_html(avgW.toFixed(2))} | Min: ${escape_html(minW.toFixed(2))} | Max: ${escape_html(maxW.toFixed(2))} | Count: ${escape_html(wVals.length)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div><strong>Waxman-Smits SWT:</strong> No data</div>`);
      }
      $$renderer2.push(`<!--]--></div></div></div></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="text-sm">Select a well to view water saturation tools.</div>`);
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
          WsSaturation($$renderer3, {
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
//# sourceMappingURL=_page.svelte-ztoYhbXn.js.map
