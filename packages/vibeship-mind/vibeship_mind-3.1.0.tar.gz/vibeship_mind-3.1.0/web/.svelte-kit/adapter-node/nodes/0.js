import * as universal from '../entries/pages/_layout.ts.js';

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/+layout.ts";
export const imports = ["_app/immutable/nodes/0.C2qcwI0N.js","_app/immutable/chunks/C0qsFOe6.js","_app/immutable/chunks/Bv5Gvc1d.js","_app/immutable/chunks/QxQV3Xij.js"];
export const stylesheets = ["_app/immutable/assets/0.D5TC0whB.css"];
export const fonts = [];
