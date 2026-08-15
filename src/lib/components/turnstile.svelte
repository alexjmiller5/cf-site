<script lang="ts">
	// Cloudflare Turnstile widget (managed mode) - THE canonical
	// implementation; never hand-roll another. Place inside a <form>; it
	// injects a hidden `cf-turnstile-response` field into the POST, which the
	// form action verifies via $lib/server/turnstile.
	//
	// Pass the site's real sitekey (PUBLIC_TURNSTILE_SITE_KEY, minted by
	// scripts/cf-turnstile.py). The default is Cloudflare's always-pass dummy
	// key, so dev/test needs no widget registration.
	let { sitekey = '1x00000000000000000000AA' }: { sitekey?: string } = $props();
</script>

<svelte:head>
	<script src="https://challenges.cloudflare.com/turnstile/api/v0/api.js" async defer></script>
</svelte:head>

<div class="cf-turnstile" data-sitekey={sitekey}></div>
