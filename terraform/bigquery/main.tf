terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  credentials = file("google_credentials.json")
  project     = "cloudmart-456007"
  region      = "us-east1"
}

# Create BigQuery dataset
resource "google_bigquery_dataset" "cloudmart" {
  dataset_id  = "cloudmart"
  description = "CloudMart e-commerce analytics dataset"
  location    = "US"

  # Optional: Set an expiration time for tables in this dataset (in ms)
  default_table_expiration_ms = 2592000000 # 30 days

  # Optional: Set access controls
  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }
  access {
    role          = "READER"
    special_group = "projectReaders"
  }
  access {
    role          = "WRITER"
    special_group = "projectWriters"
  }
}

# Create orders table
resource "google_bigquery_table" "orders" {
  dataset_id = google_bigquery_dataset.cloudmart.dataset_id
  table_id   = "cloudmart-orders"

  time_partitioning {
    type = "DAY"
    field = "createdAt"
  }

  schema = jsonencode([
    {
      name = "id",
      type = "STRING",
      mode = "REQUIRED",
      description = "Order ID"
    },
    {
      name = "items",
      type = "JSON",
      mode = "REQUIRED",
      description = "Order items"
    },
    {
      name = "userEmail",
      type = "STRING",
      mode = "REQUIRED",
      description = "Customer email"
    },
    {
      name = "total",
      type = "FLOAT",
      mode = "REQUIRED",
      description = "Order total"
    },
    {
      name = "status",
      type = "STRING",
      mode = "REQUIRED",
      description = "Order status"
    },
    {
      name = "createdAt",
      type = "TIMESTAMP",
      mode = "REQUIRED",
      description = "Order creation timestamp"
    }
  ])
} 