import imaplib
import smtplib
import email
from email.message import EmailMessage
from email import policy #useful when returning UTF-8 text
import os

try:
    from gmail_credentials import NAT_GMAIL_ADDRESS, NAT_GMAIL_PASSWORD
except ImportError:
    NAT_GMAIL_ADDRESS = os.environ.get("NAT_GMAIL_ADDRESS") 
    NAT_GMAIL_PASSWORD = os.environ.get("NAT_GMAIL_PASSWORD")

class EmailNotFound(Exception):
    pass

class NoSearchResultsFound(Exception):
    pass

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

class GmailEmail(object):
    """
    Gmail Single Email Class
    Can be instantiated from the email UID
    Or via search "Class Method"
    """
    GMAIL_EMAIL_ENCODING = "(RFC822)"

    def __init__(self, gmail_connection:imaplib.IMAP4_SSL, email_UID:str):
        # self.user_name = user_name
        self.email_UID = email_UID
        self.con = gmail_connection
        self.con.select("INBOX")
        print("Available emails UIDs in 'INBOX' folder:", self.con.uid("SEARCH", None, "ALL")[1], "\n")

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
                "To": msg["To"],
                "From": msg["From"],
                "Subject": msg["Subject"],
                "Date": msg["Date"],
                "Body": GmailEmail._get_email_body(msg), # static function call
                "AttachmentName": None if not msg_attachments_name else msg_attachments_name
            }
            return msg_info, None if not msg_attachments_data else msg_attachments_data, msg
        
        except Exception as e:
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

    @classmethod
    def from_search_result(cls, gmail_connection:imaplib.IMAP4_SSL, search_expression:str, search_field:str = "SUBJECT", unseen = True):
        """
        user_name: str, Gmail email account user name
        password: str, Gmail email account  password
        search_expression: str, the expression that will be searched 
        search_field: str, the field where the above expression will be searched, default : 'SUBJECT', can also be 'FROM', 'SENTON','SENTSINCE', 'SENTBEFORE', etc.. 
        unseen: can take TRUE, FALSE or NONE | Default set to TRUE
        - if True: will search for UNSEEN / UNREAD emails only
        - if False: will search for SEEN / READ emails only
        - if None: will search for regardless if SEEN/READ or not.
        returns the first email UID found from the search
        """
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
            if len(results) > 1: print(f"**** RESULTS FOUND: {results}. EMAIL UID RETURNED: {results[0]}") 
            print(f"Instantiating class GmailEmail(gmail_connection, email_UID = {results[0]})", "\n")
            return cls(gmail_connection, results[0])



if __name__ == "__main__":
    con = GmailConnection(NAT_GMAIL_ADDRESS, NAT_GMAIL_PASSWORD).get_connection()
    # email_object = GmailEmail(con, "17")
    email_object = GmailEmail.from_search_result(con, "décret", unseen=None)
    print(email_object.info)
    print(email_object.attachment_name_all)
    # email_object.mark_as_unseen()