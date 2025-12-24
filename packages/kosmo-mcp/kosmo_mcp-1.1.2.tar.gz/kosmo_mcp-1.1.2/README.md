# KOSMO MCP Server

<div align="center">
  <img src="https://raw.githubusercontent.com/Open-Hermios/Kosmo/main/.github/icon.png" alt="KOSMO Logo" width="200" />
  
  <h1>KOSMO</h1>
  
  <p>
    <strong>An Agency Program for Builders</strong>
  </p>
  
  <p>
    <a href="https://pypi.org/project/kosmo-mcp/"><img src="https://img.shields.io/pypi/v/kosmo-mcp?style=flat-square" alt="PyPI Version"></a>
    <a href="https://smithery.ai/server/kosmo"><img src="https://smithery.ai/badge/kosmo" alt="Smithery"></a>
    <a href="https://glama.ai/mcp/servers/kosmo"><img src="https://glama.ai/mcp/servers/kosmo/badge" alt="Glama"></a>
  </p>
</div>

## Overview

KOSMO is not an agent or a set of protocols. It is a formally structured protocol program designed to accelerate any builder at any scale. It enforces strict no-op determinism, deep research automation, and secure protocol enforcement. KOSMO loves Fortran.

## Central Features

- **Kosmo**: Basic Plan and Build logic (kosmo plan <X> then kosmo build <x> is the lightweight workflow)
- **Athena**: Theoretical Verifier, Planning Mode Intelligence boost (System and Agent Command Audits, Logic Verification)
- **Chiron**: Training Optimizer and manger (ML Pipelines)
- **Chaos**: Git Agent of Chains (Version Control for Logic, *Ongoing Development*) 

## Standard Chain Library
*At the moment, this is the only available chain in the standard chain library, try making some for yourself and let us know if you find a really useful one*

- **fullbuild**: An end to end build chain involving plannnning, verification, execution, and review. (Best with fully context engineered plan, but often capable of codegen at scale from a single well defined command)

## Installation

### Zero-Install (Recommended)

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "kosmo": {
      "command": "uvx",
      "args": ["kosmo-mcp"]
    }
  }
}
```

### Manual Install

```bash
uv tool install kosmo-mcp
```

## Support

Email: info@hermios.us
