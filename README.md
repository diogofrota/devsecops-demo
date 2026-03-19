# devsecops-demo

Pipeline de seguranca com dois eixos:
1. DevSecOps (analise de codigo para detectar credenciais expostas).
2. CloudSecurity (analise CSPM baseada em configuracao cloud simulada).

O projeto foi desenhado para rodar principalmente no GitHub Actions e gerar:
1. Relatorios tecnicos em JSON.
2. Relatorios executivos gerados por IA.
3. Artifact no workflow.
4. E-mail consolidado com os resultados.

## Objetivo

Este repositorio serve para estudo e avaliacao pratica de:
1. Automacao de seguranca no push para `main`.
2. Encadeamento de scripts Python em pipeline CI.
3. Integracao com OpenAI (Responses API e Assistant API com fallback).
4. Consolidacao de saida tecnica + executiva para auditoria.

## Estrutura do Projeto

```text
.
|-- .github/workflows/test-python.yml
|-- cloud/
|   `-- aws_mock.json
|-- cloudSecurity/
|   |-- __init__.py
|   |-- cspm_scan.py
|   |-- prepare_ai_input.py
|   `-- ai_analysis.py
|-- devSecOps/
|   |-- __init__.py
|   |-- scan.py
|   |-- prepare_ai_input.py
|   `-- ai_analysis.py
|-- index.html
`-- send_email.py
```

## Fluxo End-to-End

### Fluxo de alto nivel

```text
push em main
  -> GitHub Actions inicia
  -> DevSecOps scan.py
  -> DevSecOps prepare_ai_input.py
  -> DevSecOps ai_analysis.py
  -> CloudSecurity cspm_scan.py
  -> CloudSecurity prepare_ai_input.py
  -> CloudSecurity ai_analysis.py
  -> upload artifact
  -> send_email.py
```

### Fluxo de arquivos gerados (REPORTS_DIR)

```text
credential_report.json -> ai_input.txt -> final_report.txt
cloud_report.json      -> cloud_ai_input.txt -> cloud_final_report.txt
```

## Workflow do GitHub Actions

Arquivo: `.github/workflows/test-python.yml`

Trigger:
1. Evento `push`.
2. Apenas branch `main`.

Passos principais:
1. Checkout do codigo.
2. Setup Python 3.10.
3. Instalacao da dependencia `openai`.
4. Execucao do fluxo DevSecOps.
5. Execucao do fluxo CloudSecurity.
6. Upload de artifact `relatorios-seguranca`.
7. Envio de e-mail consolidado.

Variavel de job:
1. `REPORTS_DIR=/tmp/security-reports`

Observacao:
1. Nao existe dependencia de pasta `reports/` versionada no repositorio.
2. A saida em CI fica em `/tmp/security-reports` no runner.

## Scripts e Responsabilidades

### 1) devSecOps/scan.py

Responsabilidade:
1. Percorrer arquivos do repositorio.
2. Aplicar regex para detectar padroes de segredo.
3. Gerar `credential_report.json`.

Padroes atuais:
1. `API_KEY`
2. `SECRET_KEY`
3. `ACCESS_TOKEN`
4. `PASSWORD`

Trecho relevante:

```python
PATTERNS = [
    ("API_KEY", r"API_KEY\\s*=\\s*[\\\"'][^\\\"']+[\\\"']"),
    ("SECRET_KEY", r"SECRET_KEY\\s*=\\s*[\\\"'][^\\\"']+[\\\"']"),
    ("ACCESS_TOKEN", r"ACCESS_TOKEN\\s*=\\s*[\\\"'][^\\\"']+[\\\"']"),
    ("PASSWORD", r"PASSWORD\\s*=\\s*[\\\"'][^\\\"']+[\\\"']"),
]
```

Saida:
1. Arquivo `${REPORTS_DIR}/credential_report.json`.
2. Log com alertas por arquivo/linha.

### 2) devSecOps/prepare_ai_input.py

Responsabilidade:
1. Ler `credential_report.json`.
2. Transformar JSON tecnico em prompt textual para IA.
3. Gerar `${REPORTS_DIR}/ai_input.txt`.

### 3) devSecOps/ai_analysis.py

Responsabilidade:
1. Ler `${REPORTS_DIR}/ai_input.txt`.
2. Chamar `client.responses.create(...)` com modelo `gpt-4.1-mini`.
3. Salvar resposta final em `${REPORTS_DIR}/final_report.txt`.

Trecho relevante:

```python
response = client.responses.create(
    model="gpt-4.1-mini",
    input=build_prompt(content),
)
```

### 4) cloudSecurity/cspm_scan.py

Responsabilidade:
1. Ler arquivo cloud (padrao: `cloud/aws_mock.json`).
2. Avaliar regras CSPM por tipo de recurso.
3. Gerar `${REPORTS_DIR}/cloud_report.json`.

Variavel importante:
1. `CLOUD_CONFIG_FILE` permite trocar o JSON de entrada sem editar codigo.

Regras implementadas:

| Recurso | Condicao | Severidade |
|---|---|---|
| s3_bucket | public_read = true | high |
| s3_bucket | encryption_enabled = false | high |
| s3_bucket | logging_enabled = false | medium |
| security_group | porta 22 de 0.0.0.0/0 | critical |
| rds_instance | storage_encrypted = false | high |
| rds_instance | public_access = true | critical |
| rds_instance | backup_enabled = false | medium |
| iam_user | mfa_enabled = false | high |
| iam_user | admin_access = true | medium |

