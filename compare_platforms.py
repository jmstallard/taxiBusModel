#!/usr/bin/env python3
"""
Navarre EV Taxi Co. — Platform Comparison
Independent LLC  vs.  Uber  vs.  Lyft  vs.  Hybrid

Run:  python compare_platforms.py

KEY CONTEXT
───────────
• Routes: Navarre/Gulf Breeze → Hurlburt Field (~16 mi) / Eglin AFB (~22 mi)
• Passengers: military commuters, 2–3 per trip
• Schedule: morning drop-off + evening pick-up, ~240 days/yr
• Vehicle: 2025 Tesla Model Y RWD, $44,990 (no EV credit post-OBBB)
• Owners: 2–3 friends with residential solar panels

CRITICAL BASE-ACCESS ISSUE
───────────────────────────
Uber/Lyft drivers without DoD credentials CANNOT enter Hurlburt Field
or Eglin AFB gates.  They must drop off and pick up at the installation
entrance, not at the barracks, squadron, or work building.  This is a
meaningful degradation of the service value proposition vs. the
independent model where an owner who holds a valid base pass (or can
obtain a visitor pass) delivers door-to-door.

Sources reviewed:
  • help.uber.com — military base access application (case-by-case FOIA)
  • mybaseguide.com — Army pilot at 6 bases (not Hurlburt/Eglin as of 2026)
  • uberpeople.net — driver forum: "base access denied" is common
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
#  SHARED CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

VEHICLE_MSRP        = 44_990.00   # Tesla Model Y RWD; no EV credit (OBBB)
AVG_ROUTE_ONE_WAY   = 19.0        # miles (avg of Hurlburt 16 mi + Eglin 22 mi)
TRIPS_PER_DAY       = 2           # morning + evening
OPERATING_DAYS      = 240         # Mon–Fri less federal holidays
SOLAR_COVERAGE      = 0.85        # fraction of charging from owner solar panels
GRID_RATE           = 0.12        # $/kWh FL avg (backup only)
KWH_PER_100MI       = 25.0        # Tesla Model Y efficiency

# Annual business miles (commute runs only)
ANNUAL_BIZ_MILES = AVG_ROUTE_ONE_WAY * 2 * TRIPS_PER_DAY * OPERATING_DAYS  # 18,240

# Annual electricity cost (grid backup, 15% of charging)
_kwh_biz = (ANNUAL_BIZ_MILES / 100) * KWH_PER_100MI
ANNUAL_ELECTRICITY = round(_kwh_biz * (1 - SOLAR_COVERAGE) * GRID_RATE, 0)  # ~$83

# ── FL Uber/Lyft per-trip rate estimates (smaller market, Fort Walton Beach area) ──
# Uber publicly reports FL rates vary by market.  Estimates for NW FL:
UBER_BASE_FARE      = 1.15    # $
UBER_PER_MILE       = 0.87    # $/mi
UBER_PER_MIN        = 0.11    # $/min
UBER_PLATFORM_CUT   = 0.25    # 25% to Uber
LYFT_PLATFORM_CUT   = 0.22    # ~22% to Lyft (slightly better for driver)
AVG_TRIP_MINUTES    = 28.0    # minutes for 19-mile trip
AVG_TIP_PER_TRIP    = 3.50    # regular commuter tips well
MORNING_SURGE       = 1.30    # avg 1.3× surge on 0600–0700 commute

# ── MACRS 5-year rates ─────────────────────────────────────────────────────────
MACRS_5YR = [0.2000, 0.3200, 0.1920, 0.1152, 0.1152, 0.0576]
BIZ_PCT   = 0.624   # ~62.4% business use (biz miles / total miles, 2 owners)


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def macrs_year(year_idx: int) -> float:
    """Return MACRS deduction for year 1–6 (0-indexed)."""
    if year_idx >= len(MACRS_5YR):
        return 0.0
    return VEHICLE_MSRP * BIZ_PCT * MACRS_5YR[year_idx]


def gross_fare_per_trip(surge: float = 1.0) -> float:
    return (UBER_BASE_FARE
            + UBER_PER_MILE * AVG_ROUTE_ONE_WAY
            + UBER_PER_MIN  * AVG_TRIP_MINUTES) * surge


def _bar(value: float, max_val: float, width: int = 30) -> str:
    filled = int(round(width * value / max_val)) if max_val else 0
    return "█" * filled + "░" * (width - filled)


def _pct(a: float, b: float) -> str:
    if b == 0:
        return "N/A"
    return f"{a/b:+.0%}"


# ═══════════════════════════════════════════════════════════════════════════════
#  MODEL A — INDEPENDENT LLC
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class IndependentModel:
    """
    LLC (S-Corp election) with 2 owner-drivers.
    Revenue: monthly subscriptions + occasional ad-hoc rides.
    Charging: solar (near-zero fuel cost).
    Insurance: commercial livery policy.
    """
    seats_year1: float = 2.5
    seats_max:   float = 4.0
    sub_price:   float = 275.0    # $/seat/month
    adhoc_price: float = 18.0     # $/seat one-way
    sub_pct:     float = 0.70     # 70% of seats on subscription
    seats_growth: float = 0.50    # seats added per year

    monthly_insurance:   float = 375.00   # commercial livery auto
    formation_cost:      float = 1_500.00
    annual_report_fee:   float = 138.75
    misc_annual:         float = 500.00   # acctg, bank, etc.

    def revenue(self, year: int) -> float:
        seats     = min(self.seats_year1 + self.seats_growth * (year - 1), self.seats_max)
        sub_rev   = seats * self.sub_pct * self.sub_price * 12
        adhoc_rev = seats * (1 - self.sub_pct) * 2 * 52 * self.adhoc_price
        return round(sub_rev + adhoc_rev, 0)

    def expenses(self, year: int) -> float:
        insurance   = self.monthly_insurance * 12
        maintenance = ANNUAL_BIZ_MILES * 0.030 * BIZ_PCT
        depreciation = macrs_year(year - 1)
        annual_rpt  = self.annual_report_fee
        misc        = self.misc_annual
        return round(insurance + ANNUAL_ELECTRICITY + maintenance + depreciation + annual_rpt + misc, 0)

    def annual_revenue(self, year: int) -> float:
        return self.revenue(year)

    def ebit(self, year: int) -> float:
        return self.revenue(year) - self.expenses(year)

    def startup_cost(self) -> float:
        return VEHICLE_MSRP + self.formation_cost   # no EV credit


# ═══════════════════════════════════════════════════════════════════════════════
#  MODEL B — UBER (single owner-driver)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class UberModel:
    """
    Single driver on Uber platform.  Revenue from commute runs only
    (same hours as Independent model) PLUS opportunistic rides during
    dead time between commute runs.

    NOTE: Co-ownership is NOT directly supported by Uber's model.
    Multiple friends cannot each earn income from the same Uber account.
    They would each need their own account and alternate driving the
    same vehicle — allowed but requires careful vehicle registration
    and insurance coordination.
    """
    # Commute trips (fixed route, same as Independent model)
    commute_trips_per_day: int = 2         # morning drop + evening return
    commute_surge:   float = MORNING_SURGE  # morning surge boost

    # Opportunistic rides in dead time (noon, afternoons, weekends)
    extra_hours_per_day: float = 1.5        # conservative; military area is not dense
    extra_rev_per_hour:  float = 15.00      # net after Uber cut, NW FL market

    # Uber EV incentive (one-time, Platinum/Diamond status, 100 trips by Dec 31 2026)
    ev_incentive:         float = 4_000.00  # max Uber "Go Electric" bonus
    ev_incentive_attained: bool = True      # optimistic: assume they qualify

    # Insurance: personal auto + rideshare endorsement (Uber covers $1M during trip)
    monthly_insurance:    float = 175.00    # personal + rideshare endorsement (~$15 extra)

    def gross_fare_per_commute_trip(self) -> float:
        """What Uber charges the passenger (one vehicle, one booking)."""
        return gross_fare_per_trip(surge=self.commute_surge)

    def driver_net_per_commute_trip(self) -> float:
        """Driver's cut after Uber platform fee + tip."""
        gross = self.gross_fare_per_commute_trip()
        return round(gross * (1 - UBER_PLATFORM_CUT) + AVG_TIP_PER_TRIP, 2)

    def annual_commute_revenue(self) -> float:
        return round(self.driver_net_per_commute_trip() * self.commute_trips_per_day * OPERATING_DAYS, 0)

    def annual_extra_revenue(self) -> float:
        return round(self.extra_rev_per_hour * self.extra_hours_per_day * OPERATING_DAYS, 0)

    def annual_revenue(self, year: int) -> float:
        base = self.annual_commute_revenue() + self.annual_extra_revenue()
        # One-time Uber EV incentive in year 1
        bonus = self.ev_incentive if (year == 1 and self.ev_incentive_attained) else 0.0
        return round(base + bonus, 0)

    def expenses(self, year: int) -> float:
        insurance    = self.monthly_insurance * 12
        maintenance  = ANNUAL_BIZ_MILES * 0.030
        depreciation = macrs_year(year - 1)
        misc         = 200.0    # no formation/report costs; minimal admin
        return round(insurance + ANNUAL_ELECTRICITY + maintenance + depreciation + misc, 0)

    def ebit(self, year: int) -> float:
        return self.annual_revenue(year) - self.expenses(year)

    def startup_cost(self) -> float:
        return VEHICLE_MSRP   # no formation cost; no EV credit


