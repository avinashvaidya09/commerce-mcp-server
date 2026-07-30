## commerce-mcp-server

### Introduction

This repository contains an MCP (Model Context Protocol) server that exposes tools for working with Commerce OData APIs.

It supports two common ways of running:

- **Local development**: Run the server locally and use the MCP Inspector to explore and call tools.
- **SAP BTP (Cloud Foundry)**: Build and deploy as an MTA, using BTP services (e.g., Destination and XSUAA) for connectivity and authentication.

**I highly recommend to go through the complete README file and then start step by step**

### Pre-requisites

- **SAP BTP subaccount (Cloud Foundry)**: You have access to a BTP subaccount with a Cloud Foundry org/space and can log in using `cf login`.
  > Not required if running locally with `MOCK_BACKEND=true`.
- **Commerce OData APIs available**: 
    1. Commerce OData APIs are already deployed/running and reachable from where you run this MCP server (local or BTP). You can either create a simple e-commerce application using standard CAP template
     or create your own.
    2. Create a destination for the commerce APIs with name - COMMERCE_API_DESTINATION. 
  > Not required if running locally with `MOCK_BACKEND=true`.


**Destination name default:**

- Default Destination name is COMMERCE_API_DESTINATION which can be updated from envrironment variables


### Local Set up

1. Install Python 3.13 and verify

Install Python 3.13.x from python.org (macOS universal installer).

Verify:

```bash
python3.13 --version
```

```bash
python3.13 --version
which python3.13
```

2. (Optional) Open new terminal and install `uv` (faster pip) and ensure correct architecture (arm64 vs x86_64)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. (Optional) Add `uv` to your `PATH`

The install script typically places `uv` in `~/.local/bin/uv`. Adding `~/.local/bin` to your `PATH` makes `uv` available in new terminals.

If you installed `uv` via Homebrew (`brew install uv`), you can skip this step.

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
hash -r
```

4. (Optional) Verify `uv` is found

```bash
which uv
uv --version
file "$(which uv)"
```

5. Go to VSCode and open terminal. Create and activate a virtual environment

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

Verify venv is active and using expected Python:

```bash
which python
python --version
python -m pip --version
```

6. Install fastMCP (`uv` optional)

Using `uv`:

```bash
uv pip install --no-cache-dir "fastmcp<3"
```

Or using `pip`:

```bash
pip install "fastmcp<3"
```

7. Install dependencies
```bash
pip install -r requirements.txt
```

8. Verify version

```bash
fastmcp version
```

You are all set!


### MCP Server on BTP and Quick Validation

1. Login to the BTP subaccount using `cf login`

2. Build application and deploy to BTP
```bash
mbt build && cf deploy mta_archives/commerce-mcp-server_1.0.0.mtar
```

3. The MBT build will create the required resources and deploy the MCP server in the subaccount dev space.

4. Run the below MCP client which will list all the tools of the MCP. Ensure you have your .env set up properly as per the `.env-template`
```bash
python scripts/check_remote_mcp.py
```

5. You will receive the list of tools
```bash
Connected.
Tools: ['mcp_ping']
mcp_ping: {'status': 'success', 'message': 'MCP service is reachable.'}
```

### VCAP SERVICES

1. Get the vcap services

```bash
cf env commerce-mcp-server
```

2. Create `vcap.json` at the root of your folder. Copy the full JSON under VCAP_SERVICES and save it as vcap.json.

3. Set env variables
```bash
export VCAP_SERVICES="$(cat vcap.json)"
```

4. Check if the VCAP_SERVICES are loaded using below command
```bash
echo $VCAP_SERVICES
```

### MCP server on local

There are two ways to run the MCP server locally:

#### Option 1: Mock Backend (no BTP required)

No SAP BTP account or deployed Commerce APIs needed. The server serves sample payloads from `assets/payloads/`.

1. Create a `.env` file in the project root using the `.env-template` and set:

```
ENVIRONMENT=local
MOCK_BACKEND=true
```

2. Run MCP inspector (local STDIO)
```bash
fastmcp dev src/server.py
```

3. This opens the MCP Inspector in your browser. All tools (`get_products`, `get_categories`, `get_products_by_category`, `get_retailers`) return mock data immediately.

#### Option 2: Live Backend (BTP required)

**Pre-requisite** - Commerce OData APIs application must be deployed on BTP with `DESTINATION - COMMERCE_API_DESTINATION`.

1. Create a `.env` file in the project root using the `.env-template` and set:

```
ENVIRONMENT=local
MOCK_BACKEND=false
DESTINATION_NAME=COMMERCE_API_DESTINATION
```

2. Follow the [VCAP SERVICES](#vcap-services) section to load your service credentials.

3. Run MCP inspector (local STDIO)
```bash
fastmcp dev src/server.py
```

4. This opens the MCP Inspector in your browser.

5. Browse through the tools and run them.

### How to debug the code on local

1. Start the Debug launch configuration.

2. In Terminal 1 (debug console/terminal), verify the server is running and the MCP endpoint is available: `http://0.0.0.0:8080/mcp`

