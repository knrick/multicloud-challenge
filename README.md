# MultiCloud E-commerce Platform

A modern e-commerce application demonstrating multi-cloud architecture by leveraging AWS, Google Cloud, and Azure, along with advanced AI capabilities. This project is part of a 5-day MultiCloud Challenge aimed at gaining hands-on experience with various cloud services and modern development practices.

## Technologies Used

### Cloud Services
- **AWS**: EKS, DynamoDB, Lambda, ECR, Bedrock
- **Google Cloud**: BigQuery
- **Azure**: Text Analytics
- **OpenAI**: GPT-4 Integration

### Backend & Frontend
- **FastAPI**: Modern Python web framework
- **HTMX**: Dynamic UI without JavaScript
- **TailwindCSS**: Utility-first CSS framework
- **Jinja2**: Server-side templating
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation
- **Poetry**: Dependency management

### DevOps
- Docker
- Kubernetes
- Terraform
- AWS CodePipeline

## Project Structure

```
multicloud-ecommerce/
├── terraform/          # Infrastructure as Code
├── kubernetes/         # K8s manifests
├── src/
│   └── app/           # FastAPI application
│       ├── api/       # API endpoints
│       ├── core/      # Core functionality
│       ├── models/    # Database models
│       ├── services/  # Business logic
│       ├── static/    # CSS, JS, images
│       └── templates/ # Jinja2 templates
├── lambda/            # AWS Lambda functions
├── ci-cd/            # CI/CD configurations
└── docs/             # Documentation
```

## Getting Started

### Prerequisites
- AWS Account with appropriate permissions
- Google Cloud Account
- Azure Account
- OpenAI API access
- Python 3.11+
- Docker
- kubectl
- Terraform

### Local Development Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   cd src/app
   poetry install
   ```
3. Configure cloud credentials
4. Run locally:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## Features
- Modern, responsive UI using HTMX and TailwindCSS
- Real-time updates without complex JavaScript
- Server-side rendering for better SEO
- AI-powered product recommendations
- Multi-cloud analytics and processing
- Secure authentication and authorization
- Scalable Kubernetes deployment

## Documentation
Detailed documentation can be found in the `/docs` directory:
- Architecture Overview
- Setup Guide
- API Documentation
- Deployment Guide

## License
MIT

## Contributing
Contributions are welcome! Please read our contributing guidelines first. 