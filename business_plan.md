# Navarre EV Taxi Co. — Business Plan

**Entity:** Navarre EV Taxi LLC (S-Corp election)
**Location:** Navarre / Gulf Breeze, FL
**Primary Routes:** Home pickup → Hurlburt Field / Eglin AFB

---

## Executive Summary

A 2–3 person LLC purchases a single electric vehicle (Tesla Model Y) to provide
subscription-based morning/evening commuter taxi service for military personnel
stationed at Hurlburt Field and Eglin Air Force Base. Owners have residential
solar panels, making charging costs near zero. The business is initially
owner-operated; autonomous vehicle technology and evolving Florida law create a
path to driverless operation in Phase 2.

---

## Market

| Factor | Detail |
|---|---|
| Target customers | Active-duty military, Navarre / Gulf Breeze zip codes |
| Primary routes | Navarre → Hurlburt Field (~16 mi), Navarre → Eglin AFB (~22 mi) |
| Pain points for riders | Commute costs, parking scarcity on base, DUI risk |
| Service window | ~0600–0800 (inbound) and ~1600–1800 (outbound) |
| Capacity | 2–4 passengers per trip |
| Competition | Personal vehicles; no organized military commuter van service in area |

Military personnel are reliable, punctual, and often prefer not to drive if an
affordable alternative exists. A monthly subscription creates predictable revenue
and rider commitment.

---

## Service Model

### Phase 1 — Owner-Operated (Year 1–2)

- One owner drives each morning and evening shift (~2 hrs/day total).
- Driving rotates among owners by schedule; each logs hours for material
  participation proof (IRS §469).
- Passengers subscribe monthly ($275/seat) or book ad hoc ($18/seat one-way).
- Vehicle charges overnight at an owner's home via solar panels.

### Phase 2 — Autonomous Vehicle (Year 3+, pending FL legislation)

- Tesla FSD capability subscription (~$99/mo) activates after sufficient
  route-learning trips (~50 identical runs establishes high-confidence mapping).
- Florida Statute §316.85 already permits AV operation without a human driver
  for vehicles meeting NHTSA SAE Level 4+ standards.
- Commercial-for-hire AV service requires an FDOT permit (process still maturing;
  target 2027–2028).
- Owner driving hours are freed; vehicle can operate while owners are at work.

---

## Capital Structure

| Item | Amount |
|---|---|
| Tesla Model Y RWD (MSRP) | $44,990 |
| IRC §45W Commercial EV Tax Credit | −$7,500 |
| **Net vehicle cost** | **$37,490** |
| LLC formation (attorney + FL filing) | $1,500 |
| **Total startup costs** | **$38,990** |

### Equity — Two-Owner Base Case

| Owner | Investment | Ownership % |
|---|---|---|
| Owner A | $20,000 | 50% |
| Owner B | $20,000 | 50% |
| **Total** | **$40,000** | **100%** |

- Remaining $1,010 held as operating reserve.
- Membership units issued 1:1 with dollars invested.
- **Three-owner variant:** $13,333 each = $40,000 total; units recalculated pro-rata.
- Operating Agreement locks the unit-to-investment ratio so latecomers
  are diluted correctly if a third investor joins later.

---

## Odometer & Usage Tracking

IRS §274(d) requires *contemporaneous* records for any business vehicle.
The Python model (`business_model.py`) includes a `MileageLog` class that records:

- Date
- Odometer start / end
- Destination
- Business purpose (e.g., "Military commute, Hurlburt Field drop-off, 2 passengers")
- Passenger count
- Business vs. personal flag

`MileageLog.export_json()` produces a JSON file suitable for CPA review and
IRS audit. Tesla's built-in trip history (GPS + kWh) serves as corroborating
evidence.

**Personal use by owners** is logged separately. Maintenance costs are split
between the LLC (business share) and individual owners (personal share) in
proportion to miles driven for each purpose.

---

## Charging & Solar

- 85% of charging estimated from owner solar panels (near-zero marginal cost).
- 15% from grid backup at ~$0.12/kWh (FL average).
- Business electricity cost ≈ $50–80/year on grid backup only.
- The LLC Operating Agreement should explicitly state that owners contribute
  solar power as a capital contribution valued at the avoided grid rate, OR that
  the company reimburses at the utility rate. This prevents the IRS from treating
  "free" charging as an undocumented taxable distribution.
- Tesla app exports kWh consumed per trip — retain monthly for records.

---

## Financial Projections (5-Year)

Run `python business_model.py` for full scenario output. Summary:

| Scenario | Year 1 EBIT | Year 3 EBIT | Cumulative (Yr 5) |
|---|---|---|---|
| Pessimistic (1.5 seats) | ~−$7,500 | ~−$4,000 | ~−$23,000 |
| Base Case (2.5 seats) | ~−$2,500 | ~$1,500 | ~−$7,000 |
| Optimistic (3.2 seats) | ~$1,000 | ~$5,000 | ~+$11,000 |

**Key assumptions:**
- Owner-operated (no external driver cost)
- Solar covers 85% of charging
- MACRS 5-year depreciation on business-use portion
- ~$375/mo commercial auto insurance

**Cash break-even** (excluding non-cash depreciation): approximately **1.5–2 seats** on
monthly subscriptions. Securing just 2 regular subscribers covers all cash costs.

---

## Amortization / Depreciation

The vehicle is depreciated using **MACRS 5-year** with the half-year convention.

Because this is a vehicle used for hire (taxi), it is **exempt from the IRC §280F
luxury-automobile dollar caps** — the full MACRS schedule applies to the
business-use percentage of the vehicle cost.