3. Open second terminal and load the xsuaa service credentials (You will get it from subaccount xsuaa service instance)
```bash
export MCP_URL=http://0.0.0.0:8080/mcp
export MCP_XSUAA_AUTH_URL=https://<subaccount>.authentication.us10.hana.ondemand.com/oauth/token
export MCP_XSUAA_CLIENT_ID=<clientID>
export MCP_XSUAA_CLIENT_SECRET=<clientSecret>
```

4. Get `MCP_XSUAA_TOKEN` (XSUAA client credentials)

If you see `KeyError: 'access_token'`, the token endpoint returned an error JSON (so there is no `access_token` field). First, inspect the raw response:

```bash
curl -i -sS -X POST "$MCP_XSUAA_AUTH_URL" \
  -u "$MCP_XSUAA_CLIENT_ID:$MCP_XSUAA_CLIENT_SECRET" \
  -H "Accept: application/json" \
  -d "grant_type=client_credentials"
```

Then export the token:

```bash
export MCP_XSUAA_TOKEN=$(
  curl -sS -X POST "$MCP_XSUAA_AUTH_URL" \
    -u "$MCP_XSUAA_CLIENT_ID:$MCP_XSUAA_CLIENT_SECRET" \
    -H "Accept: application/json" \
    -d "grant_type=client_credentials" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)
```

5. Initialize and capture SID
```bash
SID=$(
  curl -i -sS -X POST "$MCP_URL" \
    -H "Authorization: Bearer $MCP_XSUAA_TOKEN" \
    -H "Accept: application/json, text/event-stream" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"0.1.0"}}}' \
  | awk -F': ' 'tolower($1)=="mcp-session-id"{print $2}' | tr -d '\r'
)
echo "SID=[$SID]"
```

6. If SID prints, run the below command
```bash
curl -sS -X POST "$MCP_URL" \
  -H "Authorization: Bearer $MCP_XSUAA_TOKEN" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

7. List tools
```bash
curl -sS -X POST "$MCP_URL" \
  -H "Authorization: Bearer $MCP_XSUAA_TOKEN" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
```

8. Set debug point in the `mcp_ping` tool and run the below command
```bash
curl -sS -X POST "$MCP_URL" \
  -H "Authorization: Bearer $MCP_XSUAA_TOKEN" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"mcp_ping","arguments":{}}}'
```

9. Call `get_products` tool 
```bash
curl -sS -X POST "$MCP_URL" \
  -H "Authorization: Bearer $MCP_XSUAA_TOKEN" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SID" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":4,\"method\":\"tools/call\",\"params\":{\"name\":\"get_products\",\"arguments\":{}}}"
```

10. Call get_categories tool
```bash
curl -sS -X POST "$MCP_URL" \
  -H "Authorization: Bearer $MCP_XSUAA_TOKEN" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"get_categories","arguments":{}}}'
```

11. Call get_products_by_category tool
```bash
CATEGORY_ID="a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c3d"

curl -sS -X POST "$MCP_URL" \
  -H "Authorization: Bearer $MCP_XSUAA_TOKEN" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SID" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":6,\"method\":\"tools/call\",\"params\":{\"name\":\"get_products_by_category\",\"arguments\":{\"category_id\":\"$CATEGORY_ID\"}}}"
