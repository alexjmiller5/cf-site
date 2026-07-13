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
- **Zone/edge config that wrangler DOESN'T manage — HSTS, WAF/rate-limit
  rules, DNS records, Access policies — is declarative-via-SCRIPTS, never
  Terraform.** When a site needs one, add an idempotent `scripts/cf-*.py`
  (reads the CF API token + zone id from 1Password, PUT/PATCHes the setting)
  plus a `just cf-*` recipe. The script IS the declarative source of truth —
  the intended settings read straight off it. Terraform is overkill for
  Cloudflare and drags back state files. Don't scaffold this until a site
  actually needs it. (See the `personal-infra` skill.)
- Scheduled work attached to this site → [`triggers.crons`](https://developers.cloudflare.com/workers/configuration/cron-triggers/)
  in wrangler.jsonc (free) — though Modal cron is the house default for
  standalone jobs.
- Private site? Put Cloudflare Access in front (login via the Cloudflare
  identity provider — sign in with the Cloudflare account, the zero-setup
  default IdP; session duration 1 month; Service Tokens for machine
  callers). Never roll custom auth for personal-only apps.
  - If it's also a homescreen PWA: manifest + apple-touch-icon are fetched
    WITHOUT cookies — see the personal-infra skill's PWA-behind-Access
    pattern (manifest `crossorigin="use-credentials"` + a Bypass Access app
    for the asset paths), or the icon degrades to a letter monogram.

## Stack

Bun (never npm) · SvelteKit + Svelte 5 runes · Tailwind v4 ·
shadcn-svelte (+ bits-ui) · vitest · prettier. Config note: there is no `svelte.config.js` — adapter and compiler
options live in `vite.config.ts` inside the `sveltekit()` plugin.

## UI conventions

- **Components: shadcn-svelte** (styled copy-paste over the Bits UI headless
  layer). The core set lives in `src/lib/components/ui/` — that code is OURS:
  edit it freely, restyle it, never treat it as a vendored dependency. Add
  more with `bunx shadcn-svelte@latest add <component>` (config in
  `components.json`; zinc base, `nova` style). Behavior/a11y fixes arrive via
  `bun update bits-ui` — the styling layer never auto-updates.
- ALL design tokens (colors, fonts, spacing, radii) go in the `@theme` block
  in `src/routes/layout.css`. Components consume tokens, never raw values.
  shadcn-svelte's semantic tokens (`--primary`, `--radius`, …) are defined in
  the `:root`/`.dark` blocks there — retheme a project by editing those, not
  the component files.
- Icons: Lucide ONLY, via `@lucide/svelte` (already a dependency; browse at
  lucide.dev) — never emojis or generic unicode. Import as components:
  `import { ChevronRight } from '@lucide/svelte'`. Same set the shadcn-svelte
  components use internally, so the whole UI shares one icon language.

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
2. Fill `@theme` tokens in `src/routes/layout.css`; adjust the shadcn-svelte
   `:root`/`.dark` variables there if the project needs its own palette.
3. Fill `.env.tpl` if the site needs secrets; `just sync-secrets`.
4. Custom domain / D1 / R2: add to `wrangler.jsonc`, then `bun run gen`.
5. CI: `gh secret set OP_SERVICE_ACCOUNT_TOKEN --body "$(op read 'op://Personal/<project>-ci SA Token/token')"`.
6. If private: enable Cloudflare Access on the domain (document the click-ops in README).
