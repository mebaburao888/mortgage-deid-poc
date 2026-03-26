import csv
import random
import os

try:
    from faker import Faker
except ImportError:
    print("ERROR: faker is not installed. Run: pip install faker")
    raise SystemExit(1)

fake = Faker()
random.seed(42)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'leads-2026-03-T1.csv')

EMPLOYERS = [
    'Google', 'Microsoft', 'Amazon', 'Apple', 'Meta',
    'Bank of America', 'Wells Fargo', 'JPMorgan',
    'Walmart', 'Target', 'Costco',
    'Kaiser', 'HCA', 'CVS',
    'Boeing', 'Lockheed',
    'Chevron', 'ExxonMobil',
    'Sunrise Plumbing LLC', 'Riverdale Properties Inc'
]

LOAN_PURPOSES = ['Purchase', 'Refinance', 'Cash-Out', 'HELOC']
LOAN_TYPES = ['Conventional', 'FHA', 'VA', 'USDA', 'Jumbo']
PROPERTY_TYPES = ['SFR', 'Condo', 'PUD', 'Multi-Family', 'Manufactured']
OCCUPANCIES = ['Primary', 'Secondary', 'Investment']
CHANNELS = ['Social', 'Direct Mail', 'Search', 'Referral', 'TV']
LEAD_TYPES = ['Warm Transfer', 'Internet Lead', 'Call-In', 'Direct']
JOURNEY_STAGES = ['Awareness', 'Consideration', 'Application', 'Decision']
EMPLOYMENT_STATUSES = ['Employed', 'Self-Employed', 'Retired', 'Unemployed']
OFFER_TYPES = ['Purchase', 'Refinance', 'HELOC', 'Cash-Out', 'VA Loan']
LOAN_TERMS = [10, 15, 20, 30]
QUARTERS = ['Q1', 'Q2', 'Q3', 'Q4']

OUTCOMES_POOL = [None] * 70 + ['funded'] * 10 + ['rejected'] * 8 + ['withdrawn'] * 7 + ['ghost'] * 5

FIELDNAMES = [
    'first_name', 'last_name', 'ssn', 'dob', 'phone', 'email',
    'street_address', 'city', 'state', 'zip', 'employer',
    'employment_status', 'employment_tenure_years', 'industry',
    'annual_income', 'loan_amount', 'loan_purpose', 'loan_type',
    'property_type', 'occupancy', 'loan_term', 'fico_score',
    'dti_ratio', 'ltv_ratio', 'channel', 'lead_type', 'lead_score',
    'journey_stage', 'first_time_buyer', 'offer_type', 'offer_rate',
    'monthly_savings', 'annual_savings', 'outcome', 'quarter', 'tranche_id'
]


def generate_record():
    employer = random.choice(EMPLOYERS)
    annual_income = round(random.uniform(30000, 200000), 2)
    offer_rate = round(random.uniform(5.0, 10.0), 3)
    loan_amount = round(random.uniform(100000, 800000), 2)
    monthly_savings = round(random.uniform(50, 800), 2)
    dob = fake.date_of_birth(minimum_age=22, maximum_age=80).isoformat()

    # Derive industry from employer
    industry_map = {
        'Google': 'Technology', 'Meta': 'Technology', 'Apple': 'Technology',
        'Amazon': 'Technology', 'Microsoft': 'Technology', 'Intel': 'Technology',
        'Bank of America': 'Finance', 'Wells Fargo': 'Finance', 'JPMorgan': 'Finance',
        'Walmart': 'Retail', 'Target': 'Retail', 'Costco': 'Retail',
        'Kaiser': 'Healthcare', 'HCA': 'Healthcare', 'CVS': 'Healthcare',
        'Boeing': 'Defense', 'Lockheed': 'Defense',
        'Chevron': 'Energy', 'ExxonMobil': 'Energy',
    }
    industry = industry_map.get(employer, 'SMB')

    return {
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'ssn': fake.ssn(),
        'dob': dob,
        'phone': fake.phone_number(),
        'email': fake.email(),
        'street_address': fake.street_address(),
        'city': fake.city(),
        'state': fake.state_abbr(),
        'zip': fake.zipcode(),
        'employer': employer,
        'employment_status': random.choice(EMPLOYMENT_STATUSES),
        'employment_tenure_years': round(random.uniform(0, 35), 1),
        'industry': industry,
        'annual_income': annual_income,
        'loan_amount': loan_amount,
        'loan_purpose': random.choice(LOAN_PURPOSES),
        'loan_type': random.choice(LOAN_TYPES),
        'property_type': random.choice(PROPERTY_TYPES),
        'occupancy': random.choice(OCCUPANCIES),
        'loan_term': random.choice(LOAN_TERMS),
        'fico_score': random.randint(580, 850),
        'dti_ratio': round(random.uniform(0.20, 0.60), 4),
        'ltv_ratio': round(random.uniform(0.50, 0.95), 4),
        'channel': random.choice(CHANNELS),
        'lead_type': random.choice(LEAD_TYPES),
        'lead_score': random.randint(1, 100),
        'journey_stage': random.choice(JOURNEY_STAGES),
        'first_time_buyer': random.choice([True, False]),
        'offer_type': random.choice(OFFER_TYPES),
        'offer_rate': offer_rate,
        'monthly_savings': monthly_savings,
        'annual_savings': round(monthly_savings * 12, 2),
        'outcome': random.choice(OUTCOMES_POOL),
        'quarter': random.choice(QUARTERS),
        'tranche_id': '2026-03-T1',
    }


def generate_csv(n=100, output_path=OUTPUT_PATH):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    records = [generate_record() for _ in range(n)]
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)
    print(f"Generated {n} records -> {output_path}")
    return records


if __name__ == '__main__':
    generate_csv()
