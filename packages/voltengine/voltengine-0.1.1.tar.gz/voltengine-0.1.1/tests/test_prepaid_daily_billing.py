import pytest

from voltengine.billing.prepaid_daily import PrepaidDailyBilling
from voltengine.accounting.ledger_engine import LedgerEngine
from voltengine.models.consumer import Consumer
from voltengine.models.meter import Meter
from voltengine.models.tariff import Tariff
from voltengine.models.period import Period


@pytest.fixture
def tariff():
    return Tariff(
        slabs=[
            {"upto": 50, "rate": 3.0},
            {"upto": 100, "rate": 4.5},
            {"upto": None, "rate": 6.0}
        ],
        fixed_charge=120,
        duty_rate=0.05,
        dps_monthly_rate=0.015,
        demand_rate=250,
        excess_demand_multiplier=1.5
    )


@pytest.fixture
def consumer():
    return Consumer(
        consumer_id="UT-001",
        wallet_balance=1000,
        arrear_balance=1200,
        load_kw=5,
        installment={
            "total": 1200,
            "daily": 20,
            "tenureDays": 60
        }
    )


@pytest.fixture
def meter():
    return Meter(
        daily_units=8,
        max_demand_kw=7
    )


@pytest.fixture
def period():
    return Period(days=30)


@pytest.fixture
def ledger():
    return LedgerEngine()


def test_prepaid_daily_billing_with_excess_demand(
    tariff, consumer, meter, period, ledger
):
    billing = PrepaidDailyBilling()

    result = billing.run(
        consumer=consumer,
        meter=meter,
        tariff=tariff,
        period=period,
        ledger=ledger,
        date="2025-01-01"
    )

    # -----------------------------
    # BASIC STRUCTURE VALIDATION
    # -----------------------------
    assert "totalDeduction" in result
    assert "breakup" in result
    assert "state" in result

    # -----------------------------
    # FINANCIAL VALIDATION
    # -----------------------------
    assert round(result["totalDeduction"], 2) == 799.20
    assert consumer.wallet_balance == pytest.approx(200.8, 0.01)
    assert consumer.arrear_balance == pytest.approx(1180.6, 0.01)

    # -----------------------------
    # BREAKUP VALIDATION
    # -----------------------------
    breakup = result["breakup"]

    assert breakup["energy"] == 24.0
    assert breakup["fixed"] == 4.0
    assert breakup["duty"] == 1.2
    assert breakup["dps"] == pytest.approx(0.6, 0.01)
    assert breakup["installment"] == 20

    assert breakup["excessDemand"]["excessKW"] == 2
    assert breakup["excessDemand"]["penalty"] == 750.0

    # -----------------------------
    # LEDGER VALIDATION
    # -----------------------------
    entries = ledger.snapshot()
    types = [e["type"] for e in entries]

    assert "ENERGY" in types
    assert "FIXED" in types
    assert "DUTY" in types
    assert "DPS" in types
    assert "INSTALLMENT_RECOVERY" in types
    assert "EXCESS_DEMAND_PENALTY" in types

    assert len(entries) == 6
