"""
De-identification engine — NEVER writes PII to disk.
All transformations happen in memory.
"""
import csv
import hashlib
import hmac
import os
from datetime import date, datetime

DEID_SALT = os.environ.get('DEID_SALT', 'dev-salt-change-in-prod')

# ── PII fields to drop entirely ───────────────────────────────────────────────
DROP_FIELDS = {'first_name', 'last_name', 'ssn', 'street_address'}

# ── Geography helpers ─────────────────────────────────────────────────────────
REGION_MAP = {
    'West':      {'CA','OR','WA','NV','AZ','CO','UT','ID','MT','WY','NM','AK','HI'},
    'South':     {'TX','FL','GA','NC','SC','VA','AL','MS','LA','AR','TN','KY','WV','MD','DE','OK'},
    'Midwest':   {'IL','OH','MI','IN','WI','MN','IA','MO','ND','SD','NE','KS'},
    'Northeast': {'NY','PA','NJ','CT','MA','RI','NH','VT','ME'},
}

def _region(state: str) -> str:
    for region, states in REGION_MAP.items():
        if state in states:
            return region
    return 'Other'

# ── Employer → industry / tier lookup ────────────────────────────────────────
EMPLOYER_INDUSTRY = {
    'Google': 'Technology', 'Meta': 'Technology', 'Apple': 'Technology',
    'Amazon': 'Technology', 'Microsoft': 'Technology', 'Intel': 'Technology',
    'Bank of America': 'Finance', 'Wells Fargo': 'Finance', 'JPMorgan': 'Finance',
    'Walmart': 'Retail', 'Target': 'Retail', 'Costco': 'Retail',
    'Kaiser': 'Healthcare', 'HCA': 'Healthcare', 'CVS': 'Healthcare',
    'Boeing': 'Defense', 'Lockheed': 'Defense',
    'Chevron': 'Energy', 'ExxonMobil': 'Energy',
}

FORTUNE500 = set(EMPLOYER_INDUSTRY.keys())


def _employer_industry(employer: str) -> str:
    return EMPLOYER_INDUSTRY.get(employer, 'SMB')

def _employer_tier(employer: str) -> str:
    return 'Fortune500' if employer in FORTUNE500 else 'SMB'

def _employment_stability(status: str, employer: str) -> str:
    tier = _employer_tier(employer)
    if status == 'Employed' and tier == 'Fortune500':
        return 'high'
    if status == 'Employed' and tier == 'SMB':
        return 'medium'
    if status == 'Self-Employed':
        return 'medium'
    return 'low'  # Retired, Unemployed

# ── HMAC-SHA256 token ─────────────────────────────────────────────────────────
def _token(value: str, salt: str) -> str:
    return hmac.new(salt.encode(), value.encode(), hashlib.sha256).hexdigest()

