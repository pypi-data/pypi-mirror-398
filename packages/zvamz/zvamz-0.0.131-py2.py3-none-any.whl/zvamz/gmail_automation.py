import os
from googleapiclient.discovery import build
import base64
import re
import requests

def extract_email_body(payload):
    """Recursively extract plain text or HTML body from payload parts."""
    if payload is None:
        return ''

    # Check if this part has the data
    mime_type = payload.get('mimeType', '')
    body_data = payload.get('body', {}).get('data')
    if body_data and mime_type in ['text/plain', 'text/html']:
        try:
            decoded = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
            if mime_type == 'text/html':
                # Remove HTML tags for plain text version
                return re.sub('<[^<]+?>', '', decoded)
            return decoded
        except Exception as e:
            print(f"Error decoding body: {e}")
            return ''

    # If this part has nested parts, recurse
    parts = payload.get('parts', [])
    for part in parts:
        body = extract_email_body(part)
        if body:
            return body

    return ''

def get_emails(creds, unread=True, folder='INBOX', max_results=10):
    """
    Retrieves emails from a specific Gmail label/folder.
    
    Parameters:
        unread (bool): If True, fetch only unread messages.
        folder (str): The label/folder name (e.g. 'INBOX', 'DRAFT', '02 Target').
        max_results (int): Maximum number of emails to fetch.
    
    Returns:
        List of message summaries (subject and id).
    """
    service = build('gmail', 'v1', credentials=creds)

    # Get label ID for the given folder name
    label_id = None
    label_results = service.users().labels().list(userId='me').execute()
    for label in label_results.get('labels', []):
        if label['name'].lower() == folder.lower():
            label_id = label['id']
            break

    if not label_id:
        raise Exception(f"Label '{folder}' not found.")

    # Build query string
    query = 'is:unread' if unread else ''

    # Fetch messages
    response = service.users().messages().list(
        userId='me',
        labelIds=[label_id],
        q=query,
        maxResults=max_results
    ).execute()

    messages = response.get('messages', [])
    email_data = []

    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()
        subject = "(No Subject)"
        payload = msg_detail['payload']
        parts = payload.get('parts', [])
        for header in msg_detail['payload']['headers']:
            if header['name'] == 'Subject':
                subject = header['value']
            elif header['name'] == 'From':
                sender = header['value']

        # Extract plain text body
        body = extract_email_body(payload)

        # Extract attachments
        attachments = []
        for part in parts:
            if part.get('filename'):
                file_name = part['filename']
                mime_type = part['mimeType']
                attachment_id = part['body'].get('attachmentId')

                attachments.append({
                    'filename': file_name,
                    'attachment_id': attachment_id,
                    'mime_type': mime_type
                })

        email_data.append({
            'id': msg['id'],
            'subject': subject,
            'from': sender,
            'body': body,
            'matching_attachments': attachments
        })

    return email_data

def download_attachment(creds, emails, folderPath, fileNameLike='', fileType=''):
    """
    Dowloads specific file from emails data.
    
    Parameters:
        emails: result of get_emails function.
        folderPath: where to save the attachment that will be downloaded
        fileNameLike: to filter the files by name that contains the string (e.g. 'report').
        fileType: to filter the files by type (e.g. '.csv', '.xlsx').
    
    Returns:
        download the files.
    """
    service = build('gmail', 'v1', credentials=creds)
    saved_files = []
    
    # Ensure the folder exists
    os.makedirs(folderPath, exist_ok=True)

    for email in emails:
        message_id = email['id']
        for att in email.get('matching_attachments', []):
            filename = att['filename']
            
            # Check filters
            name_match = fileNameLike.lower() in filename.lower() if fileNameLike else True
            type_match = filename.lower().endswith(fileType.lower()) if fileType else True

            if name_match and type_match:
                attachment_id = att['attachment_id']

                # Fetch actual attachment content from Gmail API
                att_data = service.users().messages().attachments().get(
                    userId='me',
                    messageId=message_id,
                    id=attachment_id
                ).execute()

                file_data = base64.urlsafe_b64decode(att_data['data'].encode('UTF-8'))

                path = os.path.join(folderPath, filename)
                with open(path, 'wb') as f:
                    f.write(file_data)

                saved_files.append(filename)

        # Mark email as read
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

    return saved_files

def gchat_space(formatted_message, webhook_url):
    payload = {
            'text': formatted_message
            }
    response = requests.post(webhook_url, json=payload)

    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print("Failed to send message:", response.status_code, response.text)

