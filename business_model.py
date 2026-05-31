#!/usr/bin/env python3
"""
Navarre EV Taxi Co. — Business & Financial Model
Electric commuter taxi for military personnel, Navarre / Gulf Breeze, FL
Routes: Home → Hurlburt Field / Eglin Air Force Base

Run:  python business_model.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
import json
import textwrap

# ── MACRS 5-Year Half-Year Convention (listed property > 50% business use) ────
MACRS_5YR = [0.2000, 0.3200, 0.1920, 0.1152, 0.1152, 0.0576]  # 6 tax years

# ── FL electricity rate (backup grid; solar covers most charging) ─────────────
GRID_RATE_PER_KWH = 0.12   # FL average, cents/kWh


# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class VehicleConfig:
    make: str = "Tesla"
    model: str = "Model Y RWD"
    model_year: int = 2025
    msrp: float = 44_990.00
    # IRC §45W Commercial Clean Vehicle Credit (vs §30D for personal).
    # Applies when vehicle is purchased by a business entity; up to $7,500
    # for vehicles under 14,000 lb GVWR.  Claimed on Form 8936.
    ev_tax_credit: float = 7_500.00
    range_miles: float = 330.0
    kwh_per_100mi: float = 25.0        # EPA estimate

    @property
    def net_cost(self) -> float:
        return self.msrp - self.ev_tax_credit


@dataclass
class RouteConfig:
    name: str
    base: str
    one_way_miles: float
    daily_trips: int = 2               # morning + evening


ROUTES: list[RouteConfig] = [
    RouteConfig("Hurlburt Route", "Hurlburt Field",  one_way_miles=16.0),
    RouteConfig("Eglin Route",    "Eglin AFB",       one_way_miles=22.0),
]


@dataclass
class Owner:
    name: str
    investment: float
    has_solar: bool = True
    drives: bool = True                # materially participates — drives the car
    personal_miles_per_year: float = 3_000.0


@dataclass
class BusinessConfig:
    name: str = "Navarre EV Taxi LLC"
    entity: str = "LLC (S-Corp election)"   # see IRS guidance section
    state: str = "FL"
    start_year: int = 2025

    # ── Formation costs ────────────────────────────────────────────────────────
    formation_cost: float = 1_500.00   # attorney + FL Articles of Org ($125 filing)
    annual_report_fee: float = 138.75  # FL LLC annual report

    # ── Revenue assumptions ────────────────────────────────────────────────────
    monthly_subscription_per_seat: float = 275.00  # committed monthly commuter
    per_trip_price_per_seat: float = 18.00          # walk-up / occasional
    avg_seats_filled: float = 2.5                   # of 4 rear seats

    # ── Operating calendar ─────────────────────────────────────────────────────
    operating_days_per_year: int = 240    # Mon–Fri less federal holidays + leave

    # ── Charging ───────────────────────────────────────────────────────────────
    solar_coverage_pct: float = 0.85      # 85 % from owner solar panels
    # Business reimburses owners for electricity at avoided grid cost (IRS-safe)

    # ── Insurance (commercial livery auto, FL) ─────────────────────────────────
    monthly_insurance: float = 375.00    # commercial auto + hired/non-owned

    # ── Maintenance (EV = lower than ICE) ─────────────────────────────────────
    maintenance_per_mile: float = 0.030  # tires, brakes, cabin filter, fluid

    # ── Driver wage if hiring externally (Phase 1 non-owner option) ───────────
    external_driver_hourly: float = 18.00
    drive_hours_per_day: float = 2.0     # ~1 h morning + 1 h evening

    # ── Autonomous phase ───────────────────────────────────────────────────────
    # FSD capability subscription OR one-time purchase modeled as annual cost
    fsd_annual_cost: float = 1_188.00   # $99/mo subscription
    av_legal_year: int = 2028           # optimistic estimate for FL commercial AV permit


# ═══════════════════════════════════════════════════════════════════════════════
#  MILEAGE LOG  (IRS §274(d) — "adequate contemporaneous records" required)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MileageEntry:
    entry_date: date
    odometer_start: float
    odometer_end: float
    destination: str
    business_purpose: str
    passengers: int
    is_business: bool

    @property
    def miles(self) -> float:
        return round(self.odometer_end - self.odometer_start, 1)


class MileageLog:
    """
    Tracks odometer readings for business vs. personal use.
    Required by IRS for any listed property (vehicles).  Entries should be
    made at the time of each trip — retroactive reconstruction is a red flag.
    """

    def __init__(self) -> None:
        self._entries: list[MileageEntry] = []

    def add(self, entry: MileageEntry) -> None:
        self._entries.append(entry)

    def log(
        self,
        entry_date: date,
        odometer_start: float,
        odometer_end: float,
        destination: str,
        business_purpose: str,
        passengers: int,
        is_business: bool,
    ) -> MileageEntry:
        e = MileageEntry(
            entry_date, odometer_start, odometer_end,
            destination, business_purpose, passengers, is_business,
        )
        self.add(e)
        return e

    @property
    def business_miles(self) -> float:
        return sum(e.miles for e in self._entries if e.is_business)

    @property
    def personal_miles(self) -> float:
        return sum(e.miles for e in self._entries if not e.is_business)

    @property
    def total_miles(self) -> float:
        return self.business_miles + self.personal_miles

    @property
    def business_pct(self) -> float:
        if self.total_miles == 0:
            return 0.0
        return self.business_miles / self.total_miles

    def summary(self) -> str:
        return (
            f"  Business miles : {self.business_miles:>8,.0f}\n"
            f"  Personal miles : {self.personal_miles:>8,.0f}\n"
            f"  Total miles    : {self.total_miles:>8,.0f}\n"
            f"  Business %     : {self.business_pct:>7.1%}\n"
        )

    def export_json(self, path: str) -> None:
        data = [
            {
                "date": e.entry_date.isoformat(),
                "odo_start": e.odometer_start,
                "odo_end": e.odometer_end,
                "miles": e.miles,
                "destination": e.destination,
                "purpose": e.business_purpose,
                "passengers": e.passengers,
                "business": e.is_business,
            }
            for e in self._entries
        ]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
#  EQUITY LEDGER
# ═══════════════════════════════════════════════════════════════════════════════

class EquityLedger:
    """Pro-rata membership units based on cash investment."""

    UNITS_PER_DOLLAR = 1.0   # 1 unit per $1 invested (simplifies math)

    def __init__(self, owners: list[Owner]) -> None:
        self.owners = owners
        self.total_invested = sum(o.investment for o in owners)

    def units(self, owner: Owner) -> float:
        return owner.investment * self.UNITS_PER_DOLLAR

    def ownership_pct(self, owner: Owner) -> float:
        return owner.investment / self.total_invested

    def allocate(self, amount: float) -> dict[str, float]:
        """Split any amount (profit, loss, expense) pro-rata."""
        return {o.name: amount * self.ownership_pct(o) for o in self.owners}

    def print_table(self) -> None:
        hdr = f"  {'Owner':<18} {'Investment':>12} {'Units':>10} {'Ownership %':>12}"
        print(hdr)
        print("  " + "─" * (len(hdr) - 2))
        for o in self.owners:
            print(
                f"  {o.name:<18} ${o.investment:>11,.0f} "
                f"{self.units(o):>10,.0f} {self.ownership_pct(o):>11.1%}"
            )
        print("  " + "─" * (len(hdr) - 2))
        print(
            f"  {'TOTAL':<18} ${self.total_invested:>11,.0f} "
            f"{self.total_invested:>10,.0f} {'100.0%':>12}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  DEPRECIATION SCHEDULE
# ═══════════════════════════════════════════════════════════════════════════════

def macrs_schedule(
    basis: float,
    business_pct: float,
    start_year: int,
) -> list[dict]:
    """
    5-year MACRS with half-year convention for a listed vehicle used > 50 %
    for business.  Passenger automobiles used for hire (taxi) are exempt from
    the IRC §280F luxury-auto dollar caps.

    basis        = net vehicle cost (MSRP - EV credit)
    business_pct = fraction of miles driven for business
    """
    deductible_basis = basis * business_pct
    rows = []
    for i, rate in enumerate(MACRS_5YR):
        yr = start_year + i
        depr = round(deductible_basis * rate, 2)
        rows.append({"tax_year": yr, "macrs_rate": rate, "depreciation": depr})
    return rows


def print_depreciation(rows: list[dict], basis: float, biz_pct: float) -> None:
    print(f"\n  Vehicle cost basis : ${basis:,.2f}")
    print(f"  Business use %     : {biz_pct:.1%}")
    print(f"  Deductible basis   : ${basis * biz_pct:,.2f}")
    print()
    print(f"  {'Tax Year':>9} {'MACRS Rate':>11} {'Deduction':>12} {'Cumulative':>12}")
    print("  " + "─" * 48)
    cumulative = 0.0
    for r in rows:
        cumulative += r["depreciation"]
        print(
            f"  {r['tax_year']:>9} {r['macrs_rate']:>10.2%} "
            f"  ${r['depreciation']:>10,.2f}  ${cumulative:>10,.2f}"
        )
    print()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAINTENANCE COST ALLOCATION
# ═══════════════════════════════════════════════════════════════════════════════

def allocate_maintenance(
    total_maintenance: float,
    business_pct: float,
    equity: EquityLedger,
) -> dict:
    """
    Business portion → company expense (deductible).
    Personal portion → charged to each owner pro-rata to personal miles driven.
    """
    biz_cost = total_maintenance * business_pct
    personal_cost = total_maintenance * (1 - business_pct)
    personal_alloc = equity.allocate(personal_cost)
    return {
        "business_portion": biz_cost,
        "personal_portion": personal_cost,
        "personal_by_owner": personal_alloc,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  FINANCIAL PROJECTIONS  (5-year, 3 scenarios)
# ═══════════════════════════════════════════════════════════════════════════════

SCENARIOS = {
    "pessimistic": {
        "label": "Pessimistic",
        "seats_filled_yr1": 1.5,   # slow uptake
        "seats_growth": 0.3,       # add ~0.3 seats/yr
        "subscription_pct": 0.50,  # half on subscription
        "owner_drives": True,
    },
    "base": {
        "label": "Base Case",
        "seats_filled_yr1": 2.5,
        "seats_growth": 0.5,
        "subscription_pct": 0.70,
        "owner_drives": True,
    },
    "optimistic": {
        "label": "Optimistic",
        "seats_filled_yr1": 3.2,
        "seats_growth": 0.5,
        "subscription_pct": 0.85,
        "owner_drives": True,
    },
}


def project_year(
    year_num: int,           # 1-indexed
    cfg: BusinessConfig,
    vehicle: VehicleConfig,
    equity: EquityLedger,
    scenario: dict,
    depr_rows: list[dict],
    av_savings: float = 0.0,   # driver cost savings from autonomous (Phase 2)
) -> dict:
    """Return a single-year P&L dictionary."""

    # ── Route miles ────────────────────────────────────────────────────────────
    avg_route_one_way = sum(r.one_way_miles for r in ROUTES) / len(ROUTES)  # ~19 mi
    business_miles = avg_route_one_way * 2 * cfg.operating_days_per_year     # round trip
    personal_miles_all = sum(
        o.personal_miles_per_year for o in equity.owners
        if not o.drives or scenario["owner_drives"]
    )
    total_miles = business_miles + personal_miles_all
    biz_pct = business_miles / total_miles if total_miles > 0 else 0.0

    # ── Revenue ────────────────────────────────────────────────────────────────
    seats = min(
        scenario["seats_filled_yr1"] + scenario["seats_growth"] * (year_num - 1),
        4.0,  # max rear seats
    )
    sub_seats = seats * scenario["subscription_pct"]
    adhoc_seats = seats * (1 - scenario["subscription_pct"])

    sub_revenue = sub_seats * cfg.monthly_subscription_per_seat * 12
    # Ad hoc: ~1 extra round-trip per week per ad-hoc seat
    adhoc_trips = adhoc_seats * 2 * 52
    adhoc_revenue = adhoc_trips * cfg.per_trip_price_per_seat

    gross_revenue = round(sub_revenue + adhoc_revenue, 2)

    # ── Expenses ───────────────────────────────────────────────────────────────
    insurance = cfg.monthly_insurance * 12

    # Charging electricity (actual cost — using avoided grid rate for solar)
    kwh_used = (business_miles / 100) * vehicle.kwh_per_100mi
    grid_kwh = kwh_used * (1 - cfg.solar_coverage_pct)
    electricity = round(
        kwh_used * GRID_RATE_PER_KWH * cfg.solar_coverage_pct * 0 +   # solar = $0 marginal
        grid_kwh * GRID_RATE_PER_KWH,
        2,
    )
    # IRS-safe: reimburse owners at grid rate for solar used → ~$0 net (owner contribution)
    # We show it as $0 cost since solar panels are personal assets contributing free power.

    maintenance_total = business_miles * cfg.maintenance_per_mile
    maintenance_biz = round(maintenance_total * biz_pct, 2)

    # Driver cost (Phase 1: owner drives = $0 direct cost; Phase 2: AV saves this)
    driver_cost = 0.0
    if not scenario["owner_drives"]:
        driver_cost = (
            cfg.external_driver_hourly * cfg.drive_hours_per_day * cfg.operating_days_per_year
        )
    driver_cost = max(0.0, driver_cost - av_savings)

    # FSD subscription (autonomous phase 2+)
    fsd_cost = cfg.fsd_annual_cost if year_num >= (cfg.av_legal_year - cfg.start_year + 1) else 0.0

    annual_report = cfg.annual_report_fee
    misc = 500.0   # accounting, bank fees, misc

    # Depreciation (from pre-computed MACRS schedule for this year)
    depreciation = 0.0
    if year_num - 1 < len(depr_rows):
        depreciation = depr_rows[year_num - 1]["depreciation"]

    total_expenses = round(
        insurance + electricity + maintenance_biz +
        driver_cost + fsd_cost + annual_report + misc + depreciation,
        2,
    )

    ebit = round(gross_revenue - total_expenses, 2)

    return {
        "year": cfg.start_year + year_num - 1,
        "year_num": year_num,
        "business_miles": business_miles,
        "biz_pct": biz_pct,
        "seats_filled": round(seats, 2),
        "revenue": gross_revenue,
        "insurance": insurance,
        "electricity": electricity,
        "maintenance_biz": maintenance_biz,
        "driver_cost": driver_cost,
        "fsd_cost": fsd_cost,
        "annual_report": annual_report,
        "misc": misc,
        "depreciation": depreciation,
        "total_expenses": total_expenses,
        "ebit": ebit,
        "cumulative": 0.0,   # filled in by caller
    }


def run_scenario(
    scenario_key: str,
    cfg: BusinessConfig,
    vehicle: VehicleConfig,
    equity: EquityLedger,
    years: int = 5,
) -> list[dict]:
    scenario = SCENARIOS[scenario_key]

    # Estimate business % for depreciation (use base-case miles)
    avg_route = sum(r.one_way_miles for r in ROUTES) / len(ROUTES)
    biz_miles_yr = avg_route * 2 * cfg.operating_days_per_year
    personal_miles_yr = sum(o.personal_miles_per_year for o in equity.owners)
    biz_pct_est = biz_miles_yr / (biz_miles_yr + personal_miles_yr)

    depr_rows = macrs_schedule(vehicle.net_cost, biz_pct_est, cfg.start_year)

    rows = []
    cumulative = 0.0
    for yr in range(1, years + 1):
        av_savings = 0.0   # future: model driver cost savings
        row = project_year(yr, cfg, vehicle, equity, scenario, depr_rows, av_savings)
        cumulative += row["ebit"]
        row["cumulative"] = round(cumulative, 2)
        rows.append(row)
    return rows


# ═══════════════════════════════════════════════════════════════════════════════
#  BREAK-EVEN ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def break_even_seats(cfg: BusinessConfig, vehicle: VehicleConfig) -> float:
    """
    Monthly seats needed to cover monthly cash expenses (excluding depreciation).
    Assumes owner-operated (no driver cost), base solar charging.
    """
    avg_route = sum(r.one_way_miles for r in ROUTES) / len(ROUTES)
    monthly_biz_miles = avg_route * 2 * (cfg.operating_days_per_year / 12)
    monthly_fixed = cfg.monthly_insurance + cfg.annual_report_fee / 12 + 500 / 12
    monthly_variable_per_seat = (cfg.per_trip_price_per_seat * 2 * cfg.operating_days_per_year / 12)
    monthly_maintenance = monthly_biz_miles * cfg.maintenance_per_mile

    fixed_total = monthly_fixed + monthly_maintenance
    avg_rev_per_seat = cfg.monthly_subscription_per_seat  # subscription model

    seats_needed = fixed_total / avg_rev_per_seat
    return seats_needed


# ═══════════════════════════════════════════════════════════════════════════════
#  PHASE 2: AUTONOMOUS VEHICLE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def av_analysis(cfg: BusinessConfig) -> dict:
    """Cost savings when a human driver is replaced by autonomous tech."""
    annual_driver_cost = (
        cfg.external_driver_hourly * cfg.drive_hours_per_day * cfg.operating_days_per_year
    )
    # If owner drives, opportunity cost = owner's time value (estimate $25/hr)
    owner_opportunity_cost = 25.0 * cfg.drive_hours_per_day * cfg.operating_days_per_year
    fsd_annual = cfg.fsd_annual_cost

    return {
        "external_driver_annual": annual_driver_cost,
        "fsd_annual_cost": fsd_annual,
        "savings_vs_external_driver": annual_driver_cost - fsd_annual,
        "owner_time_freed_hours": cfg.drive_hours_per_day * cfg.operating_days_per_year,
        "owner_opportunity_value": owner_opportunity_cost,
        "estimated_av_legal_year_fl": cfg.av_legal_year,
        "notes": [
            "FL Stat §316.85 permits AV operation without human driver.",
            "Commercial-for-hire AV requires FDOT permit (process still evolving).",
            "Tesla FSD (Supervised) currently requires attentive human at all times.",
            "Model assumes AV commercial viability by 2028 (optimistic).",
            "After ~50 identical trips, route mapping is well-established.",
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  IRS & ENTITY GUIDANCE
# ═══════════════════════════════════════════════════════════════════════════════

IRS_REDFLAG_NOTES = """
  IRS RED FLAGS & MITIGATION
  ──────────────────────────

  1. HOBBY LOSS RULE  (IRC §183)
     Risk:  If the IRS determines the activity lacks a profit motive, losses
            are disallowed.  Safe harbor = profitable in 3 of any 5 consecutive
            tax years.  Early-year losses are common and acceptable IF the
            business is conducted in a businesslike manner.
     Mitigation:
       • Maintain a formal written business plan (this document).
       • Open a dedicated business checking account — never commingle.
       • Keep a detailed mileage log (MileageLog class, export to JSON/CSV).
       • File Schedule C or Form 1065 reporting all income and expenses.
       • Document revenue-growth efforts (marketing, pricing changes).
       • Consider filing Form 5213 (Election to Postpone Determination) to
         get 5-year safe-harbor window (but it flags you to IRS — consult CPA).

  2. PASSIVE ACTIVITY LOSS RULES  (IRC §469)
     Risk:  If a member does NOT materially participate (< 500 hrs/yr or not
            "substantially all" participation), losses are "passive" and can
            only offset passive income, not W-2 wages.
     Mitigation:
       • Owner-drivers materially participate — log driving hours.
       • At least one member should log > 500 hours/year of business activity
         (driving, scheduling, marketing, bookkeeping).
       • Military investors who only invest and do NOT drive are passive —
         their share of losses may be suspended until the business turns
         profitable or is sold.

  3. LISTED PROPERTY / VEHICLE DOCUMENTATION  (IRC §274(d), §280F)
     Risk:  Vehicles are "listed property."  Without adequate contemporaneous
            records, the IRS can disallow ALL vehicle deductions.
     Mitigation:
       • Log every trip (date, odometer start/end, destination, purpose).
       • MileageLog.export_json() produces audit-ready records.
       • Tesla app provides GPS trip history as corroborating evidence.
       • NOTE: Taxi/for-hire vehicles are EXEMPT from §280F luxury-auto
         dollar caps (IRC §280F(d)(5)(B)) — full MACRS depreciation applies
         on the business-use percentage.

  4. CHARGING AT PERSONAL RESIDENCES
     Risk:  "Free" solar charging could be characterized as a disguised
            distribution (taxable) rather than a business expense.
     Mitigation:
       • LLC operating agreement should specify that owners' solar power
         is contributed as a capital contribution (valued at avoided grid
         cost) OR that the company reimburses at the local utility rate.
       • Keep monthly records of kWh consumed on business trips.
       • Tesla app reports kWh per trip — export monthly.

  5. RELATED-PARTY TRANSACTIONS
     Risk:  Owners renting their driveways / chargers to the LLC at above-
            market rates would be scrutinized.
     Mitigation:
       • Any lease or reimbursement should be at or below fair market value.
       • Document the basis (utility rate, local lease comps).

  6. REASONABLE COMPENSATION  (if S-Corp election is made)
     Risk:  S-Corp owner-employees must receive a "reasonable salary" before
            taking distributions; under-paying salary to avoid payroll tax
            is an audit trigger.
     Mitigation:
       • In early loss years, salary can be $0 if the business cannot afford
         it — document the rationale.
       • Once profitable, set salary at BLS median for local taxi drivers
         (~$35k–$45k/yr) and take excess profit as distributions.

  7. AT-RISK RULES  (IRC §465)
     Deductible losses limited to each member's "amount at risk" = cash
     invested + loans for which they are personally liable.  Members cannot
     deduct more than their at-risk basis.

  8. BASIS LIMITATIONS  (LLC / S-Corp)
     Members can only deduct losses up to their tax basis (investment +
     share of recourse debt).  Track each owner's basis annually.
