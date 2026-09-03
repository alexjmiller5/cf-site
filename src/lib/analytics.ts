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
		defaults: '2025-05-24',
		// Both of the below are set explicitly rather than left to the preset.
		// Observed on my-supplementals (posthog-js 1.426): the preset alone
		// recorded $pageleave but no $pageview, and it silently switched ON
		// session replay + dead-click capture - which records what users type and
		// read, well past "explicit events only" and past what a site's privacy
		// policy usually claims. Don't drop these when bumping the preset date.
		capture_pageview: 'history_change', // SPA navs count as pageviews
		disable_session_recording: true,
		capture_dead_clicks: false,
		autocapture: false // explicit events only - controls event burn + privacy surface
	});
}

export { posthog };
