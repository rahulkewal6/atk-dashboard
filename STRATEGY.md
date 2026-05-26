# Cold Email Outreach — Strategy Tracker

_Last updated: 2026-05-26_

---

## The Defined Process — 7 Stages

```
STAGE 0: EVENT CALENDAR + PRIORITY SCORING
Input:  Venue URLs (DWTC, ADNEC, Sharjah, Saudi, India)
Action: Claude scrapes + verifies events against official websites
Output: Verified event list + official homepage URLs + Last Verified Date
        + Priority Score per event (see scoring below)
Human:  Review and approve calendar, flag priority events
Rules:
  - Refresh every 30 days
  - Re-verify any event within 30 days of its start date
  - If event postponed → hold all downstream stages until new date confirmed

PRIORITY SCORING (scrape in this order):
  Factor 1 — Date proximity:
    Within 3 months  → High priority
    3-6 months away  → Medium priority
    6+ months away   → Low priority
  Factor 2 — Exhibitor count:
    500+ exhibitors  → High priority
    200-499          → Medium priority
    Under 200        → Low priority
  Rule: Highest combined score gets scraped first
```
```
STAGE 1: EXHIBITOR LIST URL DISCOVERY
Input:  Event homepage URL (from Stage 0)
Action: Claude navigates homepage → finds exhibitor list page URL
Output: Direct exhibitor list URL
Human:  None
```
```
STAGE 2: EXHIBITOR SCRAPING
Input:  Exhibitor list URL (from Stage 1)
Action: Claude finds hidden API or scrapes DOM
Output: Raw data — Name, Country, Hall, Stand No., Website, Email
        Flags which fields are missing per row
Human:  None
Tool:   Claude in Chrome (Website Scrapping project)
```
```
STAGE 3: DATA ENRICHMENT
Input:  Raw scraped data
Logic:
  Has email?               → skip enrichment
  Has website, no email?   → Apollo enrichment (low credit cost)
  Has name only?           → Claude batch web search (Gemini as backup)
                           → get website URL → then Apollo enrichment
  Phone?                   → scrape company contact page (no Apollo credits)
Output: Enriched list — Name, Country, Website, Email, Phone
Human:  None
```
```
STAGE 4: LIST SPLIT + DATA QUALITY FILTER
Input:  Enriched list
Step 1 — Split list:
  Portion A → Deepak (manual outreach from his Zoho account)
  Portion B → Apollo sequences
  Rule: No company appears in both portions — zero overlap
Step 2 — Filter each portion:
  Remove: gmail, yahoo, hotmail, qq.com and similar personal domains
  Remove: contacts flagged Unsubscribed or Not Interested in Apollo
  Keep:   everything else including pavilion coordinators
  Note:   Apollo native dedup handles any remaining duplicates on upload
Output: Two clean lists — one for Deepak, one for Apollo upload
Human:  One Excel filter + split — 5 minutes
```
```
STAGE 5: APOLLO UPLOAD + SEQUENCES
Input:  Apollo portion of clean leads list
Action: Upload to Apollo → assign to event-specific sequence
        Each mailbox sends one event's sequence:
        expo@      → Event sequence 1
        marketing@ → Event sequence 2
        accounts@  → Event sequence 3
        info@      → Event sequence 4
        sales@     → Event sequence 5
Sequence structure (3 emails):
  Email 1 (Day 1):  Intro + complimentary design offer + portfolio link
  Email 2 (Day 4):  Different angle or social proof
  Email 3 (Day 10): Short close — easy yes/no ask + calendar booking link
Personalisation:
  Apollo-sourced data    → Hi {{first_name}},
  Exhibitor-scraped data → Hi {{company}} team,
Human:  Approve before sequences go live
```
```
STAGE 6: RESPONSE CAPTURE + TRIAGE
Input:  All replies across all 5 mailboxes
Action: Apollo unified inbox — one view, all replies
Tag replies as:
  Hot          → Positive interest, wants to proceed
  Info Request → Asking questions, needs more detail
  Negative     → Not interested / unsubscribe
Human:  Review unified inbox once daily
Parallel: Deepak forwards interested replies manually to Rahul + Bhavika
```
```
STAGE 7: ACTION + PIPELINE
Hot lead     → Send calendar booking link same day (within 4 hours)
Info request → Templated reply within 24 hours
Negative     → Remove from sequence immediately
Human:  Rahul + Bhavika handle all live conversations and design briefs
        Pipeline tracked in Streamlit dashboard
```

---

## Contact Re-Outreach Rules

| Contact Status | Action | Handled By |
|---|---|---|
| Unsubscribed | Never contact again | Apollo automatic suppression |
| Clicked Not Interested | Never contact again | Tag in Apollo, exclude from all future lists |
| No response after full sequence | Re-eligible after 6 months | Apollo suppression by date |
| Replied but did not convert | Re-eligible after 3-4 months, different angle | Rahul / Bhavika to decide |
| Active in pipeline | Remove from all sequences immediately | Rahul / Bhavika |

---

## Feedback Loop — Monthly Review

After each event sequence completes:
1. Pull Apollo analytics: open rate, reply rate, bounce rate, hot lead rate
2. Log one row per event in the feedback tracker:

| Event | Emails Sent | Open Rate | Reply Rate | Hot Leads | Deals Closed |
|---|---|---|---|---|---|

