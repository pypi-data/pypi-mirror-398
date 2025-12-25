import sys
from email.message import EmailMessage
from enum import StrEnum, auto
from logging import Logger
from smtplib import SMTP, SMTP_SSL
from typing import Any

from .file_pomes import Mimetype
from .env_pomes import APP_PREFIX, env_get_int, env_get_str


class EmailParam(StrEnum):
    """
    Parameters for email.
    """
    HOST = auto()
    PORT = auto()
    ACCOUNT = auto()
    PWD = auto()
    DEFAULT_FROM = auto()
    SECURITY = auto()


_EMAIL_CONFIG: dict[EmailParam, Any] = {
    EmailParam.HOST: env_get_str(key=f"{APP_PREFIX}_EMAIL_HOST"),
    EmailParam.PORT: env_get_int(key=f"{APP_PREFIX}_EMAIL_PORT"),
    EmailParam.ACCOUNT: env_get_str(key=f"{APP_PREFIX}_EMAIL_ACCOUNT"),
    EmailParam.PWD: env_get_str(key=f"{APP_PREFIX}_EMAIL_PWD"),
    EmailParam.DEFAULT_FROM: env_get_str(key=f"{APP_PREFIX}_EMAIL_DEFAULT_FROM"),
    EmailParam.SECURITY: env_get_str(key=f"{APP_PREFIX}_EMAIL_SECURITY")
}


def email_setup(host: str,
                port: int,
                account: str,
                pwd: str,
                origin: str,
                security: str = None) -> None:
    """
    Configure the email server.

    Invoking this function overrides the configuration parameters obtained from environment variables.

    :param host: the host URL
    :param port: the connection port (a positive integer)
    :param account: the logon account
    :param pwd: the logon password
    :param origin: the address of origin for the e-mails
    :param security: the security protocol ('ssl' and 'tls' are currently supported)
    """
    global _EMAIL_CONFIG
    _EMAIL_CONFIG = {
        EmailParam.HOST: host,
        EmailParam.PORT: port,
        EmailParam.ACCOUNT: account,
        EmailParam.PWD: pwd,
        EmailParam.DEFAULT_FROM: origin or account,
        EmailParam.SECURITY: security
    }


def email_send(email_to: str,
               subject: str,
               content: str,
               mimetype: Mimetype = Mimetype.TEXT,
               email_from: str = None,
               errors: list[str] = None,
               logger: Logger = None) -> None:
    """
    Send email to *user_email*, with *subject* as the email subject, and *content* as the email message.

    :param email_to: the address to send the email to
    :param subject: the email subject
    :param content: the email message
    :param mimetype: the mimetype of the content (defaults to *text/plain*)
    :param email_from: the email address of origin (defaults to the configured origin)
    :param errors: incidental error messages
    :param logger: optional logger
    """
    # import needed function
    from .obj_pomes import exc_format

    # build the email object
    email_msg = EmailMessage()
    email_msg["From"] = (email_from or
                         _EMAIL_CONFIG[EmailParam.DEFAULT_FROM] or
                         _EMAIL_CONFIG[EmailParam.ACCOUNT])
    email_msg["To"] = email_to
    email_msg["Subject"] = subject
    maintype, subtype = mimetype.split("/")
    # BUG HANDLING:
    #   will crash if parameter 'maintype' is passed and 'content' is a string
    if isinstance(content, str):
        email_msg.set_content(content,
                              subtype=subtype)
    else:
        email_msg.set_content(content,
                              maintype=maintype,
                              subtype=subtype)
    # send the message
    try:
        # instantiate the email server, login and send the email
        if _EMAIL_CONFIG[EmailParam.SECURITY] == "ssl":
            with SMTP_SSL(host=_EMAIL_CONFIG[EmailParam.HOST],
                          port=_EMAIL_CONFIG[EmailParam.PORT]) as server:
                server.login(user=_EMAIL_CONFIG[EmailParam.ACCOUNT],
                             password=_EMAIL_CONFIG[EmailParam.PWD])
                server.send_message(msg=email_msg)
        else:
            with SMTP(host=_EMAIL_CONFIG[EmailParam.HOST],
                      port=_EMAIL_CONFIG[EmailParam.PORT]) as server:
                if _EMAIL_CONFIG[EmailParam.SECURITY] == "tls":
                    server.starttls()

                # possible exceptions:
                #   - SMTPAuthenticationError: the server didn't accept the username/password combination
                #   - SMTPException: no suitable authentication method was found
                #   - SMTPHeloError: the server didn't reply properly to the helo greeting
                #   - SMTPNotSupportedError: the AUTH command is not supported by the server
                #   - SMTPServerDisconnected: the connection was unexpectedly closed
                server.login(user=_EMAIL_CONFIG[EmailParam.ACCOUNT],
                             password=_EMAIL_CONFIG[EmailParam.PWD])
                server.send_message(msg=email_msg)
        if logger:
            logger.debug(msg=f"Sent email '{subject}' to '{email_to}'")
    except Exception as e:
        # the operation raised an exception
        exc_err: str = exc_format(exc=e,
                                  exc_info=sys.exc_info())
        err_msg: str = f"Error sending the email: {exc_err}"
        if logger:
            logger.error(msg=err_msg)
        if isinstance(errors, list):
            errors.append(err_msg)


def email_codify(email: str) -> str:
    """
    Codify *email* so as to provide a hint at its content, whilst preventing its usage.

    The codification process changes my_mail@my_server.com into m*****l@m********.com.

    :param email: the email to codify
    :return: the codified email
    """
    # initialize the return variable
    result: str = email

    pos1: int = email.rfind("@")
    pos2: int = email.rfind(".")
    if pos2 > pos1 > 0:
        result = email[0] + "*" * (pos1 - 2) + \
                 email[pos1 - 1:pos1 + 2] + "*" * (pos2 - pos1 - 2) + email[pos2:]

    return result
