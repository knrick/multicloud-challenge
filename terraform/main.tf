terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# EC2 Admin Role
resource "aws_iam_role" "ec2_admin_role" {
  name = "EC2Admin"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "EC2Admin"
    Environment = "Dev"
  }
}

# Attach AdministratorAccess policy to EC2Admin role
resource "aws_iam_role_policy_attachment" "ec2_admin_policy" {
  role       = aws_iam_role.ec2_admin_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

# Create instance profile for EC2
resource "aws_iam_instance_profile" "ec2_admin_profile" {
  name = "EC2AdminProfile"
  role = aws_iam_role.ec2_admin_role.name
}

# EC2 Instance
resource "aws_instance" "workstation" {
  ami           = "ami-0440d3b780d96b29d"  # Amazon Linux 2023 in us-east-1
  instance_type = "t2.micro"
  
  iam_instance_profile = aws_iam_instance_profile.ec2_admin_profile.name
  
  vpc_security_group_ids = [aws_security_group.workstation_sg.id]
  
  tags = {
    Name = "workstation"
    Environment = "Dev"
  }
}

# Security Group for EC2
resource "aws_security_group" "workstation_sg" {
  name        = "workstation-sg"
  description = "Security group for workstation EC2 instance"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Note: In production, restrict this to specific IPs
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Note: In production, restrict this to specific IPs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "workstation-sg"
    Environment = "Dev"
  }
}

# Output the EC2 instance public IP
output "workstation_public_ip" {
  value = aws_instance.workstation.public_ip
  description = "Public IP of the workstation EC2 instance"
}

# DynamoDB Tables
resource "aws_dynamodb_table" "cloudmart_products" {
  name           = "cloudmart-products"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  
  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name        = "cloudmart-products"
    Environment = "Dev"
  }
}

resource "aws_dynamodb_table" "cloudmart_orders" {
  name           = "cloudmart-orders"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  
  attribute {
    name = "id"
    type = "S"
  }

  # Enable DynamoDB Streams
  stream_enabled = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  tags = {
    Name        = "cloudmart-orders"
    Environment = "Dev"
  }
}

resource "aws_dynamodb_table" "cloudmart_tickets" {
  name           = "cloudmart-tickets"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  
  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name        = "cloudmart-tickets"
    Environment = "Dev"
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "cloudmart_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "cloudmart_lambda_policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Scan",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          aws_dynamodb_table.cloudmart_products.arn,
          aws_dynamodb_table.cloudmart_orders.arn,
          aws_dynamodb_table.cloudmart_tickets.arn,
          "arn:aws:logs:*:*:*"
        ]
      }
    ]
  })
}

# Create dummy ZIP file for Lambda functions
data "archive_file" "dummy" {
  type        = "zip"
  output_path = "${path.module}/lambda_function_payload.zip"

  source {
    content  = <<EOF
def handler(event, context):
    """Placeholder handler for initial Lambda deployment"""
    return {
        'statusCode': 200,
        'body': 'Function not yet updated by CI/CD pipeline'
    }
EOF
    filename = "index.py"
  }
}

# Lambda function for listing products
resource "aws_lambda_function" "list_products" {
  function_name    = "cloudmart-list-products"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.12"
  publish         = true  # Enable versioning
  
  filename         = data.archive_file.dummy.output_path
  source_code_hash = data.archive_file.dummy.output_base64sha256

  environment {
    variables = {
      PRODUCTS_TABLE = aws_dynamodb_table.cloudmart_products.name
    }
  }

  lifecycle {
    ignore_changes = [
      filename,
      source_code_hash,
    ]
  }
}

# Lambda permission for Bedrock
resource "aws_lambda_permission" "allow_bedrock" {
  statement_id  = "AllowBedrockInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.list_products.function_name
  principal     = "bedrock.amazonaws.com"
}

# IAM Role for BigQuery Sync Lambda
resource "aws_iam_role" "bigquery_sync_role" {
  name = "cloudmart_bigquery_sync_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for BigQuery Sync Lambda
resource "aws_iam_role_policy" "bigquery_sync_policy" {
  name = "cloudmart_bigquery_sync_policy"
  role = aws_iam_role.bigquery_sync_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:DescribeStream",
          "dynamodb:ListStreams",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_dynamodb_table.cloudmart_orders.arn}/stream/*",
          "arn:aws:logs:*:*:*"
        ]
      }
    ]
  })
}

# Lambda function for BigQuery sync
resource "aws_lambda_function" "bigquery_sync" {
  function_name    = "cloudmart-bigquery-sync"
  role            = aws_iam_role.bigquery_sync_role.arn
  handler         = "index.handler"
  runtime         = "python3.12"
  timeout         = 60
  publish         = true  # Enable versioning
  
  filename         = data.archive_file.dummy.output_path
  source_code_hash = data.archive_file.dummy.output_base64sha256

  environment {
    variables = {
      GOOGLE_CLOUD_PROJECT_ID = "cloudmart-456007"
      BIGQUERY_DATASET_ID     = "cloudmart"
      BIGQUERY_TABLE_ID       = "cloudmart-orders"
    }
  }

  lifecycle {
    ignore_changes = [
      filename,
      source_code_hash,
    ]
  }
}

# Event source mapping for DynamoDB Streams to Lambda
resource "aws_lambda_event_source_mapping" "orders_stream" {
  event_source_arn  = aws_dynamodb_table.cloudmart_orders.stream_arn
  function_name     = aws_lambda_function.bigquery_sync.arn
  starting_position = "LATEST"
  batch_size        = 100
  maximum_retry_attempts = 3
}