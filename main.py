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
LOGO_FILE = "logo.png"

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
        new_signups_df = df[df['Automated Email Sent'] == ''].copy()
        
        # Add the original row index to update the correct cell later
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
        print("Error: Email credentials (EMAIL_USER, EMAIL_APP_PASSWORD) are not set as environment variables.")
        return False
    
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
    departments_html = '<br><br>'.join(
        f"<u>{dep}</u>: {department_info.get(dep, 'We’ll be in touch soon with more information!')}" 
        for dep in departments_list
    )
    
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
    