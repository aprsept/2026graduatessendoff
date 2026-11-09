import base64
import io
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

st.set_page_config(page_title="2026 Graduates Send-off", page_icon="🎓", layout="centered", initial_sidebar_state="collapsed")
ROOT = Path(__file__).parent

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
</style>''', unsafe_allow_html=True)

# Production storage: Google Sheets for registration records and Google Drive for receipts.
# Streamlit Cloud local files are ephemeral, so this app intentionally does not pretend
# local SQLite/CSV storage is a durable production backend.
def google_clients():
    import gspread
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_service_account_info(dict(st.secrets['gcp_service_account']), scopes=[
        'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return gspread.authorize(creds), build('drive', 'v3', credentials=creds)

FIELDS = ['registration_id','submitted_at_utc','name','email','mobile','participant_type',
          'has_submission','submission_type','submission_minutes','submission_link',
          'receipt_drive_file_id','payment_status']

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

st.markdown(f'<img class="logo" src="data:image/png;base64,{logo}" alt="Columbia Indonesian Society logo">',unsafe_allow_html=True)
st.markdown('''<div class="hero"><span class="pill">YOU’RE INVITED</span>
<h1>2026 Graduates<br>Send-off</h1>
<p>Friday, December 4, 2026 &nbsp;·&nbsp; 5:00–7:00 PM<br><b>KJRI New York</b></p></div>''',unsafe_allow_html=True)

st.markdown('''Join us as we celebrate our 2026 graduates and send them off with warm wishes, memorable performances, and good company! Whether you're graduating or joining to celebrate, everyone is welcome to register. The engagement fee is **$10 per attendee**. Please send your payment via **Zelle to Septy at (646) 295-2209**, then upload your payment confirmation below.''')

page = st.query_params.get('page','register')
if page == 'admin':
    st.subheader('🔐 Organizer dashboard')
    if 'admin_password' not in st.secrets or 'google_sheet_id' not in st.secrets:
        st.error('Organizer backend is not configured yet. Follow README.md.')
        st.stop()
    password = st.text_input('Organizer password',type='password')
    if not password or password != st.secrets['admin_password']:
        st.info('Enter the organizer password to view registrations.')
        st.stop()
    try:
        sheets, _ = google_clients()
        rows = worksheet(sheets).get_all_records()
        df = pd.DataFrame(rows,columns=FIELDS)
        st.metric('Total registrations',len(df))
        if len(df):
            a,b,c = st.columns(3)
            a.metric('Graduates',(df['participant_type']=='Graduate').sum())
            b.metric('Non-graduates',(df['participant_type']=='Non-graduate').sum())
            c.metric('Performances',(df['has_submission']=='Yes').sum())
            st.dataframe(df,use_container_width=True,hide_index=True)
            st.download_button('Download CSV',df.to_csv(index=False).encode('utf-8'),file_name='graduates_sendoff_registrations.csv',mime='text/csv')
            st.caption('Receipts are stored privately in the configured Google Drive folder. Payment status is pending until the organizer verifies the Zelle transaction.')
        else:
            st.info('No registrations yet.')
    except Exception:
        st.error('Unable to load organizer records. Check Google permissions and Streamlit secrets.')
    st.stop()

with st.form('registration',clear_on_submit=False):
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
            st.markdown(f'**[Upload your submission to Google Drive]({upload_url})** (if applicable). Please make sure the organizers have access.')
        else:
            st.info('The organizer will provide the Google Drive upload link. You can submit your registration now.')
    st.markdown('#### Engagement fee · $10')
    st.info('Pay **$10 via Zelle** to **Septy — (646) 295-2209**. Confirm the recipient in Zelle before sending. Payment will be manually verified.')
    receipt = st.file_uploader('Upload proof of payment * (PDF, JPG or PNG)',type=['pdf','jpg','jpeg','png'],accept_multiple_files=False)
    consent = st.checkbox('I confirm that my information is accurate and agree that organizers may use it to manage this event. *')
    submitted = st.form_submit_button('Submit registration',type='primary',use_container_width=True)

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
    elif 'gcp_service_account' not in st.secrets or 'google_sheet_id' not in st.secrets or 'receipt_folder_id' not in st.secrets:
        st.error('Registration is not live yet: the organizer needs to configure Google Sheets and Drive storage. No registration was saved.')
    else:
        try:
            sheets, drive = google_clients()
            sheet = worksheet(sheets)
            registration_id = uuid4().hex[:12].upper()
            receipt_id = upload_receipt(drive,receipt,registration_id)
            record=[registration_id,datetime.now(timezone.utc).isoformat(),name.strip(),email.strip().lower(),mobile.strip(),participant_type,
                has_submission,submission_type.strip(),submission_minutes if has_submission=='Yes' else '',submission_link.strip(),receipt_id,'Pending verification']
            sheet.append_row(record,value_input_option='RAW')
            st.success(f'Registration received! Your registration ID is {registration_id}. Payment is pending organizer verification.')
            st.balloons()
        except Exception:
            st.error('We could not save your registration. Please contact the organizer before trying again to avoid duplicate payments or submissions.')

st.caption('Organized by Columbia Indonesian Society · Questions? Contact the event organizers. Payment receipts are accessible only to authorized organizers.')
