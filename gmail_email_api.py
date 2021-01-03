# Author: Amine BOUTAGHOU   / boutaghouamine@gmail.com

# **********************************************************************************************************************************************************
#             Python script that allow access to a Gmail mailbox in order to fetch e-mail general information as well as attachment data.
# **********************************************************************************************************************************************************

import imaplib
import smtplib
import email
from email.message import EmailMessage
from email import policy #useful when returning UTF-8 text
from typing import Literal  #does not work with Python 3.7
from pprint import pprint

class EmailNotFound(Exception): pass

class NoSearchResultsFound(Exception): pass

class GmailConnection(object):
    """
    Create an IMAP4_SSL connection to the Gmail account
    """
    GMAIL_HOST = "imap.gmail.com"

    def __init__(self, user_name:str, password:str):
        self.user_name = user_name
        self.connection = imaplib.IMAP4_SSL(GmailConnection.GMAIL_HOST)
        print(self.connection.login(self.user_name, password))

    def get_connection(self):
        return self.connection

    def __repr__(self):
        return f'GmailConnection(user_name= "{self.user_name}", password= "***********")'

    def __enter__(self):
        return self

    def __exit__(self, exit_type, value, traceback):
        self.connection.close()

class GmailEmail(object):
    """
    Gmail Single Email Class
    Can be instantiated from the email UID
    Or via from_search_result() "Class Method"
    """
    GMAIL_EMAIL_ENCODING = "(RFC822)"

    def __init__(self, gmail_connection:imaplib.IMAP4_SSL, email_UID:str):
        self.email_UID = email_UID
        self.con = gmail_connection
        self.con.select("INBOX")
        self.info, self.attachment_data_all, self._msg = self._fetch_email_data()
        if not self.info: raise EmailNotFound(f"Email UID {self.email_UID} CANNOT BE FOUND - Does this mail even exist ?")
        self.attachment_data = None if not self.attachment_data_all else self.attachment_data_all[0] if isinstance(self.attachment_data_all, list) else None
        self.attachment_name = None if not self.info else self.info["AttachmentName"][0] if isinstance(self.info["AttachmentName"], list) else None
        self.attachment_name_all = None if not self.info else self.info["AttachmentName"]

    def _fetch_email_data(self):
        """
        -> returns a tuple of lenght 3 ***(msg_info, attachment_data, EmailMessage object)***
        -> if error, returns tuple of lenght 3 of Nones (None, None, None)
        """
        try:
            data = self.con.uid("FETCH", self.email_UID, GmailEmail.GMAIL_EMAIL_ENCODING)[1][0][1]
            msg = email.message_from_bytes(data, policy= policy.default)
            msg_attachments_name, msg_attachments_data = GmailEmail._get_email_attachments(msg) # static function call
            msg_info = {
                "UID": self.email_UID,
                "To": msg["To"],
                "From": msg["From"],
                "Subject": msg["Subject"],
                "Date": msg["Date"],
                "Body": GmailEmail._get_email_body(msg), # static function call
                "AttachmentName": None if not msg_attachments_name else msg_attachments_name
            }
            return msg_info, None if not msg_attachments_data else msg_attachments_data, msg
        
        except Exception as e:
            print(f"Error happended when fetching email UID {self.email_UID}", e)
            return None, None, None

    def mark_as_unseen(self):
        """
        Mark the email as unseen / unread
        """
        print(self.con.uid("STORE", self.email_UID, "-FLAGS", "\\Seen"))

    def delete_email(self):
        """
        BE CAREFULL - Cannot go back once done.
        Deleted email will have a different UID if it is put back into INBOX
        """
        print(self.con.uid("STORE", self.email_UID, "+FLAGS", "\\Deleted"))

    @classmethod
    def from_search_result(cls, gmail_connection:imaplib.IMAP4_SSL, unseen:Literal[True, False, None] = True, **search_agrs):
        """
        gmail_connection: an imaplib.IMAP4_SSL connection object "use GmailConnection class and .get_connection() methode to get it.
        
        **search_agrs a series of search_field:search_expressions values such as From = 'Amine B', senton = '07-DEC-2020', subject = 'blablabla'
        searchfileds can be : [subject, body ,to, From(not from -> Python keyword), senton, sentsince, sentbefore]
        search_expression: string value of the expression that will be searched 
        
        
        
        unseen: can take TRUE, FALSE or NONE | Default set to TRUE
        - if True: will search for UNSEEN / UNREAD emails only
        - if False: will search for SEEN / READ emails only
        - if None: will search for regardless if SEEN/READ or not.
        returns the first email UID found from the search
        """
        if len(search_agrs) == 1: result = GmailEmail._search_email(gmail_connection, unseen = unseen, **search_agrs)
        if len(search_agrs) > 1:  result = GmailEmail._search_email_multi_criteria(gmail_connection, unseen = unseen, **search_agrs)
        if not search_agrs: raise NoSearchResultsFound("No search arguments passed. Try passing arguments such as subject='Hello', From='Amine' etc..")

        print(f"Instantiating class instance -> GmailEmail(gmail_connection, email_UID = {result})", "\n")
        return cls(gmail_connection, result)

    @staticmethod
    def _get_email_body(msg: email.message.EmailMessage):
        """
        Return the email body of an email object
        - msg: EmailMessage object/instance
        """    
        if msg.is_multipart():
            return GmailEmail._get_email_body(msg.get_payload(0))  #recursive function untill msg.is_multipart == False
        else:
            return msg.get_payload()

    @staticmethod
    def _get_email_attachments(msg: email.message.EmailMessage):
        """
        Return a truple of (attachments_names, attachments_bytes) from an email object
        - msg : EmailMessage object / instance
        """    
        attachments_name = []
        attachments_bytes = []

        for part in msg.walk():
            if part.get_content_maintype()=='multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            fileName = part.get_filename()
            blob = part.get_payload(decode=True)

            attachments_name.append(fileName)
            attachments_bytes.append(blob)

        return attachments_name, attachments_bytes

    @staticmethod
    def _search_email(gmail_connection:imaplib.IMAP4_SSL, unseen:Literal[True, False, None] = True, **search_agrs):
        """
        ** SUPPORT UTF-8 encoding search text. **
        Search for emails with **single key/value search argument** ex: subject = "blablabla"
        ----
        gmail_connection: an imaplib.IMAP4_SSL connection object "use GmailConnection class and .get_connection() methode to get it.
        search_expression: str, the expression that will be searched 
        search_field: str, the field where the above expression will be searched, default : 'SUBJECT', can also be 'FROM', 'SENTON','SENTSINCE', 'SENTBEFORE', etc.. 
        unseen: can take TRUE, FALSE or NONE | Default set to TRUE
        - if True: will search for UNSEEN / UNREAD emails only
        - if False: will search for SEEN / READ emails only
        - if None: will search for regardless if SEEN/READ or not.
        returns the first email UID found from the search
        """
        # transform **search_args to string
        search_field = list(search_agrs.keys())[0].upper()
        search_expression = list(search_agrs.values())[0]

        if search_field in ["SENTON", "SENTSINCE", "SENTBEFORE"]: return GmailEmail._search_email_multi_criteria(gmail_connection, unseen = unseen, **search_agrs)

        gmail_connection.select("INBOX")
        search_expression = f'"{search_expression}"'
        gmail_connection.literal = search_expression.encode("utf-8") # to work around encoding problems
        
        if unseen == True: results = gmail_connection.uid('SEARCH', 'CHARSET', 'UTF-8', "UNSEEN", search_field)[1]
        if unseen == False: results = gmail_connection.uid('SEARCH', 'CHARSET', 'UTF-8', "SEEN", search_field)[1]        
        if unseen == None: results = gmail_connection.uid('SEARCH', 'CHARSET', 'UTF-8', search_field)[1]

        gmail_connection.literal = None

        if not results or results == [b'']:
            raise NoSearchResultsFound(f"No results found for search expression: '{search_expression}', in field: '{search_field}', unseen: '{unseen}'")

        if results: 
            results = results[0].split()  #split the results ["1 2 3 4"] ==> ["1", "2", "3", "4"]  // ["1"] ==> ["1"]
            if len(results) > 1: print(f"**** BE CAREFULL, MORE THAN ONE RESULT ({len(results)}) WERE FOUND ! ****") 
            if len(results) > 1: print(f"**** RESULTS FOUND: {results}. EMAIL UID RETURNED: {results[0]} ****", "\n")
            return results[0]

    @staticmethod
    def _search_email_multi_criteria(gmail_connection:imaplib.IMAP4_SSL, unseen:Literal[True, False, None] = True, **search_agrs):
        """
        **DO NOT SUPPORT UTF-8 encoding search text.*
        ---
        search for emails with **multiple key/value search arguments** ex: subject = "blablabla", from = "Eric Dupont", senton = "07-DEC-2020", etc...
        ----
        gmail_connection: an imaplib.IMAP4_SSL connection object "use GmailConnection class and .get_connection() methode to get it.
        search_expression: str, the expression that will be searched 
        search_field: str, the field where the above expression will be searched, default : 'SUBJECT', can also be 'FROM', 'SENTON','SENTSINCE', 'SENTBEFORE', etc.. 
        unseen: can take TRUE, FALSE or NONE | Default set to TRUE
        - if True: will search for UNSEEN / UNREAD emails only
        - if False: will search for SEEN / READ emails only
        - if None: will search for regardless if SEEN/READ or not.
        returns the first email UID found from the search
        """

        # transform **search_args to list / generator which can be unpacked later on UID method
        search_agrs = {k.upper():f'"{v}"' for k,v in search_agrs.items()}  #transform keys to upper case and "" to the values
        search_agrs =[item for items in search_agrs.items() for item in items] #transform dict to list {k1:v1, k2:v2} -> (k1, v1, k2, v2)

        gmail_connection.select("INBOX")

        if unseen == True: results = gmail_connection.uid('SEARCH', 'CHARSET', 'UTF-8', "UNSEEN", *search_agrs)[1]
        if unseen == False: results = gmail_connection.uid('SEARCH', 'CHARSET', 'UTF-8', "SEEN", *search_agrs)[1]        
        if unseen == None: results = gmail_connection.uid('SEARCH', 'CHARSET', 'UTF-8', *search_agrs)[1]

        if not results or results == [b'']:
            raise NoSearchResultsFound(f"No results found for search expressions: '{search_agrs[1::2]}', in field: '{search_agrs[::2]}', unseen: '{unseen}'")

        if results: 
            results = results[0].split()  #split the results ["1 2 3 4"] ==> ["1", "2", "3", "4"]  // ["1"] ==> ["1"]
            if len(results) > 1: print(f"**** BE CAREFULL, MORE THAN ONE RESULT ({len(results)}) WERE FOUND ! ****") 
            if len(results) > 1: print(f"**** RESULTS FOUND: {results}. EMAIL UID RETURNED: {results[0]} ****", "\n") 
            return results[0]
    
    @staticmethod
    def send_mail(user_name:str, #gmail account user namge
                  password:str,
                  sender_name:str, 
                  recipient_email:str, 
                  subject:str, 
                  body_content:str, *,
                  file_name:str =None, 
                  file_data:bytes =None,
                  file_main_type:str= "application", 
                  file_sub_type:str= "csv"):
        """
        Quick-Send email with eventually attached files
        Default attached file option set to send .csv files
        password
        - user_name:       Gmail account username
        - sender_name:     Gmail account password
        - recipient_email: Recipient email address
        - subject:         Email subject
        - body_content:    Email body, must a plain text format (not html)
        - file_name:       Attached file name including the extension example -> "main.csv"
        - file_data        Attached file data in bytes
        - file_main_type   Attachment main type such as "application", "image", "audio", "text" ect...
        - file_sub_type    Attachment sub type such as "csv", "txt", "pdf", "xlsx", "jpg", "jpeg" etc...
        """
        msg = EmailMessage()
        msg["From"] = sender_name
        msg["To"] = recipient_email

        msg["Subject"] = subject    
        msg.set_content(body_content)

        if file_name and file_data and file_main_type and file_sub_type:
            msg.add_attachment(file_data, maintype=file_main_type, subtype=file_sub_type, filename=file_name)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(user_name, password)
            smtp.send_message(msg)

        print(f"E-mail with subject '{subject}' sent successfully to '{recipient_email}' !")

    def __repr__(self):
        return f"GmailEmail('gmail_connection', email_UID = '{self.email_UID}')"