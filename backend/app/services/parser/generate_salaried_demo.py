"""
Salaried Demo Persona Statement Generator
Generates a mathematically airtight, 12-month bank statement (Nov 2025 - Oct 2026)
for 'Rohan Sharma' (29, Sr. Software Engineer, Bangalore)

Seeded with Golden Test Cases for Exhibition:
1. Income: Net Salary Rs 1,05,000 on 1st + Diwali Bonus Rs 50,000 in Oct
2. Fixed EMIs: HDFC Car Loan EMI Rs 24,800 on the 5th
3. Rent: Rs 26,000 to Landlord on the 2nd
4. Duplicate Subscription: Spotify (Rs 119) + YouTube Premium (Rs 149)
5. Price Creep: Netflix Rs 499 (Nov-Apr) -> Rs 649 (May-Oct)
6. Zombie Subscription: Cult.Fit Gym Rs 2,499/mo (zero related active spends)
7. Insurance Gap:
   - LIC Endowment debit Rs 3,000/quarter (meager ~Rs 5 Lakhs cover)
   - Zero Health Insurance debits
   - Apollo Pharmacy & Hospital OPD spends (Rs 36,500 out-of-pocket medical)
8. Investments: Mutual Fund SIP Rs 12,000 on 10th
9. Realistic UPI Micro-noise: ~250 transactions (Chai, Auto, Kirana, Zomato, Weekend dining spikes)
10. Running Balance: Exact mathematical consistency.
"""

import random
from datetime import datetime, timedelta
import pandas as pd

# Fix seed for reproducibility
random.seed(42)

