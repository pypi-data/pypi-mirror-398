
import base64
import io
from form_submit.send_email import send_feedback_email

def handle_form_submission(
    email: str,
    full_name: str,
    phone_number: str,
    feedback: str,
    troubleshoots_choice: str,
    file_data: dict = None
):
    subject = f"New Feedback from {full_name} ({email})"

    body = f"""New Form Submission:

Email: {email}
Full Name: {full_name}
Phone Number: {phone_number}

Feedback: {feedback}
Troubleshoots in library: {troubleshoots_choice}

"""

    attachments = []
    if file_data:
        try:
            decoded_content = base64.b64decode(file_data['content'])
            attachments.append({
                'filename': file_data['filename'],
                'content': decoded_content,
                'mimetype': file_data['mimetype']
            })
            body += " (Attachment included)"
        except Exception as e:
            print(f"Error decoding attachment: {e}")
            body += " (Error processing attachment)"

    send_feedback_email(subject, body, attachments=attachments)
