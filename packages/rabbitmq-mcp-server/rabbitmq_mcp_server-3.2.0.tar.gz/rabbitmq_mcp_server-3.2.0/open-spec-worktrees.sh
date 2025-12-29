#!/usr/bin/env sh
# Gerenciador de Spec Drafts (bash/zsh)
#
# Uso:
#   ./open-spec-worktrees.sh "1-4,6,8-10"
#   ./open-spec-worktrees.sh            # interativo, pede números
#   ./open-spec-worktrees.sh --dry-run "1-3,7"  # simula sem criar worktrees
#   ./open-spec-worktrees.sh -h|--help
#
# Comportamento:
# - Lista specs em specs-drafts/1-mvp e specs-drafts/2-full-product
# - Aceita intervalos e listas (ex: 1-3,5,8-10)
# - Para cada número selecionado, cria/usa um git worktree em ../worktrees/<basename>
#   com branch feature/<basename> (usa local, remota, ou cria nova)
# - Abre o editor Cursor (cursor) ou VS Code (code), se disponíveis

set -u

DRY_RUN=0

print_help() {
  cat <<EOF
Gerenciador de Spec Drafts (bash/zsh)

Uso:
  ./open-spec-worktrees.sh [--dry-run|-n] [RANGES]

Exemplos:
  ./open-spec-worktrees.sh               # modo interativo
  ./open-spec-worktrees.sh "1-4,6,8-10"  # não interativo
  ./open-spec-worktrees.sh -n "1-3,7"     # simula sem executar git/editor

Flags:
  -n, --dry-run  Apenas mostra as ações, não executa git/editor
  -h, --help     Mostra esta ajuda
EOF
}

# Cores
ESC="\033"
Green="${ESC}[32m"
Yellow="${ESC}[33m"
Cyan="${ESC}[36m"
Red="${ESC}[31m"
Reset="${ESC}[0m"

# Limpa tela (opcional)
command -v clear >/dev/null 2>&1 && clear || true

printf "%s\n\n" "${Cyan}=== Gerenciador de Spec Drafts ===${Reset}"

# Utilitários
trim() {
  # remove espaços no início/fim
  printf '%s' "$1" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//'
}

abs_path() {
  # Resolve caminho absoluto sem depender de realpath
  # Uso: abs_path <path>
  # shellcheck disable=SC2164
  (
    cd "$1" 2>/dev/null && pwd -P
  )
}

# Listar specs (gera linhas: "num|folder|fileName|baseName|fullPath")
get_spec_drafts() {
  folders="1-mvp 2-full-product"
  tmpfile="$(mktemp)" || exit 1
  for folder in $folders; do
    path="specs-drafts/$folder"
    if [ -d "$path" ]; then
      # Lista arquivos .md e ordena por nome
      # Nota: assumimos nomes sem espaços (como no repo atual)
      find "$path" -type f -name "*.md" -print | sort | while IFS= read -r f; do
        fileName=$(basename "$f")
        baseName=${fileName%*.md}
        # Extrai os 3 primeiros dígitos e remove zeros à esquerda
  num=$(printf '%s' "$baseName" | cut -c1-3 | sed 's/^0*//')
        [ -z "$num" ] && num=0
        printf '%s|%s|%s|%s|%s\n' "$num" "$folder" "$fileName" "$baseName" "$f" >>"$tmpfile"
      done
    fi
  done
  if [ ! -s "$tmpfile" ]; then
    rm -f "$tmpfile"
    return 1
  fi
  # ordena numericamente pelo número
  sort -t '|' -k1,1n "$tmpfile"
  rm -f "$tmpfile"
  return 0
}

# Expande intervalos (ex: "1-4,6,8-10" -> linhas com 1 2 3 4 6 8 9 10)
expand_number_ranges() {
  input=$(trim "$1")
  [ -z "$input" ] && return 0
  # Constrói lista linha-a-linha
  out_tmp="$(mktemp)" || exit 1
  # divide por vírgula
  old_ifs=$IFS; IFS=','
  for part in $input; do
    IFS=$old_ifs
    p=$(trim "$part")
    case "$p" in
      *-*)
        # intervalo a-b
        a=$(printf '%s' "$p" | awk -F- '{print $1}')
        b=$(printf '%s' "$p" | awk -F- '{print $2}')
        if printf '%s' "$a$b" | grep -Eq '^[0-9]+$'; then
          if [ "$a" -le "$b" ] 2>/dev/null; then
            # seq é amplamente disponível no macOS
            seq "$a" "$b" >>"$out_tmp"
          else
            # intervalo invertido, ainda assim expande
            seq "$b" "$a" >>"$out_tmp"
          fi
        fi
        ;;
      *)
        # número simples
        if printf '%s' "$p" | grep -Eq '^[0-9]+$'; then
          printf '%s\n' "$p" >>"$out_tmp"
        fi
        ;;
    esac
    IFS=','
  done
  IFS=$old_ifs
  # ordena e remove duplicados
  if [ -s "$out_tmp" ]; then
    sort -n -u "$out_tmp"
  fi
  rm -f "$out_tmp"
}

