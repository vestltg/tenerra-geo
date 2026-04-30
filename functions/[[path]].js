const SITE_URL = 'https://tenerra.ai';
const OAUTH_ISSUER = `${SITE_URL}/.well-known/openid-configuration`;

const DISCOVERY_LINK_HEADER = [
  '</.well-known/api-catalog>; rel="api-catalog"',
  '</docs/api>; rel="service-doc"',
  '</.well-known/agent-skills/index.json>; rel="agent-skills"',
  '</.well-known/mcp/server-card.json>; rel="mcp-server-card"',
  '</.well-known/openid-configuration>; rel="openid-configuration"',
  '</.well-known/oauth-protected-resource>; rel="oauth-protected-resource"'
].join(', ');

const MARKDOWN_PAGES = {
  '/': [
    '# Tenerra — Built for What Lasts',
    '',
    'Tenerra is home to ANYA — continuity infrastructure for families of individuals with intellectual and developmental disabilities.',
    '',
    '## Our work',
    '',
    '- **ANYA**: A Human Continuity Operating System for special needs families.',
    '- Product site: https://anya.tenerra.ai',
    '',
    '## About',
    '',
    'Vest Life, Inc. builds Tenerra and ANYA from decades of special-needs legal and family continuity experience.'
  ].join('\n'),
  '/privacy': [
    '# Privacy Policy — Tenerra',
    '',
    'Read the complete policy at https://tenerra.ai/privacy.html.'
  ].join('\n'),
  '/tos': [
    '# Terms of Service — Tenerra',
    '',
    'Read the complete terms at https://tenerra.ai/tos.html.'
  ].join('\n')
};

const OPENAPI_DOCUMENT = {
  openapi: '3.1.0',
  info: {
    title: 'Tenerra Public API',
    version: '1.0.0',
    description: 'Public discovery endpoints for Tenerra.'
  },
  paths: {
    '/health': {
      get: {
        summary: 'Health status',
        responses: {
          '200': {
            description: 'OK'
          }
        }
      }
    }
  }
};

const API_CATALOG = {
  linkset: [
    {
      anchor: SITE_URL,
      'service-desc': [
        {
          href: `${SITE_URL}/openapi.json`,
          type: 'application/vnd.oai.openapi+json;version=3.1'
        }
      ],
      'service-doc': [
        {
          href: `${SITE_URL}/docs/api`,
          type: 'text/markdown'
        }
      ],
      status: [
        {
          href: `${SITE_URL}/health`,
          type: 'application/health+json'
        }
      ]
    }
  ]
};

const OPENID_CONFIGURATION = {
  issuer: OAUTH_ISSUER,
  authorization_endpoint: `${SITE_URL}/oauth/authorize`,
  token_endpoint: `${SITE_URL}/oauth/token`,
  jwks_uri: `${SITE_URL}/oauth/jwks.json`,
  grant_types_supported: ['authorization_code', 'refresh_token', 'client_credentials'],
  response_types_supported: ['code'],
  token_endpoint_auth_methods_supported: ['client_secret_post']
};

const OAUTH_AUTHORIZATION_SERVER = OPENID_CONFIGURATION;

const OAUTH_PROTECTED_RESOURCE = {
  resource: SITE_URL,
  authorization_servers: [OAUTH_ISSUER],
  scopes_supported: ['profile.read', 'continuity.read']
};

const MCP_SERVER_CARD = {
  serverInfo: {
    name: 'Tenerra Web MCP',
    version: '1.0.0'
  },
  transport: {
    type: 'webmcp',
    url: `${SITE_URL}/`
  },
  capabilities: {
    tools: {
      listChanged: false
    }
  }
};

function normalizePath(pathname) {
  if (pathname === '/index.html') return '/';
  if (pathname.endsWith('.html')) return pathname.slice(0, -5);
  return pathname;
}

function withDiscoveryHeaders(response, pathname) {
  const headers = new Headers(response.headers);
  if (pathname === '/' || pathname === '/index.html') {
    headers.set('Link', DISCOVERY_LINK_HEADER);
  }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers
  });
}

function markdownResponse(markdown, isHead) {
  // Approximate token count using 4 chars/token; this is a rough heuristic and can vary by tokenizer and non-ASCII content.
  const estimatedTokens = Math.ceil(markdown.length / 4);
  return new Response(isHead ? null : markdown, {
    headers: {
      'content-type': 'text/markdown; charset=utf-8',
      'x-markdown-tokens': String(estimatedTokens),
      Link: DISCOVERY_LINK_HEADER
    }
  });
}

function jsonResponse(payload, contentType) {
  return new Response(JSON.stringify(payload, null, 2), {
    headers: {
      'content-type': contentType
    }
  });
}

export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const pathname = url.pathname;
  const method = request.method;
  const isHead = method === 'HEAD';

  if (method !== 'GET' && !isHead) {
    return env.ASSETS.fetch(request);
  }

  switch (pathname) {
    case '/health':
      return jsonResponse({ status: 'ok' }, 'application/health+json; charset=utf-8');
    case '/openapi.json':
      return jsonResponse(OPENAPI_DOCUMENT, 'application/vnd.oai.openapi+json; charset=utf-8');
    case '/docs/api':
      return markdownResponse(
        '# Tenerra API Documentation\n\n- OpenAPI: https://tenerra.ai/openapi.json\n- Health: https://tenerra.ai/health\n',
        isHead
      );
    case '/.well-known/api-catalog':
      return jsonResponse(API_CATALOG, 'application/linkset+json; charset=utf-8');
    case '/.well-known/openid-configuration':
      return jsonResponse(OPENID_CONFIGURATION, 'application/json; charset=utf-8');
    case '/.well-known/oauth-authorization-server':
      return jsonResponse(OAUTH_AUTHORIZATION_SERVER, 'application/json; charset=utf-8');
    case '/.well-known/oauth-protected-resource':
      return jsonResponse(OAUTH_PROTECTED_RESOURCE, 'application/json; charset=utf-8');
    case '/.well-known/mcp/server-card.json':
      return jsonResponse(MCP_SERVER_CARD, 'application/json; charset=utf-8');
    default:
      break;
  }

  const normalizedPath = normalizePath(pathname);
  const wantsMarkdown = request.headers.get('accept')?.includes('text/markdown');
  if (wantsMarkdown && MARKDOWN_PAGES[normalizedPath]) {
    return markdownResponse(MARKDOWN_PAGES[normalizedPath], isHead);
  }

  let assetRequest = request;
  const hasHtmlFallback = normalizedPath !== '/' && Boolean(MARKDOWN_PAGES[normalizedPath]);
  if (hasHtmlFallback && pathname === normalizedPath) {
    const htmlUrl = new URL(request.url);
    htmlUrl.pathname = `${normalizedPath}.html`;
    assetRequest = new Request(htmlUrl, request);
  }

  const assetResponse = await env.ASSETS.fetch(assetRequest);
  return withDiscoveryHeaders(assetResponse, pathname);
}
