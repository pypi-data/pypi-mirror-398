const load = async ({ params }) => {
  const projectId = params.project_id ?? null;
  const wellId = params.well_id ? decodeURIComponent(params.well_id) : null;
  return { projectId, wellId };
};

var _layout_ts = /*#__PURE__*/Object.freeze({
  __proto__: null,
  load: load
});

const index = 3;
let component_cache;
const component = async () => component_cache ??= (await import('./_layout.svelte-BQ4eqa3m.js')).default;
const universal_id = "src/routes/wells/+layout.ts";
const imports = ["_app/immutable/nodes/3.DCbU_py2.js","_app/immutable/chunks/Cjo0f8hx.js","_app/immutable/chunks/BNO5OzLn.js","_app/immutable/chunks/BJMC0GYJ.js","_app/immutable/chunks/BFWBm77v.js","_app/immutable/chunks/CHHNy2JR.js","_app/immutable/chunks/CZmdasm_.js"];
const stylesheets = ["_app/immutable/assets/vendor.S5W4ZllZ.css"];
const fonts = [];

export { component, fonts, imports, index, stylesheets, _layout_ts as universal, universal_id };
//# sourceMappingURL=3-auNQhq9k.js.map