# Verifica se existe worktree com o nome (pelo caminho final)
worktree_exists() {
  name="$1"
  git worktree list --porcelain 2>/dev/null \
    | sed -n 's/^worktree //p' \
    | grep -E "/${name}$" >/dev/null 2>&1
}

open_editor() {
  wt_path="$1"
  # Detecta editor disponível: VS Code (code) ou Cursor (cursor)
  editor_cmd=""
  if command -v code >/dev/null 2>&1; then
    editor_cmd="code"
  elif command -v cursor >/dev/null 2>&1; then
    editor_cmd="cursor"
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    if [ -n "$editor_cmd" ]; then
      printf "  %s(dry-run) Abriria %s em: %s%s\n" "$Yellow" "$editor_cmd" "$wt_path" "$Reset"
    else
      printf "  %s(dry-run) Abriria editor em: %s (nenhum editor CLI detectado)%s\n" "$Yellow" "$wt_path" "$Reset"
    fi
    return 0
  fi

  if [ -n "$editor_cmd" ]; then
    printf "  %s  Executando: %s %s%s\n" "$Yellow" "$editor_cmd" "$wt_path" "$Reset"
    ($editor_cmd "$wt_path" >/dev/null 2>&1 &)
    printf "  %s✓ Editor aberto com sucesso (%s)%s\n" "$Green" "$editor_cmd" "$Reset"
  else
    printf "  %s✗ Nenhum editor de linha de comando encontrado ('code' ou 'cursor')%s\n" "$Red" "$Reset"
    printf "  %s  Worktree criado em: %s%s\n" "$Yellow" "$wt_path" "$Reset"
  fi
}

open_spec_worktree() {
  # Argumentos: num folder fileName baseName fullPath
  spec_num="$1"; folder="$2"; fileName="$3"; baseName="$4"
  worktreeName="$baseName"
  branchName="feature/$worktreeName"
  worktreePath="../worktrees/$worktreeName"

  printf "%s[%s] %s%s\n" "$Cyan" "$spec_num" "$fileName" "$Reset"

  # Verifica existência da branch local e remota
  local_exists=1
  git rev-parse --verify --quiet "refs/heads/$branchName" >/dev/null 2>&1 || local_exists=0
  remote_exists=1
  git ls-remote --exit-code --heads origin "$branchName" >/dev/null 2>&1 || remote_exists=0

  # Verifica se worktree já existe
  if worktree_exists "$worktreeName"; then
    printf "  %s→ Worktree já existe, usando existente%s\n" "$Yellow" "$Reset"
  else
    # cria diretório pai se necessário
    mkdir -p "$(dirname "$worktreePath")" 2>/dev/null || true
    if [ "$local_exists" -eq 1 ]; then
      printf "  %s→ Criando worktree com branch existente '%s'%s\n" "$Yellow" "$branchName" "$Reset"
      if [ "$DRY_RUN" -eq 0 ]; then
        git worktree add "$worktreePath" "$branchName"
        if [ "$?" -ne 0 ]; then
          printf "  %s✗ Erro ao criar worktree%s\n" "$Red" "$Reset"
          return
        fi
      else
        printf "  %s(dry-run) git worktree add %s %s%s\n" "$Yellow" "$worktreePath" "$branchName" "$Reset"
      fi
    elif [ "$remote_exists" -eq 1 ]; then
      printf "  %s→ Criando worktree com branch remota 'origin/%s'%s\n" "$Yellow" "$branchName" "$Reset"
      if [ "$DRY_RUN" -eq 0 ]; then
        git worktree add "$worktreePath" -b "$branchName" --track "origin/$branchName"
        if [ "$?" -ne 0 ]; then
          printf "  %s✗ Erro ao criar worktree%s\n" "$Red" "$Reset"
          return
        fi
      else
        printf "  %s(dry-run) git worktree add %s -b %s --track origin/%s%s\n" "$Yellow" "$worktreePath" "$branchName" "$branchName" "$Reset"
      fi
    else
      printf "  %s→ Criando worktree com nova branch '%s'%s\n" "$Yellow" "$branchName" "$Reset"
      if [ "$DRY_RUN" -eq 0 ]; then
        git worktree add "$worktreePath" -b "$branchName"
        if [ "$?" -ne 0 ]; then
          printf "  %s✗ Erro ao criar worktree%s\n" "$Red" "$Reset"
          return
        fi
      else
        printf "  %s(dry-run) git worktree add %s -b %s%s\n" "$Yellow" "$worktreePath" "$branchName" "$Reset"
      fi
    fi
  fi

  # resolve caminho absoluto
  fullWorktreePath=$(abs_path "$worktreePath")
  [ -z "$fullWorktreePath" ] && fullWorktreePath="$worktreePath"
  printf "  %s→ Abrindo editor em: %s%s\n" "$Green" "$fullWorktreePath" "$Reset"
  open_editor "$fullWorktreePath"
}

