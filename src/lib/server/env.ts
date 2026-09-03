import { env } from '$env/dynamic/private';

/**
 * Read a runtime secret. Goes through $env/dynamic/private on purpose: in dev
 * that is the process env (so `just dev` = `op run --env-file=.env.tpl` works),
 * and in production the adapter feeds the Worker's secret bindings into the
 * same module. `platform.env` is NOT a substitute - in dev it only sees
 * .dev.vars and wrangler `vars`, never the process env, so code that reads
 * secrets off it silently gets undefined under op run.
 *
 * Throws on a missing value so the failure is a clear 500 at the call site
 * rather than a baffling error from whatever upstream API got an empty key.
 */
export function requireSecret(name: string): string {
	const value = env[name];
	if (!value) throw new Error(`Missing required secret ${name}`);
	return value;
}
