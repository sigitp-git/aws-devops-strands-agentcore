#!/bin/bash

# Deploy All Prometheus Lambda Functions
# Master deployment script for all Prometheus operations

set -e

echo "Deploying All Prometheus Lambda Functions"
echo "========================================"
echo ""

# Make all deployment scripts executable
chmod +x deploy_query.sh
chmod +x deploy_range_query.sh
chmod +x deploy_list_metrics.sh
chmod +x deploy_server_info.sh

# Deploy each function
echo "1. Deploying Query Function..."
./deploy_query.sh

echo ""
echo "2. Deploying Range Query Function..."
./deploy_range_query.sh

echo ""
echo "3. Deploying List Metrics Function..."
./deploy_list_metrics.sh

echo ""
echo "4. Deploying Server Info Function..."
./deploy_server_info.sh

echo ""
echo "=========================================="
echo "All Prometheus Lambda Functions Deployed!"
echo "=========================================="
echo ""
echo "Deployed Functions:"
echo "- aws-devops-prometheus-query"
echo "- aws-devops-prometheus-range-query"
echo "- aws-devops-prometheus-list-metrics"
echo "- aws-devops-prometheus-server-info"
echo ""
echo "Each function follows Lambda best practices:"
echo "✓ Single responsibility principle"
echo "✓ Minimal deployment packages"
echo "✓ Independent scaling"
echo "✓ Specific IAM permissions"
echo "✓ Shared utilities for code reuse"
echo "✓ Comprehensive error handling"
echo ""
echo "Next steps:"
echo "1. Update your integration code to use the new function names"
echo "2. Test each function individually"
echo "3. Monitor CloudWatch logs for performance"
echo "4. Adjust memory/timeout settings based on usage patterns"
echo ""