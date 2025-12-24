# OAuth & Claude.ai Integration

pymssql-mcp supports OAuth 2.0 authentication for secure deployment as a Claude.ai Integration (Custom Connector). This allows your team to access your SQL Server database directly from Claude.ai with enterprise-grade authentication via your identity provider.

## Overview

When deployed with OAuth enabled, pymssql-mcp acts as both:
- An **OAuth Authorization Server** - Handles client registration and token issuance for Claude.ai
- An **OAuth Client** - Delegates user authentication to your identity provider (Duo, Auth0, etc.)

```
┌──────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌────────────────┐
│  Claude.ai   │────►│   pymssql-mcp   │────►│  Identity       │────►│  SQL Server    │
│  (Browser)   │◄────│  (OAuth + MCP)  │◄────│  Provider       │     │                │
└──────────────┘     └─────────────────┘     │  (Duo/Auth0)    │     └────────────────┘
                                             └─────────────────┘
```

### Authentication Flow

1. User enables the pymssql-mcp connector in Claude.ai
2. Claude.ai discovers OAuth endpoints via `/.well-known/oauth-authorization-server`
3. Claude.ai registers as a client via Dynamic Client Registration (DCR)
4. User is redirected to your identity provider (Duo, Auth0, etc.) to authenticate
5. After successful authentication, tokens are issued to Claude.ai
6. Claude.ai can now make authenticated MCP requests

## Supported Identity Providers

### Cisco Duo

Duo provides enterprise MFA and SSO. pymssql-mcp has built-in support for Duo's OIDC implementation.

**Requirements:**
- Duo Admin account
- "OIDC Relying Party" or "Generic OIDC" application in Duo

### Auth0

Auth0 is a flexible identity platform supporting various authentication methods.

**Requirements:**
- Auth0 tenant
- "Regular Web Application" configured

### Generic OIDC

Any OpenID Connect compliant provider can be used, including:
- Okta
- Azure AD / Entra ID
- Google Workspace
- Keycloak
- Custom OIDC providers

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MSSQL_AUTH_ENABLED` | Enable OAuth authentication | Yes (set to `true`) |
| `MSSQL_AUTH_ISSUER_URL` | Public URL of your pymssql-mcp server | Yes |
| `MSSQL_IDP_PROVIDER` | Identity provider type: `duo`, `auth0`, or `oidc` | Yes |
| `MSSQL_IDP_DISCOVERY_URL` | OIDC discovery URL (`.well-known/openid-configuration`) | Yes |
| `MSSQL_IDP_CLIENT_ID` | Client ID from your IdP | Yes |
| `MSSQL_IDP_CLIENT_SECRET` | Client secret from your IdP | Yes |
| `MSSQL_IDP_SCOPES` | Scopes to request from IdP | No (default: `openid profile email groups`) |
| `MSSQL_TOKEN_EXPIRY_SECONDS` | Access token lifetime | No (default: `3600`) |
| `MSSQL_REFRESH_TOKEN_EXPIRY_SECONDS` | Refresh token lifetime | No (default: `2592000`) |

### Duo-Specific Settings

| Variable | Description |
|----------|-------------|
| `MSSQL_DUO_API_HOST` | Duo API hostname (alternative to discovery URL) |

## Setup Guide

### Step 1: Deploy pymssql-mcp Server

Deploy pymssql-mcp on a server accessible from the internet with HTTPS:

```bash
# Install pymssql-mcp
pip install pymssql-mcp

# Configure database connection
export MSSQL_HOST=your-sql-server
export MSSQL_USER=username
export MSSQL_PASSWORD=password
export MSSQL_DATABASE=your-database

# Start in streamable HTTP mode
pymssql-mcp --streamable-http --host 0.0.0.0 --port 8080
```

For production, use a process manager like systemd:

```ini
[Unit]
Description=pymssql-mcp Server
After=network.target

[Service]
Type=simple
User=pymssql-mcp
WorkingDirectory=/opt/pymssql-mcp
EnvironmentFile=/opt/pymssql-mcp/.env
ExecStart=/opt/pymssql-mcp/venv/bin/pymssql-mcp --streamable-http --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 2: Configure HTTPS

pymssql-mcp should be behind a reverse proxy or load balancer that handles TLS termination:

**Example nginx configuration:**

