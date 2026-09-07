# Legitimate Interests Assessment

**INTERNAL DOCUMENT — DRAFT FOR REVIEW**
Article 6(1)(f) UK GDPR / EU GDPR
Controller: F-Keys Creative LLC · Service: Epistemend
Version 2026-09-07 · Author: Vince Gonzalez

---

This document exists because Article 6(1)(f) is a *balancing test*, not a
label. An undocumented legitimate interest is an assertion. This is the
record that the balance was actually struck, and on what reasoning, at a
date before processing began at scale.

Review annually, or on any material change to what a report contains.

---

## 1. Purpose test — is there a legitimate interest?

**The processing:** reading public scholarly indexes for what they record
about a named researcher's published work, and reporting where those
records disagree with each other.

**The interest:** the accuracy and integrity of the public scholarly
record.

**Who benefits:**

- The subject, who usually cannot see that an index has lost their
  attribution, mis-linked a DOI, or that something they cited has been
  retracted since.
- The customer, who may be the subject, a librarian, an editor, a
  historian, or someone conducting diligence.
- The wider scholarly record, which is degraded by undetected divergence
  between indexes.

**Is the interest lawful, clearly articulated, and real rather than
speculative?** Yes. Record reconciliation is an established scholarly
activity; ORCID, Crossref and OpenAlex exist to be queried for exactly
this purpose and publish APIs to enable it.

**Would there be a real consequence if we could not process?** Yes — the
service could not exist. There is no version of this product that does not
read what indexes record about named people.

---

## 2. Necessity test — is processing necessary for that interest?

**Could the purpose be achieved without personal data?** No. The question
being answered is inherently about an identified person's record.

**Could it be achieved with less?** We have taken the reductions available:

- No standing database of researchers is kept. Sources are read at run
  time and discarded.
- The submitted list or identifier is destroyed the moment the report is
  produced.
- The only persistent artefact is the report itself, held for the customer
  who bought it, and erasable on request.
- We do not enrich from private sources, social media, or any non-scholarly
  index.
- We do not infer. Nothing is scored, ranked, or characterized; the report
  states what each index says and attributes it.

**Conclusion:** necessary, and already minimized.

---

## 3. Balancing test — do the individual's interests override?

### 3.1 Nature of the data

Professional and already published. Publication list, identifiers, venues,
citation counts, deposits, retraction notices. Published by the subject or
their publisher, in a professional capacity, into indexes that exist to be
searched.

No special category data is sought under Article 9. No criminal offence
data under Article 10. **Note:** a retraction notice is not an offence
record and must never be presented as one.

### 3.2 Reasonable expectations

A researcher who obtains an ORCID and deposits work has published into a
system designed for third-party retrieval. That someone would read those
indexes and compare them is within reasonable expectation.

**Where expectation is weaker, and we acknowledge it:** the subject
expects each index to be readable, but may not expect the *comparison
across indexes* to be sold as a product, nor to be monitored on a
recurring schedule at a third party's instance. This is the genuine
pressure point in the balance, and the mitigations at 3.4 address it
directly.

### 3.3 Likely impact

**Low in the ordinary case.** The report repeats public facts, attributed,
to a single purchaser. It is not published, indexed, or broadcast.

**Where the impact could be higher, and how it is constrained:**

| Risk | Mitigation |
|---|---|
| Report used in a hiring, tenure or credit decision | Expressly prohibited in the required pre-order attestation, in terms tracking the statutory purposes. Not a consumer report; we are not a consumer reporting agency. |
| "Retracted" read as an imputation of misconduct | Findings state what the index records and the stated grounds. The product must never characterize a retraction as misconduct. **This is an architectural invariant, not a style preference.** |
| An index is wrong, and the report repeats it | The report asserts what the index records, not what is true of the person, and names the index so it can be checked and corrected at source. Rectification requests are answered with the index and the route to correct it. |
| A report is forwarded beyond its purchaser | Reachable only by a 128-bit token. The customer is told plainly that anyone holding the address can read it. |
| Indefinite retention | Discarded list; erasable report; monitoring snapshot deleted when the subscription ends or an objection is received. |

### 3.4 Safeguards

- **Article 21 objection honoured without reason given**, with a
  persistent suppression list so an objection does not lapse.
- **This assessment and the privacy notice are published**, which is both
  a safeguard and the precondition of the Article 14(5)(b) exemption.
- **Data minimization applied and verified**, not merely intended: the
  submitted list is destroyed on delivery; the event log records that an
  email was sent rather than the address; a diagnostic table holding no
  useful purpose was dropped.
- **No profiling, no automated decision-making** within Article 22. The
  report produces no decision, score or recommendation; the reader draws
  the conclusion.
- **No secondary use.** Data is not sold, shared, used for advertising, or
  used to train any model.

---

## 4. Conclusion

The interest is legitimate and real. The processing is necessary to it and
has been minimized as far as the purpose allows. The data is professional
and already public; the impact in the ordinary case is low; and the two
places where impact could be material — use in employment-type decisions,
and the implication carried by the word "retracted" — are addressed by a
binding pre-order restriction and by an architectural rule about how
findings are phrased.

**Article 6(1)(f) is available and is relied upon.**

The balance would change, and this assessment must be redone, if any of
the following occurs:

- a standing database of subjects is retained rather than read at run time;
- any non-scholarly or private source is added;
- the product begins to score, rank, or characterize rather than report;
- reports become public rather than delivered to a single purchaser;
- the use restriction is removed or ceases to be enforced.

---

*Prepared as a working document. It is not legal advice and has not been
reviewed by counsel.*
