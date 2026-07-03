PIPELINE_STAGES = [
    # Outreach
    "Hot Lead (Apollo)",
    "Hot Lead (Deepak)",
    "Hot Lead (Inbound)",
    "Info Request Replied",
    # Brief
    "Brief Received (v1)",
    "Brief Received (v2)",
    "Brief Received (v3)",
    "Brief Sent to Designer",
    # Design
    "Design Option 1 Sent",
    "Design Option 2 Sent",
    "Design Option 3 Sent",
    "Additional Changes Requested",
    "New Brief Received (Client Changed)",
    "Revised Brief Sent to Designer",
    "Waiting for Design Feedback",
    # Quotation
    "Brief Sent to Vendor",
    "Vendor Quotation Received",
    "Client Quotation Prepared",
    "Client Quotation 1 Sent",
    "Client Requested Discount",
    "Discounted Quotation Sent",
    "Revised Quotation Sent",
    "Waiting for Final Approval",
    # Closed
    "Won",
    "Lost",
    "No Response — Follow Up Later",
]

# Status system for the Leads UI
# red           = action needed from our side (pending on us)
# design_prog   = brief with our in-house designer
# quote_prog    = quotation being prepared / waiting on vendor
# design_client = design sent to client, awaiting their feedback
# quote_client  = quotation sent to client, awaiting approval
STAGE_TIERS = {
    "Hot Lead (Apollo)":                  "red",
    "Hot Lead (Deepak)":                  "red",
    "Hot Lead (Inbound)":                 "red",
    "Info Request Replied":               "red",
    "Brief Received (v1)":                "red",
    "Brief Received (v2)":                "red",
    "Brief Received (v3)":                "red",
    "New Brief Received (Client Changed)": "red",
    "Additional Changes Requested":       "red",
    "Client Requested Discount":          "red",
    "No Response — Follow Up Later":      "red",
    "Brief Sent to Designer":             "design_prog",
    "Revised Brief Sent to Designer":     "design_prog",
    "Brief Sent to Vendor":               "quote_prog",
    "Vendor Quotation Received":          "quote_prog",
    "Client Quotation Prepared":          "quote_prog",
    "Design Option 1 Sent":               "design_client",
    "Design Option 2 Sent":               "design_client",
    "Design Option 3 Sent":               "design_client",
    "Waiting for Design Feedback":        "design_client",
    "Client Quotation 1 Sent":            "quote_client",
    "Discounted Quotation Sent":          "quote_client",
    "Revised Quotation Sent":             "quote_client",
    "Waiting for Final Approval":         "quote_client",
    "Won":                                "won",
    "Lost":                               "lost",
}

TIER_STYLE = {
    "red":           {"color": "#D92D20", "bg": "#FCEBEB", "label": "Action needed"},
    "design_prog":   {"color": "#B54708", "bg": "#FAEEDA", "label": "Design in progress"},
    "quote_prog":    {"color": "#C2410C", "bg": "#FAECE7", "label": "Quotation in progress"},
    "design_client": {"color": "#3B6D11", "bg": "#EAF3DE", "label": "Design with client"},
    "quote_client":  {"color": "#185FA5", "bg": "#E6F1FB", "label": "Quotation with client"},
    "won":           {"color": "#3B6D11", "bg": "#EAF3DE", "label": "Won"},
    "lost":          {"color": "#6B7280", "bg": "#F1EFE8", "label": "Lost"},
}

STAGE_COLORS = {
    "Hot Lead (Apollo)": "🔴",
    "Hot Lead (Deepak)": "🔴",
    "Hot Lead (Inbound)": "🔴",
    "Info Request Replied": "🔴",
    "Brief Received (v1)": "🟢",
    "Brief Received (v2)": "🟢",
    "Brief Received (v3)": "🟢",
    "Brief Sent to Designer": "🟢",
    "Design Option 1 Sent": "🟢",
    "Design Option 2 Sent": "🟢",
    "Design Option 3 Sent": "🟢",
    "Additional Changes Requested": "🟡",
    "New Brief Received (Client Changed)": "🟡",
    "Revised Brief Sent to Designer": "🟢",
    "Waiting for Design Feedback": "🟡",
    "Brief Sent to Vendor": "🟠",
    "Vendor Quotation Received": "🟠",
    "Client Quotation Prepared": "🟠",
    "Client Quotation 1 Sent": "🟠",
    "Client Requested Discount": "🟡",
    "Discounted Quotation Sent": "🟠",
    "Revised Quotation Sent": "🟠",
    "Waiting for Final Approval": "🟡",
    "Won": "✅",
    "Lost": "❌",
    "No Response — Follow Up Later": "⏸️",
}

