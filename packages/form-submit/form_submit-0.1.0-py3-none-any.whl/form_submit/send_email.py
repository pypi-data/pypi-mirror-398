
import smtplib
from email.message import EmailMessage

def send_feedback_email(subject, body):
    sender_email = 'louatimahdi390@gmail.com'
    recipient_email = 'louatimahdi390@gmail.com'
    app_password = 'nucm mizw szlu oloq' # Use the provided app password

    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        print(f"Email sent successfully to {recipient_email}!")
    except Exception as e:
        print(f"Error sending email: {e}")

