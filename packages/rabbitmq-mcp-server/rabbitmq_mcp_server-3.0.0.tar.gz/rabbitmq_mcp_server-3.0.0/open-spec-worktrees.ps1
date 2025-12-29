#!/usr/bin/env pwsh
# Script para abrir specs em worktrees separados

param(
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$Numbers = ""
)

# Mostrar erros
$ErrorActionPreference = "Continue"

# Cores para output
$ESC = [char]27
$Green = "$ESC[32m"
$Yellow = "$ESC[33m"
$Cyan = "$ESC[36m"
$Red = "$ESC[31m"
$Reset = "$ESC[0m"

# Função para listar todos os spec drafts
function Get-SpecDrafts {
    $specs = @()
    $folders = @("1-mvp", "2-full-product")

    foreach ($folder in $folders) {
        $path = "specs-drafts/$folder"
        if (Test-Path $path) {
            $files = Get-ChildItem -Path $path -Filter "*.md" | Sort-Object Name
            foreach ($file in $files) {
                $specs += [PSCustomObject]@{
                    Number = [int]($file.BaseName.Substring(0, 3))
                    FileName = $file.Name
                    BaseName = $file.BaseName
                    FullPath = $file.FullName
                    Folder = $folder
                }
            }
        }
    }

    return $specs | Sort-Object Number
}

# Função para expandir ranges (ex: "1-4,6,8-10" -> 1,2,3,4,6,8,9,10)
function Expand-NumberRanges {
    param([string]$rangeText)

    $numbers = @()
    $parts = $rangeText -split ','

    foreach ($part in $parts) {
        $part = $part.Trim()
        if ($part -match '^(\d+)-(\d+)$') {
            $start = [int]$matches[1]
            $end = [int]$matches[2]
            $numbers += $start..$end
        }
        elseif ($part -match '^\d+$') {
            $numbers += [int]$part
        }
    }

    return $numbers | Select-Object -Unique | Sort-Object
}

# Função para verificar se worktree existe
function Test-WorktreeExists {
    param([string]$name)

    $worktrees = git worktree list --porcelain
    return $worktrees -match "worktree.*$name"
}

# Função para criar ou usar worktree
function Open-SpecWorktree {
    param(
        [PSCustomObject]$spec
    )

    $worktreeName = $spec.BaseName
    $branchName = "feature/$worktreeName"
    $worktreePath = "../worktrees/$worktreeName"

    Write-Host "${Cyan}[$($spec.Number)] $($spec.FileName)${Reset}"

    # Verificar se branch existe remotamente
    $remoteBranch = git branch -r | Select-String "origin/$branchName"

    # Verificar se branch existe localmente
    $localBranch = git branch | Select-String -Pattern "\s+$branchName$|^\*\s+$branchName$"

    # Verificar se worktree já existe
    if (Test-WorktreeExists $worktreeName) {
        Write-Host "  ${Yellow}→ Worktree já existe, usando existente${Reset}"
    }
    else {
        # Criar diretório para worktrees se não existir
        $worktreeDir = Split-Path $worktreePath -Parent
        if (-not (Test-Path $worktreeDir)) {
            New-Item -ItemType Directory -Path $worktreeDir -Force | Out-Null
        }

        # Criar worktree
        if ($localBranch) {
            Write-Host "  ${Yellow}→ Criando worktree com branch existente '$branchName'${Reset}"
            git worktree add $worktreePath $branchName
        }
        elseif ($remoteBranch) {
            Write-Host "  ${Yellow}→ Criando worktree com branch remota 'origin/$branchName'${Reset}"
            git worktree add $worktreePath -b $branchName --track origin/$branchName
        }
        else {
            Write-Host "  ${Yellow}→ Criando worktree com nova branch '$branchName'${Reset}"
            git worktree add $worktreePath -b $branchName
        }

        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ${Red}✗ Erro ao criar worktree${Reset}"
            return
        }
    }

    # Abrir nova instância do Cursor no worktree
    $fullWorktreePath = Resolve-Path $worktreePath -ErrorAction SilentlyContinue
    if (-not $fullWorktreePath) {
        $fullWorktreePath = (Get-Item $worktreePath).FullName
    }

    Write-Host "  ${Green}→ Abrindo editor em: $fullWorktreePath${Reset}"

    # Tentar abrir com VS Code
    try {
        if (Get-Command code -ErrorAction SilentlyContinue) {
            Write-Host "  ${Yellow}  Executando: code $fullWorktreePath${Reset}"
            Start-Process code -ArgumentList $fullWorktreePath
            Write-Host "  ${Green}✓ Editor aberto com sucesso${Reset}"
        }
        elseif (Get-Command cursor -ErrorAction SilentlyContinue) {
            Write-Host "  ${Yellow}  Executando: cursor $fullWorktreePath${Reset}"
            Start-Process cursor -ArgumentList $fullWorktreePath
            Write-Host "  ${Green}✓ Editor aberto com sucesso${Reset}"
        }
        else {
            Write-Host "  ${Red}✗ Editor não encontrado. Instale 'code' ou 'cursor' no PATH${Reset}"
            Write-Host "  ${Yellow}  Worktree criado em: $fullWorktreePath${Reset}"
        }
    }
    catch {
        Write-Host "  ${Red}✗ Erro ao abrir editor: $_${Reset}"
        Write-Host "  ${Yellow}  Worktree criado em: $fullWorktreePath${Reset}"
    }
}

# Main
Clear-Host
Write-Host "${Cyan}=== Gerenciador de Spec Drafts ===${Reset}`n"

# Listar specs
$specs = Get-SpecDrafts

if ($specs.Count -eq 0) {
    Write-Host "${Red}Nenhum spec draft encontrado!${Reset}"
    exit 1
}

Write-Host "${Green}Specs disponíveis:${Reset}`n"

$currentFolder = ""
foreach ($spec in $specs) {
    if ($spec.Folder -ne $currentFolder) {
        $currentFolder = $spec.Folder
        Write-Host "`n${Yellow}$currentFolder/${Reset}"
    }
    Write-Host ("  {0,3}. {1}" -f $spec.Number, $spec.FileName)
}

# Obter números do usuário
if ([string]::IsNullOrWhiteSpace($Numbers)) {
    Write-Host "`n${Cyan}Digite os números desejados${Reset} ${Yellow}(ex: 1-4,6,8-10)${Reset}:"
    $userInput = Read-Host "Números"

    if ([string]::IsNullOrWhiteSpace($userInput)) {
        Write-Host "${Red}Nenhum número informado. Saindo...${Reset}"
        exit 0
    }
}
else {
    $userInput = $Numbers
    Write-Host "`n${Yellow}Usando números fornecidos: $userInput${Reset}"
}

# Expandir ranges
Write-Host "${Yellow}Expandindo seleção: $userInput${Reset}"
$selectedNumbers = Expand-NumberRanges $userInput
Write-Host "${Yellow}Números selecionados: $($selectedNumbers -join ', ')${Reset}`n"

Write-Host "`n${Green}Processando specs selecionados...${Reset}`n"

foreach ($num in $selectedNumbers) {
    $spec = $specs | Where-Object { $_.Number -eq $num }

    if ($spec) {
        Open-SpecWorktree $spec
        Write-Host ""
    }
    else {
        Write-Host "${Red}Spec #$num não encontrado!${Reset}`n"
    }
}

Write-Host "${Green}Concluído!${Reset}"
