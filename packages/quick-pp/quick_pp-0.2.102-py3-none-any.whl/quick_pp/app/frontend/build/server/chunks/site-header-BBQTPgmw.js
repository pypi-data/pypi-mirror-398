import { T as Tooltip_provider, c as bind_props, j as setContext, k as derived, M as MediaQuery, e as attributes, f as clsx, i as stringify, g as spread_props, l as getContext, D as Dialog, a as attr, m as attr_class, P as Portal, n as Dialog_content, q as Dialog_close, r as Dialog_overlay, t as derived$1, s as store_get, v as escape_html, u as unsubscribe_stores, w as Panel_left, S as Separator$1, X, o as onDestroy, x as ensure_array_like, y as Menu, z as Map_search, A as List_details, W as Wall, B as Text_wrap_disabled, C as Wash_temperature_6, E as Table, F as Stack_back, G as Ease_in_out_control_points, H as Chart_scatter, I as Database, R as Report, J as File_word, K as Settings, N as Help, O as Search, Q as Tooltip, p as page, U as goto, V as Dialog_title, Y as Dialog_description, Z as mergeProps, _ as Circle_plus_filled, $ as Tooltip_trigger$1, a0 as Tooltip_content$1, a1 as Tooltip_arrow, a2 as Menu_trigger, a3 as Dropdown_menu_content$1, a4 as Dots, a5 as Dots_vertical, a6 as Menu_item, a7 as Menu_separator, a8 as Menu_group, a9 as Avatar$1, aa as Folder, ab as Share_3, ac as Trash, ad as User_circle, ae as Credit_card, af as Notification, ag as Logout, ah as Avatar_image$1, ai as Avatar_fallback$1 } from './error.svelte-DOTZbGc-.js';
import { t as tv, c as cn, B as Button } from './button-ChiBJf5X.js';
import { w as workspace, p as projects, s as selectProjectAndLoadWells, a as selectWell } from './workspace-C36GNT6i.js';

