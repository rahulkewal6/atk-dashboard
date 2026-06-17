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
    "red":           {"color": "#FF4D4F", "bg": "rgba(255,77,79,0.14)",   "label": "Action needed"},
    "design_prog":   {"color": "#FFB020", "bg": "rgba(255,176,32,0.14)",  "label": "Design in progress"},
    "quote_prog":    {"color": "#FF8C42", "bg": "rgba(255,140,66,0.14)",  "label": "Quotation in progress"},
    "design_client": {"color": "#2ECC71", "bg": "rgba(46,204,113,0.14)",  "label": "Design with client"},
    "quote_client":  {"color": "#38BDF8", "bg": "rgba(56,189,248,0.14)",  "label": "Quotation with client"},
    "won":           {"color": "#2ECC71", "bg": "rgba(46,204,113,0.18)",  "label": "Won"},
    "lost":          {"color": "#8B8B8B", "bg": "rgba(139,139,139,0.14)", "label": "Lost"},
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
    "Company Name", "Exhibition", "Source", "Contact Email", "Contact Name",
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
]

FOLLOWUP_HEADERS = [
    "Follow-up ID", "Company Name", "Exhibition", "Stage at Time",
    "Follow-up Date", "Follow-up Time", "Assigned To", "Notes", "Status",
    "Created By", "Created Date", "Reminder Sent",
]

TASK_PRIORITIES = ["High", "Medium", "Low"]
TASK_STATUSES   = ["Pending", "In Progress", "Done"]

CALENDAR_HEADERS = [
    "Event Name", "Venue", "City", "Start Date", "End Date",
    "Exhibitor Count", "Official URL", "Verification Status",
    "Last Verified", "Date Priority", "Exhibitor Priority", "Notes",
]
