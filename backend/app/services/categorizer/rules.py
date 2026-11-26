"""
Transaction Normalizer & Categorizer Engine
Enhanced Rules + Heuristics for Indian UPI & Bank Statements
"""

import re
from typing import Dict, Tuple, Optional, Any

KNOWN_PATTERNS = [
    # 1. Food Delivery, Restaurants, Cafeterias, Bakeries, Canteens (generic and national brands only)
    (r'(?i)(zomato|swiggy|eatsure|faasos|behrouz|mcdonald|kfc|burger king|burger k\b|domino|pizza|pizzahut|zaitoon|usha cafe|cane crush|vajra ca\b|nescafe|cream st\b|srivari|juice\b)', 'Discretionary', 'Food Delivery & Dining'),
    (r'(?i)(bakery|bakers|bake\b|chai|\btea\b|coffee|cafe|darshini|hotel|restaurant|biriyani|biri\b|dhaba|sweets|canteen|food\s*court)', 'Discretionary', 'Food Delivery & Dining'),
    
    # 2. Quick Commerce, Supermarkets, Provisions & Groceries
    (r'(?i)(blinkit|zepto|bigbasket|instamart|dmart|supermarket|kirana|grocer|provision|freshto|reliance\s*fresh|nature\s*basket|more\s*retail|milky mist)', 'Variable Essentials', 'Groceries & Supplies'),

    # 3. Healthcare, Eyewear, Pharmacy & Medical
    (r'(?i)(apollo|pharmeasy|netmeds|1mg|medplus|clinic|hospital|doctor|pharmacy|dental|lab|lenskart|vision\s*express)', 'Variable Essentials', 'Healthcare & Eyewear'),

    # 4. Education, Academic, Hostels, Coliving & Rent
    (r'(?i)cf\.isthara', 'Discretionary', 'Food Delivery & Dining'),  # Isthara's food courts; its co-living rent falls through to the next rule
    (r'(?i)(isthara|coliving|co-living|stanza|luxury mens pg|pg\b|flat rent|chq dep rent)', 'Fixed Expenses', 'Loan EMIs & Rent'),
    (r'(?i)(indian\s*institute|iitm|iit\b|hostel|mess\b|institute|college|university|exam|fees|tuition|xerox|stationery|library)', 'Variable Essentials', 'Education & Academic'),

    # 5. Public Transit, Cabs, Auto & Commute
    (r'(?i)(bmrcl|metro|namma metro)', 'Variable Essentials', 'Public Transit & Metro'),
    (r'(?i)(uber|ola|rapido)', 'Variable Essentials', 'Ride Hailing & Auto'),
    (r'(?i)(irctc|railway|makemytrip|goibibo|ixigo|flight|airways|air india|vistara|indigo\b)', 'Discretionary', 'Travel & Vacation'),
    (r'(?i)(petrol|fuel|hpcl|bpcl|iocl|shell)', 'Variable Essentials', 'Fuel & Commute'),

    # 6. Streaming, Digital Subscriptions & App Stores
    (r'(?i)\b(netflix|spotify|hotstar|youtube|sony liv|disney\+|patreon)\b|amazon\s*prime|apple\s*music|apple\s*services|appleservi|itunes|google\s*play|google\s*storage', 'Fixed Expenses', 'Subscriptions'),
    (r'(?i)(amoeba|pvr|inox|cinepolis|gaming|bowling|bookmyshow)', 'Discretionary', 'Entertainment & Outings'),
    
    # 7. Cloud, Developer & Hosting Tools
    (r'(?i)(aws\s*india|amazonaws|google\s*cloud|googleclou|digitalocean|cloudflare|github|cursor|openai)', 'Fixed Expenses', 'Cloud & Tech Tools'),

    # 8. Utilities, Broadband & Recharges (strict boundaries so names like Manvi aren't matched)
    (r'(?i)\b(airtel|jio|vodafone|bsnl|bescom|tneb|electricity|water\s*board|gas|broadband|act\s*fiber)\b|\bvi\s+recharge\b|\bbill\s*payment\b', 'Fixed Expenses', 'Utilities & Bills'),

    # 9. Shopping & E-Commerce
    (r'(?i)(amazon|flipkart|myntra|ajio|meesho|tata cliq|zara|h&m|decathlon|nykaa|purplle|zudio)', 'Discretionary', 'Shopping & E-Commerce'),

    # 10. Insurance & Loan EMIs
    (r'(?i)(lic\b|hdfc life|icici pru|max life|star health|care health|bajaj allianz|tata aia)', 'Fixed Expenses', 'Insurance Premiums'),
    (r'(?i)(emi\b|loan\b|bajaj finserv|hsg loan)', 'Fixed Expenses', 'Loan EMIs'),

    # 11. Investments & Mutual Funds
    (r'(?i)(dspim|prudent|uti mut|whiteoak|motilal oswal|groww|mutual fund|mf redemp|zerodha|coin\b|kuvera|cams\b|kfin)', 'Investments', 'Mutual Funds & Equities'),
]

