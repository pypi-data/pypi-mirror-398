import imaplib

servers = {
    "Gmail": "imap.gmail.com",
    "Outlook": "imap-mail.outlook.com",
    "Hotmail": "imap-mail.outlook.com",
    "Icloud": "imap.mail.me.com",
}


def mail_selection(mail, selection, custom_address="n/a"):
    """Searches mail box for selected emails

    Args:
        mail (imaplib connection): imaplib's connection to the email object
        selection (string): type of emails to be marked for delition
                                       passes the address . Defaults to "n/a".
    Returns:
        messages : returns list of messages that fit the search
    """
    messages = None

    if selection == "Newsletters":
        status, messages = mail.search(None, '(BODY "unsubscribe")')

    elif selection == "All":
        status, messages = mail.search(None, "ALL")

    elif selection == "Custom":
        status, messages = mail.search(None, f'FROM "{custom_address}"')

    if not messages or messages[0] == b"":
        print("No emails found matching that criteria.")

    return messages[0].split()


def connect_to_email(provider, username, password, selection, custom_address="n/a"):
    """Tries connection to email server ,
    checks connection and marks emails for deletion
    """
    mail = imaplib.IMAP4_SSL(servers[provider])

    try:
        print(f"Logging in as {username}...")
        mail.login(username, password)
        mail.select("INBOX")

        email_ids = mail_selection(mail, selection, custom_address)
        print(f"Found {len(email_ids)} emails.")
        if len(email_ids) == 0:
            return

        # loops through the list in chunks of 100
        for i in range(0, len(email_ids), 100):
            batch = email_ids[i : i + 100]

            #  allows sending one command for 100 emails
            email_id_string = b",".join(batch)

            mail.store(email_id_string, "+FLAGS", "\\Deleted")

            # deletes the batch immediately
            mail.expunge()

            print(
                f"Deleted {min(i + 100, len(email_ids))} emails out of {len(email_ids)}"
            )

        mail.close()
        mail.logout()
        print("Deletion complete.")

    except Exception as error:
        print(f"Error: {error}")
        print("Please run 'setup' again")
