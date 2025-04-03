# Stop on any error
$ErrorActionPreference = "Stop"

Write-Host "1. Deleting ECR repository..."
aws ecr delete-repository --repository-name cloudmart-backend --force --region us-east-1

Write-Host "`n2. Destroying Terraform resources..."
Set-Location ../terraform/kubernetes
terraform destroy -auto-approve

Write-Host "`nCleanup complete!" 