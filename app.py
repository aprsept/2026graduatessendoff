import base64
import io
import hmac
import logging
import smtplib
from email.message import EmailMessage
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

st.set_page_config(page_title="2026 Graduates Send-off", page_icon="🎓", layout="centered", initial_sidebar_state="collapsed")
ROOT = Path(__file__).parent
logger = logging.getLogger(__name__)

def image_data(path):
    return base64.b64encode((ROOT / path).read_bytes()).decode()

logo = image_data('assets/cis_logo.png')
st.markdown(f'''<style>
.stApp {{background: radial-gradient(ellipse at 27% 24%, rgba(241,173,219,.6), transparent 25%),radial-gradient(ellipse at 65% 37%, rgba(45,96,191,.55), transparent 34%),radial-gradient(ellipse at 82% 78%, rgba(166,213,175,.4), transparent 25%),linear-gradient(155deg,#62b7cb 0%,#a4c9e7 49%,#2489bd 100%);background-attachment:fixed;}}
.block-container {{max-width:790px;padding-top:2rem;padding-bottom:4rem;}}
.hero {{text-align:center;color:white;text-shadow:0 1px 8px #225f8b70;margin:1rem auto 1.5rem;}}
.hero h1 {{font-family:Georgia,serif;font-size:clamp(2.4rem,6vw,4rem);line-height:1.12;margin:1rem 0;}}
.hero p {{font-size:1.12rem;line-height:1.7;}}
.pill {{display:inline-block;background:white;color:#263951;padding:.55rem 1.35rem;border-radius:999px;font-weight:750;letter-spacing:.06em;text-shadow:none;}}
.logo {{display:block;margin-left:auto;width:215px;max-width:55%;}}
[data-testid="stForm"],div[data-testid="stVerticalBlockBorderWrapper"] {{background:rgba(255,255,255,.93);border-radius:20px;}}
[data-testid="stForm"] {{padding:1.2rem 1.5rem;box-shadow:0 12px 35px #0e4b7733;}}
.stButton button[kind="primary"],.stFormSubmitButton button {{background:#173d7c;color:white;border-radius:12px;border:none;}}
.smallnote {{color:#193e63;font-size:.93rem;}}
/* High contrast payment notice in both Streamlit themes. */
.payment-notice {{background:#e7f1fc !important;color:#173451 !important;border:1px solid #9bbbd9;border-left:5px solid #245a9d;border-radius:12px;padding:16px 18px;line-height:1.65;margin:12px 0 20px;}}
.payment-notice strong {{color:#102d50 !important;font-weight:750;}}
/* Keep the invitation readable against the watercolor background. */
.stApp .block-container > div [data-testid="stMarkdownContainer"] p {{color:#153956;}}
.stApp .block-container > div [data-testid="stMarkdownContainer"] strong {{color:inherit;}}
.hero, .hero h1, .hero p, .hero b {{color:#ffffff !important;}}
.hero .pill {{color:#263951 !important;}}
.logo {{width:245px;max-width:65%;height:auto;object-fit:contain;}}
/* The registration form is light regardless of the visitor's Streamlit theme. */
[data-testid="stForm"] {{background:#f8fbff !important;border:1px solid #d5e2ef !important;}}
[data-testid="stForm"] h1, [data-testid="stForm"] h2, [data-testid="stForm"] h3,
[data-testid="stForm"] p, [data-testid="stForm"] label,
[data-testid="stForm"] [data-testid="stWidgetLabel"] *,
[data-testid="stForm"] [data-testid="stMarkdownContainer"] *,
[data-testid="stForm"] [data-testid="stCaptionContainer"] {{color:#173451 !important;}}
[data-testid="stForm"] input,
[data-testid="stForm"] textarea,
[data-testid="stForm"] [data-baseweb="select"] > div {{background:#ffffff !important;color:#173451 !important;border:1px solid #a8bfd2 !important;border-radius:9px;}}
[data-testid="stForm"] input::placeholder,
[data-testid="stForm"] textarea::placeholder {{color:#65788a !important;opacity:1;}}
[data-testid="stForm"] [data-baseweb="select"] *,
[data-testid="stForm"] [data-baseweb="input"] *,
[data-testid="stForm"] [data-baseweb="textarea"] * {{color:#173451 !important;}}
[data-testid="stForm"] button[kind="primaryFormSubmit"],
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {{background:#173d7c !important;color:#ffffff !important;}}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button * {{color:#ffffff !important;}}


/* Registration uses st.container(border=True), not st.form. */
[data-testid="stVerticalBlockBorderWrapper"] input,
[data-testid="stVerticalBlockBorderWrapper"] textarea,
[data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="select"] > div,
[data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="base-input"] {{background-color:#f5f7fa !important;color:#173451 !important;border-color:#cbd5e1 !important;}}
[data-testid="stVerticalBlockBorderWrapper"] input::placeholder,
[data-testid="stVerticalBlockBorderWrapper"] textarea::placeholder {{color:#64748b !important;opacity:1;}}
[data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="input"] *,
[data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="select"] *,
[data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="textarea"] * {{color:#173451 !important;}}
/* Ensure registration failure alert text stays white and readable. */
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) {{background:#9f2440 !important;}}
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) *,
[data-testid="stAlertContentError"] * {{color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;}}
/* White readable text on submission upload link and payment proof picker. */
[data-testid="stLinkButton"] a, [data-testid="stLinkButton"] a *,
[data-testid="stFileUploader"] button, [data-testid="stFileUploader"] button *,
[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"],
[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] * {{color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;}}
[data-testid="stLinkButton"] a,
[data-testid="stFileUploader"] button {{background:#173d7c !important;border-color:#173d7c !important;}}
/* Keep the uploader's surrounding instructions dark on light backgrounds. */
[data-testid="stFileUploader"] label *,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] * {{color:#173451 !important;-webkit-text-fill-color:#173451 !important;}}
/* Organizer dashboard: buttons and their nested labels. */
.stApp:has(.admin-page-marker) .stButton button,
.stApp:has(.admin-page-marker) .stDownloadButton button {{background:#173d7c !important;color:#ffffff !important;border:1px solid #8dc7ff !important;font-weight:700 !important;}}
.stApp:has(.admin-page-marker) .stButton button *,
.stApp:has(.admin-page-marker) .stDownloadButton button * {{color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;}}
.stApp:has(.admin-page-marker) .stButton button:hover,
.stApp:has(.admin-page-marker) .stDownloadButton button:hover {{background:#245a9d !important;}}
/* Dark readable input text, white labels and captions on the blue page. */
.stApp:has(.admin-page-marker) [data-testid="stWidgetLabel"] *,
.stApp:has(.admin-page-marker) [data-testid="stCaptionContainer"] *,
.stApp:has(.admin-page-marker) [data-testid="stMetric"] *,
.stApp:has(.admin-page-marker) h1,
.stApp:has(.admin-page-marker) h2,
.stApp:has(.admin-page-marker) h3 {{color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;}}
.stApp:has(.admin-page-marker) input {{background:#f5f7fa !important;color:#173451 !important;-webkit-text-fill-color:#173451 !important;}}
.stApp:has(.admin-page-marker) [data-testid="stExpander"] {{background:rgba(12,45,82,.75) !important;border-radius:12px;}}
.stApp:has(.admin-page-marker) [data-testid="stExpander"] summary *,
.stApp:has(.admin-page-marker) [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {{color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;}}
/* Organizer empty-state message. */
.admin-empty-state {{background:#173d7c;color:#ffffff !important;padding:14px 18px;border-radius:12px;margin:10px 0;}}
.admin-empty-state * {{color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;}}
/* Submit button: force white text even with Streamlit's dark theme. */
.st-key-submit_registration button,
.st-key-submit_registration button p,
.st-key-submit_registration button span,
.st-key-submit_registration button [data-testid="stMarkdownContainer"] * {{color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;}}
.st-key-submit_registration button {{background:#173d7c !important;border:1px solid #173d7c !important;}}
.st-key-submit_registration button:hover {{background:#245a9d !important;}}

</style>''', unsafe_allow_html=True)