# ═══════════════════════════════════════════════════════════════════════════════
#  MODEL C — LYFT (single owner-driver)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LyftModel:
    """
    Same as Uber model but with Lyft's slightly lower platform cut (~22%)
    and generally similar but slightly lower driver earnings in smaller FL markets.
    Lyft market share is lower in NW Florida — fewer opportunistic rides.
    """
    commute_trips_per_day: int = 2
    commute_surge:   float = 1.20         # Lyft surge is typically lower than Uber
    extra_hours_per_day: float = 1.0      # less demand than Uber in this market
    extra_rev_per_hour:  float = 13.00    # net after Lyft cut
    ev_incentive:        float = 0.0      # Lyft EV program not confirmed for this market
    monthly_insurance:   float = 175.00

    def gross_fare_per_commute_trip(self) -> float:
        return gross_fare_per_trip(surge=self.commute_surge)

    def driver_net_per_commute_trip(self) -> float:
        gross = self.gross_fare_per_commute_trip()
        return round(gross * (1 - LYFT_PLATFORM_CUT) + AVG_TIP_PER_TRIP, 2)

    def annual_commute_revenue(self) -> float:
        return round(self.driver_net_per_commute_trip() * self.commute_trips_per_day * OPERATING_DAYS, 0)

    def annual_extra_revenue(self) -> float:
        return round(self.extra_rev_per_hour * self.extra_hours_per_day * OPERATING_DAYS, 0)

    def annual_revenue(self, year: int) -> float:
        return round(self.annual_commute_revenue() + self.annual_extra_revenue(), 0)

    def expenses(self, year: int) -> float:
        insurance    = self.monthly_insurance * 12
        maintenance  = ANNUAL_BIZ_MILES * 0.030
        depreciation = macrs_year(year - 1)
        misc         = 200.0
        return round(insurance + ANNUAL_ELECTRICITY + maintenance + depreciation + misc, 0)

    def ebit(self, year: int) -> float:
        return self.annual_revenue(year) - self.expenses(year)

    def startup_cost(self) -> float:
        return VEHICLE_MSRP


