import { o as onDestroy, v as escape_html } from './error.svelte-DOTZbGc-.js';
import { w as workspace } from './workspace-C36GNT6i.js';

function DepthFilterStatus($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let hasFilter, filterText;
    let depthFilter = { enabled: false, minDepth: null, maxDepth: null };
    const unsubscribe = workspace.subscribe((w) => {
      if (w?.depthFilter) {
        depthFilter = { ...w.depthFilter };
      }
    });
    onDestroy(() => unsubscribe());
    function getFilterText() {
      if (!hasFilter) return "";
      const parts = [];
      if (depthFilter.minDepth !== null) {
        parts.push(`≥ ${depthFilter.minDepth}`);
      }
      if (depthFilter.maxDepth !== null) {
        parts.push(`≤ ${depthFilter.maxDepth}`);
      }
      return `Depth: ${parts.join(" & ")}`;
    }
    hasFilter = depthFilter.enabled && (depthFilter.minDepth !== null || depthFilter.maxDepth !== null);
    filterText = getFilterText();
    if (hasFilter) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="depth-filter-status bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-md px-3 py-2 mb-3 svelte-1r4q86p"><div class="flex items-center gap-2"><div class="w-2 h-2 bg-blue-500 rounded-full"></div> <span class="text-sm font-medium text-blue-800 dark:text-blue-200">Analysis filtered by ${escape_html(filterText)}</span></div></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}

export { DepthFilterStatus as D };
//# sourceMappingURL=DepthFilterStatus-C1J1t2oq.js.map
