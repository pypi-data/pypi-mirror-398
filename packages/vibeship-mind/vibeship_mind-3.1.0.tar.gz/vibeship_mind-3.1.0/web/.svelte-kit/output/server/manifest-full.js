export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set(["logo.png","robots.txt"]),
	mimeTypes: {".png":"image/png",".txt":"text/plain"},
	_: {
		client: {start:"_app/immutable/entry/start.fhmDZwET.js",app:"_app/immutable/entry/app.DkyP7Mv7.js",imports:["_app/immutable/entry/start.fhmDZwET.js","_app/immutable/chunks/zlp-wkp4.js","_app/immutable/chunks/Bv5Gvc1d.js","_app/immutable/chunks/BrbQ73kd.js","_app/immutable/entry/app.DkyP7Mv7.js","_app/immutable/chunks/Bv5Gvc1d.js","_app/immutable/chunks/BMalaSs_.js","_app/immutable/chunks/C0qsFOe6.js","_app/immutable/chunks/BrbQ73kd.js","_app/immutable/chunks/QxQV3Xij.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js')),
			__memo(() => import('./nodes/3.js'))
		],
		remotes: {
			
		},
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			},
			{
				id: "/get-started",
				pattern: /^\/get-started\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 3 },
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
