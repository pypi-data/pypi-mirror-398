#!/usr/bin/env python3
"""Generate fake fixture files for tests.

This script creates fake API response fixtures using fictional stock tickers
(FAKE1-FAKE5) with realistic random values. The structure is based on the
original fixture files in .responses/ but with randomized, non-proprietary data.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Directories
SCRIPT_DIR = Path(__file__).parent
PACKAGE_DIR = SCRIPT_DIR.parent
ORIGINAL_RESPONSES_DIR = PACKAGE_DIR / ".responses"
TEST_DATA_DIR = PACKAGE_DIR / "tests" / "data"

# Fake companies
FAKE_COMPANIES = {
    "FAKE1": {
        "name": "Fake Company One",
        "short_name": "FakeOne Inc",
        "sector": "TestSector",
        "group": "TestGroup",
        "subindustry": "TestSubindustry",
        "country": "USA",
        "currency": "USD",
    },
    "FAKE2": {
        "name": "Fake Company Two",
        "short_name": "FakeTwo Corp",
        "sector": "TestSector",
        "group": "TestGroup",
        "subindustry": "TestSubindustry",
        "country": "USA",
        "currency": "USD",
    },
    "FAKE3": {
        "name": "Fake Company Three",
        "short_name": "FakeThree Ltd",
        "sector": "TestSector",
        "group": "TestGroup",
        "subindustry": "TestSubindustry",
        "country": "USA",
        "currency": "USD",
    },
    "FAKE4": {
        "name": "Fake Company Four",
        "short_name": "FakeFour Inc",
        "sector": "TestSector",
        "group": "TestGroup",
        "subindustry": "TestSubindustry",
        "country": "USA",
        "currency": "USD",
    },
    "FAKE5": {
        "name": "Fake Company Five",
        "short_name": "FakeFive Corp",
        "sector": "TestSector",
        "group": "TestGroup",
        "subindustry": "TestSubindustry",
        "country": "USA",
        "currency": "USD",
    },
}

# Set seed for reproducibility
random.seed(42)


def random_price(base: float = 100.0) -> float:
    """Generate a random stock price."""
    return round(random.uniform(base * 0.5, base * 1.5), 2)


def random_percentage() -> float:
    """Generate a random percentage."""
    return round(random.uniform(0, 100), 2)


def random_score() -> int:
    """Generate a random score 1-10."""
    return random.randint(1, 10)


def random_ratio() -> str:
    """Generate a random financial ratio."""
    return f"{random.uniform(0.1, 50.0):.2f}"


def random_date(start_year: int = 2020, end_year: int = 2025) -> str:
    """Generate a random date string."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    random_days = random.randint(0, delta)
    date = start + timedelta(days=random_days)
    return date.strftime("%Y-%m-%d")


def random_amount() -> str:
    """Generate a random dividend amount."""
    return f"{random.uniform(0.10, 2.00):.2f}"


