"""
Unified Master Statement Synthesizer
Learns patterns from:
1. Real SBI bank statement PDF extractions (real Indian UPI formats, RRNs, banks, merchants)
2. Kaggle Bank Statements (banking transactions, NEFT, ATM, fuel stations, bill desks)
3. Kaggle Daily Household Transactions (real household items, grocery prices, medicine, maid, milk, local transport)

Produces: ONE comprehensive, realistic 12-month statement CSV for our salaried user.
It includes:
- Authentic Indian banking narrations (UPI RRNs, IFSC/bank handles, NEFT, ACH, POS, ATM)
- Real daily living expenses learned from real households (milk, local auto, snacks, medicine, maid, groceries)
- The complete financial baseline required for our engines (Salary, EMI, Rent, Subscriptions, Insurance, Tax)
- Mathematically consistent running balances.
"""

import random
from datetime import datetime, timedelta
import pandas as pd

random.seed(42)

# Learned from Real SBI + Kaggle datasets
UPI_BANKS = ['SBIN', 'HDFC', 'ICIC', 'YESB', 'UTIB', 'PUNB', 'AIRP', 'NSPB']
PAYMENT_APPS = ['paytm', 'gpay', 'phonepe', 'bharatpe', 'cred']

# Real household items learned from Daily_Household_Transactions.csv
DAILY_ITEMS = [
    # (narration_name, min_amt, max_amt, category, subcategory)
    ("Amul Milk Booth / Dairy Point", 34.0, 72.0, "Variable Essentials", "Groceries & Supplies"),
    ("Blinkit Commerce Pvt Ltd", 180.0, 850.0, "Variable Essentials", "Groceries & Supplies"),
    ("Zepto Quick Delivery", 120.0, 640.0, "Variable Essentials", "Groceries & Supplies"),
    ("Local Kirana & Provisions", 85.0, 450.0, "Variable Essentials", "Groceries & Supplies"),
    ("Fresh Fruits and Vegetables Stall", 60.0, 320.0, "Variable Essentials", "Groceries & Supplies"),
    ("Namma Auto / Local Auto Fare", 30.0, 150.0, "Variable Essentials", "Ride Hailing & Auto"),
    ("BMRCL Namma Metro Bangalore", 30.0, 60.0, "Variable Essentials", "Public Transit & Metro"),
    ("SLN Tea Stall & Bakery", 15.0, 45.0, "Discretionary", "Food Delivery & Dining"),
    ("Idli Dosa Medu Vada Point", 40.0, 90.0, "Discretionary", "Food Delivery & Dining"),
    ("Chai Point / Tea Post", 25.0, 65.0, "Discretionary", "Food Delivery & Dining"),
    ("Swiggy Food Delivery", 240.0, 680.0, "Discretionary", "Food Delivery & Dining"),
    ("Zomato Online Orders", 290.0, 820.0, "Discretionary", "Food Delivery & Dining"),
    ("Apollo Pharmacy / MedPlus", 45.0, 380.0, "Variable Essentials", "Healthcare & Pharmacy"),
    ("Printout Xerox & Stationery", 20.0, 75.0, "Variable Essentials", "Education & Office"),
]

PEER_NAMES = [
    "DINESH KUMAR S", "MOHAMED JUNAIDEEN", "RAHUL SHARMA", "PRIYA V",
    "ADITYA VERMA", "PRADIP K", "JOTIKA B", "SUMANTA P", "MALATHI R"
]

def generate_upi_narration(merchant_name, is_dr=True):
    rrn = random.randint(100000000000, 999999999999)
    bank = random.choice(UPI_BANKS)
    app = random.choice(PAYMENT_APPS)
    short_name = merchant_name[:12].replace(' ', '_').upper()
    dr_cr = "DR" if is_dr else "CR"
    return f"UPI/{dr_cr}/{rrn}/{short_name}/{bank}/{app}.{random.randint(100,999)}/Payme"

