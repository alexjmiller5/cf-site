# CLAUDE.md

Website on Cloudflare Workers with static assets: Svelte 5 frontend +
optional thin co-located API (server routes → the same Worker). This is the
template for every site, dashboard, and site-attached backend.

## Architecture rules

- **Backend logic that exists to serve this site lives HERE** as SvelteKit
  server routes (`+page.server.ts`, `src/routes/api/*/+server.ts`) — it all
  compiles into the one Worker. Do not create a separate backend for form
  handling, D1 reads, or thin API glue.
- Heavier Python work (AI pipelines, scraping, long jobs) does NOT belong
  here — that's Modal or the mac mini (see the `personal-infra` skill).
- Bindings (D1, R2, KV, cron triggers) are declared in `wrangler.jsonc` —
  that file IS the IaC. Access them via `platform.env` (typed in
  `worker-configuration.d.ts`; regenerate with `bun run gen`).
- Scheduled work attached to this site → [`triggers.crons`](https://developers.cloudflare.com/workers/configuration/cron-triggers/)
  in wrangler.jsonc (free) — though Modal cron is the house default for
  standalone jobs.
- Private site? Put Cloudflare Access in front (Google SSO for browsers,
  Service Tokens for machine callers). Never roll custom auth for
  personal-only apps.

## Stack

Bun (never npm) · SvelteKit + Svelte 5 runes · Tailwind v4 · vitest ·
prettier. Config note: there is no `svelte.config.js` — adapter and compiler
options live in `vite.config.ts` inside the `sveltekit()` plugin.

## UI conventions

- ALL design tokens (colors, fonts, spacing, radii) go in the `@theme` block
  in `src/routes/layout.css`. Components consume tokens, never raw values.
- Icons: heroicons.com ONLY — never emojis or generic unicode. Reference
  clone at `~/Desktop/coding/reference-repos/heroicons`.

## Commands

Standard verb set (see global CLAUDE.md) — the justfile is the interface,
not a script catalog; one-offs go in `scripts/` and run directly.

| Command | Purpose |
|---|---|
| `just dev` | Dev server (secrets injected via op) |
| `just test` | vitest |
| `just check` / `just fmt` | wrangler types + svelte-check + prettier / auto-fix |
| `just build` | Production build |
| `just logs` | `wrangler tail` on the deployed Worker |
| `just sync-secrets` | Push `.env.tpl` → Worker secrets |
| `just deploy` | test + build + `wrangler deploy` |

## TDD

Write the test first (`*.spec.ts` next to the code, or `src/**/*.svelte.spec.ts`
for components), then the code. Delete `src/lib/vitest-examples/` once real
tests exist.

## New-project checklist (delete this section after setup)

1. Rename `name` in `wrangler.jsonc` and `package.json`.
2. Fill `@theme` tokens in `src/routes/layout.css`.
3. Fill `.env.tpl` if the site needs secrets; `just sync-secrets`.
4. Custom domain / D1 / R2: add to `wrangler.jsonc`, then `bun run gen`.
5. CI: `gh secret set OP_SERVICE_ACCOUNT_TOKEN --body "$(op read 'op://Personal/op-service-account-personal-infra/token')"`.
6. If private: enable Cloudflare Access on the domain (document the click-ops in README).
