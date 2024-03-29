Author: Amine BOUTAGHOU   / boutaghouamine@gmail.com

*********************************************************************************************************************************
Python script that allow access to a Gmail mailbox in order to fetch e-mail general information as well as attachment data.
*********************************************************************************************************************************

        pip install -e git+https://github.com/AmineBTG/gmail-email-api.git#egg=gmail_email_api

No external Python librairies needed.

Modules used : imaplib, smtplib, email, typing and pprint 

Works very well with Python 3.8+

If older python version used, discrepencies will occur with module 'typing' when importing 'Literal' class. 
Therefore Literal must be deleted from the code in order to get it work. Literal class are used in the import statement and in GmailEmail class (from_search_result, _search_email and _search_email_multi_criteria methods.)

*********************************************************************************************************************************
Script contains 4 classes :

    EmailNotFound  --> Exception class

    NoSearchResultsFound --> Exception class

    GmailConnection --> istantiate an IMAP4_SSL connection instance which will be passed to the GmailEmail constructor method.
                    --> __init__ arguments: email_user_name, email_password
                    --> Attributes : user_name, connection
                    --> Methods : get_connection() -> returns the connection attribute
                    --> Magic methods : __repr__, __open__ and __exit__ so can be passed in a context manager
                    --> Class variables: GMAIL_HOST = "imap.gmail.com"


    GmailEmail      --> instantiate an email object 
                    --> __init__ arguments: gmail_connection_instance, email UID
                    --> alternative constructor : from_search_results
                    --> alternative constructor arguments : gmail_connection_instance, search keywords arguments
                            --> returns a GmailEmail instance with the first email found in the search results

                    --> attributes :
                            --> email_UID
                            --> con
                            --> info
                            --> attachment_name:     returns the name of the first attachment file -> str
                            --> attachment_name_all: returns a list of all the names of the attachment files -> list of str
                            --> attachment_data:     returns the first attachment file data (in bytes) -> bytes
                            --> attachment_data_all: returns a list of all attachment files data (in bytes) -> list of bytes

                    --> methods :
                            --> mark_as_unseen():      Mark the email as unseen / unread (adds an 'Unseen' flag into emails FLAGS)
                            --> delete_email():        Delete the email from the 'INBOX' (adds an 'Deleted' flag into emails FLAGS)
                            --> from_search_results(): class method / alternative constructor
                            --> send_email():          static method we can user to send an email using smptlib

                    --> Class variables: GMAIL_EMAIL_ENCODING = "(RFC822)"
                
*********************************************************************************************************************************
Best practice and get started :
*********************************************************************************************************************************
```python
if __name__ == "__main__":

        # retrieve environment variables
        username = os.environ.get("GMAIL_USER_NAME")
        password = os.environ.get("GMAIL_PASSWORD")

        with GmailConnection(username, password) as gmail:
                # get the gmail IMAP4_SSL connection
                connection = gmail.get_connection()

                # get email through search criterias
                email_object = GmailEmail.from_search_result(
                        gmail_connection=connection,
                        subject="Test Email",
                        From="boutaghouamine@gmail.com",
                        unseen=None,
                )
```
*********************************************************************************************************************************