```

12. Call get_retailers tool
```bash
curl -sS -X POST "$MCP_URL" \
  -H "Authorization: Bearer $MCP_XSUAA_TOKEN" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"get_retailers","arguments":{}}}'
```

# Proposed Topic: Custom MCP Server Vs Integration Suite MCP Gateway in an Enterprise Landscape

## Overview

This topic presents a hands-on comparison of two approaches for exposing SAP business APIs as tools for AI agents:

1. Developing a custom MCP server using Python and deploying it on SAP BTP Cloud Foundry.
2. Creating and governing MCP tools using the MCP Gateway capability in SAP Integration Suite.

The same backend OData API and Joule agent scenario were implemented using both approaches. This allows the article to compare them based on actual implementation experience rather than only explaining MCP concepts theoretically.

## Scenario Implemented

A Commerce OData service exposed product information through operations such as:

* Get product by product ID
* Search for a product using SKU

### Approach 1: Custom Python MCP Server

A Python-based MCP server was developed and deployed on SAP BTP Cloud Foundry.

The MCP server:

* Destination was created to connect to the backend Commerce OData service.
* Exposed the backend operations as MCP tools.
* Was registered in Joule Studio.
* Was consumed by a Joule agent and deployed as part of an AI assistant.

This approach demonstrates how developers can create custom MCP tools with complete control over the implementation, business logic, request processing, response transformation, and integration behavior.

### Approach 2: SAP Integration Suite MCP Gateway

The same backend API was exposed using SAP Integration Suite MCP Gateway.

* Destination was created to connect to the backend Commerce OData service. 
* An OpenAPI 3.0 specification was created to describe the operations that should be exposed as MCP tools.
* The generated MCP server was then connected to the same Joule agent.
* SAP Integration Suite supports exposing APIs as governed MCP tools

## Comparison of the Two Approaches

### Custom Python MCP Server

**Advantages**

* Complete flexibility over tool behavior and implementation.
* Can combine multiple backend systems into a single tool.
* Allows custom validation, transformations, orchestration, caching, and error handling.
* Does not require an OpenAPI specification because tool definitions are implemented directly in code.

**Considerations**

* The development team owns deployment, scaling, patching, and runtime maintenance.
* Authentication and authorization must be designed and implemented.
* Monitoring and logging must be configured separately.
* Traffic management and consumption controls require additional services or custom implementation.
* Tool lifecycle and version management remain the responsibility of the development team.

### SAP Integration Suite MCP Gateway

**Advantages**

* Existing APIs can be exposed as MCP tools with less custom implementation.
* Provides a centralized and standardized approach for publishing enterprise tools.
* API policies can be applied for security and traffic management.
* Capabilities such as quota enforcement, surge protection, IP filtering, authentication, monitoring, and analytics can be applied centrally.
* Existing Integration Suite API governance practices can be extended to AI-agent tool consumption.
* MCP servers can be published and bundled into products for controlled discovery and consumption.

**Considerations**

* Complex tool-specific business logic may still require a custom service or integration layer.
* The quality of the MCP tool depends heavily on the underlying API design and OpenAPI specification.
* Availability depends on the applicable SAP Integration Suite service plan.

## Key Learning

The two approaches are not necessarily competitors.

A custom Python MCP server is useful when the tool requires significant custom logic, orchestration, aggregation, or transformation.

SAP Integration Suite MCP Gateway is useful when organizations want to expose existing SAP or non-SAP APIs as standardized, secure, monitored, and governed tools for AI agents.


## SAP’s Direction for MCP

SAP appears to be positioning MCP as a standard for connecting AI agents with enterprise systems and SAP Integration Suite as a governed integration layer for those agent-to-tool interactions.


## How This Topic Is Different from a Generic MCP Server Topic

This is not another **“how to build an MCP server”** article.

A generic MCP server topic normally focuses on:

* MCP architecture and protocol concepts.
* Creating tools using Python.
* Running an MCP server locally or on Cloud Foundry.
* Connecting the server to an AI client.

This topic begins where a normal MCP server implementation ends.

Its primary focus is:

* Comparing a custom MCP server with SAP Integration Suite MCP Gateway.
* Showing how existing APIs can become governed tools for Joule agents.
* Showing how enterprise policies such as quotas, surge protection, and IP filtering can be leveraged.


