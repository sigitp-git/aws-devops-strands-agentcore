### Check gateway_config.json to get the "properties": {} 
### for each Lambda Target Schema, need to be configured for the agent to understand the structure of the MCP server schema

You > `avg(rate(node_cpu_seconds_total[5m]))` - Node-level CPU for my prometheus workspace ws-484afeca-566c-4932-8f04-828f652995c9

I'll query the node-level CPU usage using that PromQL expression for your workspace.
Tool #2: prometheus-query___prometheus-query
Great! Here are your node-level CPU metrics:

**Average Node CPU Usage: 0.125 (12.5%)**

This represents the average CPU utilization rate across all your nodes over the last 5 minutes. The value of ~0.125 means your nodes are running at about 12.5% CPU utilization on average, which indicates:

✅ **Healthy CPU usage** - plenty of headroom
✅ **Good performance** - not under stress
✅ **Cost optimization opportunity** - might be over-provisioned

**Key insights:**
- Low CPU utilization suggests efficient workload distribution
- Consider rightsizing if this trend continues
- Good baseline for capacity planning

Would you like me to help you query CPU usage by specific nodes, check memory metrics, or explore other performance indicators for your infrastructure?
AWS-DevOps-agent > Great! Here are your node-level CPU metrics:

**Average Node CPU Usage: 0.125 (12.5%)**

This represents the average CPU utilization rate across all your nodes over the last 5 minutes. The value of ~0.125 means your nodes are running at about 12.5% CPU utilization on average, which indicates:

✅ **Healthy CPU usage** - plenty of headroom
✅ **Good performance** - not under stress
✅ **Cost optimization opportunity** - might be over-provisioned

**Key insights:**
- Low CPU utilization suggests efficient workload distribution
- Consider rightsizing if this trend continues
- Good baseline for capacity planning

Would you like me to help you query CPU usage by specific nodes, check memory metrics, or explore other performance indicators for your infrastructure?


You > 