### 5) cloudSecurity/prepare_ai_input.py

Responsabilidade:
1. Ler `${REPORTS_DIR}/cloud_report.json`.
2. Montar prompt textual para analise de risco cloud.
3. Salvar `${REPORTS_DIR}/cloud_ai_input.txt`.

### 6) cloudSecurity/ai_analysis.py

Responsabilidade:
1. Ler `${REPORTS_DIR}/cloud_ai_input.txt`.
2. Priorizar uso de Assistant API se `CLOUD_ASSISTANT_ID` estiver definido.
3. Em falha do assistant, fazer fallback automatico para Responses API.
4. Salvar `${REPORTS_DIR}/cloud_final_report.txt`.

Trecho de decisao:

```python
if assistant_id:
    try:
        result = analyze_with_assistant(client, assistant_id, content)
    except Exception:
        result = analyze_with_responses(client, content)
else:
    result = analyze_with_responses(client, content)
```

### 7) send_email.py

Responsabilidade:
1. Ler relatorios finais e tecnicos em `${REPORTS_DIR}`.
2. Construir corpo de e-mail consolidado.
3. Anexar ate 4 arquivos (se existirem).
4. Enviar via SMTP SSL Gmail (`smtp.gmail.com:465`).

Arquivos esperados para anexar:
1. `final_report.txt`
2. `cloud_final_report.txt`
3. `credential_report.json`
4. `cloud_report.json`

## Variaveis e Secrets

### Secrets obrigatorios (GitHub)

| Nome | Uso |
|---|---|
| `OPENAI_API_KEY` | chamadas OpenAI nos dois fluxos |
| `EMAIL_USER` | remetente do SMTP |
| `EMAIL_PASSWORD` | senha/app password do SMTP |
| `EMAIL_TO` | destinatario do relatorio |

### Secret opcional

| Nome | Uso |
|---|---|
| `CLOUD_ASSISTANT_ID` | ativa fluxo via Assistant API no cloudSecurity |

### Variaveis de ambiente opcionais

| Nome | Padrao | Uso |
|---|---|---|
| `REPORTS_DIR` | `/tmp/security-reports` | pasta de saida de todos os relatorios |
| `CLOUD_CONFIG_FILE` | `cloud/aws_mock.json` | caminho do JSON cloud a ser escaneado |

## Artefatos Gerados

Arquivos produzidos por execucao:
1. `${REPORTS_DIR}/credential_report.json`
2. `${REPORTS_DIR}/ai_input.txt`
3. `${REPORTS_DIR}/final_report.txt`
4. `${REPORTS_DIR}/cloud_report.json`
5. `${REPORTS_DIR}/cloud_ai_input.txt`
6. `${REPORTS_DIR}/cloud_final_report.txt`

No GitHub Actions:
1. Os arquivos principais sao publicados no artifact `relatorios-seguranca`.

## Como Rodar Localmente (Opcional)

Mesmo com foco em CI, voce pode reproduzir local para estudo:

```bash
export REPORTS_DIR=/tmp/security-reports
python3 devSecOps/scan.py
python3 devSecOps/prepare_ai_input.py
OPENAI_API_KEY=... python3 devSecOps/ai_analysis.py
python3 cloudSecurity/cspm_scan.py
python3 cloudSecurity/prepare_ai_input.py
OPENAI_API_KEY=... CLOUD_ASSISTANT_ID=... python3 cloudSecurity/ai_analysis.py
EMAIL_USER=... EMAIL_PASSWORD=... EMAIL_TO=... python3 send_email.py
```

## Troubleshooting Rapido

### 1) Workflow invalido por expressao

Sintoma:
1. Erro de parser no YAML antes de rodar job.

Causa comum:
1. Uso de contexto nao suportado em `env` do job.

Status atual:
1. Corrigido com caminho fixo `REPORTS_DIR: /tmp/security-reports`.

### 2) Warning de Node 20 deprecated nas actions

Mitigacao aplicada:
1. `actions/checkout@v6`
2. `actions/setup-python@v6`
3. `actions/upload-artifact@v6`

### 3) Falha no envio de e-mail

Checklist:
1. Validar `EMAIL_USER`, `EMAIL_PASSWORD`, `EMAIL_TO`.
2. Garantir credencial SMTP valida (app password quando necessario).
3. Confirmar que os relatorios foram gerados antes do step de e-mail.

### 4) Falha no assistant cloud

Comportamento esperado:
1. O script tenta Assistant API.
2. Em erro, cai para Responses API sem interromper o fluxo cloud.

## Limites Conhecidos

1. O scanner DevSecOps usa regex simples e pode ter falso positivo/falso negativo.
2. O scanner CSPM avalia um conjunto fixo de regras; nao cobre todos os controles AWS.
3. O projeto analisa principalmente configuracao simulada (`aws_mock.json`), nao ambiente cloud real.

## Sugestoes de Evolucao

1. Adicionar testes unitarios para cada script.
2. Adicionar gate de qualidade para bloquear pipeline com `critical` em cloud.
3. Expandir regras CSPM para IAM policy, KMS, S3 bucket policy e CloudTrail.
4. Exportar tambem em formato Markdown para leitura humana no artifact.

---

Se voce abrir este README no futuro, a ordem mais rapida para relembrar o projeto e:
1. Ler "Fluxo End-to-End".
2. Ler "Workflow do GitHub Actions".
3. Ler "Scripts e Responsabilidades".
4. Ler "Variaveis e Secrets".
