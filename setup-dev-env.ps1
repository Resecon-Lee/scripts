#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Complete development environment setup script for Windows
.DESCRIPTION
    Installs and configures essential development tools for React, Node.js, Python, and web development
.NOTES
    Run as Administrator in PowerShell
    Author: Generated for seasoned software engineer
#>

Write-Host "=== Development Environment Setup Script ===" -ForegroundColor Green
Write-Host "Setting up your development environment..." -ForegroundColor Yellow

# Set execution policy if needed
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Install Chocolatey if not already installed
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey package manager..." -ForegroundColor Cyan
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    refreshenv
}

# Install Scoop if not already installed
if (!(Get-Command scoop -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Scoop package manager..." -ForegroundColor Cyan
    Invoke-RestMethod get.scoop.sh | Invoke-Expression
    scoop bucket add extras
    scoop bucket add versions
}

Write-Host "Installing development tools via Chocolatey..." -ForegroundColor Cyan

# Essential development tools
$chocoPackages = @(
    'git',
    'nodejs',
    'python',
    'yarn',
    'firefox',
    'googlechrome',
    'postman',
    'insomnia-rest-api-client',
    'mongodb',
    'postgresql',
    'redis-64',
    'mysql',
    'dbeaver',
    'tableplus',
    'ngrok',
    'fiddler',
    'wireshark',
    'curl',
    'wget',
    'jq',
    'vim',
    'neovim',
    'sublimetext4',
    'notepadplusplus',
    'gitextensions',
    'sourcetree',
    'github-desktop',
    'tortoisegit',
    'putty',
    'winscp',
    'filezilla',
    'imagemagick',
    '7zip',
    'winrar',
    'everything',
    'powertoys',
    'windows-terminal',
    'oh-my-posh',
    'starship',
    'fzf',
    'ripgrep',
    'bat',
    'fd',
    'tree-sitter',
    'lazygit',
    'htop',
    'bottom',
    'dust'
)

foreach ($package in $chocoPackages) {
    Write-Host "Installing $package..." -ForegroundColor Yellow
    choco install $package -y
}

Write-Host "Installing additional tools via Scoop..." -ForegroundColor Cyan

# Additional CLI tools and utilities
$scoopPackages = @(
    'gh',
    'hub',
    'delta',
    'exa',
    'zoxide',
    'tokei',
    'hyperfine',
    'glow',
    'fx',
    'httpie',
    'ctop',
    'dive'
)

foreach ($package in $scoopPackages) {
    Write-Host "Installing $package..." -ForegroundColor Yellow
    scoop install $package
}

# Install global npm packages
Write-Host "Installing global npm packages..." -ForegroundColor Cyan
$npmPackages = @(
    '@vue/cli',
    '@angular/cli',
    'create-react-app',
    'next',
    'nuxt',
    'gatsby-cli',
    'vite',
    'typescript',
    'ts-node',
    'nodemon',
    'concurrently',
    'pm2',
    'serve',
    'http-server',
    'live-server',
    'json-server',
    'eslint',
    'prettier',
    'stylelint',
    'sass',
    'less',
    'stylus',
    'autoprefixer',
    'postcss-cli',
    'tailwindcss',
    'webpack',
    'webpack-cli',
    'parcel',
    'rollup',
    'jest',
    'mocha',
    'cypress',
    'playwright',
    'puppeteer',
    'lighthouse',
    'npm-check-updates',
    'nvm-windows',
    'pnpm',
    'lerna',
    'nx',
    'turbo',
    'vercel',
    'netlify-cli',
    'firebase-tools',
    'heroku'
)

foreach ($package in $npmPackages) {
    Write-Host "Installing npm package: $package" -ForegroundColor Yellow
    npm install -g $package
}

# Install global Python packages
Write-Host "Installing Python packages..." -ForegroundColor Cyan
python -m pip install --upgrade pip
$pythonPackages = @(
    'virtualenv',
    'pipenv',
    'poetry',
    'cookiecutter',
    'black',
    'isort',
    'flake8',
    'mypy',
    'pylint',
    'autopep8',
    'jupyter',
    'jupyterlab',
    'requests',
    'flask',
    'django',
    'fastapi',
    'uvicorn',
    'gunicorn',
    'celery',
    'redis',
    'pymongo',
    'psycopg2',
    'sqlalchemy',
    'alembic',
    'pytest',
    'pytest-cov',
    'coverage',
    'tox',
    'pre-commit',
    'httpx',
    'aiohttp'
)

foreach ($package in $pythonPackages) {
    Write-Host "Installing Python package: $package" -ForegroundColor Yellow
    pip install $package
}

# Configure Git (you'll need to update with your details)
Write-Host "Configuring Git..." -ForegroundColor Cyan
Write-Host "Please configure Git with your details:" -ForegroundColor Yellow
$gitName = Read-Host "Enter your Git name"
$gitEmail = Read-Host "Enter your Git email"

git config --global user.name "$gitName"
git config --global user.email "$gitEmail"
git config --global init.defaultBranch main
git config --global pull.rebase false
git config --global core.autocrlf true
git config --global core.editor "code --wait"

# Enable WSL features if not already enabled
Write-Host "Ensuring WSL features are enabled..." -ForegroundColor Cyan
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Install Windows Subsystem for Linux kernel update
Write-Host "Installing WSL2 Linux kernel update..." -ForegroundColor Cyan
$wslUpdateUrl = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
$wslUpdatePath = "$env:TEMP\wsl_update_x64.msi"
Invoke-WebRequest -Uri $wslUpdateUrl -OutFile $wslUpdatePath
Start-Process msiexec.exe -Wait -ArgumentList "/I $wslUpdatePath /quiet"

# Set WSL 2 as default version
wsl --set-default-version 2

# Install Ubuntu on WSL2 (if desired)
Write-Host "Would you like to install Ubuntu 22.04 LTS on WSL2? (y/n)" -ForegroundColor Yellow
$installUbuntu = Read-Host
if ($installUbuntu -eq 'y' -or $installUbuntu -eq 'Y') {
    wsl --install -d Ubuntu-22.04
}

# Create development directories
Write-Host "Creating development directories..." -ForegroundColor Cyan
$devDirs = @(
    "$env:USERPROFILE\Dev",
    "$env:USERPROFILE\Dev\Projects",
    "$env:USERPROFILE\Dev\Learning",
    "$env:USERPROFILE\Dev\Tools",
    "$env:USERPROFILE\Dev\Scripts"
)

foreach ($dir in $devDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created directory: $dir" -ForegroundColor Green
    }
}

