import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
from configparser import ConfigParser
import os
from datetime import datetime


def bodybuilder(date, diff_add=None, diff_del=None, announcement=None):
    if diff_add == None and diff_del == None:
        b = ["В реестре нет изменений.",
        f"Версия реестра от {date} прикреплена к письму."]
        
    else:
        b = [f"Реестр был обновлён {date}."]
        if diff_add:
            b.extend(["В него были добалены записи:\n","\n".join(diff_add)])
        if diff_del:
            b.extend(["\nИз него были исключены записи:\n","\n".join(diff_del)])
        if announcement:
            b.extend(["\nИз реестра будут исключены записи:",announcement]) # !!!!!
        
        b.append("\nАктуальная версия реестра прикреплена к письму")

    return "\n".join(b)


def get_config(config_path):
    if os.path.exists(config_path):
        cfg = ConfigParser()
        cfg.read(config_path)
    else:
        print("Config not found! Exiting!")

    host = cfg.get("smtp", "server")
    sender = cfg.get("smtp", "from_addr")
    port = cfg.get("smtp", "port")
    password = cfg.get("smtp", "password")

    return host, sender, port, password


def construct_message(file_path, file_name, body, sender, emails):
    
    cdate = datetime.now().strftime("%d.%m.%Y")
    subject = f"Тестовая рассылка. Реестр лиц, уволенных в связи с утратой доверия на {cdate}"

    message = MIMEMultipart()

    message["From"] = sender
    message["Subject"] = subject
    message["To"] = ', '.join(emails)

    message.attach(MIMEText(body, "plain"))
    
    if file_path and file_name: 
        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={file_name}",
        )

        message.attach(part)
    
    return message.as_string()


def send_mail(date, flag, announcement=None, diff_add=None, diff_del=None, csv_file_path=None, csv_file_name=None):
    
    host, sender, port, password = get_config("config.ini")
    
    if flag:
        emails = json.loads(open('emails.json').read())
        body = bodybuilder(
            date, 
            diff_add, 
            diff_del, 
            announcement
        )
    
    else:
        emails = json.loads(open('admin_email.json').read())
        body = "Eror"
    
    text = construct_message(
        csv_file_path,
        csv_file_name,
        body,
        sender,
        emails
    )
    
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, emails, text)