```nginx
server {
    listen 443 ssl;
    server_name pymssql-mcp.example.com;

    ssl_certificate /etc/ssl/certs/pymssql-mcp.crt;
    ssl_certificate_key /etc/ssl/private/pymssql-mcp.key;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Step 3: Configure Identity Provider

#### Duo Setup

1. Log into [Duo Admin Panel](https://admin.duosecurity.com)
2. Go to **Applications** → **Protect an Application**
3. Search for **"OIDC Relying Party"** and click **Protect**
4. Configure the application:
   - **Name**: `pymssql-mcp` (or your preferred name)
   - **Redirect URIs**: `https://your-pymssql-mcp-server.com/oauth/callback`
   - **Grant Types**: Authorization Code
   - **Token Endpoint Auth Method**: Client Secret Post
5. Note the following from the application settings:
   - **Client ID**
   - **Client Secret**
   - **OIDC Metadata URL** (Discovery URL)
6. Configure user/group access as needed

#### Auth0 Setup

1. Log into [Auth0 Dashboard](https://manage.auth0.com)
2. Go to **Applications** → **Create Application**
3. Select **Regular Web Application**
4. Configure:
   - **Allowed Callback URLs**: `https://your-pymssql-mcp-server.com/oauth/callback`
   - **Allowed Web Origins**: `https://your-pymssql-mcp-server.com`
5. Note the following from Settings:
   - **Domain** (used to construct discovery URL)
   - **Client ID**
   - **Client Secret**

Discovery URL format: `https://YOUR_DOMAIN/.well-known/openid-configuration`

#### Azure AD / Entra ID Setup

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory
2. Go to **App registrations** → **New registration**
3. Configure:
   - **Name**: `pymssql-mcp`
   - **Redirect URI**: `https://your-pymssql-mcp-server.com/oauth/callback` (Web)
4. Create a client secret under **Certificates & secrets**
5. Note:
   - **Application (client) ID**
   - **Directory (tenant) ID**
   - **Client secret value**

Discovery URL format: `https://login.microsoftonline.com/YOUR_TENANT_ID/v2.0/.well-known/openid-configuration`

### Step 4: Configure pymssql-mcp OAuth

Create or update your `.env` file:

```bash
# Database Connection
MSSQL_HOST=your-sql-server
MSSQL_USER=username
MSSQL_PASSWORD=password
MSSQL_DATABASE=your-database

# OAuth Configuration
MSSQL_AUTH_ENABLED=true
MSSQL_AUTH_ISSUER_URL=https://pymssql-mcp.example.com

# Identity Provider (Duo example)
MSSQL_IDP_PROVIDER=duo
MSSQL_IDP_DISCOVERY_URL=https://sso-XXXXXXXX.sso.duosecurity.com/oidc/YOUR_CLIENT_ID/.well-known/openid-configuration
MSSQL_IDP_CLIENT_ID=YOUR_CLIENT_ID
MSSQL_IDP_CLIENT_SECRET=YOUR_CLIENT_SECRET
MSSQL_IDP_SCOPES=openid profile email groups

# Token Settings (optional)
MSSQL_TOKEN_EXPIRY_SECONDS=3600
MSSQL_REFRESH_TOKEN_EXPIRY_SECONDS=2592000

# CORS - Allow Claude.ai
MSSQL_HTTP_CORS_ORIGINS=https://claude.ai,https://*.claude.ai
```

### Step 5: Add to Claude.ai

1. Go to Claude.ai → **Settings** (or Admin Settings for organizations)
2. Navigate to **Connectors** or **Integrations**
3. Click **Add Custom Connector**
4. Enter your pymssql-mcp URL: `https://pymssql-mcp.example.com`
5. Claude.ai will:
   - Discover OAuth endpoints automatically
   - Register as a client
   - Redirect you to authenticate with your IdP
6. After authentication, the connector is ready to use

## OAuth Endpoints

pymssql-mcp exposes the following OAuth endpoints:

| Endpoint | Description |
|----------|-------------|
| `/.well-known/oauth-authorization-server` | OAuth server metadata (RFC 8414) |
| `/register` | Dynamic Client Registration (RFC 7591) |
| `/authorize` | Authorization endpoint |
| `/token` | Token endpoint |
| `/revoke` | Token revocation endpoint |
| `/oauth/callback` | Callback for IdP redirects |

## Security Considerations

### Token Storage

Tokens are stored in memory by default. For production deployments with multiple instances, consider:
- Running a single instance behind a load balancer with sticky sessions
- Implementing persistent token storage (database, Redis)

### CORS Configuration

Configure CORS to only allow Claude.ai origins:

```bash
MSSQL_HTTP_CORS_ORIGINS=https://claude.ai,https://*.claude.ai
```

### Network Security

- Always use HTTPS in production
- Consider IP allowlisting if possible
- Use a Web Application Firewall (WAF) for additional protection

### IdP Security

- Enforce MFA in your identity provider
- Use short token lifetimes
- Regularly rotate client secrets
- Monitor authentication logs

### Database Security

- Use a dedicated database account for pymssql-mcp
- Apply principle of least privilege
- Enable read-only mode for exploration: `MSSQL_READ_ONLY=true`
- Block sensitive databases: `MSSQL_BLOCKED_DATABASES=master,msdb`

## Troubleshooting

### "Invalid authorization" Error

**Cause:** OAuth state mismatch between Claude.ai and pymssql-mcp.

**Solution:** Ensure you're using the latest version of pymssql-mcp.

### "Unsupported auth method: None" Error

**Cause:** Client registration missing authentication method.

**Solution:** Update to pymssql-mcp version 0.2.0 or later.

### 404 on Discovery URL

**Cause:** Incorrect OIDC discovery URL.

**Solution:**
- For Duo, the URL includes the client ID: `https://sso-XXX.sso.duosecurity.com/oidc/CLIENT_ID/.well-known/openid-configuration`
- Verify the URL returns JSON when accessed directly

### 503 Service Unavailable

**Cause:** Load balancer cannot reach the backend server.

**Solution:**
- Verify the backend server is running
- Check firewall rules allow traffic from the load balancer
- Verify the backend IP/port in load balancer configuration

### Connection Timeout After Authentication

**Cause:** MCP endpoint path mismatch.

**Solution:** Ensure pymssql-mcp is running in streamable-http mode and serving MCP at the root path (`/`).

## Example: Complete Duo Integration

Here's a complete example for integrating with Duo:

**`.env` file:**

```bash
# SQL Server Database
MSSQL_HOST=sqlserver.internal.example.com
MSSQL_USER=mcp_user
MSSQL_PASSWORD=secure_password
MSSQL_DATABASE=ProductionDB
MSSQL_READ_ONLY=false

# OAuth with Duo
MSSQL_AUTH_ENABLED=true
MSSQL_AUTH_ISSUER_URL=https://pymssql-mcp.example.com

MSSQL_IDP_PROVIDER=duo
MSSQL_IDP_DISCOVERY_URL=https://sso-abc123.sso.duosecurity.com/oidc/DIKJHZW79A2219BVX2SS/.well-known/openid-configuration
MSSQL_IDP_CLIENT_ID=DIKJHZW79A2219BVX2SS
MSSQL_IDP_CLIENT_SECRET=your_client_secret_here
MSSQL_IDP_SCOPES=openid profile email groups

# CORS
MSSQL_HTTP_CORS_ORIGINS=https://claude.ai,https://*.claude.ai

# Token expiry
MSSQL_TOKEN_EXPIRY_SECONDS=3600
MSSQL_REFRESH_TOKEN_EXPIRY_SECONDS=2592000

# Watchdog
MSSQL_WATCHDOG_ENABLED=true
```

**Duo Application Settings:**
- Redirect URI: `https://pymssql-mcp.example.com/oauth/callback`
- Grant Type: Authorization Code
- Token Endpoint Auth: Client Secret Post

After configuration, users can:
1. Add the connector in Claude.ai
2. Authenticate via Duo (with MFA if configured)
3. Query their SQL Server database using natural language

## Example: Azure AD Integration

**`.env` file:**

```bash
# SQL Server Database
MSSQL_HOST=sqlserver.example.com
MSSQL_USER=mcp_user
MSSQL_PASSWORD=password
MSSQL_DATABASE=CompanyDB

# OAuth with Azure AD
MSSQL_AUTH_ENABLED=true
MSSQL_AUTH_ISSUER_URL=https://pymssql-mcp.example.com

MSSQL_IDP_PROVIDER=oidc
MSSQL_IDP_DISCOVERY_URL=https://login.microsoftonline.com/YOUR_TENANT_ID/v2.0/.well-known/openid-configuration
MSSQL_IDP_CLIENT_ID=YOUR_APPLICATION_ID
MSSQL_IDP_CLIENT_SECRET=YOUR_CLIENT_SECRET
MSSQL_IDP_SCOPES=openid profile email

# CORS
MSSQL_HTTP_CORS_ORIGINS=https://claude.ai,https://*.claude.ai
```
