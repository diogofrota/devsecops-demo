import smtplib
import os
from email.message import EmailMessage

def main():
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_to = os.getenv("EMAIL_TO")

    # Ler relatório
    with open("reports/final_report.txt", "r", encoding="utf-8") as f:
        content = f.read()

    msg = EmailMessage()
    msg["Subject"] = "Relatório DevSecOps - Análise de Segurança"
    msg["From"] = email_user
    msg["To"] = email_to

    msg.set_content(content)

    # Enviar via Gmail SMTP
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_user, email_password)
        smtp.send_message(msg)

    print("[INFO] E-mail enviado com sucesso!")

if __name__ == "__main__":
    main()