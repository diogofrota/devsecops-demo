import re
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
                    "trecho": linha.strip()
                })

    return achados

def main():
    print("Iniciando varredura de credenciais expostas...")
    total_achados = 0

    for caminho in Path(".").rglob("*"):
        if caminho.is_file() and deve_analisar(caminho):
            resultados = analisar_arquivo(caminho)

            for item in resultados:
                total_achados += 1
                print(f"[ALERTA] Tipo: {item['tipo']}")
                print(f"Arquivo: {item['arquivo']}")
                print(f"Linha: {item['linha']}")
                print(f"Trecho: {item['trecho']}")
                print("-" * 50)

    print(f"Varredura finalizada. Total de achados: {total_achados}")

if __name__ == "__main__":
    main()