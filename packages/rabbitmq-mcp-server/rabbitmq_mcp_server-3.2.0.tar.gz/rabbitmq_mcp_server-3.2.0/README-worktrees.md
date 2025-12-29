# Gerenciador de Spec Drafts com Worktrees

Scripts para facilitar o trabalho com múltiplos spec drafts em worktrees separados.

## Uso (PowerShell)

```powershell
.\open-spec-worktrees.ps1
```

## Uso (macOS/Linux – bash/zsh)

```bash
./open-spec-worktrees.sh
# Interativo: informe, por exemplo, 1-4,6,8-10
```

Modo não-interativo:

```bash
./open-spec-worktrees.sh "1-4,6,8-10"
```

Dry-run (simula sem efeitos colaterais):

```bash
./open-spec-worktrees.sh --dry-run "1-3,7"
```

## Funcionalidades

1. **Lista todos os spec drafts** organizados por pasta (1-mvp, 2-full-product)
2. **Aceita entrada flexível** de números:
   - Números individuais: `1,2,3`
   - Ranges: `1-5`
   - Combinações: `1-4,6,8-10,15`
3. **Gerencia worktrees automaticamente**:
   - Cria worktree se não existir
   - Usa worktree existente se já criado
   - Cria branch `feature/XXX-spec-name` automaticamente
   - Conecta a branches remotas se existirem
4. **Abre editor automaticamente** em cada worktree
  - macOS/Linux: tenta `cursor`, depois `code`
  - Windows/PowerShell: tenta `cursor`, depois `code`

## Estrutura de Worktrees

Os worktrees são criados em `../worktrees/` com a seguinte estrutura:

```
rabbitmq-mcp-server/          (repositório principal)
worktrees/
  ├── 001-base-architecture/  (worktree + branch feature/001-base-architecture)
  ├── 002-basic-rabbitmq-connection/
  └── ...
```

## Exemplos (PowerShell)

### Trabalhar nos primeiros 4 specs do MVP

```powershell
.\open-spec-worktrees.ps1
# Digite: 1-4
```

### Trabalhar em specs específicos

```powershell
.\open-spec-worktrees.ps1
# Digite: 1,5,9,15
```

### Trabalhar em um range com exceções

```powershell
.\open-spec-worktrees.ps1
# Digite: 1-8,10-12,15-20
```

## Exemplos (bash/zsh)

### Trabalhar nos primeiros 4 specs do MVP

```bash
./open-spec-worktrees.sh "1-4"
```

### Trabalhar em specs específicos

```bash
./open-spec-worktrees.sh "1,5,9,15"
```

### Trabalhar em um range com exceções

```bash
./open-spec-worktrees.sh "1-8,10-12,15-20"
```

## Gerenciamento de Worktrees

### Listar worktrees ativos

```bash
git worktree list
```

### Remover um worktree

```bash
git worktree remove ../worktrees/001-base-architecture
```

### Remover todos os worktrees

```bash
# Cuidado: remove todos os worktrees fora do repo principal
git worktree list --porcelain \
  | awk '/^worktree /{print $2}' \
  | grep -v "/rabbitmq-mcp-server$" \
  | xargs -I{} git worktree remove {} --force
```

## Requisitos

- Git instalado
- PowerShell 7+ (recomendado para Windows) ou bash/zsh (macOS/Linux)
- Editor `cursor` ou `code` no PATH

## Troubleshooting

### Editor não abre automaticamente

O script tenta abrir com `cursor` primeiro, depois `code`. Se nenhum estiver no PATH:

1. Adicione o editor ao PATH do sistema
2. Ou abra manualmente: o caminho do worktree é exibido no console

### Erro ao criar worktree

Se um worktree não pode ser criado, verifique:

- Se já existe um worktree com esse nome: `git worktree list`
- Se a branch está em uso em outro lugar
- Se há alterações não commitadas

### Limpar worktrees órfãos

```bash
git worktree prune
```