| Tax Year | MACRS Rate | Deduction (Base Case ~70% biz use) |
|---|---|---|
| 2025 | 20.00% | ~$5,249 |
| 2026 | 32.00% | ~$8,398 |
| 2027 | 19.20% | ~$5,039 |
| 2028 | 11.52% | ~$3,023 |
| 2029 | 11.52% | ~$3,023 |
| 2030 | 5.76% | ~$1,512 |

*Actual amounts depend on the finalized business-use % from mileage logs.*

---

## Maintenance Cost Allocation

Total maintenance (tires, brake fluid, cabin air filter) estimated at $0.03/mile.

- **Business miles** → LLC expense (deductible on Form 1065 / Schedule K-1)
- **Personal miles** → charged to the owner who drove them, pro-rata

Formula: `personal_cost_per_owner = total_cost × personal_pct × owner_personal_miles / all_personal_miles`

---

## IRS Red Flags & Mitigations

### 1. Hobby Loss Rule (IRC §183)
**Risk:** Losses disallowed if no profit motive.
**Safe harbor:** 3 profitable years out of any 5 consecutive years.
**Mitigations:**
- Written business plan (this document) on file from Day 1.
- Dedicated business bank account — no commingling.
- Contemporaneous mileage log.
- Adjust pricing or add routes if revenue falls short — document the decision.

### 2. Passive Activity Loss Rules (IRC §469)
**Risk:** Members who don't drive (passive investors) cannot deduct losses
against W-2 income; losses are suspended until the business is profitable or sold.
**Mitigation:** Owner-drivers must log > 500 hours/year of business activity
(driving + scheduling + bookkeeping) to qualify as material participants.

### 3. Listed Property Documentation (IRC §274(d))
**Risk:** IRS can disallow all vehicle deductions without adequate records.
**Mitigation:** `MileageLog` with daily entries; Tesla trip history as backup.

### 4. Charging at Personal Residences
**Risk:** Undocumented "free" electricity = disguised distribution.
**Mitigation:** Operating Agreement documents solar power as capital contribution
at avoided grid rate; Tesla kWh data retained monthly.

### 5. Reasonable Compensation (S-Corp)
**Risk:** IRS requires owner-employees to receive a reasonable salary before
distributions once the business is profitable.
**Mitigation:** In loss years, $0 salary is defensible. Once profitable, set salary
at BLS median for FL taxi drivers (~$35k–$45k) and take remainder as distributions
(saving self-employment tax on the distribution portion).

### 6. At-Risk and Basis Limitations (IRC §465 / §1366)
Deductible losses cannot exceed each member's at-risk amount (cash invested +
personal-guarantee debt). Track basis annually with your CPA.

---

## Entity Structure Recommendation

**Recommended: Florida LLC with S-Corporation Tax Election**

| Option | Verdict | Reason |
|---|---|---|
| C-Corporation | ✗ Not recommended | Double taxation; losses stay inside corp |
| S-Corporation (standalone) | Acceptable | Less flexible than LLC wrapper |
| LLC (default partnership) | Good | Pass-through; losses flow to owners |
| **LLC + S-Corp election** | **Best** | Pass-through + SE tax savings when profitable |

### Formation Checklist

- [ ] File Articles of Organization with FL DOS ($125 filing fee)
- [ ] Draft Operating Agreement (membership units, driving policy, charging policy)
- [ ] Obtain EIN (IRS Form SS-4, free, instant online)
- [ ] Open dedicated business checking account (no personal transactions)
- [ ] File IRS Form 2553 (S-Corp election) within 75 days of formation
- [ ] Apply for FL commercial vehicle registration + livery plate
- [ ] Obtain commercial auto insurance (livery/for-hire endorsement)
- [ ] Verify local Navarre / Santa Rosa County business license requirements
- [ ] File FL LLC Annual Report by May 1 each year ($138.75)

### Florida Tax Advantage
Florida has **no state personal income tax**. Pass-through LLC income/loss flows
only to federal returns — a meaningful advantage versus most other states.

---

## Autonomous Vehicle Roadmap

| Milestone | Est. Date | Action |
|---|---|---|
| 50 identical route trips logged | Month 2–3 | Route mapping matures for AV |
| Tesla FSD unsupervised (regulatory) | 2026–2027 | Monitor NHTSA approvals |
| FL FDOT commercial AV permit available | 2027–2028 | Apply for permit |
| Phase 2 launch (driverless service) | 2028 | Owners no longer need to drive |

**Savings from driverless operation:**
- Eliminates ~480 owner driving hours/year (2 hrs/day × 240 days)
- If an external driver is ever hired: saves ~$8,640/year vs. FSD subscription cost of $1,188/year
- Allows service window expansion (can add midday trips or weekend service)

---

## Appendix: Key IRS References

| Code Section | Topic |
|---|---|
| IRC §45W | Commercial Clean Vehicle Credit (EV tax credit for businesses) |
| IRC §168 | MACRS depreciation |
| IRC §183 | Hobby loss / profit motive |
| IRC §274(d) | Listed property substantiation requirements |
| IRC §280F(d)(5)(B) | Taxi/for-hire exemption from luxury auto caps |
| IRC §465 | At-risk rules |
| IRC §469 | Passive activity loss rules |
| Form 2553 | S-Corporation election |
| Form 8936 | Clean Vehicle Credit |
| FL Stat §316.85 | Florida autonomous vehicle operation |

---

*This document is a planning tool. Consult a licensed CPA and attorney before
forming the entity, electing tax status, or filing returns.*
