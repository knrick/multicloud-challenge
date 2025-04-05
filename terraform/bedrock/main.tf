provider "aws" {
  region = "us-east-1"
}

provider "opensearch" {
  url = "http://dummy-url"  # Required but won't be used since create_opensearch_config = false
  healthcheck = false
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.41.0"
    }
    opensearch = {
      source = "opensearch-project/opensearch"
      version = "2.2.0"
    }
  }
}

# Get common information about the environment
data "aws_caller_identity" "this" {}
data "aws_partition" "this" {}
data "aws_region" "this" {}

locals {
  account_id = data.aws_caller_identity.this.account_id
  partition  = data.aws_partition.this.partition
  region     = data.aws_region.this.name
}

# Reference to the Lambda function
data "aws_lambda_function" "list_products" {
  function_name = "cloudmart-list-products"
}

module "bedrock" {
  source  = "aws-ia/bedrock/aws"
  version = "0.0.15"

  # Agent configuration
  create_agent = true
  agent_name = "cloudmart-product-recommendation-agent"
  agent_description = "Product recommendation agent for CloudMart e-commerce store"
  name_prefix = "cloudmart"
  foundation_model = "anthropic.claude-3-sonnet-20240229-v1:0"
  idle_session_ttl = 1800  # 30 minutes
  
  # Tags for better resource management
  tags = {
    Environment = "Production"
    Project     = "CloudMart"
    ManagedBy   = "Terraform"
  }

  # Agent alias configuration
  create_agent_alias = true
  agent_alias_name = "cloudmart-prod"
  agent_alias_description = "Production alias for CloudMart product recommendation agent"
  agent_alias_tags = {
    Environment = "Production"
    Project     = "CloudMart"
    ManagedBy   = "Terraform"
  }

  instruction = <<-EOT
You are a product recommendations agent for CloudMart, an online e-commerce store. Your role is to assist customers in finding products that best suit their needs. Follow these instructions carefully:

1. Begin each interaction by retrieving the full list of products from the API. This will inform you of the available products and their details.
2. Your goal is to help users find suitable products based on their requirements. Ask questions to understand their needs and preferences if they're not clear from the user's initial input.
3. Use the 'name' parameter to filter products when appropriate. Do not use or mention any other filter parameters that are not part of the API.
4. Always base your product suggestions solely on the information returned by the API. Never recommend or mention products that are not in the API response.
5. When suggesting products, provide the name, description, and price as returned by the API. Do not invent or modify any product details.
6. If the user's request doesn't match any available products, politely inform them that we don't currently have such products and offer alternatives from the available list.
7. Be conversational and friendly, but focus on helping the user find suitable products efficiently.
8. Do not mention the API, database, or any technical aspects of how you retrieve the information. Present yourself as a knowledgeable sales assistant.
9. If you're unsure about a product's availability or details, always check with the API rather than making assumptions.
10. If the user asks about product features or comparisons, use only the information provided in the product descriptions from the API.
11. Be prepared to assist with a wide range of product inquiries, as our e-commerce store may carry various types of items.
12. If a user is looking for a specific type of product, use the 'name' parameter to search for relevant items, but be aware that this may not capture all categories or types of products.

Remember, your primary goal is to help users find the best products for their needs from what's available in our store. Be helpful, informative, and always base your recommendations on the actual product data provided by the API.
EOT

  action_group_list = [
    {
      action_group_name = "Get-Product-Recommendations"
      description = "API for retrieving product recommendations"
      action_group_executor = {
        lambda = data.aws_lambda_function.list_products.arn
      }
      api_schema = {
        payload = jsonencode({
          openapi = "3.0.0"
          info = {
            title       = "Product Details API"
            version     = "1.0.0"
            description = "This API retrieves product information. Filtering parameters are passed as query strings. If query strings are empty, it performs a full scan and retrieves the full product list."
          }
          paths = {
            "/products" = {
              get = {
                summary     = "Retrieve product details"
                description = "Retrieves a list of products based on the provided query string parameters. If no parameters are provided, it returns the full list of products."
                parameters = [
                  {
                    name        = "name"
                    in         = "query"
                    description = "Retrieve details for a specific product by name"
                    schema = {
                      type = "string"
                    }
                  }
                ]
                responses = {
                  "200" = {
                    description = "Successful response"
                    content = {
                      "application/json" = {
                        schema = {
                          type  = "array"
                          items = {
                            type = "object"
                            properties = {
                              name = {
                                type = "string"
                              }
                              description = {
                                type = "string"
                              }
                              price = {
                                type = "number"
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                  "500" = {
                    description = "Internal Server Error"
                    content = {
                      "application/json" = {
                        schema = {
                          "$ref" = "#/components/schemas/ErrorResponse"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
          components = {
            schemas = {
              ErrorResponse = {
                type = "object"
                properties = {
                  error = {
                    type        = "string"
                    description = "Error message"
                  }
                }
                required = ["error"]
              }
            }
          }
        })
      }
    }
  ]
}

# Output the agent role ARN for use in application
output "bedrock_agent_role_arn" {
  value       = module.bedrock.agent_resource_role_arn
  description = "The ARN of the IAM role created for the Bedrock agent"
} 