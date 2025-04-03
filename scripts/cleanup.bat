@echo off
setlocal enabledelayedexpansion

echo 1. Deleting ECR repositories...
aws ecr delete-repository --repository-name cloudmart --force --region us-east-1

echo.
echo 2. Cleaning up Kubernetes resources...
kubectl delete -f kubernetes/cloudmart-secrets.yaml --ignore-not-found
kubectl delete -f kubernetes/cloudmart.yaml --ignore-not-found

echo.
echo 3. Destroying Terraform resources...
cd ..\terraform\kubernetes
terraform destroy -auto-approve

echo.
echo Cleanup complete!