provider "aws" {
  region = "us-east-1"
}

# Get EKS cluster for Kubernetes provider
data "aws_eks_cluster" "cloudmart" {
  name = "cloudmart"
}

data "aws_eks_cluster_auth" "cloudmart" {
  name = "cloudmart"
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.cloudmart.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cloudmart.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.cloudmart.token
}

# Add CodeBuild role to aws-auth ConfigMap
resource "kubernetes_config_map_v1_data" "aws_auth" {
  metadata {
    name      = "aws-auth"
    namespace = "kube-system"
  }

  data = {
    mapRoles = yamlencode([
      {
        rolearn  = "arn:aws:iam::039612844200:role/cloudmart-eks-node-group-role"
        username = "system:node:{{EC2PrivateDNSName}}"
        groups   = ["system:bootstrappers", "system:nodes"]
      },
      {
        rolearn  = aws_iam_role.codebuild_role.arn
        username = "codebuild"
        groups   = ["system:masters"]
      }
    ])
  }

  force = true
}

# CodeBuild project for building Docker image
resource "aws_codebuild_project" "cloudmart_build" {
  name          = "cloudmartBuild"
  description   = "Build Docker image for CloudMart application"
  service_role  = aws_iam_role.codebuild_role.arn

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                      = "aws/codebuild/amazonlinux2-x86_64-standard:4.0"
    type                       = "LINUX_CONTAINER"
    privileged_mode            = true
    
    environment_variable {
      name  = "ECR_REPO"
      value = "039612844200.dkr.ecr.us-east-1.amazonaws.com/cloudmart"
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "ci-cd/buildspec.yml"
    git_clone_depth = 1
    git_submodules_config {
      fetch_submodules = true
    }
  }
}

# IAM role for CodeBuild
resource "aws_iam_role" "codebuild_role" {
  name = "cloudmartBuild"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codebuild.amazonaws.com"
        }
      }
    ]
  })
}

# CodePipeline IAM Role
resource "aws_iam_role" "codepipeline_role" {
  name = "cloudmart-codepipeline-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codepipeline.amazonaws.com"
        }
      }
    ]
  })
}

# CodePipeline Policy
resource "aws_iam_role_policy" "codepipeline_policy" {
  name = "cloudmart-codepipeline-policy"
  role = aws_iam_role.codepipeline_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:GetBucketVersioning",
          "s3:PutObject",
          "codestar-connections:UseConnection",
          "codebuild:BatchGetBuilds",
          "codebuild:StartBuild",
          "eks:DescribeCluster",
          "eks:ListClusters",
          "eks:UpdateClusterConfig",
          "eks:AccessKubernetesApi",
          "eks:CreateCluster",
          "eks:DeleteCluster",
          "eks:UpdateClusterVersion",
          "eks:DescribeUpdate",
          "eks:TagResource",
          "eks:UntagResource",
          "eks:ListTagsForResource",
          "eks:CreateFargateProfile",
          "eks:DeleteFargateProfile",
          "eks:DescribeFargateProfile",
          "eks:ListFargateProfiles",
          "eks:CreateNodegroup",
          "eks:DeleteNodegroup",
          "eks:DescribeNodegroup",
          "eks:ListNodegroups",
          "eks:UpdateNodegroupConfig",
          "eks:UpdateNodegroupVersion"
        ]
        Resource = "*"
      }
    ]
  })
}

# S3 bucket for artifacts
resource "aws_s3_bucket" "artifacts" {
  bucket = "cloudmart-pipeline-artifacts"
  force_destroy = true
}

# Block public access to the S3 bucket
resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning on the S3 bucket
resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

# GitHub connection
resource "aws_codestarconnections_connection" "github" {
  name          = "cloudmart-github"
  provider_type = "GitHub"
}

# CodePipeline
resource "aws_codepipeline" "cloudmart" {
  name     = "cloudmart-cicd-pipeline"
  role_arn = aws_iam_role.codepipeline_role.arn

  artifact_store {
    location = aws_s3_bucket.artifacts.bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner           = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        ConnectionArn    = aws_codestarconnections_connection.github.arn
        FullRepositoryId = "knrick/multicloud-challenge"
        BranchName       = "master"
        DetectChanges    = true
      }
    }
  }

  stage {
    name = "Build"

    action {
      name            = "Build"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      input_artifacts = ["source_output"]
      version         = "1"

      configuration = {
        ProjectName = aws_codebuild_project.cloudmart_build.name
      }
    }
  }
}

# Update CodeBuild role policy to include ECR permissions
resource "aws_iam_role_policy" "codebuild_policy" {
  name = "cloudmart-codebuild-policy"
  role = aws_iam_role.codebuild_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "eks:DescribeCluster",
          "eks:ListClusters",
          "eks:AccessKubernetesApi",
          "eks:GetToken",
          "sts:GetCallerIdentity",
          "lambda:UpdateFunctionCode",
          "lambda:GetFunction"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:us-east-1:*:log-group:/aws/codebuild/*",
          "arn:aws:logs:us-east-1:*:log-group:/aws/codebuild/*:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:GetBucketVersioning",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${aws_s3_bucket.artifacts.arn}",
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr-public:GetAuthorizationToken",
          "sts:GetServiceBearerToken"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:CompleteLayerUpload",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart"
        ]
        Resource = "arn:aws:ecr:us-east-1:039612844200:repository/cloudmart"
      }
    ]
  })
} 