# Install PowerShell modules
Write-Host "Installing PowerShell modules..." -ForegroundColor Cyan
$psModules = @(
    'PowerShellGet',
    'PSReadLine',
    'Terminal-Icons',
    'PSFzf',
    'z',
    'posh-git'
)

foreach ($module in $psModules) {
    Write-Host "Installing PowerShell module: $module" -ForegroundColor Yellow
    Install-Module -Name $module -Force -SkipPublisherCheck
}

# Configure PowerShell profile
Write-Host "Configuring PowerShell profile..." -ForegroundColor Cyan
$profileContent = @'
# PowerShell Profile Configuration

# Import modules
Import-Module posh-git
Import-Module Terminal-Icons
Import-Module PSFzf
Import-Module z

# Set up Oh My Posh or Starship prompt
# Uncomment one of the following lines:
# oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH\paradox.omp.json" | Invoke-Expression
# Invoke-Expression (&starship init powershell)

# PSReadLine configuration
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -PredictionViewStyle ListView
Set-PSReadLineKeyHandler -Key Tab -Function Complete

# Aliases
Set-Alias -Name ll -Value Get-ChildItem
Set-Alias -Name grep -Value Select-String
Set-Alias -Name which -Value Get-Command
Set-Alias -Name touch -Value New-Item

# Functions
function .. { Set-Location .. }
function ... { Set-Location ..\.. }
function .... { Set-Location ..\..\.. }

function gst { git status }
function gaa { git add . }
function gcm { param($message) git commit -m $message }
function gp { git push }
function gl { git pull }

function mkcd { param($path) mkdir $path; cd $path }
function open { param($path) Start-Process $path }

# Quick navigation to development folder
function dev { Set-Location "$env:USERPROFILE\Dev" }
function projects { Set-Location "$env:USERPROFILE\Dev\Projects" }

Write-Host "Development environment loaded!" -ForegroundColor Green
'@

if (!(Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force
}
$profileContent | Out-File -FilePath $PROFILE -Encoding UTF8

# Final message
Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Installed tools include:" -ForegroundColor Cyan
Write-Host "• Package managers: Chocolatey, Scoop, npm, pip, yarn, pnpm" -ForegroundColor White
Write-Host "• Runtimes: Node.js, Python" -ForegroundColor White
Write-Host "• Databases: MongoDB, PostgreSQL, Redis, MySQL" -ForegroundColor White
Write-Host "• Browsers: Chrome, Firefox" -ForegroundColor White
Write-Host "• API Tools: Postman, Insomnia" -ForegroundColor White
Write-Host "• Version Control: Git, GitHub CLI, GitExtensions, SourceTree" -ForegroundColor White
Write-Host "• CLI Tools: fzf, ripgrep, bat, exa, zoxide, and many more" -ForegroundColor White
Write-Host "• Development frameworks and tools via npm and pip" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart your terminal to load the new profile" -ForegroundColor White
Write-Host "2. Configure your Git credentials if you didn't during setup" -ForegroundColor White
Write-Host "3. Install any additional browser extensions you need" -ForegroundColor White
Write-Host "4. Set up your preferred terminal theme (Oh My Posh or Starship)" -ForegroundColor White
Write-Host "5. Use pnpm for new projects (shortcuts: pn, pni, pna, pnr)" -ForegroundColor White
Write-Host "6. Consider restarting your computer to complete WSL setup" -ForegroundColor White
Write-Host ""
Write-Host "Happy coding! 🚀" -ForegroundColor Green