const DEFAULT_MOBILE_BREAKPOINT = 768;
class IsMobile extends MediaQuery {
  constructor(breakpoint = DEFAULT_MOBILE_BREAKPOINT) {
    super(`max-width: ${breakpoint - 1}px`);
  }
}
const SIDEBAR_COOKIE_NAME = "sidebar:state";
const SIDEBAR_COOKIE_MAX_AGE = 60 * 60 * 24 * 7;
const SIDEBAR_WIDTH = "16rem";
const SIDEBAR_WIDTH_MOBILE = "18rem";
const SIDEBAR_WIDTH_ICON = "3rem";
const SIDEBAR_KEYBOARD_SHORTCUT = "b";
class SidebarState {
  props;
  #open = derived(() => this.props.open());
  get open() {
    return this.#open();
  }
  set open($$value) {
    return this.#open($$value);
  }
  openMobile = false;
  setOpen;
  #isMobile;
  #state = derived(() => this.open ? "expanded" : "collapsed");
  get state() {
    return this.#state();
  }
  set state($$value) {
    return this.#state($$value);
  }
  constructor(props) {
    this.setOpen = props.setOpen;
    this.#isMobile = new IsMobile();
    this.props = props;
  }
  // Convenience getter for checking if the sidebar is mobile
  // without this, we would need to use `sidebar.isMobile.current` everywhere
  get isMobile() {
    return this.#isMobile.current;
  }
  // Event handler to apply to the `<svelte:window>`
  handleShortcutKeydown = (e) => {
    if (e.key === SIDEBAR_KEYBOARD_SHORTCUT && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      this.toggle();
    }
  };
  setOpenMobile = (value) => {
    this.openMobile = value;
  };
  toggle = () => {
    return this.#isMobile.current ? this.openMobile = !this.openMobile : this.setOpen(!this.open);
  };
}
const SYMBOL_KEY = "scn-sidebar";
function setSidebar(props) {
  return setContext(Symbol.for(SYMBOL_KEY), new SidebarState(props));
}
function useSidebar() {
  return getContext(Symbol.for(SYMBOL_KEY));
}
function Sidebar_content($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    $$renderer2.push(`<div${attributes({
      "data-slot": "sidebar-content",
      "data-sidebar": "content",
      class: clsx(cn("flex min-h-0 flex-1 flex-col gap-2 overflow-auto group-data-[collapsible=icon]:overflow-hidden", className)),
      ...restProps
    })}>`);
    children?.($$renderer2);
    $$renderer2.push(`<!----></div>`);
    bind_props($$props, { ref });
  });
}
function Sidebar_footer($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    $$renderer2.push(`<div${attributes({
      "data-slot": "sidebar-footer",
      "data-sidebar": "footer",
      class: clsx(cn("flex flex-col gap-2 p-2", className)),
      ...restProps
    })}>`);
    children?.($$renderer2);
    $$renderer2.push(`<!----></div>`);
    bind_props($$props, { ref });
  });
}
function Sidebar_group_content($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    $$renderer2.push(`<div${attributes({
      "data-slot": "sidebar-group-content",
      "data-sidebar": "group-content",
      class: clsx(cn("w-full text-sm", className)),
      ...restProps
    })}>`);
    children?.($$renderer2);
    $$renderer2.push(`<!----></div>`);
    bind_props($$props, { ref });
  });
}
function Sidebar_group_label($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      children,
      child,
      class: className,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    const mergedProps = {
      class: cn("text-sidebar-foreground/70 ring-sidebar-ring outline-hidden flex h-8 shrink-0 items-center rounded-md px-2 text-xs font-medium transition-[margin,opacity] duration-200 ease-linear focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0", "group-data-[collapsible=icon]:-mt-8 group-data-[collapsible=icon]:opacity-0", className),
      "data-slot": "sidebar-group-label",
      "data-sidebar": "group-label",
      ...restProps
    };
    if (child) {
      $$renderer2.push("<!--[-->");
      child($$renderer2, { props: mergedProps });
      $$renderer2.push(`<!---->`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div${attributes({ ...mergedProps })}>`);
      children?.($$renderer2);
      $$renderer2.push(`<!----></div>`);
    }
    $$renderer2.push(`<!--]-->`);
    bind_props($$props, { ref });
  });
}
function Sidebar_group($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    $$renderer2.push(`<div${attributes({
      "data-slot": "sidebar-group",
      "data-sidebar": "group",
      class: clsx(cn("relative flex w-full min-w-0 flex-col p-2", className)),
      ...restProps
    })}>`);
    children?.($$renderer2);
    $$renderer2.push(`<!----></div>`);
    bind_props($$props, { ref });
  });
}
function Sidebar_header($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    $$renderer2.push(`<div${attributes({
      "data-slot": "sidebar-header",
      "data-sidebar": "header",
      class: clsx(cn("flex flex-col gap-2 p-2", className)),
      ...restProps
    })}>`);
    children?.($$renderer2);
    $$renderer2.push(`<!----></div>`);
    bind_props($$props, { ref });
  });
}
function Sidebar_inset($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    $$renderer2.push(`<main${attributes({
      "data-slot": "sidebar-inset",
      class: clsx(cn("bg-background relative flex w-full flex-1 flex-col", "md:peer-data-[variant=inset]:m-2 md:peer-data-[variant=inset]:ms-0 md:peer-data-[variant=inset]:peer-data-[state=collapsed]:ms-2 md:peer-data-[variant=inset]:rounded-xl md:peer-data-[variant=inset]:shadow-sm", className)),
      ...restProps
    })}>`);
    children?.($$renderer2);
    $$renderer2.push(`<!----></main>`);
    bind_props($$props, { ref });
  });
}
function Sidebar_menu_action($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      showOnHover = false,
      children,
      child,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    const mergedProps = {
      class: cn(
        "text-sidebar-foreground ring-sidebar-ring hover:bg-sidebar-accent hover:text-sidebar-accent-foreground peer-hover/menu-button:text-sidebar-accent-foreground outline-hidden absolute end-1 top-1.5 flex aspect-square w-5 items-center justify-center rounded-md p-0 transition-transform focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0",
        // Increases the hit area of the button on mobile.
        "after:absolute after:-inset-2 md:after:hidden",
        "peer-data-[size=sm]/menu-button:top-1",
        "peer-data-[size=default]/menu-button:top-1.5",
        "peer-data-[size=lg]/menu-button:top-2.5",
        "group-data-[collapsible=icon]:hidden",
        showOnHover && "peer-data-[active=true]/menu-button:text-sidebar-accent-foreground group-focus-within/menu-item:opacity-100 group-hover/menu-item:opacity-100 data-[state=open]:opacity-100 md:opacity-0",
        className
      ),
      "data-slot": "sidebar-menu-action",
      "data-sidebar": "menu-action",
      ...restProps
    };
    if (child) {
      $$renderer2.push("<!--[-->");
      child($$renderer2, { props: mergedProps });
      $$renderer2.push(`<!---->`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<button${attributes({ ...mergedProps })}>`);
      children?.($$renderer2);
      $$renderer2.push(`<!----></button>`);
    }
    $$renderer2.push(`<!--]-->`);
    bind_props($$props, { ref });
  });
}
function Tooltip_trigger($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { ref = null, $$slots, $$events, ...restProps } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Tooltip_trigger$1($$renderer3, spread_props([
        { "data-slot": "tooltip-trigger" },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
function Tooltip_content($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      sideOffset = 0,
      side = "top",
      children,
      arrowClasses,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Portal($$renderer3, {
        children: ($$renderer4) => {
          $$renderer4.push(`<!---->`);
          Tooltip_content$1($$renderer4, spread_props([
            {
              "data-slot": "tooltip-content",
              sideOffset,
              side,
              class: cn("bg-primary text-primary-foreground animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-end-2 data-[side=right]:slide-in-from-start-2 data-[side=top]:slide-in-from-bottom-2 origin-(--bits-tooltip-content-transform-origin) z-50 w-fit text-balance rounded-md px-3 py-1.5 text-xs", className)
            },
            restProps,
            {
              get ref() {
                return ref;
              },
              set ref($$value) {
                ref = $$value;
                $$settled = false;
              },
              children: ($$renderer5) => {
                children?.($$renderer5);
                $$renderer5.push(`<!----> <!---->`);
                {
                  let child = function($$renderer6, { props }) {
                    $$renderer6.push(`<div${attributes({
                      class: clsx(cn("bg-primary z-50 size-2.5 rotate-45 rounded-[2px]", "data-[side=top]:translate-x-1/2 data-[side=top]:translate-y-[calc(-50%_+_2px)]", "data-[side=bottom]:-translate-x-1/2 data-[side=bottom]:-translate-y-[calc(-50%_+_1px)]", "data-[side=right]:translate-x-[calc(50%_+_2px)] data-[side=right]:translate-y-1/2", "data-[side=left]:-translate-y-[calc(50%_-_3px)]", arrowClasses)),
                      ...props
                    })}></div>`);
                  };
                  Tooltip_arrow($$renderer5, { child, $$slots: { child: true } });
                }
                $$renderer5.push(`<!---->`);
              },
              $$slots: { default: true }
            }
          ]));
          $$renderer4.push(`<!---->`);
        }
      });
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
const Root$2 = Tooltip;
const Provider = Tooltip_provider;
const sidebarMenuButtonVariants = tv({
  base: "peer/menu-button outline-hidden ring-sidebar-ring hover:bg-sidebar-accent hover:text-sidebar-accent-foreground active:bg-sidebar-accent active:text-sidebar-accent-foreground group-has-data-[sidebar=menu-action]/menu-item:pe-8 data-[active=true]:bg-sidebar-accent data-[active=true]:text-sidebar-accent-foreground data-[state=open]:hover:bg-sidebar-accent data-[state=open]:hover:text-sidebar-accent-foreground group-data-[collapsible=icon]:size-8! group-data-[collapsible=icon]:p-2! flex w-full items-center gap-2 overflow-hidden rounded-md p-2 text-start text-sm transition-[width,height,padding] focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50 data-[active=true]:font-medium [&>span:last-child]:truncate [&>svg]:size-4 [&>svg]:shrink-0",
  variants: {
    variant: {
      default: "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
      outline: "bg-background hover:bg-sidebar-accent hover:text-sidebar-accent-foreground shadow-[0_0_0_1px_var(--sidebar-border)] hover:shadow-[0_0_0_1px_var(--sidebar-accent)]"
    },
    size: {
      default: "h-8 text-sm",
      sm: "h-7 text-xs",
      lg: "group-data-[collapsible=icon]:p-0! h-12 text-sm"
    }
  },
  defaultVariants: { variant: "default", size: "default" }
});
function Sidebar_menu_button($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      children,
      child,
      variant = "default",
      size = "default",
      isActive = false,
      tooltipContent,
      tooltipContentProps,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    const sidebar = useSidebar();
    const buttonProps = {
      class: cn(sidebarMenuButtonVariants({ variant, size }), className),
      "data-slot": "sidebar-menu-button",
      "data-sidebar": "menu-button",
      "data-size": size,
      "data-active": isActive,
      ...restProps
    };
    function Button2($$renderer3, { props }) {
      const mergedProps = mergeProps(buttonProps, props);
      if (child) {
        $$renderer3.push("<!--[-->");
        child($$renderer3, { props: mergedProps });
        $$renderer3.push(`<!---->`);
      } else {
        $$renderer3.push("<!--[!-->");
        $$renderer3.push(`<button${attributes({ ...mergedProps })}>`);
        children?.($$renderer3);
        $$renderer3.push(`<!----></button>`);
      }
      $$renderer3.push(`<!--]-->`);
    }
    if (!tooltipContent) {
      $$renderer2.push("<!--[-->");
      Button2($$renderer2, {});
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<!---->`);
      Root$2($$renderer2, {
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->`);
          {
            let child2 = function($$renderer4, { props }) {
              Button2($$renderer4, { props });
            };
            Tooltip_trigger($$renderer3, { child: child2, $$slots: { child: true } });
          }
          $$renderer3.push(`<!----> <!---->`);
          Tooltip_content($$renderer3, spread_props([
            {
              side: "right",
              align: "center",
              hidden: sidebar.state !== "collapsed" || sidebar.isMobile
            },
            tooltipContentProps,
            {
              children: ($$renderer4) => {
                if (typeof tooltipContent === "string") {
                  $$renderer4.push("<!--[-->");
                  $$renderer4.push(`${escape_html(tooltipContent)}`);
                } else {
                  $$renderer4.push("<!--[!-->");
                  if (tooltipContent) {
                    $$renderer4.push("<!--[-->");
                    tooltipContent($$renderer4);
                    $$renderer4.push(`<!---->`);
                  } else {
                    $$renderer4.push("<!--[!-->");
                  }
                  $$renderer4.push(`<!--]-->`);
                }
                $$renderer4.push(`<!--]-->`);
              },
              $$slots: { default: true }
            }
          ]));
          $$renderer3.push(`<!---->`);
        },
        $$slots: { default: true }
      });
      $$renderer2.push(`<!---->`);
    }
    $$renderer2.push(`<!--]-->`);
    bind_props($$props, { ref });
  });
}
function Sidebar_menu_item($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    $$renderer2.push(`<li${attributes({
      "data-slot": "sidebar-menu-item",
      "data-sidebar": "menu-item",
      class: clsx(cn("group/menu-item relative", className)),
      ...restProps
    })}>`);
    children?.($$renderer2);
    $$renderer2.push(`<!----></li>`);
    bind_props($$props, { ref });
  });
}
function Sidebar_menu($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    $$renderer2.push(`<ul${attributes({
      "data-slot": "sidebar-menu",
      "data-sidebar": "menu",
      class: clsx(cn("flex w-full min-w-0 flex-col gap-1", className)),
      ...restProps
    })}>`);
    children?.($$renderer2);
    $$renderer2.push(`<!----></ul>`);
    bind_props($$props, { ref });
  });
}
function Sidebar_provider($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      open = true,
      onOpenChange = () => {
      },
      class: className,
      style,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    setSidebar({
      open: () => open,
      setOpen: (value) => {
        open = value;
        onOpenChange(value);
        document.cookie = `${SIDEBAR_COOKIE_NAME}=${open}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`;
      }
    });
    $$renderer2.push(`<!---->`);
    Provider($$renderer2, {
      delayDuration: 0,
      children: ($$renderer3) => {
        $$renderer3.push(`<div${attributes({
          "data-slot": "sidebar-wrapper",
          style: `--sidebar-width: ${stringify(SIDEBAR_WIDTH)}; --sidebar-width-icon: ${stringify(SIDEBAR_WIDTH_ICON)}; ${stringify(style)}`,
          class: clsx(cn("group/sidebar-wrapper has-data-[variant=inset]:bg-sidebar flex min-h-svh w-full", className)),
          ...restProps
        })}>`);
        children?.($$renderer3);
        $$renderer3.push(`<!----></div>`);
      }
    });
    $$renderer2.push(`<!---->`);
    bind_props($$props, { ref, open });
  });
}
function Separator($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      "data-slot": dataSlot = "separator",
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Separator$1($$renderer3, spread_props([
        {
          "data-slot": dataSlot,
          class: cn("bg-border shrink-0 data-[orientation=horizontal]:h-px data-[orientation=vertical]:h-full data-[orientation=horizontal]:w-full data-[orientation=vertical]:w-px", className)
        },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
function Sidebar_trigger($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      onclick,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    const sidebar = useSidebar();
    Button($$renderer2, spread_props([
      {
        "data-sidebar": "trigger",
        "data-slot": "sidebar-trigger",
        variant: "ghost",
        size: "icon",
        class: cn("size-7", className),
        type: "button",
        onclick: (e) => {
          onclick?.(e);
          sidebar.toggle();
        }
      },
      restProps,
      {
        children: ($$renderer3) => {
          Panel_left($$renderer3, {});
          $$renderer3.push(`<!----> <span class="sr-only">Toggle Sidebar</span>`);
        },
        $$slots: { default: true }
      }
    ]));
    bind_props($$props, { ref });
  });
}
function Sheet_overlay($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Dialog_overlay($$renderer3, spread_props([
        {
          "data-slot": "sheet-overlay",
          class: cn("data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-50 bg-black/50", className)
        },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
const sheetVariants = tv({
  base: "bg-background data-[state=open]:animate-in data-[state=closed]:animate-out fixed z-50 flex flex-col gap-4 shadow-lg transition ease-in-out data-[state=closed]:duration-300 data-[state=open]:duration-500",
  variants: {
    side: {
      top: "data-[state=closed]:slide-out-to-top data-[state=open]:slide-in-from-top inset-x-0 top-0 h-auto border-b",
      bottom: "data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom inset-x-0 bottom-0 h-auto border-t",
      left: "data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left inset-y-0 start-0 h-full w-3/4 border-e sm:max-w-sm",
      right: "data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right inset-y-0 end-0 h-full w-3/4 border-s sm:max-w-sm"
    }
  },
  defaultVariants: { side: "right" }
});
function Sheet_content($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      side = "right",
      portalProps,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Portal($$renderer3, spread_props([
        portalProps,
        {
          children: ($$renderer4) => {
            Sheet_overlay($$renderer4, {});
            $$renderer4.push(`<!----> <!---->`);
            Dialog_content($$renderer4, spread_props([
              {
                "data-slot": "sheet-content",
                class: cn(sheetVariants({ side }), className)
              },
              restProps,
              {
                get ref() {
                  return ref;
                },
                set ref($$value) {
                  ref = $$value;
                  $$settled = false;
                },
                children: ($$renderer5) => {
                  children?.($$renderer5);
                  $$renderer5.push(`<!----> <!---->`);
                  Dialog_close($$renderer5, {
                    class: "ring-offset-background focus-visible:ring-ring rounded-xs focus-visible:outline-hidden absolute end-4 top-4 opacity-70 transition-opacity hover:opacity-100 focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none",
                    children: ($$renderer6) => {
                      X($$renderer6, { class: "size-4" });
                      $$renderer6.push(`<!----> <span class="sr-only">Close</span>`);
                    },
                    $$slots: { default: true }
                  });
                  $$renderer5.push(`<!---->`);
                },
                $$slots: { default: true }
              }
            ]));
            $$renderer4.push(`<!---->`);
          },
          $$slots: { default: true }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
function Sheet_header($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    $$renderer2.push(`<div${attributes({
      "data-slot": "sheet-header",
      class: clsx(cn("flex flex-col gap-1.5 p-4", className)),
      ...restProps
    })}>`);
    children?.($$renderer2);
    $$renderer2.push(`<!----></div>`);
    bind_props($$props, { ref });
  });
}
function Sheet_title($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Dialog_title($$renderer3, spread_props([
        {
          "data-slot": "sheet-title",
          class: cn("text-foreground font-semibold", className)
        },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
function Sheet_description($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Dialog_description($$renderer3, spread_props([
        {
          "data-slot": "sheet-description",
          class: cn("text-muted-foreground text-sm", className)
        },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
const Root$1 = Dialog;
function Sidebar($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      side = "left",
      variant = "sidebar",
      collapsible = "offcanvas",
      class: className,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    const sidebar = useSidebar();
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      if (collapsible === "none") {
        $$renderer3.push("<!--[-->");
        $$renderer3.push(`<div${attributes({
          class: clsx(cn("bg-sidebar text-sidebar-foreground w-(--sidebar-width) flex h-full flex-col", className)),
          ...restProps
        })}>`);
        children?.($$renderer3);
        $$renderer3.push(`<!----></div>`);
      } else {
        $$renderer3.push("<!--[!-->");
        if (sidebar.isMobile) {
          $$renderer3.push("<!--[-->");
          var bind_get = () => sidebar.openMobile;
          var bind_set = (v) => sidebar.setOpenMobile(v);
          $$renderer3.push(`<!---->`);
          Root$1($$renderer3, spread_props([
            {
              get open() {
                return bind_get();
              },
              set open($$value) {
                bind_set($$value);
              }
            },
            restProps,
            {
              children: ($$renderer4) => {
                $$renderer4.push(`<!---->`);
                Sheet_content($$renderer4, {
                  "data-sidebar": "sidebar",
                  "data-slot": "sidebar",
                  "data-mobile": "true",
                  class: "bg-sidebar text-sidebar-foreground w-(--sidebar-width) p-0 [&>button]:hidden",
                  style: `--sidebar-width: ${stringify(SIDEBAR_WIDTH_MOBILE)};`,
                  side,
                  children: ($$renderer5) => {
                    $$renderer5.push(`<!---->`);
                    Sheet_header($$renderer5, {
                      class: "sr-only",
                      children: ($$renderer6) => {
                        $$renderer6.push(`<!---->`);
                        Sheet_title($$renderer6, {
                          children: ($$renderer7) => {
                            $$renderer7.push(`<!---->Sidebar`);
                          },
                          $$slots: { default: true }
                        });
                        $$renderer6.push(`<!----> <!---->`);
                        Sheet_description($$renderer6, {
                          children: ($$renderer7) => {
                            $$renderer7.push(`<!---->Displays the mobile sidebar.`);
                          },
                          $$slots: { default: true }
                        });
                        $$renderer6.push(`<!---->`);
                      },
                      $$slots: { default: true }
                    });
                    $$renderer5.push(`<!----> <div class="flex h-full w-full flex-col">`);
                    children?.($$renderer5);
                    $$renderer5.push(`<!----></div>`);
                  },
                  $$slots: { default: true }
                });
                $$renderer4.push(`<!---->`);
              },
              $$slots: { default: true }
            }
          ]));
          $$renderer3.push(`<!---->`);
        } else {
          $$renderer3.push("<!--[!-->");
          $$renderer3.push(`<div class="text-sidebar-foreground group peer hidden md:block"${attr("data-state", sidebar.state)}${attr("data-collapsible", sidebar.state === "collapsed" ? collapsible : "")}${attr("data-variant", variant)}${attr("data-side", side)} data-slot="sidebar"><div data-slot="sidebar-gap"${attr_class(clsx(cn("w-(--sidebar-width) relative bg-transparent transition-[width] duration-200 ease-linear", "group-data-[collapsible=offcanvas]:w-0", "group-data-[side=right]:rotate-180", variant === "floating" || variant === "inset" ? "group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)+(--spacing(4))+2px)]" : "group-data-[collapsible=icon]:w-(--sidebar-width-icon)")))}></div> <div${attributes({
            "data-slot": "sidebar-container",
            class: clsx(cn(
              "w-(--sidebar-width) fixed inset-y-0 z-10 hidden h-svh transition-[left,right,width] duration-200 ease-linear md:flex",
              side === "left" ? "start-0 group-data-[collapsible=offcanvas]:start-[calc(var(--sidebar-width)*-1)]" : "end-0 group-data-[collapsible=offcanvas]:end-[calc(var(--sidebar-width)*-1)]",
              variant === "floating" || variant === "inset" ? "p-2 group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)+(--spacing(4))+2px)]" : "group-data-[collapsible=icon]:w-(--sidebar-width-icon) group-data-[side=left]:border-e group-data-[side=right]:border-s",
              className
            )),
            ...restProps
          })}><div data-sidebar="sidebar" data-slot="sidebar-inner" class="bg-sidebar group-data-[variant=floating]:border-sidebar-border flex h-full w-full flex-col group-data-[variant=floating]:rounded-lg group-data-[variant=floating]:border group-data-[variant=floating]:shadow-sm">`);
          children?.($$renderer3);
          $$renderer3.push(`<!----></div></div></div>`);
        }
        $$renderer3.push(`<!--]-->`);
      }
      $$renderer3.push(`<!--]-->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
const logo = "/_app/immutable/assets/logo.CT2Yyt_j.png";
function Nav_project($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let { items } = $$props;
    function isActive(url) {
      const path = store_get($$store_subs ??= {}, "$page", page).url.pathname;
      if (!url) return false;
      return path === url || url !== "/" && path.startsWith(url);
    }
    let creating = false;
    let selectedProjectId = "";
    let _unsubWorkspace = null;
    function handleProjectSelect(e) {
      const id = e.target.value;
      const p = store_get($$store_subs ??= {}, "$projects", projects).find((pp) => String(pp.project_id) === String(id));
      if (p) {
        selectProjectAndLoadWells(p);
        const target = `/projects/${p.project_id}`;
        if (store_get($$store_subs ??= {}, "$page", page).url.pathname !== target) goto();
      }
    }
    onDestroy(() => {
      try {
        _unsubWorkspace && _unsubWorkspace();
      } catch (e) {
      }
    });
    $$renderer2.push(`<!---->`);
    Sidebar_group($$renderer2, {
      children: ($$renderer3) => {
        $$renderer3.push(`<!---->`);
        Sidebar_group_label($$renderer3, {
          children: ($$renderer4) => {
            $$renderer4.push(`<!---->Project Management`);
          },
          $$slots: { default: true }
        });
        $$renderer3.push(`<!----> <!---->`);
        Sidebar_group_content($$renderer3, {
          class: "flex flex-col gap-2",
          children: ($$renderer4) => {
            $$renderer4.push(`<!---->`);
            Sidebar_menu($$renderer4, {
              children: ($$renderer5) => {
                $$renderer5.push(`<!---->`);
                Sidebar_menu_item($$renderer5, {
                  class: "flex items-center gap-2",
                  children: ($$renderer6) => {
                    $$renderer6.push(`<!---->`);
                    {
                      let child = function($$renderer7, { props }) {
                        {
                          $$renderer7.push("<!--[!-->");
                          $$renderer7.push(`<button${attributes({
                            type: "button",
                            ...props,
                            class: "flex items-center gap-2",
                            disabled: creating
                          })}>`);
                          Circle_plus_filled($$renderer7, {});
                          $$renderer7.push(`<!----> <span>${escape_html("New Project")}</span></button>`);
                        }
                        $$renderer7.push(`<!--]-->`);
                      };
                      Sidebar_menu_button($$renderer6, {
                        class: "bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground active:bg-primary/90 active:text-primary-foreground min-w-8 duration-200 ease-linear",
                        tooltipContent: "Create new project",
                        child,
                        $$slots: { child: true }
                      });
                    }
                    $$renderer6.push(`<!---->`);
                  },
                  $$slots: { default: true }
                });
                $$renderer5.push(`<!---->`);
              },
              $$slots: { default: true }
            });
            $$renderer4.push(`<!----> <!---->`);
            Sidebar_menu($$renderer4, {
              children: ($$renderer5) => {
                if (store_get($$store_subs ??= {}, "$projects", projects) && store_get($$store_subs ??= {}, "$projects", projects).length) {
                  $$renderer5.push("<!--[-->");
                  $$renderer5.push(`<div class="px-2 py-2">`);
                  $$renderer5.select(
                    {
                      id: "project-select",
                      class: "input w-full text-sm h-9",
                      value: selectedProjectId,
                      onchange: handleProjectSelect
                    },
                    ($$renderer6) => {
                      $$renderer6.option({ value: "" }, ($$renderer7) => {
                        $$renderer7.push(`— select project —`);
                      });
                      $$renderer6.push(`<!--[-->`);
                      const each_array = ensure_array_like(store_get($$store_subs ??= {}, "$projects", projects));
                      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
                        let p = each_array[$$index];
                        $$renderer6.option({ value: String(p.project_id) }, ($$renderer7) => {
                          $$renderer7.push(`${escape_html(p.name)}`);
                        });
                      }
                      $$renderer6.push(`<!--]-->`);
                    }
                  );
                  $$renderer5.push(`</div>`);
                } else {
                  $$renderer5.push("<!--[!-->");
                }
                $$renderer5.push(`<!--]--> <!--[-->`);
                const each_array_1 = ensure_array_like(items);
                for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
                  let item = each_array_1[$$index_1];
                  $$renderer5.push(`<!---->`);
                  Sidebar_menu_item($$renderer5, {
                    children: ($$renderer6) => {
                      $$renderer6.push(`<!---->`);
                      {
                        let child = function($$renderer7, { props }) {
                          $$renderer7.push(`<a${attributes({
                            href: item.url,
                            ...props,
                            class: `${stringify(isActive(item.url) ? "bg-panel-foreground/5 font-semibold" : "")} flex items-center gap-2 w-full`,
                            "aria-current": isActive(item.url) ? "page" : void 0
                          })}>`);
                          if (item.icon) {
                            $$renderer7.push("<!--[-->");
                            $$renderer7.push(`<!---->`);
                            item.icon($$renderer7, {});
                            $$renderer7.push(`<!---->`);
                          } else {
                            $$renderer7.push("<!--[!-->");
                          }
                          $$renderer7.push(`<!--]--> <span>${escape_html(item.title)}</span></a>`);
                        };
                        Sidebar_menu_button($$renderer6, { tooltipContent: item.title, child, $$slots: { child: true } });
                      }
                      $$renderer6.push(`<!---->`);
                    },
                    $$slots: { default: true }
                  });
                  $$renderer5.push(`<!---->`);
                }
                $$renderer5.push(`<!--]-->`);
              },
              $$slots: { default: true }
            });
            $$renderer4.push(`<!---->`);
          },
          $$slots: { default: true }
        });
        $$renderer3.push(`<!---->`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!---->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function Nav_well($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    const API_BASE = "http://localhost:6312";
    let project = null;
    let wells = [];
    let loadingWells = false;
    let selectedWell = null;
    let selectedWellName = "";
    let depthFilterEnabled = false;
    let minDepth = null;
    let maxDepth = null;
    let zoneFilterEnabled = false;
    let zones = [];
    let selectedZones = [];
    let loadingZones = false;
    let zonesOpen = false;
    let _lastSelectedWellName = null;
    async function fetchWells(projectId) {
      loadingWells = true;
      wells = [];
      try {
        const res = await fetch(`${API_BASE}/quick_pp/database/projects/${projectId}/wells`);
        if (res.ok) {
          const data = await res.json();
          wells = data?.wells || [];
          wells.sort((a, b) => a.name.localeCompare(b.name));
        }
      } catch (e) {
        console.warn("Failed to fetch wells for sidebar", e);
      } finally {
        loadingWells = false;
      }
    }
    const unsubscribe = workspace.subscribe((w) => {
      if (w && w.project && w.project.project_id) {
        project = { ...w.project };
        selectedWell = w.selectedWell ?? null;
        selectedWellName = selectedWell?.name ?? "";
        fetchWells(w.project.project_id);
        const curWellName = w.selectedWell && w.selectedWell.name ? String(w.selectedWell.name) : null;
        if (curWellName !== _lastSelectedWellName) {
          _lastSelectedWellName = curWellName;
          if (curWellName) {
            fetchZones(w.project.project_id, curWellName);
          } else {
            zones = [];
          }
        }
      } else {
        project = null;
        wells = [];
        selectedWell = null;
        selectedWellName = "";
      }
      if (w?.depthFilter) {
        depthFilterEnabled = w.depthFilter.enabled;
        minDepth = w.depthFilter.minDepth;
        maxDepth = w.depthFilter.maxDepth;
      }
      if (w?.zoneFilter) {
        zoneFilterEnabled = w.zoneFilter.enabled;
        selectedZones = Array.isArray(w.zoneFilter.zones) ? [...w.zoneFilter.zones] : [];
      }
    });
    onDestroy(() => unsubscribe());
    let { items } = $$props;
    function isActive(url) {
      const path = store_get($$store_subs ??= {}, "$page", page).url.pathname;
      if (!url) return false;
      return path === url || url !== "/" && path.startsWith(url);
    }
    function handleSelect(e) {
      const name = e.target.value;
      if (!name || !project) return;
      selectedWellName = name;
      selectWell({ id: name, name });
      goto(`/wells/${project.project_id}/${encodeURIComponent(String(name))}`);
    }
    function computeHref(itemUrl) {
      if (!project) return itemUrl;
      try {
        if (itemUrl && itemUrl.startsWith("/wells")) {
          const suffix = itemUrl.replace(/^\/wells/, "");
          if (selectedWell && selectedWell.name) {
            return `/wells/${project.project_id}/${encodeURIComponent(selectedWell.name)}${suffix}`;
          }
          return `/wells/${project.project_id}`;
        }
      } catch (e) {
        console.warn("Failed to compute href for nav item", e);
      }
      return itemUrl;
    }
    function extractZoneValue(row) {
      if (!row || typeof row !== "object") return null;
      const candidates = [
        "name",
        "zone",
        "Zone",
        "ZONE",
        "formation",
        "formation_name",
        "formationName",
        "FORMATION",
        "formation_top",
        "formationTop"
      ];
      for (const k of candidates) {
        if (k in row && row[k] !== null && row[k] !== void 0 && String(row[k]).trim() !== "") {
          return String(row[k]);
        }
      }
      for (const k of Object.keys(row)) {
        if (/zone|formation/i.test(k) && row[k] !== null && row[k] !== void 0 && String(row[k]).trim() !== "") {
          return String(row[k]);
        }
      }
      return null;
    }
    async function fetchZones(projectId, wellName) {
      loadingZones = true;
      zones = [];
      try {
        const url = `${API_BASE}/quick_pp/database/projects/${projectId}/formation_tops?well_name=${encodeURIComponent(wellName)}`;
        const res = await fetch(url);
        if (!res.ok) return;
        const fd = await res.json();
        console.log("Fetched formation tops for zones:", fd);
        let dataArray = [];
        if (Array.isArray(fd)) dataArray = fd;
        else if (fd && Array.isArray(fd.tops)) dataArray = fd.tops;
        const setVals = /* @__PURE__ */ new Set();
        for (const r of dataArray) {
          const v = extractZoneValue(r);
          if (v !== null) setVals.add(v);
        }
        zones = Array.from(setVals).sort((a, b) => a.localeCompare(b));
      } catch (e) {
        console.warn("Failed to fetch zones for sidebar", e);
      } finally {
        loadingZones = false;
      }
    }
    $$renderer2.push(`<!---->`);
    Sidebar_group($$renderer2, {
      children: ($$renderer3) => {
        $$renderer3.push(`<!---->`);
        Sidebar_group_label($$renderer3, {
          children: ($$renderer4) => {
            $$renderer4.push(`<!---->Well Analysis`);
          },
          $$slots: { default: true }
        });
        $$renderer3.push(`<!----> <!---->`);
        Sidebar_group_content($$renderer3, {
          class: "flex flex-col gap-2",
          children: ($$renderer4) => {
            if (project) {
              $$renderer4.push("<!--[-->");
              $$renderer4.push(`<div class="px-2 py-2"><div class="text-sm font-semibold">${escape_html(project.name)}</div> `);
              if (loadingWells) {
                $$renderer4.push("<!--[-->");
                $$renderer4.push(`<div class="text-sm">Loading wells…</div>`);
              } else {
                $$renderer4.push("<!--[!-->");
                if (wells && wells.length) {
                  $$renderer4.push("<!--[-->");
                  $$renderer4.push(`<div class="mt-2">`);
                  $$renderer4.select(
                    {
                      id: "well-select",
                      class: "input w-full mt-1 text-sm h-9",
                      value: selectedWellName,
                      onchange: handleSelect
                    },
                    ($$renderer5) => {
                      $$renderer5.option({ value: "" }, ($$renderer6) => {
                        $$renderer6.push(`— select well —`);
                      });
                      $$renderer5.push(`<!--[-->`);
                      const each_array = ensure_array_like(wells);
                      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
                        let w = each_array[$$index];
                        $$renderer5.option({ value: w.name }, ($$renderer6) => {
                          $$renderer6.push(`${escape_html(w.name)}`);
                        });
                      }
                      $$renderer5.push(`<!--]-->`);
                    }
                  );
                  $$renderer4.push(`</div>`);
                } else {
                  $$renderer4.push("<!--[!-->");
                  $$renderer4.push(`<div class="text-sm text-muted-foreground mt-2">No wells in this project.</div>`);
                }
                $$renderer4.push(`<!--]-->`);
              }
              $$renderer4.push(`<!--]--></div> `);
              if (selectedWell) {
                $$renderer4.push("<!--[-->");
                $$renderer4.push(`<div class="flex items-center gap-2 mb-2"><input type="checkbox" id="depth-filter"${attr("checked", depthFilterEnabled, true)} class="rounded"/> <label for="depth-filter" class="text-sm font-medium cursor-pointer">Filter by Depth</label></div> `);
                if (depthFilterEnabled) {
                  $$renderer4.push("<!--[-->");
                  $$renderer4.push(`<div class="space-y-2"><div><label class="text-xs text-muted-foreground" for="min-depth">Min Depth</label> <input type="number" id="min-depth"${attr("value", minDepth)} placeholder="e.g. 1000" class="input w-full text-sm h-8"/></div> <div><label class="text-xs text-muted-foreground" for="max-depth">Max Depth</label> <input type="number" id="max-depth"${attr("value", maxDepth)} placeholder="e.g. 2000" class="input w-full text-sm h-8"/></div> <button class="text-xs text-muted-foreground hover:text-foreground underline">Clear Filter</button></div>`);
                } else {
                  $$renderer4.push("<!--[!-->");
                }
                $$renderer4.push(`<!--]--> <div class="flex items-center gap-2 mb-2"><input type="checkbox" id="zone-filter"${attr("checked", zoneFilterEnabled, true)} class="rounded"/> <label for="zone-filter" class="text-sm font-medium cursor-pointer">Filter by Zone</label></div> `);
                if (zoneFilterEnabled) {
                  $$renderer4.push("<!--[-->");
                  if (loadingZones) {
                    $$renderer4.push("<!--[-->");
                    $$renderer4.push(`<div class="text-sm">Loading zones…</div>`);
                  } else {
                    $$renderer4.push("<!--[!-->");
                    if (zones && zones.length) {
                      $$renderer4.push("<!--[-->");
                      $$renderer4.push(`<div><div class="relative mt-1"><button type="button" class="input w-full text-sm h-9 flex items-center justify-between" aria-haspopup="listbox"${attr("aria-expanded", zonesOpen)}><span>${escape_html(selectedZones && selectedZones.length ? `${selectedZones.length} selected` : "Choose zones")}</span> <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-2" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 011.08 1.04l-4.25 4.25a.75.75 0 01-1.06 0L5.21 8.27a.75.75 0 01.02-1.06z" clip-rule="evenodd"></path></svg></button> `);
                      {
                        $$renderer4.push("<!--[!-->");
                      }
                      $$renderer4.push(`<!--]--></div></div>`);
                    } else {
                      $$renderer4.push("<!--[!-->");
                      $$renderer4.push(`<div class="text-sm text-muted-foreground">No zones available for this well.</div>`);
                    }
                    $$renderer4.push(`<!--]-->`);
                  }
                  $$renderer4.push(`<!--]-->`);
                } else {
                  $$renderer4.push("<!--[!-->");
                }
                $$renderer4.push(`<!--]-->`);
              } else {
                $$renderer4.push("<!--[!-->");
              }
              $$renderer4.push(`<!--]-->`);
            } else {
              $$renderer4.push("<!--[!-->");
              $$renderer4.push(`<div class="px-2 py-2 text-sm text-muted-foreground">No project selected <a href="/projects" class="ml-1">Open Projects</a></div>`);
            }
            $$renderer4.push(`<!--]--> <!---->`);
            Sidebar_menu($$renderer4, {
              children: ($$renderer5) => {
                $$renderer5.push(`<!--[-->`);
                const each_array_2 = ensure_array_like(items);
                for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
                  let item = each_array_2[$$index_2];
                  $$renderer5.push(`<!---->`);
                  Sidebar_menu_item($$renderer5, {
                    children: ($$renderer6) => {
                      $$renderer6.push(`<!---->`);
                      {
                        let child = function($$renderer7, { props }) {
                          $$renderer7.push(`<a${attributes({
                            href: computeHref(item.url),
                            ...props,
                            class: `${stringify(isActive(computeHref(item.url)) ? "bg-panel-foreground/5 font-semibold" : "")} flex items-center gap-2 w-full`,
                            "aria-current": isActive(computeHref(item.url)) ? "page" : void 0
                          })}>`);
                          if (item.icon) {
                            $$renderer7.push("<!--[-->");
                            $$renderer7.push(`<!---->`);
                            item.icon($$renderer7, {});
                            $$renderer7.push(`<!---->`);
                          } else {
                            $$renderer7.push("<!--[!-->");
                          }
                          $$renderer7.push(`<!--]--> <span>${escape_html(item.title)}</span></a>`);
                        };
                        Sidebar_menu_button($$renderer6, { tooltipContent: item.title, child, $$slots: { child: true } });
                      }
                      $$renderer6.push(`<!---->`);
                    },
                    $$slots: { default: true }
                  });
                  $$renderer5.push(`<!---->`);
                }
                $$renderer5.push(`<!--]-->`);
              },
              $$slots: { default: true }
            });
            $$renderer4.push(`<!---->`);
          },
          $$slots: { default: true }
        });
        $$renderer3.push(`<!---->`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!---->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function Nav_multiWell($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    function isActive(url) {
      const path = store_get($$store_subs ??= {}, "$page", page).url.pathname;
      if (!url) return false;
      return path === url || url !== "/" && path.startsWith(url);
    }
    let { items } = $$props;
    let project = null;
    const API_BASE = "http://localhost:6312";
    let zoneFilterEnabled = false;
    let zones = [];
    let selectedZones = [];
    let loadingZones = false;
    let zonesOpen = false;
    let _lastProjectId = null;
    const unsub = workspace.subscribe((w) => {
      project = w?.project ?? null;
      if (w?.zoneFilter) {
        zoneFilterEnabled = !!w.zoneFilter.enabled;
        selectedZones = Array.isArray(w.zoneFilter.zones) ? [...w.zoneFilter.zones] : [];
      }
      try {
        const pid = project && project.project_id ? project.project_id : null;
        if (pid && pid !== _lastProjectId) {
          _lastProjectId = pid;
          fetchZones(pid);
        } else if (!pid) {
          zones = [];
        }
      } catch (e) {
        console.warn("workspace.subscribe multi-well", e);
      }
    });
    onDestroy(() => unsub());
    function computeHref(itemUrl) {
      if (!project) return itemUrl;
      try {
        if (itemUrl && itemUrl.startsWith("/projects")) {
          const suffix = itemUrl.replace(/^\/projects/, "");
          return `/projects/${project.project_id}${suffix}`;
        }
      } catch (e) {
        console.warn("computeHref multi-well", e);
      }
      return itemUrl;
    }
    function extractZoneValue(row) {
      if (!row || typeof row !== "object") return null;
      const candidates = [
        "name",
        "zone",
        "Zone",
        "ZONE",
        "formation",
        "formation_name",
        "formationName",
        "FORMATION",
        "formation_top",
        "formationTop"
      ];
      for (const k of candidates) {
        if (k in row && row[k] !== null && row[k] !== void 0 && String(row[k]).trim() !== "") {
          return String(row[k]);
        }
      }
      for (const k of Object.keys(row)) {
        if (/zone|formation/i.test(k) && row[k] !== null && row[k] !== void 0 && String(row[k]).trim() !== "") {
          return String(row[k]);
        }
      }
      return null;
    }
    async function fetchZones(projectId) {
      loadingZones = true;
      zones = [];
      try {
        const url = `${API_BASE}/quick_pp/database/projects/${projectId}/formation_tops`;
        const res = await fetch(url);
        if (!res.ok) return;
        const fd = await res.json();
        let dataArray = [];
        if (fd && Array.isArray(fd.tops)) dataArray = fd.tops;
        else if (Array.isArray(fd)) dataArray = fd;
        else if (fd && Array.isArray(fd.tops)) dataArray = fd.tops;
        const setVals = /* @__PURE__ */ new Set();
        for (const r of dataArray) {
          const v = extractZoneValue(r);
          if (v !== null) setVals.add(v);
        }
        zones = Array.from(setVals).sort((a, b) => a.localeCompare(b));
      } catch (e) {
        console.warn("Failed to fetch project zones for sidebar", e);
      } finally {
        loadingZones = false;
      }
    }
    $$renderer2.push(`<!---->`);
    Sidebar_group($$renderer2, {
      class: "group-data-[collapsible=icon]:hidden",
      children: ($$renderer3) => {
        $$renderer3.push(`<!---->`);
        Sidebar_group_label($$renderer3, {
          children: ($$renderer4) => {
            $$renderer4.push(`<!---->Multi-Well`);
          },
          $$slots: { default: true }
        });
        $$renderer3.push(`<!----> <!---->`);
        Sidebar_menu($$renderer3, {
          children: ($$renderer4) => {
            $$renderer4.push(`<div class="flex items-center gap-2 mb-2"><input type="checkbox" id="zone-filter"${attr("checked", zoneFilterEnabled, true)} class="rounded"/> <label for="zone-filter" class="text-sm font-medium cursor-pointer">Filter by Zone</label></div> `);
            if (zoneFilterEnabled) {
              $$renderer4.push("<!--[-->");
              if (loadingZones) {
                $$renderer4.push("<!--[-->");
                $$renderer4.push(`<div class="text-sm">Loading zones…</div>`);
              } else {
                $$renderer4.push("<!--[!-->");
                if (zones && zones.length) {
                  $$renderer4.push("<!--[-->");
                  $$renderer4.push(`<div><div class="relative mt-1"><button type="button" class="input w-full text-sm h-9 flex items-center justify-between" aria-haspopup="listbox"${attr("aria-expanded", zonesOpen)}><span>${escape_html(selectedZones && selectedZones.length ? `${selectedZones.length} selected` : "Choose zones")}</span> <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-2" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 011.08 1.04l-4.25 4.25a.75.75 0 01-1.06 0L5.21 8.27a.75.75 0 01.02-1.06z" clip-rule="evenodd"></path></svg></button> `);
                  {
                    $$renderer4.push("<!--[!-->");
                  }
                  $$renderer4.push(`<!--]--></div></div>`);
                } else {
                  $$renderer4.push("<!--[!-->");
                  $$renderer4.push(`<div class="text-sm text-muted-foreground">No zones available for this well.</div>`);
                }
                $$renderer4.push(`<!--]-->`);
              }
              $$renderer4.push(`<!--]-->`);
            } else {
              $$renderer4.push("<!--[!-->");
            }
            $$renderer4.push(`<!--]--> <!--[-->`);
            const each_array_1 = ensure_array_like(items);
            for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
              let item = each_array_1[$$index_1];
              $$renderer4.push(`<!---->`);
              Sidebar_menu_item($$renderer4, {
                children: ($$renderer5) => {
                  $$renderer5.push(`<!---->`);
                  {
                    let child = function($$renderer6, { props }) {
                      $$renderer6.push(`<a${attributes({
                        ...props,
                        href: computeHref(item.url),
                        class: `${stringify(isActive(computeHref(item.url)) ? "bg-panel-foreground/5 font-semibold" : "")} flex items-center gap-2`,
                        "aria-current": isActive(computeHref(item.url)) ? "page" : void 0
                      })}>`);
                      if (item.icon) {
                        $$renderer6.push("<!--[-->");
                        $$renderer6.push(`<!---->`);
                        item.icon($$renderer6, {});
                        $$renderer6.push(`<!---->`);
                      } else {
                        $$renderer6.push("<!--[!-->");
                      }
                      $$renderer6.push(`<!--]--> <span>${escape_html(item.title)}</span></a>`);
                    };
                    Sidebar_menu_button($$renderer5, { child, $$slots: { child: true } });
                  }
                  $$renderer5.push(`<!---->`);
                },
                $$slots: { default: true }
              });
              $$renderer4.push(`<!---->`);
            }
            $$renderer4.push(`<!--]-->`);
          },
          $$slots: { default: true }
        });
        $$renderer3.push(`<!---->`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!---->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function Dropdown_menu_content($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      sideOffset = 4,
      portalProps,
      class: className,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Portal($$renderer3, spread_props([
        portalProps,
        {
          children: ($$renderer4) => {
            $$renderer4.push(`<!---->`);
            Dropdown_menu_content$1($$renderer4, spread_props([
              {
                "data-slot": "dropdown-menu-content",
                sideOffset,
                class: cn("bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-end-2 data-[side=right]:slide-in-from-start-2 data-[side=top]:slide-in-from-bottom-2 max-h-(--bits-dropdown-menu-content-available-height) origin-(--bits-dropdown-menu-content-transform-origin) z-50 min-w-[8rem] overflow-y-auto overflow-x-hidden rounded-md border p-1 shadow-md outline-none", className)
              },
              restProps,
              {
                get ref() {
                  return ref;
                },
                set ref($$value) {
                  ref = $$value;
                  $$settled = false;
                }
              }
            ]));
            $$renderer4.push(`<!---->`);
          },
          $$slots: { default: true }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
function Dropdown_menu_group($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { ref = null, $$slots, $$events, ...restProps } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Menu_group($$renderer3, spread_props([
        { "data-slot": "dropdown-menu-group" },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
function Dropdown_menu_item($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      inset,
      variant = "default",
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Menu_item($$renderer3, spread_props([
        {
          "data-slot": "dropdown-menu-item",
          "data-inset": inset,
          "data-variant": variant,
          class: cn("data-highlighted:bg-accent data-highlighted:text-accent-foreground data-[variant=destructive]:text-destructive data-[variant=destructive]:data-highlighted:bg-destructive/10 dark:data-[variant=destructive]:data-highlighted:bg-destructive/20 data-[variant=destructive]:data-highlighted:text-destructive data-[variant=destructive]:*:[svg]:!text-destructive [&_svg:not([class*='text-'])]:text-muted-foreground outline-hidden relative flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm data-[disabled]:pointer-events-none data-[inset]:ps-8 data-[disabled]:opacity-50 [&_svg:not([class*='size-'])]:size-4 [&_svg]:pointer-events-none [&_svg]:shrink-0", className)
        },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
function Dropdown_menu_label($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      inset,
      children,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    $$renderer2.push(`<div${attributes({
      "data-slot": "dropdown-menu-label",
      "data-inset": inset,
      class: clsx(cn("px-2 py-1.5 text-sm font-semibold data-[inset]:ps-8", className)),
      ...restProps
    })}>`);
    children?.($$renderer2);
    $$renderer2.push(`<!----></div>`);
    bind_props($$props, { ref });
  });
}
function Dropdown_menu_separator($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Menu_separator($$renderer3, spread_props([
        {
          "data-slot": "dropdown-menu-separator",
          class: cn("bg-border -mx-1 my-1 h-px", className)
        },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
function Dropdown_menu_trigger($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { ref = null, $$slots, $$events, ...restProps } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Menu_trigger($$renderer3, spread_props([
        { "data-slot": "dropdown-menu-trigger" },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
const Root = Menu;
function Nav_reporting($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    function isActive(url) {
      const path = store_get($$store_subs ??= {}, "$page", page).url.pathname;
      if (!url) return false;
      return path === url || url !== "/" && path.startsWith(url);
    }
    let { items } = $$props;
    const sidebar = useSidebar();
    $$renderer2.push(`<!---->`);
    Sidebar_group($$renderer2, {
      class: "group-data-[collapsible=icon]:hidden",
      children: ($$renderer3) => {
        $$renderer3.push(`<!---->`);
        Sidebar_group_label($$renderer3, {
          children: ($$renderer4) => {
            $$renderer4.push(`<!---->Reporting`);
          },
          $$slots: { default: true }
        });
        $$renderer3.push(`<!----> <!---->`);
        Sidebar_menu($$renderer3, {
          children: ($$renderer4) => {
            $$renderer4.push(`<!--[-->`);
            const each_array = ensure_array_like(items);
            for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
              let item = each_array[$$index];
              $$renderer4.push(`<!---->`);
              Sidebar_menu_item($$renderer4, {
                children: ($$renderer5) => {
                  $$renderer5.push(`<!---->`);
                  {
                    let child = function($$renderer6, { props }) {
                      $$renderer6.push(`<a${attributes({
                        ...props,
                        href: item.url,
                        class: `${stringify(isActive(item.url) ? "bg-panel-foreground/5 font-semibold" : "")} flex items-center gap-2`,
                        "aria-current": isActive(item.url) ? "page" : void 0
                      })}><!---->`);
                      item.icon($$renderer6, {});
                      $$renderer6.push(`<!----> <span>${escape_html(item.name)}</span></a>`);
                    };
                    Sidebar_menu_button($$renderer5, { child, $$slots: { child: true } });
                  }
                  $$renderer5.push(`<!----> <!---->`);
                  Root($$renderer5, {
                    children: ($$renderer6) => {
                      $$renderer6.push(`<!---->`);
                      {
                        let child = function($$renderer7, { props }) {
                          $$renderer7.push(`<!---->`);
                          Sidebar_menu_action($$renderer7, spread_props([
                            props,
                            {
                              showOnHover: true,
                              class: "data-[state=open]:bg-accent rounded-sm",
                              children: ($$renderer8) => {
                                Dots($$renderer8, {});
                                $$renderer8.push(`<!----> <span class="sr-only">More</span>`);
                              },
                              $$slots: { default: true }
                            }
                          ]));
                          $$renderer7.push(`<!---->`);
                        };
                        Dropdown_menu_trigger($$renderer6, { child, $$slots: { child: true } });
                      }
                      $$renderer6.push(`<!----> <!---->`);
                      Dropdown_menu_content($$renderer6, {
                        class: "w-24 rounded-lg",
                        side: sidebar.isMobile ? "bottom" : "right",
                        align: sidebar.isMobile ? "end" : "start",
                        children: ($$renderer7) => {
                          $$renderer7.push(`<!---->`);
                          Dropdown_menu_item($$renderer7, {
                            children: ($$renderer8) => {
                              Folder($$renderer8, {});
                              $$renderer8.push(`<!----> <span>Open</span>`);
                            },
                            $$slots: { default: true }
                          });
                          $$renderer7.push(`<!----> <!---->`);
                          Dropdown_menu_item($$renderer7, {
                            children: ($$renderer8) => {
                              Share_3($$renderer8, {});
                              $$renderer8.push(`<!----> <span>Share</span>`);
                            },
                            $$slots: { default: true }
                          });
                          $$renderer7.push(`<!----> <!---->`);
                          Dropdown_menu_separator($$renderer7, {});
                          $$renderer7.push(`<!----> <!---->`);
                          Dropdown_menu_item($$renderer7, {
                            variant: "destructive",
                            children: ($$renderer8) => {
                              Trash($$renderer8, {});
                              $$renderer8.push(`<!----> <span>Delete</span>`);
                            },
                            $$slots: { default: true }
                          });
                          $$renderer7.push(`<!---->`);
                        },
                        $$slots: { default: true }
                      });
                      $$renderer6.push(`<!---->`);
                    },
                    $$slots: { default: true }
                  });
                  $$renderer5.push(`<!---->`);
                },
                $$slots: { default: true }
              });
              $$renderer4.push(`<!---->`);
            }
            $$renderer4.push(`<!--]-->`);
          },
          $$slots: { default: true }
        });
        $$renderer3.push(`<!---->`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!---->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function Nav_secondary($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    function isActive(url) {
      const path = store_get($$store_subs ??= {}, "$page", page).url.pathname;
      if (!url) return false;
      return path === url || url !== "/" && path.startsWith(url);
    }
    let { items, $$slots, $$events, ...restProps } = $$props;
    $$renderer2.push(`<!---->`);
    Sidebar_group($$renderer2, spread_props([
      restProps,
      {
        children: ($$renderer3) => {
          $$renderer3.push(`<!---->`);
          Sidebar_group_content($$renderer3, {
            children: ($$renderer4) => {
              $$renderer4.push(`<!---->`);
              Sidebar_menu($$renderer4, {
                children: ($$renderer5) => {
                  $$renderer5.push(`<!--[-->`);
                  const each_array = ensure_array_like(items);
                  for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
                    let item = each_array[$$index];
                    $$renderer5.push(`<!---->`);
                    Sidebar_menu_item($$renderer5, {
                      children: ($$renderer6) => {
                        $$renderer6.push(`<!---->`);
                        {
                          let child = function($$renderer7, { props }) {
                            $$renderer7.push(`<a${attributes({
                              href: item.url,
                              ...props,
                              class: `${stringify(isActive(item.url) ? "bg-panel-foreground/5 font-semibold" : "")} flex items-center gap-2`,
                              "aria-current": isActive(item.url) ? "page" : void 0
                            })}><!---->`);
                            item.icon($$renderer7, {});
                            $$renderer7.push(`<!----> <span>${escape_html(item.title)}</span></a>`);
                          };
                          Sidebar_menu_button($$renderer6, { child, $$slots: { child: true } });
                        }
                        $$renderer6.push(`<!---->`);
                      },
                      $$slots: { default: true }
                    });
                    $$renderer5.push(`<!---->`);
                  }
                  $$renderer5.push(`<!--]-->`);
                },
                $$slots: { default: true }
              });
              $$renderer4.push(`<!---->`);
            },
            $$slots: { default: true }
          });
          $$renderer3.push(`<!---->`);
        },
        $$slots: { default: true }
      }
    ]));
    $$renderer2.push(`<!---->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function Avatar($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      loadingStatus = "loading",
      class: className,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Avatar$1($$renderer3, spread_props([
        {
          "data-slot": "avatar",
          class: cn("relative flex size-8 shrink-0 overflow-hidden rounded-full", className)
        },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          },
          get loadingStatus() {
            return loadingStatus;
          },
          set loadingStatus($$value) {
            loadingStatus = $$value;
            $$settled = false;
          }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref, loadingStatus });
  });
}
function Avatar_image($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Avatar_image$1($$renderer3, spread_props([
        {
          "data-slot": "avatar-image",
          class: cn("aspect-square size-full", className)
        },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
function Avatar_fallback($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      ref = null,
      class: className,
      $$slots,
      $$events,
      ...restProps
    } = $$props;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<!---->`);
      Avatar_fallback$1($$renderer3, spread_props([
        {
          "data-slot": "avatar-fallback",
          class: cn("bg-muted flex size-full items-center justify-center rounded-full", className)
        },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          }
        }
      ]));
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { ref });
  });
}
function Nav_user($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { user } = $$props;
    const sidebar = useSidebar();
    $$renderer2.push(`<!---->`);
    Sidebar_menu($$renderer2, {
      children: ($$renderer3) => {
        $$renderer3.push(`<!---->`);
        Sidebar_menu_item($$renderer3, {
          children: ($$renderer4) => {
            $$renderer4.push(`<!---->`);
            Root($$renderer4, {
              children: ($$renderer5) => {
                $$renderer5.push(`<!---->`);
                {
                  let child = function($$renderer6, { props }) {
                    $$renderer6.push(`<!---->`);
                    Sidebar_menu_button($$renderer6, spread_props([
                      props,
                      {
                        size: "lg",
                        class: "data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground",
                        children: ($$renderer7) => {
                          $$renderer7.push(`<!---->`);
                          Avatar($$renderer7, {
                            class: "size-8 rounded-lg grayscale",
                            children: ($$renderer8) => {
                              $$renderer8.push(`<!---->`);
                              Avatar_image($$renderer8, { src: user.avatar, alt: user.name });
                              $$renderer8.push(`<!----> <!---->`);
                              Avatar_fallback($$renderer8, {
                                class: "rounded-lg",
                                children: ($$renderer9) => {
                                  $$renderer9.push(`<!---->CN`);
                                },
                                $$slots: { default: true }
                              });
                              $$renderer8.push(`<!---->`);
                            },
                            $$slots: { default: true }
                          });
                          $$renderer7.push(`<!----> <div class="grid flex-1 text-start text-sm leading-tight"><span class="truncate font-medium">${escape_html(user.name)}</span> <span class="text-muted-foreground truncate text-xs">${escape_html(user.email)}</span></div> `);
                          Dots_vertical($$renderer7, { class: "ms-auto size-4" });
                          $$renderer7.push(`<!---->`);
                        },
                        $$slots: { default: true }
                      }
                    ]));
                    $$renderer6.push(`<!---->`);
                  };
                  Dropdown_menu_trigger($$renderer5, { child, $$slots: { child: true } });
                }
                $$renderer5.push(`<!----> <!---->`);
                Dropdown_menu_content($$renderer5, {
                  class: "w-(--bits-dropdown-menu-anchor-width) min-w-56 rounded-lg",
                  side: sidebar.isMobile ? "bottom" : "right",
                  align: "end",
                  sideOffset: 4,
                  children: ($$renderer6) => {
                    $$renderer6.push(`<!---->`);
                    Dropdown_menu_label($$renderer6, {
                      class: "p-0 font-normal",
                      children: ($$renderer7) => {
                        $$renderer7.push(`<div class="flex items-center gap-2 px-1 py-1.5 text-start text-sm"><!---->`);
                        Avatar($$renderer7, {
                          class: "size-8 rounded-lg",
                          children: ($$renderer8) => {
                            $$renderer8.push(`<!---->`);
                            Avatar_image($$renderer8, { src: user.avatar, alt: user.name });
                            $$renderer8.push(`<!----> <!---->`);
                            Avatar_fallback($$renderer8, {
                              class: "rounded-lg",
                              children: ($$renderer9) => {
                                $$renderer9.push(`<!---->CN`);
                              },
                              $$slots: { default: true }
                            });
                            $$renderer8.push(`<!---->`);
                          },
                          $$slots: { default: true }
                        });
                        $$renderer7.push(`<!----> <div class="grid flex-1 text-start text-sm leading-tight"><span class="truncate font-medium">${escape_html(user.name)}</span> <span class="text-muted-foreground truncate text-xs">${escape_html(user.email)}</span></div></div>`);
                      },
                      $$slots: { default: true }
                    });
                    $$renderer6.push(`<!----> <!---->`);
                    Dropdown_menu_separator($$renderer6, {});
                    $$renderer6.push(`<!----> <!---->`);
                    Dropdown_menu_group($$renderer6, {
                      children: ($$renderer7) => {
                        $$renderer7.push(`<!---->`);
                        Dropdown_menu_item($$renderer7, {
                          children: ($$renderer8) => {
                            User_circle($$renderer8, {});
                            $$renderer8.push(`<!----> Account`);
                          },
                          $$slots: { default: true }
                        });
                        $$renderer7.push(`<!----> <!---->`);
                        Dropdown_menu_item($$renderer7, {
                          children: ($$renderer8) => {
                            Credit_card($$renderer8, {});
                            $$renderer8.push(`<!----> Billing`);
                          },
                          $$slots: { default: true }
                        });
                        $$renderer7.push(`<!----> <!---->`);
                        Dropdown_menu_item($$renderer7, {
                          children: ($$renderer8) => {
                            Notification($$renderer8, {});
                            $$renderer8.push(`<!----> Notifications`);
                          },
                          $$slots: { default: true }
                        });
                        $$renderer7.push(`<!---->`);
                      },
                      $$slots: { default: true }
                    });
                    $$renderer6.push(`<!----> <!---->`);
                    Dropdown_menu_separator($$renderer6, {});
                    $$renderer6.push(`<!----> <!---->`);
                    Dropdown_menu_item($$renderer6, {
                      children: ($$renderer7) => {
                        Logout($$renderer7, {});
                        $$renderer7.push(`<!----> Log out`);
                      },
                      $$slots: { default: true }
                    });
                    $$renderer6.push(`<!---->`);
                  },
                  $$slots: { default: true }
                });
                $$renderer5.push(`<!---->`);
              },
              $$slots: { default: true }
            });
            $$renderer4.push(`<!---->`);
          },
          $$slots: { default: true }
        });
        $$renderer3.push(`<!---->`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!---->`);
  });
}
function App_sidebar($$renderer, $$props) {
  const data = {
    user: { name: "quick-pp", email: "admin@quick-pp.com", avatar: logo },
    navProject: [
      {
        title: "Project Overview",
        url: "/projects",
        icon: Map_search
      }
    ],
    navWell: [
      {
        title: "Data Overview",
        url: "/wells/data",
        icon: List_details
      },
      {
        title: "Lithology & Porosity",
        url: "/wells/litho-poro",
        icon: Wall
      },
      {
        title: "Permeability",
        url: "/wells/perm",
        icon: Text_wrap_disabled
      },
      {
        title: "Water Saturation",
        url: "/wells/saturation",
        icon: Wash_temperature_6
      },
      {
        title: "Reservoir Summary",
        url: "/wells/ressum",
        icon: Table
      }
    ],
    navMultiWell: [
      {
        title: "Rock Typing",
        url: "/projects/rock-typing",
        icon: Stack_back
      },
      {
        title: "Perm Transform",
        url: "/projects/perm-transform",
        icon: Ease_in_out_control_points
      },
      {
        title: "Saturation Height Function",
        url: "/projects/shf",
        icon: Chart_scatter
      }
    ],
    navSecondary: [
      { title: "Settings", url: "#", icon: Settings },
      { title: "Get Help", url: "#", icon: Help },
      { title: "Search", url: "#", icon: Search }
    ],
    navReporting: [
      { name: "Data Library", url: "#", icon: Database },
      { name: "Reports", url: "#", icon: Report },
      { name: "Word Assistant", url: "#", icon: File_word }
    ]
  };
  let { $$slots, $$events, ...restProps } = $$props;
  $$renderer.push(`<!---->`);
  Sidebar($$renderer, spread_props([
    { collapsible: "offcanvas" },
    restProps,
    {
      children: ($$renderer2) => {
        $$renderer2.push(`<!---->`);
        Sidebar_header($$renderer2, {
          children: ($$renderer3) => {
            $$renderer3.push(`<!---->`);
            Sidebar_menu($$renderer3, {
              children: ($$renderer4) => {
                $$renderer4.push(`<!---->`);
                Sidebar_menu_item($$renderer4, {
                  children: ($$renderer5) => {
                    $$renderer5.push(`<!---->`);
                    {
                      let child = function($$renderer6, { props }) {
                        $$renderer6.push(`<a${attributes({ href: "##", ...props })}><img${attr("src", logo)} alt="quick-pp logo" class="!size-7"/> <span class="text-base font-semibold">quick-pp</span></a>`);
                      };
                      Sidebar_menu_button($$renderer5, {
                        class: "data-[slot=sidebar-menu-button]:!p-1.5",
                        child,
                        $$slots: { child: true }
                      });
                    }
                    $$renderer5.push(`<!---->`);
                  },
                  $$slots: { default: true }
                });
                $$renderer4.push(`<!---->`);
              },
              $$slots: { default: true }
            });
            $$renderer3.push(`<!---->`);
          },
          $$slots: { default: true }
        });
        $$renderer2.push(`<!----> <!---->`);
        Sidebar_content($$renderer2, {
          children: ($$renderer3) => {
            $$renderer3.push(`<div class="px-2 py-2 border-t border-border/50 mt-2">`);
            Nav_project($$renderer3, { items: data.navProject });
            $$renderer3.push(`<!----></div> <div class="px-2 py-2 border-t border-border/50 mt-2">`);
            Nav_well($$renderer3, { items: data.navWell });
            $$renderer3.push(`<!----></div> <div class="px-2 py-2 border-t border-border/50 mt-2">`);
            Nav_multiWell($$renderer3, { items: data.navMultiWell });
            $$renderer3.push(`<!----></div> <div class="px-2 py-2 border-t border-border/50 mt-2">`);
            Nav_reporting($$renderer3, { items: data.navReporting });
            $$renderer3.push(`<!----></div> `);
            Nav_secondary($$renderer3, { items: data.navSecondary, class: "mt-auto" });
            $$renderer3.push(`<!---->`);
          },
          $$slots: { default: true }
        });
        $$renderer2.push(`<!----> <!---->`);
        Sidebar_footer($$renderer2, {
          children: ($$renderer3) => {
            Nav_user($$renderer3, { user: data.user });
          },
          $$slots: { default: true }
        });
        $$renderer2.push(`<!---->`);
      },
      $$slots: { default: true }
    }
  ]));
  $$renderer.push(`<!---->`);
}
function Site_header($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    derived$1(workspace, ($w) => $w.title || "QPP - Petrophysical Analysis");
    const subtitle = derived$1(workspace, ($w) => $w.subtitle || "");
    const projectName = derived$1(workspace, ($w) => $w.project && $w.project.name ? String($w.project.name) : "");
    const projectId = derived$1(workspace, ($w) => $w.project && $w.project.project_id ? String($w.project.project_id) : "");
    const wellName = derived$1(workspace, ($w) => $w.selectedWell && $w.selectedWell.name ? String($w.selectedWell.name) : "");
    $$renderer2.push(`<header class="h-(--header-height) group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height) flex shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear"><div class="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">`);
    Sidebar_trigger($$renderer2, { class: "-ms-1" });
    $$renderer2.push(`<!----> `);
    Separator($$renderer2, {
      orientation: "vertical",
      class: "mx-2 data-[orientation=vertical]:h-4"
    });
    $$renderer2.push(`<!----> <div><nav class="text-sm text-muted-foreground mb-1" aria-label="Breadcrumb"><a href="/" class="hover:underline">Home</a> <span class="mx-2">/</span> <a href="/projects" class="hover:underline">Projects</a> `);
    if (store_get($$store_subs ??= {}, "$projectName", projectName)) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<span class="mx-2">/</span> <a${attr("href", "/projects/" + store_get($$store_subs ??= {}, "$projectId", projectId))} class="hover:underline">${escape_html(store_get($$store_subs ??= {}, "$projectName", projectName))}</a>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (store_get($$store_subs ??= {}, "$wellName", wellName)) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<span class="mx-2 text-muted-foreground">/</span> <span class="text-muted-foreground">${escape_html(store_get($$store_subs ??= {}, "$wellName", wellName))}</span>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></nav> `);
    if (store_get($$store_subs ??= {}, "$subtitle", subtitle)) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-xs text-muted-foreground">${escape_html(store_get($$store_subs ??= {}, "$subtitle", subtitle))}</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="ms-auto flex items-center gap-2">`);
    Button($$renderer2, {
      href: "https://github.com/imranfadhil/quick_pp",
      variant: "ghost",
      size: "sm",
      class: "dark:text-foreground hidden sm:flex",
      target: "_blank",
      rel: "noopener noreferrer",
      children: ($$renderer3) => {
        $$renderer3.push(`<!---->GitHub`);
      },
      $$slots: { default: true }
    });
    $$renderer2.push(`<!----></div></div></header>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}

export { App_sidebar as A, Sidebar_provider as S, Sidebar_inset as a, Site_header as b };
//# sourceMappingURL=site-header-BBQTPgmw.js.map
