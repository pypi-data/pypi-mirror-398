const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set(["robots.txt"]),
	mimeTypes: {".txt":"text/plain"},
	_: {
		client: {start:"_app/immutable/entry/start.DQiViigm.js",app:"_app/immutable/entry/app.D42B-Mir.js",imports:["_app/immutable/entry/start.DQiViigm.js","_app/immutable/chunks/Cjo0f8hx.js","_app/immutable/chunks/BNO5OzLn.js","_app/immutable/chunks/BJMC0GYJ.js","_app/immutable/entry/app.D42B-Mir.js","_app/immutable/chunks/PPVm8Dsz.js","_app/immutable/chunks/Cjo0f8hx.js","_app/immutable/chunks/BNO5OzLn.js","_app/immutable/chunks/BJMC0GYJ.js"],stylesheets:["_app/immutable/assets/vendor.S5W4ZllZ.css","_app/immutable/assets/vendor.S5W4ZllZ.css"],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('./chunks/0-BDI6Dkov.js')),
			__memo(() => import('./chunks/1-DrQtFEOH.js')),
			__memo(() => import('./chunks/2-HIkiKw3q.js')),
			__memo(() => import('./chunks/3-auNQhq9k.js')),
			__memo(() => import('./chunks/4-D_CGxrmh.js')),
			__memo(() => import('./chunks/5-CQbwQuKM.js')),
			__memo(() => import('./chunks/6-BVvNDoQZ.js')),
			__memo(() => import('./chunks/7-BldxkpeB.js')),
			__memo(() => import('./chunks/8-CnyJQpNc.js')),
			__memo(() => import('./chunks/9-COsUVmDk.js')),
			__memo(() => import('./chunks/10-DFBL7Sao.js')),
			__memo(() => import('./chunks/11-J4tDnH6M.js')),
			__memo(() => import('./chunks/12-LUeBIboV.js')),
			__memo(() => import('./chunks/13-BXQYWUgn.js')),
			__memo(() => import('./chunks/14-ByEWLF2F.js')),
			__memo(() => import('./chunks/15-D-BCzJoD.js')),
			__memo(() => import('./chunks/16-DFPHmfpi.js')),
			__memo(() => import('./chunks/17-D4zYmJJ3.js')),
			__memo(() => import('./chunks/18-ylmr8nFt.js'))
		],
		remotes: {
			
		},
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 4 },
				endpoint: null
			},
			{
				id: "/login",
				pattern: /^\/login\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 5 },
				endpoint: null
			},
			{
				id: "/projects",
				pattern: /^\/projects\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 6 },
				endpoint: null
			},
			{
				id: "/projects/[project_id]",
				pattern: /^\/projects\/([^/]+?)\/?$/,
				params: [{"name":"project_id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,2,], errors: [1,,], leaf: 7 },
				endpoint: null
			},
			{
				id: "/projects/[project_id]/perm-transform",
				pattern: /^\/projects\/([^/]+?)\/perm-transform\/?$/,
				params: [{"name":"project_id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,2,], errors: [1,,], leaf: 8 },
				endpoint: null
			},
			{
				id: "/projects/[project_id]/rock-typing",
				pattern: /^\/projects\/([^/]+?)\/rock-typing\/?$/,
				params: [{"name":"project_id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,2,], errors: [1,,], leaf: 9 },
				endpoint: null
			},
			{
				id: "/projects/[project_id]/shf",
				pattern: /^\/projects\/([^/]+?)\/shf\/?$/,
				params: [{"name":"project_id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,2,], errors: [1,,], leaf: 10 },
				endpoint: null
			},
			{
				id: "/wells",
				pattern: /^\/wells\/?$/,
				params: [],
				page: { layouts: [0,3,], errors: [1,,], leaf: 11 },
				endpoint: null
			},
			{
				id: "/wells/[project_id]",
				pattern: /^\/wells\/([^/]+?)\/?$/,
				params: [{"name":"project_id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,3,], errors: [1,,], leaf: 12 },
				endpoint: null
			},
			{
				id: "/wells/[project_id]/[well_id]",
				pattern: /^\/wells\/([^/]+?)\/([^/]+?)\/?$/,
				params: [{"name":"project_id","optional":false,"rest":false,"chained":false},{"name":"well_id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,3,], errors: [1,,], leaf: 13 },
				endpoint: null
			},
			{
				id: "/wells/[project_id]/[well_id]/data",
				pattern: /^\/wells\/([^/]+?)\/([^/]+?)\/data\/?$/,
				params: [{"name":"project_id","optional":false,"rest":false,"chained":false},{"name":"well_id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,3,], errors: [1,,], leaf: 14 },
				endpoint: null
			},
			{
				id: "/wells/[project_id]/[well_id]/litho-poro",
				pattern: /^\/wells\/([^/]+?)\/([^/]+?)\/litho-poro\/?$/,
				params: [{"name":"project_id","optional":false,"rest":false,"chained":false},{"name":"well_id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,3,], errors: [1,,], leaf: 15 },
				endpoint: null
			},
			{
				id: "/wells/[project_id]/[well_id]/perm",
				pattern: /^\/wells\/([^/]+?)\/([^/]+?)\/perm\/?$/,
				params: [{"name":"project_id","optional":false,"rest":false,"chained":false},{"name":"well_id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,3,], errors: [1,,], leaf: 16 },
				endpoint: null
			},
			{
				id: "/wells/[project_id]/[well_id]/ressum",
				pattern: /^\/wells\/([^/]+?)\/([^/]+?)\/ressum\/?$/,
				params: [{"name":"project_id","optional":false,"rest":false,"chained":false},{"name":"well_id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,3,], errors: [1,,], leaf: 17 },
				endpoint: null
			},
			{
				id: "/wells/[project_id]/[well_id]/saturation",
				pattern: /^\/wells\/([^/]+?)\/([^/]+?)\/saturation\/?$/,
				params: [{"name":"project_id","optional":false,"rest":false,"chained":false},{"name":"well_id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,3,], errors: [1,,], leaf: 18 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();

const prerendered = new Set([]);

const base = "";

export { base, manifest, prerendered };
//# sourceMappingURL=manifest.js.map
