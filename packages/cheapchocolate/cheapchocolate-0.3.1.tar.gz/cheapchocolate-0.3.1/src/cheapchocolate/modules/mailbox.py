import os


def get_local_mails():
    mails = []
    for mail_file in os.listdir(get_local_mailbox_folder()):
        mail_file.split(" - ")[0]
        mails.append(mail_file.split(" - ")[0])
    return mails


def get_local_mailbox_folder():
    mailbox_folder = "mailbox"
    if not os.path.exists(mailbox_folder):
        os.mkdir(mailbox_folder)
    return mailbox_folder
