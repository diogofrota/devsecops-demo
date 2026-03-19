import smtplib
import os
from email.message import EmailMessage
from pathlib import Path


def read_report(path: Path, title: str) -> str:
    if not path.exists():
        return f"{title}\nArquivo nao encontrado: {path}\n"
    return f"{title}\n{path.read_text(encoding='utf-8')}\n"


def add_attachment_if_exists(message: EmailMessage, path: Path) -> None:
    if not path.exists():
        return
    message.add_attachment(
        path.read_bytes(),
        maintype="application",
        subtype="octet-stream",
        filename=path.name,
    )


def build_email_body() -> str:
    reports_dir = Path(os.getenv("REPORTS_DIR", "/tmp/security-reports"))
    devsecops_section = read_report(
        reports_dir / "final_report.txt", "===== RELATORIO DEVSECOPS ====="
    )
    cloud_section = read_report(
        reports_dir / "cloud_final_report.txt", "===== RELATORIO CLOUD SECURITY ====="
    )
    return (
        "Relatorio consolidado da pipeline de seguranca.\n\n"
        f"{devsecops_section}\n{cloud_section}"
    )


def main() -> None:
    email_user = os.getenv("EMAIL_USER", "").strip()
    email_password = os.getenv("EMAIL_PASSWORD", "").strip()
    email_to = os.getenv("EMAIL_TO", "").strip()

    if not all([email_user, email_password, email_to]):
        raise ValueError("[ERRO] EMAIL_USER, EMAIL_PASSWORD e EMAIL_TO sao obrigatorios.")

    reports_dir = Path(os.getenv("REPORTS_DIR", "/tmp/security-reports"))

    msg = EmailMessage()
    msg["Subject"] = "Relatorio DevSecOps + Cloud Security"
    msg["From"] = email_user
    msg["To"] = email_to
    msg.set_content(build_email_body())

    add_attachment_if_exists(msg, reports_dir / "final_report.txt")
    add_attachment_if_exists(msg, reports_dir / "cloud_final_report.txt")
    add_attachment_if_exists(msg, reports_dir / "credential_report.json")
    add_attachment_if_exists(msg, reports_dir / "cloud_report.json")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_user, email_password)
        smtp.send_message(msg)

    print("[INFO] E-mail enviado com sucesso!")


if __name__ == "__main__":
    main()
