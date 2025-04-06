terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Create a resource group
resource "azurerm_resource_group" "cloudmart" {
  name     = "cloudmart-analytics"
  location = "eastus"  # Same region as our other resources

  tags = {
    Environment = "Dev"
    Project     = "CloudMart"
    ManagedBy   = "Terraform"
  }
}

# Create Language Service account (Text Analytics)
resource "azurerm_cognitive_account" "language" {
  name                = "cloudmart-language"
  location            = azurerm_resource_group.cloudmart.location
  resource_group_name = azurerm_resource_group.cloudmart.name
  kind                = "TextAnalytics"  # This creates a Language Service resource
  sku_name            = "F0"  # Free tier

  tags = {
    Environment = "Dev"
    Project     = "CloudMart"
    ManagedBy   = "Terraform"
  }
}

# Output the endpoint and key for use in our application
output "language_service_endpoint" {
  value     = azurerm_cognitive_account.language.endpoint
  sensitive = false
}

output "language_service_key" {
  value     = azurerm_cognitive_account.language.primary_access_key
  sensitive = true
} 