EXHIBITIONS = [
    "ADIPEC",
    "WoodShow",
    "GISEC",
    "GITEX",
    "ATM",
    "INDEX",
    "Beautyworld",
    "Other",
]

SOURCES = [
    "Apollo",
    "Deepak",
    "Bhavika",
    "Telecalling",
    "Organic / Inbound",
    "Client Reached Out",
    "Referral",
    "Other (specify)",
]
USERS = ["Rahul", "Bhavika", "Deepak"]

# Email addresses for notifications (not secret)
USER_EMAILS = {
    "Rahul":   "marketing@atkexhibitions.com",
    "Bhavika": "bhavika@atkexhibitions.com",
    "Deepak":  "deepak@atkexhibitions.com",
}

PIPELINE_HEADERS = [
    "Company Name", "Exhibition", "Stand Size", "Source", "Contact Email", "Contact Name",
    "Contact Phone", "Current Stage", "Brief Version", "Design Options Sent",
    "Vendor Quote (AED)", "Margin (AED)", "Client Quote (AED)",
    "Discount Given", "Notes", "Added By", "Last Updated By", "Date Added",
]

HISTORY_HEADERS = ["Company Name", "Stage", "Updated By", "Date/Time", "Notes"]

EXHIBITOR_HEADERS = [
    "Event Name", "Event Date", "Company Name", "Stand Number", "Hall / Pavilion",
    "Country", "Website", "Email", "Phone", "Contact Name",
    "Call Status", "Called By", "Call Notes",
    "Uploaded By", "Upload Date",
]

CALL_STATUSES = [
    "Not Called",
    "Called — Interested",
    "Called — Not Interested",
    "No Answer",
    "Call Back",
    "WhatsApp Sent",
    "Do Not Contact",
]

TASK_HEADERS = [
    "Task ID", "Title", "Assigned To", "Priority", "Status",
    "Due Date", "Due Time", "Notes", "Source", "Source Company",
    "Created By", "Created Date", "Reminder Sent",
    "Completed By", "Completed Date",
]

FOLLOWUP_HEADERS = [
    "Follow-up ID", "Company Name", "Exhibition", "Stage at Time",
    "Follow-up Date", "Follow-up Time", "Assigned To", "Notes", "Status",
    "Created By", "Created Date", "Reminder Sent",
]

TASK_PRIORITIES = ["High", "Medium", "Low"]
TASK_STATUSES   = ["Pending", "In Progress", "Done"]

# ── Design brief (sent to the in-house designer) ─────────────────────────────
DESIGNER_EMAIL = "imraankhan3ddesigner@gmail.com"
BRIEF_CC       = ["marketing@atkexhibitions.com", "bhavika@atkexhibitions.com"]
BRIEF_REPLY_TO = "marketing@atkexhibitions.com"
LAYOUTS        = ["All sides open", "3 sides open", "2 sides open", "1 side open"]
MEETING_ROOMS  = ["None", "Open", "Semi-open", "Closed"]
BRIEF_FEATURES = [
    "Reception counter", "Storage room", "Pantry", "Coffee counter",
    "Product display podium", "Glass showcase",
]
BRIEF_HEADERS = [
    "Brief ID", "Company Name", "Exhibition", "Stand Size", "Location", "Layout",
    "Design Direction", "Brand Colours", "Meeting Room", "Features", "AV / Digital",
    "Products", "Notes", "First Concept Deadline", "Attachments", "Sent To",
    "Sent By", "Sent Date",
]

CALENDAR_HEADERS = [
    "Event Name", "Venue", "City", "Start Date", "End Date",
    "Exhibitor Count", "Official URL", "Verification Status",
    "Last Verified", "Date Priority", "Exhibitor Priority", "Notes",
]
