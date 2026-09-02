<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { initAnalytics } from '$lib/analytics';
	import { onMount } from 'svelte';

	let { children } = $props();
	onMount(initAnalytics);
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
{@render children()}
