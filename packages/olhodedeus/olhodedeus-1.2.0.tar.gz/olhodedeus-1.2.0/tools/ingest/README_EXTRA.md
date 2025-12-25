Extra: Automação de ingest

Arquivos novos:
- `scraper.py`: baixa URLs listadas em `allowed_sources.json` e gera CSVs extraídos em `raw_data/`.
- `pipeline.py`: wrapper que chama `ingest_categorize.py` e opcionalmente encripta o DB; move arquivos para `raw_data/processed/`.
- `watch_and_ingest.py`: observa `raw_data/` e dispara o pipeline para novos arquivos.
- `utils.py`: funções utilitárias de download seguro e encriptação GPG simétrica.
- `extractors.py`: heurísticas para extrair pares email:password e CPFs de texto.

Fluxo recomendado:
1) Preencha `tools/ingest/allowed_sources.json` com as URLs que você tem permissão para processar.
2) Rode `python3 tools/ingest/scraper.py` para baixar arquivos autorizados para `raw_data/`.
3) Rode `python3 tools/ingest/watch_and_ingest.py --encrypt` para processar automaticamente novos arquivos e encriptar o DB.

Segurança e conformidade
- Verifique sempre a licença/termos antes de automatizar downloads.
- Nunca comite `raw_data/` ou `data/` no repositório. O `.gitignore` já inclui esses paths.
- A encriptação exige `gpg` instalado no sistema.
