# Stop on any error
$ErrorActionPreference = "Stop"

Write-Host "1. Initializing Terraform..."
Set-Location ../terraform/kubernetes
terraform init

Write-Host "`n2. Applying Terraform configuration..."
terraform apply -auto-approve

Write-Host "`n3. Configuring kubectl..."
aws eks update-kubeconfig --name cloudmart --region us-east-1

Write-Host "`n4. Verifying cluster status..."
Write-Host "Checking nodes..."
kubectl get nodes
Write-Host "`nChecking system pods..."
kubectl get pods -n kube-system

Write-Host "`n5. Creating service account..."
kubectl create serviceaccount cloudmart-app

Write-Host "`n6. Creating ECR repository..."
aws ecr create-repository --repository-name cloudmart-backend --region us-east-1

Write-Host "`nSetup complete! Next steps:"
Write-Host "1. Run build_and_push.ps1 to build and push the Docker image"
Write-Host "2. Deploy the application using kubectl apply" 