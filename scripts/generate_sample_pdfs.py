"""Generate sample PDF fixtures for testing all LegalLens AI scenarios.

Documents produced
------------------
tests/fixtures/
  employment_contract.pdf        — multi-page employment contract (simplify, risks, checklist, Q&A)
  employment_contract_v2.pdf     — amended version for document comparison (compare)
  nda_confidentiality.pdf        — NDA / confidentiality agreement (risks: high-severity clauses)
  residential_lease.pdf          — residential lease (checklist focus)
  saas_terms_of_service.pdf      — SaaS ToS (auto-renewal, liability cap, data clauses)
  image_only.pdf                 — blank-page PDF (triggers ScannedPDFError)
  single_clause.pdf              — tiny one-sentence PDF (minimal valid text)
  unicode_contract.pdf           — contract with non-ASCII characters (encoding robustness)

Run:
    python scripts/generate_sample_pdfs.py
"""

from __future__ import annotations

import io
import os
from pathlib import Path

import pypdf
from fpdf import FPDF

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------

OUT_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Characters that cannot be encoded with latin-1 core fonts; replace with ASCII equivalents.
_CHAR_MAP = str.maketrans({
    "\u2014": "--",   # em dash
    "\u2013": "-",    # en dash
    "\u2018": "'",    # left single quote
    "\u2019": "'",    # right single quote
    "\u201c": '"',    # left double quote
    "\u201d": '"',    # right double quote
    "\u2022": "*",    # bullet
    "\u2026": "...",  # ellipsis
    "\u00e9": "e",    # e-acute (used in unicode doc handled separately)
    "\u00fc": "u",    # u-umlaut (used in unicode doc handled separately)
})


def _latin1_safe(text: str) -> str:
    """Replace non-latin-1 characters so Helvetica core fonts do not crash."""
    return text.translate(_CHAR_MAP)


