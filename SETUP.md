# ATK Dashboard — Setup Guide

Follow these steps in order. Takes about 20 minutes total.

---

## STEP 1 — Install Python (if not already installed)

1. Go to https://www.python.org/downloads/
2. Download and install Python 3.11 or higher
3. During install, tick "Add Python to PATH"

---

## STEP 2 — Install the app dependencies

1. Open Terminal (Mac: press Cmd+Space, type "Terminal", press Enter)
2. Type this command and press Enter:

```
cd "/Users/deepakkewal/Desktop/Dashboard build" && pip install -r requirements.txt
```

Wait for it to finish.

---

## STEP 3 — Create the Google Sheet

1. Go to sheets.google.com (sign in as rahulkewal6@gmail.com)
2. Create a new blank spreadsheet
3. Name it exactly: **ATK Dashboard**
4. Create 3 sheets (tabs at the bottom):
   - Rename "Sheet1" to: **Pipeline**
   - Add a new tab named: **Stage History**
   - Add a new tab named: **Event Calendar**

5. In the **Pipeline** tab, paste these headers in Row 1 (one per cell A to O):
```
Company Name | Exhibition | Source | Contact Email | Contact Name | Current Stage | Brief Version | Design Options Sent | Vendor Quote (AED) | Margin (AED) | Client Quote (AED) | Discount Given | Notes | Last Updated By | Date Added
```

6. In the **Stage History** tab, paste these headers in Row 1:
```
Company Name | Stage | Updated By | Date/Time | Notes
```

7. In the **Event Calendar** tab, paste these headers in Row 1:
```
Event Name | Venue | City | Start Date | End Date | Exhibitor Count | Official URL | Verification Status | Last Verified | Date Priority | Exhibitor Priority | Notes
```

8. Copy the Sheet ID from the URL bar:
   - URL looks like: https://docs.google.com/spreadsheets/d/**THIS_IS_YOUR_ID**/edit
   - Copy only the ID part (between /d/ and /edit)

---

## STEP 4 — Set up Google Sheets API

1. Go to: https://console.cloud.google.com/
2. Sign in with rahulkewal6@gmail.com
3. Click **"Select a project"** → **"New Project"**
4. Name it: **ATK Dashboard** → click Create
5. Make sure the new project is selected

6. In the search bar at the top, search: **Google Sheets API**
7. Click on it → click **Enable**

8. Search again: **Google Drive API**
9. Click on it → click **Enable**

10. In the left sidebar: **APIs & Services → Credentials**
11. Click **"+ Create Credentials"** → **"Service account"**
12. Name: **atk-dashboard** → click Create and Continue → click Done

13. Click on the service account you just created
14. Go to the **Keys** tab → **Add Key** → **Create new key** → JSON → Create
15. A JSON file will download to your computer — **keep this safe**

---

## STEP 5 — Share the Google Sheet with the service account

1. Open the downloaded JSON file in any text editor (Notepad/TextEdit)
2. Find the line that says **"client_email"** — copy the email address (looks like: atk-dashboard@your-project.iam.gserviceaccount.com)
3. Go back to your ATK Dashboard Google Sheet
4. Click **Share** (top right)
5. Paste the service account email → give it **Editor** access → click Share

---

## STEP 6 — Fill in the secrets file

1. Open this file: `.streamlit/secrets.toml` (in the Dashboard build folder)
2. Fill in:
   - `GOOGLE_SHEET_ID` = the ID you copied in Step 3
   - Under `[gcp_service_account]`: copy each value from your downloaded JSON file into the matching field

---

## STEP 7 — Run the dashboard

1. Open Terminal
2. Run:

```
cd "/Users/deepakkewal/Desktop/Dashboard build" && streamlit run app.py
```

3. Your browser will open automatically at http://localhost:8501
4. You should see the ATK Dashboard

---

## Sharing with Bhavika

Once the app is running locally, to share it with Bhavika:

**Option A — Run on the same network:**
- Share your local IP address (e.g. http://192.168.1.x:8501) with Bhavika while the app is running

**Option B — Deploy to Streamlit Community Cloud (free, accessible from anywhere):**
1. Create a free account at https://streamlit.io/cloud
2. Upload the project to GitHub (private repo)
3. Connect Streamlit Cloud to the repo
4. Add secrets in the Streamlit Cloud dashboard
5. Share the public URL with Bhavika

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Module not found" | Run: pip install -r requirements.txt |
| "Google Sheets connection failed" | Check service account email is shared on the Sheet |
| "Apollo API not connected" | Check API key in secrets.toml |
| App goes to sleep | Normal on free Streamlit Cloud — refresh the page |
