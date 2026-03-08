# Deployment script for AI Builder Copilot (Windows)

param(
    [string]$ENV = "dev"
)

Write-Host "Deploying AI Builder Copilot to $ENV environment..." -ForegroundColor Green

# Navigate to infrastructure directory
Set-Location infrastructure

# Activate virtual environment if it exists
if (Test-Path "venv") {
    .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
}

# Deploy CDK stacks
Write-Host "Deploying CDK stacks..." -ForegroundColor Yellow
cdk deploy --all --context env=$ENV --require-approval never

Write-Host "Deployment complete!" -ForegroundColor Green
