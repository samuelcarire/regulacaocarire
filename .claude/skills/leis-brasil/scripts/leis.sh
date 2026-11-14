#!/usr/bin/env bash
# Consulta ao acervo github.com/ctresb/leis (legislação brasileira em Markdown).
# O acervo tem ~1,2 milhão de normas; nunca é baixado inteiro. Baixa-se só o
# índice de caminhos (clone sem conteúdo, ~45 MB) e, sob demanda, pastas ou
# arquivos individuais.
#
# Uso:
#   leis.sh atualizar                 cria/atualiza o índice local
#   leis.sh localizar TERMO...        caminhos que contêm TODOS os termos (regex, sem maiúsculas)
#   leis.sh ler CAMINHO               imprime a norma (baixa só esse arquivo)
#   leis.sh baixar PASTA...           baixa todas as normas de uma ou mais pastas
#   leis.sh buscar REGEX PASTA...     procura REGEX no título/ementa das normas das pastas
#   leis.sh texto REGEX PASTA...      procura REGEX no texto inteiro das normas das pastas
#   leis.sh pastas [PREFIXO]          lista subpastas e quantas normas cada uma tem
set -euo pipefail
# Locale UTF-8 para que -i trate acentos (diárias = DIÁRIAS).
if locale -a 2>/dev/null | grep -qi '^c\.utf-\?8$'; then export LC_ALL=C.UTF-8; fi

REPO_URL="https://github.com/ctresb/leis.git"
RAW="https://raw.githubusercontent.com/ctresb/leis/main"
CACHE="${LEIS_CACHE:-$HOME/.cache/leis-brasil}"
DIR="$CACHE/leis"
IDX="$CACHE/normas.txt"

die() { echo "erro: $*" >&2; exit 1; }

atualizar() {
  mkdir -p "$CACHE"
  if [ ! -d "$DIR/.git" ]; then
    git clone -q --depth 1 --filter=blob:none --no-checkout "$REPO_URL" "$DIR"
    git -C "$DIR" sparse-checkout set --no-cone '/README.md' >/dev/null
    git -C "$DIR" checkout -q main
  else
    git -C "$DIR" fetch -q --depth 1 --filter=blob:none origin main
    git -C "$DIR" reset -q --hard origin/main
  fi
  # Só as normas: .md fora das pastas técnicas (_fonte, _indice, _lotes...).
  git -C "$DIR" ls-tree -r --name-only HEAD \
    | grep '\.md$' | grep -v -E '(^|/)_' | grep -v -E '^[^/]+\.md$|^scripts/' > "$IDX.tmp"
  mv "$IDX.tmp" "$IDX"
  echo "índice: $(wc -l < "$IDX") normas ($(git -C "$DIR" log -1 --format=%cs))"
}

garantir() { [ -s "$IDX" ] || atualizar >&2; }

localizar() {
  [ $# -ge 1 ] || die "informe ao menos um termo"
  garantir
  local out; out=$(grep -i -E -- "$1" "$IDX" || true); shift
  for t in "$@"; do out=$(printf '%s\n' "$out" | grep -i -E -- "$t" || true); done
  local n; n=$(printf '%s' "$out" | grep -c . || true)
  printf '%s\n' "$out" | head -100
  [ "$n" -gt 100 ] && echo "... ($n resultados; refine os termos)" >&2
  [ "$n" -eq 0 ] && echo "(nenhum caminho encontrado)" >&2
  return 0
}

ler() {
  [ $# -eq 1 ] || die "informe um caminho"
  local p="${1#/}"
  if [ -f "$DIR/$p" ]; then cat "$DIR/$p"; return; fi
  curl -sSfL "$RAW/$p" || die "não consegui baixar $p"
}

baixar() {
  [ $# -ge 1 ] || die "informe ao menos uma pasta"
  garantir
  local args=()
  for p in "$@"; do
    p="${p#/}"; p="${p%/}"
    grep -q -m1 "^$p/" "$IDX" || die "pasta sem normas no índice: $p (veja: leis.sh pastas)"
    args+=("/$p/")
  done
  git -C "$DIR" sparse-checkout add "${args[@]}" >/dev/null
  echo "baixado: $*" >&2
}

_procurar() {
  local modo="$1" re="$2"; shift 2
  [ $# -ge 1 ] || die "informe ao menos uma pasta"
  baixar "$@" 2>/dev/null
  local dirs=(); for p in "$@"; do p="${p#/}"; dirs+=("${p%/}"); done
  if [ "$modo" = cab ]; then
    (cd "$DIR" && grep -r -i -E -H -m2 --include='*.md' "^(titulo|ementa): .*($re)" "${dirs[@]}") \
      | head -200 || true
  else
    (cd "$DIR" && grep -r -i -E -l --include='*.md' -- "$re" "${dirs[@]}") | head -200 || true
  fi
}

pastas() {
  garantir
  local pre="${1:-}"; pre="${pre#/}"; pre="${pre%/}"
  local nivel=1; [ -n "$pre" ] && nivel=$(( $(tr -cd / <<<"$pre/" | wc -c) + 1 ))
  grep -E "^${pre:+$pre/}" "$IDX" | cut -d/ -f1-"$nivel" | sort | uniq -c
}

cmd="${1:-}"; shift || true
case "$cmd" in
  atualizar) atualizar ;;
  localizar) localizar "$@" ;;
  ler)       ler "$@" ;;
  baixar)    baixar "$@" ;;
  buscar)    [ $# -ge 2 ] || die "uso: buscar REGEX PASTA..."; _procurar cab "$@" ;;
  texto)     [ $# -ge 2 ] || die "uso: texto REGEX PASTA..."; _procurar txt "$@" ;;
  pastas)    pastas "$@" ;;
  *) sed -n '2,15p' "$0"; exit 1 ;;
esac