def generate_salaried_statement():
    records = []
    current_balance = 145200.50  # Starting balance on 2025-11-01
    start_date = datetime(2025, 11, 1)
    
    # Months list: Nov 2025 to Oct 2026 (12 months)
    months = []
    curr = start_date
    for _ in range(12):
        months.append((curr.year, curr.month))
        # advance month
        if curr.month == 12:
            curr = datetime(curr.year + 1, 1, 1)
        else:
            curr = datetime(curr.year, curr.month + 1, 1)
            
    # Vendors list for realistic UPI noise
    daily_micro_vendors = [
        ("S L N TEA STALL", 20.0, 40.0),
        ("RAMESH CHETTINAD CHAI", 25.0, 50.0),
        ("NAMMA AUTO RAJU", 90.0, 180.0),
        ("SURESH AUTO RAPIDO", 65.0, 140.0),
        ("GUPTA PROVISION STORE", 120.0, 480.0),
        ("SRI GANESH BAKERY", 45.0, 120.0),
        ("PAAN CORNER BANGALORE", 30.0, 70.0),
        ("TENDER COCONUT POINT", 50.0, 100.0),
        ("SRI BALAJI VEG HOTEL", 110.0, 220.0),
        ("PRINT OUT & XEROX POINT", 35.0, 80.0),
    ]
    
    dining_merchants = [
        ("Zomato", 350.0, 850.0),
        ("Swiggy", 280.0, 720.0),
        ("Starbucks Coffee", 380.0, 650.0),
        ("Third Wave Coffee", 290.0, 520.0),
        ("Toit Brewpub Bangalore", 1800.0, 3400.0),
        ("Meghana Foods Biryani", 450.0, 950.0),
        ("Truffles Koramangala", 650.0, 1400.0),
    ]
    
    grocery_merchants = [
        ("Blinkit Commerce", 350.0, 1200.0),
        ("Zepto Delivery", 280.0, 950.0),
        ("Nature Basket", 850.0, 2100.0),
    ]

    for yr, mo in months:
        # 1. Salary Credit (1st of month)
        sal_date = datetime(yr, mo, 1)
        sal_amt = 105000.00
        current_balance += sal_amt
        records.append({
            'date': sal_date.strftime('%Y-%m-%d'),
            'narration': f"NEFT CR-TECHCORP SOLUTIONS PVT LTD-SALARY-{sal_date.strftime('%b%y').upper()}",
            'debit': 0.0,
            'credit': sal_amt,
            'balance': current_balance,
            'mode': 'NEFT',
            'expected_category': 'Income',
            'expected_sub': 'Salary'
        })
        
        # Diwali Bonus in Oct 2026
        if yr == 2026 and mo == 10:
            bonus_date = datetime(2026, 10, 24)
            bonus_amt = 50000.00
            current_balance += bonus_amt
            records.append({
                'date': bonus_date.strftime('%Y-%m-%d'),
                'narration': "NEFT CR-TECHCORP SOLUTIONS-FESTIVE BONUS",
                'debit': 0.0,
                'credit': bonus_amt,
                'balance': current_balance,
                'mode': 'NEFT',
                'expected_category': 'Income',
                'expected_sub': 'Bonus'
            })
            
        # 2. Rent Payment (2nd of month)
        rent_date = datetime(yr, mo, 2)
        rent_amt = 26000.00
        current_balance -= rent_amt
        records.append({
            'date': rent_date.strftime('%Y-%m-%d'),
            'narration': "UPI/DR/48192841/RAJESH KUMAR/HDFC/rajesh.landlord@hdfc/RENT",
            'debit': rent_amt,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'UPI',
            'expected_category': 'Fixed Expenses',
            'expected_sub': 'Rent'
        })
        
        # 3. Car Loan EMI (5th of month)
        emi_date = datetime(yr, mo, 5)
        emi_amt = 24800.00
        current_balance -= emi_amt
        records.append({
            'date': emi_date.strftime('%Y-%m-%d'),
            'narration': "ACH D-HDFC BANK LTD-AUTO LOAN EMI-LN492819",
            'debit': emi_amt,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'ACH',
            'expected_category': 'Fixed Expenses',
            'expected_sub': 'Loan EMIs'
        })
        
        # 4. Mutual Fund SIP (10th of month)
        sip_date = datetime(yr, mo, 10)
        sip_amt = 12000.00
        current_balance -= sip_amt
        records.append({
            'date': sip_date.strftime('%Y-%m-%d'),
            'narration': "ACH D-NIPPON INDIA MUTUAL FUND-SIP-00941824",
            'debit': sip_amt,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'ACH',
            'expected_category': 'Investments',
            'expected_sub': 'Mutual Funds'
        })
        
        # 5. Utilities (Electricity & Broadband around 7th - 9th)
        util_date = datetime(yr, mo, 7)
        elec_amt = round(random.uniform(1450.0, 2100.0), 2)
        current_balance -= elec_amt
        records.append({
            'date': util_date.strftime('%Y-%m-%d'),
            'narration': "UPI/DR/39104812/BESCOM ELECTRICITY/SBIN/bescom.bill/Pay",
            'debit': elec_amt,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'UPI',
            'expected_category': 'Fixed Expenses',
            'expected_sub': 'Utilities'
        })
        
        bb_date = datetime(yr, mo, 8)
        bb_amt = 1179.00
        current_balance -= bb_amt
        records.append({
            'date': bb_date.strftime('%Y-%m-%d'),
            'narration': "UPI/DR/48194012/ACT FIBERNET BANGALORE/HDFC/actcorp/Pay",
            'debit': bb_amt,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'UPI',
            'expected_category': 'Fixed Expenses',
            'expected_sub': 'Utilities'
        })
        
        # 6. Subscriptions
        # A) Netflix with Price Creep (was 499, became 649 in May 2026)
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
            'expected_category': 'Fixed Expenses',
            'expected_sub': 'Subscriptions'
        })
        
        # B) Duplicate: Spotify (119) & YouTube Premium (149)
        spot_date = datetime(yr, mo, 16)
        current_balance -= 119.00
        records.append({
            'date': spot_date.strftime('%Y-%m-%d'),
            'narration': "UPI/DR/9481920/Spotify India/ICIC/spotify.pay/Monthly",
            'debit': 119.00,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'UPI',
            'expected_category': 'Fixed Expenses',
            'expected_sub': 'Subscriptions'
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
            'expected_category': 'Fixed Expenses',
            'expected_sub': 'Subscriptions'
        })
        
        # C) Zombie Subscription: Cult.Fit Gym Rs 2,499
        gym_date = datetime(yr, mo, 20)
        current_balance -= 2499.00
        records.append({
            'date': gym_date.strftime('%Y-%m-%d'),
            'narration': "ACH D-CULT FIT HEALTHCARE PVT LTD-MONTHLY SUB",
            'debit': 2499.00,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'ACH',
            'expected_category': 'Fixed Expenses',
            'expected_sub': 'Subscriptions'
        })
        
        # D) Apple iCloud Rs 75
        cloud_date = datetime(yr, mo, 22)
        current_balance -= 75.00
        records.append({
            'date': cloud_date.strftime('%Y-%m-%d'),
            'narration': "POS DEBIT-APPLE.COM/BILL-ITUNES-IRELAND",
            'debit': 75.00,
            'credit': 0.0,
            'balance': current_balance,
            'mode': 'POS',
            'expected_category': 'Fixed Expenses',
            'expected_sub': 'Subscriptions'
        })
        
        # 7. Insurance: Meager LIC Endowment (Quarterly: Jan, Apr, Jul, Oct)
        if mo in (1, 4, 7, 10):
            lic_date = datetime(yr, mo, 18)
            current_balance -= 3000.00
            records.append({
                'date': lic_date.strftime('%Y-%m-%d'),
                'narration': "ACH D-LIFE INSURANCE CORP OF INDIA-LIC PREMIUM",
                'debit': 3000.00,
                'credit': 0.0,
                'balance': current_balance,
                'mode': 'ACH',
                'expected_category': 'Fixed Expenses',
                'expected_sub': 'Insurance Premiums'
            })
            
        # 8. Out-of-pocket Medical (Demonstrating Health Insurance Gap)
        # Random hospital/pharmacy spends in Feb, May, Aug
        if mo == 2:
            med_date = datetime(yr, mo, 15)
            med_amt = 12400.00
            current_balance -= med_amt
            records.append({
                'date': med_date.strftime('%Y-%m-%d'),
                'narration': "POS DEBIT-MANIPAL HOSPITAL OPD & DIAGNOSTICS",
                'debit': med_amt,
                'credit': 0.0,
                'balance': current_balance,
                'mode': 'POS',
                'expected_category': 'Variable Essentials',
                'expected_sub': 'Healthcare & Pharmacy'
            })
        elif mo == 5:
            med_date = datetime(yr, mo, 21)
            med_amt = 16800.00
            current_balance -= med_amt
            records.append({
                'date': med_date.strftime('%Y-%m-%d'),
                'narration': "POS DEBIT-APOLLO HOSPITALS EMERGENCY & CONSULT",
                'debit': med_amt,
                'credit': 0.0,
                'balance': current_balance,
                'mode': 'POS',
                'expected_category': 'Variable Essentials',
                'expected_sub': 'Healthcare & Pharmacy'
            })
        elif mo == 8:
            med_date = datetime(yr, mo, 12)
            med_amt = 7300.00
            current_balance -= med_amt
            records.append({
                'date': med_date.strftime('%Y-%m-%d'),
                'narration': "UPI/DR/849182/APOLLO PHARMACY BANGALORE/HDFC/apollopharm/Pay",
                'debit': med_amt,
                'credit': 0.0,
                'balance': current_balance,
                'mode': 'UPI',
                'expected_category': 'Variable Essentials',
                'expected_sub': 'Healthcare & Pharmacy'
            })

        # 9. Daily Micro-Spends & Messy UPI Reality (~18-24 transactions per month)
        # Generate days in month
        num_days = 28 if mo == 2 else (30 if mo in (4, 6, 9, 11) else 31)
        for day in range(3, num_days + 1):
            d_obj = datetime(yr, mo, day)
            is_weekend = d_obj.weekday() in (4, 5, 6) # Fri, Sat, Sun
            
            # Daily Chai/Auto micro-spend (1 to 2 times a day)
            v_name, min_p, max_p = random.choice(daily_micro_vendors)
            v_amt = round(random.uniform(min_p, max_p), 2)
            current_balance -= v_amt
            records.append({
                'date': d_obj.strftime('%Y-%m-%d'),
                'narration': f"UPI/DR/{random.randint(100000000000, 999999999999)}/{v_name}/YESB/paytmqr{random.randint(1000,9999)}/Pay",
                'debit': v_amt,
                'credit': 0.0,
                'balance': round(current_balance, 2),
                'mode': 'UPI',
                'expected_category': 'Daily Micro-Spends',
                'expected_sub': 'Local Vendor / Street Pay'
            })
            
            # Weekend Dining Spikes (Swiggy / Zomato / Pubs)
            if is_weekend and random.random() < 0.70:
                d_merchant, d_min, d_max = random.choice(dining_merchants)
                d_amt = round(random.uniform(d_min, d_max), 2)
                current_balance -= d_amt
                records.append({
                    'date': d_obj.strftime('%Y-%m-%d'),
                    'narration': f"UPI/DR/{random.randint(100000000000, 999999999999)}/{d_merchant}/HDFC/pay.{d_merchant.lower().split()[0]}/Orders",
                    'debit': d_amt,
                    'credit': 0.0,
                    'balance': round(current_balance, 2),
                    'mode': 'UPI',
                    'expected_category': 'Discretionary',
                    'expected_sub': 'Food Delivery & Dining'
                })
                
            # Groceries (Blinkit / Zepto) once or twice a week
            if day in (4, 11, 19, 26):
                g_merchant, g_min, g_max = random.choice(grocery_merchants)
                g_amt = round(random.uniform(g_min, g_max), 2)
                current_balance -= g_amt
                records.append({
                    'date': d_obj.strftime('%Y-%m-%d'),
                    'narration': f"UPI/DR/{random.randint(100000000000, 999999999999)}/{g_merchant}/UTIB/groceries{random.randint(100,999)}/Pay",
                    'debit': g_amt,
                    'credit': 0.0,
                    'balance': round(current_balance, 2),
                    'mode': 'UPI',
                    'expected_category': 'Variable Essentials',
                    'expected_sub': 'Groceries & Supplies'
                })
                
            # Occasional Amazon / Shopping (1-2 per month)
            if day in (13, 27) and random.random() < 0.6:
                shop_amt = round(random.uniform(699.0, 3499.0), 2)
                current_balance -= shop_amt
                records.append({
                    'date': d_obj.strftime('%Y-%m-%d'),
                    'narration': f"POS DEBIT-AMAZON SELLER SERVICES BANGALORE",
                    'debit': shop_amt,
                    'credit': 0.0,
                    'balance': round(current_balance, 2),
                    'mode': 'POS',
                    'expected_category': 'Discretionary',
                    'expected_sub': 'Shopping & E-Commerce'
                })
                
            # Fuel / Petrol (twice a month)
            if day in (6, 21):
                fuel_amt = round(random.uniform(1800.0, 2400.0), 2)
                current_balance -= fuel_amt
                records.append({
                    'date': d_obj.strftime('%Y-%m-%d'),
                    'narration': f"POS DEBIT-SHELL PETROL PUMP KORAMANGALA",
                    'debit': fuel_amt,
                    'credit': 0.0,
                    'balance': round(current_balance, 2),
                    'mode': 'POS',
                    'expected_category': 'Variable Essentials',
                    'expected_sub': 'Fuel & Commute'
                })

    # Sort all by date
    df = pd.DataFrame(records)
    df = df.sort_values(by=['date']).reset_index(drop=True)
    
    # Recalculate exact running balance
    bal = 145200.50
    final_bals = []
    for _, row in df.iterrows():
        bal = bal + row['credit'] - row['debit']
        final_bals.append(round(bal, 2))
    df['balance'] = final_bals
    
    return df

if __name__ == '__main__':
    df = generate_salaried_statement()
    out_file = 'demo_salaried_statement_12months.csv'
    df.to_csv(out_file, index=False)
    print(f"Generated {len(df)} transactions spanning {df['date'].min()} to {df['date'].max()}")
    print(f"File saved to: {out_file}")
    print("\nFinancial Highlights of Demo Profile:")
    print(f" - Total Income: Rs {df['credit'].sum():,.2f}")
    print(f" - Total Expenses: Rs {df['debit'].sum():,.2f}")
    print(f" - Net Savings across 12 months: Rs {(df['credit'].sum() - df['debit'].sum()):,.2f}")
    print(f" - End Balance: Rs {df['balance'].iloc[-1]:,.2f}")
    print("\nExpected Category Breakdown:")
    print(df['expected_category'].value_counts())
