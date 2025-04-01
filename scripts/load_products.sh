#!/bin/bash

# Load products into DynamoDB
aws dynamodb batch-write-item \
    --request-items file://products.json \
    --region us-east-1

echo "Products loaded successfully!" 