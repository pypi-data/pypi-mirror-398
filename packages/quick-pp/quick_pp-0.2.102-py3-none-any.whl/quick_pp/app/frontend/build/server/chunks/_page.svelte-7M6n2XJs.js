import { s as store_get, u as unsubscribe_stores, o as onDestroy, aj as attr_style, i as stringify, a as attr, p as page, ak as fallback, m as attr_class, x as ensure_array_like, v as escape_html, c as bind_props } from './error.svelte-DOTZbGc-.js';
import './workspace-C36GNT6i.js';
import { B as Button } from './button-ChiBJf5X.js';

/* empty css                        */
function WsFormationTops($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let projectId = $$props["projectId"];
    let wellName = fallback($$props["wellName"], "");
    let showList = fallback($$props["showList"], true);
    function normalizeWellNames() {
      if (!wellName) return null;
      if (Array.isArray(wellName)) return wellName.map(String);
      return [String(wellName)];
    }
    function buildWellNameQs() {
      const names = normalizeWellNames();
      if (!names || names.length === 0) return "";
      return "?" + names.map((n) => `well_name=${encodeURIComponent(String(n))}`).join("&");
    }
    const API_BASE = "http://localhost:6312";
    let tops = [];
    let loading = false;
    let error = null;
    let newTop = { name: "", depth: null };
    async function loadTops() {
      if (!projectId) return;
      loading = true;
      error = null;
      try {
        const qs = buildWellNameQs();
        const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/formation_tops${qs}`);
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        tops = data.tops || [];
      } catch (err) {
        error = String(err?.message ?? err);
      } finally {
        loading = false;
      }
    }
    async function addTop() {
      {
        error = "Name and depth are required";
        return;
      }
    }
    async function deleteTop(name) {
      if (!confirm(`Delete top '${name}'?`)) return;
      loading = true;
      error = null;
      try {
        const qs = buildWellNameQs();
        const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/formation_tops/${encodeURIComponent(name)}${qs}`, { method: "DELETE" });
        if (!res.ok) throw new Error(await res.text());
        await loadTops();
      } catch (err) {
        error = String(err?.message ?? err);
      } finally {
        loading = false;
      }
    }
    if (projectId) {
      loadTops();
    }
    $$renderer2.push(`<div class="formation-tops">`);
    if (error) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-sm text-red-600">${escape_html(error)}</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="flex gap-2 border-b border-white/10 mb-4"><button${attr_class(`px-3 py-2 text-sm ${stringify("border-b-2 border-blue-500")}`)}>Manual Entry</button> <button${attr_class(`px-3 py-2 text-sm ${stringify("text-muted-foreground")}`)}>Bulk Import</button></div> `);
    if (loading) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-sm">Loading…</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="bg-surface rounded p-3 space-y-3 mb-4"><div class="font-medium text-sm">Add Formation Top Manually</div> <div class="flex items-center gap-2"><input placeholder="Well name"${attr("value", wellName)} class="input w-32"/> <input placeholder="Top name"${attr("value", newTop.name)} class="input w-32"/> <input placeholder="Depth" type="number"${attr("value", newTop.depth)} class="input w-24"/></div> `);
        Button($$renderer2, {
          variant: "default",
          onclick: addTop,
          children: ($$renderer3) => {
            $$renderer3.push(`<!---->Add Top`);
          },
          $$slots: { default: true }
        });
        $$renderer2.push(`<!----></div>`);
      }
      $$renderer2.push(`<!--]--> `);
      if (showList) {
        $$renderer2.push("<!--[-->");
        if (tops.length === 0) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="text-sm text-muted-foreground">No tops defined for this well.</div>`);
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push(`<ul class="space-y-1"><!--[-->`);
          const each_array = ensure_array_like(tops);
          for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
            let t = each_array[$$index];
            $$renderer2.push(`<li class="flex justify-between items-center p-2 bg-white/5 rounded"><div>${escape_html(t.well_name)}: ${escape_html(t.name)} — ${escape_html(t.depth)}</div> <div>`);
            Button($$renderer2, {
              variant: "outline",
              onclick: () => deleteTop(t.name),
              children: ($$renderer3) => {
                $$renderer3.push(`<!---->Delete`);
              },
              $$slots: { default: true }
            });
            $$renderer2.push(`<!----></div></li>`);
          }
          $$renderer2.push(`<!--]--></ul>`);
        }
        $$renderer2.push(`<!--]-->`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div>`);
    bind_props($$props, { projectId, wellName, showList });
  });
}
function WsFluidContacts($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let projectId = $$props["projectId"];
    let wellName = $$props["wellName"];
    let showList = fallback($$props["showList"], true);
    const API_BASE = "http://localhost:6312";
    let contacts = [];
    let loading = false;
    let error = null;
    let newContact = { name: "", depth: null };
    async function loadContacts() {
      if (!projectId) return;
      loading = true;
      error = null;
      try {
        const qs = wellName ? `?well_name=${encodeURIComponent(String(wellName))}` : "";
        const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/fluid_contacts${qs}`);
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        contacts = data.fluid_contacts || [];
      } catch (err) {
        error = String(err?.message ?? err);
      } finally {
        loading = false;
      }
    }
    async function addContact() {
      {
        error = "Name and depth required";
        return;
      }
    }
    if (projectId) loadContacts();
    $$renderer2.push(`<div class="fluid-contacts">`);
    if (error) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-sm text-red-600">${escape_html(error)}</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="flex gap-2 border-b border-white/10 mb-4"><button${attr_class(`px-3 py-2 text-sm ${stringify("border-b-2 border-blue-500")}`)}>Manual Entry</button> <button${attr_class(`px-3 py-2 text-sm ${stringify("text-muted-foreground")}`)}>Bulk Import</button></div> `);
    if (loading) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-sm">Loading…</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="bg-surface rounded p-3 space-y-3 mb-4"><div class="font-medium text-sm">Add Fluid Contact Manually</div> <div class="flex items-center gap-2"><input placeholder="Well name"${attr("value", wellName)} class="input w-32"/> <input placeholder="Contact name"${attr("value", newContact.name)} class="input w-32"/> <input placeholder="Depth" type="number"${attr("value", newContact.depth)} class="input w-24"/></div> `);
        Button($$renderer2, {
          variant: "default",
          onclick: addContact,
          children: ($$renderer3) => {
            $$renderer3.push(`<!---->Add`);
          },
          $$slots: { default: true }
        });
        $$renderer2.push(`<!----></div>`);
      }
      $$renderer2.push(`<!--]--> `);
      if (showList) {
        $$renderer2.push("<!--[-->");
        if (contacts.length === 0) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="text-sm text-muted">No fluid contacts</div>`);
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push(`<ul class="space-y-1"><!--[-->`);
          const each_array = ensure_array_like(contacts);
          for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
            let c = each_array[$$index];
            $$renderer2.push(`<li class="flex justify-between items-center p-2 bg-white/5 rounded"><div>${escape_html(c.well_name ?? wellName)}: ${escape_html(c.name)} — ${escape_html(c.depth)}</div></li>`);
          }
          $$renderer2.push(`<!--]--></ul>`);
        }
        $$renderer2.push(`<!--]-->`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div>`);
    bind_props($$props, { projectId, wellName, showList });
  });
}
function WsPressureTests($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let projectId = $$props["projectId"];
    let wellName = $$props["wellName"];
    let showList = fallback($$props["showList"], true);
    const API_BASE = "http://localhost:6312";
    let tests = [];
    let loading = false;
    let error = null;
    let newTest = { depth: null, pressure: null, pressure_uom: "psi" };
    async function loadTests() {
      if (!projectId) return;
      loading = true;
      error = null;
      try {
        const qs = wellName ? `?well_name=${encodeURIComponent(String(wellName))}` : "";
        const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/pressure_tests${qs}`);
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        tests = data.pressure_tests || [];
      } catch (err) {
        error = String(err?.message ?? err);
      } finally {
        loading = false;
      }
    }
    async function addTest() {
      {
        error = "Depth and pressure are required";
        return;
      }
    }
    if (projectId) loadTests();
    $$renderer2.push(`<div class="pressure-tests">`);
    if (error) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-sm text-red-600">${escape_html(error)}</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="flex gap-2 border-b border-white/10 mb-4"><button${attr_class(`px-3 py-2 text-sm ${stringify("border-b-2 border-blue-500")}`)}>Manual Entry</button> <button${attr_class(`px-3 py-2 text-sm ${stringify("text-muted-foreground")}`)}>Bulk Import</button></div> `);
    if (loading) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-sm">Loading…</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="bg-surface rounded p-3 space-y-3 mb-4"><div class="font-medium text-sm">Add Pressure Test Manually</div> <div class="flex items-center gap-2"><input placeholder="Well name"${attr("value", wellName)} class="input w-32"/> <input placeholder="Depth" type="number"${attr("value", newTest.depth)} class="input w-24"/> <input placeholder="Pressure" type="number"${attr("value", newTest.pressure)} class="input w-24"/> `);
        $$renderer2.select({ value: newTest.pressure_uom, class: "input w-24" }, ($$renderer3) => {
          $$renderer3.option({}, ($$renderer4) => {
            $$renderer4.push(`psi`);
          });
          $$renderer3.option({}, ($$renderer4) => {
            $$renderer4.push(`bar`);
          });
        });
        $$renderer2.push(`</div> `);
        Button($$renderer2, {
          variant: "default",
          onclick: addTest,
          children: ($$renderer3) => {
            $$renderer3.push(`<!---->Add`);
          },
          $$slots: { default: true }
        });
        $$renderer2.push(`<!----></div>`);
      }
      $$renderer2.push(`<!--]--> `);
      if (showList) {
        $$renderer2.push("<!--[-->");
        if (tests.length === 0) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="text-sm text-muted">No pressure tests</div>`);
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push(`<ul class="space-y-1"><!--[-->`);
          const each_array = ensure_array_like(tests);
          for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
            let t = each_array[$$index];
            $$renderer2.push(`<li class="flex justify-between items-center p-2 bg-white/5 rounded"><div>${escape_html(t.well_name)}: ${escape_html(t.depth)} — ${escape_html(t.pressure)} ${escape_html(t.pressure_uom)}</div></li>`);
          }
          $$renderer2.push(`<!--]--></ul>`);
        }
        $$renderer2.push(`<!--]-->`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div>`);
    bind_props($$props, { projectId, wellName, showList });
  });
}
function WsCoreSamples($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    const API_BASE = "http://localhost:6312";
    let projectId = $$props["projectId"];
    let wellName = $$props["wellName"];
    let showList = fallback($$props["showList"], true);
    let samples = [];
    let loading = false;
    let form = { sample_name: "", depth: "", description: "" };
    let measurements = [{ property_name: "", value: "", unit: "" }];
    let relperm = [{ saturation: "", kr: "", phase: "water" }];
    let pc = [
      { saturation: "", pressure: "", experiment_type: "", cycle: "" }
    ];
    async function fetchSamples() {
      loading = true;
      try {
        const qs = wellName ? `?well_name=${encodeURIComponent(String(wellName))}` : "";
        const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/core_samples${qs}`);
        if (res.ok) {
          const data = await res.json();
          samples = data.core_samples || [];
        } else {
          console.warn("Failed to load core samples", await res.text());
        }
      } catch (e) {
        console.warn("Error fetching core samples", e);
      } finally {
        loading = false;
      }
    }
    function addMeasurement() {
      measurements = [...measurements, { property_name: "", value: "", unit: "" }];
    }
    function removeMeasurement(i) {
      measurements = [...measurements.slice(0, i), ...measurements.slice(i + 1)];
    }
    function addRelperm() {
      relperm = [...relperm, { saturation: "", kr: "", phase: "" }];
    }
    function removeRelperm(i) {
      relperm = [...relperm.slice(0, i), ...relperm.slice(i + 1)];
    }
    function addPc() {
      pc = [
        ...pc,
        { saturation: "", pressure: "", experiment_type: "", cycle: "" }
      ];
    }
    function removePc(i) {
      pc = [...pc.slice(0, i), ...pc.slice(i + 1)];
    }
    async function submitSample() {
      {
        alert("Sample name is required");
        return;
      }
    }
    if (projectId) {
      fetchSamples();
    }
    $$renderer2.push(`<div class="ws-core-samples"><div class="flex gap-2 border-b border-white/10 mb-4"><button${attr_class(`px-3 py-2 text-sm ${stringify(
      // basic validation
      "border-b-2 border-blue-500"
    )}`)}>Manual Entry</button> <button${attr_class(`px-3 py-2 text-sm ${stringify("text-muted-foreground")}`)}>Bulk Import</button></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="bg-surface rounded p-3"><div class="font-semibold mb-2">Add / Update Sample</div> <div class="grid grid-cols-1 gap-2"><div class="flex items-center gap-2"><input placeholder="Well name"${attr("value", wellName)} class="input w-32"/> <input placeholder="Sample name"${attr("value", form.sample_name)} class="input w-32"/> <input placeholder="Depth"${attr("value", form.depth)} class="input w-32"/></div> <input placeholder="Description"${attr("value", form.description)} class="input"/> <div><div class="flex items-center justify-between"><span class="text-sm font-medium">Measurements (RCA)</span> `);
      Button($$renderer2, {
        class: "btn btn-sm",
        type: "button",
        onclick: addMeasurement,
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Add`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----></div> <div class="space-y-2 mt-2"><!--[-->`);
      const each_array = ensure_array_like(measurements);
      for (let i = 0, $$length = each_array.length; i < $$length; i++) {
        let m = each_array[i];
        $$renderer2.push(`<div class="grid grid-cols-12 gap-2 items-center"><input class="col-span-5 input" placeholder="Property"${attr("value", m.property_name)}/> <input class="col-span-3 input" placeholder="Value"${attr("value", m.value)}/> <input class="col-span-3 input" placeholder="Unit"${attr("value", m.unit)}/> `);
        Button($$renderer2, {
          variant: "secondary",
          type: "button",
          onclick: () => removeMeasurement(i),
          children: ($$renderer3) => {
            $$renderer3.push(`<!---->✕`);
          },
          $$slots: { default: true }
        });
        $$renderer2.push(`<!----></div>`);
      }
      $$renderer2.push(`<!--]--></div></div> <div><div class="flex items-center justify-between"><span class="text-sm font-medium">Relative Permeability (relperm)</span> `);
      Button($$renderer2, {
        class: "btn btn-sm",
        type: "button",
        onclick: addRelperm,
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Add`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----></div> <div class="space-y-2 mt-2"><!--[-->`);
      const each_array_1 = ensure_array_like(relperm);
      for (let i = 0, $$length = each_array_1.length; i < $$length; i++) {
        let r = each_array_1[i];
        $$renderer2.push(`<div class="grid grid-cols-12 gap-2 items-center"><input class="col-span-4 input" placeholder="Saturation"${attr("value", r.saturation)}/> <input class="col-span-4 input" placeholder="kr"${attr("value", r.kr)}/> <input class="col-span-3 input" placeholder="Phase"${attr("value", r.phase)}/> `);
        Button($$renderer2, {
          variant: "secondary",
          type: "button",
          onclick: () => removeRelperm(i),
          children: ($$renderer3) => {
            $$renderer3.push(`<!---->✕`);
          },
          $$slots: { default: true }
        });
        $$renderer2.push(`<!----></div>`);
      }
      $$renderer2.push(`<!--]--></div></div> <div><div class="flex items-center justify-between"><span class="text-sm font-medium">Capillary Pressure (pc)</span> `);
      Button($$renderer2, {
        class: "btn btn-sm",
        type: "button",
        onclick: addPc,
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Add`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----></div> <div class="space-y-2 mt-2"><!--[-->`);
      const each_array_2 = ensure_array_like(pc);
      for (let i = 0, $$length = each_array_2.length; i < $$length; i++) {
        let p = each_array_2[i];
        $$renderer2.push(`<div class="grid grid-cols-12 gap-2 items-center"><input class="col-span-3 input" placeholder="Saturation"${attr("value", p.saturation)}/> <input class="col-span-3 input" placeholder="Pressure"${attr("value", p.pressure)}/> `);
        $$renderer2.select({ class: "col-span-3 input", value: p.experiment_type }, ($$renderer3) => {
          $$renderer3.option({ value: "", disabled: true, hidden: true }, ($$renderer4) => {
            $$renderer4.push(`Experiment Type`);
          });
          $$renderer3.option({ value: "Porous plate" }, ($$renderer4) => {
            $$renderer4.push(`Porous plate`);
          });
          $$renderer3.option({ value: "Centrifuge" }, ($$renderer4) => {
            $$renderer4.push(`Centrifuge`);
          });
          $$renderer3.option({ value: "Mercury Injection" }, ($$renderer4) => {
            $$renderer4.push(`Mercury Injection`);
          });
        });
        $$renderer2.push(` `);
        $$renderer2.select({ class: "col-span-2 input", value: p.cycle }, ($$renderer3) => {
          $$renderer3.option({ value: "", disabled: true, hidden: true }, ($$renderer4) => {
            $$renderer4.push(`Cycle`);
          });
          $$renderer3.option({ value: "Drainage" }, ($$renderer4) => {
            $$renderer4.push(`Drainage`);
          });
          $$renderer3.option({ value: "Imbibition" }, ($$renderer4) => {
            $$renderer4.push(`Imbibition`);
          });
        });
        $$renderer2.push(` `);
        Button($$renderer2, {
          variant: "secondary",
          type: "button",
          onclick: () => removePc(i),
          children: ($$renderer3) => {
            $$renderer3.push(`<!---->✕`);
          },
          $$slots: { default: true }
        });
        $$renderer2.push(`<!----></div>`);
      }
      $$renderer2.push(`<!--]--></div></div> <div class="mt-2">`);
      Button($$renderer2, {
        class: "btn btn-primary",
        onclick: submitSample,
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Save Sample`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----></div></div></div>`);
    }
    $$renderer2.push(`<!--]--> `);
    if (showList) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="mt-4"><div class="text-sm font-medium mb-2">Samples (${escape_html(samples.length)})</div> `);
      if (loading) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div>Loading...</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<ul class="space-y-2"><!--[-->`);
        const each_array_3 = ensure_array_like(samples);
        for (let $$index_3 = 0, $$length = each_array_3.length; $$index_3 < $$length; $$index_3++) {
          let s = each_array_3[$$index_3];
          $$renderer2.push(`<li class="p-2 bg-surface rounded"><div class="font-medium">${escape_html(s.sample_name)}</div> <div class="text-sm">Depth: ${escape_html(s.depth)} ${escape_html(s.description ? `- ${s.description}` : "")}</div></li>`);
        }
        $$renderer2.push(`<!--]--></ul>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
    bind_props($$props, { projectId, wellName, showList });
  });
}
function WsDeviationSurvey($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let projectId = $$props["projectId"];
    let wellName = fallback($$props["wellName"], "");
    function buildWellNameQs() {
      if (!wellName) return "";
      const names = Array.isArray(wellName) ? wellName.map(String) : [String(wellName)];
      if (names.length === 0) return "";
      return "?" + names.map((n) => `well_name=${encodeURIComponent(String(n))}`).join("&");
    }
    const API_BASE = "http://localhost:6312";
    let surveys = [];
    let loading = false;
    let uploading = false;
    let error = null;
    let manualMd = "";
    let manualInc = "";
    let manualAzim = "";
    let manualError = null;
    let manualSelectedWell = null;
    async function loadSurveys() {
      if (!projectId) return;
      loading = true;
      error = null;
      try {
        const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/well_surveys`);
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        surveys = data.well_surveys || [];
      } catch (err) {
        error = String(err?.message ?? err);
      } finally {
        loading = false;
      }
    }
    async function deleteSurvey(md) {
      if (!confirm(`Delete survey point at MD ${md}?`)) return;
      loading = true;
      error = null;
      try {
        const qs = buildWellNameQs();
        const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/well_surveys/${md}${qs}`, { method: "DELETE" });
        if (!res.ok) throw new Error(await res.text());
        await loadSurveys();
      } catch (err) {
        error = String(err?.message ?? err);
      } finally {
        loading = false;
      }
    }
    async function addManualSurvey() {
      manualError = null;
      {
        manualError = "Please fill in all fields";
        return;
      }
    }
    async function calculateTvd() {
      if (!surveys.length) {
        error = "No survey points available to calculate TVD";
        return;
      }
      loading = true;
      error = null;
      try {
        const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/well_surveys/calculate_tvd`, { method: "POST" });
        if (!res.ok) throw new Error(await res.text());
        const result = await res.json();
        error = `TVD calculated for ${result.wells_processed} well(s): ${result.tvd_points_saved || 0} total points saved`;
        await loadSurveys();
      } catch (err) {
        error = String(err?.message ?? err);
      } finally {
        loading = false;
      }
    }
    if (projectId) {
      loadSurveys();
    }
    $$renderer2.push(`<div class="deviation-survey space-y-4">`);
    if (error) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div${attr_class(`text-sm ${stringify(error.includes("Successfully") || error.includes("added") ? "text-green-600" : "text-red-600")}`)}>${escape_html(error)}</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="flex gap-2 border-b border-white/10"><button${attr_class(`px-3 py-2 text-sm ${stringify("border-b-2 border-blue-500")}`)}>Manual Entry</button> <button${attr_class(`px-3 py-2 text-sm ${stringify("text-muted-foreground")}`)}>Bulk Import</button></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="bg-surface rounded p-3 space-y-3"><div class="font-medium text-sm">Add Survey Point Manually</div> `);
      if (manualError) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="text-sm text-red-600">${escape_html(manualError)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <div class="grid grid-cols-4 gap-3 items-end"><div><label for="manual-well" class="text-xs block mb-1">Well Name</label> <input id="manual-well" type="text"${attr("value", manualSelectedWell)}${attr("placeholder", String(wellName))}${attr("disabled", uploading, true)} class="input w-full text-sm"/></div> <div><label for="manual-md" class="text-xs block mb-1">Measured Depth (MD)</label> <input id="manual-md" type="number" step="0.1"${attr("value", manualMd)} placeholder="e.g. 1000.5"${attr("disabled", uploading, true)} class="input w-full text-sm"/></div> <div><label for="manual-inc" class="text-xs block mb-1">Inclination (degrees)</label> <input id="manual-inc" type="number" step="0.01"${attr("value", manualInc)} placeholder="e.g. 45.5"${attr("disabled", uploading, true)} class="input w-full text-sm"/></div> <div><label for="manual-azim" class="text-xs block mb-1">Azimuth (degrees)</label> <input id="manual-azim" type="number" step="0.01"${attr("value", manualAzim)} placeholder="e.g. 180"${attr("disabled", uploading, true)} class="input w-full text-sm"/></div></div> <div class="flex gap-2">`);
      Button($$renderer2, {
        variant: "default",
        size: "sm",
        onclick: addManualSurvey,
        disabled: uploading,
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->${escape_html("Add Point")}`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----></div></div>`);
    }
    $$renderer2.push(`<!--]--> <div class="space-y-2"><div class="flex justify-between items-center"><div class="text-sm font-medium">Survey Points (${escape_html(surveys.length)})</div> `);
    Button($$renderer2, {
      variant: "outline",
      size: "sm",
      onclick: calculateTvd,
      disabled: loading || surveys.length === 0,
      children: ($$renderer3) => {
        $$renderer3.push(`<!---->${escape_html(loading ? "Calculating..." : "Calculate TVD")}`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!----></div> `);
    if (loading && surveys.length === 0) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-sm text-muted-foreground">Loading...</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      if (surveys.length === 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="text-sm text-muted-foreground">No survey points loaded</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="bg-black/20 rounded p-2 max-h-60 overflow-y-auto text-xs"><table class="w-full"><thead><tr class="border-b border-white/10"><th class="px-2 py-1 text-left">MD</th><th class="px-2 py-1 text-left">Inc</th><th class="px-2 py-1 text-left">Azim</th><th class="px-2 py-1 text-left">Action</th></tr></thead><tbody><!--[-->`);
        const each_array = ensure_array_like(surveys);
        for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
          let s = each_array[$$index];
          $$renderer2.push(`<tr class="border-b border-white/10"><td class="px-2 py-1">${escape_html(s.md.toFixed(2))}</td><td class="px-2 py-1">${escape_html(s.inc.toFixed(2))}</td><td class="px-2 py-1">${escape_html(s.azim.toFixed(2))}</td><td class="px-2 py-1">`);
          Button($$renderer2, {
            variant: "outline",
            size: "sm",
            onclick: () => deleteSurvey(s.md),
            disabled: loading,
            children: ($$renderer3) => {
              $$renderer3.push(`<!---->Delete`);
            },
            $$slots: { default: true }
          });
          $$renderer2.push(`<!----></td></tr>`);
        }
        $$renderer2.push(`<!--]--></tbody></table></div>`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div></div>`);
    bind_props($$props, { projectId, wellName });
  });
}
function Ws_project($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let _unsubWorkspace = null;
    let depthUom = "m";
    const depthUomId = `depth-uom-${Math.random().toString(36).slice(2, 9)}`;
    let showTops = false;
    let showContacts = false;
    let showPressure = false;
    let showCore = false;
    let showDeviation = false;
    let showUpload = false;
    async function uploadLas() {
      return;
    }
    onDestroy(() => {
      try {
        _unsubWorkspace && _unsubWorkspace();
      } catch (e) {
      }
    });
    $$renderer2.push(`<div class="project-workspace p-4"><div class="grid grid-cols-1 md:grid-cols-3 gap-4"><div class="col-span-1"><div class="bg-panel rounded p-4 space-y-4"><div class="font-semibold">Data Inputs</div> <div class="text-sm text-muted-foreground">Add or edit data for wells.</div> <div class="accordion-item bg-surface rounded">`);
    Button($$renderer2, {
      variant: "ghost",
      class: "w-full flex justify-between items-center p-2",
      onclick: () => showUpload = !showUpload,
      "aria-expanded": showUpload,
      children: ($$renderer3) => {
        $$renderer3.push(`<div class="font-medium">Add wells from LAS</div> <div class="text-sm"><svg class="inline-block" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"${attr_style(`transform: rotate(${stringify(showUpload ? 90 : 0)}deg); transition: transform .18s ease;`)}><path d="M8 5l8 7-8 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></path></svg></div>`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!----> `);
    if (showUpload) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="p-3"><div class="mt-1"><div class="text-sm">Select one or more LAS files to add wells to this project.</div> <div class="mt-2"><label${attr("for", depthUomId)} class="text-sm text-muted-foreground">Depth units</label> `);
      $$renderer2.select(
        {
          id: depthUomId,
          value: depthUom,
          class: "rounded border bg-white/5 text-sm p-1 w-27"
        },
        ($$renderer3) => {
          $$renderer3.option({ value: "m" }, ($$renderer4) => {
            $$renderer4.push(`m (meters)`);
          });
          $$renderer3.option({ value: "ft" }, ($$renderer4) => {
            $$renderer4.push(`ft (feet)`);
          });
        }
      );
      $$renderer2.push(` <div class="flex items-center justify-between border rounded-md p-2 bg-white/5"><div class="text-sm text-muted-foreground">`);
      {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`No files chosen`);
      }
      $$renderer2.push(`<!--]--></div> <div class="flex items-center gap-2"><label class="inline-flex items-center px-3 py-1 rounded-md border cursor-pointer text-sm"><input type="file" accept=".las,.LAS" multiple class="hidden"/> Choose</label> `);
      Button($$renderer2, {
        variant: "default",
        onclick: uploadLas,
        disabled: true,
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->Upload`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!----></div></div> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div></div></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="accordion-item bg-surface rounded">`);
    Button($$renderer2, {
      variant: "ghost",
      class: "w-full flex justify-between items-center p-2",
      onclick: () => showTops = !showTops,
      "aria-expanded": showTops,
      children: ($$renderer3) => {
        $$renderer3.push(`<div class="font-medium">Formation Tops</div> <div class="text-sm"><svg class="inline-block" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"${attr_style(`transform: rotate(${stringify(showTops ? 90 : 0)}deg); transition: transform .18s ease;`)}><path d="M8 5l8 7-8 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></path></svg></div>`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!----> `);
    if (showTops) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="p-2">`);
      WsFormationTops($$renderer2, {
        projectId: "",
        wellName: "",
        showList: false
      });
      $$renderer2.push(`<!----></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="accordion-item bg-surface rounded">`);
    Button($$renderer2, {
      variant: "ghost",
      class: "w-full flex justify-between items-center p-2",
      onclick: () => showCore = !showCore,
      "aria-expanded": showCore,
      children: ($$renderer3) => {
        $$renderer3.push(`<div class="font-medium">Core Samples (RCA &amp; SCAL)</div> <div class="text-sm"><svg class="inline-block" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"${attr_style(`transform: rotate(${stringify(showCore ? 90 : 0)}deg); transition: transform .18s ease;`)}><path d="M8 5l8 7-8 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></path></svg></div>`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!----> `);
    if (showCore) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="p-2">`);
      WsCoreSamples($$renderer2, {
        projectId: "",
        wellName: "",
        showList: false
      });
      $$renderer2.push(`<!----></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="accordion-item bg-surface rounded">`);
    Button($$renderer2, {
      variant: "ghost",
      class: "w-full flex justify-between items-center p-2",
      onclick: () => showPressure = !showPressure,
      "aria-expanded": showPressure,
      children: ($$renderer3) => {
        $$renderer3.push(`<div class="font-medium">Pressure Tests</div> <div class="text-sm"><svg class="inline-block" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"${attr_style(`transform: rotate(${stringify(showPressure ? 90 : 0)}deg); transition: transform .18s ease;`)}><path d="M8 5l8 7-8 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></path></svg></div>`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!----> `);
    if (showPressure) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="p-2">`);
      WsPressureTests($$renderer2, {
        projectId: "",
        wellName: "",
        showList: false
      });
      $$renderer2.push(`<!----></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="accordion-item bg-surface rounded">`);
    Button($$renderer2, {
      variant: "ghost",
      class: "w-full flex justify-between items-center p-2",
      onclick: () => showContacts = !showContacts,
      "aria-expanded": showContacts,
      children: ($$renderer3) => {
        $$renderer3.push(`<div class="font-medium">Fluid Contacts</div> <div class="text-sm"><svg class="inline-block" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"${attr_style(`transform: rotate(${stringify(showContacts ? 90 : 0)}deg); transition: transform .18s ease;`)}><path d="M8 5l8 7-8 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></path></svg></div>`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!----> `);
    if (showContacts) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="p-2">`);
      WsFluidContacts($$renderer2, {
        projectId: "",
        wellName: "",
        showList: false
      });
      $$renderer2.push(`<!----></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="accordion-item bg-surface rounded">`);
    Button($$renderer2, {
      variant: "ghost",
      class: "w-full flex justify-between items-center p-2",
      onclick: () => showDeviation = !showDeviation,
      "aria-expanded": showDeviation,
      children: ($$renderer3) => {
        $$renderer3.push(`<div class="font-medium">Deviation Survey (TVD)</div> <div class="text-sm"><svg class="inline-block" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"${attr_style(`transform: rotate(${stringify(showDeviation ? 90 : 0)}deg); transition: transform .18s ease;`)}><path d="M8 5l8 7-8 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></path></svg></div>`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!----> `);
    if (showDeviation) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="p-2">`);
      WsDeviationSurvey($$renderer2, {
        projectId: "",
        wellName: ""
      });
      $$renderer2.push(`<!----></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div></div></div> <div class="col-span-2"><div class="bg-panel rounded p-4">`);
    {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="text-muted-foreground">Select a project from the sidebar to view details.</div>`);
    }
    $$renderer2.push(`<!--]--></div></div></div></div>`);
  });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    store_get($$store_subs ??= {}, "$page", page).params.project_id;
    $$renderer2.push(`<div>`);
    Ws_project($$renderer2);
    $$renderer2.push(`<!----></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}

export { _page as default };
//# sourceMappingURL=_page.svelte-7M6n2XJs.js.map
