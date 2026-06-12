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

# Three-tier status system for the Leads UI
# red    = action needed from our side (pending on us)
# yellow = work in progress (design/quotation being prepared, waiting on vendor)
# green  = sent to client (design or quotation with the client)
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
    "Brief Sent to Designer":             "yellow",
    "Revised Brief Sent to Designer":     "yellow",
    "Brief Sent to Vendor":               "yellow",
    "Vendor Quotation Received":          "yellow",
    "Client Quotation Prepared":          "yellow",
    "Design Option 1 Sent":               "green",
    "Design Option 2 Sent":               "green",
    "Design Option 3 Sent":               "green",
    "Waiting for Design Feedback":        "green",
    "Client Quotation 1 Sent":            "green",
    "Discounted Quotation Sent":          "green",
    "Revised Quotation Sent":             "green",
    "Waiting for Final Approval":         "green",
    "Won":                                "won",
    "Lost":                               "lost",
}

TIER_STYLE = {
    "red":    {"color": "#FF4D4F", "bg": "rgba(255,77,79,0.14)",  "label": "Action needed"},
    "yellow": {"color": "#FFB020", "bg": "rgba(255,176,32,0.14)", "label": "In progress"},
    "green":  {"color": "#2ECC71", "bg": "rgba(46,204,113,0.14)", "label": "With client"},
    "won":    {"color": "#2ECC71", "bg": "rgba(46,204,113,0.18)", "label": "Won"},
    "lost":   {"color": "#8B8B8B", "bg": "rgba(139,139,139,0.14)","label": "Lost"},
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
USERS = ["Rahul", "Bhavika"]

PIPELINE_HEADERS = [
    "Company Name", "Exhibition", "Source", "Contact Email", "Contact Name",
    "Contact Phone", "Current Stage", "Brief Version", "Design Options Sent",
    "Vendor Quote (AED)", "Margin (AED)", "Client Quote (AED)",
    "Discount Given", "Notes", "Last Updated By", "Date Added",
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
    "Due Date", "Notes", "Source", "Source Company", "Created By", "Created Date",
]

FOLLOWUP_HEADERS = [
    "Follow-up ID", "Company Name", "Exhibition", "Stage at Time",
    "Follow-up Date", "Assigned To", "Notes", "Status", "Created By", "Created Date",
]

TASK_PRIORITIES = ["High", "Medium", "Low"]
TASK_STATUSES   = ["Pending", "In Progress", "Done"]

CALENDAR_HEADERS = [
    "Event Name", "Venue", "City", "Start Date", "End Date",
    "Exhibitor Count", "Official URL", "Verification Status",
    "Last Verified", "Date Priority", "Exhibitor Priority", "Notes",
]
