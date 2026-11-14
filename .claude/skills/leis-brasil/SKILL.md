---
name: leis-brasil
description: Consulta o texto de leis, decretos, atos de órgãos reguladores (RFB, ANVISA...), súmulas e normas estaduais e municipais brasileiras no acervo aberto github.com/ctresb/leis (~1,2 milhão de normas em Markdown, com link para a fonte oficial). Use quando precisar do texto ou da ementa de uma norma brasileira, descobrir qual norma trata de um assunto, ou conferir um artigo antes de citá-lo.
---

# Leis do Brasil (acervo ctresb/leis)

O acervo é grande demais para baixar (1,2 milhão de arquivos). O script
`scripts/leis.sh` baixa só o **índice de caminhos** (~45 MB, segundos) e, sob demanda,
um arquivo ou uma pasta.

```bash
S=.claude/skills/leis-brasil/scripts/leis.sh
$S atualizar                       # 1ª vez na sessão (ou para pegar normas novas)
$S localizar lcp 116-2003          # caminhos que contêm todos os termos
$S ler federal/leis-complementares/2003/lcp-116-2003-07-31.md
$S pastas estaduais/CE             # o que existe numa pasta, com contagem
$S buscar 'diárias' estaduais/CE/leis-ordinarias    # regex no título/ementa
$S texto 'art\. 3º' federal/leis-complementares/2003 # regex no texto inteiro
```

`buscar` e `texto` baixam a pasta inteira antes de procurar. Use a pasta mais
estreita possível: até alguns milhares de arquivos é rápido, mas
`reguladores/rfb` (75 mil) ou `estaduais` inteiro é pesado demais. Prefira
recortar por ano (`reguladores/rfb/2024`).

Cache em `~/.cache/leis-brasil` (mude com `LEIS_CACHE`).

## Como os caminhos são formados

| Norma | Caminho |
|---|---|
| Constituição Federal | `constituicao.md` |
| Lei federal | `federal/leis-ordinarias/AAAA/lei-NUMERO-AAAA-MM-DD.md` |
| Lei complementar federal | `federal/leis-complementares/AAAA/lcp-NUMERO-AAAA-MM-DD.md` |
| Outras federais | `federal/{decretos,decretos-lei,medidas-provisorias,emendas-constitucionais,decretos-legislativos,resolucoes-senado,...}/AAAA/` |
| Estaduais | `estaduais/UF/{constituicao,leis-ordinarias,leis-complementares,emendas-constitucionais,...}/AAAA/` (o nome termina em `-idNNNN`) |
| Reguladores | `reguladores/<orgao>/...` (rfb, anvisa, ms, mapa, bcb, conselhos-profissionais, ...). Os nomes são códigos, então use `buscar` |
| Jurisprudência | `jurisprudencia/{stf,stj,tst,tnu,trf4,outros-tribunais}/` |
| Municipais | `municipais/UF/<municipio-sem-acento>/<tipo>/AAAA/` |

O número **não tem ponto**: Lei 14.133 vira `lei-14133`. Para achar uma norma pelo
número, use `localizar` com o prefixo e o número (`localizar lei-8666`), e acrescente
`^federal` ou `^estaduais/CE` se aparecerem leis homônimas de outros entes.

Cada arquivo tem um cabeçalho YAML (`titulo`, `ementa`, `data`, `situacao`,
`revogada`, `versao_texto`, `fonte`, `baixado_em`) e depois o texto.

## Regras ao responder

1. **Cite a fonte oficial**, isto é, o campo `fonte` do cabeçalho, e não só o GitHub.
   Os textos são conversões automáticas e OCR. O próprio acervo avisa que não
   substituem o Diário Oficial. Para fundamentar um ato (parecer, empenho,
   retenção), recomende conferir na fonte.
2. **Verifique a vigência**: veja `revogada`, `situacao` e `versao_texto`
   (compilada ou original), e as notas "(Vide ...)" e "(Redação dada por ...)" no
   texto. Uma norma original pode ter sido alterada depois.
3. **Lacunas conhecidas**:
   - **Ceará estadual**: só leis, sem decretos.
   - **Municipal**: cobertura pequena. **Cariré não está no acervo** (no CE só há
     Fortaleza, Amontada e poucos outros). Para normas de Cariré, peça o texto ao
     usuário ou consulte o Diário Oficial dos Municípios (APRECE).
   - **Federal**: está avançando. Use `pastas` para ver o que existe antes de
     concluir que uma norma não está lá.
4. Se `localizar` não achar nada, tente variações (sem data, outro tipo de pasta) e
   `pastas` antes de dizer que a norma não existe no acervo. Não existir no acervo
   não quer dizer que a norma não exista.
