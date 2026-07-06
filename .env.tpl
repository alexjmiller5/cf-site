# Canonical secrets manifest — op:// references only, SAFE to commit.
# Most sites have zero-to-few secrets; Worker bindings (D1, R2, KV) are NOT
# secrets — they go in wrangler.jsonc.
# Local dev:      op run --env-file=.env.tpl -- bun run dev
# Push to CF:     just sync-secrets
#
# CHANGEME — one line per secret, e.g.:
# RESEND_API_KEY=op://personal-infra/resend/credential