def generate_summary(ticker: str) -> dict:
    """Generate a fake summary response."""
    company = FAKE_COMPANIES[ticker]
    base_price = random.uniform(50, 300)

    return {
        "summary": {
            "general": {
                "company": company["name"],
                "price": round(base_price, 2),
                "timestamp": str(int(datetime.now().timestamp())),
                "gf_score": str(random.randint(50, 99)),
                "rank_financial_strength": str(random_score()),
                "rank_profitability": str(random_score()),
                "rank_gf_value": str(random_score()),
                "rank_growth": str(random_score()),
                "rank_momentum": str(random_score()),
                "supersector": "Sensitive",
                "sector": company["sector"],
                "group": company["group"],
                "subindustry": company["subindustry"],
                "risk_assessment": "Medium Risk: For testing purposes only",
                "gf_valuation": "Fairly Valued",
                "valuation_box_status": "Mixed Valued",
                "desc": f"{company['name']} is a fictional company created for testing purposes. "
                "This company does not exist in the real world and any resemblance to actual "
                "companies is purely coincidental.",
                "short_desc": f"{company['name']} is a fictional test company.",
                "rating": "3.5",
                "currency": "$",
                "country": company["country"],
                "percentage_of_13f_buys": random_percentage(),
                "percentage_of_13f_sells": random_percentage(),
                "percentage_of_13f_holds": random_percentage(),
                "percentage_of_mutual_fund_buys": random_percentage(),
                "percentage_of_mutual_fund_sells": random_percentage(),
                "percentage_of_mutual_fund_holds": random_percentage(),
                "percentage_of_etf_buys": random_percentage(),
                "percentage_of_etf_sells": random_percentage(),
                "percentage_of_etf_holds": random_percentage(),
                "percentage_of_premium_guru_buys": random_percentage(),
                "percentage_of_premium_guru_sells": random_percentage(),
                "percentage_of_premium_guru_holds": random_percentage(),
                "percentage_of_premiumplus_guru_buys": random_percentage(),
                "percentage_of_premiumplus_guru_sells": random_percentage(),
                "percentage_of_premiumplus_guru_holds": random_percentage(),
            },
            "chart": {
                "GF Value": f"{base_price * random.uniform(0.8, 1.2):.2f}",
                "Earnings Power Value": f"{base_price * random.uniform(0.3, 0.6):.2f}",
                "Net-Net Working Capital": f"{random.uniform(-20, 10):.2f}",
                "Net Current Asset Value": f"{random.uniform(-15, 15):.2f}",
                "Tangible Book": f"{random.uniform(1, 50):.2f}",
                "Projected FCF": f"{base_price * random.uniform(0.3, 0.5):.2f}",
                "DCF (FCF Based)": f"{base_price * random.uniform(0.4, 0.7):.2f}",
                "DCF (Earnings Based)": f"{base_price * random.uniform(0.5, 0.8):.2f}",
                "Median P/S Value": f"{base_price * random.uniform(0.5, 0.9):.2f}",
                "Graham Number": f"{random.uniform(10, 100):.2f}",
                "Peter Lynch Value": f"{base_price * random.uniform(0.3, 0.5):.2f}",
            },
            "ratio": {
                "Cash Ratio": _create_ratio_entry(0.33),
                "Current Ratio": _create_ratio_entry(1.2),
                "Quick Ratio": _create_ratio_entry(0.9),
                "P/E(ttm)": _create_ratio_entry(25.0),
                "F-Score": _create_ratio_entry(7, is_int=True),
                "Forward P/E": _create_ratio_entry(22.0),
                "P/B": _create_ratio_entry(5.0),
                "P/S": _create_ratio_entry(3.0),
            },
        }
    }


def _create_ratio_entry(base_value: float, is_int: bool = False) -> dict:
    """Create a ratio entry with industry and historical data."""
    value = base_value * random.uniform(0.8, 1.2)
    if is_int:
        value = int(value)
        value_str = str(value)
    else:
        value_str = f"{value:.2f}"

    return {
        "indu": {
            "global_rank": str(random.randint(100, 2000)),
            "indu_med": f"{base_value * random.uniform(0.9, 1.1):.2f}",
            "indu_tot": str(random.randint(1000, 3000)),
        },
        "value": value_str,
        "status": random.randint(0, 1),
        "his": {
            "low": f"{base_value * 0.5:.2f}" if not is_int else str(int(base_value * 0.5)),
            "high": f"{base_value * 1.5:.2f}" if not is_int else str(int(base_value * 1.5)),
            "med": f"{base_value:.2f}" if not is_int else str(int(base_value)),
        },
    }


def generate_analyst_estimate(ticker: str) -> dict:
    """Generate fake analyst estimates."""
    base_revenue = random.uniform(10000, 500000)
    base_eps = random.uniform(1, 10)

    return {
        "annual": {
            "date": ["202509", "202609", "202709"],
            "revenue_estimate": [
                round(base_revenue, 2),
                round(base_revenue * 1.08, 2),
                round(base_revenue * 1.15, 2),
            ],
            "ebit_estimate": [
                round(base_revenue * 0.3, 2),
                round(base_revenue * 0.32, 2),
                round(base_revenue * 0.34, 2),
            ],
            "ebitda_estimate": [
                round(base_revenue * 0.35, 2),
                round(base_revenue * 0.37, 2),
                round(base_revenue * 0.39, 2),
            ],
            "net_income_estimate": [
                round(base_revenue * 0.25, 2),
                round(base_revenue * 0.27, 2),
                round(base_revenue * 0.29, 2),
            ],
            "per_share_eps_estimate": [
                round(base_eps, 2),
                round(base_eps * 1.1, 2),
                round(base_eps * 1.2, 2),
            ],
            "eps_nri_estimate": [
                round(base_eps * 1.01, 2),
                round(base_eps * 1.11, 2),
                round(base_eps * 1.21, 2),
            ],
            "dividend_estimate": [
                round(base_eps * 0.12, 2),
                round(base_eps * 0.13, 2),
                round(base_eps * 0.14, 2),
            ],
            "book_value_per_share_estimate": [
                round(base_eps * 0.7, 2),
                round(base_eps * 0.8, 2),
                round(base_eps * 0.9, 2),
            ],
            "pretax_income_estimate": [
                round(base_revenue * 0.3, 2),
                round(base_revenue * 0.32, 2),
                round(base_revenue * 0.34, 2),
            ],
        }
    }


