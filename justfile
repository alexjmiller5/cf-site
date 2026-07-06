set shell := ["bash", "-cu"]

default:
    @just --list

# Dev server (secrets injected if .env.tpl has any)
dev:
    op run --env-file=.env.tpl -- bun run dev

test:
    bun run test

# Type-check + svelte-check
check:
    bun run check

build:
    bun run build

# Push .env.tpl secrets to the Worker (no plaintext touches disk)
sync-secrets:
    op inject -i .env.tpl | grep -v '^#' | grep . | while IFS='=' read -r k v; do echo -n "$v" | bunx wrangler secret put "$k"; done

# Build + deploy to Cloudflare
deploy: test build
    bunx wrangler deploy