def synthesize_master_statement():
    records = []
    # Starting balance on 2025-11-01
    current_balance = 168450.75
    start_date = datetime(2025, 11, 1)
    
    # 12 Months: Nov 2025 to Oct 2026
    months = []
    curr = start_date
    for _ in range(12):
        months.append((curr.year, curr.month))
        curr = datetime(curr.year + (1 if curr.month == 12 else 0), 1 if curr.month == 12 else curr.month + 1, 1)

    for yr, mo in months:
        # === 1. SALARY CREDIT (1st of month) ===
        sal_date = datetime(yr, mo, 1)
        sal_amt = 105000.00
        current_balance += sal_amt
        records.append({
            'date': sal_date.strftime('%Y-%m-%d'),
            'narration': f"NEFT CR-TECHCORP SOLUTIONS PVT LTD-SALARY-{sal_date.strftime('%b%y').upper()}-009841829",
            'debit': 0.0,
            'credit': sal_amt,
            'balance': current_balance,
            'mode': 'NEFT',
            'category': 'Income',
            'sub_category': 'Salary'
        })
        
        # Annual Bonus in Diwali / Oct 2026
        if yr == 2026 and mo == 10:
            b_date = datetime(2026, 10, 24)
            b_amt = 50000.00
            current_balance += b_amt
            records.append({
                'date': b_date.strftime('%Y-%m-%d'),
                'narration': "NEFT CR-TECHCORP SOLUTIONS PVT LTD-FESTIVE PERFORMANCE BONUS",
                'debit': 0.0,
                'credit': b_amt,
                'balance': current_balance,
                'mode': 'NEFT',
                'category': 'Income',
                'sub_category': 'Bonus'
            })

        # === 2. RENT TRANSFER (2nd of month) ===
        rent_date = datetime(yr, mo, 2)
        rent_amt = 26000.00
        current_balance -= rent_amt
        records.append({
            'date': rent_date.strftime('%Y-%m-%d'),
            'narration': "UPI/DR/481928410291/RAJESH KUMAR/HDFC/rajesh.landlord/RENT",
            'debit': rent_amt,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'UPI',
            'category': 'Fixed Expenses',
            'sub_category': 'Rent'
        })
        
        # === 3. MAID SALARY (Learned from Daily Household dataset - 3rd of month) ===
        maid_date = datetime(yr, mo, 3)
        maid_amt = 3500.00
        current_balance -= maid_amt
        records.append({
            'date': maid_date.strftime('%Y-%m-%d'),
            'narration': generate_upi_narration("LAKSHMI MAID HOUSEKEEPING"),
            'debit': maid_amt,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'UPI',
            'category': 'Fixed Expenses',
            'sub_category': 'Domestic Help'
        })

        # === 4. CAR LOAN EMI (5th of month) ===
        emi_date = datetime(yr, mo, 5)
        emi_amt = 24800.00
        current_balance -= emi_amt
        records.append({
            'date': emi_date.strftime('%Y-%m-%d'),
            'narration': "ACH D-HDFC BANK LTD-AUTO LOAN EMI-LN49281984",
            'debit': emi_amt,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'ACH',
            'category': 'Fixed Expenses',
            'sub_category': 'Loan EMIs'
        })

        # === 5. UTILITIES (Electricity, Broadband, Mobile Recharge) ===
        elec_date = datetime(yr, mo, 7)
        elec_amt = round(random.uniform(1450.0, 2150.0), 2)
        current_balance -= elec_amt
        records.append({
            'date': elec_date.strftime('%Y-%m-%d'),
            'narration': "UPI/DR/391048129481/BESCOM ELECTRICITY/SBIN/bescom.bill/Pay",
            'debit': elec_amt,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'UPI',
            'category': 'Fixed Expenses',
            'sub_category': 'Utilities'
        })

        bb_date = datetime(yr, mo, 8)
        bb_amt = 1179.00
        current_balance -= bb_amt
        records.append({
            'date': bb_date.strftime('%Y-%m-%d'),
            'narration': "UPI/DR/481940120194/ACT FIBERNET/HDFC/actcorp.bill/Pay",
            'debit': bb_amt,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'UPI',
            'category': 'Fixed Expenses',
            'sub_category': 'Utilities'
        })

        # === 6. MUTUAL FUND SIP (10th of month) ===
        sip_date = datetime(yr, mo, 10)
        sip_amt = 12000.00
        current_balance -= sip_amt
        records.append({
            'date': sip_date.strftime('%Y-%m-%d'),
            'narration': "ACH D-NIPPON INDIA MUTUAL FUND-SIP AUTO DEBIT-00941824",
            'debit': sip_amt,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'ACH',
            'category': 'Investments',
            'sub_category': 'Mutual Funds'
        })

        # === 7. RECURRING SUBSCRIPTIONS & TRAPS ===
        # Netflix (Price Creep: 499 -> 649 from May)
        nflx_date = datetime(yr, mo, 14)
        nflx_amt = 499.00 if (yr == 2025 or (yr == 2026 and mo < 5)) else 649.00
        current_balance -= nflx_amt
        records.append({
            'date': nflx_date.strftime('%Y-%m-%d'),
            'narration': "POS DEBIT-NETFLIX ENTERTAINMENT SERVICES-MUMBAI",
            'debit': nflx_amt,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'POS',
            'category': 'Fixed Expenses',
            'sub_category': 'Subscriptions'
        })

        # Duplicate: Spotify (119) & YouTube Premium (149)
        spot_date = datetime(yr, mo, 16)
        current_balance -= 119.00
        records.append({
            'date': spot_date.strftime('%Y-%m-%d'),
            'narration': "UPI/DR/948192019481/Spotify India/ICIC/spotify.pay/Monthly",
            'debit': 119.00,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'UPI',
            'category': 'Fixed Expenses',
            'sub_category': 'Subscriptions'
        })

        yt_date = datetime(yr, mo, 17)
        current_balance -= 149.00
        records.append({
            'date': yt_date.strftime('%Y-%m-%d'),
            'narration': "POS DEBIT-GOOGLE*YOUTUBE PREMIUM-G.CO/HELPPAY",
            'debit': 149.00,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'POS',
            'category': 'Fixed Expenses',
            'sub_category': 'Subscriptions'
        })

        # Zombie Subscription: Cult.Fit Gym Rs 2,499
        gym_date = datetime(yr, mo, 20)
        current_balance -= 2499.00
        records.append({
            'date': gym_date.strftime('%Y-%m-%d'),
            'narration': "ACH D-CULT FIT HEALTHCARE PVT LTD-MONTHLY SUB",
            'debit': 2499.00,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'ACH',
            'category': 'Fixed Expenses',
            'sub_category': 'Subscriptions'
        })

        # Apple iCloud Rs 75
        cloud_date = datetime(yr, mo, 22)
        current_balance -= 75.00
        records.append({
            'date': cloud_date.strftime('%Y-%m-%d'),
            'narration': "POS DEBIT-APPLE.COM/BILL-ITUNES-IRELAND",
            'debit': 75.00,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'POS',
            'category': 'Fixed Expenses',
            'sub_category': 'Subscriptions'
        })

        # === 8. INSURANCE AUDIT (Quarterly LIC Endowment) ===
        if mo in (1, 4, 7, 10):
            lic_date = datetime(yr, mo, 18)
            current_balance -= 3000.00
            records.append({
                'date': lic_date.strftime('%Y-%m-%d'),
                'narration': "ACH D-LIFE INSURANCE CORP OF INDIA-LIC PREMIUM-094182918",
                'debit': 3000.00,
                'credit': 0.0,
                'balance': current_balance,
                'mode': 'ACH',
                'category': 'Fixed Expenses',
                'sub_category': 'Insurance Premiums'
            })

        # Out-of-pocket medical events (Feb, May, Aug)
        if mo == 2:
            med_amt = 12400.00
            current_balance -= med_amt
            records.append({
                'date': datetime(yr, mo, 15).strftime('%Y-%m-%d'),
                'narration': "POS DEBIT-MANIPAL HOSPITAL OPD & DIAGNOSTICS-BANGALORE",
                'debit': med_amt,
                'credit': 0.0,
                'balance': current_balance,
                'mode': 'POS',
                'category': 'Variable Essentials',
                'sub_category': 'Healthcare & Pharmacy'
            })
        elif mo == 5:
            med_amt = 16800.00
            current_balance -= med_amt
            records.append({
                'date': datetime(yr, mo, 21).strftime('%Y-%m-%d'),
                'narration': "POS DEBIT-APOLLO HOSPITALS EMERGENCY & CONSULT",
                'debit': med_amt,
                'credit': 0.0,
                'balance': current_balance,
                'mode': 'POS',
                'category': 'Variable Essentials',
                'sub_category': 'Healthcare & Pharmacy'
            })
        elif mo == 8:
            med_amt = 7300.00
            current_balance -= med_amt
            records.append({
                'date': datetime(yr, mo, 12).strftime('%Y-%m-%d'),
                'narration': "UPI/DR/849182910481/APOLLO PHARMACY BANGALORE/HDFC/apollopharm/Pay",
                'debit': med_amt,
                'credit': 0.0,
                'balance': current_balance,
                'mode': 'UPI',
                'category': 'Variable Essentials',
                'sub_category': 'Healthcare & Pharmacy'
            })

        # === 9. ATM CASH WITHDRAWAL (Learned from Kaggle Bank Statement: 1-2 times/month) ===
        atm_date = datetime(yr, mo, 11)
        current_balance -= 2000.00
        records.append({
            'date': atm_date.strftime('%Y-%m-%d'),
            'narration': "ATM WDL-SBI ATM KORAMANGALA BANGALORE-00982",
            'debit': 2000.00,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'ATM',
            'category': 'Daily Micro-Spends',
            'sub_category': 'Cash Withdrawal'
        })

        # === 10. FUEL / PETROL (Learned from Kaggle: Gas filling stations) ===
        fuel_date1 = datetime(yr, mo, 6)
        f_amt1 = round(random.uniform(1800.0, 2400.0), 2)
        current_balance -= f_amt1
        records.append({
            'date': fuel_date1.strftime('%Y-%m-%d'),
            'narration': "POS DEBIT-SHELL PETROL PUMP KORAMANGALA BANGALORE",
            'debit': f_amt1,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'POS',
            'category': 'Variable Essentials',
            'sub_category': 'Fuel & Commute'
        })

        fuel_date2 = datetime(yr, mo, 22)
        f_amt2 = round(random.uniform(1600.0, 2200.0), 2)
        current_balance -= f_amt2
        records.append({
            'date': fuel_date2.strftime('%Y-%m-%d'),
            'narration': "POS DEBIT-HPCL FUEL STATION INDIRANAGAR",
            'debit': f_amt2,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'POS',
            'category': 'Variable Essentials',
            'sub_category': 'Fuel & Commute'
        })

        # === 11. DAILY LIVING SPENDS (Learned from Daily Household Dataset + Real SBI UPI) ===
        days_in_month = 28 if mo == 2 else (30 if mo in (4, 6, 9, 11) else 31)
        for day in range(1, days_in_month + 1):
            d_obj = datetime(yr, mo, day)
            is_weekend = d_obj.weekday() in (4, 5, 6)

            # Daily item (Milk/Chai/Metro/Grocery) - 1 to 2 times a day
            item_name, min_a, max_a, cat, sub = random.choice(DAILY_ITEMS)
            amt = round(random.uniform(min_a, max_a), 2)
            current_balance -= amt
            records.append({
                'date': d_obj.strftime('%Y-%m-%d'),
                'narration': generate_upi_narration(item_name),
                'debit': amt,
                'credit': 0.0,
                'balance': current_balance,
                'mode': 'UPI',
                'category': cat,
                'sub_category': sub
            })

            # Random small peer payment / split with friend (every 3-4 days)
            if day % 4 == 0:
                p_name = random.choice(PEER_NAMES)
                p_amt = round(random.uniform(40.0, 350.0), 2)
                current_balance -= p_amt
                records.append({
                    'date': d_obj.strftime('%Y-%m-%d'),
                    'narration': generate_upi_narration(p_name),
                    'debit': p_amt,
                    'credit': 0.0,
                    'balance': current_balance,
                    'mode': 'UPI',
                    'category': 'Daily Micro-Spends',
                    'sub_category': 'Peer Transfer / Local Pay'
                })

            # Weekend dining / pub outings
            if is_weekend and random.random() < 0.65:
                w_merchant = random.choice(["Toit Brewpub", "Truffles", "Meghana Biryani", "Third Wave Coffee"])
                w_amt = round(random.uniform(450.0, 1850.0), 2)
                current_balance -= w_amt
                records.append({
                    'date': d_obj.strftime('%Y-%m-%d'),
                    'narration': generate_upi_narration(w_merchant),
                    'debit': w_amt,
                    'credit': 0.0,
                    'balance': current_balance,
                    'mode': 'UPI',
                    'category': 'Discretionary',
                    'sub_category': 'Food Delivery & Dining'
                })

            # Occasional Amazon shopping (twice a month)
            if day in (12, 25) and random.random() < 0.60:
                shop_amt = round(random.uniform(599.0, 2899.0), 2)
                current_balance -= shop_amt
                records.append({
                    'date': d_obj.strftime('%Y-%m-%d'),
                    'narration': "POS DEBIT-AMAZON SELLER SERVICES BANGALORE-009841",
                    'debit': shop_amt,
                    'credit': 0.0,
                    'balance': current_balance,
                    'mode': 'POS',
                    'category': 'Discretionary',
                    'sub_category': 'Shopping & E-Commerce'
                })

    df = pd.DataFrame(records)
    df = df.sort_values(by=['date']).reset_index(drop=True)

    # Recalculate mathematical running balance
    bal = 168450.75
    running = []
    for _, row in df.iterrows():
        bal = bal + row['credit'] - row['debit']
        running.append(round(bal, 2))
    df['balance'] = running

    return df

if __name__ == '__main__':
    df = synthesize_master_statement()
    out_file = 'master_salaried_statement.csv'
    df.to_csv(out_file, index=False)
    print(f"Generated {len(df)} transactions spanning {df['date'].min()} to {df['date'].max()}")
    print(f"Saved to '{out_file}'.")
    print(f"Total Inflow:  Rs {df['credit'].sum():,.2f}")
    print(f"Total Outflow: Rs {df['debit'].sum():,.2f}")
    print(f"Net Savings:   Rs {(df['credit'].sum() - df['debit'].sum()):,.2f}")
    print(f"Final Balance: Rs {df['balance'].iloc[-1]:,.2f}")
    print("\nCategory Distribution:")
    print(df['category'].value_counts())
