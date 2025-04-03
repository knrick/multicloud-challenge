@echo off
setlocal enabledelayedexpansion

rem Get ECR login token and login to Docker
echo Logging into ECR...
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 039612844200.dkr.ecr.us-east-1.amazonaws.com

rem Tag and push to ECR
echo Tagging and pushing to ECR...
docker tag cloudmart:latest 039612844200.dkr.ecr.us-east-1.amazonaws.com/cloudmart:latest
docker push 039612844200.dkr.ecr.us-east-1.amazonaws.com/cloudmart:latest

echo Done!