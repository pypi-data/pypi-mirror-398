import { o as onDestroy, a as attr, aj as attr_style, m as attr_class, i as stringify, v as escape_html, c as bind_props } from './error.svelte-DOTZbGc-.js';
import { w as workspace, c as applyDepthFilter, b as applyZoneFilter } from './workspace-C36GNT6i.js';
import { D as DepthFilterStatus } from './DepthFilterStatus-C1J1t2oq.js';
import { P as ProjectWorkspace } from './ProjectWorkspace-buzBVCPi.js';
import './WsWellPlot-CHO-dE21.js';

function WsLithoPoro($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let projectId = $$props["projectId"];
    let wellName = $$props["wellName"];
    const API_BASE = "http://localhost:6312";
    let depthFilter = { enabled: false, minDepth: null, maxDepth: null };
    let zoneFilter = { enabled: false, zones: [] };
    let loading = false;
    let error = null;
    let saveLoadingLitho = false;
    let saveLoadingPoro = false;
    let drySandNphi = -0.02;
    let drySandRhob = 2.65;
    let dryClayNphi = 0.35;
    let dryClayRhob = 2.71;
    let fluidNphi = 1;
    let fluidRhob = 1;
    let siltLineAngle = 117;
    let depthMatching = false;
    let hcCorrAngle = 50;
    let hcBuffer = 0.01;
    let useHCCorrected = false;
    let saveLoadingHC = false;
    let fullRows = [];
    let lithoChartData = [];
    let poroChartData = [];
    let cporeData = [];
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
    lithoChartData.map((d) => ({
      x: d.depth,
      vclay: d.VCLAY,
      vsilt: d.VCLAY + d.VSILT,
      vsand: d.VCLAY + d.VSILT + d.VSAND
    }));
    poroChartData.map((d) => ({ x: d.depth, y: d.PHIT }));
    poroChartData.map((d) => ({ x: d.depth, y: d.PHIE })).filter((p) => p.y !== void 0 && p.y !== null && !isNaN(Number(p.y)));
    cporeData.map((d) => ({ x: d.depth, y: d.CPORE }));
    (() => {
      let rows = fullRows || [];
      rows = applyDepthFilter(rows, depthFilter);
      rows = applyZoneFilter(rows, zoneFilter);
      return rows;
    })();
    {
      const currentKey = `${projectId}_${wellName}`;
      if (projectId && wellName && currentKey !== previousWellKey) {
        previousWellKey = currentKey;
        {
          loadWellData();
        }
      }
    }
    $$renderer2.push(`<div class="ws-lithology"><div class="mb-2"><div class="text-sm mb-2">Tools for lithology and porosity estimations.</div></div> `);
    DepthFilterStatus($$renderer2);
    $$renderer2.push(`<!----> `);
    if (wellName) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="bg-panel rounded p-3"><div class="grid grid-cols-2 gap-2 mb-3"><div><label class="text-xs" for="dry-sand-nphi">Dry sand (NPHI)</label> <input id="dry-sand-nphi" class="input" type="number" step="any"${attr("value", drySandNphi)}/></div> <div><label class="text-xs" for="dry-sand-rhob">Dry sand (RHOB)</label> <input id="dry-sand-rhob" class="input" type="number" step="any"${attr("value", drySandRhob)}/></div> <div><label class="text-xs" for="dry-clay-nphi">Dry clay (NPHI)</label> <input id="dry-clay-nphi" class="input" type="number" step="any"${attr("value", dryClayNphi)}/></div> <div><label class="text-xs" for="dry-clay-rhob">Dry clay (RHOB)</label> <input id="dry-clay-rhob" class="input" type="number" step="any"${attr("value", dryClayRhob)}/></div> <div><label class="text-xs" for="fluid-nphi">Fluid (NPHI)</label> <input id="fluid-nphi" class="input" type="number" step="any"${attr("value", fluidNphi)}/></div> <div><label class="text-xs" for="fluid-rhob">Fluid (RHOB)</label> <input id="fluid-rhob" class="input" type="number" step="any"${attr("value", fluidRhob)}/></div> <div><label class="text-xs" for="silt-line-angle">Silt line angle</label> <input id="silt-line-angle" class="input" type="number" step="1"${attr("value", siltLineAngle)}/></div></div> `);
      if (error) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="text-sm text-red-500 mb-2">Error: ${escape_html(error)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <div class="space-y-3"><div><div><div class="font-medium text-sm mb-1">NPHI - RHOB Crossplot</div> <div class="bg-surface rounded p-2"><div class="w-full max-w-[600px] h-[500px] mx-auto"></div></div></div> <div class="px-2 py-2 border-t border-border/50 mt-2"><div class="font-medium text-sm mb-3 mt-4">Hydrocarbon Correction</div> <div class="bg-surface rounded p-2"><div class="grid grid-cols-2 gap-2 mb-3"><div><label class="text-xs" for="hc-corr-angle">HC Correction Angle (°)</label> <input id="hc-corr-angle" class="input" type="number" step="0.1"${attr("value", hcCorrAngle)}/></div> <div><label class="text-xs" for="hc-buffer">HC Buffer</label> <input id="hc-buffer" class="input" type="number" step="0.001"${attr("value", hcBuffer)}/></div></div> <div class="flex gap-2 mb-3"><button class="btn px-3 py-1 text-sm font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500"${attr("disabled", loading, true)}${attr_style(loading ? "opacity:0.5; pointer-events:none;" : "")} aria-label="Apply HC correction" title="Apply hydrocarbon correction to NPHI/RHOB data">`);
      if (loading) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`Applying...`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`Apply HC Correction`);
      }
      $$renderer2.push(`<!--]--></button> <button class="btn px-3 py-1 text-sm font-medium rounded-md bg-emerald-700 text-white hover:bg-emerald-600 shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-emerald-600"${attr("disabled", loading || saveLoadingHC || true, true)}${attr_style(loading || saveLoadingHC || true ? "opacity:0.5; pointer-events:none;" : "")} aria-label="Save HC corrected data" title="Save corrected NPHI_HC and RHOB_HC to database">`);
      {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`Save HC Data`);
      }
      $$renderer2.push(`<!--]--></button></div> <div class="flex items-center"><input type="checkbox" id="use-hc-corrected" class="mr-2"${attr("checked", useHCCorrected, true)}${attr("disabled", loading || true, true)}/> <label for="use-hc-corrected"${attr_class(`text-sm cursor-pointer ${stringify(loading || true ? "opacity-50" : "")}`)}>Use HC corrected NPHI/RHOB for lithology and porosity estimation</label></div> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div></div> <div class="px-2 py-2 border-t border-border/50 mt-2"><div class="font-medium text-sm mb-1">Lithology (VSAND / VSILT / VCLAY)</div> <div class="bg-surface rounded p-2"><button class="btn px-3 py-1 text-sm font-semibold rounded-md bg-gray-900 text-white hover:bg-gray-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-700"${attr("disabled", loading, true)}${attr_style(loading ? "opacity:0.5; pointer-events:none;" : "")} aria-label="Run lithology classification" title="Run lithology classification">Estimate Lithology</button> <button class="btn px-3 py-1 text-sm font-medium rounded-md bg-emerald-700 text-white hover:bg-emerald-600 shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-emerald-600"${attr("disabled", loading || saveLoadingLitho, true)}${attr_style(loading || saveLoadingLitho ? "opacity:0.5; pointer-events:none;" : "")} aria-label="Save lithology" title="Save lithology results to database">`);
      {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`Save Lithology`);
      }
      $$renderer2.push(`<!--]--></button> <div class="h-[220px] w-full overflow-hidden">`);
      if (lithoChartData.length > 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="w-full h-[220px]"></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="flex items-center justify-center h-full text-sm text-gray-500">No lithology data available. Click "Estimate Lithology" first.</div>`);
      }
      $$renderer2.push(`<!--]--></div> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div></div> <div><div class="font-medium text-sm mb-1">Porosity (PHIT)</div> <div class="bg-surface rounded p-2"><button class="btn px-3 py-1 text-sm font-medium rounded-md bg-gray-800 text-gray-100 hover:bg-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-600"${attr("disabled", loading, true)}${attr_style(loading ? "opacity:0.5; pointer-events:none;" : "")} aria-label="Estimate porosity" title="Estimate porosity">Estimate Porosity</button> <button class="btn px-3 py-1 text-sm font-medium rounded-md bg-emerald-700 text-white hover:bg-emerald-600 shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-emerald-600"${attr("disabled", loading || saveLoadingPoro, true)}${attr_style(loading || saveLoadingPoro ? "opacity:0.5; pointer-events:none;" : "")} aria-label="Save porosity" title="Save porosity results to database">`);
      {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`Save Porosity`);
      }
      $$renderer2.push(`<!--]--></button> <div class="flex items-center ml-2"><input type="checkbox" id="depth-matching-poro" class="mr-2"${attr("checked", depthMatching, true)}${attr("disabled", loading, true)}/> <label for="depth-matching-poro"${attr_class(`text-sm cursor-pointer ${stringify(loading ? "opacity-50" : "")}`)}>Depth Matching</label></div> <div class="h-[220px] w-full overflow-hidden">`);
      if (poroChartData.length > 0 || cporeData.length > 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="w-full h-[220px]"></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="flex items-center justify-center h-full text-sm text-gray-500">No porosity data available. Click "Estimate Porosity" first.</div>`);
      }
      $$renderer2.push(`<!--]--></div> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div> <div class="text-xs text-muted-foreground space-y-1 mt-2">`);
      if (poroChartData.length > 0) {
        $$renderer2.push("<!--[-->");
        const phits = poroChartData.map((d) => d.PHIT);
        const avgPhit = phits.reduce((a, b) => a + b, 0) / phits.length;
        const minPhit = Math.min(...phits);
        const maxPhit = Math.max(...phits);
        $$renderer2.push(`<div><strong>Calculated PHIT:</strong> Avg: ${escape_html(avgPhit.toFixed(3))} | Min: ${escape_html(minPhit.toFixed(3))} | Max: ${escape_html(maxPhit.toFixed(3))} | Count: ${escape_html(phits.length)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div><strong>Calculated PHIT:</strong> No data</div>`);
      }
      $$renderer2.push(`<!--]--> `);
      if (cporeData.length > 0) {
        $$renderer2.push("<!--[-->");
        const cpores = cporeData.map((d) => d.CPORE);
        const avgCpore = cpores.reduce((a, b) => a + b, 0) / cpores.length;
        const minCpore = Math.min(...cpores);
        const maxCpore = Math.max(...cpores);
        $$renderer2.push(`<div><strong>Core Porosity (CPORE):</strong> <span class="inline-block w-2 h-2 bg-red-600 rounded-full"></span> Avg: ${escape_html(avgCpore.toFixed(3))} | Min: ${escape_html(minCpore.toFixed(3))} | Max: ${escape_html(maxCpore.toFixed(3))} | Count: ${escape_html(cpores.length)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="text-gray-500">No core porosity data (CPORE) found</div>`);
      }
      $$renderer2.push(`<!--]--></div></div></div></div></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="text-sm">Select a well.</div>`);
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
          WsLithoPoro($$renderer3, {
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
//# sourceMappingURL=_page.svelte-Byu8wLbH.js.map
