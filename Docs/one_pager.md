<!-- The customer-facing one-pager. Designed/branded version: AdvisorBrief_OnePager.pdf
     (kept alongside this file). This markdown mirrors that content. -->

**Northwind Securities** · Advisor Enablement · Prototype
`PROTOTYPE ONE-PAGER · CONFIDENTIAL`

# AdvisorBrief

Get up to speed on a stock in minutes — a time-stamped quote and the key points from
recent SEC filings, every fact linked to its source.

**Client** Northwind Securities (US wealth management) · **User** advisor (firm
employee) · **Coverage** ticker-agnostic market data across top market-cap names
(NYSE & beyond); MSFT shown · **Sources** market-data quote + SEC filings
(10-K / 10-Q / 8-K)

---

### Outcome
Advisors get up to speed on a stock fast — a current, clearly-dated quote plus a
plain-English summary of what matters in recent SEC filings — so client conversations
start informed, consistent, and inside the firm's compliance lines.

### How one query works
- **Capture** — the question and the advisor's identity are logged.
- **Retrieve** — current quote, plus relevant passages from recent 10-K / 10-Q / 8-K filings.
- **Synthesize** — a brief grounded only in those sources, every fact linked to its source.
- **Evaluation gate** — claims cited, language fair and balanced, disclosures present,
  confidence above threshold.
- **Human-in-the-loop** — flagged or low-confidence briefs escalate to a supervising
  principal before client use.
- **Audit** — every briefing kept as a tamper-evident, exportable record.

### 🖥️ What the advisor sees
A delivered MSFT briefing. The quote is a dated, clearly-labeled end-of-day value
(informational, not an execution price); "How this was checked" and the audit reference
expose the gate and tamper-evident trail. MSFT is the ticker-agnostic market-data
example; the worked filing example uses a separate issuer.

### 🗺️ Roadmap
- **Now** — prototype: governed quote-plus-filings briefing with gate, escalation, and
  audit trail.
- **Next** — manager view: a dashboard showing which advisors log in and how much
  material they review — a signal of learning and readiness.
- **Later** — coverage: full multi-exchange universe, earnings / 8-K alerts, and CRM hooks.

---

⚖ *Prototype built on a synthetic golden dataset and the firm's encoded policy
rule-set; figures shown are illustrative. Informational only — not investment advice or
a recommendation. Suitability and required disclosures apply at the point of client
use, subject to the firm's own compliance and legal review.*
