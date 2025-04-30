import smtplib
import logging
from config import Config_lock
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_alert(subject, body):
    """
    发送警报邮件
    """
    msg = MIMEMultipart()
    msg['From'] = Config_lock.EMAIL_USER
    msg['To'] = Config_lock.ALERT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(Config_lock.EMAIL_HOST, Config_lock.EMAIL_PORT)
        server.starttls()
        server.login(Config_lock.EMAIL_USER, Config_lock.EMAIL_PASS)
        server.sendmail(Config_lock.EMAIL_USER, Config_lock.ALERT_EMAIL, msg.as_string())
        server.quit()
        logging.error(f"Alert email sent successfully")
        print("Alert email sent successfully")
    except Exception as e:
        logging.error(f"Failed to send alert email: {str(e)}")
        print(f"Failed to send alert email: {str(e)}")
