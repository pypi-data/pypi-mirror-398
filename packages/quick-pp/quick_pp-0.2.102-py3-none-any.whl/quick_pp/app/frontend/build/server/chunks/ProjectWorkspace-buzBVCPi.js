import { ak as fallback, b as slot, x as ensure_array_like, v as escape_html, c as bind_props } from './error.svelte-DOTZbGc-.js';
import WsWellPlot from './WsWellPlot-CHO-dE21.js';

function ProjectWorkspace($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let project = fallback($$props["project"], null);
    let selectedWell = fallback($$props["selectedWell"], null);
    if (project) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="grid grid-cols-1 md:grid-cols-2 gap-4"><div class="col-span-1"><div class="bg-panel rounded p-4"><!--[-->`);
      slot($$renderer2, $$props, "left", {});
      $$renderer2.push(`<!--]--></div></div> <div class="col-span-1">`);
      if (selectedWell) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="bg-panel rounded p-4 min-h-[300px]">`);
        WsWellPlot($$renderer2, {
          projectId: project?.project_id ?? "",
          wellName: selectedWell.name ?? ""
        });
        $$renderer2.push(`<!----></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="bg-panel rounded p-4 min-h-[300px] mx-auto flex items-center justify-center">`);
        if (project?.wells && project.wells.length > 0) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="text-center py-12"><div class="font-semibold">Select a Well</div> <div class="text-sm text-muted-foreground mt-2">Choose a well to view its logs and analysis.</div> <div class="mt-4">`);
          $$renderer2.select(
            {
              class: "form-select px-3 py-2 border border-border rounded-md bg-background text-foreground w-32",
              value: selectedWell
            },
            ($$renderer3) => {
              $$renderer3.option({ value: "", disabled: true, selected: true }, ($$renderer4) => {
                $$renderer4.push(`Select a well...`);
              });
              $$renderer3.push(`<!--[-->`);
              const each_array = ensure_array_like(project?.wells || []);
              for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
                let well = each_array[$$index];
                $$renderer3.option({ value: well }, ($$renderer4) => {
                  $$renderer4.push(`${escape_html(well.name || `Well ${well.id}`)}`);
                });
              }
              $$renderer3.push(`<!--]-->`);
            }
          );
          $$renderer2.push(`</div></div>`);
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push(`<div class="text-center py-12"><div class="font-semibold">No Wells Available</div> <div class="text-sm text-muted-foreground mt-2">This project has no wells to select.</div></div>`);
        }
        $$renderer2.push(`<!--]--></div>`);
      }
      $$renderer2.push(`<!--]--></div></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="bg-panel rounded p-6 text-center"><div class="font-semibold">No project selected</div> <div class="text-sm text-muted mt-2">Select a project in the Projects workspace to begin.</div> <div class="mt-4"><button class="btn btn-primary">Open Projects</button></div></div>`);
    }
    $$renderer2.push(`<!--]-->`);
    bind_props($$props, { project, selectedWell });
  });
}

export { ProjectWorkspace as P };
//# sourceMappingURL=ProjectWorkspace-buzBVCPi.js.map