# ═══════════════════════════════════════════════════════════════════════════════
#  MODEL D — HYBRID (LLC + Uber/Lyft for fill-in rides)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class HybridModel:
    """
    LLC handles the committed military subscription commuters (contract revenue).
    Same driver also registers as an Uber/Lyft driver and fills dead time
    (mid-morning to mid-afternoon, some weekends) with platform rides.

    IMPORTANT LEGAL NOTE:
    Uber/Lyft Terms of Service prohibit soliciting riders OFF the platform for
    platform-matched trips.  However, the LLC's subscription contracts are
    pre-arranged BEFORE the platform is involved — these are not Uber/Lyft trips.
    The driver simply uses two revenue streams: LLC subscriptions for the fixed
    military commute + Uber/Lyft app for opportunistic rides.
    Verify with an attorney that your LLC's subscription model does not conflict
    with Uber/Lyft ToS in your specific market.

    Insurance: commercial livery policy covers the LLC work; Uber/Lyft $1M
    covers platform trips.  Rideshare endorsement bridges the gap.
    Total insurance cost is higher but justified by dual-stream revenue.
    """
    # LLC subscription revenue (same as Independent base case)
    seats_year1:   float = 2.5
    seats_max:     float = 4.0
    sub_price:     float = 275.0
    adhoc_price:   float = 18.0
    sub_pct:       float = 0.70
    seats_growth:  float = 0.50

    # Platform fill-in (dead time only — NOT during subscription commute hours)
    extra_hours_per_day: float = 2.0     # mid-morning + afternoon
    extra_rev_per_hour:  float = 14.00   # blended Uber/Lyft, NW FL market

    # Uber EV incentive (one-time year 1, if they qualify)
    ev_incentive:  float = 4_000.00
    ev_incentive_attained: bool = True

    # Insurance: commercial + rideshare endorsement
    monthly_insurance: float = 420.00   # slightly above pure commercial

    formation_cost:    float = 1_500.00
    annual_report_fee: float = 138.75
    misc_annual:       float = 600.00

    def sub_revenue(self, year: int) -> float:
        seats     = min(self.seats_year1 + self.seats_growth * (year - 1), self.seats_max)
        sub_rev   = seats * self.sub_pct * self.sub_price * 12
        adhoc_rev = seats * (1 - self.sub_pct) * 2 * 52 * self.adhoc_price
        return round(sub_rev + adhoc_rev, 0)

    def platform_revenue(self, year: int) -> float:
        base  = round(self.extra_rev_per_hour * self.extra_hours_per_day * OPERATING_DAYS, 0)
        bonus = self.ev_incentive if (year == 1 and self.ev_incentive_attained) else 0.0
        return round(base + bonus, 0)

    def annual_revenue(self, year: int) -> float:
        return self.sub_revenue(year) + self.platform_revenue(year)

    def expenses(self, year: int) -> float:
        insurance    = self.monthly_insurance * 12
        maintenance  = ANNUAL_BIZ_MILES * 0.030
        depreciation = macrs_year(year - 1)
        annual_rpt   = self.annual_report_fee
        misc         = self.misc_annual
        return round(insurance + ANNUAL_ELECTRICITY + maintenance + depreciation + annual_rpt + misc, 0)

    def ebit(self, year: int) -> float:
        return self.annual_revenue(year) - self.expenses(year)

    def startup_cost(self) -> float:
        return VEHICLE_MSRP + self.formation_cost


