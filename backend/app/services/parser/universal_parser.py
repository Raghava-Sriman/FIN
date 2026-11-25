"""
Universal Bank Statement Parser
Supports:
1. SBI YONO App PDF Statements (Table-based: Dec, Jan, Feb, Mar, Apr)
2. SBI Online Netbanking PDF Statements (Stream-based: May)
3. PhonePe CSV Statement
"""

import os
import re
import glob
import datetime
import pdfplumber
import pypdf
import pandas as pd
from typing import List, Dict, Any, Optional, Union

from app.services.parser.dates import detect_day_first, parse_statement_date

def is_paytm_pdf(filepath: str) -> bool:
    """Checks if a PDF is a Paytm e-statement."""
    try:
        with pdfplumber.open(filepath) as pdf:
            if not pdf.pages:
                return False
            for p in pdf.pages[:3]:
                txt = (p.extract_text() or "").lower()
                if "paytm" in txt or "passbook payments history" in txt:
                    return True
    except Exception:
        pass
    return False

def parse_paytm_pdf(filepath: str) -> List[Dict[str, Any]]:
    """Extracts transactions from Paytm Passbook/UPI PDF statements."""
    months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
              'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}

    with pdfplumber.open(filepath) as pdf:
        if not pdf.pages:
            return []

        p0_text = pdf.pages[0].extract_text() or ''
        m_range = re.search(r'(\d{1,2}\s+[A-Za-z]+)\'?(\d{2,4})\s*-\s*(\d{1,2}\s+[A-Za-z]+)\'?(\d{2,4})', p0_text)
        end_year = datetime.datetime.now().year
        if m_range:
            y_str = m_range.group(4)
            end_year = int('20' + y_str if len(y_str) == 2 else y_str)

        current_year = end_year
        last_month = None
        raw_txs = []

        for p_idx, page in enumerate(pdf.pages):
            words = page.extract_words()
            if not words:
                continue

            footer_top = 780
            for w in words:
                if (w['text'] == 'Page' or 'queries' in w['text'].lower()) and w['top'] > 700:
                    footer_top = min(footer_top, w['top'])

            header_bottom = 120 if p_idx == 0 else 85
            for w in words:
                if w['text'] == 'Amount' and w['top'] < 200:
                    header_bottom = max(header_bottom, w['bottom'] + 2)

            tx_words = [w for w in words if w['top'] >= header_bottom and w['top'] < footer_top]

            date_anchors = []
            for i in range(len(tx_words)-1):
                w0, w1 = tx_words[i], tx_words[i+1]
                if w0['x0'] < 80 and w0['text'].isdigit() and w1['text'].lower() in months:
                    date_anchors.append((w0['top'], int(w0['text']), w1['text'].lower()))

            for k in range(len(date_anchors)):
                y_anchor, day, mon_str = date_anchors[k]
                top_min = y_anchor - 6
                top_max = date_anchors[k+1][0] - 6 if k + 1 < len(date_anchors) else footer_top

                block_words = [w for w in tx_words if top_min <= w['top'] < top_max]

                details_words = [w['text'] for w in block_words if 85 <= w['x0'] < 285]
                tags_words = [w['text'] for w in block_words if 285 <= w['x0'] < 410]
                account_words = [w['text'] for w in block_words if 410 <= w['x0'] < 485]
                amount_words = [w['text'] for w in block_words if w['x0'] >= 485]

                mon = months[mon_str]
                if last_month is not None:
                    if last_month == 1 and mon == 12:
                        current_year -= 1
                    elif mon > last_month and last_month <= 2 and mon >= 11:
                        current_year -= 1
                last_month = mon

                amt_str = ' '.join(amount_words).replace(',', '')
                is_credit = '+' in amt_str
                is_debit = '-' in amt_str

                details_str = ' '.join(details_words)
                tags_str = ' '.join(tags_words)
                account_str = ' '.join(account_words)

                amt_match = re.search(r'[\d]+(?:\.\d+)?', amt_str)
                val = float(amt_match.group(0)) if amt_match else 0.0

                if not is_credit and not is_debit:
                    if 'received' in details_str.lower() or 'refund' in details_str.lower():
                        is_credit = True
                    else:
                        is_debit = True

                debit = val if is_debit else 0.0
                credit = val if is_credit else 0.0

                m_upi = re.search(r'^(?:Paid to|Money sent to|Received from|Refund from|Transferred to)?\s*(.*?)(?:\s+(?:UPI ID:|UPI Ref No:|Note:|Tag:|Order ID:)|$)', details_str, re.IGNORECASE)
                clean_name = m_upi.group(1).strip() if m_upi and m_upi.group(1).strip() else details_str

                narration = f"{details_str} {tags_str}".strip()

                raw_txs.append({
                    'date': f'{current_year}-{mon:02d}-{day:02d}',
                    'narration': narration,
                    'merchant': clean_name,
                    'debit': debit,
                    'credit': credit,
                    'balance': 0.0,
                    'mode': 'UPI',
                    'source': os.path.basename(filepath),
                    'account': account_str
                })

    # Reverse to chronological order (oldest first)
    raw_txs.reverse()

    # Calculate virtual running balance
    running_balance = 25000.0
    for t in raw_txs:
        running_balance = running_balance - t['debit'] + t['credit']
        t['balance'] = round(running_balance, 2)

    min_bal = min(t['balance'] for t in raw_txs) if raw_txs else 0.0
    if min_bal < 0:
        offset = abs(min_bal) + 15000.0
        for t in raw_txs:
            t['balance'] = round(t['balance'] + offset, 2)

    return raw_txs