3. Use findings to:
   - Prioritise similar events in future calendar
   - Improve underperforming email templates
   - Drop event types that consistently produce no results

**Time required: 20 minutes per month**

---

## Dashboard Design — Streamlit

**Platform:** Streamlit + Google Sheets (backend database)
**Users:** Rahul + Bhavika (both can read and update)
**Pages:** 4 tabs

### Page 1 — Pipeline
Main daily view. All active leads with current stage and last update.
Clicking a lead opens the full lead detail card.

### Page 2 — Sequences
Daily health check per active exhibition sequence.
Shows: emails sent, open rate, reply rate, status per mailbox.

### Page 3 — Reports
Monthly performance summary.
Shows: hot leads, deals closed, best-performing events.

### Page 4 — Calendar
Upcoming events with priority scores.
Flags any event not re-verified in last 30 days.

---

## Pipeline Stages — Full List

These are all available options in the stage dropdown.
Any stage can be set at any time — the pipeline is not locked to linear order.
Every stage change is logged with date + who updated it.

**Outreach Stages**
- Hot Lead (reply received — Apollo or Deepak)
- Info Request Replied

**Brief Stages** ← can repeat if client changes brief
- Brief Received from Client (v1 / v2 / v3)
- Brief Sent to Designer

**Design Stages** ← can repeat per revision round
- Design Option 1 Sent to Client
- Design Option 2 Sent to Client
- Design Option 3 Sent to Client
- Additional Changes Requested by Client
- New Brief Received from Client (brief changed mid-process)
- Revised Brief Sent to Designer
- Waiting for Design Feedback

**Quotation Stages**
- Brief Sent to Vendor (for pricing)
- Vendor Quotation Received           ← internal, not shared with client
- Client Quotation Prepared           ← vendor price + margin added
- Client Quotation 1 Sent
- Client Requested Discount
- Discounted Quotation Sent
- Revised Quotation Sent (scope change)
- Waiting for Final Approval

**Closed**
- Won
- Lost
- No Response — follow up later

---

## Lead Detail Fields (per lead in Google Sheet)

| Field | Type | Notes |
|---|---|---|
| Company Name | Text | |
| Exhibition | Dropdown | Which event they came from |
| Source | Dropdown | Apollo / Deepak |
| Contact Email | Text | |
| Current Stage | Dropdown | Full stage list above |
| Brief Version | Number | 1 / 2 / 3 |
| Design Options Sent | Number | 1 / 2 / 3 |
| Vendor Quote (AED) | Number | Internal only |
| Margin (AED) | Number | Internal only |
| Client Quote (AED) | Number | Shown to client |
| Discount Given | Yes / No | |
| Notes | Text | Free field |
| Last Updated By | Text | Rahul / Bhavika |
| Date Added | Date | Auto |
| Stage History | Auto-log | Date + stage + who updated |

---

## Human Touchpoints — Summary

| Stage | Human Action | Frequency |
|---|---|---|
| 0 | Review and approve event calendar + priority scores | Every 30 days |
| 4 | Split list + remove invalid emails | Per event scrape |
| 5 | Approve before sequences go live | Per event |
| 6 | Check Apollo unified inbox + Deepak forwards | Once daily |
| 7 | Handle live conversations + update pipeline stages | As needed |
| — | Monthly feedback loop review | Monthly |

---

## Known Risks — To Monitor

| Risk | Status |
|---|---|
| Mailbox setup incomplete (60-40%) | Fix: complete setup to 100% immediately |
| expo@ and accounts@ warmup off | Fix: switch warmup on immediately |
| Sequences paused last 2 months (war/market) | Fix: restart immediately |
| Deepak's outreach coordination | Managed: list split at Stage 4, manual forwarding kept |
| Event date changes (Middle East uncertainty) | Managed: 30-day re-verify + pre-scrape checkpoint |

---

## Tools in Use

| Tool | Purpose |
|---|---|
| Claude in Chrome | Exhibitor list scraping |
| Gemini | Company name → website URL lookup (free, Google-powered) |
| Apollo (paid) | Email enrichment, sequences, unified inbox, suppression |
| Zoho Mail | Hosting for all 5 mailboxes + Deepak's account |
| Excel | Intermediate data format between scraping and Apollo |
| Streamlit | Dashboard — pipeline, sequences, reports, calendar |
| Google Sheets | Backend database for pipeline leads and stage history |

---

## Mailboxes (all on Zoho, all connected to Apollo)
- expo@atkexhibitions.com
- marketing@atkexhibitions.com
- accounts@atkexhibitions.com
- info@atkexhibitions.com
- sales@atkexhibitions.com (Default)

---

## Current Exhibitions Being Targeted
ADIPEC, ATM, INDEX, WoodShow

---

## Open Items

- [ ] Complete all mailbox setups to 100% in Apollo
- [ ] Switch warmup back on for expo@ and accounts@
- [ ] Restart Apollo sequences (paused due to market uncertainty)
- [ ] Set up Apollo unified inbox
- [ ] Define which industries/sectors are priority targets
- [ ] Write/review email templates for each active event sequence
- [ ] Build feedback loop tracker (feeds into dashboard)
- [ ] Deepak's coordination — revisit when dashboard is built
- [ ] Set up Google Sheet as pipeline database
- [ ] Build Streamlit dashboard
