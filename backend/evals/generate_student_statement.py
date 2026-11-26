"""
Generates a synthetic 12-month bank statement for a college student, plus a separate
ground-truth labels file recording the category each transaction was generated as.

Persona: Meera Krishnan, third-year engineering student in Chennai living in a PG.
Her father sends a monthly allowance, her mother sends occasional extra money, she splits
costs with friends over UPI, does a two-month winter internship, and pays small vendors
through QR codes whose narrations say little about the shop.

The narrations follow HDFC Bank statement formats (UPI-, NEFT CR-, IMPS-, POS, ME DC SI).
They were written from real statement conventions, not from the app's categorization rules.

Output (deterministic for a given seed):
  data/student_statement.csv  the statement as a bank would export it
  data/student_labels.csv     one row per transaction: expected sub-category and macro
                              category, hard-case group, and whether a careful human
                              could tell the category from the narration and amount alone

Usage: python evals/generate_student_statement.py [--seed 20250701]
"""

import argparse
import calendar
import csv
import datetime as dt
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from app.services.categorizer.merchant_intelligence import SUB_TO_MACRO  # noqa: E402  (label vocabulary only)

DATA_DIR = os.path.join(HERE, "data")
STATEMENT_PATH = os.path.join(DATA_DIR, "student_statement.csv")
LABELS_PATH = os.path.join(DATA_DIR, "student_labels.csv")

START = dt.date(2025, 7, 1)
MONTHS = 12
OPENING_BALANCE = 12000.0
MIN_BALANCE = 800.0  # discretionary spends are skipped rather than overdrawing

CARD = "416021XXXXXX4821"

FATHER = ("K RAMESH", "ramesh.k1969@oksbi", "SBIN0000951")
MOTHER = ("LATHA RAMESH", "latharamesh@okicici", "ICIC0001207")
FRIENDS = [
    ("KARTHIK S", "karthik.s2004@okaxis", "UTIB0002913"),
    ("ARJUN V", "arjunv@ybl", "HDFC0001744"),
    ("DIVYA R", "divya.r.03@okhdfcbank", "HDFC0000312"),
    ("SNEHA P", "snehap22@paytm", "PYTM0123456"),
    ("ROHIT M", "rohitm@ibl", "INDB0000171"),
    ("NIKHIL J", "nikhil.j@okicici", "ICIC0000593"),
]
FRIEND_OUT_REMARKS = ["dinner split", "movie", "NA", "Sent using Paytm", "trip share", "UPI", "cab share", "bday gift"]
FRIEND_IN_REMARKS = ["splitwise", "UPI", "NA", "returning", "cab share", "food"]

# Hard-case groups, reported separately
ALLOWANCE, FRIENDS_GROUP, REFUND_CASHBACK, CRYPTIC = "allowance", "friends", "refund_cashback", "cryptic"


class Ledger:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.rows = []
        self._refs = set()

    def ref(self) -> str:
        while True:
            r = str(self.rng.randint(500000000000, 599999999999))
            if r not in self._refs:
                self._refs.add(r)
                return r

    def add(self, date, narration, amount, sub, *, credit=False, hard_case="", ambiguous=False, note=""):
        assert sub in SUB_TO_MACRO, sub
        self.rows.append({
            "date": date,
            "narration": narration,
            "debit": 0.0 if credit else round(amount, 2),
            "credit": round(amount, 2) if credit else 0.0,
            "expected_sub_category": sub,
            "expected_category": SUB_TO_MACRO[sub],
            "hard_case": hard_case,
            "ambiguous": "yes" if ambiguous else "no",
            "note": note,
        })


def upi(name, vpa, ifsc, ref, remark):
    return f"UPI-{name}-{vpa}-{ifsc}-{ref}-{remark}"


def month_start(i: int) -> dt.date:
    y, m = START.year + (START.month - 1 + i) // 12, (START.month - 1 + i) % 12 + 1
    return dt.date(y, m, 1)


