## Target Schme for Prometheus Lambda functions on AgentCore Gateway

```
[
  {
    "description": "Get a list of all metric names available in the Prometheus server",
    "inputSchema": {
      "properties": {
        "region": {
          "description": "AWS region (defaults to current region)",
          "type": "string"
        },
        "workspace_id": {
          "description": "The Prometheus workspace ID to use (e.g., ws-12345678-abcd-1234-efgh-123456789012)",
          "type": "string"
        }
      },
      "type": "object"
    },
    "name": "prometheus-list-metrics"
  }
]
```

```
[
  {
    "description": "Get information about the Prometheus server configuration",
    "inputSchema": {
      "properties": {
        "region": {
          "description": "AWS region (defaults to current region)",
          "type": "string"
        },
        "workspace_id": {
          "description": "The Prometheus workspace ID to use (e.g., ws-12345678-abcd-1234-efgh-123456789012)",
          "type": "string"
        }
      },
      "type": "object"
    },
    "name": "prometheus-server-info"
  }
]
```

```
[
  {
    "description": "Execute a PromQL range query over a time period against Amazon Managed Prometheus",
    "inputSchema": {
      "properties": {
        "end": {
          "description": "End timestamp (RFC3339 or Unix timestamp)",
          "type": "string"
        },
        "query": {
          "description": "The PromQL query to execute",
          "type": "string"
        },
        "region": {
          "description": "AWS region (defaults to current region)",
          "type": "string"
        },
        "start": {
          "description": "Start timestamp (RFC3339 or Unix timestamp)",
          "type": "string"
        },
        "step": {
          "description": "Query resolution step width (duration format, e.g. '15s', '1m', '1h')",
          "type": "string"
        },
        "workspace_id": {
          "description": "The Prometheus workspace ID to use (e.g., ws-12345678-abcd-1234-efgh-123456789012)",
          "type": "string"
        }
      },
      "type": "object"
    },
    "name": "prometheus-range-query"
  }
]

```

```
[
  {
    "description": "Execute an instant PromQL query against Amazon Managed Prometheus",
    "inputSchema": {
      "properties": {
        "query": {
          "description": "The PromQL query to execute",
          "type": "string"
        },
        "region": {
          "description": "AWS region (defaults to current region)",
          "type": "string"
        },
        "time": {
          "description": "Optional timestamp for query evaluation (RFC3339 or Unix timestamp)",
          "type": "string"
        },
        "workspace_id": {
          "description": "The Prometheus workspace ID to use (e.g., ws-12345678-abcd-1234-efgh-123456789012)",
          "type": "string"
        }
      },
      "type": "object"
    },
    "name": "prometheus-query"
  }
]
```