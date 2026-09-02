import { browser } from '$app/environment';
import { env } from '$env/dynamic/public';
import posthog from 'posthog-js';

// PostHog is the standard analytics layer (see AGENTS.md). No-ops when
// PUBLIC_POSTHOG_KEY is unset, so the template runs untouched without it.
// All projects share ONE PostHog project; events are segmented by the
// `app` super property (hostname by default).
export function initAnalytics() {
	const key = env.PUBLIC_POSTHOG_KEY;
	if (!browser || !key) return;
	posthog.init(key, {
		api_host: 'https://us.i.posthog.com',
		defaults: '2025-05-24', // history-change pageviews: SPA navs tracked for free
		autocapture: false // explicit events only - controls event burn + privacy surface
	});
	posthog.register({ app: env.PUBLIC_POSTHOG_APP ?? location.hostname });
}

export { posthog };
