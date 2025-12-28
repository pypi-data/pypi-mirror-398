import { o as onDestroy, s as store_get, u as unsubscribe_stores, c as bind_props, v as escape_html, x as ensure_array_like, a as attr, d as props_id, e as attributes, f as clsx, j as setContext, an as element } from './error.svelte-DOTZbGc-.js';
import { C as Card, a as Card_header, c as Card_title, d as Card_description, b as Card_content } from './card-title-Bf48KX6b.js';
import { B as Button, c as cn } from './button-ChiBJf5X.js';
import { w as workspace, c as applyDepthFilter, d as depthFilter, b as applyZoneFilter, z as zoneFilter, g as getStatsCache, e as setStatsCache, f as clearStatsCache } from './workspace-C36GNT6i.js';
import { D as DepthFilterStatus } from './DepthFilterStatus-C1J1t2oq.js';

const THEMES = { light: "", dark: ".dark" };
const chartContextKey = Symbol("chart-context");
function setChartContext(value) {
  return setContext(chartContextKey, value);
}
function Chart_style($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { id, config } = $$props;
    const colorConfig = config ? Object.entries(config).filter(([, config2]) => config2.theme || config2.color) : null;
    const themeContents = (() => {
      if (!colorConfig || !colorConfig.length) return;
      const themeContents2 = [];
      for (let [_theme, prefix] of Object.entries(THEMES)) {
        let content = `${prefix} [data-chart=${id}] {
`;
        const color = colorConfig.map(([key, itemConfig]) => {
          const theme = _theme;
          const color2 = itemConfig.theme?.[theme] || itemConfig.color;
          return color2 ? `	--color-${key}: ${color2};` : null;
        });
        content += color.join("\n") + "\n}";
        themeContents2.push(content);
      }
      return themeContents2.join("\n");
    })();
    if (themeContents) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<!---->`);
      {
        element($$renderer2, "style", void 0, () => {
          $$renderer2.push(`${escape_html(themeContents)}`);
        });
      }
      $$renderer2.push(`<!---->`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function Chart_container($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    const uid = props_id($$renderer2);
    let {
      ref = null,
      id = uid,
      class: className,
      children,
      config,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    const chartId = `chart-${id || uid.replace(/:/g, "")}`;
    setChartContext({
      get config() {
        return config;
      }
    });
    $$renderer2.push(`<div${attributes({
      "data-chart": chartId,
      "data-slot": "chart",
      class: clsx(cn(
        "flex aspect-video justify-center overflow-visible text-xs",
        // Overrides
        //
        // Stroke around dots/marks when hovering
        "[&_.stroke-white]:stroke-transparent",
        // override the default stroke color of lines
        "[&_.lc-line]:stroke-border/50",
        // by default, layerchart shows a line intersecting the point when hovering, this hides that
        "[&_.lc-highlight-line]:stroke-0",
        // by default, when you hover a point on a stacked series chart, it will drop the opacity
        // of the other series, this overrides that
        "[&_.lc-area-path]:opacity-100 [&_.lc-highlight-line]:opacity-100 [&_.lc-highlight-point]:opacity-100 [&_.lc-spline-path]:opacity-100 [&_.lc-text-svg]:overflow-visible [&_.lc-text]:text-xs",
        // We don't want the little tick lines between the axis labels and the chart, so we remove
        // the stroke. The alternative is to manually disable `tickMarks` on the x/y axis of every
        // chart.
        "[&_.lc-axis-tick]:stroke-0",
        // We don't want to display the rule on the x/y axis, as there is already going to be
        // a grid line there and rule ends up overlapping the marks because it is rendered after
        // the marks
        "[&_.lc-rule-x-line:not(.lc-grid-x-rule)]:stroke-0 [&_.lc-rule-y-line:not(.lc-grid-y-rule)]:stroke-0",
        "[&_.lc-grid-x-radial-line]:stroke-border [&_.lc-grid-x-radial-circle]:stroke-border",
        "[&_.lc-grid-y-radial-line]:stroke-border [&_.lc-grid-y-radial-circle]:stroke-border",
        // Legend adjustments
        "[&_.lc-legend-swatch-button]:items-center [&_.lc-legend-swatch-button]:gap-1.5",
        "[&_.lc-legend-swatch-group]:items-center [&_.lc-legend-swatch-group]:gap-4",
        "[&_.lc-legend-swatch]:size-2.5 [&_.lc-legend-swatch]:rounded-[2px]",
        // Labels
        "[&_.lc-labels-text:not([fill])]:fill-foreground [&_text]:stroke-transparent",
        // Tick labels on th x/y axes
        "[&_.lc-axis-tick-label]:fill-muted-foreground [&_.lc-axis-tick-label]:font-normal",
        "[&_.lc-tooltip-rects-g]:fill-transparent",
        "[&_.lc-layout-svg-g]:fill-transparent",
        "[&_.lc-root-container]:w-full",
        className
      )),
      ...restProps
    })}>`);
    Chart_style($$renderer2, { id: chartId, config });
    $$renderer2.push(`<!----> `);
    children?.($$renderer2);
    $$renderer2.push(`<!----></div>`);
    bind_props($$props, { ref });
  });
}
function renameColumn(rows, oldName, newName) {
  if (!oldName || !newName || oldName === newName) return rows;
  return rows.map((r) => {
    const newRow = {};
    for (const k of Object.keys(r)) {
      if (k === oldName) newRow[newName] = r[k];
      else newRow[k] = r[k];
    }
    return newRow;
  });
}
function convertPercentToFraction(rows, col) {
  if (!col) return rows;
  return rows.map((r) => {
    const v = r[col];
    const num = typeof v === "number" ? v : v === null || v === void 0 || v === "" ? NaN : Number(String(v).replace("%", ""));
    if (isNaN(num)) return { ...r };
    const out = num > 1 ? num / 100 : num;
    return { ...r, [col]: out };
  });
}
function applyRenameInColumns(columns, oldName, newName) {
  if (!oldName || !newName || oldName === newName) return columns;
  return columns.map((c) => c === oldName ? newName : c);
}
function WsWellStats($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let paginatedRows, totalPages, chartPoints;
    let projectId = $$props["projectId"];
    let wellName = $$props["wellName"];
    const API_BASE = "http://localhost:6312";
    let loading = false;
    let error = null;
    let loadingFullData = false;
    let counts = {
      formation_tops: 0,
      fluid_contacts: 0,
      pressure_tests: 0,
      core_samples: 0
    };
    let samples = [];
    let propOptions = [];
    let selectedProp = null;
    let chartData = [];
    let showFullData = false;
    let fullRows = [];
    let originalFullRows = [];
    let fullColumns = [];
    let selectedLog = null;
    let formationTops = [];
    let fluidContacts = [];
    let pressureTestsFull = [];
    let coreSamplesFull = [];
    let dataProfile = {};
    let profileDebounceTimer = null;
    let visibleRows = [];
    let currentPage = 0;
    let rowsPerPage = 100;
    let showDataProfile = false;
    let fullDataLoaded = false;
    let showEditModal = false;
    let editColumn = null;
    let editNewName = "";
    let doConvertPercent = false;
    let previewRows = [];
    let undoStack = [];
    let editedColumns = /* @__PURE__ */ new Set();
    let renameMap = {};
    let hasUnsavedEdits = false;
    let editMessage = null;
    let lastChartParams = { log: "", rowsLength: 0, prop: "" };
    function profileData() {
      const profile = {};
      const sampleSize = Math.min(visibleRows.length, 1e4);
      const sampledRows = visibleRows.length > sampleSize ? visibleRows.filter((_, i) => i % Math.ceil(visibleRows.length / sampleSize) === 0).slice(0, sampleSize) : visibleRows;
      for (const col of fullColumns) {
        const values = sampledRows.map((row) => row[col]);
        const nonNullValues = values.filter((v) => v !== null && v !== void 0 && v !== "");
        const nullCount = values.length - nonNullValues.length;
        const firstNonNull = nonNullValues.find((v) => v !== null && v !== void 0);
        let dataType = typeof firstNonNull;
        if (dataType === "string" && !isNaN(Number(firstNonNull))) {
          dataType = "numeric (string)";
        }
        const uniqueValues = new Set(nonNullValues.slice(0, 1e3));
        const uniqueCount = uniqueValues.size;
        let stats = null;
        if (dataType === "number" || dataType === "numeric (string)") {
          const numericValues = nonNullValues.map((v) => Number(v)).filter((v) => !isNaN(v));
          if (numericValues.length > 0) {
            const sum = numericValues.reduce((a, b) => a + b, 0);
            const mean = sum / numericValues.length;
            const min = Math.min(...numericValues);
            const max = Math.max(...numericValues);
            stats = { min, max, mean, median: mean, count: numericValues.length };
          }
        }
        profile[col] = {
          dataType,
          totalCount: values.length,
          nonNullCount: nonNullValues.length,
          nullCount,
          missingPercent: (nullCount / values.length * 100).toFixed(2),
          uniqueCount,
          uniqueValues: uniqueCount <= 20 ? Array.from(uniqueValues).slice(0, 20) : null,
          stats,
          sampled: sampledRows.length < visibleRows.length
        };
      }
      dataProfile = profile;
    }
    async function fetchCounts(forceRefresh = false) {
      if (!projectId || !wellName) return;
      const cached = getStatsCache(projectId, wellName);
      if (!forceRefresh && cached) {
        const c = cached.data;
        counts = c.counts;
        samples = c.samples;
        propOptions = c.propOptions;
        selectedProp = c.selectedProp;
        fullRows = c.fullRows || [];
        originalFullRows = c.originalFullRows || [];
        fullColumns = c.fullColumns || [];
        selectedLog = c.selectedLog;
        formationTops = c.formationTops || [];
        fluidContacts = c.fluidContacts || [];
        pressureTestsFull = c.pressureTestsFull || [];
        coreSamplesFull = c.coreSamplesFull || [];
        fullDataLoaded = fullRows.length > 0;
        return;
      }
      loading = true;
      error = null;
      try {
        const urls = {
          formation_tops: `${API_BASE}/quick_pp/database/projects/${projectId}/formation_tops?well_name=${encodeURIComponent(String(wellName))}`,
          fluid_contacts: `${API_BASE}/quick_pp/database/projects/${projectId}/fluid_contacts?well_name=${encodeURIComponent(String(wellName))}`,
          pressure_tests: `${API_BASE}/quick_pp/database/projects/${projectId}/pressure_tests?well_name=${encodeURIComponent(String(wellName))}`,
          core_samples: `${API_BASE}/quick_pp/database/projects/${projectId}/core_samples?well_name=${encodeURIComponent(String(wellName))}`
        };
        const [topsRes, contactsRes, pressureRes, samplesRes] = await Promise.all([
          fetch(urls.formation_tops),
          fetch(urls.fluid_contacts),
          fetch(urls.pressure_tests),
          fetch(urls.core_samples)
        ]);
        if (topsRes.ok) {
          const d = await topsRes.json();
          counts.formation_tops = Array.isArray(d) ? d.length : d?.formation_tops?.length ?? 0;
        }
        if (contactsRes.ok) {
          const d = await contactsRes.json();
          counts.fluid_contacts = Array.isArray(d) ? d.length : d?.fluid_contacts?.length ?? 0;
        }
        if (pressureRes.ok) {
          const d = await pressureRes.json();
          counts.pressure_tests = Array.isArray(d) ? d.length : d?.pressure_tests?.length ?? 0;
        }
        if (samplesRes.ok) {
          const d = await samplesRes.json();
          samples = Array.isArray(d) ? d : d?.core_samples ?? [];
          counts.core_samples = samples.length;
          const props = /* @__PURE__ */ new Set();
          for (const s of samples) {
            if (s.measurements && Array.isArray(s.measurements)) {
              for (const m of s.measurements) {
                if (m.property_name) props.add(String(m.property_name));
              }
            }
          }
          propOptions = Array.from(props).sort();
          selectedProp = propOptions[0] ?? null;
        }
        setStatsCache(projectId, wellName, {
          counts,
          samples,
          propOptions,
          selectedProp,
          fullRows,
          originalFullRows,
          fullColumns,
          selectedLog,
          formationTops,
          fluidContacts,
          pressureTestsFull,
          coreSamplesFull
        });
      } catch (e) {
        console.warn("WsWellStats fetch error", e);
        error = String(e?.message ?? e);
      } finally {
        loading = false;
      }
    }
    function buildChartData(selectedLog2, visibleRows2, selectedProp2, samples2) {
      const getValue = (row, key) => {
        if (!row || !key) return NaN;
        if (key in row) return Number(row[key]);
        const lowerKey = key.toLowerCase();
        for (const k of Object.keys(row)) {
          if (k.toLowerCase() === lowerKey) return Number(row[k]);
        }
        return NaN;
      };
      const getDepth = (row) => {
        if (!row) return NaN;
        for (const key of ["depth", "DEPTH", "Depth", "depth_m", "DEPTH_M", "MD", "md"]) {
          if (key in row && row[key] !== null && row[key] !== void 0) {
            return Number(row[key]);
          }
        }
        return NaN;
      };
      if (visibleRows2 && visibleRows2.length && selectedLog2) {
        const rows = visibleRows2.map((r) => ({ depth: getDepth(r), value: getValue(r, selectedLog2) })).filter((r) => !isNaN(r.depth) && !isNaN(r.value) && isFinite(r.value));
        rows.sort((a, b) => a.depth - b.depth);
        console.debug("buildChartData:", {
          selectedLog: selectedLog2,
          visibleRowsCount: visibleRows2.length,
          validRowsCount: rows.length,
          sampleValues: rows.slice(0, 5).map((r) => r.value)
        });
        if (rows.length) {
          return rows;
        }
      }
      if (selectedProp2 && samples2 && samples2.length > 0) {
        const rows = [];
        for (const s of samples2) {
          const depth = Number(s.depth ?? NaN);
          if (isNaN(depth)) continue;
          const m = (s.measurements || []).find((x) => String(x.property_name) === String(selectedProp2));
          const val = m ? Number(m.value) : NaN;
          if (!isNaN(val) && isFinite(val)) rows.push({ depth, value: val });
        }
        rows.sort((a, b) => a.depth - b.depth);
        if (rows.length > 0) {
          return rows;
        }
      }
      console.warn("buildChartData: No valid data found for", { selectedLog: selectedLog2, selectedProp: selectedProp2 });
      return [];
    }
    async function saveEditsToServer() {
      if (!projectId || !wellName) {
        editMessage = "Missing project/well context";
        return;
      }
      if (!hasUnsavedEdits) {
        editMessage = "No changes to save";
        return;
      }
      editMessage = "Saving...";
      const getMeasuredDepth = (row) => {
        if (!row) return null;
        return row.depth ?? row.DEPTH ?? row.depth_m ?? row.DEPTH_M ?? row["Depth"] ?? row["depth_m"] ?? null;
      };
      try {
        const dataPayload = fullRows.map((r) => {
          const out = {};
          out["DEPTH"] = getMeasuredDepth(r);
          out["WELL_NAME"] = String(wellName);
          if (editColumn) {
            out[editColumn] = r[editColumn];
          }
          return out;
        });
        const payload = { data: dataPayload };
        const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/wells/${encodeURIComponent(String(wellName))}/data`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(await res.text());
        originalFullRows = fullRows.map((r) => ({ ...r }));
        editedColumns = /* @__PURE__ */ new Set();
        renameMap = {};
        hasUnsavedEdits = false;
        undoStack = [];
        editMessage = "Saved edits to server";
        invalidateCache();
      } catch (err) {
        editMessage = `Save failed: ${String(err?.message ?? err)}`;
      }
    }
    function openEditModal() {
      editColumn = fullColumns[0] ?? null;
      editNewName = "";
      doConvertPercent = false;
      previewRows = [];
      editMessage = null;
      showEditModal = true;
    }
    function closeEditModal() {
      showEditModal = false;
      previewRows = [];
      editMessage = null;
    }
    function previewEdits() {
      if (!editColumn) {
        editMessage = "Choose column to preview";
        return;
      }
      const getVal = (row, key) => {
        if (row == null) return void 0;
        if (key in row) return row[key];
        const up = String(key).toUpperCase();
        if (up in row) return row[up];
        const low = String(key).toLowerCase();
        if (low in row) return row[low];
        return void 0;
      };
      const rowsWithData = fullRows.filter((r) => {
        const v = getVal(r, editColumn);
        if (v === null || v === void 0 || v === "") return false;
        if (typeof v === "number" && isNaN(v)) return false;
        return true;
      }).slice(0, 12);
      previewRows = rowsWithData.map((r) => {
        const oldValue = getVal(r, editColumn);
        let newValue = oldValue;
        if (doConvertPercent) {
          const num = typeof oldValue === "number" ? oldValue : oldValue === null || oldValue === void 0 || oldValue === "" ? NaN : Number(String(oldValue).replace("%", ""));
          if (isNaN(num)) newValue = oldValue;
          else newValue = num > 1 ? num / 100 : num;
        }
        const depth = getVal(r, "depth") ?? getVal(r, "DEPTH") ?? getVal(r, "depth_m") ?? "";
        return { depth, oldValue, newValue };
      });
      if (previewRows.length === 0) {
        editMessage = "No data available in that column for preview";
      } else {
        editMessage = `Previewing first ${previewRows.length} rows with data`;
      }
    }
    function applyEditsInMemory() {
      if (!editColumn) {
        editMessage = "Choose column to apply";
        return;
      }
      undoStack.push({
        rows: fullRows.slice(0, 50).map((r) => ({ ...r })),
        columns: fullColumns.slice(),
        editedColumns: Array.from(editedColumns),
        renameMap: { ...renameMap }
      });
      const originalEditColumn = editColumn;
      if (editNewName && editNewName.trim()) {
        const newName = editNewName.trim();
        fullRows = renameColumn(fullRows, editColumn, newName);
        fullColumns = applyRenameInColumns(fullColumns, editColumn, newName);
        if (selectedLog === editColumn) selectedLog = newName;
        renameMap[originalEditColumn] = newName;
        editColumn = newName;
        editNewName = "";
      }
      if (doConvertPercent) {
        fullRows = convertPercentToFraction(fullRows, editColumn);
      }
      editedColumns.add(editColumn);
      hasUnsavedEdits = true;
      editMessage = "Applied edits in-memory";
      previewRows = [];
    }
    function undoLast() {
      const s = undoStack.pop();
      if (!s) {
        editMessage = "Nothing to undo";
        return;
      }
      if (s.rows.length === fullRows.length) {
        fullRows = s.rows.map((r) => ({ ...r }));
      } else {
        for (let i = 0; i < s.rows.length; i++) {
          fullRows[i] = { ...s.rows[i] };
        }
      }
      fullColumns = s.columns.slice();
      if (s.editedColumns) editedColumns = new Set(s.editedColumns);
      if (s.renameMap) renameMap = { ...s.renameMap };
      hasUnsavedEdits = true;
      editMessage = "Undid last action (partial restore)";
    }
    function invalidateCache() {
      clearStatsCache(projectId, wellName);
    }
    visibleRows = (() => {
      let rows = fullRows || [];
      rows = applyDepthFilter(rows, store_get($$store_subs ??= {}, "$depthFilter", depthFilter));
      rows = applyZoneFilter(rows, store_get($$store_subs ??= {}, "$zoneFilter", zoneFilter));
      return rows;
    })();
    {
      const newParams = {
        log: selectedLog || "",
        rowsLength: visibleRows.length,
        prop: selectedProp || ""
      };
      if (JSON.stringify(newParams) !== JSON.stringify(lastChartParams)) {
        chartData = buildChartData(selectedLog, visibleRows, selectedProp, samples);
        lastChartParams = newParams;
      }
    }
    if (visibleRows.length > 0 && fullColumns.length > 0 && showDataProfile) {
      if (profileDebounceTimer) clearTimeout(profileDebounceTimer);
      profileDebounceTimer = setTimeout(() => profileData(), 300);
    }
    paginatedRows = visibleRows.slice(currentPage * rowsPerPage, (currentPage + 1) * rowsPerPage);
    totalPages = Math.ceil(visibleRows.length / rowsPerPage);
    chartPoints = chartData.map((d) => ({ x: d.depth, y: d.value }));
    if (projectId && wellName) {
      fetchCounts();
    }
    Card($$renderer2, {
      children: ($$renderer3) => {
        Card_header($$renderer3, {
          children: ($$renderer4) => {
            Card_title($$renderer4, {
              children: ($$renderer5) => {
                $$renderer5.push(`<!---->Well Statistics`);
              },
              $$slots: { default: true }
            });
            $$renderer4.push(`<!----> `);
            Card_description($$renderer4, {
              children: ($$renderer5) => {
                $$renderer5.push(`<!---->Summary for the selected well`);
              },
              $$slots: { default: true }
            });
            $$renderer4.push(`<!----> <div class="ml-auto flex items-center gap-2">`);
            Button($$renderer4, {
              variant: "ghost",
              size: "sm",
              onclick: openEditModal,
              title: "Open edits modal",
              "aria-label": "Open edits modal",
              disabled: loading || !fullDataLoaded,
              style: loading || !fullDataLoaded ? "opacity:0.5; pointer-events:none;" : "",
              children: ($$renderer5) => {
                $$renderer5.push(`<!---->✏️ Edits`);
              },
              $$slots: { default: true }
            });
            $$renderer4.push(`<!----> `);
            Button($$renderer4, {
              variant: hasUnsavedEdits ? "default" : "ghost",
              size: "sm",
              onclick: saveEditsToServer,
              disabled: loading || !hasUnsavedEdits || !fullDataLoaded,
              title: "Save edits to server",
              "aria-label": "Save edits to server",
              style: loading || !hasUnsavedEdits || !fullDataLoaded ? "opacity:0.5; pointer-events:none;" : "",
              children: ($$renderer5) => {
                $$renderer5.push(`<!---->Save Edits `);
                if (hasUnsavedEdits) {
                  $$renderer5.push("<!--[-->");
                  $$renderer5.push(`<span class="unsaved-dot" aria-hidden="true" style="background:#ef4444; margin-left:.5rem;"></span>`);
                } else {
                  $$renderer5.push("<!--[!-->");
                }
                $$renderer5.push(`<!--]-->`);
              },
              $$slots: { default: true }
            });
            $$renderer4.push(`<!----></div>`);
          },
          $$slots: { default: true }
        });
        $$renderer3.push(`<!----> `);
        Card_content($$renderer3, {
          class: "p-3",
          children: ($$renderer4) => {
            DepthFilterStatus($$renderer4);
            $$renderer4.push(`<!----> `);
            if (loading) {
              $$renderer4.push("<!--[-->");
              $$renderer4.push(`<div class="text-sm">Loading…</div>`);
            } else {
              $$renderer4.push("<!--[!-->");
              if (error) {
                $$renderer4.push("<!--[-->");
                $$renderer4.push(`<div class="text-sm text-red-500">Error: ${escape_html(error)}</div>`);
              } else {
                $$renderer4.push("<!--[!-->");
              }
              $$renderer4.push(`<!--]--> <div class="grid grid-cols-2 gap-2"><div class="p-3 bg-surface rounded"><div class="text-sm text-muted-foreground">Formation Tops</div> <div class="font-semibold">${escape_html(counts.formation_tops)}</div></div> <div class="p-3 bg-surface rounded"><div class="text-sm text-muted-foreground">Fluid Contacts</div> <div class="font-semibold">${escape_html(counts.fluid_contacts)}</div></div> <div class="p-3 bg-surface rounded"><div class="text-sm text-muted-foreground">Pressure Tests</div> <div class="font-semibold">${escape_html(counts.pressure_tests)}</div></div> <div class="p-3 bg-surface rounded"><div class="text-sm text-muted-foreground">Core Samples</div> <div class="font-semibold">${escape_html(counts.core_samples)}</div></div></div> <div class="mt-4"><div class="flex items-center justify-between"><div class="font-medium">Property vs Depth Data</div> <div class="flex gap-2">`);
              Button($$renderer4, {
                variant: "ghost",
                size: "sm",
                onclick: () => {
                  showDataProfile = !showDataProfile;
                },
                title: showDataProfile ? "Hide Profile" : "Show Profile",
                "aria-label": showDataProfile ? "Hide Profile" : "Show Profile",
                disabled: loading,
                style: loading ? "opacity:0.5; pointer-events:none;" : "",
                children: ($$renderer5) => {
                  $$renderer5.push(`<!---->${escape_html(showDataProfile ? "Hide" : "Show")} Profile`);
                },
                $$slots: { default: true }
              });
              $$renderer4.push(`<!----> `);
              Button($$renderer4, {
                variant: "ghost",
                size: "sm",
                title: showFullData ? "Hide full well data" : "Show full well data",
                "aria-label": showFullData ? "Hide full well data" : "Show full well data",
                disabled: loading,
                style: loading ? "opacity:0.5; pointer-events:none;" : "",
                onclick: async () => {
                  showFullData = !showFullData;
                  if (showFullData && !fullDataLoaded) {
                    loadingFullData = true;
                    try {
                      const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/wells/${encodeURIComponent(String(wellName))}/data?include_ancillary=true`);
                      if (res.ok) {
                        const fd = await res.json();
                        console.log("Well data fetched on demand:", fd);
                        let dataArray = [];
                        if (Array.isArray(fd)) {
                          dataArray = fd;
                        } else if (fd && Array.isArray(fd.data)) {
                          dataArray = fd.data;
                          if (fd.formation_tops) formationTops = fd.formation_tops;
                          if (fd.fluid_contacts) fluidContacts = fd.fluid_contacts;
                          if (fd.pressure_tests) pressureTestsFull = fd.pressure_tests;
                          if (fd.core_samples) coreSamplesFull = fd.core_samples;
                        }
                        if (dataArray.length > 0) {
                          fullRows = dataArray;
                          fullDataLoaded = true;
                          originalFullRows = dataArray.slice();
                          fullColumns = Object.keys(dataArray[0] ?? {});
                          selectedLog = selectedLog ?? fullColumns.find((c) => c !== "depth") ?? null;
                          editedColumns = /* @__PURE__ */ new Set();
                          renameMap = {};
                          hasUnsavedEdits = false;
                          console.log(`Loaded ${fullRows.length} rows with ${fullColumns.length} columns`);
                        } else {
                          error = "No well data available";
                        }
                      } else {
                        error = `Failed to load well data: ${res.status}`;
                      }
                    } catch (e) {
                      console.error("Error loading well data:", e);
                      error = `Error: ${e.message}`;
                    } finally {
                      loadingFullData = false;
                    }
                  }
                },
                children: ($$renderer5) => {
                  $$renderer5.push(`<!---->${escape_html(showFullData ? "Hide" : "Show")}`);
                },
                $$slots: { default: true }
              });
              $$renderer4.push(`<!----></div></div> `);
              if (showFullData) {
                $$renderer4.push("<!--[-->");
                $$renderer4.push(`<div class="mt-2 space-y-2">`);
                if (showDataProfile && Object.keys(dataProfile).length > 0) {
                  $$renderer4.push("<!--[-->");
                  $$renderer4.push(`<div class="bg-surface rounded p-3 space-y-3"><div class="font-medium">Data Profile</div> <div class="grid grid-cols-2 gap-2 text-sm"><div class="p-2 bg-panel rounded"><div class="text-muted-foreground">Total Columns</div> <div class="font-semibold">${escape_html(fullColumns.length)}</div></div> <div class="p-2 bg-panel rounded"><div class="text-muted-foreground">Total Rows</div> <div class="font-semibold">${escape_html(fullRows.length)}</div></div></div> <div class="overflow-auto max-h-96"><table class="w-full text-xs"><thead class="sticky top-0 bg-surface"><tr class="border-b"><th class="p-2 text-left">Column</th><th class="p-2 text-left">Type</th><th class="p-2 text-right">Non-Null</th><th class="p-2 text-right">Missing</th><th class="p-2 text-right">Missing %</th><th class="p-2 text-right">Unique</th><th class="p-2 text-left">Stats / Values</th></tr></thead><tbody><!--[-->`);
                  const each_array = ensure_array_like(fullColumns);
                  for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
                    let col = each_array[$$index];
                    const prof = dataProfile[col];
                    if (prof) {
                      $$renderer4.push("<!--[-->");
                      $$renderer4.push(`<tr class="border-b hover:bg-panel/50"><td class="p-2 font-medium">${escape_html(col)}</td><td class="p-2 text-muted-foreground">${escape_html(prof.dataType)}</td><td class="p-2 text-right">${escape_html(prof.nonNullCount)}</td><td class="p-2 text-right">${escape_html(prof.nullCount)}</td><td class="p-2 text-right">${escape_html(prof.missingPercent)}%</td><td class="p-2 text-right">${escape_html(prof.uniqueCount)}</td><td class="p-2">`);
                      if (prof.stats) {
                        $$renderer4.push("<!--[-->");
                        $$renderer4.push(`<div class="text-xs"><span class="text-muted-foreground">min:</span> ${escape_html(prof.stats.min.toFixed(2))}, <span class="text-muted-foreground">max:</span> ${escape_html(prof.stats.max.toFixed(2))}, <span class="text-muted-foreground">mean:</span> ${escape_html(prof.stats.mean.toFixed(2))}</div>`);
                      } else {
                        $$renderer4.push("<!--[!-->");
                        if (prof.uniqueValues) {
                          $$renderer4.push("<!--[-->");
                          $$renderer4.push(`<div class="text-xs truncate max-w-xs"${attr("title", prof.uniqueValues.join(", "))}>${escape_html(prof.uniqueValues.slice(0, 5).join(", "))} `);
                          if (prof.uniqueValues.length > 5) {
                            $$renderer4.push("<!--[-->");
                            $$renderer4.push(`...`);
                          } else {
                            $$renderer4.push("<!--[!-->");
                          }
                          $$renderer4.push(`<!--]--></div>`);
                        } else {
                          $$renderer4.push("<!--[!-->");
                          $$renderer4.push(`<div class="text-xs text-muted-foreground">${escape_html(prof.uniqueCount)} unique values</div>`);
                        }
                        $$renderer4.push(`<!--]-->`);
                      }
                      $$renderer4.push(`<!--]--></td></tr>`);
                    } else {
                      $$renderer4.push("<!--[!-->");
                    }
                    $$renderer4.push(`<!--]-->`);
                  }
                  $$renderer4.push(`<!--]--></tbody></table></div></div>`);
                } else {
                  $$renderer4.push("<!--[!-->");
                }
                $$renderer4.push(`<!--]--> <div class="flex items-center gap-2"><div class="text-sm text-muted-foreground">Plot log:</div> `);
                $$renderer4.select({ class: "input", value: selectedLog }, ($$renderer5) => {
                  if (fullColumns.length) {
                    $$renderer5.push("<!--[-->");
                    $$renderer5.push(`<!--[-->`);
                    const each_array_1 = ensure_array_like(fullColumns);
                    for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
                      let c = each_array_1[$$index_1];
                      if (c !== "depth") {
                        $$renderer5.push("<!--[-->");
                        $$renderer5.option({ value: c }, ($$renderer6) => {
                          $$renderer6.push(`${escape_html(c)}`);
                        });
                      } else {
                        $$renderer5.push("<!--[!-->");
                      }
                      $$renderer5.push(`<!--]-->`);
                    }
                    $$renderer5.push(`<!--]-->`);
                  } else {
                    $$renderer5.push("<!--[!-->");
                  }
                  $$renderer5.push(`<!--]-->`);
                });
                $$renderer4.push(`</div> `);
                if (formationTops && formationTops.length) {
                  $$renderer4.push("<!--[-->");
                  $$renderer4.push(`<div class="mt-2"><div class="text-sm font-medium">Formation Tops</div> <ul class="text-sm"><!--[-->`);
                  const each_array_2 = ensure_array_like(formationTops);
                  for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
                    let t = each_array_2[$$index_2];
                    $$renderer4.push(`<li>${escape_html(t.name)} — ${escape_html(t.depth)}</li>`);
                  }
                  $$renderer4.push(`<!--]--></ul></div>`);
                } else {
                  $$renderer4.push("<!--[!-->");
                }
                $$renderer4.push(`<!--]--> `);
                if (fluidContacts && fluidContacts.length) {
                  $$renderer4.push("<!--[-->");
                  $$renderer4.push(`<div class="mt-2"><div class="text-sm font-medium">Fluid Contacts</div> <ul class="text-sm"><!--[-->`);
                  const each_array_3 = ensure_array_like(fluidContacts);
                  for (let $$index_3 = 0, $$length = each_array_3.length; $$index_3 < $$length; $$index_3++) {
                    let c = each_array_3[$$index_3];
                    $$renderer4.push(`<li>${escape_html(c.name)} — ${escape_html(c.depth)}</li>`);
                  }
                  $$renderer4.push(`<!--]--></ul></div>`);
                } else {
                  $$renderer4.push("<!--[!-->");
                }
                $$renderer4.push(`<!--]--> <div class="bg-surface rounded p-2">`);
                Chart_container($$renderer4, {
                  class: "h-[240px] w-full",
                  config: {},
                  children: ($$renderer5) => {
                    $$renderer5.push(`<div class="w-full h-[240px]"></div> `);
                    if (chartPoints.length === 0) {
                      $$renderer5.push("<!--[-->");
                      $$renderer5.push(`<div class="absolute inset-0 flex items-center justify-center text-sm text-muted-foreground">No data available for ${escape_html(selectedLog ?? "selected log")}</div>`);
                    } else {
                      $$renderer5.push("<!--[!-->");
                    }
                    $$renderer5.push(`<!--]-->`);
                  },
                  $$slots: { default: true }
                });
                $$renderer4.push(`<!----></div> <div class="overflow-auto max-h-48 mt-2 bg-panel rounded p-2">`);
                if (loadingFullData) {
                  $$renderer4.push("<!--[-->");
                  $$renderer4.push(`<div class="text-center py-4 text-sm text-muted-foreground">Loading data...</div>`);
                } else {
                  $$renderer4.push("<!--[!-->");
                  $$renderer4.push(`<table class="w-full text-sm"><thead><tr><!--[-->`);
                  const each_array_4 = ensure_array_like(fullColumns);
                  for (let $$index_4 = 0, $$length = each_array_4.length; $$index_4 < $$length; $$index_4++) {
                    let c = each_array_4[$$index_4];
                    $$renderer4.push(`<th class="p-1 text-left">${escape_html(c)}</th>`);
                  }
                  $$renderer4.push(`<!--]--></tr></thead><tbody><!--[-->`);
                  const each_array_5 = ensure_array_like(paginatedRows);
                  for (let $$index_6 = 0, $$length = each_array_5.length; $$index_6 < $$length; $$index_6++) {
                    let row = each_array_5[$$index_6];
                    $$renderer4.push(`<tr><!--[-->`);
                    const each_array_6 = ensure_array_like(fullColumns);
                    for (let $$index_5 = 0, $$length2 = each_array_6.length; $$index_5 < $$length2; $$index_5++) {
                      let c = each_array_6[$$index_5];
                      $$renderer4.push(`<td class="p-1">${escape_html(String(row[c] ?? ""))}</td>`);
                    }
                    $$renderer4.push(`<!--]--></tr>`);
                  }
                  $$renderer4.push(`<!--]--></tbody></table> `);
                  if (visibleRows.length > rowsPerPage) {
                    $$renderer4.push("<!--[-->");
                    $$renderer4.push(`<div class="flex items-center justify-between mt-2 text-xs text-muted-foreground"><div>Showing ${escape_html(currentPage * rowsPerPage + 1)}-${escape_html(Math.min((currentPage + 1) * rowsPerPage, visibleRows.length))} of ${escape_html(visibleRows.length)} rows</div> <div class="flex gap-2">`);
                    Button($$renderer4, {
                      variant: "ghost",
                      size: "sm",
                      onclick: () => currentPage = Math.max(0, currentPage - 1),
                      disabled: currentPage === 0,
                      children: ($$renderer5) => {
                        $$renderer5.push(`<!---->Previous`);
                      },
                      $$slots: { default: true }
                    });
                    $$renderer4.push(`<!----> <span>Page ${escape_html(currentPage + 1)} of ${escape_html(totalPages)}</span> `);
                    Button($$renderer4, {
                      variant: "ghost",
                      size: "sm",
                      onclick: () => currentPage = Math.min(totalPages - 1, currentPage + 1),
                      disabled: currentPage >= totalPages - 1,
                      children: ($$renderer5) => {
                        $$renderer5.push(`<!---->Next`);
                      },
                      $$slots: { default: true }
                    });
                    $$renderer4.push(`<!----></div></div>`);
                  } else {
                    $$renderer4.push("<!--[!-->");
                  }
                  $$renderer4.push(`<!--]-->`);
                }
                $$renderer4.push(`<!--]--></div></div>`);
              } else {
                $$renderer4.push("<!--[!-->");
              }
              $$renderer4.push(`<!--]--></div>`);
            }
            $$renderer4.push(`<!--]-->`);
          },
          $$slots: { default: true }
        });
        $$renderer3.push(`<!---->`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!----> `);
    if (showEditModal) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="fixed inset-0 z-50 flex items-start justify-center p-6"><button type="button" class="absolute inset-0 bg-black/40" aria-label="Close modal"></button> <div class="relative bg-white dark:bg-surface rounded shadow-lg w-full max-w-md p-4 z-10"><div class="flex items-center justify-between mb-2"><div class="font-medium">Edit Columns</div> <div class="flex gap-2">`);
      Button($$renderer2, {
        variant: "ghost",
        size: "sm",
        onclick: undoLast,
        title: "Undo last",
        "aria-label": "Undo last",
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Undo`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----> `);
      Button($$renderer2, {
        variant: "ghost",
        size: "sm",
        onclick: closeEditModal,
        title: "Close modal",
        "aria-label": "Close modal",
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Close`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----></div></div> `);
      if (editMessage) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="text-sm text-muted-foreground-foreground mb-2">${escape_html(editMessage)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <div class="space-y-2"><div><label for="editColumn" class="text-xs text-muted-foreground">Column</label> `);
      $$renderer2.select({ id: "editColumn", class: "input w-full", value: editColumn }, ($$renderer3) => {
        if (fullColumns.length) {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<!--[-->`);
          const each_array_7 = ensure_array_like(fullColumns);
          for (let $$index_7 = 0, $$length = each_array_7.length; $$index_7 < $$length; $$index_7++) {
            let c = each_array_7[$$index_7];
            $$renderer3.option({ value: c }, ($$renderer4) => {
              $$renderer4.push(`${escape_html(c)}`);
            });
          }
          $$renderer3.push(`<!--]-->`);
        } else {
          $$renderer3.push("<!--[!-->");
          $$renderer3.option({ value: "" }, ($$renderer4) => {
            $$renderer4.push(`(no columns)`);
          });
        }
        $$renderer3.push(`<!--]-->`);
      });
      $$renderer2.push(`</div> <div><label for="editNewName" class="text-xs text-muted-foreground">Rename to (optional)</label> <input id="editNewName" class="input w-full"${attr("value", editNewName)} placeholder="e.g. NPHI"/></div> <div class="flex items-center gap-2"><input id="conv" type="checkbox"${attr("checked", doConvertPercent, true)}/> <label for="conv" class="text-sm">Convert % → fraction</label></div> <div class="flex gap-2">`);
      Button($$renderer2, {
        variant: "ghost",
        size: "sm",
        onclick: previewEdits,
        title: "Preview changes",
        disabled: loading,
        style: loading ? "opacity:0.5; pointer-events:none;" : "",
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Preview`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----> `);
      Button($$renderer2, {
        variant: "default",
        onclick: applyEditsInMemory,
        title: "Apply edits in-memory",
        disabled: loading,
        style: loading ? "opacity:0.5; pointer-events:none;" : "",
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Apply`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----> `);
      Button($$renderer2, {
        variant: "default",
        size: "sm",
        onclick: saveEditsToServer,
        disabled: loading || !hasUnsavedEdits,
        title: "Save edits to server",
        style: loading || !hasUnsavedEdits ? "opacity:0.5; pointer-events:none;" : "",
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Save`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----></div> `);
      if (previewRows.length) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="mt-2 bg-panel rounded p-2 max-h-40 overflow-auto"><div class="text-xs text-muted-foreground mb-1">Preview (first ${escape_html(previewRows.length)} rows)</div> <table class="w-full text-xs"><thead><tr><th class="p-1 text-left">Depth</th><th class="p-1 text-left">Old</th><th class="p-1 text-left">New</th></tr></thead><tbody><!--[-->`);
        const each_array_8 = ensure_array_like(previewRows);
        for (let $$index_8 = 0, $$length = each_array_8.length; $$index_8 < $$length; $$index_8++) {
          let pr = each_array_8[$$index_8];
          $$renderer2.push(`<tr><td class="p-1">${escape_html(String(pr.depth))}</td><td class="p-1">${escape_html(String(pr.oldValue))}</td><td class="p-1">${escape_html(String(pr.newValue))}</td></tr>`);
        }
        $$renderer2.push(`<!--]--></tbody></table></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div></div></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
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
    if (selectedProject) {
      $$renderer2.push("<!--[-->");
      if (selectedWell) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="bg-panel rounded p-4 min-h-[300px]">`);
        WsWellStats($$renderer2, {
          projectId: selectedProject?.project_id ?? "",
          wellName: selectedWell?.name ?? ""
        });
        $$renderer2.push(`<!----></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="bg-panel rounded p-4 min-h-[300px]"><div class="text-center py-12"><div class="font-semibold">No well selected</div> <div class="text-sm text-muted mt-2">Select a well to view its data.</div></div></div>`);
      }
      $$renderer2.push(`<!--]-->`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="bg-panel rounded p-6 text-center"><div class="font-semibold">No project selected</div> <div class="text-sm text-muted mt-2">Select a project in the Projects workspace to begin.</div> <div class="mt-4"><button class="btn btn-primary">Open Projects</button></div></div>`);
    }
    $$renderer2.push(`<!--]-->`);
  });
}

export { _page as default };
//# sourceMappingURL=_page.svelte-mkFh8uuk.js.map
