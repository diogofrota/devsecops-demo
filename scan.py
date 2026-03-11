import re
import json
from pathlib import Path

ARQUIVOS_PERMITIDOS = {".html", ".js", ".py", ".json", ".env", ".txt"}

PADROES = [
    ("API_KEY", r"API_KEY\s*=\s*[\"'][^\"']+[\"']"),
    ("SECRET_KEY", r"SECRET_KEY\s*=\s*[\"'][^\"']+[\"']"),
    ("ACCESS_TOKEN", r"ACCESS_TOKEN\s*=\s*[\"'][^\"']+[\"']"),
    ("PASSWORD", r"PASSWORD\s*=\s*[\"'][^\"']+[\"']"),
]

def deve_analisar(caminho: Path) -> bool:
    return caminho.suffix.lower() in ARQUIVOS_PERMITIDOS

def analisar_arquivo(caminho: Path):
    achados = []

    try:
        conteudo = caminho.read_text(encoding="utf-8", errors="ignore")
    except Exception as erro:
        print(f"[ERRO] Não foi possível ler {caminho}: {erro}")
        return achados

    linhas = conteudo.splitlines()

    for numero_linha, linha in enumerate(linhas, start=1):
        for nome_padrao, padrao in PADROES:
            if re.search(padrao, linha):
                achados.append({
                    "arquivo": str(caminho),
                    "linha": numero_linha,
                    "tipo": nome_padrao,
                    "trecho": linha.strip(),
                    "severidade": "alta"
                })

    return achados

def main():
    print("Iniciando varredura de credenciais expostas...")
    todos_achados = []

    for caminho in Path(".").rglob("*"):
        if caminho.is_file() and deve_analisar(caminho):
            resultados = analisar_arquivo(caminho)

            for item in resultados:
                todos_achados.append(item)
                print(f"[ALERTA] Tipo: {item['tipo']}")
                print(f"Arquivo: {item['arquivo']}")
                print(f"Linha: {item['linha']}")
                print(f"Trecho: {item['trecho']}")
                print("-" * 50)

    Path("reports").mkdir(exist_ok=True)

    relatorio = {
        "resumo": {
            "total_achados": len(todos_achados),
            "status": "credenciais expostas encontradas" if todos_achados else "nenhum achado"
        },
        "achados": todos_achados
    }

    with open("reports/credential_report.json", "w", encoding="utf-8") as arquivo:
        json.dump(relatorio, arquivo, indent=2, ensure_ascii=False)

    print(f"Varredura finalizada. Total de achados: {len(todos_achados)}")
    print("Relatório salvo em reports/credential_report.json")

if __name__ == "__main__":
    main()