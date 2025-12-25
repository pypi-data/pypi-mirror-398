# Ingestão e Análise de Datasets de Senhas (seguro)

Este diretório contém ferramentas auxiliares para ingerir datasets de senhas
para fins de pesquisa/estudo de forma mais segura — o fluxo evita armazenar
senhas em texto plano.

Arquivos:
- `ingest_hibp.py`: ingere arquivos no formato HIBP Pwned Passwords
  (SHA1:count por linha) para um banco SQLite (`data/passwords.db`).
  Opcionalmente encripta o DB com GPG simétrico (`--encrypt`).
- `analyze.py`: consulta básica do DB (top N e sumário).

Uso recomendado (exemplos):

1) Ingerir um arquivo local:
```bash
python3 tools/ingest/ingest_hibp.py raw_data/pwned-passwords-sha1-1-1.txt --db data/passwords.db --encrypt
```

2) Ingerir a partir de URL (apenas quando a fonte for legal/permitida):
```bash
python3 tools/ingest/ingest_hibp.py "https://example.org/pwned-passwords.txt.gz" --db data/passwords.db
```

3) Analisar o DB:
```bash
python3 tools/ingest/analyze.py --db data/passwords.db --summary --top 50
```

4) Ingestão categorizada (CSV com colunas como `email,name,password,service,cpf`):
```bash
python3 tools/ingest/ingest_categorize.py --source raw_data/leak.csv --db data/leaks.db --hash-salt "minha-senha-secreta"
```

Importante: por padrão o script armazena apenas hashes (SHA256) dos valores
sensíveis para reduzir risco de manter PII em texto claro. Para permitir
armazenar plaintext use `--allow-plaintext` (não recomendado).

5) Buscar no DB categorizado:
```bash
python3 tools/ingest/search.py --db data/leaks.db --category netflix --limit 20
```


Avisos legais e de segurança:
- Nunca colete dados de vazamentos contendo informações pessoais sem
  permissão e sem garantir conformidade legal. Use apenas datasets com
  licença apropriada ou criados para pesquisa.
- Não comite arquivos em `data/`, `raw_data/` ou qualquer arquivo contendo
  dados sensíveis no repositório. O `.gitignore` deste repositório já
  contém regras para ignorar esses arquivos.
- Quando possível, trabalhe com hashes (como HIBP) ou datasets públicos
  especificamente preparados para pesquisa (Kaggle etc.).
