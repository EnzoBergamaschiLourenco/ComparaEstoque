import imaplib
import email
import re

def buscar_link(email_usuario, senha_usuario):
    """
    Busca o link de contagem no e-mail utilizando credenciais 
    fornecidas dinamicamente via interface.
    """
    try:
        # Conexão IMAP (Locaweb)
        mail = imaplib.IMAP4_SSL("email-ssl.com.br", 993)
        mail.login(email_usuario, senha_usuario) # Agora usa os parâmetros
        mail.select("inbox")

        # 🔍 Buscar apenas emails do sistema uMov.me
        status, messages = mail.search(None, '(FROM "noreply@umov.me")')
        email_ids = messages[0].split()

        if not email_ids:
            print("Nenhum email encontrado")
            return None # Retorna None em vez de encerrar o programa

        # Pegar o mais recente[cite: 9]
        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        # 📬 Extrair corpo HTML[cite: 9]
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        # 🔗 Extrair link do email usando regex[cite: 9]
        links = re.findall(r'https://[^\s"]+', body)

        if not links:
            print("Nenhum link encontrado no email")
            return None
        
        link = links[0] 
        return link # Retorna o link para ser usado no fluxo principal[cite: 9]

    except Exception as e:
        print(f"Erro ao acessar e-mail: {e}")
        return None

# Removido o bloco if __name__ == "__main__" com dados fixos para evitar vazamentos[cite: 9]