# ===== Main =====

spec_lines=$(get_spec_drafts) || {
  printf "%sNenhum spec draft encontrado!%s\n" "$Red" "$Reset"
  exit 1
}

printf "%sSpecs disponíveis:%s\n\n" "$Green" "$Reset"

currentFolder=""
printf '%s\n' "$spec_lines" | while IFS='|' read -r num folder fileName baseName fullPath; do
  if [ "$folder" != "$currentFolder" ]; then
    currentFolder="$folder"
    printf "\n%s%s/%s\n" "$Yellow" "$currentFolder" "$Reset"
  fi
  # formata número alinhado em 3 colunas
  printf "  %3s. %s\n" "$num" "$fileName"
done

# Parse flags e coleta números
numbers_input=""
if [ $# -gt 0 ]; then
  while [ $# -gt 0 ]; do
    case "${1}" in
      -n|--dry-run)
        DRY_RUN=1
        shift
        ;;
      -h|--help)
        print_help
        exit 0
        ;;
      --)
        shift
        break
        ;;
      -*)
        printf "%sFlag desconhecida: %s%s\n" "$Red" "$1" "$Reset"
        print_help
        exit 2
        ;;
      *)
        numbers_input="${1}"
        shift
        ;;
    esac
  done
fi
if [ -z "${numbers_input}" ]; then
  printf "\n%sDigite os números desejados%s %s(ex: 1-4,6,8-10)%s:\n" "$Cyan" "$Reset" "$Yellow" "$Reset"
  printf "Números: "
  IFS= read -r numbers_input
  if [ -z "$(trim "$numbers_input")" ]; then
    printf "%sNenhum número informado. Saindo...%s\n" "$Red" "$Reset"
    exit 0
  fi
else
  printf "\n%sUsando números fornecidos: %s%s\n" "$Yellow" "$numbers_input" "$Reset"
fi

printf "%sExpandindo seleção: %s%s\n" "$Yellow" "$numbers_input" "$Reset"
selected_numbers=$(expand_number_ranges "$numbers_input")
sel_display=$(printf '%s\n' "$selected_numbers" | paste -sd',' - | sed 's/,/, /g')
printf "%sNúmeros selecionados: %s%s\n\n" "$Yellow" "$sel_display" "$Reset"

printf "\n%sProcessando specs selecionados...%s\n\n" "$Green" "$Reset"

# Para procurar a linha do spec por número rapidamente, mantemos em arquivo temporário
spec_tmp="$(mktemp)" || exit 1
printf '%s\n' "$spec_lines" >"$spec_tmp"

printf '%s\n' "$selected_numbers" | while IFS= read -r n; do
  [ -z "$n" ] && continue
  # Busca a linha do spec correspondente ao número
  line=$(grep -E "^${n}\|" "$spec_tmp" | head -n1 || true)
  if [ -n "$line" ]; then
    IFS='|' read -r num folder fileName baseName fullPath <<EOF
$line
EOF
    open_spec_worktree "$num" "$folder" "$fileName" "$baseName" "$fullPath"
    printf "\n"
  else
    printf "%sSpec #%s não encontrado!%s\n\n" "$Red" "$n" "$Reset"
  fi
done

rm -f "$spec_tmp" 2>/dev/null || true

printf "%sConcluído!%s\n" "$Green" "$Reset"