"""

ENTITY_RECOMMENDATION = """
  RECOMMENDED ENTITY: Florida LLC → S-Corporation Tax Election

  WHY NOT C-CORP:
    • Double taxation: corporate income taxed, then dividends taxed again.
    • Losses in the LLC flow through to owners' personal returns immediately.
      C-Corp losses stay inside the corporation and cannot offset owners'
      other W-2 income.

  WHY NOT PURE S-CORP (without LLC wrapper):
    • S-Corp is a tax status, not a state entity.  Florida does not have
      an S-Corp filing — you elect S-Corp treatment for an existing entity.
    • LLC provides operational flexibility (no required board meetings,
      no stock certificates required, flexible profit allocation rules).

  RECOMMENDED STRUCTURE — LLC with S-Corp Election:
    Step 1: Form a Florida LLC  ($125 state filing + attorney ~ $1,000–$1,500)
    Step 2: Draft an Operating Agreement specifying:
              – Membership units proportional to initial capital contribution.
              – Profit/loss allocation = pro-rata to units (simplest for IRS).
              – Management: member-managed (all owners vote on major decisions).
              – Charging/electricity reimbursement policy.
              – Vehicle personal-use policy and mileage log requirement.
    Step 3: Obtain EIN from IRS (Form SS-4, free, instant online).
    Step 4: Open dedicated business checking account.
    Step 5: Elect S-Corporation tax treatment (IRS Form 2553) within 75 days
            of formation.  This gives pass-through taxation AND potential
            self-employment tax savings once profitable.
    Step 6: File FL annual report ($138.75) each year by May 1.

  FL TAX ADVANTAGE:
    Florida has NO state personal income tax.  Pass-through income from the
    LLC flows to owners' federal returns only — a significant advantage.

  WHEN TO REVISIT:
    • If a third investor joins later, amend the Operating Agreement and issue
      new units pro-rata to the new investment.  No need to restructure.
    • If revenue exceeds ~$100k/yr, consult a CPA on whether S-Corp salary
      optimization is saving meaningful self-employment tax.
