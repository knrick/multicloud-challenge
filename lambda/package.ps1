# Package the product-recommendations Lambda function
Set-Location product-recommendations

# Create and activate mamba environment
mamba env create -f environment.yml --force
mamba activate lambda-products

# Create a new directory for packaging
New-Item -ItemType Directory -Force -Path build
Copy-Item -Path "index.py" -Destination "build/"
Copy-Item -Path "$env:CONDA_PREFIX/Lib/site-packages/boto3" -Destination "build/boto3" -Recurse
Copy-Item -Path "$env:CONDA_PREFIX/Lib/site-packages/botocore" -Destination "build/botocore" -Recurse
Copy-Item -Path "$env:CONDA_PREFIX/Lib/site-packages/urllib3" -Destination "build/urllib3" -Recurse
Copy-Item -Path "$env:CONDA_PREFIX/Lib/site-packages/dateutil" -Destination "build/dateutil" -Recurse
Copy-Item -Path "$env:CONDA_PREFIX/Lib/site-packages/jmespath" -Destination "build/jmespath" -Recurse

# Create the ZIP file
Set-Location build
Compress-Archive -Path * -DestinationPath ../list_products.zip -Force
Set-Location ..

# Cleanup
Remove-Item -Path build -Recurse -Force
mamba deactivate
mamba env remove -n lambda-products -y

Set-Location .. 