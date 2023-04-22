import logging
import os

from dotenv import load_dotenv

from gmail_email_api import GmailConnection, GmailEmail

# load environment variable
load_dotenv()

# configure custom console logger
logger = logging.getLogger("test")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("[%(asctime)s | %(name)s | %(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

logger_stream_handler = logging.StreamHandler()
logger_stream_handler.setFormatter(formatter)

logger.addHandler(logger_stream_handler)

# retrieve environment variables
username = os.environ.get("GMAIL_USER_NAME")
password = os.environ.get("GMAIL_PASSWORD")

# test program
# IMPORTANT: NOT ALL USE CASES ARE TESTED. ONLY THE SIMPLEST USE CASE IS TESTED HERE.
with GmailConnection(username, password) as gmail:
    # get the IMAP4_SSL connection
    connection = gmail.get_connection()

    # get email through search criterias
    email_object = GmailEmail.from_search_result(
        gmail_connection=connection,
        subject="Test Email",
        From="boutaghouamine@gmail.com",
        unseen=None,
    )

    # some basic assertions
    assert email_object.attachment_name == "test_attachment.txt"
    assert email_object.attachment_data.decode("ASCII") == "Test text file !"
    assert email_object.info["Body"].find("This is a test email.") != -1

    logger.info("Basic tests (body content, single attachment text file name and content) successfully passed !")
