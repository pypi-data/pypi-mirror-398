import logging
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email_validator import validate_email, EmailNotValidError


async def send_email(message: str, sender: str, receivers: list[str], subject: str, host: str, host_port: int):
    """
    Send an email and if failed then raise a ``ValueError``.

    :param message: the message as string formatted.
    :param sender: a string with the address of the sender. Raise ValueError if address is not valid
    :param receivers: list of strings, one for each recipient. Raise ValueError if any address is not valid
    :param subject: a string with brief preview or headline for the content of the email.
    :param host: host running the SMTP server, the IP address of the host or a domain name can be specified.
    :param host_port: if the host argument is specified, specify a port where the SMTP server should be listening.
    """

    logger = logging.getLogger(__name__)
    if not sender:
        logger.debug("Sender is empty")
        return

    if not receivers:
        logger.debug("Receivers is empty")
        raise ValueError("Receivers is empty")

    if not host:
        logger.debug("Mail Host is empty")
        raise ValueError("Mail Host is empty")

    if not host_port:
        logger.debug("Mail Host Port is not correct")
        raise ValueError("Mail Host Port is not correct")

    try:
        validate_email(sender, check_deliverability=False)
    except EmailNotValidError as email_exception:
        raise ValueError("Error: Sender Email is not Valid") from email_exception

    try:
        for x in receivers:
            validate_email(x, check_deliverability=False)
    except EmailNotValidError as email_exception:
        raise ValueError("Error: One of Receiver Email is not Valid") from email_exception

    msg = MIMEText(message, 'html', 'utf-8')
    msg['From'] = str(Header(sender, 'utf-8'))  # cast to str to pass mypy
    msg['To'] = ", ".join(receivers)
    msg['Subject'] = str(Header(subject, 'utf-8'))  # cast to str to pass mypy

    try:
        smtp_obj = smtplib.SMTP()
        smtp_obj.connect(host, host_port)
        # smtp_obj.login(mail_user,mail_pass)
        smtp_obj.sendmail(sender, receivers, msg.as_string())
    except smtplib.SMTPException as exception:
        logger.debug("Error: Send Email Failed")
        raise ValueError(exception)
