import os
from email import generator
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

default_subject = "Email for testing purpose"
default_sender = "Alice <alice@ink.i>"
default_recipient = "Bob <bob@ink.i>"
default_carbon_copy = None
default_blink_carbon_copy = None
default_html = """\
<html>
    <head></head>
    <body>
        <p> To always achieve the best results I write my emails using ink! </p>
    </body>
</html>
"""

default_filename = "generated_eml"


def is_empty(string):
    return string is None or not string.isprintable()


def save_eml_to_file(eml, subject):
    if is_empty(subject):
        filename = default_filename + '.eml'
    else:
        filename = subject + '.eml'

    cwd = os.getcwd()
    outfile_name = os.path.join(cwd, filename)

    with open(outfile_name, 'w') as outfile:
        gen = generator.Generator(outfile)
        gen.flatten(eml)


def add_field(eml, field, value):
    if not is_empty(value):
        eml[field] = value


def new_eml(subject, sender, recipient, carbon_copy, blink_carbon_copy, html):
    # Set default values if they do not exist
    if is_empty(subject):
        subject = default_subject

    if is_empty(sender):
        sender = default_sender

    if is_empty(recipient):
        recipient = default_recipient

    if is_empty(carbon_copy):
        carbon_copy = default_carbon_copy

    if is_empty(blink_carbon_copy):
        blink_carbon_copy = default_blink_carbon_copy

    date = formatdate(localtime=True)

    if is_empty(html):
        html = default_html

    # Put values inside the eml object
    eml = MIMEMultipart('alternative')
    add_field(eml, 'Subject', subject)
    add_field(eml, 'From', sender)
    add_field(eml, 'To', recipient)
    add_field(eml, 'Cc', carbon_copy)
    add_field(eml, 'Bcc', blink_carbon_copy)
    add_field(eml, 'Date', date)
    part = MIMEText(html, 'html')

    eml.attach(part)

    save_eml_to_file(eml, subject)
