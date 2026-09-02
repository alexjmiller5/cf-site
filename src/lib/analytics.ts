import { browser } from '$app/environment';
import { env } from '$env/dynamic/public';
import posthog from 'posthog-js';

// PostHog is the standard analytics layer (see AGENTS.md). No-ops when
// PUBLIC_POSTHOG_KEY is unset, so the template runs untouched without it.
// Each app gets its OWN PostHog project (created at scaffold time).
export function initAnalytics() {
	const key = env.PUBLIC_POSTHOG_KEY;
	if (!browser || !key) return;
	posthog.init(key, {
		api_host: 'https://us.i.posthog.com',
		defaults: '2025-05-24', // history-change pageviews: SPA navs tracked for free
		autocapture: false // explicit events only - controls event burn + privacy surface
	});
}

export { posthog };
