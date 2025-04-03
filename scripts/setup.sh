#!/bin/bash
# 1. Update the system
sudo yum update -y

# 2. Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# 3. Install Python 3.12 and development tools
sudo yum groupinstall -y "Development Tools"
sudo yum install -y openssl-devel bzip2-devel libffi-devel
wget https://www.python.org/ftp/python/3.12.2/Python-3.12.2.tgz
tar xzf Python-3.12.2.tgz
cd Python-3.12.2
./configure --enable-optimizations
sudo make altinstall
cd ..
sudo rm -rf Python-3.12.2*

# 4. Install Poetry
curl -sSL https://install.python-poetry.org | python3.12 -

# 5. Install AWS CLI (latest version)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install --update
sudo rm -rf aws awscliv2.zip

# 6. Install Terraform
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
sudo yum install -y terraform


# 7. Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# 8. Pull the git repo
git clone https://github.com/knrick/multicloud-challenge.git

# 9. Load products into DynamoDB (products.json is not a part of the repo)
cd multicloud-challenge/scripts
chmod +x load_products.sh
./load_products.sh

# 10. Build the docker image
cd ../src/app
docker build -t cloudmart:latest .

# 11. Run the docker container
docker run -p 8080:8080 cloudmart:latest
