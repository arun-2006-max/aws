# Setup script for AI Builder Copilot development environment (Windows)

Write-Host "Setting up AI Builder Copilot development environment..." -ForegroundColor Green

# Setup infrastructure
Write-Host "Setting up infrastructure..." -ForegroundColor Yellow
Set-Location infrastructure
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Set-Location ..

# Setup Lambda functions
Write-Host "Setting up Lambda functions..." -ForegroundColor Yellow
Set-Location lambda
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Set-Location ..

# Setup frontend
Write-Host "Setting up frontend..." -ForegroundColor Yellow
Set-Location frontend
npm install
Set-Location ..

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Configure AWS credentials: aws configure"
Write-Host "2. Bootstrap CDK: cd infrastructure; cdk bootstrap"
Write-Host "3. Deploy infrastructure: .\scripts\deploy.ps1 dev"
Write-Host "4. Start frontend: cd frontend; npm start"
