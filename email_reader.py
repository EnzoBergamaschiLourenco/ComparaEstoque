import imaplib
import email
import re
from sensitive import EMAIL, PASSWORD

def buscar_link():
    # conexão IMAP (Locaweb)
    mail = imaplib.IMAP4_SSL("email-ssl.com.br", 993)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    # 🔍 buscar apenas emails do sistema
    status, messages = mail.search(None, '(FROM "noreply@umov.me")')

    email_ids = messages[0].split()

    if not email_ids:
        print("Nenhum email encontrado")
        exit()

    # pegar o mais recente
    latest_email_id = email_ids[-1]

    status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    print("Email capturado com sucesso")

    # 📬 extrair corpo HTML
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                body = part.get_payload(decode=True).decode()
    else:
        body = msg.get_payload(decode=True).decode()

    print("HTML capturado com sucesso")

    # 🔗 extrair link do email
    links = re.findall(r'https://[^\s"]+', body)

    if not links:
        print("Nenhum link encontrado no email")
    else:
        link = links[0]  # pega o primeiro (normalmente é o principal)
        print("Link capturado:", link)
        return link

if __name__ == "__main__":
    buscar_link()