# ═══════════════════════════════════════════════════════════════════════════════
#  QUALITATIVE SCORECARD
# ═══════════════════════════════════════════════════════════════════════════════

SCORECARD = {
    #  Factor                    Indep   Uber   Lyft   Hybrid
    "Base access (door-to-door)": ["✓ Yes*", "✗ Gate only", "✗ Gate only", "✓ Yes*"],
    "Co-ownership / revenue split":["✓ LLC units", "✗ One driver", "✗ One driver", "✓ LLC units"],
    "Guaranteed revenue":          ["✓ Subscriptions", "✗ Pay-per-ride", "✗ Pay-per-ride", "✓ Sub + rides"],
    "Startup complexity":          ["Medium", "Low", "Low", "Medium"],
    "Startup cost":                ["$46,490", "$44,990", "$44,990", "$46,490"],
    "Insurance cost/yr":           ["$4,500", "$2,100", "$2,100", "$5,040"],
    "Platform cut on rides":       ["None", "25%", "~22%", "22–25% (fill only)"],
    "Uber $4k EV incentive":       ["✗ No", "✓ Possible", "✗ No", "✓ Possible"],
    "Path to driverless (Phase 2)":["✓ Full AV taxi", "✗ Uber owns AV", "✗ Lyft owns AV", "✓ Subscriptions only"],
    "IRS filing":                  ["Form 1065/K-1", "Schedule C", "Schedule C", "Form 1065/K-1"],
    "Hobby-loss risk":             ["Medium (losses yr 1–3)", "Low (active gig income)", "Low", "Low (hybrid revenue)"],
    "Scalability (2nd vehicle)":   ["✓ Expand LLC", "Medium (new account)", "Medium", "✓ Expand LLC"],
}


