#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output "Usage: ./setup-decide.ps1 [-Json] [-Help] [decision_topic]"
    Write-Output "  -Json     Output results in JSON format"
    Write-Output "  -Help     Show this help message"
    exit 0
}

# Load common functions
. "$PSScriptRoot/common.ps1"

# Get repository root
$repoRoot = Get-RepoRoot

# Create decisions directory
$decisionsDir = Join-Path $repoRoot 'docs' 'decisions'
New-Item -ItemType Directory -Path $decisionsDir -Force | Out-Null

# Path to template
$templatePath = Join-Path $repoRoot '.specify' 'templates' 'decide-template.md'

# Function to get next ADR number
function Get-NextAdrNumber {
    param([string]$DecisionsDir)

    $highest = 0

    if (Test-Path $DecisionsDir) {
        Get-ChildItem -Path $DecisionsDir -Filter "*.md" -File | ForEach-Object {
            if ($_.Name -match '^(\d{4})-') {
                $num = [int]$matches[1]
                if ($num -gt $highest) {
                    $highest = $num
                }
            }
        }
    }

    # Return next number in 4-digit format
    return ($highest + 1).ToString("0000")
}

$adrNumber = Get-NextAdrNumber -DecisionsDir $decisionsDir

# Output results
if ($Json) {
    $result = [PSCustomObject]@{
        REPO_ROOT = $repoRoot
        DECISIONS_DIR = $decisionsDir
        ADR_NUMBER = $adrNumber
        TEMPLATE_PATH = $templatePath
    }
    $result | ConvertTo-Json -Compress
} else {
    Write-Output "REPO_ROOT: $repoRoot"
    Write-Output "DECISIONS_DIR: $decisionsDir"
    Write-Output "ADR_NUMBER: $adrNumber"
    Write-Output "TEMPLATE_PATH: $templatePath"
}