def parse_paytm_excel(filepath: str) -> List[Dict[str, Any]]:
    """Extracts transactions from Paytm Passbook/UPI Excel (.xlsx/.xls) statements."""
    try:
        # Close the workbook after reading so the file is not left locked (Windows)
        with pd.ExcelFile(filepath) as xl:
            sheet_name = None
            for s in xl.sheet_names:
                if any(k in s.lower() for k in ('passbook', 'payment', 'history')):
                    sheet_name = s
                    break
            if not sheet_name:
                sheet_name = xl.sheet_names[0]

            df = xl.parse(sheet_name)
        cols_clean = {str(c).strip(): c for c in df.columns}
        if 'Date' not in cols_clean or 'Amount' not in cols_clean:
            return []

        transactions = []
        for _, row in df.iterrows():
            raw_date = str(row[cols_clean['Date']]).strip()
            if not raw_date or raw_date == 'nan':
                continue
            try:
                std_date = pd.to_datetime(raw_date, format='%d/%m/%Y', errors='coerce')
                if pd.isnull(std_date):
                    std_date = pd.to_datetime(raw_date, errors='coerce')
                date_str = std_date.strftime('%Y-%m-%d') if pd.notnull(std_date) else raw_date
            except Exception:
                date_str = raw_date

            amt_val = row[cols_clean['Amount']]
            try:
                val = float(str(amt_val).replace(',', '').strip())
            except Exception:
                continue

            is_debit = val < 0
            val_abs = abs(val)

            details = str(row.get(cols_clean.get('Transaction Details', ''), '')).strip()
            if details == 'nan':
                details = ''
            other = str(row.get(cols_clean.get('Other Transaction Details (UPI ID or A/c No)', ''), '')).strip()
            if other == 'nan':
                other = ''
            tags = str(row.get(cols_clean.get('Tags', ''), '')).strip()
            if tags == 'nan':
                tags = ''
            account = str(row.get(cols_clean.get('Your Account', ''), '')).strip()
            if account == 'nan':
                account = ''

            narr = f"{details} {other} {tags}".strip()

            m_upi = re.search(r'^(?:Paid to|Money sent to|Received from|Refund from|Transferred to)?\s*(.*?)(?:\s+(?:UPI ID:|UPI Ref No:|Note:|Tag:|Order ID:)|$)', details, re.IGNORECASE)
            clean_name = m_upi.group(1).strip() if m_upi and m_upi.group(1).strip() else details

            transactions.append({
                'date': date_str,
                'narration': narr,
                'merchant': clean_name,
                'debit': val_abs if is_debit else 0.0,
                'credit': 0.0 if is_debit else val_abs,
                'balance': 0.0,
                'mode': 'UPI',
                'source': os.path.basename(filepath),
                'account': account
            })

        transactions.reverse()
        running = 25000.0
        for t in transactions:
            running = running - t['debit'] + t['credit']
            t['balance'] = round(running, 2)

        min_bal = min(t['balance'] for t in transactions) if transactions else 0.0
        if min_bal < 0:
            offset = abs(min_bal) + 15000.0
            for t in transactions:
                t['balance'] = round(t['balance'] + offset, 2)

        return transactions
    except Exception as e:
        print(f"Error parsing Paytm Excel: {e}")
        return []

