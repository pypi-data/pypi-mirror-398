export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    let assetPath = url.pathname;

    // Serve index.html for the root path
    if (assetPath === '/' || assetPath === '') {
      assetPath = '/index.html';
    }

    // Create a new URL for the asset
    const assetUrl = new URL(assetPath, url.origin);
    const assetRequest = new Request(assetUrl, request);

    // Fetch from the static assets binding
    const response = await env.ASSETS.fetch(assetRequest);

    // Add CORS headers for the JSON API
    if (assetPath.endsWith('.json')) {
      const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      };

      return new Response(response.body, {
        status: response.status,
        headers: { ...Object.fromEntries(response.headers), ...corsHeaders },
      });
    }

    return response;
  },
};
