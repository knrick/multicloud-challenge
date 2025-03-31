# Package the product-recommendations Lambda function
$ErrorActionPreference = "Stop"

try {
    Set-Location product-recommendations

    Write-Host "Creating Mamba environment..."
    mamba env create -f environment.yml --force
    if ($LASTEXITCODE -ne 0) { throw "Failed to create Mamba environment" }

    $envPath = "C:\Users\Asus\miniforge-pypy3\envs\lambda-products"

    Write-Host "Creating build directory..."
    New-Item -ItemType Directory -Force -Path build
    Copy-Item -Path "index.py" -Destination "build/"
    
    Write-Host "Copying dependencies..."
    Copy-Item -Path "$envPath\Lib\site-packages\boto3" -Destination "build/boto3" -Recurse
    Copy-Item -Path "$envPath\Lib\site-packages\botocore" -Destination "build/botocore" -Recurse
    Copy-Item -Path "$envPath\Lib\site-packages\urllib3" -Destination "build/urllib3" -Recurse
    Copy-Item -Path "$envPath\Lib\site-packages\python_dateutil*" -Destination "build/dateutil" -Recurse
    Copy-Item -Path "$envPath\Lib\site-packages\jmespath" -Destination "build/jmespath" -Recurse

    Write-Host "Creating ZIP file..."
    Set-Location build
    Compress-Archive -Path * -DestinationPath ../list_products.zip -Force
    Set-Location ..

    Write-Host "Cleaning up..."
    Remove-Item -Path build -Recurse -Force
    mamba env remove -n lambda-products -y
}
catch {
    Write-Error "An error occurred: $_"
    exit 1
}
finally {
    Set-Location ..
}

Write-Host "Lambda package created successfully!" 