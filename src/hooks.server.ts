import { dev } from '$app/environment';
import { redirect, type Handle } from '@sveltejs/kit';

// http → https at the Worker, so it holds on any domain with no zone config.
// (Cloudflare's "Always Use HTTPS" zone setting is off by default.)
export const handle: Handle = async ({ event, resolve }) => {
	const url = event.url;
	if (!dev && url.protocol === 'http:') {
		redirect(301, `https://${url.host}${url.pathname}${url.search}`);
	}
	return resolve(event);
};
