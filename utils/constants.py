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

CALENDAR_HEADERS = [
    "Event Name", "Venue", "City", "Start Date", "End Date",
    "Exhibitor Count", "Official URL", "Verification Status",
    "Last Verified", "Date Priority", "Exhibitor Priority", "Notes",
]
