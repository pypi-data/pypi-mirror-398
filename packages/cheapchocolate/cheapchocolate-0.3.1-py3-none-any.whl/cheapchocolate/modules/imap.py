import os
import imaplib
from dotenv import load_dotenv
import email
from email.header import decode_header
from datetime import datetime, timedelta

from cheapchocolate.modules.mailbox import get_local_mails, get_local_mailbox_folder


def get_imap_connection():
    load_dotenv()
    if os.getenv("user") is None or os.getenv("user") == "myuser@my-mail.server":
        create_env_file()
        print(
            "🫠 Appearently you did't set up your `/.env` file to connect to your email service."
        )
        return None
    try:
        print("☎️  Calling your imap server...")
        imap_connection = imaplib.IMAP4_SSL(os.getenv("server"))
        imap_connection.login(os.getenv("user"), os.getenv("password"))
        print("🙌 It worked!")
    except:
        print("😅 Oops! We cannot login, can you please check your `/.env` file?")
        return None
    return imap_connection


def create_env_file():
    if not os.path.exists(".env"):
        with open(".env", "+a") as f:
            f.write("user=myuser@my-mail.server\n")
            f.write("password=mypassword\n")
            f.write("server=imap.my-mail.server\n")


def get_folders():
    imap_connection = get_imap_connection()
    if imap_connection is None:
        return
    print("🗣️  Asking for your folders...")
    result, folders_list = imap_connection.list()

    if len(folders_list) == 0:
        print(f"😅 You have no new folder...")
        imap_connection.close()
        imap_connection.logout()
        return
    print("These are your folder from your online 📫 mailbox: ")
    for index, folder in enumerate(folders_list):
        folder_name = _clean_folder_name(folder)
        print(f"[{index}] {folder_name}")

    user_option = -1
    while user_option < 0 or user_option >= len(folders_list):
        user_option = input(
            "Choose one of the online 🗂️ folders above to receive the emails or `q` to quit: "
        )
        if user_option == "q":
            return
        elif user_option.isdigit():
            user_option = int(user_option)
            if user_option >= 0 and user_option < len(folders_list):
                get_mails(
                    mail_folder=_clean_folder_name(folders_list[user_option]),
                    imap_connection=imap_connection,
                )
    return


def _clean_folder_name(folder):
    folder_name = str(folder).split('"/" "')[1].replace("\"'", "")
    return folder_name


def get_mails(mail_folder="inbox", imap_connection=None, local_mails=[]):

    today = datetime.today().date()
    time = (today + timedelta(days=0)).strftime("%d-%b-%Y")

    if imap_connection is None:
        imap_connection = get_imap_connection()
        if imap_connection is None:
            return False

    imap_connection.select(mail_folder)

    print(f"🗣️  Asking for the today`s mail in {mail_folder}...")
    result, data = imap_connection.search(None, f"SINCE {time}")
    remote_mails = data[0].split()

    local_mails = get_local_mails()
    mails_to_receive = []
    for remote_mail_id in remote_mails:
        if str(remote_mail_id).replace("'", "") not in local_mails:
            mails_to_receive.append(remote_mail_id)

    if len(mails_to_receive) == 0:
        print(f"📭 You have no new mails...")
        imap_connection.close()
        imap_connection.logout()
        return

    print(f"🗃️  You have {len(mails_to_receive)} mails...")

    for email_id in mails_to_receive:
        load_email_by_id(
            imap_connection=imap_connection, email_id=email_id, mail_folder=mail_folder
        )
    imap_connection.close()
    imap_connection.logout()

    print("🍫 We are done, let`s have a dessert...")


def load_email_by_id(imap_connection, email_id, mail_folder="inbox"):

    result, msg_data = imap_connection.fetch(email_id, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    if msg.is_multipart():
        for msg_part in msg.walk():
            try:
                body = msg_part.get_payload(decode=True).decode()
            except:
                pass
    else:
        body = msg.get_payload(decode=True).decode()
    email_id = str(email_id).replace("'", "")
    mailbox_folder = get_local_mailbox_folder()
    subject_file_name = (
        extract_from_header(msg=msg, key="subject").replace("'", "").replace("/", "")
    )
    with open(f"{mailbox_folder}/{email_id} - {subject_file_name}.md", "+w") as f:
        mail_string = ""
        mail_string = add_mail_line(mail_string=mail_string, line="-" * 10)
        mail_string = add_mail_line(
            mail_string=mail_string,
            line="from: " + extract_from_header(msg=msg, key="from"),
        )
        mail_string = add_mail_line(
            mail_string=mail_string,
            line="to: " + extract_from_header(msg=msg, key="to"),
        )
        mail_string = add_mail_line(
            mail_string=mail_string,
            line='subject: "' + extract_from_header(msg=msg, key="subject") + '"',
        )
        mail_string = add_mail_line(
            mail_string=mail_string,
            line="date: " + extract_from_header(msg=msg, key="date"),
        )
        mail_string = add_mail_line(
            mail_string=mail_string,
            line='mail_folder: "' + mail_folder + '"',
        )
        mail_string = add_mail_line(mail_string=mail_string, line="-" * 10)
        mail_string = add_mail_line(mail_string=mail_string, line=body)
        mail_string = add_mail_line(mail_string=mail_string, line="-" * 10)
        f.write(mail_string)
        print(
            f'📨 {email_id} - {extract_from_header(msg=msg, key="subject")} received...'
        )


def add_mail_line(line, mail_string, verbose=False):
    mail_string = mail_string + "\n" + line
    if verbose:
        print(line)
    return mail_string.strip()


def extract_from_header(msg, key):
    value, encoding = decode_header(msg[key])[0]
    if isinstance(value, bytes) and isinstance(encoding, str):
        value = value.decode(encoding)
    else:
        value = str(value)
    return value