def _make_pdf(pages: list[dict[str, str | list[str]]]) -> FPDF:
    """Return an FPDF object with one page per entry in *pages*.

    Each dict may have:
      - "title"   : str       -- printed as bold heading
      - "body"    : str       -- main paragraph text (multi_cell, auto-wrapped)
      - "items"   : list[str] -- bullet lines
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    for page in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", style="B", size=14)
        if title := page.get("title"):
            pdf.multi_cell(0, 8, _latin1_safe(str(title)))
            pdf.ln(4)
        pdf.set_font("Helvetica", size=11)
        if body := page.get("body"):
            pdf.multi_cell(0, 6, _latin1_safe(str(body)))
            pdf.ln(3)
        if items := page.get("items"):
            for item in items:
                pdf.multi_cell(0, 6, _latin1_safe(f"  *  {item}"))
    return pdf


def _save(pdf: FPDF, name: str) -> Path:
    dest = OUT_DIR / name
    pdf.output(str(dest))
    print(f"  Written: {dest}")
    return dest


# ---------------------------------------------------------------------------
# 1. Employment Contract  (v1 — baseline for simplify / risks / checklist / Q&A)
# ---------------------------------------------------------------------------

EMPLOYMENT_V1_PAGES = [
    {
        "title": "EMPLOYMENT AGREEMENT",
        "body": (
            "This Employment Agreement ('Agreement') is entered into as of January 1, 2025 "
            "('Effective Date') by and between Acme Corporation, a Delaware corporation "
            "('Employer'), and Jane Doe ('Employee').\n\n"
            "RECITALS\n"
            "WHEREAS, Employer desires to employ Employee, and Employee desires to accept "
            "such employment, on the terms and conditions set forth herein."
        ),
    },
    {
        "title": "1. Position and Duties",
        "body": (
            "1.1 Position. Employee shall serve as Senior Software Engineer. Employee shall "
            "report to the Chief Technology Officer.\n\n"
            "1.2 Duties. Employee shall perform all duties customarily associated with the "
            "position and such other duties as may be assigned from time to time. Employee "
            "shall devote full business time and effort exclusively to Employer's business."
        ),
    },
    {
        "title": "2. Compensation and Benefits",
        "body": (
            "2.1 Base Salary. Employer shall pay Employee a base salary of $120,000 per "
            "year, payable in bi-weekly installments of $4,615.38, subject to applicable "
            "tax withholdings.\n\n"
            "2.2 Bonus. Employee is eligible for an annual performance bonus of up to 15% "
            "of base salary, determined at Employer's sole discretion.\n\n"
            "2.3 Benefits. Employee shall be entitled to participate in health, dental, "
            "and vision insurance plans maintained by Employer for its employees. Employer "
            "shall contribute $500 per month toward Employee's health insurance premium.\n\n"
            "2.4 Equity. Employee shall receive stock options for 10,000 shares vesting "
            "over four years with a one-year cliff."
        ),
    },
    {
        "title": "3. Term and Termination",
        "body": (
            "3.1 Term. This Agreement commences on the Effective Date and continues until "
            "terminated in accordance with this Section 3.\n\n"
            "3.2 Termination Without Cause. Employer may terminate this Agreement at any "
            "time without cause upon thirty (30) days prior written notice to Employee. "
            "In such event, Employer shall pay Employee a severance equal to three (3) "
            "months of base salary.\n\n"
            "3.3 Termination for Cause. Employer may terminate this Agreement immediately "
            "for Cause. 'Cause' means: (a) material breach of this Agreement; (b) gross "
            "negligence or willful misconduct; (c) conviction of a felony; or (d) repeated "
            "failure to perform duties after written warning.\n\n"
            "3.4 Resignation. Employee may resign upon thirty (30) days written notice. "
            "No severance is owed upon resignation."
        ),
    },
    {
        "title": "4. Confidentiality and Intellectual Property",
        "body": (
            "4.1 Confidential Information. Employee shall not, during or after employment, "
            "disclose any Confidential Information to any third party without prior written "
            "consent of Employer. 'Confidential Information' includes trade secrets, customer "
            "lists, source code, financial data, and business strategies.\n\n"
            "4.2 Work Product. All work product, inventions, and improvements created by "
            "Employee in the scope of employment shall be the exclusive property of Employer. "
            "Employee hereby irrevocably assigns all such rights to Employer.\n\n"
            "4.3 Survival. Obligations under Section 4 survive termination of this Agreement "
            "for a period of five (5) years."
        ),
    },
    {
        "title": "5. Non-Compete and Non-Solicitation",
        "body": (
            "5.1 Non-Compete. For a period of twelve (12) months following termination, "
            "Employee shall not, directly or indirectly, engage in any business that competes "
            "with Employer within a fifty (50) mile radius of any Employer office.\n\n"
            "5.2 Non-Solicitation. For a period of twenty-four (24) months following "
            "termination, Employee shall not solicit or hire any current or former employee "
            "of Employer, nor solicit any customer of Employer.\n\n"
            "5.3 Remedies. Employee acknowledges that breach of this Section will cause "
            "irreparable harm and that Employer shall be entitled to injunctive relief in "
            "addition to all other remedies at law or equity."
        ),
    },
    {
        "title": "6. Dispute Resolution and Governing Law",
        "body": (
            "6.1 Arbitration. Any dispute arising from this Agreement shall be resolved by "
            "binding arbitration administered by the American Arbitration Association under "
            "its Commercial Arbitration Rules. The arbitration shall take place in "
            "San Francisco, California. The arbitrator's decision shall be final and "
            "enforceable in any court of competent jurisdiction.\n\n"
            "6.2 Class Action Waiver. Employee waives any right to participate in any "
            "class action or collective proceeding against Employer.\n\n"
            "6.3 Governing Law. This Agreement shall be governed by the laws of the "
            "State of California, without regard to conflict of law principles."
        ),
    },
    {
        "title": "7. General Provisions",
        "body": (
            "7.1 Entire Agreement. This Agreement constitutes the entire agreement between "
            "the parties and supersedes all prior negotiations, representations, and "
            "agreements relating to the subject matter hereof.\n\n"
            "7.2 Amendment. This Agreement may not be modified except by a written "
            "instrument signed by both parties.\n\n"
            "7.3 Severability. If any provision of this Agreement is held unenforceable, "
            "the remaining provisions shall continue in full force and effect.\n\n"
            "IN WITNESS WHEREOF, the parties have executed this Agreement as of the date "
            "first written above.\n\n"
            "Acme Corporation: ________________________  Date: __________\n"
            "Employee (Jane Doe): _____________________ Date: __________"
        ),
    },
]


# ---------------------------------------------------------------------------
# 2. Employment Contract v2  (amended — for comparison testing)
# ---------------------------------------------------------------------------

EMPLOYMENT_V2_PAGES = [
    {
        "title": "EMPLOYMENT AGREEMENT (AMENDED)",
        "body": (
            "This Amended Employment Agreement ('Agreement') is entered into as of "
            "March 1, 2025 ('Effective Date') by and between Acme Corporation, a "
            "Delaware corporation ('Employer'), and Jane Doe ('Employee').\n\n"
            "This Agreement replaces and supersedes the Employment Agreement dated "
            "January 1, 2025 in its entirety."
        ),
    },
    {
        "title": "1. Position and Duties",
        "body": (
            "1.1 Position. Employee shall serve as Staff Software Engineer (promoted "
            "from Senior Software Engineer). Employee shall report to the VP of Engineering.\n\n"
            "1.2 Duties. Employee shall perform all duties customarily associated with "
            "the position and such other duties as may be assigned from time to time."
        ),
    },
    {
        "title": "2. Compensation and Benefits",
        "body": (
            "2.1 Base Salary. Employer shall pay Employee a base salary of $155,000 per "
            "year, payable in bi-weekly installments, subject to applicable tax withholdings.\n\n"
            "2.2 Bonus. Employee is eligible for an annual performance bonus of up to 20% "
            "of base salary, determined by the annual review process.\n\n"
            "2.3 Benefits. Employee shall be entitled to participate in health, dental, "
            "vision, and life insurance plans. Employer shall contribute $750 per month "
            "toward Employee's health insurance premium.\n\n"
            "2.4 Equity. Employee shall receive an additional grant of 5,000 RSUs "
            "vesting quarterly over two years. Previously granted options remain in effect."
        ),
    },
    {
        "title": "3. Term and Termination",
        "body": (
            "3.1 Term. This Agreement commences on the Effective Date and continues until "
            "terminated in accordance with this Section 3.\n\n"
            "3.2 Termination Without Cause. Employer may terminate this Agreement at any "
            "time without cause upon sixty (60) days prior written notice to Employee. "
            "In such event, Employer shall pay Employee a severance equal to six (6) "
            "months of base salary.\n\n"
            "3.3 Termination for Cause. Employer may terminate immediately for Cause as "
            "defined in Section 3.3 of the prior agreement.\n\n"
            "3.4 Resignation. Employee may resign upon thirty (30) days written notice."
        ),
    },
    {
        "title": "4-7. Unchanged Provisions",
        "body": (
            "Sections 4 (Confidentiality and IP), 5 (Non-Compete and Non-Solicitation), "
            "6 (Dispute Resolution), and 7 (General Provisions) remain unchanged from "
            "the January 1, 2025 Employment Agreement, which is incorporated herein by "
            "reference.\n\n"
            "IN WITNESS WHEREOF, the parties have executed this Amended Agreement.\n\n"
            "Acme Corporation: ________________________  Date: __________\n"
            "Employee (Jane Doe): _____________________ Date: __________"
        ),
    },
]


# ---------------------------------------------------------------------------
# 3. NDA / Confidentiality Agreement  (high-severity risk clauses)
# ---------------------------------------------------------------------------

NDA_PAGES = [
    {
        "title": "MUTUAL NON-DISCLOSURE AGREEMENT",
        "body": (
            "This Mutual Non-Disclosure Agreement ('Agreement') is entered into as of "
            "February 15, 2025 between TechVentures Inc. ('Company') and Beta Corp. ('Recipient'). "
            "Each party may disclose Confidential Information to the other in connection with "
            "a potential business collaboration ('Purpose')."
        ),
    },
    {
        "title": "1. Definition of Confidential Information",
        "body": (
            "1.1 'Confidential Information' means any non-public information disclosed by "
            "either party, whether orally, in writing, or by any other means, that is "
            "designated as confidential or that reasonably should be understood to be "
            "confidential given the nature of the information and circumstances of disclosure. "
            "This includes but is not limited to: technical data, trade secrets, know-how, "
            "research, product plans, services, customers, markets, software, developments, "
            "inventions, processes, formulas, technology, designs, drawings, engineering, "
            "hardware configuration information, marketing, finances, or other business information.\n\n"
            "1.2 Confidential Information does NOT include information that: (a) is or becomes "
            "publicly known through no fault of the Recipient; (b) was rightfully known to the "
            "Recipient prior to disclosure; (c) is independently developed by Recipient without "
            "use of Confidential Information; or (d) is required to be disclosed by law or court order."
        ),
    },
    {
        "title": "2. Obligations",
        "body": (
            "2.1 Non-Disclosure. Each party shall: (a) hold Confidential Information in strict "
            "confidence; (b) not disclose Confidential Information to any third party without "
            "prior written consent; (c) use Confidential Information solely for the Purpose; and "
            "(d) limit access to Confidential Information to employees who have a need to know and "
            "are bound by confidentiality obligations no less protective than this Agreement.\n\n"
            "2.2 No License. Nothing in this Agreement grants either party any right or license "
            "to any intellectual property of the other party."
        ),
    },
    {
        "title": "3. Term and Survival — HIGH RISK CLAUSES",
        "body": (
            "3.1 Term. This Agreement shall remain in effect for a period of three (3) years "
            "from the Effective Date.\n\n"
            "3.2 Survival. Notwithstanding Section 3.1, obligations with respect to trade secrets "
            "shall survive indefinitely. All other confidentiality obligations survive for five (5) "
            "years after termination.\n\n"
            "3.3 Return of Information. Upon written request or termination, each party shall "
            "promptly destroy or return all Confidential Information and certify destruction in "
            "writing within ten (10) business days."
        ),
    },
    {
        "title": "4. Remedies and Liability",
        "body": (
            "4.1 Injunctive Relief. Each party acknowledges that breach of this Agreement may "
            "cause irreparable harm for which monetary damages would be an inadequate remedy. "
            "Accordingly, the non-breaching party shall be entitled to seek injunctive and other "
            "equitable relief without posting any bond.\n\n"
            "4.2 Liquidated Damages. In the event of unauthorized disclosure, the breaching party "
            "shall pay liquidated damages of $500,000 per incident. The parties agree this amount "
            "represents a reasonable estimate of damages.\n\n"
            "4.3 Indemnification. Each party shall indemnify, defend, and hold harmless the other "
            "from any claims, losses, costs, and expenses (including attorneys' fees) arising from "
            "a breach of this Agreement by the indemnifying party or its representatives."
        ),
    },
    {
        "title": "5. General Provisions",
        "body": (
            "5.1 Governing Law. This Agreement is governed by the laws of the State of New York.\n\n"
            "5.2 Entire Agreement. This Agreement constitutes the entire agreement between the parties "
            "concerning confidentiality and supersedes all prior agreements on the subject.\n\n"
            "5.3 Amendment. This Agreement may only be amended by a written instrument signed by "
            "authorized representatives of both parties.\n\n"
            "Signed on behalf of TechVentures Inc.: __________________ Date: __________\n"
            "Signed on behalf of Beta Corp.: _________________________ Date: __________"
        ),
    },
]


# ---------------------------------------------------------------------------
# 4. Residential Lease Agreement  (checklist focus)
# ---------------------------------------------------------------------------

LEASE_PAGES = [
    {
        "title": "RESIDENTIAL LEASE AGREEMENT",
        "body": (
            "This Residential Lease Agreement ('Lease') is made as of April 1, 2025 "
            "between Green Estates LLC ('Landlord') and Alex Smith ('Tenant') for the "
            "property located at 42 Maple Street, Apt 3B, Springfield, IL 62701 ('Premises')."
        ),
    },
    {
        "title": "1. Lease Term and Rent",
        "body": (
            "1.1 Term. The lease term begins on April 1, 2025 and ends on March 31, 2026 "
            "('Initial Term'). After the Initial Term, this Lease shall convert to a month-to-month "
            "tenancy unless either party provides sixty (60) days written notice of non-renewal.\n\n"
            "1.2 Rent. Tenant shall pay $1,850 per month, due on the first (1st) day of each month. "
            "Rent is payable by check or electronic transfer to Landlord's designated account.\n\n"
            "1.3 Late Fee. A late fee of $75 shall be assessed if rent is not received by the "
            "fifth (5th) of the month. If rent remains unpaid after the tenth (10th), an additional "
            "$10 per day shall accrue until paid."
        ),
    },
    {
        "title": "2. Security Deposit",
        "body": (
            "2.1 Amount. Tenant shall deposit $3,700 (equal to two months' rent) as a security "
            "deposit upon execution of this Lease.\n\n"
            "2.2 Conditions for Return. The security deposit shall be returned within thirty (30) "
            "days of move-out, less any deductions for unpaid rent, damages beyond normal wear and "
            "tear, or cleaning costs.\n\n"
            "2.3 Itemization. Any deductions shall be itemized and provided in writing to Tenant "
            "within thirty (30) days of Tenant vacating the Premises."
        ),
    },
    {
        "title": "3. Utilities and Maintenance",
        "body": (
            "3.1 Tenant Utilities. Tenant is responsible for electricity, internet, and renters "
            "insurance (minimum $100,000 liability coverage required). Landlord pays water, sewer, "
            "and trash collection.\n\n"
            "3.2 Maintenance. Tenant shall maintain the Premises in clean condition and promptly "
            "report any damage or needed repairs. Tenant is responsible for minor repairs under $75.\n\n"
            "3.3 Alterations. Tenant shall not make any alterations, additions, or improvements "
            "without prior written consent of Landlord."
        ),
    },
    {
        "title": "4. Prohibited Uses and Rules",
        "body": (
            "4.1 Occupants. Only the named Tenant and approved occupants may reside on the Premises. "
            "Guests may not stay more than fourteen (14) consecutive days without written approval.\n\n"
            "4.2 Pets. No pets are permitted without a separate Pet Addendum and an additional "
            "pet deposit of $500 per pet (non-refundable).\n\n"
            "4.3 Smoking. Smoking of any kind is strictly prohibited on the Premises and within "
            "25 feet of any building entrance.\n\n"
            "4.4 Noise. Tenant shall comply with all local noise ordinances. Quiet hours are "
            "10:00 PM to 8:00 AM."
        ),
    },
    {
        "title": "5. Termination and Default",
        "body": (
            "5.1 Termination by Tenant. Tenant may terminate early with sixty (60) days written "
            "notice AND payment of an early termination fee equal to two (2) months' rent.\n\n"
            "5.2 Default. If Tenant fails to pay rent or breaches any term, Landlord may issue a "
            "three (3) day notice to cure or quit. Continued default shall entitle Landlord to "
            "initiate eviction proceedings.\n\n"
            "5.3 Holdover. If Tenant remains after expiration without a new agreement, Tenant "
            "shall be deemed a holdover tenant and rent shall increase by 25% on a month-to-month basis."
        ),
    },
    {
        "title": "6. Entry and Inspection",
        "body": (
            "6.1 Right of Entry. Landlord may enter the Premises with twenty-four (24) hours "
            "advance written notice for inspection, repairs, or showing to prospective tenants "
            "or buyers.\n\n"
            "6.2 Emergency Entry. In case of emergency, Landlord may enter without prior notice.\n\n"
            "IN WITNESS WHEREOF, the parties have executed this Lease as of the date first written.\n\n"
            "Landlord (Green Estates LLC): _______________ Date: __________\n"
            "Tenant (Alex Smith): _____________________ Date: __________"
        ),
    },
]


# ---------------------------------------------------------------------------
# 5. SaaS Terms of Service  (auto-renewal, liability cap, data processing)
# ---------------------------------------------------------------------------

SAAS_PAGES = [
    {
        "title": "SAAS SUBSCRIPTION AGREEMENT AND TERMS OF SERVICE",
        "body": (
            "These Terms of Service ('Agreement') govern access to and use of the CloudSync "
            "platform ('Service') provided by CloudSync Technologies, Inc. ('Provider'). "
            "By clicking 'Agree' or accessing the Service, Customer ('Customer') accepts "
            "these terms in their entirety as of the date of acceptance ('Effective Date')."
        ),
    },
    {
        "title": "1. Subscription and Fees",
        "body": (
            "1.1 Subscription Plan. Customer subscribes to the Business Plan at $499 per "
            "month for up to 50 users. Additional users are $12/user/month.\n\n"
            "1.2 Auto-Renewal. UNLESS CUSTOMER PROVIDES WRITTEN CANCELLATION NOTICE AT LEAST "
            "THIRTY (30) DAYS BEFORE THE END OF THE THEN-CURRENT SUBSCRIPTION PERIOD, THIS "
            "AGREEMENT WILL AUTOMATICALLY RENEW FOR SUCCESSIVE ONE-YEAR TERMS AT THE THEN-CURRENT "
            "LIST PRICE, WHICH MAY INCREASE BY UP TO 10% ANNUALLY WITHOUT FURTHER NOTICE.\n\n"
            "1.3 Payment. All fees are due net-30 from invoice date. Overdue amounts accrue "
            "interest at 1.5% per month. Provider reserves the right to suspend access for "
            "accounts more than 15 days past due.\n\n"
            "1.4 No Refunds. All fees are non-refundable except as expressly set forth herein."
        ),
    },
    {
        "title": "2. Data and Privacy",
        "body": (
            "2.1 Customer Data. Customer retains all rights to data uploaded to the Service "
            "('Customer Data'). Provider may access Customer Data solely to provide the Service.\n\n"
            "2.2 Data Processing. Provider shall process Customer Data in accordance with its "
            "Privacy Policy and applicable data protection laws. For EU/UK customers, the "
            "Data Processing Addendum ('DPA') incorporated by reference governs GDPR compliance.\n\n"
            "2.3 Data Retention. Upon termination, Provider will retain Customer Data for sixty "
            "(60) days, after which it will be permanently deleted. Customer is responsible for "
            "exporting data prior to termination.\n\n"
            "2.4 Subprocessors. Provider may engage subprocessors listed at provider.com/subprocessors "
            "and shall notify Customer thirty (30) days before adding new subprocessors."
        ),
    },
    {
        "title": "3. Intellectual Property and Acceptable Use",
        "body": (
            "3.1 License. Provider grants Customer a non-exclusive, non-transferable license to "
            "access and use the Service during the subscription term solely for Customer's "
            "internal business purposes.\n\n"
            "3.2 Restrictions. Customer shall not: (a) sublicense or resell access; (b) reverse "
            "engineer the Service; (c) use the Service to store or transmit malicious code; "
            "(d) interfere with or disrupt the Service's integrity; or (e) use the Service "
            "to develop a competing product.\n\n"
            "3.3 Feedback. Any feedback Customer provides may be used by Provider without "
            "restriction or compensation to Customer."
        ),
    },
    {
        "title": "4. Warranties and Disclaimers",
        "body": (
            "4.1 Limited Warranty. Provider warrants that the Service will perform materially "
            "in accordance with the Documentation under normal use. Customer's sole remedy for "
            "breach of this warranty is re-performance or a pro-rata refund for the affected period.\n\n"
            "4.2 DISCLAIMER. EXCEPT AS SET FORTH IN SECTION 4.1, THE SERVICE IS PROVIDED 'AS IS' "
            "WITHOUT WARRANTIES OF ANY KIND, WHETHER EXPRESS, IMPLIED, STATUTORY, OR OTHERWISE. "
            "PROVIDER DISCLAIMS ALL IMPLIED WARRANTIES, INCLUDING MERCHANTABILITY, FITNESS FOR "
            "A PARTICULAR PURPOSE, AND NON-INFRINGEMENT."
        ),
    },
    {
        "title": "5. Limitation of Liability — HIGH RISK",
        "body": (
            "5.1 EXCLUSION OF CONSEQUENTIAL DAMAGES. IN NO EVENT SHALL EITHER PARTY BE LIABLE "
            "FOR ANY INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, CONSEQUENTIAL, OR PUNITIVE DAMAGES, "
            "INCLUDING LOSS OF PROFITS, DATA, BUSINESS, OR GOODWILL, EVEN IF ADVISED OF THE "
            "POSSIBILITY OF SUCH DAMAGES.\n\n"
            "5.2 LIABILITY CAP. PROVIDER'S TOTAL CUMULATIVE LIABILITY ARISING OUT OF OR RELATED "
            "TO THIS AGREEMENT SHALL NOT EXCEED THE TOTAL FEES PAID BY CUSTOMER IN THE TWELVE (12) "
            "MONTHS IMMEDIATELY PRECEDING THE CLAIM. CUSTOMER ACKNOWLEDGES THIS LIMIT IS A "
            "FUNDAMENTAL ELEMENT OF THE BASIS OF THE BARGAIN BETWEEN THE PARTIES."
        ),
    },
    {
        "title": "6. Termination",
        "body": (
            "6.1 Termination for Convenience. Either party may terminate this Agreement for any "
            "reason upon sixty (60) days written notice; provided, Customer shall remain liable "
            "for all fees through the end of the current subscription period.\n\n"
            "6.2 Termination for Cause. Either party may terminate immediately upon written notice "
            "if the other party materially breaches this Agreement and fails to cure within "
            "thirty (30) days of notice.\n\n"
            "6.3 Effect of Termination. Upon termination, all licenses granted herein shall "
            "immediately terminate. Sections 1.4, 2.3, 3.3, 4.2, 5, 6.3, and 7 survive termination."
        ),
    },
    {
        "title": "7. General",
        "body": (
            "7.1 Governing Law. This Agreement is governed by the laws of the State of Delaware.\n\n"
            "7.2 Entire Agreement. This Agreement (including the DPA and any Order Forms) "
            "constitutes the entire agreement and supersedes all prior understandings.\n\n"
            "7.3 Changes to Terms. Provider may modify these Terms upon thirty (30) days written "
            "notice. Continued use of the Service after the effective date constitutes acceptance.\n\n"
            "Customer: __________________________________ Date: __________\n"
            "CloudSync Technologies, Inc.: ______________ Date: __________"
        ),
    },
]


# ---------------------------------------------------------------------------
# 6. Single-clause PDF  (minimal valid text — boundary condition)
# ---------------------------------------------------------------------------

SINGLE_CLAUSE_PAGES = [
    {
        "title": "SIMPLE PAYMENT CLAUSE",
        "body": (
            "The Buyer shall pay the Seller the sum of $10,000 within fifteen (15) days "
            "of receipt of the invoice. Payment shall be made by wire transfer to the "
            "account specified by Seller in writing."
        ),
    },
]


# ---------------------------------------------------------------------------
# 7. Unicode / international contract  (encoding robustness)
# ---------------------------------------------------------------------------

UNICODE_PAGES = [
    {
        "title": "INTERNATIONAL SERVICE AGREEMENT",
        "body": (
            "This Agreement is made between Entreprise Dupont SARL ('Prestataire') and "
            "Muller GmbH ('Client') effective 1 January 2025.\n\n"
            "1. Services. Prestataire shall provide software development services as "
            "described in Annex A. The parties may communicate in English or French.\n\n"
            "2. Remuneration. Client shall pay EUR 15,000 per month. Invoices are payable "
            "within 30 days. Delayed payments incur interest at the ECB rate plus 8%.\n\n"
            "3. Confidentiality. Both parties shall keep all business information strictly "
            "confidential for 5 years after termination of this Agreement.\n\n"
            "4. Jurisdiction. Any disputes shall be resolved before the competent courts "
            "of Paris, France, applying French law.\n\n"
            "Fait en double exemplaire. / Executed in duplicate.\n\n"
            "Prestataire: _____________________ Date: __________\n"
            "Client: _________________________ Date: __________"
        ),
    },
]


# ---------------------------------------------------------------------------
# 8. Image-only / blank PDF  (triggers ScannedPDFError)
# ---------------------------------------------------------------------------

def _make_image_only_pdf(num_pages: int = 3) -> bytes:
    """Build a valid PDF with blank pages — no text content."""
    writer = pypdf.PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Generating sample PDFs in: {OUT_DIR}\n")

    _save(_make_pdf(EMPLOYMENT_V1_PAGES), "employment_contract.pdf")
    _save(_make_pdf(EMPLOYMENT_V2_PAGES), "employment_contract_v2.pdf")
    _save(_make_pdf(NDA_PAGES), "nda_confidentiality.pdf")
    _save(_make_pdf(LEASE_PAGES), "residential_lease.pdf")
    _save(_make_pdf(SAAS_PAGES), "saas_terms_of_service.pdf")
    _save(_make_pdf(SINGLE_CLAUSE_PAGES), "single_clause.pdf")
    _save(_make_pdf(UNICODE_PAGES), "unicode_contract.pdf")

    # Blank-page PDF (no fpdf — use pypdf directly)
    blank_path = OUT_DIR / "image_only.pdf"
    blank_path.write_bytes(_make_image_only_pdf(num_pages=3))
    print(f"  Written: {blank_path}")

    print(f"\nDone. {len(list(OUT_DIR.glob('*.pdf')))} PDF(s) in {OUT_DIR}")


if __name__ == "__main__":
    main()
