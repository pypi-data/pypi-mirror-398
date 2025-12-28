import { c as bind_props, b as slot } from './error.svelte-DOTZbGc-.js';
import { S as Sidebar_provider, A as App_sidebar, a as Sidebar_inset, b as Site_header } from './site-header-BBQTPgmw.js';
import './button-ChiBJf5X.js';
import './workspace-C36GNT6i.js';

function _layout($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let data = $$props["data"];
    Sidebar_provider($$renderer2, {
      style: "--sidebar-width: calc(var(--spacing) * 72); --header-height: calc(var(--spacing) * 12);",
      children: ($$renderer3) => {
        App_sidebar($$renderer3, { variant: "inset" });
        $$renderer3.push(`<!----> `);
        Sidebar_inset($$renderer3, {
          children: ($$renderer4) => {
            Site_header($$renderer4);
            $$renderer4.push(`<!----> <div class="flex flex-1 flex-col"><div class="@container/main flex flex-1 flex-col gap-2"><div class="flex flex-col gap-4 py-4 md:gap-6 md:py-6"><!--[-->`);
            slot($$renderer4, $$props, "default", {});
            $$renderer4.push(`<!--]--></div></div></div>`);
          },
          $$slots: { default: true }
        });
        $$renderer3.push(`<!---->`);
      },
      $$slots: { default: true }
    });
    bind_props($$props, { data });
  });
}

export { _layout as default };
//# sourceMappingURL=_layout.svelte-BQ4eqa3m.js.map