def parse_standard_excel(filepath: str, skipped_rows: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Extracts transactions from standard bank Excel files.
    Rows that could not be read are added to `skipped_rows` for the sheet that was used
    (or for every sheet, if none produced transactions).
    """
    all_sheets_skipped: List[Dict[str, Any]] = []
    try:
        # Close the workbook after reading so the file is not left locked (Windows)
        with pd.ExcelFile(filepath) as xl:
            sheets = [xl.parse(s) for s in xl.sheet_names]
        for df in sheets:
            temp_csv = filepath + ".tmp.csv"
            df.to_csv(temp_csv, index=False)
            sheet_skipped: List[Dict[str, Any]] = []
            try:
                res = parse_standard_bank_csv(temp_csv, sheet_skipped)
                if os.path.exists(temp_csv):
                    os.remove(temp_csv)
                if len(res) > 0:
                    if skipped_rows is not None:
                        skipped_rows.extend(sheet_skipped)
                    return res
                all_sheets_skipped.extend(sheet_skipped)
            except Exception:
                if os.path.exists(temp_csv):
                    os.remove(temp_csv)
    except Exception:
        pass
    if skipped_rows is not None:
        skipped_rows.extend(all_sheets_skipped)
    return []


def is_gpay_pdf(filepath: str) -> bool:
    """Checks if a PDF is a Google Pay transaction statement."""
    try:
        reader = pypdf.PdfReader(filepath)
        if not reader.pages:
            return False
        for p in reader.pages[:2]:
            txt = (p.extract_text() or "").lower()
            if "google pay" in txt or ("transactionstatement" in txt.replace(" ", "") and ("upitransactionid" in txt.replace(" ", "") or "paidto" in txt.replace(" ", "") or "receivedfrom" in txt.replace(" ", ""))):
                return True
    except Exception:
        pass
    return False

def parse_gpay_pdf(filepath: str) -> List[Dict[str, Any]]:
    """Extracts transactions from Google Pay PDF transaction statements."""
    reader = pypdf.PdfReader(filepath)
    months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
              'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
    txs = []

    for page in reader.pages:
        lines = [l.strip() for l in page.extract_text().split('\n') if l.strip()]
        i = 0
        while i < len(lines):
            line = lines[i]
            # Match date e.g. 02Apr,2026 or 02 Apr, 2026 or 02-Apr-2026
            m_date = re.match(r'^(\d{1,2})\s*([A-Za-z]{3})[,\s-]+(\d{4})$', line)
            if m_date:
                day, mon_str, year = int(m_date.group(1)), m_date.group(2).lower(), int(m_date.group(3))
                mon = months.get(mon_str, 1)
                date_str = f'{year}-{mon:02d}-{day:02d}'
                i += 1

                time_str = ''
                if i < len(lines) and re.match(r'^\d{1,2}:\d{2}\s*(?:AM|PM)$', lines[i], re.I):
                    time_str = lines[i]
                    i += 1

                entity_raw = ''
                is_debit = True
                if i < len(lines) and ('Paidto' in lines[i] or 'Receivedfrom' in lines[i] or 'Paid to' in lines[i] or 'Received from' in lines[i]):
                    entity_raw = lines[i]
                    if 'Received' in entity_raw:
                        is_debit = False
                    i += 1

                upi_id = ''
                if i < len(lines) and 'UPITransactionID' in lines[i]:
                    upi_id = lines[i]
                    i += 1

                account_raw = ''
                if i < len(lines) and ('Paidby' in lines[i] or 'Paidto' in lines[i] or 'Paid by' in lines[i] or 'Paid to' in lines[i]):
                    account_raw = lines[i]
                    i += 1

                amt = 0.0
                if i < len(lines) and '₹' in lines[i]:
                    amt_str = lines[i].replace('₹', '').replace(',', '').strip()
                    try:
                        amt = float(amt_str)
                    except ValueError:
                        amt = 0.0
                    i += 1

                if amt > 0:
                    clean_name = re.sub(r'^(?:Paid\s*to|Received\s*from|Paidto|Receivedfrom)\s*', '', entity_raw, flags=re.I).strip()
                    clean_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_name)
                    clean_name = re.sub(r'(\b[A-Z]+)(PARKS)', r'\1 \2', clean_name)
                    clean_name = re.sub(r'(PARKS)(PRIVATE)', r'\1 \2', clean_name)
                    clean_name = re.sub(r'(PRIVATE)(LIMITED)', r'\1 \2', clean_name)
                    clean_name = re.sub(r'(PVT)(LTD)', r'\1 \2', clean_name).strip()

                    prefix = "Paid to" if is_debit else "Received from"
                    narration = f"{prefix} {clean_name} {upi_id} {account_raw}".strip()

                    txs.append({
                        'date': date_str,
                        'narration': narration,
                        'merchant': clean_name,
                        'debit': amt if is_debit else 0.0,
                        'credit': 0.0 if is_debit else amt,
                        'balance': 0.0,
                        'mode': 'UPI',
                        'source': os.path.basename(filepath),
                        'account': account_raw
                    })
            else:
                i += 1

    # Virtual running balance for statements without balance column
    running = 25000.0
    for t in txs:
        running = running - t['debit'] + t['credit']
        t['balance'] = round(running, 2)
    min_bal = min(t['balance'] for t in txs) if txs else 0.0
    if min_bal < 0:
        offset = abs(min_bal) + 15000.0
        for t in txs:
            t['balance'] = round(t['balance'] + offset, 2)

    return txs

def is_sbi_yono_alternating(pdf) -> bool:
    """Detects SBI YONO statements where wide table is printed across alternating pages."""
    if len(pdf.pages) < 2:
        return False
    t0 = pdf.pages[0].extract_tables()
    t1 = pdf.pages[1].extract_tables()
    if not t0 or not t1:
        return False
    c0 = len(t0[0][0]) if t0[0] else 0
    c1 = len(t1[0][0]) if t1[0] else 0
    return c0 == 2 and c1 in (3, 4)

def parse_sbi_yono_alternating(pdf, filepath: str) -> List[Dict[str, Any]]:
    """Merges page pairs for SBI YONO statements printed across alternating pages."""
    transactions = []
    num_pages = len(pdf.pages)
    for p_idx in range(0, num_pages, 2):
        if p_idx + 1 >= num_pages:
            break
        t_left = pdf.pages[p_idx].extract_tables()
        t_right = pdf.pages[p_idx + 1].extract_tables()
        if not t_left or not t_right:
            continue

        table_l = t_left[0]
        table_r = t_right[0]
        min_rows = min(len(table_l), len(table_r))

        for r_idx in range(min_rows):
            row_l = table_l[r_idx]
            row_r = table_r[r_idx]

            date_cell = str(row_l[0]).strip() if row_l and row_l[0] else ''
            m_date = re.match(r'^(\d{2})[/.-](\d{2})[/.-](\d{2,4})$', date_cell)
            if not m_date:
                continue

            day, mon, year = int(m_date.group(1)), int(m_date.group(2)), int(m_date.group(3))
            if year < 100:
                year += 2000
            date_str = f'{year}-{mon:02d}-{day:02d}'
            details = str(row_l[1]).strip() if len(row_l) > 1 and row_l[1] else ''

            # row_r: [Ref No, Debit, Credit, Balance]
            ref_no = str(row_r[0]).strip() if len(row_r) > 0 and row_r[0] else ''
            debit_str = str(row_r[1]).replace(',', '').strip() if len(row_r) > 1 and row_r[1] else ''
            credit_str = str(row_r[2]).replace(',', '').strip() if len(row_r) > 2 and row_r[2] else ''
            bal_str = str(row_r[3]).replace(',', '').strip() if len(row_r) > 3 and row_r[3] else ''

            debit = 0.0
            credit = 0.0
            balance = 0.0

            try:
                if debit_str and debit_str not in ('-', '0', 'null', 'nan'):
                    debit = float(debit_str)
            except ValueError:
                pass

            try:
                if credit_str and credit_str not in ('-', '0', 'null', 'nan'):
                    credit = float(credit_str)
            except ValueError:
                pass

            try:
                if bal_str and bal_str not in ('-', 'null', 'nan'):
                    balance = float(bal_str)
            except ValueError:
                pass

            narration = details.replace('\n', ' ')
            if ref_no and ref_no not in narration:
                narration = f"{narration} Ref:{ref_no}".strip()

            mode = 'UPI' if 'UPI' in narration else ('ATM' if 'ATM' in narration or 'WDL' in narration else ('ACH' if 'ACH' in narration else 'BANK_TRANSFER'))

            transactions.append({
                'date': date_str,
                'narration': narration,
                'debit': debit,
                'credit': credit,
                'balance': balance,
                'mode': mode,
                'source': os.path.basename(filepath)
            })

    return transactions

def parse_sbi_yono_pdf(filepath: str) -> List[Dict[str, Any]]:
    """Extracts transactions from SBI YONO mobile app e-statements (tables)."""
    with pdfplumber.open(filepath) as pdf:
        if is_sbi_yono_alternating(pdf):
            return parse_sbi_yono_alternating(pdf, filepath)

        transactions = []
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or not row[0]:
                        continue
                    first_cell = str(row[0]).strip()
                    m_date = re.match(r'^(\d{2})[/.-](\d{2})[/.-](\d{2,4})$', first_cell)
                    if m_date:
                        cells = [str(c).strip() if c is not None else '' for c in row if c is not None and str(c).strip() != '']
                        if len(cells) < 4:
                            continue

                        day, mon, year = int(m_date.group(1)), int(m_date.group(2)), int(m_date.group(3))
                        if year < 100:
                            year += 2000
                        date_str = f'{year}-{mon:02d}-{day:02d}'
                        narration = cells[1] if len(cells) > 1 else ''

                        try:
                            balance = float(cells[-1].replace(',', ''))
                        except ValueError:
                            balance = 0.0

                        try:
                            debit_str = cells[-2]
                            debit = float(debit_str.replace(',', '')) if debit_str not in ('-', '0', '', 'null') else 0.0
                        except ValueError:
                            debit = 0.0

                        try:
                            credit_str = cells[-3] if len(cells) >= 3 else '0'
                            credit = float(credit_str.replace(',', '')) if credit_str not in ('-', '0', '', 'null') else 0.0
                        except ValueError:
                            credit = 0.0

                        transactions.append({
                            'date': date_str,
                            'narration': narration,
                            'debit': debit,
                            'credit': credit,
                            'balance': balance,
                            'mode': 'UPI' if 'UPI' in narration else ('ATM' if 'ATM' in narration or 'WDL' in narration else 'BANK_TRANSFER'),
                            'source': os.path.basename(filepath)
                        })
        return transactions

def parse_sbi_netbanking_pdf(filepath: str) -> List[Dict[str, Any]]:
    """Extracts transactions from SBI Internet Banking downloaded PDF statements."""
    reader = pypdf.PdfReader(filepath)
    text = '\n'.join([p.extract_text() for p in reader.pages[1:]])
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    transactions = []
    i = 0
    date_regex = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})')
    
    while i < len(lines):
        m = date_regex.match(lines[i])
        if m:
            date_str = m.group(1)
            i += 1
            tx_type = lines[i] if i < len(lines) else ''
            i += 1
            narration_parts = []
            while i < len(lines) and not re.search(r'[\d,]+\.\d{2}', lines[i]):
                narration_parts.append(lines[i])
                i += 1
            
            if i < len(lines):
                amt_line = lines[i]
                numbers = re.findall(r'[\d,]+\.\d{2}', amt_line)
                if len(numbers) >= 2:
                    try:
                        amt = float(numbers[0].replace(',', ''))
                        balance = float(numbers[1].replace(',', ''))
                        is_debit = 'WDL' in tx_type or '-' in amt_line
                        transactions.append({
                            'date': pd.to_datetime(date_str, format='%d/%m/%Y').strftime('%Y-%m-%d'),
                            'narration': ' '.join(narration_parts),
                            'debit': amt if is_debit else 0.0,
                            'credit': 0.0 if is_debit else amt,
                            'balance': balance,
                            'mode': 'UPI' if 'UPI' in ' '.join(narration_parts) else 'TRANSFER',
                            'source': os.path.basename(filepath)
                        })
                    except ValueError:
                        pass
            i += 1
        else:
            i += 1
    return transactions

def parse_standard_bank_csv(filepath: str, skipped_rows: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Parses standard bank statement CSVs (HDFC, ICICI, SBI, Axis, synthetic CSVs).
    Rows that have an amount but a missing or unreadable date are not imported; if
    `skipped_rows` is given, each one is appended as {"row_number", "raw_date", "values"},
    where row_number is the line in the file.
    """
    df = None
    header_line = 1
    for skip in (0, 1, 2, 3, 4, 5):
        try:
            temp_df = pd.read_csv(filepath, skiprows=skip)
            cols_lower = [str(c).strip().lower() for c in temp_df.columns]
            if any("date" in c for c in cols_lower) and (any("narration" in c or "desc" in c or "particular" in c or "detail" in c for c in cols_lower) or any("debit" in c for c in cols_lower)):
                df = temp_df
                header_line = skip + 1
                break
        except Exception:
            continue
            
    if df is None:
        try:
            df = pd.read_csv(filepath)
        except Exception:
            return []

    col_map = {}
    for c in df.columns:
        cl = str(c).strip().lower()
        if "date" in cl and "val" not in cl:
            col_map["date"] = c
        elif any(k in cl for k in ("narration", "description", "particulars", "detail", "remarks")):
            col_map["narration"] = c
        elif any(k in cl for k in ("debit", "withdrawal", "dr", "dr_amt")):
            col_map["debit"] = c
        elif any(k in cl for k in ("credit", "deposit", "cr", "cr_amt")):
            col_map["credit"] = c
        elif any(k in cl for k in ("balance", "bal", "closing")):
            col_map["balance"] = c
        elif "amount" in cl:
            col_map["amount"] = c
        elif "type" in cl:
            col_map["type"] = c

    if "date" not in col_map:
        return []

    day_first = detect_day_first(df[col_map["date"]].dropna())
    transactions = []
    running_balance = 0.0

    for idx, (_, row) in enumerate(df.iterrows()):
        try:
            narration = str(row[col_map["narration"]]).strip() if "narration" in col_map else ""
            if narration == "nan":
                narration = ""

            debit = 0.0
            credit = 0.0

            if "debit" in col_map:
                d_str = str(row[col_map["debit"]]).replace(",", "").strip()
                debit = float(d_str) if d_str and d_str not in ("nan", "-", "null") else 0.0
            if "credit" in col_map:
                c_str = str(row[col_map["credit"]]).replace(",", "").strip()
                credit = float(c_str) if c_str and c_str not in ("nan", "-", "null") else 0.0

            if debit == 0.0 and credit == 0.0 and "amount" in col_map:
                amt_str = str(row[col_map["amount"]]).replace(",", "").strip()
                amt = float(amt_str) if amt_str and amt_str != "nan" else 0.0
                t_str = str(row.get(col_map.get("type", ""), "")).lower()
                if "debit" in t_str or "dr" in t_str or "-" in amt_str:
                    debit = abs(amt)
                else:
                    credit = abs(amt)

            if debit == 0.0 and credit == 0.0:
                continue

            date_str = parse_statement_date(row[col_map["date"]], day_first)
            if not date_str:
                if skipped_rows is not None:
                    raw_date = row[col_map["date"]]
                    skipped_rows.append({
                        "row_number": header_line + 1 + idx,
                        "raw_date": "" if pd.isna(raw_date) else str(raw_date).strip(),
                        "values": {str(k): ("" if pd.isna(v) else str(v)) for k, v in row.items()},
                    })
                continue

            if "balance" in col_map:
                b_str = str(row[col_map["balance"]]).replace(",", "").strip()
                bal = float(b_str) if b_str and b_str not in ("nan", "-", "null") else running_balance
            else:
                running_balance = running_balance - debit + credit
                bal = running_balance

            running_balance = bal

            tx = {
                "date": date_str,
                "narration": narration,
                "debit": debit,
                "credit": credit,
                "balance": bal,
                "mode": "UPI" if "UPI" in narration else ("ACH" if "ACH" in narration else ("POS" if "POS" in narration else "NETBANKING")),
                "source": os.path.basename(filepath)
            }
            if "merchant" in row and pd.notna(row["merchant"]):
                tx["merchant"] = str(row["merchant"])
            if "category" in row and pd.notna(row["category"]):
                tx["category"] = str(row["category"])
            if "sub_category" in row and pd.notna(row["sub_category"]):
                tx["sub_category"] = str(row["sub_category"])

            transactions.append(tx)
        except Exception:
            continue

    return transactions

def parse_phonepe_csv(filepath: str) -> List[Dict[str, Any]]:
    """Parses PhonePe export CSV & synthetic CSVs."""
    df = pd.read_csv(filepath, skiprows=2)
    # Strip whitespace from columns
    df.columns = [c.strip() for c in df.columns]
    
    transactions = []
    running_balance = 0.0
    
    for _, row in df.iterrows():
        try:
            amt_str = str(row['Amount']).replace(',', '').strip()
            amt = float(amt_str) if amt_str and amt_str != 'nan' else 0.0
            
            tx_type = str(row.get('Transaction Type', '')).strip().lower()
            is_debit = 'debit' in tx_type
            
            # Standardize date to YYYY-MM-DD
            raw_date = str(row.get('Date', '')).strip()
            std_date = pd.to_datetime(raw_date, errors='coerce')
            date_str = std_date.strftime('%Y-%m-%d') if pd.notnull(std_date) else raw_date
            
            # Update virtual running balance if not provided by bank
            if is_debit:
                running_balance -= amt
            else:
                running_balance += amt
                
            narration = f"{row.get('Transaction Details', '')}".strip()
            
            transactions.append({
                'date': date_str,
                'narration': narration,
                'debit': amt if is_debit else 0.0,
                'credit': 0.0 if is_debit else amt,
                'balance': running_balance,
                'mode': 'UPI',
                'source': os.path.basename(filepath)
            })
        except Exception as e:
            continue
            
    # Normalize running balance so it never starts negative
    min_bal = min([t['balance'] for t in transactions]) if transactions else 0.0
    if min_bal < 0:
        offset = abs(min_bal) + 15000.0
        for t in transactions:
            t['balance'] = round(t['balance'] + offset, 2)
            
    return transactions

def parse_statement_file(filepath: str, skipped_rows: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Universal router that detects statement type and parses.
    If `skipped_rows` is given, rows the generic CSV/Excel parser could not read are appended to it.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.csv':
        csv_skipped: List[Dict[str, Any]] = []
        res = parse_standard_bank_csv(filepath, csv_skipped)
        if len(res) > 0:
            if skipped_rows is not None:
                skipped_rows.extend(csv_skipped)
            return res
        try:
            res = parse_phonepe_csv(filepath)
        except Exception as e:
            print(f"Not a PhonePe CSV ({os.path.basename(filepath)}): {e}")
            res = []
        if not res and skipped_rows is not None:
            skipped_rows.extend(csv_skipped)
        return res
    elif ext in ('.xlsx', '.xls'):
        res = parse_paytm_excel(filepath)
        if len(res) > 0:
            return res
        return parse_standard_excel(filepath, skipped_rows)
    elif ext == '.pdf':
        # 1. Detect if Google Pay PDF
        if is_gpay_pdf(filepath):
            res = parse_gpay_pdf(filepath)
            if len(res) > 0:
                return res

        # 2. Detect if Paytm PDF statement
        if is_paytm_pdf(filepath):
            res = parse_paytm_pdf(filepath)
            if len(res) > 0:
                return res

        # 3. Check if table-based (SBI YONO, including alternating-page tables)
        with pdfplumber.open(filepath) as pdf:
            has_tables = any(len(p.extract_tables()) > 0 for p in pdf.pages[:3])
        if has_tables:
            res = parse_sbi_yono_pdf(filepath)
            if len(res) > 0:
                return res

        # 4. Check SBI Netbanking stream format
        res = parse_sbi_netbanking_pdf(filepath)
        if len(res) > 0:
            return res

        # 5. Fallback attempt with GPay parser
        res = parse_gpay_pdf(filepath)
        if len(res) > 0:
            return res

        # 6. Fallback attempt with Paytm PDF parser
        res = parse_paytm_pdf(filepath)
        if len(res) > 0:
            return res

        return []
    else:
        raise ValueError(f"Unsupported file format: {ext}")

if __name__ == '__main__':
    all_data = []
    pdf_files = sorted(glob.glob('*.pdf'))
    print(f"Found {len(pdf_files)} PDF statements: {pdf_files}")
    for f in pdf_files:
        parsed = parse_statement_file(f)
        print(f" -> {f}: Successfully parsed {len(parsed)} transactions")
        all_data.extend(parsed)
        
    unified_df = pd.DataFrame(all_data)
    unified_df = unified_df.sort_values(by='date').reset_index(drop=True)
    out_csv = 'parsed_real_transactions.csv'
    unified_df.to_csv(out_csv, index=False)
    print(f"\n[DONE] Combined {len(unified_df)} total transactions saved to '{out_csv}'.")
    print(unified_df.head(5))
