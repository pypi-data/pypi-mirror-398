from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

def send(api_key:str, sender:str, receiver:str, subject:str, body:str, attachment_path : str=None,sendgrid_template: str=None):
    # Création de l'objet SendGrid
    sg = sendgrid.SendGridAPIClient(api_key)

    # Création du mail
    from_email = Email(sender)
    to_email = To(receiver)
    content = Content("text/plain", body)
    mail = Mail(from_email, to_email, subject, content)

    if sendgrid_template:
        # Utilisation du template ID
        mail.template_id = sendgrid_template

    if attachment_path:
        # Lecture du fichier et création de la pièce jointe
        with open(attachment_path, 'rb') as f:
            data = f.read()
            encoded_file = base64.b64encode(data).decode()

        attachment = Attachment()
        attachment.file_content = FileContent(encoded_file)
        attachment.file_type = FileType('text/plain')
        attachment.file_name = FileName(attachment_path.split('/')[-1])
        attachment.disposition = Disposition('attachment')

        # Ajout de la pièce jointe au mail
        mail.attachment = attachment

    try:
        # Envoi du mail
        response = sg.send(mail)
        print(f"Email envoyé avec statut: {response.status_code}")
        return response
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")