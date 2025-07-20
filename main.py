import smtplib
import ssl
import os
import pandas as pd
import gspread
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime

#--- CONFIG ---
GOOGLE_SHEET_NAME = "SBI General Interest Form (Responses)"
SERVICE_ACCOUNT_FILE = "credentials.json"
LOGO_FILE = "EmailSignature.gif"

#--- Email Config ---
SENDER_EMAIL = os.getenv('EMAIL_USER')
SENDER_PASSWORD = os.getenv('GOOGLE_PASS')
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def get_new_signups():
    try:
        # Authenticate using the service account
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        
        # Open the spreadsheet and the first worksheet
        sh = gc.open(GOOGLE_SHEET_NAME).sheet1
        
        # Get all records from the sheet and convert to a pandas DataFrame
        records = sh.get_all_records()
        df = pd.DataFrame(records)
        
        # Filter for rows where "Automated Email sent" is empty
        new_signups_df = df[df["Automated Email Sent"] == ''].copy()
        
        # Add the original row index to update the correct cell later
        new_signups_df = new_signups_df.reset_index()
        new_signups_df ["original_row_index"] = new_signups_df.index + 2
        return sh, new_signups_df
    
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Error: Spreadsheet '{GOOGLE_SHEET_NAME}' not found.")
        return None, pd.DataFrame()
    
    except Exception as e:
        print(f"An error occurred while fetching data: {e}")
        return None, pd.DataFrame()
    
def send_welcome_email(recipient_name, recipient_email, departments_str):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Error: Email credentials are not set as environment variables.")
        return False
    
    try:
        message = MIMEMultipart("related")
        message["Subject"] = "Next Steps With SBI!"
        message["From"] = SENDER_EMAIL
        message["To"] = recipient_email
        
        # Department descriptions
        department_info = {
            'Research and Development': 'Researches and advises on cutting-edge sustainable materials, technologies, and methodologies, and conducts post-project analysis.',
            
            'Finance': 'Manages all financial aspects of projects, from initial budgeting and expense tracking, invoicing, and final financial reporting.',
            
            'Tech': 'Identifies, designs, and implements internal and external technologies with AI integration, managing software and system installation.',
            
            'Engineering': 'Designs and oversees the structural, mechanical (HVAC, plumbing), and electrical systems, including renewable energy integration and site planning.',
            
            'Architecture': 'Responsible for the aesthetic and functional design of projects, creating concepts, detailed drawings, and selecting sustainable materials.',
            
            'Public Relations': 'Handles recruitment, internal and external communications, project announcements, and public events, maintaining team morale.',
            
            'Legal': 'Manages contracts, ensures regulatory compliance, handles permitting, and oversees all legal aspects of the project.',
        }

        # Split the comma-separated departments string into a list
        departments_list = [dep.strip() for dep in departments_str.split(',')]
        
        # Generate the HTML for the department selections
        departments_html = '<br>'.join([
            f"<strong>{dep}</strong>: {department_info.get(dep, 'We\'ll be in touch soon with more information!')}"
            for dep in departments_list
        ])
        
        # Create the HTML content for the email
        html = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333333; line-height: 1.5; max-width: 600px;">
            <p>Hello {recipient_name},</p>
            <p>Thank you so much for completing our form and for your interest in joining Sustainable Building Initiative!</p>
            <p>We wanted to give you a quick update on what happens next:</p>
            <p>
                <b>Your Department Selections:</b><br>
                {departments_html}
            </p>
            <p>
                <b>What to Expect Next:</b><br>
                Our team will review your responses and reach out to you with more details about each department you’ve selected. You’ll also receive updates about opportunities, events, and important information for the upcoming semester.
            </p>
            <p>If you have any questions, feel free to reply to this email or contact our President at <a href="mailto:px.guzman@utexas.edu">px.guzman@utexas.edu</a>.</p>
            <p>Stay tuned—we’re excited to connect with you soon!</p>
            <p>
                <b>Best regards,</b><br>
                The Sustainable Building Initiative Team
            </p>
            <div style="margin-top: 20px;">
                <img src="cid:logoImage" style="width: 120px;" /><br>
                Website: <a href="http://utsbi.org" target="_blank">utsbi.org</a>
            </div>
            </div>
        </body>
        </html>
        """

        # Attach HTML to root message
        message.attach(MIMEText(html, "html"))
        
        # Optional: Add logo if file exists
        if os.path.exists(LOGO_FILE):
            with open(LOGO_FILE, "rb") as f:
                logo_data = f.read()
                logo = MIMEImage(logo_data)
                logo.add_header("Content-ID", "<logo>")
                message.attach(logo)
                
        # Create SMTP session and send email
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
                
        print(f"Email sent successfully to {recipient_email}")
        return True
    
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")
        return False


def update_email_sent_status(sheet, row_index):
    try:
        # Find the column index for "Automated Email Sent"
        headers = sheet.row_values(1)
        email_sent_col = headers.index("Automated Email Sent") + 1
        
        # Update the cell
        sheet.update_cell(row_index, email_sent_col, "Yes")
        print(f"Updated row {row_index} - marked email as sent")
        return True
    
    except Exception as e:
        print(f"Failed to update row {row_index}: {e}")
        return False


def main():    
    # Get new signups from Google Sheets
    sheet, new_signups_df = get_new_signups()
    
    if sheet is None or new_signups_df.empty:
        print("No new signups found or error accessing sheet.")
        return
    
    print(f"Found {len(new_signups_df)} new signups to process.")
    
    # Process each new signup
    for index, row in new_signups_df.iterrows():
        name = row.get("What is your name?", "")
        email = row.get("What is your email?", "")
        departments = row.get("Which department(s) do you want to be in? (Pick up to 2)", "")
        original_row = row.get("original_row_index")

        if not email or not name:
            print(f"Skipping row {original_row}: missing name or email")
            continue
        
        print(f"Processing: {name} ({email})")

        # Send email
        if send_welcome_email(name, email, departments):
            # Mark as sent in Google Sheets
            if update_email_sent_status(sheet, original_row):
                print(f"Successfully processed {name}")
            else:
                print(f"Email sent to {name} but failed to update sheet")
        else:
            print(f"Failed to process {name}")
    
    print("Email automation process completed.")

if __name__ == "__main__":
    main()