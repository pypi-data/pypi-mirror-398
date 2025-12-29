form_submit: HTML Form Submission for Google Colab
A Python package designed to simplify displaying HTML forms in Google Colab notebooks, capturing user submissions, and securely sending the collected data (including file attachments) via email.

Features
Easy HTML Form Display: Render interactive forms directly within your Colab cells.
Secure Email Submission: Send form data, including attached files, to a specified email address using an app password.
Attachment Handling: Supports decoding and attaching base64 encoded files from the form.
Installation
Install the package directly from PyPI:

%pip install form_submit
Usage
1. Displaying the Form
First, import the display_feedback_form function and call it in a code cell. This will render the HTML form in your Colab output.

from form_submit import display_feedback_form

display_feedback_form()
2. Handling Form Submissions
To capture and process form submissions, you need to set up a JavaScript listener that sends the form data back to Python. The handle_form_submission function in this package is designed to receive this data and send an email.

Here's an example of how you might set up the JavaScript in a Colab notebook (this assumes you've displayed the form and want to handle its submission):

from google.colab import output
from form_submit import handle_form_submission

# Define a Python function to be called from JavaScript
def _handle_js_form_data(data):
    email = data.get('enter_your_email', 'N/A')
    full_name = data.get('enter_your_full_name', 'N/A')
    phone_number = data.get('enter_your', 'N/A') # Note: original form input name was 'enter_your'
    feedback = data.get('give_your_feedback_about_the_library', 'N/A')
    troubleshoots_choice = data.get('any_trobleshoots_in_the_library', 'N/A')

    file_input = data.get('upload_your_poblem_in_a_file_pdf_content', None)
    file_data = None
    if file_input and isinstance(file_input, dict):
        file_data = {
            'filename': file_input.get('filename'),
            'content': file_input.get('content'), # Base64 encoded content
            'mimetype': file_input.get('mimetype')
        }

    handle_form_submission(
        email=email,
        full_name=full_name,
        phone_number=phone_number,
        feedback=feedback,
        troubleshoots_choice=troubleshoots_choice,
        file_data=file_data
    )

# Expose the Python function to JavaScript
output.register_callback('handle_colab_form', _handle_js_form_data)

# JavaScript to intercept form submission and send data to Python
js_code = """
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const form = document.querySelector('form'); // Adjust selector if multiple forms
        if (form) {
            form.addEventListener('submit', function(event) {
                event.preventDefault(); // Prevent default form submission
                const formData = new FormData(form);
                const data = {};
                for (let [key, value] of formData.entries()) {
                    if (value instanceof File) {
                        if (value.size > 0) {
                            const reader = new FileReader();
                            reader.onload = function(e) {
                                data[key] = {
                                    filename: value.name,
                                    content: btoa(e.target.result), // Base64 encode file content
                                    mimetype: value.type
                                };
                                google.colab.kernel.invokeFunction('handle_colab_form', [data], {});
                            };
                            reader.readAsBinaryString(value);
                            return; // Stop and wait for file read
                        }
                    } else {
                        data[key] = value;
                    }
                }
                google.colab.kernel.invokeFunction('handle_colab_form', [data], {});