def generate_dividend(ticker: str) -> list:
    """Generate fake dividend history."""
    dividends = []
    base_amount = random.uniform(0.2, 1.0)
    start_date = datetime(2020, 1, 15)

    for i in range(20):
        ex_date = start_date + timedelta(days=90 * i)
        pay_date = ex_date + timedelta(days=5)
        amount = base_amount * (1 + 0.02 * (i // 4))

        dividends.append(
            {
                "amount": f"{amount:.2f}",
                "ex_date": ex_date.strftime("%Y-%m-%d"),
                "record_date": ex_date.strftime("%Y-%m-%d"),
                "pay_date": pay_date.strftime("%Y-%m-%d"),
                "type": "Cash Div.",
                "currency": "USD",
            }
        )

    return dividends


def generate_financials(ticker: str) -> dict:
    """Generate fake financials data."""
    fiscal_years = [f"{2020 + i}-09" for i in range(5)] + ["TTM"]
    num_years = len(fiscal_years)

    base_revenue = random.uniform(50000, 400000)
    revenues = [round(base_revenue * (1.1**i), 3) for i in range(num_years)]

    return {
        "financials": {
            "financial_template_parameters": {
                "ind_template": "N",
                "REITs": "N",
                "IsDirect": "Indirect Method",
                "financial_report_frequency": "Quarterly",
            },
            "annuals": {
                "Fiscal Year": fiscal_years,
                "Preliminary": [0] * num_years,
                "per_share_data_array": {
                    "Revenue per Share": [f"{r / 1000:.3f}" for r in revenues],
                    "Earnings per Share (Diluted)": [f"{r * 0.002:.3f}" for r in revenues],
                    "Book Value per Share": [f"{r * 0.0001:.3f}" for r in revenues],
                    "Free Cash Flow per Share": [f"{r * 0.0015:.3f}" for r in revenues],
                },
                "income_statement": {
                    "Revenue": revenues,
                    "Gross Profit": [round(r * 0.4, 3) for r in revenues],
                    "Operating Income": [round(r * 0.3, 3) for r in revenues],
                    "Net Income": [round(r * 0.2, 3) for r in revenues],
                },
                "balance_sheet": {
                    "Total Assets": [round(r * 0.8, 3) for r in revenues],
                    "Total Liabilities": [round(r * 0.5, 3) for r in revenues],
                    "Total Equity": [round(r * 0.3, 3) for r in revenues],
                    "Cash and Cash Equivalents": [round(r * 0.1, 3) for r in revenues],
                },
                "cashflow_statement": {
                    "Operating Cash Flow": [round(r * 0.25, 3) for r in revenues],
                    "Capital Expenditure": [round(r * -0.05, 3) for r in revenues],
                    "Free Cash Flow": [round(r * 0.2, 3) for r in revenues],
                },
            },
        }
    }


def generate_insider(ticker: str) -> dict:
    """Generate fake insider trades."""
    positions = [
        "CEO",
        "CFO",
        "Director",
        "Senior Vice President",
        "General Counsel",
    ]
    fake_names = [
        "SMITH JOHN",
        "DOE JANE",
        "JOHNSON ROBERT",
        "WILLIAMS SARAH",
        "BROWN MICHAEL",
    ]

    trades = []
    for _i in range(10):
        trade_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
        trans_shares = random.randint(1000, 50000)
        price = random.uniform(50, 300)

        trades.append(
            {
                "position": random.choice(positions),
                "date": trade_date.strftime("%Y-%m-%d"),
                "type": random.choice(["S", "P"]),
                "trans_share": f"{trans_shares:,}",
                "final_share": f"{trans_shares * random.randint(2, 10):,}",
                "price": f"{price:.2f}",
                "cost": f"{trans_shares * price / 1000:.1f}",
                "insider": random.choice(fake_names),
                "change": f"{random.uniform(1, 15):.2f}",
            }
        )

    return {ticker: trades}


def generate_keyratios(ticker: str) -> dict:
    """Generate fake key ratios."""
    company = FAKE_COMPANIES[ticker]

    return {
        "Basic": {
            "Price Updated Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S (EST)"),
            "Company": company["name"],
        },
        "Fundamental": {
            "Currency": "USD",
            "Reporting Currency": "USD",
            "Total Assets (Current)": f"{random.uniform(10000, 500000):.3f}",
            "Book Value per Share": f"{random.uniform(1, 50):.2f}",
            "Cash-to-Debt": f"{random.uniform(0.2, 1.0):.2f}",
            "Cash-to-Debt (10y High)": f"{random.uniform(0.5, 1.5):.2f}",
            "Cash-to-Debt (10y Low)": f"{random.uniform(0.1, 0.5):.2f}",
            "Cash-to-Debt (10y Median)": f"{random.uniform(0.3, 0.8):.2f}",
            "Share Class Description": "Ordinary Shares",
            "Headquarter Country": company["country"],
            "Current Ratio": f"{random.uniform(0.8, 2.0):.2f}",
            "Current Ratio (10y High)": f"{random.uniform(1.5, 3.0):.2f}",
            "Current Ratio (10y Low)": f"{random.uniform(0.5, 1.0):.2f}",
            "Current Ratio (10y Median)": f"{random.uniform(1.0, 1.5):.2f}",
            "EPS (TTM)": f"{random.uniform(1, 10):.3f}",
            "Enterprise Value": f"{random.uniform(100000, 5000000):.3f}",
            "Enterprise Value ($M)": f"{random.uniform(100000, 5000000):.3f}",
            "Piotroski F-Score": random.randint(4, 9),
            "Piotroski F-Score (10y High)": random.randint(7, 9),
            "Piotroski F-Score (10y Low)": random.randint(3, 5),
            "Piotroski F-Score (10y Median)": random.randint(5, 7),
            "Market Cap ($M)": f"{random.uniform(100000, 4000000):.3f}",
            "Primary Exchange": "NAS",
            "Primary Symbol": ticker,
            "Financial Strength": random.randint(5, 9),
            "Financial Strength (10y High)": f"{random.randint(7, 10):.2f}",
            "Financial Strength (10y Low)": f"{random.randint(4, 6):.2f}",
            "Financial Strength (10y Median)": f"{random.randint(5, 8):.2f}",
            "ROA %": f"{random.uniform(5, 35):.2f}",
            "ROE %": f"{random.uniform(10, 200):.2f}",
            "Predictability Rank": f"{random.uniform(2, 5):.1f}",
        },
    }


def generate_price(ticker: str) -> list:
    """Generate fake price history."""
    prices = []
    base_price = random.uniform(10, 100)
    start_date = datetime(2020, 1, 1)

    for i in range(250):  # ~1 year of trading days
        trade_date = start_date + timedelta(days=i)
        if trade_date.weekday() >= 5:  # Skip weekends
            continue
        price = base_price * (1 + 0.0005 * i) * random.uniform(0.98, 1.02)
        prices.append([trade_date.strftime("%m-%d-%Y"), round(price, 6)])

    return prices


# Mapping of category to generator function
GENERATORS = {
    "summary": generate_summary,
    "analyst_estimate": generate_analyst_estimate,
    "dividend": generate_dividend,
    "financials": generate_financials,
    "insider": generate_insider,
    "keyratios": generate_keyratios,
    "price": generate_price,
}


def main() -> None:
    """Generate all fake fixture files."""
    print("Generating fake fixture files...")

    for category, generator in GENERATORS.items():
        category_dir = TEST_DATA_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        for ticker in FAKE_COMPANIES:
            # Reset random seed for each ticker to get consistent but different data
            random.seed(hash(f"{category}:{ticker}") % (2**32))

            data = generator(ticker)
            output_file = category_dir / f"{ticker}.json"

            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

            print(f"  Created {output_file.relative_to(PACKAGE_DIR)}")

    print(f"\nGenerated {len(FAKE_COMPANIES) * len(GENERATORS)} fixture files.")


if __name__ == "__main__":
    main()