def clean_narration(
    narration: str, 
    debit: float = 0.0, 
    credit: float = 0.0,
    merchant_dict: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, str]:
    """
    Cleans messy Indian bank narration string and assigns accurate Category and Sub-category.
    Checks merchant_dict first if available.
    Returns: (cleaned_merchant, category, sub_category)
    """
    narration_clean = str(narration or '').strip()
    
    # Check for self transfers
    if 'transferred to self' in narration_clean.lower() or 'self transfer' in narration_clean.lower():
        return "Self Transfer", "Transfers & P2P", "Self Transfer"

    # 1. Clean UPI strings:
    # Conversational formats (Google Pay, Paytm, PhonePe): Paid to X, Money sent to X, Received from X, Refund from X
    cleaned_name = narration_clean
    nl_match = re.search(r'^(?:Paid\s*to|Money\s*sent\s*to|Received\s*from|Refund\s*from|Transferred\s*to)\s+(.*?)(?:\s+(?:UPI\s*Transaction\s*ID[:\s]*|UPI\s*ID[:\s]*|UPI\s*Ref\s*No[:\s]*|Note[:\s]*|Tag[:\s]*|Order\s*ID[:\s]*|Paid\s*by|Paid\s*to)|$)', narration_clean, re.IGNORECASE)
    if nl_match and nl_match.group(1).strip():
        cleaned_name = nl_match.group(1).strip()
    else:
        upi_match = re.search(r'UPI/(?:DR|CR)/\d+/([^/]+)/', narration_clean)
        if upi_match:
            cleaned_name = upi_match.group(1).strip()
        else:
            # Strip common banking prefixes
            cleaned_name = re.sub(r'^(?:UPI/DR/|UPI/CR/|WDL TFR|DEP TFR|NEFT CR-|ACH D-|ACH C-)', '', narration_clean).strip()
            cleaned_name = cleaned_name.split('/')[0].strip()

    # Split camelCase and common merged uppercase tokens
    cleaned_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned_name)
    cleaned_name = re.sub(r'(\b[A-Z]+)(PARKS)', r'\1 \2', cleaned_name)
    cleaned_name = re.sub(r'(PARKS)(PRIVATE)', r'\1 \2', cleaned_name)
    cleaned_name = re.sub(r'(PRIVATE)(LIMITED)', r'\1 \2', cleaned_name)
    cleaned_name = re.sub(r'(PVT)(LTD)', r'\1 \2', cleaned_name)
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()

    # 2. Inflow / Credit transactions (Must NEVER be classified as Local Vendor / Street Pay)
    if credit > 0 or 'INTEREST CREDIT' in narration_clean.upper() or 'UPI/CR/' in narration_clean.upper() or 'CR' == narration_clean.split('/')[-1].strip().upper():
        if re.search(r'(?i)(interest|int\.pd|bank\s*int)', narration_clean):
            return "Bank Interest Credit", "Income", "Bank Interest"
        if re.search(r'(?i)(cashback|bhimcashba|reward|loyalty)', narration_clean):
            return "Cashback Reward", "Income", "Cashbacks & Rewards"
        if re.search(r'(?i)(refund|upi/ref/|reversal|rev-)', narration_clean):
            return cleaned_name or "Refund / Reversal", "Income", "Refunds & Reversals"
        if re.search(r'(?i)(salary|sal\s+cr|payroll)', narration_clean):
            return cleaned_name or "Salary Credit", "Income", "Salary"
        return cleaned_name or "Transfer In", "Income", "Transfers In (P2P)"

    # Check explicit statement tags (e.g. Paytm tag: #Food, #Groceries, #Bill Payments, #Shopping)
    if re.search(r'(?i)#\s*food\b', narration_clean):
        return cleaned_name, "Discretionary", "Food Delivery & Dining"
    if re.search(r'(?i)#\s*grocer', narration_clean):
        return cleaned_name, "Variable Essentials", "Groceries & Supplies"
    if re.search(r'(?i)#\s*bill\s*payment', narration_clean):
        return cleaned_name, "Fixed Expenses", "Utilities & Bills"
    if re.search(r'(?i)#\s*shopping\b', narration_clean):
        return cleaned_name, "Discretionary", "Shopping & E-Commerce"
    if re.search(r'(?i)#\s*medical\b', narration_clean):
        return cleaned_name, "Variable Essentials", "Healthcare & Eyewear"
    if re.search(r'(?i)#\s*education\b', narration_clean):
        return cleaned_name, "Variable Essentials", "Education & Academic"
    if re.search(r'(?i)#\s*travel\b', narration_clean):
        return cleaned_name, "Discretionary", "Travel & Vacation"
    if re.search(r'(?i)#\s*(?:money\s*transfer|p2p)\b', narration_clean):
        return cleaned_name, "Transfers & P2P", "Transfer to Friends & Contacts"
    if re.search(r'(?i)^money\s+sent\s+to\b', narration_clean):
        return cleaned_name, "Transfers & P2P", "Transfer to Friends & Contacts"

    # 3. Check Merchant Dictionary (AI learned or user verified)
    if merchant_dict:
        norm_key = re.sub(r'[/\\_,-]+', ' ', cleaned_name.upper()).strip()
        norm_key = re.sub(r'\s+', ' ', norm_key)
        if norm_key in merchant_dict:
            entry = merchant_dict[norm_key]
            # Only apply if verified, from LLM, or confidence > 0.40 so low-confidence fallbacks don't block rule matching
            if entry.get("verified") or entry.get("source") == "llm" or entry.get("confidence", 0) > 0.40:
                return cleaned_name, entry.get("category", "Discretionary"), entry.get("sub_category", "Local Shopping & Services")

    # 4. Known entity pattern matching for Debits
    for pattern, cat, subcat in KNOWN_PATTERNS:
        if re.search(pattern, narration_clean):
            return cleaned_name, cat, subcat

    # 5. Peer-to-Peer (P2P) Transfers vs Commercial Merchants
    # If the VPA or narration contains a 10-digit mobile number or personal titles (Miss/Mr/Mrs)
    is_p2p = bool(re.search(r'(?i)\b[6-9]\d{9}\b|\b(miss|mr|mrs)\b', narration_clean))
    if is_p2p:
        return cleaned_name, "Transfers & P2P", "Transfer to Friends & Contacts"

    # 6. Fallback heuristics for unbranded vendors
    if debit > 500:
        return cleaned_name, 'Discretionary', 'Local Shopping & Services'
    else:
        return cleaned_name, 'Daily Micro-Spends', 'Local Vendor / Street Pay'

