import { afterEach, describe, expect, it, vi } from 'vitest';
import { verifyTurnstile } from './turnstile';

const mockFetch = (body: unknown, ok = true) => {
	const fn = vi.fn(async () => ({ ok, json: async () => body }));
	vi.stubGlobal('fetch', fn);
	return fn;
};

describe('verifyTurnstile', () => {
	afterEach(() => vi.unstubAllGlobals());

	it('accepts a valid token', async () => {
		mockFetch({ success: true });
		expect(await verifyTurnstile('tok', 'secret')).toBe(true);
	});

	it('rejects a failed challenge', async () => {
		mockFetch({ success: false });
		expect(await verifyTurnstile('tok', 'secret')).toBe(false);
	});

	it('rejects missing/empty tokens without calling siteverify', async () => {
		const f = mockFetch({ success: true });
		expect(await verifyTurnstile(null, 'secret')).toBe(false);
		expect(await verifyTurnstile('', 'secret')).toBe(false);
		expect(f).not.toHaveBeenCalled();
	});

	it('rejects on non-OK siteverify responses', async () => {
		mockFetch({}, false);
		expect(await verifyTurnstile('tok', 'secret')).toBe(false);
	});
});
