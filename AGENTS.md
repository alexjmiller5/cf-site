# AGENTS.md

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
- Icons: Tabler ONLY, via `@tabler/icons-svelte` (already a dependency; browse
  at tabler.io/icons or icones.js.org) — never emojis or generic unicode.
  Import as components: `import { IconChevronRight } from '@tabler/icons-svelte'`.
  shadcn-svelte components render Lucide internally (`@lucide/svelte` stays a
  dependency for that) — same 24px/2px visual language, so the UI still reads
  as one icon set. Full standard in the global `icons` skill.

## Site basics (SEO, titles, favicon, https)

- **Every route sets `<title>` + `<meta name="description">`** in
  `<svelte:head>` (pattern in `src/routes/+page.svelte`). Titles live on
  pages, not the layout - a layout title duplicates when a page adds its own.
- **Favicon: purpose-driven, never empty, never stock.** Replace
  `src/lib/assets/favicon.svg` (keep SVG; it's wired in `+layout.svelte`)
  with an icon that depicts THIS site specifically - its subject + function
  together, e.g. a ticket tracker for the ACL festival gets the ACL logo
  merged with a ticket glyph, not a bare ticket. The global `icons` skill is
  raw material (glyphs to compose, recolor, overlay into one SVG), never the
  finished favicon on its own. Shipping the template default or a blank
  favicon to prod is a bug - the browser tab is the site's smallest logo,
  treat it like one.
- **`static/robots.txt`** ships allow-all; **`static/llms.txt`** describes
  the site for LLM crawlers - fill its CHANGEMEs alongside the titles.
- **http → https** is a 301 in `src/hooks.server.ts` (skipped in dev) - works
  on any domain with zero zone config. Zone-level HSTS, if a site wants it,
  follows the `scripts/cf-*.py` convention above.

## Form abuse ladder

Public forms get defenses in this order, stopping at the first level that
holds (pattern proven on WTW - its historical bot spam died at level 3):

1. **Honeypot field** - off-screen input; bots fill it, handler fakes success.
2. **Per-IP rate limit** - Workers rate-limiting binding in `wrangler.jsonc`;
   caps email-relay/D1 abuse. Free, no zone config.
3. **Semantic validation** - server-side checks only a human passes (known
   event names, ASCII folding, field plausibility).
4. **Cloudflare Turnstile (managed mode)** - not baked into this template.
   When scaffolding a site with a public form, OFFER it to Alex and lay out
   the tradeoffs for THIS site: what the form triggers (email relay, D1
   writes, paid APIs, reputational spam) and how costly/abusable that is,
   versus what Turnstile costs here - a per-hostname widget registration
   (account-level, not wrangler - needs a `scripts/cf-turnstile.py`
   provisioner), a secret per site, a third-party script, and a nonzero
   real-human block rate. Lean toward levels 1-3 alone for low-stakes forms;
   lean toward adding Turnstile when side effects are expensive or abuse is
   expected. Dev/test uses Cloudflare's dummy keys, so no widget needed
   locally.

## Commands

Standard verb set (see global AGENTS.md) — the justfile is the interface,
not a script catalog; one-offs go in `scripts/` and run directly.

| Command                   | Purpose                                                        |
| ------------------------- | -------------------------------------------------------------- |
| `just dev`                | Dev server (secrets injected via op)                           |
| `just test`               | vitest                                                         |
| `just check` / `just fmt` | wrangler types + svelte-check + prettier / auto-fix            |
| `just build`              | Production build                                               |
| `just logs`               | `wrangler tail` on the deployed Worker                         |
| `just sync-secrets`       | Push `.env.tpl` → Worker secrets                               |
| `just deploy`             | test + build + `wrangler deploy` — CI's job, not yours (below) |

**Deploying = commit + push to `main`.** The GHA deploy workflow runs tests,
syncs secrets, and deploys — never run `just deploy` locally unless there's a
legitimate stated reason (e.g. CI itself is broken): local deploys ship code
that isn't in git, and the next push silently reverts it. After pushing,
verify the run with the gh CLI (`gh run watch <id> --exit-status`; on failure
`gh run view <id> --log-failed`) — never assume the deploy succeeded.

## TDD

Write the test first (`*.spec.ts` next to the code, or `src/**/*.svelte.spec.ts`
for components), then the code. Delete `src/lib/vitest-examples/` once real
tests exist.

## New-project checklist (delete this section after setup)

1. Rename `name` in `wrangler.jsonc` and `package.json`.
2. Fill `@theme` tokens in `src/routes/layout.css`; adjust the shadcn-svelte
   `:root`/`.dark` variables there if the project needs its own palette.
3. Site basics: page `<title>`/description CHANGEMEs, `static/llms.txt`,
   and a purpose-driven favicon (see "Site basics" above - compose one for
   this site; never ship the template default).
4. Fill `.env.tpl` if the site needs secrets; `just sync-secrets`.
5. Custom domain / D1 / R2: add to `wrangler.jsonc`, then `bun run gen`.
6. Vault + CI: Alex runs `op-project-bootstrap .env.tpl --repo <owner/name>` — creates the project vault, the `<Project> ENV` item, the read-only CI SA, and sets the repo's `OP_SERVICE_ACCOUNT_TOKEN`.
7. If private: enable Cloudflare Access on the domain (document the click-ops in README).

## Hardcoded owner assumptions

The code is generic, but the workflow is wired to Alex's setup for
convenience: secrets flow through his 1Password (`.env.tpl` with `op://`
references; `op-project-bootstrap` is his private bootstrap script) and
deploys target his Cloudflare account.
