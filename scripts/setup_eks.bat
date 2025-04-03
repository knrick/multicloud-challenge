@echo off
setlocal enabledelayedexpansion

rem Stop on any error
echo off

echo 3. Configuring kubectl...
aws eks update-kubeconfig --name cloudmart --region us-east-1

echo.
echo 4. Verifying cluster status...
echo Checking nodes...
kubectl get nodes
echo.
echo Checking system pods...
kubectl get pods -n kube-system

echo.
echo 5. Creating service account...
kubectl create serviceaccount cloudmart-app

echo.
echo 6. Creating ECR repository...
aws ecr create-repository --repository-name cloudmart-backend --region us-east-1

echo.
echo Setup complete! Next steps:
echo 1. Run build_and_push.bat to build and push the Docker image
echo 2. Deploy the application using kubectl apply