# Production storage: Google Sheets for registration records and Google Drive for receipts.
# Streamlit Cloud local files are ephemeral, so this app intentionally does not pretend
# local SQLite/CSV storage is a durable production backend.
def google_clients():
    """Use the service account for Sheets and the user's OAuth for My Drive."""
    import gspread
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials as UserCredentials

    service_info = dict(st.secrets['gcp_service_account'])
    if 'private_key' in service_info:
        service_info['private_key'] = service_info['private_key'].replace('\\n', '\n').strip() + '\n'
    sheets_creds = ServiceAccountCredentials.from_service_account_info(
        service_info, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    sheets = gspread.authorize(sheets_creds)

    oauth = st.secrets['google_oauth']
    drive_creds = UserCredentials(
        token=None,
        refresh_token=oauth['refresh_token'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=oauth['client_id'],
        client_secret=oauth['client_secret'],
        scopes=['https://www.googleapis.com/auth/drive'],
    )
    drive = build('drive', 'v3', credentials=drive_creds, cache_discovery=False)
    return sheets, drive

FIELDS = ['registration_id','submitted_at_utc','name','email','mobile','participant_type',
          'has_submission','submission_type','submission_minutes','submission_link',
          'receipt_drive_file_id','payment_status','qr_token','email_status','checked_in_at_utc','verified_at_utc']

def worksheet(client):
    sheet = client.open_by_key(st.secrets['google_sheet_id']).sheet1
    if not sheet.row_values(1):
        sheet.append_row(FIELDS)
    return sheet

def upload_receipt(drive, uploaded, registration_id):
    from googleapiclient.http import MediaIoBaseUpload
    mime = {'pdf':'application/pdf','jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png'}[uploaded.name.rsplit('.',1)[-1].lower()]
    media = MediaIoBaseUpload(io.BytesIO(uploaded.getvalue()), mimetype=mime, resumable=False)
    file = drive.files().create(body={'name':f'{registration_id}_receipt.{uploaded.name.rsplit(".",1)[-1].lower()}',
        'parents':[st.secrets['receipt_folder_id']]},media_body=media,fields='id').execute()
    return file['id']

def make_qr_png(token):
    import qrcode
    out = io.BytesIO()
    qrcode.make(f"SENDOFF2026:{token}").save(out, format='PNG')
    return out.getvalue()

def send_ticket(email, name, token):
    # Configure [smtp] in Streamlit Secrets. SMTP is used only on committee approval.
    smtp = st.secrets['smtp']
    msg = EmailMessage()
    msg['Subject'] = '2026 Graduates Send-off — Your confirmed entry QR code'
    msg['From'] = smtp['sender_email']
    msg['To'] = email
    msg.set_content(f"""Hello {name},

Your $10 payment has been verified and your registration is confirmed!

2026 Graduates Send-off
Friday, December 4, 2026 | 5:00–7:00 PM
KJRI New York

Please show the attached QR code at check-in. Each code can be checked in once.

See you there!
The Organizing Committee
""")
    msg.add_attachment(make_qr_png(token), maintype='image', subtype='png', filename='sendoff-entry-qr.png')
    with smtplib.SMTP_SSL(smtp.get('host','smtp.gmail.com'), int(smtp.get('port',465)), timeout=25) as server:
        server.login(smtp['username'], smtp['app_password'])
        server.send_message(msg)

def update_fields(sheet, row_number, changes):
    from gspread.utils import rowcol_to_a1
    sheet.batch_update([{'range':rowcol_to_a1(row_number,FIELDS.index(key)+1), 'values':[[value]]} for key,value in changes.items()])

st.markdown(f'<img class="logo" src="data:image/png;base64,{logo}" alt="Columbia Indonesian Society logo">',unsafe_allow_html=True)
st.markdown('''<div class="hero"><span class="pill">YOU’RE INVITED</span>
<h1>2026 Graduates<br>Send-off</h1>
<p>Friday, December 4, 2026 &nbsp;·&nbsp; 5:00–7:00 PM<br><b>KJRI New York</b></p></div>''',unsafe_allow_html=True)

st.markdown('''Join us as we celebrate our 2026 graduates and send them off with warm wishes, memorable performances, and good company! Whether you're graduating or joining to celebrate, everyone is welcome to register. The engagement fee is **$10 per attendee**. Please send your payment via **Zelle to Septy at (646) 295-2209**, then upload your payment confirmation below.''')

page = st.query_params.get('page','register')
if page == 'admin':
    st.markdown('<span class="admin-page-marker" style="display:none"></span>', unsafe_allow_html=True)
    st.subheader('🔐 Organizer dashboard')
    if 'admin_password' not in st.secrets or 'google_sheet_id' not in st.secrets:
        st.error('Organizer backend is not configured yet. Follow README.md.')
        st.stop()
    password = st.text_input('Organizer password',type='password')
    if not password or password != st.secrets['admin_password']:
        st.markdown(
            """
            <div style="
                background-color: #214E80;
                color: #FFFFFF;
                padding: 14px 20px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                border: 1px solid #8DC7FF;
                margin-bottom: 15px;
            ">
                Enter the organizer password to view registrations.
            </div>
            """,
            unsafe_allow_html=True
        )
        st.stop()
    try:
        sheets, drive = google_clients()
        sheet = worksheet(sheets)
        values = sheet.get_all_values()
        records = [dict(zip(FIELDS, row + [''] * max(0,len(FIELDS)-len(row)))) for row in values[1:]]
        df = pd.DataFrame(records, columns=FIELDS)
        st.metric('Total registrations',len(df))
        if records:
            a,b,c = st.columns(3)
            a.metric('Pending',sum(r['payment_status']=='Pending verification' for r in records))
            b.metric('Approved',sum(r['payment_status']=='Approved' for r in records))
            c.metric('Checked in',sum(bool(r['checked_in_at_utc']) for r in records))
            st.download_button('Download registrations CSV',df.to_csv(index=False),file_name='sendoff_registrations.csv',mime='text/csv')
            st.subheader('Review payments')
            for row_num, r in enumerate(records, start=2):
                with st.expander(f"{r['name']} · {r['registration_id']} · {r['payment_status']}"):
                    st.write(f"{r['email']} · {r['participant_type']}")
                    st.write('Receipt Drive file ID:',r['receipt_drive_file_id'])
                    st.caption('Open the receipt in the private Google Drive folder and independently verify the Zelle transaction before approving.')
                    if r['payment_status'] == 'Pending verification':
                        left,right = st.columns(2)
                        if left.button('Approve and email QR',key=f"approve_{row_num}"):
                            token = uuid4().hex
                            now = datetime.now(timezone.utc).isoformat()
                            # Persist token and approval BEFORE email, to prevent issuing multiple tickets.
                            update_fields(sheet,row_num,{'payment_status':'Approved','qr_token':token,'verified_at_utc':now,'email_status':'Pending send'})
                            try:
                                send_ticket(r['email'],r['name'],token)
                                update_fields(sheet,row_num,{'email_status':'Sent'})
                                st.success('Approved; QR email sent.')
                            except Exception:
                                update_fields(sheet,row_num,{'email_status':'Send failed'})
                                st.error('Payment approved but email failed. Configure SMTP and use the retry action.')
                            st.rerun()
                        if right.button('Reject payment',key=f"reject_{row_num}"):
                            update_fields(sheet,row_num,{'payment_status':'Rejected'})
                            st.rerun()
                    elif r['payment_status']=='Approved':
                        st.write('Email status:',r['email_status'] or 'Not sent')
                        if r['email_status']!='Sent' and st.button('Retry sending QR email',key=f"retry_{row_num}"):
                            try:
                                send_ticket(r['email'],r['name'],r['qr_token'])
                                update_fields(sheet,row_num,{'email_status':'Sent'})
                                st.success('Email sent.')
                            except Exception:
                                st.error('Email failed again. Check SMTP configuration.')
                            st.rerun()
            st.subheader('📷 Event-day QR check-in')
            st.caption('Open this organizer dashboard on a phone, allow camera access, and photograph the attendee’s QR ticket. You can also paste the QR content manually.')
            camera_photo = st.camera_input('Scan a participant QR ticket', key='ticket_camera')
            decoded_qr = ''
            if camera_photo is not None:
                try:
                    import cv2
                    import numpy as np
                    image_bytes = np.frombuffer(camera_photo.getvalue(), dtype=np.uint8)
                    image_array = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
                    if image_array is not None:
                        decoded_qr, _, _ = cv2.QRCodeDetector().detectAndDecode(image_array)
                    if decoded_qr:
                        st.success('QR code recognized. Click Check in participant to confirm.')
                    else:
                        st.warning('No readable QR code found. Try moving closer, improving the lighting, or using manual entry.')
                except Exception:
                    logger.exception('QR camera decoding failed')
                    st.error('Camera QR decoding failed. Check that opencv-python-headless is installed, or use manual entry.')
            manual_qr = st.text_input('Or paste QR code content', placeholder='SENDOFF2026:...', key='manual_ticket_qr')
            if st.button('Check in participant', type='primary', key='confirm_ticket_checkin'):
                raw_qr = (manual_qr or decoded_qr).strip()
                if not raw_qr:
                    st.error('Please scan a QR code or enter the ticket code first.')
                elif not raw_qr.startswith('SENDOFF2026:'):
                    st.error('This is not a valid Send-off QR ticket.')
                else:
                    token = raw_qr.removeprefix('SENDOFF2026:')
                    # Reload before checking to catch check-ins from other volunteers.
                    fresh_values = sheet.get_all_values()
                    fresh_records = [dict(zip(FIELDS, row + [''] * max(0, len(FIELDS) - len(row)))) for row in fresh_values[1:]]
                    found = [(i, r) for i, r in enumerate(fresh_records, start=2)
                             if r['qr_token'] and hmac.compare_digest(r['qr_token'], token)]
                    if not found:
                        st.error('Invalid QR code: no matching ticket found.')
                    else:
                        i, r = found[0]
                        if r['payment_status'] != 'Approved':
                            st.error('Payment not approved. Do not admit this attendee.')
                        elif r['checked_in_at_utc']:
                            st.warning(f"Already checked in: {r['name']}")
                        else:
                            update_fields(sheet, i, {'checked_in_at_utc': datetime.now(timezone.utc).isoformat()})
                            st.success(f"Checked in successfully: {r['name']}")
                            st.info('Ready for the next participant. Clear the camera photo and scan the next ticket.')
        else:
            st.markdown('<div class="admin-empty-state">No registrations yet.</div>', unsafe_allow_html=True)
    except Exception:
        logger.exception('Organizer dashboard failed')
        st.error('Unable to load or update organizer records. Check permissions and secrets. See Streamlit server logs for details.')
    st.stop()

# Use a normal container: radio changes must rerun immediately to reveal conditional fields.
with st.container(border=True):
    st.subheader('Registration form')
    name = st.text_input('Full name *',max_chars=150)
    email = st.text_input('Email address *',max_chars=254)
    mobile = st.text_input('Mobile number *',placeholder='+1 (___) ___-____',max_chars=30)
    participant_type = st.selectbox('Are you a graduate or non-graduate? *',['Select an option','Graduate','Non-graduate'])
    st.markdown('#### Optional event submission')
    has_submission = st.radio('Would you like to submit a performance or contribution for the event? *',['No','Yes'],horizontal=True)
    submission_type = ''
    submission_minutes = 0
    submission_link = ''
    if has_submission == 'Yes':
        submission_type = st.text_input('What kind of submission? *',placeholder='e.g., video, live singing, dance, speech, stand-up comedy')
        submission_minutes = st.number_input('How many minutes will your submission take? *',min_value=1,max_value=120,value=5,step=1)
        submission_link = st.text_input('Link to your submission (optional)',placeholder='https://drive.google.com/...')
        upload_url = st.secrets.get('submission_upload_url','')
        if upload_url:
            st.link_button('Upload your submission to Google Drive', upload_url, use_container_width=True)
            st.caption('Upload using the link, then paste a shareable file link above if available. A standard folder link may not allow uploads without editor access.')
        else:
            st.info('The organizer will provide the Google Drive upload link. You can submit your registration now.')
    st.markdown('#### Engagement fee · $10')
    st.markdown('''<div class="payment-notice">Pay <strong>$10 via Zelle</strong> to <strong>Septy — (646) 295-2209</strong>.<br>Confirm the recipient in Zelle before sending. Payment will be manually verified.</div>''', unsafe_allow_html=True)
    receipt = st.file_uploader('Upload proof of payment * (PDF, JPG or PNG)',type=['pdf','jpg','jpeg','png'],accept_multiple_files=False)
    consent = st.checkbox('I confirm that my information is accurate and agree that organizers may use it to manage this event. *')
    submitted = st.button('Submit registration',type='primary',use_container_width=True, key='submit_registration')

if submitted:
    errors=[]
    if not name.strip(): errors.append('Enter your full name.')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email.strip()): errors.append('Enter a valid email address.')
    if len(re.sub(r'\D','',mobile)) < 7: errors.append('Enter a valid mobile number.')
    if participant_type == 'Select an option': errors.append('Select graduate or non-graduate.')
    if has_submission == 'Yes' and not submission_type.strip(): errors.append('Describe your submission.')
    if receipt is None: errors.append('Upload your proof of payment.')
    elif receipt.size > 10*1024*1024: errors.append('Payment proof must be 10 MB or smaller.')
    if not consent: errors.append('Please confirm the consent checkbox.')
    if errors:
        for e in errors: st.error(e)
    elif 'gcp_service_account' not in st.secrets or 'google_sheet_id' not in st.secrets or 'receipt_folder_id' not in st.secrets or 'google_oauth' not in st.secrets:
        st.error('Registration is not live yet: the organizer needs to configure Google Sheets and Drive storage. No registration was saved.')
    else:
        try:
            sheets, drive = google_clients()
            sheet = worksheet(sheets)
            registration_id = uuid4().hex[:12].upper()
            receipt_id = upload_receipt(drive,receipt,registration_id)
            record=[registration_id,datetime.now(timezone.utc).isoformat(),name.strip(),email.strip().lower(),mobile.strip(),participant_type,
                has_submission,submission_type.strip(),submission_minutes if has_submission=='Yes' else '',submission_link.strip(),receipt_id,'Pending verification','','','','']
            sheet.append_row(record,value_input_option='RAW')
            st.markdown(f'''<div style="background:#174b3a;color:#b9ffcf;padding:18px 22px;border-radius:12px;border:1px solid #73e6a0;font-weight:650;line-height:1.7;">Registration received! Your registration ID is <strong style="color:#b9ffcf;">{registration_id}</strong>. The committee will verify your Zelle payment. Your entry QR code will be emailed only after approval.</div>''', unsafe_allow_html=True)
            st.balloons()
        except Exception:
            logger.exception('Registration submission failed (Google authentication, receipt upload, or sheet append)')
            st.error('We could not save your registration. Please contact the organizer before trying again to avoid duplicate payments or submissions. The technical error is available in the organizer’s Streamlit logs.')

st.caption('Organized by Columbia Indonesian Society · Questions? Contact the event organizers. Payment receipts are accessible only to authorized organizers.')