def days_in(d: dt.date) -> int:
    return calendar.monthrange(d.year, d.month)[1]


def generate(seed: int):
    rng = random.Random(seed)
    L = Ledger(rng)

    def day(m0, lo=1, hi=None):
        hi = min(hi or days_in(m0), days_in(m0))
        return m0.replace(day=rng.randint(lo, hi))

    def amt(lo, hi, step=1):
        return float(rng.randrange(lo, hi + 1, step))

    for i in range(MONTHS):
        m0 = month_start(i)
        mon = m0.strftime("%b").upper()
        yy = m0.strftime("%y")

        # ---------- Income ----------
        # Monthly allowance from father: always 15,000, channel and remark vary
        d = day(m0, 1, 3)
        style = i % 3
        if style == 0:
            L.add(d, upi(*FATHER[:1], FATHER[1], FATHER[2], L.ref(), "pocket money"), 15000, "Transfers In (P2P)",
                  credit=True, hard_case=ALLOWANCE, note="father's monthly allowance")
        elif style == 1:
            L.add(d, f"IMPS-{L.ref()}-K RAMESH-SBIN-XXXXXXX4410-MONTHLY", 15000, "Transfers In (P2P)",
                  credit=True, hard_case=ALLOWANCE, note="father's monthly allowance (IMPS)")
        else:
            L.add(d, upi(FATHER[0], FATHER[1], FATHER[2], L.ref(), "NA"), 15000, "Transfers In (P2P)",
                  credit=True, hard_case=ALLOWANCE, note="father's monthly allowance, no remark")
        # Occasional extra money from mother
        if rng.random() < 0.45:
            remark = rng.choice(["for books", "exam", "NA", "Sent from Paytm"])
            L.add(day(m0, 8, 25), upi(MOTHER[0], MOTHER[1], MOTHER[2], L.ref(), remark), amt(1000, 3000, 500),
                  "Transfers In (P2P)", credit=True, hard_case=ALLOWANCE, note="mother's extra money")
        # Winter internship stipend (Dec, Jan), paid early the following month
        if m0.month in (1, 2):
            paid_for = "DEC25" if m0.month == 1 else "JAN26"
            L.add(day(m0, 2, 5), f"NEFT CR-ICIC0000104-FRESHWORKS TECHNOLOGIES PVT LTD-STIPEND {paid_for}-CMS{L.ref()}",
                  15000, "Salary", credit=True, note="internship stipend")
        # Quarterly savings interest
        if m0.month in (7, 10, 1, 4) and i > 0:
            L.add(m0.replace(day=1), "CREDIT INTEREST CAPITALISED", amt(38, 95), "Bank Interest", credit=True)
        # Friends paying her back
        for _ in range(rng.choice([0, 1, 1, 2])):
            f = rng.choice(FRIENDS)
            L.add(day(m0), upi(f[0], f[1], f[2], L.ref(), rng.choice(FRIEND_IN_REMARKS)), amt(150, 1200, 10),
                  "Transfers In (P2P)", credit=True, hard_case=FRIENDS_GROUP, note="friend repaying")

        # ---------- Fixed ----------
        rent_day = day(m0, 2, 5)
        if i % 2 == 0:
            L.add(rent_day, f"NEFT DR-IOBA0001542-SRI SAI LADIES PG-NETBANK, MUM-N{L.ref()}-RENT {mon}{yy}", 7500,
                  "Loan EMIs & Rent", note="PG rent")
        else:
            L.add(rent_day, upi("SRI SAI LADIES PG", "srisaipg@iob", "IOBA0001542", L.ref(), f"rent {mon.lower()}"), 7500,
                  "Loan EMIs & Rent", note="PG rent")
        # Mobile recharge every month: Jio directly, or through Google Pay's recharge partner (Euronet)
        if i % 2 == 0:
            L.add(day(m0, 6, 10), upi("RELIANCE JIO INFOCOMM LTD", "jiomobility@hdfcbank", "HDFC0000499", L.ref(), "Recharge"),
                  299, "Utilities & Bills", note="mobile recharge")
        else:
            L.add(day(m0, 6, 10), upi("EURONETGPAY", "euronetgpay.pay@icici", "ICIC0DC0099", L.ref(), "UPI"),
                  299, "Utilities & Bills", hard_case=CRYPTIC, note="mobile recharge via Google Pay (Euronet)")
        L.add(m0.replace(day=11), f"ME DC SI {CARD} SPOTIFY INDIA", 59, "Subscriptions", note="Spotify student")
        L.add(m0.replace(day=17), f"ME DC SI {CARD} GOOGLE *YouTubePremium", 89, "Subscriptions", note="YouTube Premium student")
        L.add(m0.replace(day=21), f"ME DC SI {CARD} GOOGLE *Google One", 130, "Cloud & Tech Tools", note="Google One storage")
        if m0.month in (10, 11, 4):  # exam months
            L.add(m0.replace(day=14), f"POS {CARD} OPENAI *CHATGPT SUBSCR", 1999, "Cloud & Tech Tools", note="ChatGPT Plus")
        # Laundry
        L.add(day(m0, 12, 16), upi("WASHMART LAUNDRY", "washmart.velachery@okaxis", "UTIB0000512", L.ref(), "Payment"),
              amt(350, 600, 10), "Local Shopping & Services", note="laundry")

        rows_month = []  # discretionary spends, applied later in date order with a balance check

        def later(date, narration, amount, sub, **kw):
            rows_month.append((date, narration, amount, sub, kw))

        # ---------- Food ----------
        for _ in range(rng.randint(4, 6)):
            later(day(m0), upi("SRM UNIV FOOD COURT", "srmfoodcourt@icici", "ICIC0000611", L.ref(), "Payment"),
                  amt(60, 180, 5), "Food Delivery & Dining", note="college food court")
        for _ in range(rng.randint(2, 4)):
            if rng.random() < 0.6:
                later(day(m0), upi("Swiggy", "swiggy.order@axisbank", "UTIB0000100", L.ref(), "Swiggy Order"),
                      amt(180, 520, 1), "Food Delivery & Dining", note="Swiggy")
            else:
                later(day(m0), upi("Zomato", "zomato.order@ptybl", "PYTM0123456", L.ref(), "Zomato Order"),
                      amt(180, 480, 1), "Food Delivery & Dining", note="Zomato")
        if rng.random() < 0.5:
            later(day(m0), upi("BUNDL TECHNOLOGIES PVT LTD", "bundl.swiggy@axisbank", "UTIB0000100", L.ref(), "UPI"),
                  amt(200, 450, 1), "Food Delivery & Dining", hard_case=CRYPTIC, note="Swiggy under its legal name")
        if rng.random() < 0.6:
            later(day(m0), upi("cf.isthara", "cf.isthara@axisbank", "UTIB0000100", L.ref(), "Pay"),
                  amt(120, 260, 5), "Food Delivery & Dining", hard_case=CRYPTIC, note="Isthara food court")
        if rng.random() < 0.4:
            later(day(m0), f"POS {CARD} THIRD WAVE COFFEE ROAS", amt(220, 420, 10), "Food Delivery & Dining", note="cafe")

        # ---------- Daily micro-spends ----------
        for _ in range(rng.randint(3, 5)):
            later(day(m0), upi("MURUGAN TEA STALL", "q291049381@ybl", "YESB0YBLUPI", L.ref(), "Payment"),
                  amt(15, 60, 5), "Local Vendor / Street Pay", note="tea stall")
        for _ in range(rng.randint(1, 2)):
            code = rng.choice([
                ("Vyapar.171812345", "vyapar.171812345@hdfcbank", "HDFC0MERUPI"),
                ("paytmqr2810050501", "paytmqr2810050501@paytm", "PYTM0123456"),
                ("BHARATPE.9071234567", "bharatpe.9071234567@yesbankltd", "YESB0000001"),
            ])
            later(day(m0), upi(code[0], code[1], code[2], L.ref(), "UPI"), amt(20, 90, 5), "Local Vendor / Street Pay",
                  hard_case=CRYPTIC, ambiguous=True, note="small QR payment to an unnamed shop (snacks)")
        if rng.random() < 0.5:
            later(day(m0), upi("SELVI", "selvi.m1978@ybl", "YESB0YBLUPI", L.ref(), "Payment"), amt(30, 80, 5),
                  "Local Vendor / Street Pay", hard_case=CRYPTIC, ambiguous=True,
                  note="fruit vendor paid on a personal VPA (looks like a person)")

        # ---------- Groceries ----------
        for _ in range(rng.randint(1, 2)):
            if rng.random() < 0.5:
                later(day(m0), upi("Blinkit", "blinkit.payu@hdfcbank", "HDFC0000499", L.ref(), "Payment"),
                      amt(150, 650, 1), "Groceries & Supplies", note="Blinkit")
            else:
                later(day(m0), upi("KIRANAKART TECHNOLOGIES PVT LTD", "zeptonow@ybl", "YESB0YBLUPI", L.ref(), "UPI"),
                      amt(150, 650, 1), "Groceries & Supplies", hard_case=CRYPTIC, note="Zepto under its legal name")

        # ---------- Commute ----------
        for _ in range(rng.randint(2, 4)):
            if rng.random() < 0.5:
                later(day(m0), upi("Rapido", "rapido.rides@axisbank", "UTIB0000100", L.ref(), "Ride payment"),
                      amt(45, 160, 1), "Ride Hailing & Auto", note="Rapido")
            else:
                later(day(m0), upi("ROPPEN TRANSPORTATION SERVICES PVT LTD", "rapidobike@ybl", "YESB0YBLUPI", L.ref(), "UPI"),
                      amt(45, 160, 1), "Ride Hailing & Auto", hard_case=CRYPTIC, note="Rapido under its legal name")
        if rng.random() < 0.5:
            later(day(m0), upi("ANI TECHNOLOGIES PVT LTD", "olacabs@ybl", "YESB0YBLUPI", L.ref(), "UPI"),
                  amt(140, 380, 1), "Ride Hailing & Auto", hard_case=CRYPTIC, note="Ola under its legal name")
        if rng.random() < 0.4:
            later(day(m0), upi("Uber India", "uber.india@axisbank", "UTIB0000100", L.ref(), "Uber trip"),
                  amt(150, 420, 1), "Ride Hailing & Auto", note="Uber")
        if rng.random() < 0.5:
            later(day(m0), upi("RAJESH KUMAR", "rajeshkumar1987@okicici", "ICIC0000593", L.ref(), "Payment"),
                  amt(60, 150, 10), "Ride Hailing & Auto", hard_case=CRYPTIC, ambiguous=True,
                  note="auto-rickshaw driver paid on a personal VPA (looks like a person)")
        for _ in range(rng.randint(2, 4)):
            later(day(m0), upi("CHENNAI METRO RAIL LIMITED", "cmrl.qr@icici", "ICIC0DC0099", L.ref(), "QR Ticket"),
                  amt(20, 50, 10), "Public Transit & Metro", note="metro ticket")

        # ---------- Shopping, entertainment, services ----------
        if rng.random() < 0.7:
            later(day(m0), upi("Amazon Pay India", "amazonpay@apl", "UTIB0000100", L.ref(), "Amazon order"),
                  amt(299, 1899, 1), "Shopping & E-Commerce", note="Amazon")
        if rng.random() < 0.35:
            later(day(m0), upi("FLIPKART INTERNET PVT LTD", "fkrt@ybl", "YESB0YBLUPI", L.ref(), "UPI"),
                  amt(399, 2499, 1), "Shopping & E-Commerce", note="Flipkart")
        if rng.random() < 0.25:
            later(day(m0), upi("Myntra Designs", "myntra@hdfcbank", "HDFC0000499", L.ref(), "Myntra order"),
                  amt(499, 1999, 1), "Shopping & E-Commerce", note="Myntra")
        if rng.random() < 0.6:
            later(day(m0), upi("BOOKMYSHOW", "bookmyshow.rzp@icici", "ICIC0DC0099", L.ref(), "Movie tickets"),
                  amt(180, 450, 1), "Entertainment & Outings", note="movie tickets")
        if rng.random() < 0.15:
            later(day(m0), f"POS {CARD} STEAM PURCHASE", amt(199, 899, 1), "Entertainment & Outings", note="Steam game")
        if i % 2 == 1:
            later(day(m0), upi("NATURALS SALON VELACHERY", "naturals.velachery@okhdfcbank", "HDFC0000312", L.ref(), "Payment"),
                  amt(250, 450, 50), "Local Shopping & Services", note="haircut")

        # ---------- Education ----------
        if rng.random() < 0.6:
            later(day(m0), upi("SRI GANESH XEROX", "q781209443@ybl", "YESB0YBLUPI", L.ref(), "Payment"),
                  amt(20, 120, 5), "Education & Academic", note="photocopies and prints")
        if m0.month in (8, 1):
            later(day(m0, 5, 20), upi("PAYU", "payu@hdfcbank", "HDFC0000499", L.ref(), "Payment"), 1650,
                  "Education & Academic", hard_case=CRYPTIC, ambiguous=True, note="semester exam fee through the PayU gateway")
            later(day(m0, 5, 20), f"POS {CARD} SVM ENTERPRISES", amt(400, 900, 10), "Education & Academic",
                  hard_case=CRYPTIC, ambiguous=True, note="stationery and lab record books")
        if m0.month == 9:
            later(day(m0), f"POS {CARD} UDEMY ONLINE COURSES", 449, "Education & Academic", note="Udemy course")
        if m0.month == 2:
            later(day(m0), f"POS {CARD} COURSERA", 2999, "Education & Academic", note="Coursera certificate")

        # ---------- Health ----------
        if rng.random() < 0.3:
            later(day(m0), upi("APOLLO PHARMACY", "apollopharmacy@icici", "ICIC0DC0099", L.ref(), "Payment"),
                  amt(90, 650, 1), "Healthcare & Eyewear", note="pharmacy")

        # ---------- Travel ----------
        if m0.month in (10, 1, 5):
            later(day(m0, 3, 12), upi("IRCTC", "irctc.web@hdfcbank", "HDFC0000499", L.ref(), "IRCTC ticket"),
                  amt(620, 1450, 5), "Travel & Vacation", note="train home")
        if m0.month == 12:
            later(m0.replace(day=6), upi("redBus", "redbus@icici", "ICIC0DC0099", L.ref(), "Bus ticket"), 1340,
                  "Travel & Vacation", note="bus for a trip with friends")

        # ---------- Friends ----------
        for _ in range(rng.randint(1, 3)):
            f = rng.choice(FRIENDS)
            later(day(m0), upi(f[0], f[1], f[2], L.ref(), rng.choice(FRIEND_OUT_REMARKS)), amt(100, 900, 10),
                  "Transfer to Friends & Contacts", hard_case=FRIENDS_GROUP, note="paying a friend")
        if m0.month == 12:
            f = FRIENDS[1]
            later(m0.replace(day=8), upi(f[0], f[1], f[2], L.ref(), "goa trip stay"), 3200,
                  "Transfer to Friends & Contacts", hard_case=FRIENDS_GROUP, note="her share of a trip, paid to a friend")

        # ---------- Refunds and cashbacks (paired with earlier spends where realistic) ----------
        if m0.month in (8, 11, 3):
            amazon = [r for r in rows_month if "amazonpay" in r[1]]
            if amazon:
                src = amazon[0]
                rd = min(src[0] + dt.timedelta(days=rng.randint(3, 6)), m0.replace(day=days_in(m0)))
                later(rd, upi("Amazon Pay India", "amazonpay@apl", "UTIB0000100", L.ref(), "Refund"), src[2],
                      "Refunds & Reversals", credit=True, hard_case=REFUND_CASHBACK, note="Amazon return refund")
        if m0.month == 10:
            later(m0.replace(day=27), upi("IRCTC", "irctc.web@hdfcbank", "HDFC0000499", L.ref(), "TKT CANCEL REFUND"),
                  480, "Refunds & Reversals", credit=True, hard_case=REFUND_CASHBACK, note="train ticket cancellation refund")
        if m0.month in (9, 2):
            swg = [r for r in rows_month if "swiggy.order" in r[1]]
            if swg:
                src = swg[0]
                later(src[0], f"REV-UPI-{L.ref()}-SWIGGY-ORDER CANCELLED", src[2], "Refunds & Reversals", credit=True,
                      hard_case=REFUND_CASHBACK, note="Swiggy cancelled-order reversal")
        if m0.month in (12, 6):
            later(day(m0, 10, 20), f"NEFT CR-YESB0000001-FLIPKART INTERNET PVT LTD-REFUND OD{rng.randint(10**14, 10**15)}-{L.ref()}",
                  amt(399, 1299, 1), "Refunds & Reversals", credit=True, hard_case=REFUND_CASHBACK, note="Flipkart refund")
        if m0.month in (7, 9, 11, 1, 3, 5):
            later(day(m0), upi("GOOGLE PAY", "goog-payment@okaxis", "UTIB0000553", L.ref(), "Rewards"), amt(5, 75, 1),
                  "Cashbacks & Rewards", credit=True, hard_case=REFUND_CASHBACK, note="Google Pay scratch-card reward")
        if m0.month in (8, 12, 4):
            later(day(m0), f"CASHBACK-PAYTM-{L.ref()}", amt(10, 50, 1), "Cashbacks & Rewards", credit=True,
                  hard_case=REFUND_CASHBACK, note="Paytm cashback")
        if m0.month in (10, 2):
            later(day(m0), f"AMAZON PAY CASHBACK {L.ref()}", amt(25, 100, 1), "Cashbacks & Rewards", credit=True,
                  hard_case=REFUND_CASHBACK, note="Amazon Pay cashback")

        for date, narration, amount, sub, kw in rows_month:
            L.add(date, narration, amount, sub, **kw)

    # Order by date (stable), then drop discretionary debits that would overdraw the account
    L.rows.sort(key=lambda r: r["date"])
    essential = {"Loan EMIs & Rent", "Utilities & Bills", "Subscriptions", "Cloud & Tech Tools", "Education & Academic"}
    kept, balance = [], OPENING_BALANCE
    for r in L.rows:
        nb = balance + r["credit"] - r["debit"]
        if nb < MIN_BALANCE and r["debit"] > 0 and r["expected_sub_category"] not in essential:
            continue
        balance = nb
        r["balance"] = round(balance, 2)
        kept.append(r)
    for n, r in enumerate(kept, 1):
        r["txn_id"] = f"T{n:04d}"
    return kept


def write(rows):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATEMENT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Narration", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"])
        for r in rows:
            w.writerow([r["date"].strftime("%d/%m/%Y"), r["narration"],
                        f"{r['debit']:.2f}" if r["debit"] else "", f"{r['credit']:.2f}" if r["credit"] else "",
                        f"{r['balance']:.2f}"])
    fields = ["txn_id", "date", "narration", "debit", "credit", "expected_sub_category", "expected_category",
              "hard_case", "ambiguous", "note"]
    with open(LABELS_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "date": r["date"].isoformat()})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=20250701)
    args = ap.parse_args()
    rows = generate(args.seed)
    write(rows)
    print(f"Wrote {len(rows)} transactions to {STATEMENT_PATH} and labels to {LABELS_PATH}")


if __name__ == "__main__":
    main()
