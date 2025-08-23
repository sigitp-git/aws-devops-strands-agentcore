> Perfect! I've successfully updated the MCP-Lambda-Policies inline policy with comprehensive permissions for all your MCP Lambda functions. Here's a summary of what was added:

## Updated MCP-Lambda-Policies Permissions

### 1. STS Permissions (Enhanced)
• sts:GetSessionToken
• sts:GetCallerIdentity
• sts:AssumeRole (NEW)

### 2. Pricing Permissions (NEW)
• pricing:GetProducts
• pricing:DescribeServices
• pricing:GetAttributeValues
• pricing:GetPriceListFileUrl

### 3. Documentation Permissions (NEW)
• support:DescribeServices
• support:DescribeSeverityLevels
• support:DescribeCommunications

### 4. Location Permissions (NEW)
• geo:SearchPlaceIndexForText
• geo:SearchPlaceIndexForPosition
• geo:GetPlace
• geo:CalculateRoute
• geo:SearchPlaceIndexForSuggestions

### 5. Terraform Permissions (NEW)
• S3 operations: GetObject, PutObject, ListBucket, DeleteObject
• DynamoDB operations: GetItem, PutItem, UpdateItem, DeleteItem, Scan, Query

### 6. CloudWatch Permissions (NEW)
• Logs: CreateLogGroup, CreateLogStream, PutLogEvents, DescribeLogGroups, DescribeLogStreams, GetLogEvents, FilterLogEvents, StartQuery, StopQuery, GetQueryResults
• Metrics: GetMetricData, GetMetricStatistics, ListMetrics, PutMetricData, DescribeAlarms, GetMetricWidgetImage

### 7. EKS Permissions (NEW)
• eks:DescribeCluster, eks:ListClusters
• eks:DescribeNodegroup, eks:ListNodegroups
• eks:DescribeAddon, eks:ListAddons
• eks:DescribeUpdate, eks:ListUpdates
• eks:AccessKubernetesApi

### 8. Git and Code Permissions (NEW)
• CodeCommit: GetRepository, ListRepositories, GetBranch, ListBranches, GetCommit, GetDifferences, GetFile, GetFolder
• CodeArtifact: GetAuthorizationToken, ReadFromRepository

### 9. Frontend Permissions (NEW)
• Amplify: GetApp, ListApps, GetBranch, ListBranches, GetJob, ListJobs
• CloudFront: GetDistribution, ListDistributions
• Route53: GetHostedZone, ListHostedZones

### 10. Additional Permissions (NEW)
• Secrets Manager: GetSecretValue, DescribeSecret
• KMS: Decrypt, DescribeKey
• Lambda: InvokeFunction, GetFunction
• API Gateway: GET, execute-api:Invoke

## Benefits

Your MCP Lambda functions now have comprehensive permissions to:

✅ Execute all pricing operations (get service codes, attributes, pricing data)
✅ Access AWS documentation and support APIs
✅ Perform location-based operations (geocoding, routing, place search)
✅ Manage Terraform state and configurations
✅ Query CloudWatch logs and metrics
✅ Interact with EKS clusters and resources
✅ Access Git repositories and code artifacts
✅ Work with frontend services (Amplify, CloudFront, Route53)
✅ Handle secrets and encryption
✅ Invoke other Lambda functions and APIs

The policy follows the principle of least privilege while ensuring all MCP functionalities work properly. All permissions are scoped appropriately for the services your MCP Lambda
functions need to interact with.
