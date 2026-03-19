# devsecops-demo

Projeto de pipeline DevSecOps com analise de codigo e seguranca cloud.

## Estrutura

- `devSecOps/`
  - `scan.py`
  - `prepare_ai_input.py`
  - `ai_analysis.py`
- `cloudSecurity/`
  - `cspm_scan.py`
  - `prepare_ai_input.py`
  - `ai_analysis.py`
- `cloud/aws_mock.json`
- `send_email.py`

## Secrets esperados no GitHub

- `OPENAI_API_KEY`
- `EMAIL_USER`
- `EMAIL_PASSWORD`
- `EMAIL_TO`
- `CLOUD_ASSISTANT_ID` (opcional)

## Saida de relatorios

- Em execucao local e no GitHub Actions, os arquivos sao gravados em
  `REPORTS_DIR` (padrao: `/tmp/security-reports`).