"""


# ═══════════════════════════════════════════════════════════════════════════════
#  REPORT PRINTER
# ═══════════════════════════════════════════════════════════════════════════════

def _money(v: float) -> str:
    sign = "-" if v < 0 else " "
    return f"{sign}${abs(v):>10,.0f}"


def print_report(
    cfg: BusinessConfig,
    vehicle: VehicleConfig,
    owners: list[Owner],
) -> None:
    equity = EquityLedger(owners)
    sep = "═" * 72

    # ── Header ─────────────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"  {cfg.name}  |  Business Model  |  {cfg.start_year}")
    print(f"  Navarre / Gulf Breeze, FL  →  Hurlburt Field & Eglin AFB")
    print(sep)

    # ── Vehicle ────────────────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  VEHICLE")
    print(f"{'─'*72}")
    print(f"  {vehicle.model_year} {vehicle.make} {vehicle.model}")
    print(f"  MSRP                      : ${vehicle.msrp:>10,.2f}")
    print(f"  IRC §45W EV Tax Credit    : -${vehicle.ev_tax_credit:>9,.2f}")
    print(f"  Net Cost (vehicle basis)  : ${vehicle.net_cost:>10,.2f}")
    print(f"  Range                     : {vehicle.range_miles:.0f} miles")
    print(f"  Efficiency                : {vehicle.kwh_per_100mi:.0f} kWh / 100 mi")

    # ── Capital & Equity ───────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  CAPITAL STRUCTURE & EQUITY")
    print(f"{'─'*72}")
    equity.print_table()
    print(f"\n  Total capital raised       : ${equity.total_invested:>10,.0f}")
    startup_costs = vehicle.net_cost + cfg.formation_cost
    reserve = equity.total_invested - startup_costs
    print(f"  Vehicle + formation costs  : ${startup_costs:>10,.0f}")
    print(f"  Operating reserve          : ${reserve:>10,.0f}")

    # ── Routes ─────────────────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  ROUTES")
    print(f"{'─'*72}")
    for r in ROUTES:
        rt = r.one_way_miles * 2 * cfg.operating_days_per_year
        print(
            f"  {r.name:<20} {r.one_way_miles:.0f} mi one-way   "
            f"~{rt:,.0f} business mi/yr"
        )

    # ── Mileage log demo ───────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  MILEAGE LOG  (sample — IRS §274(d) contemporaneous records)")
    print(f"{'─'*72}")
    log = MileageLog()
    log.log(date(2025, 9, 2),  0.0,    16.1, "Hurlburt Field",
            "Passenger drop-off, military commute", 2, True)
    log.log(date(2025, 9, 2),  16.1,   32.2, "Navarre (return)",
            "Return from Hurlburt Field drop-off", 0, True)
    log.log(date(2025, 9, 2),  32.2,   47.1, "Publix, Navarre",
            "Personal grocery run", 0, False)
    log.log(date(2025, 9, 2),  47.1,   49.8, "Home",
            "Personal (return from grocery)", 0, False)
    log.log(date(2025, 9, 3),  49.8,   49.8 + 21.8, "Eglin AFB",
            "Passenger drop-off, military commute", 3, True)
    log.log(date(2025, 9, 3),  49.8 + 21.8, 49.8 + 43.6, "Navarre (return)",
            "Return from Eglin AFB", 0, True)
    print(log.summary())
    print("  TIP: Call log.export_json('mileage_2025.json') to produce an")
    print("  audit-ready JSON file.  Tesla app trip history corroborates.")

    # ── Depreciation ───────────────────────────────────────────────────────────
    avg_route = sum(r.one_way_miles for r in ROUTES) / len(ROUTES)
    biz_miles_yr = avg_route * 2 * cfg.operating_days_per_year
    personal_miles_yr = sum(o.personal_miles_per_year for o in owners)
    biz_pct = biz_miles_yr / (biz_miles_yr + personal_miles_yr)
    depr_rows = macrs_schedule(vehicle.net_cost, biz_pct, cfg.start_year)

    print(f"\n{'─'*72}")
    print(f"  MACRS 5-YEAR DEPRECIATION SCHEDULE  (IRC §168, for-hire vehicle)")
    print(f"{'─'*72}")
    print_depreciation(depr_rows, vehicle.net_cost, biz_pct)

    # ── Maintenance allocation ─────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  MAINTENANCE COST ALLOCATION  (sample year 1)")
    print(f"{'─'*72}")
    total_maint = (biz_miles_yr + personal_miles_yr) * cfg.maintenance_per_mile
    alloc = allocate_maintenance(total_maint, biz_pct, equity)
    print(f"  Total estimated maintenance       : ${total_maint:>8,.0f}/yr")
    print(f"  Business portion (deductible)     : ${alloc['business_portion']:>8,.0f}")
    print(f"  Personal portion (charged to owners):")
    for name, amt in alloc["personal_by_owner"].items():
        print(f"    {name:<20} : ${amt:>7,.2f}")

    # ── Break-even ─────────────────────────────────────────────────────────────
    be_seats = break_even_seats(cfg, vehicle)
    print(f"\n{'─'*72}")
    print(f"  BREAK-EVEN ANALYSIS  (cash basis, owner-operated, subscription model)")
    print(f"{'─'*72}")
    print(f"  Monthly fixed costs (insurance + fees + maintenance)")
    print(f"  Monthly subscription per seat     : ${cfg.monthly_subscription_per_seat:>8,.2f}")
    print(f"  Seats needed to break even (cash) : {be_seats:>8.2f}")
    print(f"  → With 2 regular subscribers you cover all cash costs.")
    print(f"  → Depreciation is non-cash; ignoring it for cash break-even.")

    # ── 5-Year Projections ─────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  5-YEAR P&L PROJECTIONS  (all values USD, tax-basis incl. depreciation)")
    print(f"{'─'*72}")

    col_w = 12
    for skey, sdata in SCENARIOS.items():
        rows = run_scenario(skey, cfg, vehicle, equity)
        print(f"\n  ── {sdata['label']} ──")
        hdr = (
            f"  {'Year':>6} {'Seats':>6} {'Revenue':>{col_w}} "
            f"{'Expenses':>{col_w}} {'EBIT':>{col_w}} {'Cumulative':>{col_w}}"
        )
        print(hdr)
        print("  " + "─" * (len(hdr) - 2))
        for r in rows:
            ebit_s = _money(r["ebit"])
            cum_s  = _money(r["cumulative"])
            print(
                f"  {r['year']:>6} {r['seats_filled']:>6.1f}"
                f"  ${r['revenue']:>10,.0f}"
                f"  ${r['total_expenses']:>10,.0f}"
                f" {ebit_s}"
                f" {cum_s}"
            )

        # Expense detail for year 1
        r1 = rows[0]
        print(f"\n  Year 1 expense detail:")
        print(f"    Insurance                : ${r1['insurance']:>9,.0f}")
        print(f"    Electricity (grid backup): ${r1['electricity']:>9,.0f}  (solar covers {cfg.solar_coverage_pct:.0%})")
        print(f"    Maintenance (biz share)  : ${r1['maintenance_biz']:>9,.0f}")
        print(f"    Driver cost              : ${r1['driver_cost']:>9,.0f}  (owner-operated = $0)")
        print(f"    FL annual report         : ${r1['annual_report']:>9.2f}")
        print(f"    Misc (acctg, bank, etc.) : ${r1['misc']:>9,.0f}")
        print(f"    Depreciation (non-cash)  : ${r1['depreciation']:>9,.0f}")

    # ── Autonomous Phase ───────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  PHASE 2: AUTONOMOUS VEHICLE ANALYSIS")
    print(f"{'─'*72}")
    av = av_analysis(cfg)
    print(f"  Est. external driver cost/yr  : ${av['external_driver_annual']:>9,.0f}")
    print(f"  FSD annual subscription       : ${av['fsd_annual_cost']:>9,.0f}")
    print(f"  Net savings vs hired driver   : ${av['savings_vs_external_driver']:>9,.0f}/yr")
    print(f"  Owner driving hours freed/yr  : {av['owner_time_freed_hours']:>9.0f} hrs")
    print(f"  Owner opportunity value       : ${av['owner_opportunity_value']:>9,.0f}/yr")
    print(f"  Est. FL commercial AV permit  : {av['estimated_av_legal_year_fl']}")
    print()
    for note in av["notes"]:
        print(f"  • {note}")

    # ── IRS & Entity ───────────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  IRS CONSIDERATIONS")
    print(f"{'─'*72}")
    print(IRS_REDFLAG_NOTES)

    print(f"\n{'─'*72}")
    print(f"  ENTITY STRUCTURE RECOMMENDATION")
    print(f"{'─'*72}")
    print(ENTITY_RECOMMENDATION)

    print(sep)
    print(f"  Model generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  DISCLAIMER: This model is for planning purposes.  Consult a CPA")
    print(f"  and attorney before forming the entity or filing tax returns.")
    print(sep)


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT — edit owners / config here before running
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    # ── Define your owners ─────────────────────────────────────────────────────
    # Two-owner example.  Add a third block if there's a third investor.
    owners = [
        Owner(
            name="Owner A",
            investment=20_000.00,
            has_solar=True,
            drives=True,
            personal_miles_per_year=3_000,
        ),
        Owner(
            name="Owner B",
            investment=20_000.00,
            has_solar=True,
            drives=True,
            personal_miles_per_year=2_500,
        ),
        # Uncomment and adjust for a third investor:
        # Owner(
        #     name="Owner C",
        #     investment=10_000.00,
        #     has_solar=True,
        #     drives=False,   # passive investor
        #     personal_miles_per_year=0,
        # ),
    ]

    vehicle = VehicleConfig()
    cfg = BusinessConfig()

    print_report(cfg, vehicle, owners)
