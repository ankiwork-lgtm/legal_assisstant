/**
 * generate-sample-pdfs.js
 *
 * Generates five sample legal PDF documents for testing LexAid features.
 * Uses only Node.js built-ins — no external dependencies required.
 *
 * Output: public/sample-docs/
 *   1. nda-confidentiality-agreement.pdf       (Simplify / Q&A / Prep)
 *   2. employment-contract-v1.pdf              (Compare – version A)
 *   3. employment-contract-v2.pdf              (Compare – version B)
 *   4. residential-lease-agreement.pdf         (Simplify / Q&A / Prep)
 *   5. software-saas-terms-of-service.pdf      (Simplify / Q&A)
 *
 * Run: node scripts/generate-sample-pdfs.js
 */

const fs   = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Minimal PDF builder (no external deps)
// ---------------------------------------------------------------------------

function buildPdf(title, pages) {
  // Each page is an array of text lines.
  // Font: Helvetica (standard PDF font, no embedding needed)

  const objects = [];
  let oid = 1;

  const obj = (content) => {
    const id = oid++;
    objects.push({ id, content });
    return id;
  };

  // Catalog + Pages placeholder (filled in later)
  const catalogId  = oid++;
  const pagesId    = oid++;

  const pageIds = [];

  for (const lines of pages) {
    const pageId    = oid++;
    const contentId = oid++;

    // Build page content stream
    let stream = 'BT\n/F1 11 Tf\n12 TL\n72 750 Td\n';
    for (const line of lines) {
      // Escape special PDF string chars
      const safe = line
        .replace(/\\/g, '\\\\')
        .replace(/\(/g, '\\(')
        .replace(/\)/g, '\\)');
      stream += `(${safe}) '\n`;
    }
    stream += 'ET\n';

    objects.push({
      id: contentId,
      content: `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`,
    });

    objects.push({
      id: pageId,
      content:
        `<< /Type /Page\n` +
        `   /Parent ${pagesId} 0 R\n` +
        `   /MediaBox [0 0 612 792]\n` +
        `   /Contents ${contentId} 0 R\n` +
        `   /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >>\n` +
        `>>`,
    });

    pageIds.push(pageId);
  }

  // Now write catalog and pages
  objects.push({
    id: catalogId,
    content: `<< /Type /Catalog /Pages ${pagesId} 0 R >>`,
  });

  objects.push({
    id: pagesId,
    content:
      `<< /Type /Pages\n` +
      `   /Kids [${pageIds.map((id) => `${id} 0 R`).join(' ')}]\n` +
      `   /Count ${pageIds.length}\n` +
      `>>`,
  });

  // Sort by id
  objects.sort((a, b) => a.id - b.id);

  // Serialise
  let body = '%PDF-1.4\n';
  const offsets = {};

  for (const o of objects) {
    offsets[o.id] = body.length;
    body += `${o.id} 0 obj\n${o.content}\nendobj\n`;
  }

  const xrefOffset = body.length;
  const count = objects.length + 1; // +1 for free entry

  let xref = `xref\n0 ${count}\n0000000000 65535 f \n`;
  for (const o of objects) {
    xref += String(offsets[o.id]).padStart(10, '0') + ' 00000 n \n';
  }

  body += xref;
  body +=
    `trailer\n<< /Size ${count} /Root ${catalogId} 0 R >>\n` +
    `startxref\n${xrefOffset}\n%%EOF\n`;

  return Buffer.from(body, 'latin1');
}

// ---------------------------------------------------------------------------
// Document content definitions
// ---------------------------------------------------------------------------

