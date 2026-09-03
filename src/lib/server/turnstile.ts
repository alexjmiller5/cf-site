// Server-side Cloudflare Turnstile verification - the canonical helper;
// never hand-roll another. Call at the TOP of any form action whose form
// renders the <Turnstile> component, before any other validation:
//
//   const ok = await verifyTurnstile(
//     form.get('cf-turnstile-response'),
//     requireSecret('TURNSTILE_SECRET_KEY'),   // $lib/server/env - never platform.env
//     request.headers.get('cf-connecting-ip')
//   );
//   if (!ok) return fail(403, { error: 'Verification failed - please retry.' });
//
// Dev/test: secret '1x0000000000000000000000000000000AA' always passes
// (pairs with the component's dummy sitekey); '2x...AA' always fails.
export async function verifyTurnstile(
	token: FormDataEntryValue | null | undefined,
	secret: string,
	remoteip?: string | null
): Promise<boolean> {
	if (typeof token !== 'string' || token === '') return false;
	const res = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
		method: 'POST',
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify({ secret, response: token, ...(remoteip ? { remoteip } : {}) })
	});
	if (!res.ok) return false;
	const outcome = (await res.json()) as { success?: boolean };
	return outcome.success === true;
}
