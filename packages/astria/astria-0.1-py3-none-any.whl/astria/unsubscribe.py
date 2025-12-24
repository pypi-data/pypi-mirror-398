import imaplib
from collections import defaultdict
import email
from bs4 import BeautifulSoup
import re
import os

servers = {
    "Gmail": "imap.gmail.com",
    "Outlook": "imap-mail.outlook.com",
    "Hotmail": "imap-mail.outlook.com",
    "Icloud": "imap.mail.me.com",
}


def start_unsubscriber(provider, username, password):
    """Establishes connection and logs in."""
    mail = imaplib.IMAP4_SSL(servers[provider])
    mail.login(username, password)
    mail.select("inbox")
    return mail


def extract_links_from_html(html_content):
    """Parses HTML and finds all 'unsubscribe' links."""
    soup = BeautifulSoup(html_content, "html.parser")
    links = [
        link["href"]
        for link in soup.find_all("a", href=True)
        if "unsubscribe" in link["href"].lower()
    ]
    return links


def process_email_data(raw_email_bytes):
    """Helper function to parse a single email bytes object and return a dictionary of {sender: set(links)}."""
    msg = email.message_from_bytes(raw_email_bytes)
    # extract sender for readability
    sender_header = msg.get("From", "Unknown Sender")
    # clean up the sender string
    match = re.search(r"<(.*?)>", sender_header)
    sender = match.group(1) if match else sender_header.strip()
    email_links = defaultdict(set)
    # extract links
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                try:
                    html_content = part.get_payload(decode=True).decode(errors="ignore")
                    links = extract_links_from_html(html_content)
                    for link in links:
                        email_links[sender].add(link)
                except Exception:
                    pass
    else:
        content_type = msg.get_content_type()
        if content_type == "text/html":
            try:
                content = msg.get_payload(decode=True).decode(errors="ignore")
                links = extract_links_from_html(content)
                for link in links:
                    email_links[sender].add(link)
            except Exception:
                pass
    return email_links


def save_links(links_with_sender):
    """Saves the list of extracted links to a text file and opens it in the browser."""
    # Save to links.txt
    with open("links.txt", "w") as f:
        for sender, link in links_with_sender:
            f.write(f"{sender}: {link}\n")

    # Get absolute path
    txt_file_path = os.path.abspath("links.txt")
    print(f"File saved at: {txt_file_path}")


def search_for_email(provider, username, password):
    """
    Main function to connect, search, fetch, process emails, and save links.
    The automated 'clicking' functionality has been removed.
    """
    mail = start_unsubscriber(provider, username, password)
    print("Searching for emails...")
    print("Process could take a few minutes")
    _, search_data = mail.search(None, '(BODY "unsubscribe")')
    email_ids = search_data[0].split()
    print(f"Found {len(email_ids)} emails. Fetching content...")
    all_links_dict = defaultdict(set)
    batch_size = 50
    for i in range(0, len(email_ids), batch_size):
        batch_ids = email_ids[i : i + batch_size]
        id_string = b",".join(batch_ids)
        status, response_data = mail.fetch(id_string, "(RFC822)")
        for response_part in response_data:
            if isinstance(response_part, tuple):
                links_dict = process_email_data(response_part[1])
                for sender, links in links_dict.items():
                    all_links_dict[sender].update(links)
    mail.logout()
    # convert to tuples for saving to the file
    links_with_sender = []
    for sender, links in all_links_dict.items():
        for link in links:
            links_with_sender.append((sender, link))
    print(f"Found {len(links_with_sender)} unique subscriptions/links:")
    # Function call: save_links()
    save_links(links_with_sender)