const documents = [
  {
    filename: 'nda-confidentiality-agreement.pdf',
    pages: [
      [
        'NON-DISCLOSURE AND CONFIDENTIALITY AGREEMENT',
        '',
        'This Non-Disclosure Agreement ("Agreement") is entered into as of January 15, 2024',
        'by and between Acme Technologies Inc., a Delaware corporation ("Disclosing Party")',
        'and John Smith, an individual residing at 42 Elm Street, Chicago, IL 60601',
        '("Receiving Party").',
        '',
        '1. DEFINITION OF CONFIDENTIAL INFORMATION',
        '',
        '"Confidential Information" means any non-public information that Disclosing Party',
        'designates as being confidential or which, under the circumstances surrounding',
        'disclosure, the Receiving Party knows or has reason to know is confidential,',
        'including but not limited to: source code, algorithms, business plans,',
        'financial projections, customer lists, trade secrets, and technical specifications.',
        '',
        '2. OBLIGATIONS OF RECEIVING PARTY',
        '',
        'The Receiving Party agrees to: (a) hold all Confidential Information in strict',
        'confidence; (b) not disclose such information to any third party without prior',
        'written consent; (c) use the Confidential Information solely for the purpose of',
        'evaluating a potential business relationship; (d) restrict access to those',
        'employees who have a need to know and who are bound by similar confidentiality',
        'obligations.',
        '',
        '3. TERM AND TERMINATION',
        '',
        'This Agreement shall remain in effect for a period of three (3) years from the',
        'date first written above. Upon termination or expiration, the Receiving Party',
        'shall promptly return or destroy all Confidential Information.',
      ],
      [
        'NDA — Page 2',
        '',
        '4. EXCLUSIONS FROM CONFIDENTIAL INFORMATION',
        '',
        'The obligations of this Agreement do not apply to information that:',
        '(a) is or becomes publicly known through no wrongful act of the Receiving Party;',
        '(b) was rightfully known to the Receiving Party prior to disclosure;',
        '(c) is independently developed by the Receiving Party without use of the',
        '    Confidential Information; or',
        '(d) is required to be disclosed by law or court order, provided that the',
        '    Receiving Party gives Disclosing Party prompt written notice.',
        '',
        '5. REMEDIES',
        '',
        'The Receiving Party acknowledges that any breach of this Agreement may cause',
        'irreparable harm for which monetary damages would be an inadequate remedy.',
        'Accordingly, the Disclosing Party shall be entitled to seek equitable relief,',
        'including injunction and specific performance, in addition to all other remedies',
        'available at law or in equity.',
        '',
        '6. GOVERNING LAW',
        '',
        'This Agreement shall be governed by and construed in accordance with the laws of',
        'the State of Delaware, without regard to its conflict of law provisions.',
        '',
        '7. ENTIRE AGREEMENT',
        '',
        'This Agreement constitutes the entire agreement between the parties with respect',
        'to its subject matter and supersedes all prior negotiations, representations, or',
        'agreements, whether oral or written.',
        '',
        'IN WITNESS WHEREOF, the parties have executed this Agreement as of the date above.',
        '',
        'Acme Technologies Inc.                  John Smith',
        'By: _______________________             Signature: ___________________',
        'Name: Sarah Johnson, CEO                Date: _______________________',
      ],
    ],
  },

  {
    filename: 'employment-contract-v1.pdf',
    pages: [
      [
        'EMPLOYMENT AGREEMENT — VERSION 1.0',
        '',
        'This Employment Agreement ("Agreement") is made effective March 1, 2024,',
        'between BrightPath Solutions LLC ("Employer") and Maria Gonzalez ("Employee").',
        '',
        '1. POSITION AND DUTIES',
        'Employee is hired as Senior Software Engineer. Employee shall report to the',
        'VP of Engineering and perform duties as reasonably assigned.',
        '',
        '2. COMPENSATION',
        'Base Salary: USD $110,000 per year, paid bi-weekly.',
        'Annual Bonus: Up to 10% of base salary, at Employer discretion.',
        'Equity: 0.05% stock options vesting over 4 years with a 1-year cliff.',
        '',
        '3. BENEFITS',
        'Health Insurance: Employer pays 80% of premium for Employee and dependants.',
        'Paid Time Off: 15 days per calendar year.',
        'Remote Work: Up to 2 days per week from home.',
        '',
        '4. TERM AND TERMINATION',
        'Employment is at-will. Either party may terminate with 2 weeks written notice.',
        'Employer may terminate immediately for cause.',
        '',
        '5. INTELLECTUAL PROPERTY',
        'All work product created by Employee during employment belongs exclusively',
        'to Employer, including inventions, software, and written materials.',
        '',
        '6. NON-COMPETE',
        'Employee agrees not to work for a direct competitor for 6 months after',
        'termination within a 50-mile radius of Chicago, IL.',
        '',
        '7. GOVERNING LAW',
        'This Agreement is governed by the laws of Illinois.',
        '',
        'Signatures:',
        'Employer: _______________________   Employee: _______________________',
      ],
    ],
  },

  {
    filename: 'employment-contract-v2.pdf',
    pages: [
      [
        'EMPLOYMENT AGREEMENT — VERSION 2.0 (REVISED)',
        '',
        'This Employment Agreement ("Agreement") is made effective March 1, 2024,',
        'between BrightPath Solutions LLC ("Employer") and Maria Gonzalez ("Employee").',
        '',
        '1. POSITION AND DUTIES',
        'Employee is hired as Lead Software Engineer. Employee shall report to the',
        'CTO and perform duties as reasonably assigned.',
        '',
        '2. COMPENSATION',
        'Base Salary: USD $125,000 per year, paid bi-weekly.',
        'Annual Bonus: Up to 15% of base salary, subject to performance review.',
        'Equity: 0.10% stock options vesting over 4 years with a 1-year cliff.',
        '',
        '3. BENEFITS',
        'Health Insurance: Employer pays 100% of premium for Employee; 80% for dependants.',
        'Paid Time Off: 20 days per calendar year, plus 5 sick days.',
        'Remote Work: Fully remote with quarterly in-office visits required.',
        '',
        '4. TERM AND TERMINATION',
        'Employment is at-will. Either party may terminate with 4 weeks written notice.',
        'Employer may terminate immediately for cause.',
        'Severance: 1 month salary if terminated without cause after 1 year.',
        '',
        '5. INTELLECTUAL PROPERTY',
        'All work product created by Employee during employment belongs exclusively',
        'to Employer, including inventions, software, and written materials.',
        'Employee retains rights to pre-existing personal projects listed in Exhibit A.',
        '',
        '6. NON-COMPETE',
        'REMOVED — this clause has been deleted from the revised agreement.',
        '',
        '7. DISPUTE RESOLUTION',
        'Any dispute shall be resolved by binding arbitration under AAA Commercial Rules.',
        '',
        '8. GOVERNING LAW',
        'This Agreement is governed by the laws of Illinois.',
        '',
        'Signatures:',
        'Employer: _______________________   Employee: _______________________',
      ],
    ],
  },

  {
    filename: 'residential-lease-agreement.pdf',
    pages: [
      [
        'RESIDENTIAL LEASE AGREEMENT',
        '',
        'This Lease Agreement is entered into on February 1, 2024 between',
        'Oak Park Properties LLC ("Landlord") and David and Lisa Chen ("Tenants").',
        '',
        '1. PREMISES',
        'Landlord leases to Tenants the residential property located at',
        '1847 Maple Avenue, Apt 3B, Evanston, IL 60201 ("Premises").',
        '',
        '2. TERM',
        'The lease term begins February 1, 2024 and ends January 31, 2025 (12 months).',
        'After expiry, tenancy converts to month-to-month with 60 days written notice',
        'required to terminate.',
        '',
        '3. RENT',
        'Monthly Rent: $1,950 due on the 1st of each month.',
        'Late Fee: $75 if rent is received after the 5th day of the month.',
        'Returned Check Fee: $35 per occurrence.',
        '',
        '4. SECURITY DEPOSIT',
        'Security Deposit: $2,925 (1.5 months rent), due at signing.',
        'Returned within 30 days of move-out, less documented deductions.',
        'Deductions permitted for: unpaid rent, damage beyond normal wear and tear.',
        '',
        '5. UTILITIES',
        'Tenants pay: electricity, internet, renter\'s insurance (min $100k liability).',
        'Landlord pays: water, trash, gas for heating, building maintenance.',
        '',
        '6. PETS',
        'Pets are permitted with a one-time non-refundable pet fee of $300 per pet.',
        'Maximum 2 pets. No animals over 50 lbs. No restricted breeds.',
      ],
      [
        'RESIDENTIAL LEASE — Page 2',
        '',
        '7. MAINTENANCE AND REPAIRS',
        'Tenants shall keep the Premises in clean condition and promptly notify',
        'Landlord of any damage or needed repairs. Tenants are responsible for',
        'minor repairs under $75. Landlord must respond to urgent repairs within',
        '24 hours and non-urgent repairs within 14 days.',
        '',
        '8. ENTRY BY LANDLORD',
        'Landlord shall provide at least 48 hours notice before entering the Premises',
        'except in cases of emergency.',
        '',
        '9. SUBLETTING',
        'Tenants may not sublet or assign the Premises without prior written consent',
        'from Landlord, which shall not be unreasonably withheld.',
        '',
        '10. ALTERATIONS',
        'No alterations, painting, or modifications to the Premises without written',
        'Landlord approval. Approved alterations become Landlord property unless',
        'Landlord directs removal at move-out.',
        '',
        '11. TERMINATION FOR CAUSE',
        'Landlord may terminate with 5-day notice for non-payment of rent.',
        'Landlord may terminate with 30-day notice for material lease violations.',
        '',
        '12. MOVE-OUT PROCEDURE',
        'Tenants must provide 60 days written notice. A move-out inspection will be',
        'scheduled within 3 days of vacating. All keys and access cards must be returned.',
        '',
        '13. GOVERNING LAW',
        'This Lease is governed by the Residential Landlord and Tenant Act of Illinois.',
        '',
        'Landlord: _____________________   Tenants: _______________________',
        'Date: _________________________   Date: __________________________',
      ],
    ],
  },

  {
    filename: 'saas-terms-of-service.pdf',
    pages: [
      [
        'SOFTWARE-AS-A-SERVICE TERMS OF SERVICE',
        '',
        'Last Updated: January 1, 2024',
        'Provider: DataVault Corp., 200 Tech Plaza, San Francisco, CA 94107',
        '',
        '1. ACCEPTANCE OF TERMS',
        'By accessing or using the DataVault platform ("Service"), you ("Customer")',
        'agree to be bound by these Terms of Service. If you are accepting on behalf',
        'of a company, you represent that you have authority to bind that entity.',
        '',
        '2. SUBSCRIPTION AND FEES',
        'Customer agrees to pay the subscription fees set out in the applicable Order',
        'Form. Fees are billed monthly in advance. Unpaid invoices accrue interest at',
        '1.5% per month. Provider may suspend Service after 15 days of non-payment.',
        '',
        '3. DATA OWNERSHIP AND PRIVACY',
        'Customer retains full ownership of all data uploaded to the Service.',
        'Provider processes Customer data only as directed and in accordance with',
        'the Data Processing Agreement (DPA) attached as Exhibit B.',
        'Provider shall not sell or share Customer data with third parties.',
        '',
        '4. INTELLECTUAL PROPERTY',
        'Provider retains all rights, title, and interest in the Service, including',
        'all software, interfaces, and documentation. Customer is granted a limited,',
        'non-exclusive, non-transferable licence to use the Service during the term.',
        '',
        '5. SERVICE LEVEL AGREEMENT (SLA)',
        'Provider guarantees 99.5% monthly uptime for the Service.',
        'Downtime credits: 10% bill credit for each 0.5% below the SLA guarantee.',
        'Scheduled maintenance windows (max 4 hours/month) excluded from SLA.',
      ],
      [
        'SaaS Terms of Service — Page 2',
        '',
        '6. LIMITATION OF LIABILITY',
        'IN NO EVENT SHALL PROVIDER BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL,',
        'OR CONSEQUENTIAL DAMAGES, INCLUDING LOSS OF PROFITS OR DATA.',
        'PROVIDER\'S TOTAL LIABILITY SHALL NOT EXCEED THE FEES PAID BY CUSTOMER',
        'IN THE TWELVE MONTHS PRECEDING THE CLAIM.',
        '',
        '7. INDEMNIFICATION',
        'Customer shall indemnify and hold Provider harmless from any claims arising',
        'from: (a) Customer\'s use of the Service in violation of these Terms;',
        '(b) Customer\'s data infringing third-party intellectual property rights.',
        '',
        '8. TERM AND TERMINATION',
        'The initial term is 12 months. Either party may terminate with 30 days notice',
        'at the end of any term. Provider may terminate immediately if Customer',
        'materially breaches these Terms and fails to cure within 10 days of notice.',
        '',
        '9. DATA RETURN AND DELETION',
        'Upon termination, Provider will make Customer data available for export',
        'for 30 days. After that period, Provider will securely delete all Customer data.',
        '',
        '10. DISPUTE RESOLUTION',
        'Disputes shall be resolved by binding arbitration in San Francisco, CA under',
        'JAMS rules. Class action waiver applies — disputes must be brought individually.',
        '',
        '11. GOVERNING LAW',
        'These Terms are governed by the laws of California.',
        '',
        '12. MODIFICATIONS',
        'Provider may update these Terms with 30 days notice. Continued use of the',
        'Service after notice constitutes acceptance of the updated Terms.',
      ],
    ],
  },
];

// ---------------------------------------------------------------------------
// Write files
// ---------------------------------------------------------------------------

const outDir = path.join(__dirname, '..', 'public', 'sample-docs');
fs.mkdirSync(outDir, { recursive: true });

for (const doc of documents) {
  const pdf  = buildPdf(doc.filename, doc.pages);
  const dest = path.join(outDir, doc.filename);
  fs.writeFileSync(dest, pdf);
  console.log(`✓  ${doc.filename}  (${(pdf.length / 1024).toFixed(1)} KB)`);
}

console.log(`\nAll sample PDFs written to: ${outDir}`);