# ── Age / life stage / generation ────────────────────────────────────────────
def _age_from_dob(dob_str: str) -> int:
    dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def _age_range(age: int) -> str:
    lo = (age // 5) * 5
    return f'{lo}-{lo+4}'

def _life_stage(age: int) -> str:
    if age < 35:
        return 'early-career'
    if age < 55:
        return 'mid-career'
    if age < 65:
        return 'pre-retirement'
    return 'retirement'

def _generation(age: int) -> str:
    if age < 27:
        return 'GenZ'
    if age <= 42:
        return 'Millennial'
    if age <= 58:
        return 'GenX'
    if age <= 77:
        return 'Boomer'
    return 'Silent'

# ── Income bucket helpers ─────────────────────────────────────────────────────
def _income_range(income: float) -> str:
    if income < 30_000:   return '<30k'
    if income < 50_000:   return '30k-50k'
    if income < 75_000:   return '50k-75k'
    if income < 100_000:  return '75k-100k'
    if income < 150_000:  return '100k-150k'
    if income < 200_000:  return '150k-200k'
    return '200k+'

def _income_tier(income: float) -> str:
    if income < 30_000:   return 'lower'
    if income < 50_000:   return 'lower-middle'
    if income < 100_000:  return 'middle'
    if income < 150_000:  return 'upper-middle'
    return 'upper'

# ── Loan amount bucket ────────────────────────────────────────────────────────
def _loan_amount_bucket(amount: float) -> str:
    lo = (int(amount) // 50_000) * 50_000
    hi = lo + 50_000
    return f'{lo // 1000}k-{hi // 1000}k'

# ── FICO band / credit profile ────────────────────────────────────────────────
def _fico_band(score: int) -> str:
    bands = [300, 580, 620, 660, 700, 740, 760, 780, 800, 9999]
    for i in range(len(bands) - 1):
        if score < bands[i + 1]:
            lo, hi = bands[i], bands[i + 1] - 1
            if hi >= 9998:
                return '800+'
            return f'{lo}-{hi}'
    return '800+'

def _credit_profile(score: int) -> str:
    if score < 580:   return 'Poor'
    if score < 620:   return 'Fair'
    if score < 700:   return 'Good'
    if score < 760:   return 'Very Good'
    return 'Excellent'

# ── Ratio buckets (0.05 increments) ──────────────────────────────────────────
def _ratio_bucket(ratio: float) -> str:
    lo = (int(ratio * 20)) / 20  # floor to nearest 0.05
    hi = lo + 0.05
    return f'{lo:.2f}-{hi:.2f}'

# ── Tenure band ───────────────────────────────────────────────────────────────
def _tenure_band(years: float) -> str:
    if years < 1:    return '<1yr'
    if years < 3:    return '1-3yr'
    if years < 7:    return '3-7yr'
    if years < 15:   return '7-15yr'
    return '15+ years'

# ── Main de-identification function ──────────────────────────────────────────
def deid_csv(csv_path: str, salt: str = None) -> list:
    if salt is None:
        salt = DEID_SALT

    signal_records = []

    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for raw in reader:
            # Drop PII fields (operate on copy, never persist)
            row = {k: v for k, v in raw.items() if k not in DROP_FIELDS}

            # Tokens
            email_token = _token(row['email'], salt)
            phone_token = _token(row['phone'], salt)

            # Age-derived
            age = _age_from_dob(row['dob'])

            # Employer-derived
            employer = row['employer']
            industry = _employer_industry(employer)
            tier = _employer_tier(employer)
            stability = _employment_stability(row['employment_status'], employer)

            # Financials
            annual_income = float(row['annual_income'])
            loan_amount = float(row['loan_amount'])
            fico_score = int(row['fico_score'])
            dti_ratio = float(row['dti_ratio'])
            ltv_ratio = float(row['ltv_ratio'])

            # Outcome: empty string → None
            outcome_raw = row.get('outcome', '') or None
            outcome = None if (outcome_raw in (None, '', 'None', 'null')) else outcome_raw

            signal = {
                'email_token': email_token,
                'phone_token': phone_token,
                'demographics': {
                    'age_range': _age_range(age),
                    'life_stage': _life_stage(age),
                    'generation': _generation(age),
                    'city': row['city'],
                    'state': row['state'],
                },
                'geography': {
                    'zip3': row['zip'][:3],
                    'region': _region(row['state']),
                    'urban_class': 'Urban',
                },
                'financial': {
                    'credit_profile': _credit_profile(fico_score),
                    'fico_band': _fico_band(fico_score),
                    'income_range': _income_range(annual_income),
                    'income_tier': _income_tier(annual_income),
                    'dti_bucket': _ratio_bucket(dti_ratio),
                    'ltv_bucket': _ratio_bucket(ltv_ratio),
                },
                'employment': {
                    'status': row['employment_status'],
                    'tenure_band': _tenure_band(float(row['employment_tenure_years'])),
                    'industry': industry,
                    'tier': tier,
                    'stability': stability,
                },
                'loan_intent': {
                    'purpose': row['loan_purpose'],
                    'type': row['loan_type'],
                    'amount_bucket': _loan_amount_bucket(loan_amount),
                    'property_type': row['property_type'],
                    'occupancy': row['occupancy'],
                    'term': int(row['loan_term']),
                },
                'lead_behavior': {
                    'channel': row['channel'],
                    'type': row['lead_type'],
                    'score': int(row['lead_score']),
                    'journey_stage': row['journey_stage'],
                    'first_time_buyer': row['first_time_buyer'] in ('True', 'true', '1', True),
                    'quarter': row['quarter'],
                },
                'offer': {
                    'type': row['offer_type'],
                    'rate': float(row['offer_rate']),
                    'monthly_savings': float(row['monthly_savings']),
                    'annual_savings': float(row['annual_savings']),
                },
                'outcome': outcome,
                'tranche_id': row['tranche_id'],
            }

            signal_records.append(signal)

    return signal_records