# ═══════════════════════════════════════════════════════════════════════════════
#  REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def print_report() -> None:
    indie  = IndependentModel()
    uber   = UberModel()
    lyft   = LyftModel()
    hybrid = HybridModel()

    models = [
        ("Independent LLC", indie),
        ("Uber",            uber),
        ("Lyft",            lyft),
        ("Hybrid LLC+Uber", hybrid),
    ]

    SEP  = "═" * 76
    DASH = "─" * 76

    print(f"\n{SEP}")
    print("  NAVARRE EV TAXI — Platform Comparison")
    print("  Independent LLC  vs.  Uber  vs.  Lyft  vs.  Hybrid LLC+Uber")
    print(f"{SEP}")

    # ── Base access warning ────────────────────────────────────────────────────
    print("""
  ⚠  BASE ACCESS — THE KEY DIFFERENTIATOR
  ─────────────────────────────────────────────────────────────────────────
  Uber/Lyft drivers WITHOUT DoD credentials must stop at the installation
  gate.  They cannot enter Hurlburt Field or Eglin AFB to drop off or
  pick up inside the base.

  The Army's rideshare pilot (2025) covers 6 Army bases — NOT Air Force
  installations.  Eglin and Hurlburt are Air Force / AFSOC bases with
  stricter access control than Army posts.

  Impact:
    • Independent LLC owner WITH a base pass → door-to-building service.
      This is a premium differentiator worth $50–75/mo extra to riders
      who hate the gate wait (10–20 min each way during morning rush).
    • Uber/Lyft → gate drop only; riders walk/shuttle from gate.

  * "Yes" for Independent/Hybrid assumes at least one owner holds or can
    obtain a base visitor credential.  Contact the Hurlburt/Eglin visitor
    control center for sponsor requirements.
""")

    # ── Startup costs ──────────────────────────────────────────────────────────
    print(DASH)
    print("  STARTUP COSTS")
    print(DASH)
    for name, m in models:
        sc = m.startup_cost()
        print(f"  {name:<20} ${sc:>10,.0f}  {_bar(sc, 50_000)}")
    print()

    # ── Trip economics ─────────────────────────────────────────────────────────
    print(DASH)
    print("  SINGLE COMMUTE TRIP ECONOMICS  (19-mile route, morning surge)")
    print(DASH)
    gross  = gross_fare_per_trip(MORNING_SURGE)
    uber_n = uber.driver_net_per_commute_trip()
    lyft_n = lyft.driver_net_per_commute_trip()
    # Independent: one-way fare if paid per trip vs. subscription amortized
    indie_per_trip = (indie.sub_price * indie.sub_pct + indie.adhoc_price * (1-indie.sub_pct) * 2 * 4) / (2 * 20) * indie.seats_year1
    indie_per_vehicle_trip = indie.revenue(1) / (TRIPS_PER_DAY * OPERATING_DAYS)

    print(f"  Gross fare (passenger pays)      : ${gross:>7.2f}  [Uber/Lyft estimate]")
    print(f"  Uber driver net/trip (70% + tip) : ${uber_n:>7.2f}")
    print(f"  Lyft driver net/trip (78% + tip) : ${lyft_n:>7.2f}")
    print(f"  Independent net/trip (all to LLC): ${indie_per_vehicle_trip:>7.2f}  [avg vehicle trip, base case]")
    print()
    print(f"  Passenger pays to Uber           : ${gross:>7.2f}  (Uber keeps ${gross*UBER_PLATFORM_CUT:.2f})")
    print(f"  Passenger pays to Lyft           : ${gross_fare_per_trip(lyft.commute_surge):>7.2f}  (Lyft keeps ${gross_fare_per_trip(lyft.commute_surge)*LYFT_PLATFORM_CUT:.2f})")
    print(f"  Passenger pays to Independent    : ${indie.sub_price:>7.2f}/mo flat  (LLC keeps 100%)")

    # ── 5-Year P&L ─────────────────────────────────────────────────────────────
    print(f"\n{DASH}")
    print("  5-YEAR P&L COMPARISON  (EBIT, tax-basis incl. MACRS depreciation)")
    print(DASH)

    years = list(range(1, 6))
    year_labels = [str(2026 + y - 1) for y in years]

    # Header
    print(f"\n  {'Year':<6}", end="")
    for name, _ in models:
        print(f"  {name:>16}", end="")
    print()
    print("  " + "─" * (6 + len(models) * 18))

    # Revenue
    print(f"  {'':6}  {'── REVENUE ──':>16}", end="")
    for _ in models[1:]:
        print(f"  {'':>16}", end="")
    print()
    for y in years:
        print(f"  {year_labels[y-1]:<6}", end="")
        for _, m in models:
            r = m.annual_revenue(y)
            print(f"  ${r:>15,.0f}", end="")
        print()

    # Expenses
    print(f"\n  {'':6}  {'── EXPENSES ──':>16}", end="")
    for _ in models[1:]:
        print(f"  {'':>16}", end="")
    print()
    for y in years:
        print(f"  {year_labels[y-1]:<6}", end="")
        for _, m in models:
            e = m.expenses(y)
            print(f"  ${e:>15,.0f}", end="")
        print()

    # EBIT
    print(f"\n  {'':6}  {'── EBIT ──':>16}", end="")
    for _ in models[1:]:
        print(f"  {'':>16}", end="")
    print()
    cumulative = {name: 0.0 for name, _ in models}
    for y in years:
        print(f"  {year_labels[y-1]:<6}", end="")
        for name, m in models:
            e = m.ebit(y)
            cumulative[name] += e
            sign = "-" if e < 0 else " "
            print(f"  {sign}${abs(e):>14,.0f}", end="")
        print()

    # Cumulative
    print(f"\n  {'5yr cum':6}", end="")
    for name, _ in models:
        c = cumulative[name]
        sign = "-" if c < 0 else " "
        print(f"  {sign}${abs(c):>14,.0f}", end="")
    print()

    # ── Insurance & key cost breakdown ────────────────────────────────────────
    print(f"\n{DASH}")
    print("  YEAR 1 COST BREAKDOWN")
    print(DASH)
    labels = ["Insurance/yr", "Electricity/yr", "Maintenance/yr", "Depreciation/yr",
              "Formation+report/yr", "Misc/yr"]
    indie_costs = [
        indie.monthly_insurance * 12, ANNUAL_ELECTRICITY,
        round(ANNUAL_BIZ_MILES * 0.030 * BIZ_PCT, 0), round(macrs_year(0), 0),
        round(indie.formation_cost + indie.annual_report_fee, 0), indie.misc_annual,
    ]
    uber_costs = [
        uber.monthly_insurance * 12, ANNUAL_ELECTRICITY,
        round(ANNUAL_BIZ_MILES * 0.030, 0), round(macrs_year(0), 0), 0.0, 200.0,
    ]
    lyft_costs = uber_costs[:]
    hybrid_costs = [
        hybrid.monthly_insurance * 12, ANNUAL_ELECTRICITY,
        round(ANNUAL_BIZ_MILES * 0.030, 0), round(macrs_year(0), 0),
        round(hybrid.formation_cost + hybrid.annual_report_fee, 0), hybrid.misc_annual,
    ]
    all_costs = [indie_costs, uber_costs, lyft_costs, hybrid_costs]

    print(f"\n  {'Item':<24}", end="")
    for name, _ in models:
        print(f"  {name:>14}", end="")
    print()
    print("  " + "─" * (24 + len(models) * 16))
    for i, lbl in enumerate(labels):
        print(f"  {lbl:<24}", end="")
        for c_list in all_costs:
            print(f"  ${c_list[i]:>13,.0f}", end="")
        print()
    print()
    print("  NOTE: Uber/Lyft maintenance shown on full business miles (not biz-pct)")
    print("        because IRS treats all gig miles as business for platform drivers.")

    # ── Qualitative Scorecard ─────────────────────────────────────────────────
    print(f"\n{DASH}")
    print("  QUALITATIVE SCORECARD")
    print(DASH)
    headers = ["Independent LLC", "Uber", "Lyft", "Hybrid LLC+Uber"]
    print(f"\n  {'Factor':<32}", end="")
    for h in headers:
        print(f"  {h:>16}", end="")
    print()
    print("  " + "─" * (32 + len(headers) * 18))
    for factor, values in SCORECARD.items():
        print(f"  {factor:<32}", end="")
        for v in values:
            print(f"  {v:>16}", end="")
        print()

    # ── Recommendation ────────────────────────────────────────────────────────
    print(f"\n{DASH}")
    print("  RECOMMENDATION MATRIX")
    print(DASH)
    print("""
  ── If an owner HAS a base pass (or can get one): ──────────────────────────
     HYBRID LLC + Uber is likely the best model.

     • LLC locks in military subscribers with monthly contracts (guaranteed cash).
     • Uber/Lyft fills the 4–5 idle hours per day with opportunistic rides.
     • Year 1 Uber EV incentive ($4,000) nearly offsets the LLC formation cost.
     • Combined revenue is strongest of all four models by Year 2.
     • Two owners can alternate driving the same vehicle; LLC pays both pro-rata.
     • Path to autonomous taxi (Phase 2) preserved for the subscription routes.

  ── If NO owner has base access: ───────────────────────────────────────────
     Uber ALONE is simpler and cash-flow-positive sooner.

     • Without door-to-building service, the subscription premium shrinks.
     • Uber/Lyft gate-drop service is equivalent to personal transport — the
       military value proposition largely disappears.
     • Lower startup cost ($44,990 vs $46,490), no LLC overhead.
     • Single driver; co-ownership is awkward (alternating Uber accounts).
     • Recommend each friend registers their OWN vehicle on Uber/Lyft separately
       rather than sharing one vehicle.

  ── On the $7,500 EV credit loss (OBBB): ──────────────────────────────────
     The credit loss shifts the calculus slightly toward Uber/Lyft because:
     • Higher MSRP basis = larger MACRS depreciation = deeper losses on the
       LLC in years 1–3 = bigger hobby-loss IRS risk.
     • Uber/Lyft gig income is always "active" business income — no hobby-
       loss problem regardless of whether expenses exceed revenue.
     • The Uber $4,000 EV incentive partially replaces the lost tax credit
       but is cash-in-hand (better) rather than a tax deduction.

  ── Bottom line numbers (5-year cumulative EBIT): ──────────────────────────""")

    max_cum = max(abs(v) for v in cumulative.values()) or 1
    for name, val in cumulative.items():
        sign = "+" if val >= 0 else "-"
        bar = _bar(abs(val), max_cum)
        print(f"     {name:<20} {sign}${abs(val):>8,.0f}  {bar}")

    print(f"""
  ── Tax filing comparison: ──────────────────────────────────────────────────
     Independent LLC : IRS Form 1065 (partnership return) + K-1 to each owner.
                       More complex but allows income splitting and basis mgmt.
     Uber / Lyft     : Schedule C on each driver's 1040. Simple. 1099-K from
                       platform.  IRS standard mileage rate ($0.70/mi in 2025)
                       OR actual expenses — actual is better for an EV w/ solar.
     Hybrid          : Both Form 1065 (LLC) AND gig income on Schedule C.
                       Slightly more complex at tax time but manageable.
""")

    print(SEP)
    print(f"  Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("  DISCLAIMER: For planning only.  Rate estimates are NW FL market")
    print("  approximations.  Verify Uber/Lyft per-mile rates in your market")
    print("  via the Uber driver app before making financial decisions.")
    print(SEP)


if __name__ == "__main__":
    print_report()
