<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { initAnalytics } from '$lib/analytics';
	import { onMount } from 'svelte';
	import { APP_VERSION } from '$lib/version';

	let { children } = $props();
	onMount(initAnalytics);
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
{@render children()}
<span
	class="pointer-events-none fixed right-2 bottom-1 text-[10px] text-muted-foreground/60 select-none"
	aria-label="Version {APP_VERSION}">v{APP_VERSION}</span
>
