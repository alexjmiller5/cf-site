import { describe, expect, it } from 'vitest';
import pkg from '../../package.json';
import { APP_VERSION } from './version';

describe('APP_VERSION', () => {
	it('is the package.json version, the single version source', () => {
		expect(APP_VERSION).toBe(pkg.version);
	});
});
