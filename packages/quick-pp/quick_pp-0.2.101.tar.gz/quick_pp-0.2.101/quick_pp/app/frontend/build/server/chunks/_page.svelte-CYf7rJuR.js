import { o as onDestroy } from './error.svelte-DOTZbGc-.js';
import './workspace-C36GNT6i.js';
import { S as Sidebar_provider, A as App_sidebar, a as Sidebar_inset, b as Site_header } from './site-header-BBQTPgmw.js';
import './button-ChiBJf5X.js';

function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let _unsubWorkspace = null;
    let _unsubProjects = null;
    onDestroy(() => {
      try {
        _unsubWorkspace && _unsubWorkspace();
      } catch (e) {
      }
      try {
        _unsubProjects && _unsubProjects();
      } catch (e) {
      }
    });
    Sidebar_provider($$renderer2, {
      style: "--sidebar-width: calc(var(--spacing) * 72); --header-height: calc(var(--spacing) * 12);",
      children: ($$renderer3) => {
        App_sidebar($$renderer3, { variant: "inset" });
        $$renderer3.push(`<!----> `);
        Sidebar_inset($$renderer3, {
          children: ($$renderer4) => {
            Site_header($$renderer4);
            $$renderer4.push(`<!----> `);
            {
              $$renderer4.push("<!--[!-->");
              $$renderer4.push(`<div class="p-6"><h2 class="text-lg font-semibold">Projects</h2> `);
              {
                $$renderer4.push("<!--[-->");
                $$renderer4.push(`<div class="mt-4 text-sm"><p>No projects found for your account or workspace.</p> <p class="mt-2">How to proceed:</p> <ul class="list-disc ml-6 mt-2 text-sm"><li>Use the <strong>New Project</strong> button in the left sidebar to create a project.</li> <li>If you already have projects, open the project selector in the sidebar and choose one to activate it.</li></ul> <p class="mt-3 text-muted-foreground">After creating or selecting a project the workspace will open automatically.</p></div>`);
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
  });
}

export { _page as default };
//# sourceMappingURL=_page.svelte-CYf7rJuR.js.map
