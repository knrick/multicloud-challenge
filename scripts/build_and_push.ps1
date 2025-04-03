$ErrorActionPreference = "Stop"

# Get ECR login token and login to Docker
Write-Host "Logging into ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 039612844200.dkr.ecr.us-east-1.amazonaws.com

# Tag and push to ECR
Write-Host "Tagging and pushing to ECR..."
Set-Location ../src/app
docker tag cloudmart:latest 039612844200.dkr.ecr.us-east-1.amazonaws.com/cloudmart-backend:latest
docker push 039612844200.dkr.ecr.us-east-1.amazonaws.com/cloudmart-backend:latest

Write-Host "Done!" 