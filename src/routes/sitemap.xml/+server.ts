// Content sites: list every public route here and uncomment the Sitemap line
// in static/robots.txt. Dashboards / personal tools: delete this directory.
const routes = ['/'];

export const GET = ({ url }: { url: URL }) => {
	const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${routes.map((path) => `\t<url><loc>${url.origin}${path}</loc></url>`).join('\n')}
</urlset>`;
	return new Response(body, { headers: { 'content-type': 'application/xml' } });
};
