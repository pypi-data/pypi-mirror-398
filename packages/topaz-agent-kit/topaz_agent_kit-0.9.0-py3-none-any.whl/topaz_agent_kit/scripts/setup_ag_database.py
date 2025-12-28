#!/usr/bin/env python3
"""Setup script for Appeal Grievance Processor pipeline.

Creates SQLite database, initializes schema, and generates mock data:
- AG Requests tracking table (with response tracking fields)
- Claim History table
- Research Reports table
- Mock emails in "AG/Pending" folder

Usage:
    python scripts/setup_ag_database.py [--db-path <path>] [--reset] [--email-count <n>] [--skip-emails]
    uv run -m scripts.setup_ag_database --db-path projects/ensemble/data/ag/ag_database.db --reset
    
Response Email Configuration:
    --response-recipient-email: Where to send decision letter responses (default: topazagentkit@gmail.com)
    --skip-response-emails: Don't send response emails, only store in database (for testing)
    
Note: Since mock customer emails don't exist, responses are sent to a configurable test recipient
      or stored in database only. The pipeline will always store decision letters in the database.
"""

import sqlite3
import os
import sys
import argparse
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from topaz_agent_kit.utils.path_resolver import resolve_script_path, detect_project_name

# Try to import SimpleGmail for email creation
try:
    from simplegmail import Gmail
    from simplegmail.label import Label
    SIMPLEGMAIL_AVAILABLE = True
except ImportError:
    SIMPLEGMAIL_AVAILABLE = False
    print("Warning: simplegmail not available. Email generation will be skipped.")
    print("Install with: pip install simplegmail")


def create_database_schema(db_path: str) -> None:
    """Create all database tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # AG Requests table - tracks all processed requests
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ag_requests (
            request_id TEXT PRIMARY KEY,
            email_message_id TEXT UNIQUE,
            email_thread_id TEXT,
            sender_email TEXT,
            recipient_email TEXT,
            member_id TEXT,
            member_name TEXT,
            reference_id TEXT,
            classification TEXT,
            category TEXT,
            status TEXT DEFAULT 'pending',
            decision TEXT,
            decision_letter_md TEXT,
            response_sent_at TIMESTAMP,
            response_recipient TEXT,
            response_message_id TEXT,
            error_message TEXT,
            run_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    
    # Claim History table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claim_history (
            tracking_id TEXT PRIMARY KEY,
            member_id TEXT NOT NULL,
            plan_id TEXT,
            member_name TEXT,
            dob TEXT,
            date_of_service TEXT,
            provider_name TEXT,
            claim_status TEXT,
            claim_type TEXT,
            procedure_code TEXT,
            billed_amount REAL,
            paid_amount REAL,
            action_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Research Reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_reports (
            research_id TEXT PRIMARY KEY,
            reference_id TEXT,
            member_id TEXT,
            research_date TEXT,
            researcher_name TEXT,
            medication_name TEXT,
            diagnosis_code TEXT,
            initial_denial_reason TEXT,
            benefit_exclusion TEXT,
            previous_decision_maker TEXT,
            research_notes TEXT,
            decision_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for faster lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claim_history_member_id ON claim_history(member_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claim_history_reference_id ON claim_history(tracking_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_reports_reference_id ON research_reports(reference_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_reports_member_id ON research_reports(member_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ag_requests_email_message_id ON ag_requests(email_message_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ag_requests_member_id ON ag_requests(member_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ag_requests_reference_id ON ag_requests(reference_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ag_requests_run_id ON ag_requests(run_id)")
    
    conn.commit()
    conn.close()
    print("✓ Database schema created")


def generate_mock_members(count: int = 5) -> List[Dict[str, Any]]:
    """Generate mock member data with diverse names from different countries."""
    # Western names
    western_first = ["Archie", "Sarah", "Michael", "Emma", "David", "Jessica", "Robert", "Amanda", "James", "Lisa", 
                     "Christopher", "Jennifer", "Matthew", "Emily", "Daniel", "Ashley", "Andrew", "Michelle", "Joshua", "Nicole"]
    western_last = ["Saunders", "Johnson", "Rodriguez", "Williams", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
                    "Anderson", "Martinez", "Garcia", "Lee", "White", "Harris", "Clark", "Lewis", "Walker", "Hall"]
    
    # Hispanic/Latino names
    hispanic_first = ["Carlos", "Maria", "Jose", "Ana", "Luis", "Carmen", "Miguel", "Sofia", "Diego", "Isabella",
                      "Fernando", "Elena", "Ricardo", "Gabriela", "Alejandro", "Valentina", "Andres", "Camila", "Javier", "Lucia"]
    hispanic_last = ["Garcia", "Rodriguez", "Martinez", "Lopez", "Gonzalez", "Perez", "Sanchez", "Ramirez", "Torres", "Flores",
                     "Rivera", "Gomez", "Diaz", "Cruz", "Morales", "Ortiz", "Ramos", "Mendoza", "Vargas", "Herrera"]
    
    # Asian names
    asian_first = ["Wei", "Li", "Zhang", "Wang", "Chen", "Liu", "Yang", "Huang", "Zhao", "Wu",
                   "Hiroshi", "Yuki", "Kenji", "Aiko", "Takeshi", "Mei", "Raj", "Priya", "Amit", "Anjali"]
    asian_last = ["Chen", "Wang", "Li", "Zhang", "Liu", "Wu", "Yang", "Huang", "Zhou", "Xu",
                 "Tanaka", "Yamamoto", "Sato", "Kumar", "Patel", "Singh", "Sharma", "Kim", "Park", "Lee"]
    
    # Middle Eastern names
    middle_eastern_first = ["Ahmed", "Fatima", "Mohammed", "Aisha", "Omar", "Layla", "Hassan", "Zara", "Ibrahim", "Noor",
                           "Ali", "Sara", "Yusuf", "Maya", "Khalid", "Amira", "Malik", "Leila", "Tariq", "Rania"]
    middle_eastern_last = ["Al-Ahmad", "Hassan", "Ibrahim", "Ali", "Khan", "Malik", "Rahman", "Hussein", "Abbas", "Nasser",
                          "Mahmoud", "Farid", "Zayed", "Omar", "Said", "Hamid", "Rashid", "Tariq", "Khalil", "Noor"]
    
    # African names
    african_first = ["Kwame", "Amina", "Kofi", "Zara", "Jabari", "Nia", "Malik", "Keisha", "Darius", "Imani",
                    "Tunde", "Adeola", "Chukwu", "Ifeoma", "Oluwaseun", "Chioma", "Thabo", "Nomsa", "Sipho", "Lindiwe"]
    african_last = ["Okafor", "Nwosu", "Adebayo", "Okafor", "Okonkwo", "Adeyemi", "Mthembu", "Ndlovu", "Kone", "Diallo",
                   "Traore", "Sangare", "Kamau", "Njoroge", "Ochieng", "Mwangi", "Kipchoge", "Wanjiru", "Onyango", "Achieng"]
    
    # Combine all name pools
    all_first_names = western_first + hispanic_first + asian_first + middle_eastern_first + african_first
    all_last_names = western_last + hispanic_last + asian_last + middle_eastern_last + african_last
    
    members = []
    for i in range(count):
        first = random.choice(all_first_names)
        last = random.choice(all_last_names)
        member_id = str(100000 + i)
        dob_month = random.randint(1, 12)
        dob_day = random.randint(1, 28)
        dob_year = random.randint(1950, 2000)
        
        members.append({
            "member_id": member_id,
            "member_name": f"{first} {last}",
            "dob": f"{dob_month:02d}/{dob_day:02d}/{dob_year}",
            "email": f"{first.lower()}.{last.lower()}@example.com"
        })
    
    return members


def generate_mock_providers(count: int = 10, base_email: str = "topazagentkit@gmail.com") -> List[Dict[str, Any]]:
    """Generate mock provider data (doctors, clinics, etc.).
    
    Args:
        count: Number of providers to generate
        base_email: Base email address to use for Gmail + aliases (default: topazagentkit@gmail.com)
                    If you set up Gmail "Send As" aliases, use those addresses instead
    """
    provider_first_names = ["Max", "Patricia", "Benjamin", "Jennifer", "Robert", "Amanda", "David", "Sarah", "Michael", "Lisa"]
    provider_last_names = ["Reynolds", "Williams", "Brooks", "Martinez", "Chen", "Thompson", "Anderson", "Garcia", "Lee", "White"]
    
    clinic_names = [
        "Internal Medicine Associates",
        "Orthopedic Specialists",
        "Regional Medical Group",
        "City General Hospital",
        "Specialty Care Center",
        "Primary Care Associates",
        "Urban Health Clinic",
        "Advanced Medical Center",
        "Community Health Partners",
        "Metro Healthcare"
    ]
    
    specialties = [
        "Internal Medicine",
        "Orthopedics",
        "Rheumatology",
        "Cardiology",
        "Oncology",
        "Pediatrics",
        "Family Medicine",
        "Endocrinology",
        "Neurology",
        "Pulmonology"
    ]
    
    # Extract base email (before @) for + alias generation
    base_email_local = base_email.split('@')[0]
    base_email_domain = base_email.split('@')[1] if '@' in base_email else 'gmail.com'
    
    # Use Gmail + aliases for all providers (no verification needed, Gmail recognizes them)
    # Format: topazagentkit+dr.firstname.lastname.clinicname@gmail.com
    providers = []
    for i in range(count):
        first = random.choice(provider_first_names)
        last = random.choice(provider_last_names)
        clinic = random.choice(clinic_names)
        specialty = random.choice(specialties)
        
        # Generate Gmail + alias format (works automatically, no verification needed)
        # Clean clinic name for alias (remove spaces, special chars)
        clinic_alias = clinic.lower().replace(' ', '').replace('associates', 'med').replace('specialists', 'med')
        provider_alias = f"dr.{first.lower()}.{last.lower()}.{clinic_alias}"
        provider_email = f"{base_email_local}+{provider_alias}@{base_email_domain}"
        
        providers.append({
            "provider_id": f"PROV-{1000 + i:04d}",
            "provider_name": f"Dr. {first} {last}",
            "clinic_name": clinic,
            "specialty": specialty,
            "email": provider_email
        })
    
    return providers


def generate_mock_claim_history(cursor, members: List[Dict[str, Any]], provider_list: List[Dict[str, Any]] = None) -> None:
    """Generate mock claim history data for members.
    
    Args:
        cursor: Database cursor
        members: List of member dictionaries
        provider_list: Optional list of provider dictionaries to link claims to specific providers
    """
    # Use provider list if provided, otherwise use simple provider names
    if provider_list:
        provider_names = [p["clinic_name"] for p in provider_list]
    else:
        provider_names = [
            "Internal Med Assoc.", "Orthopedic Assoc.", "RESNA Mobility", 
            "Urban Health Clinic", "City General Hospital", "Specialty Care Center",
            "Primary Care Associates", "Regional Medical Group"
        ]
    
    procedure_codes = {
        "Medical": ["99213", "99214", "99202", "99203", "99215"],
        "Lab": ["80053", "85025", "85610", "86580"],
        "Pharmacy": ["J0129", "J0135", "J1745"],
        "DME": ["E0143", "E0148", "E1390"]
    }
    
    action_codes = [
        "",  # Empty for paid claims
        "W91 - denied no precert",
        "W88 - Frequency limit exceeded or insufficient documentation to support high-level visit",
        "W25 - not a covered benefit",
        "W50 - service not authorized",
        "W27 - experimental/investigational"
    ]
    
    claim_types = ["Medical", "Lab", "Pharmacy", "DME"]
    
    for member in members:
        # Generate 3-8 claims per member
        num_claims = random.randint(3, 8)
        base_date = datetime.now() - timedelta(days=random.randint(30, 180))
        
        for i in range(num_claims):
            tracking_id = str(random.randint(100000, 999999))
            claim_type = random.choice(claim_types)
            procedure_code = random.choice(procedure_codes.get(claim_type, ["99213"]))
            
            # 60% paid, 40% denied
            is_paid = random.random() < 0.6
            claim_status = "Paid" if is_paid else "Denied"
            
            billed_amount = round(random.uniform(50, 500), 2)
            paid_amount = round(billed_amount * random.uniform(0.8, 1.0), 2) if is_paid else 0.0
            action_code = "" if is_paid else random.choice(action_codes[1:])
            
            # Store date in ISO format (YYYY-MM-DD) for proper sorting
            service_date_obj = base_date + timedelta(days=random.randint(0, 60))
            service_date = service_date_obj.strftime("%Y-%m-%d")  # ISO format for sorting
            
            cursor.execute("""
                INSERT OR REPLACE INTO claim_history 
                (tracking_id, member_id, plan_id, member_name, dob, date_of_service, 
                 provider_name, claim_status, claim_type, procedure_code, billed_amount, 
                 paid_amount, action_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tracking_id,
                member["member_id"],
                "P12005",
                member["member_name"],
                member["dob"],
                service_date,
                random.choice(provider_names),
                claim_status,
                claim_type,
                procedure_code,
                billed_amount,
                paid_amount,
                action_code
            ))
    
    print(f"✓ Generated claim history for {len(members)} members")


def generate_mock_research_reports(cursor, members: List[Dict[str, Any]]) -> None:
    """Generate mock research reports."""
    medications = [
        "Kineret", "Humira", "Enbrel", "Remicade", "Stelara", 
        "Cosentyx", "Taltz", "Orencia", "Actemra", "Xeljanz"
    ]
    
    diagnosis_codes = [
        "M04.9 - Autoinflammatory syndrome, unspecified",
        "M05.9 - Rheumatoid arthritis, unspecified",
        "M79.3 - Panniculitis, unspecified",
        "K50.9 - Crohn's disease, unspecified",
        "L40.9 - Psoriasis, unspecified"
    ]
    
    denial_reasons = [
        "Medical Necessity",
        "Prior Authorization Required",
        "Not a Covered Benefit",
        "Experimental/Investigational",
        "Frequency Limit Exceeded"
    ]
    
    researchers = [
        "Benjamin Brooks", "Patricia Williams", "Robert Chen", 
        "Jennifer Martinez", "David Thompson"
    ]
    
    for member in members:
        # Generate 1-3 research reports per member
        num_reports = random.randint(1, 3)
        
        for i in range(num_reports):
            research_id = str(uuid.uuid4())
            reference_id = str(random.randint(600000, 699999))
            
            # Generate research date (within last 6 months)
            research_date = (datetime.now() - timedelta(days=random.randint(0, 180)))
            research_date_str = research_date.strftime("%-m/%-d/%Y")
            
            medication = random.choice(medications)
            diagnosis = random.choice(diagnosis_codes)
            denial_reason = random.choice(denial_reasons)
            researcher = random.choice(researchers)
            
            # Generate research notes based on template
            research_notes_parts = []
            
            # Part 1: Fiduciary responsibility (sometimes)
            if random.random() < 0.3:
                research_notes_parts.append(
                    "CLAIM FIDUCIARY RESPONSIBILITY HEALWELL PERFORMS CLAIM FIDUCIARY-NON-ERIS-FOR LEVEL 1 AND 2 APPEALS. "
                    "PLAN SPONSOR PERFORMS CLAIM FIDUCIARY FOR VOLUNTARY APPEALS TO PLAN SPONSER AFTER LEVEL 1 AND 2 EXHAUSTED- "
                    "INCLUDES FEDERAL EXTERNAL REVIEW PROGRAM - PROCESS 4.\n\n"
                    "HEALTH CARE REFORM PLAN STATUS FULLY COMPLIANT\n"
                    "Grandfathering - NON-GRANDFATHERED"
                )
            
            # Part 2: UM PREP section
            research_notes_parts.append(
                f"UM PREP\n"
                f"Reference No: {reference_id}\n"
                f"Benefit Exclusion: {'Yes' if random.random() < 0.2 else 'No'}\n"
                f"Initial Denial Reason: {denial_reason}\n"
                f"Medication Name: {medication}\n"
                f"DX: {diagnosis}\n"
                f"Claim Subject to High Dollar Claim Policy: {'Yes' if random.random() < 0.3 else 'NA'}\n"
                f"Previous Decision Maker: {researcher}\n"
                f"Additional Comments: Current plan approved criteria does not allow coverage of the requested drug unless "
                f"the patient's tuberculosis (TB) results are known. Additional coverage criteria may apply, please review "
                f"policy or plan documents for full requirements.\n"
                f"Non-Participating Provider: {'True' if random.random() < 0.1 else 'False'}"
            )
            
            # Part 3: Decision summary (sometimes)
            if random.random() < 0.5:
                decision = random.choice(["Approval", "Denial"])
                research_notes_parts.append(
                    f"\n\nNCAU Letter Language for CRT – {decision} - "
                    f"{'All services now allowed' if decision == 'Approval' else 'Services remain denied'}\n\n"
                    f"Information Reviewed: appeal request, authorization on file\n\n"
                    f"Description of approved service(s): The basis for this determination is a review of the available information. "
                    f"{'The requested service has been authorized on a prior review.' if decision == 'Approval' else 'The requested service does not meet medical necessity criteria.'}\n\n"
                    f"Our Decision\n"
                    f"Pharmacy files\n\n"
                    f"NOTE TO CRT: Choose: Pharmacy"
                )
            
            research_notes = "\n".join(research_notes_parts)
            
            decision_summary = random.choice([
                "Appeal approved based on comprehensive review",
                "Appeal denied due to lack of medical necessity",
                "Additional documentation required",
                "Appeal approved with conditions"
            ])
            
            cursor.execute("""
                INSERT OR REPLACE INTO research_reports
                (research_id, reference_id, member_id, research_date, researcher_name,
                 medication_name, diagnosis_code, initial_denial_reason, benefit_exclusion,
                 previous_decision_maker, research_notes, decision_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                research_id,
                reference_id,
                member["member_id"],
                research_date_str,
                researcher,
                medication,
                diagnosis,
                denial_reason,
                "No" if random.random() < 0.8 else "Yes",
                researcher,
                research_notes,
                decision_summary
            ))
    
    print(f"✓ Generated research reports for {len(members)} members")


def generate_appeal_grievance_letter(member: Dict[str, Any], provider: Dict[str, Any], reference_id: str, is_appeal: bool = True) -> str:
    """Generate a mock appeal or grievance letter with varied openings."""
    letter_type = "Appeal" if is_appeal else "Grievance"
    category = random.choice([
        "Medication Denial",
        "Service Denial", 
        "Billing Error",
        "Poor Customer Service",
        "Coverage Dispute"
    ]) if is_appeal else random.choice([
        "Poor Customer Service",
        "Billing Error",
        "Provider Network Issue",
        "Claims Processing Delay"
    ])
    
    medications = ["Kineret", "Humira", "Enbrel", "Remicade"]
    medication = random.choice(medications)
    
    # Varied opening phrases
    opening_phrases = [
        f"I am writing on behalf of my patient, {member['member_name']}, to formally {letter_type.lower()}",
        f"My patient, {member['member_name']}, has asked me to write this {letter_type.lower()} on their behalf",
        f"It has come to my attention that coverage for {medication} has been denied for my patient, {member['member_name']}. I am writing to formally {letter_type.lower()} this decision",
        f"I am writing to {letter_type.lower()} the denial of coverage for {medication} for my patient, {member['member_name']}",
        f"On behalf of my patient {member['member_name']}, I am submitting this {letter_type.lower()} regarding the denial of coverage for {medication}",
        f"My patient {member['member_name']} has requested that I submit this {letter_type.lower()} for the denial of {medication}",
        f"I am writing to formally {letter_type.lower()} the coverage denial for {medication} affecting my patient, {member['member_name']}"
    ]
    opening = random.choice(opening_phrases)
    
    # Different letter format variations
    letter_format = random.choice(['detailed', 'concise', 'formal', 'clinical', 'narrative'])
    
    if is_appeal:
        if letter_format == 'detailed':
            letter = f"""Dear Insurance Appeals Department,

{opening} the denial of coverage for {medication}.

Patient Information:
Patient Name: {member['member_name']}
Patient ID #: {member['member_id']}
PA #: {reference_id}
Date of Birth: {member['dob']}
Patient Address: {random.choice(['123 Main St, New York, NY 10011', '456 Oak Ave, Los Angeles, CA 90001', '789 Pine Rd, Chicago, IL 60601'])}
Medication Requested: {medication}

Clinical Summary:
{member['member_name']} has a history of {random.choice(['autoimmune condition', 'chronic inflammatory disease', 'rheumatoid arthritis'])} requiring ongoing treatment. 
The requested medication {medication} is medically necessary for managing this condition and has been recommended as part of the patient's treatment plan.

Previous attempts to obtain coverage for this medication have been denied, but we believe this decision was made in error. The medication is FDA-approved for this condition and is included in the plan's formulary. The patient has tried alternative treatments without adequate response, making {medication} the most appropriate therapeutic option.

We have attached all relevant medical records, physician notes, laboratory results, and supporting documentation. We request that you review this case and approve coverage for the requested medication.

Thank you for your time and consideration.

Sincerely,
{provider['provider_name']}
{provider['specialty']}
{provider['clinic_name']}
Phone: {random.choice(['(555) 123-4567', '(555) 234-5678', '(555) 345-6789'])}
Email: {provider['email']}
NPI: {random.randint(1000000000, 9999999999)}"""
        
        elif letter_format == 'concise':
            letter = f"""Dear Appeals Department,

{opening} the denial of {medication} for {member['member_name']} (ID: {member['member_id']}, PA: {reference_id}).

{member['member_name']} requires {medication} for {random.choice(['autoimmune condition', 'chronic inflammatory disease', 'rheumatoid arthritis'])}. 
This medication is FDA-approved and medically necessary. Previous denials were in error.

Please approve coverage. Medical records attached.

Best regards,
{provider['provider_name']}, {provider['specialty']}
{provider['clinic_name']}
{provider['email']}"""
        
        elif letter_format == 'formal':
            letter = f"""To Whom It May Concern:

RE: Appeal of Coverage Denial - {member['member_name']} (Member ID: {member['member_id']}, PA #: {reference_id})

I am writing to formally {letter_type.lower()} the denial of coverage for {medication} prescribed to my patient, {member['member_name']}, date of birth {member['dob']}.

CLINICAL JUSTIFICATION:
The patient has been diagnosed with {random.choice(['autoimmune condition', 'chronic inflammatory disease', 'rheumatoid arthritis'])} and requires {medication} as part of their ongoing treatment regimen. This medication has been determined to be medically necessary based on the patient's clinical presentation and failure to respond adequately to alternative therapies.

The medication {medication} is FDA-approved for this indication and is included in the plan's formulary. Denial of coverage is not medically appropriate given the patient's condition and treatment history.

REQUESTED ACTION:
I respectfully request that this denial be overturned and coverage for {medication} be approved for {member['member_name']}.

All supporting documentation, including medical records, laboratory results, and prior authorization requests, are attached for your review.

Respectfully submitted,
{provider['provider_name']}, {provider['specialty']}
{provider['clinic_name']}
Phone: {random.choice(['(555) 123-4567', '(555) 234-5678', '(555) 345-6789'])}
Email: {provider['email']}
NPI: {random.randint(1000000000, 9999999999)}"""
        
        elif letter_format == 'clinical':
            letter = f"""Appeal Request - {medication} Coverage Denial

Patient: {member['member_name']}
DOB: {member['dob']}
Member ID: {member['member_id']}
PA #: {reference_id}

DIAGNOSIS: {random.choice(['Autoimmune condition', 'Chronic inflammatory disease', 'Rheumatoid arthritis'])}
PRESCRIBED MEDICATION: {medication}
DENIAL REASON: {random.choice(['Medical necessity', 'Prior authorization required', 'Not a covered benefit'])}
APPEAL BASIS: Medical necessity and FDA approval

CLINICAL RATIONALE:
Patient has failed alternative treatments including {random.choice(['methotrexate', 'sulfasalazine', 'hydroxychloroquine', 'prednisone'])}. 
{medication} is indicated for this condition per FDA labeling and plan formulary. Continued denial places patient at risk for disease progression.

RECOMMENDATION: Approve coverage for {medication}

Attached: Medical records, lab results, treatment history

{provider['provider_name']}, {provider['specialty']}
{provider['clinic_name']}
{provider['email']} | NPI: {random.randint(1000000000, 9999999999)}"""
        
        else:  # narrative
            letter = f"""Dear Insurance Appeals Department,

{opening} the denial of coverage for {medication}.

I have been treating {member['member_name']} (Member ID: {member['member_id']}, PA #: {reference_id}) for {random.choice(['an autoimmune condition', 'a chronic inflammatory disease', 'rheumatoid arthritis'])}. 
Over the past {random.choice(['6 months', 'year', '18 months'])}, we have tried several treatment approaches, including {random.choice(['methotrexate', 'sulfasalazine', 'hydroxychloroquine'])} and {random.choice(['prednisone', 'NSAIDs', 'physical therapy'])}, 
but the patient has not achieved adequate symptom control or disease management.

{medication} represents the next appropriate step in {member['member_name']}'s treatment plan. This medication is not only FDA-approved for this condition, 
but has shown significant efficacy in patients with similar presentations. The patient's quality of life has been significantly impacted, and we believe 
{medication} will provide the therapeutic benefit needed.

I understand that cost considerations are important, but in this case, the medical necessity is clear. The patient has exhausted reasonable alternatives, 
and {medication} is the most appropriate option available. I have included comprehensive medical records, laboratory findings, and treatment history 
to support this appeal.

I hope you will reconsider this decision and approve coverage for {medication}. Please feel free to contact me if you need any additional information.

Sincerely,
{provider['provider_name']}
{provider['specialty']}
{provider['clinic_name']}
{random.choice(['(555) 123-4567', '(555) 234-5678', '(555) 345-6789'])} | {provider['email']}"""
    else:
        # Varied opening phrases for grievances
        grievance_openings = [
            f"I am writing on behalf of my patient, {member['member_name']}, to formally file a grievance regarding ongoing billing errors and poor customer service",
            f"My patient, {member['member_name']}, has asked me to file this grievance on their behalf regarding billing issues they have experienced",
            f"It has come to my attention that my patient, {member['member_name']}, has been experiencing ongoing billing errors and poor customer service. I am writing to file a formal grievance",
            f"On behalf of my patient {member['member_name']}, I am filing this grievance regarding billing errors and customer service issues",
            f"My patient {member['member_name']} has requested that I file this grievance regarding ongoing billing problems with your company"
        ]
        grievance_opening = random.choice(grievance_openings)
        
        # Different grievance letter formats
        grievance_format = random.choice(['detailed', 'concise', 'formal'])
        
        if grievance_format == 'detailed':
            letter = f"""Dear Customer Service Manager,

{grievance_opening} that my patient has experienced with your company.

Patient Information:
Patient Name: {member['member_name']}
Patient ID #: {member['member_id']}
Reference ID: {reference_id}
Date of Birth: {member['dob']}

Issue Summary:
Since {random.choice(['January', 'February', 'March'])} 2024, my patient has been incorrectly charged ${random.randint(200, 500)}.00 per month for services that should be fully covered under their plan. Despite multiple attempts by the patient to resolve this issue, the billing errors continue to occur.

The patient has made {random.randint(3, 7)} separate calls to your customer service department, and each time they receive different explanations about why these charges are appearing on their account. Representatives have told them to call back later, that the issue is being escalated, or that they need to speak with a different department. However, none of these calls have resulted in a resolution.

The patient has provided policy documents, payment history, and account statements multiple times to demonstrate that these services should be covered under their plan. Despite this documentation, the billing department continues to process incorrect charges.

This situation has caused significant financial hardship and frustration for my patient. As their healthcare provider, I am requesting immediate resolution of these billing errors, reimbursement for the incorrect charges, and assurance that future billing will be accurate.

I expect a response within 10 business days outlining the steps being taken to resolve this matter.

Sincerely,
{provider['provider_name']}
{provider['specialty']}
{provider['clinic_name']}
Phone: {random.choice(['(555) 123-4567', '(555) 234-5678', '(555) 345-6789'])}
Email: {provider['email']}"""
        
        elif grievance_format == 'concise':
            letter = f"""Dear Customer Service,

{grievance_opening} regarding billing errors affecting {member['member_name']} (ID: {member['member_id']}, Ref: {reference_id}).

Patient has been incorrectly charged ${random.randint(200, 500)}/month since {random.choice(['January', 'February', 'March'])} 2024. 
Multiple calls ({random.randint(3, 7)} attempts) have not resolved the issue. Services should be covered under plan.

Request immediate resolution, reimbursement, and corrected billing going forward.

Response requested within 10 business days.

{provider['provider_name']}, {provider['specialty']}
{provider['clinic_name']}
{provider['email']}"""
        
        else:  # formal
            letter = f"""GRIEVANCE FILING - Billing Errors

Patient: {member['member_name']}
Member ID: {member['member_id']}
Reference ID: {reference_id}
DOB: {member['dob']}

ISSUE: Ongoing billing errors and poor customer service

DETAILS:
- Incorrect charges: ${random.randint(200, 500)}.00/month since {random.choice(['January', 'February', 'March'])} 2024
- Services should be covered under plan
- {random.randint(3, 7)} customer service calls made without resolution
- Documentation provided multiple times

REQUESTED RESOLUTION:
1. Immediate correction of billing errors
2. Reimbursement for incorrect charges
3. Assurance of accurate future billing

Response required within 10 business days per plan policy.

{provider['provider_name']}, {provider['specialty']}
{provider['clinic_name']}
{provider['email']} | {random.choice(['(555) 123-4567', '(555) 234-5678', '(555) 345-6789'])}"""
    
    return letter


def _configure_ssl_for_gmail():
    """Configure SSL certificates for Gmail API (handles corporate proxies like Zscaler)."""
    import ssl
    
    # Priority: 1. Corporate certs (Zscaler), 2. certifi, 3. System defaults
    ssl_cert_path = None
    
    # Check for corporate certificate bundles (common locations)
    corporate_cert_paths = [
        os.path.expanduser("~/.certs/cacert-with-zscaler.pem"),
        os.path.expanduser("~/.certs/cacert.pem"),
        "/etc/ssl/certs/ca-certificates.crt",
    ]
    
    for cert_path in corporate_cert_paths:
        if os.path.exists(cert_path):
            ssl_cert_path = cert_path
            print(f"   Found corporate SSL certificate: {cert_path}")
            break
    
    # Fallback to certifi if no corporate certs found
    if not ssl_cert_path:
        try:
            import certifi
            ssl_cert_path = certifi.where()
        except ImportError:
            pass  # certifi not available, will rely on system certificates
    
    # Set environment variables for libraries that respect them
    if ssl_cert_path:
        os.environ['SSL_CERT_FILE'] = ssl_cert_path
        os.environ['REQUESTS_CA_BUNDLE'] = ssl_cert_path
        os.environ['CURL_CA_BUNDLE'] = ssl_cert_path
    
    # Configure Python's default SSL context
    if ssl_cert_path:
        try:
            context = ssl.create_default_context(cafile=ssl_cert_path)
            ssl._create_default_https_context = lambda: context
        except Exception:
            pass  # If context creation fails, continue anyway
    
    # Patch httplib2 (used by oauth2client) to use our certificate
    if ssl_cert_path:
        try:
            import httplib2
            
            # httplib2 uses ca_certs parameter instead of context
            # Patch the Http class to use our certificate file
            original_http_init = httplib2.Http.__init__
            
            def patched_http_init(self, *args, **kwargs):
                # Set ca_certs to our certificate file if not already set
                if 'ca_certs' not in kwargs:
                    kwargs['ca_certs'] = ssl_cert_path
                return original_http_init(self, *args, **kwargs)
            
            httplib2.Http.__init__ = patched_http_init
        except (ImportError, Exception):
            pass  # httplib2 might not be available or patching might fail


def create_mock_emails(members: List[Dict[str, Any]], email_count: int = 5, skip_emails: bool = False, recipient_email: str = "topazagentkit@gmail.com", db_path: str = None) -> List[Dict[str, Any]]:
    """Create mock emails in AG/Pending folder.
    
    Sends emails from different customer email addresses (based on member names) to the recipient.
    Since Gmail API requires sending from authenticated account, we format emails to indicate
    the original sender in the email body.
    """
    if skip_emails or not SIMPLEGMAIL_AVAILABLE:
        print("⚠ Skipping email creation (simplegmail not available or --skip-emails flag set)")
        return []
    
    try:
        # Configure SSL certificates BEFORE initializing Gmail
        _configure_ssl_for_gmail()
        
        # Check for invalid token file and provide helpful error message
        token_file = Path("gmail_token.json")
        if token_file.exists():
            try:
                import json
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                    if token_data.get("invalid", False):
                        print("⚠ Gmail token file is marked as invalid.")
                        print("   The token has been expired or revoked.")
                        print(f"   To fix: Delete {token_file.absolute()} and re-run this script.")
                        print("   The OAuth flow will trigger automatically on next run.")
                        return []
            except Exception:
                pass  # If we can't read the token file, let Gmail() handle it
        
        gmail = Gmail()
        
        # Check if AG/Pending label exists, create if not
        labels = gmail.list_labels()
        pending_label = None
        for label in labels:
            if label.name == "AG/Pending":
                pending_label = label
                break
        
        if not pending_label:
            print("⚠ AG/Pending label not found. Please create it manually in Gmail.")
            print("   You can create it by going to Gmail Settings > Labels > Create new label")
            return []
        
        # Get authenticated user's email (for sender parameter - required by Gmail API)
        try:
            profile = gmail.service.users().getProfile(userId='me').execute()
            authenticated_sender = profile.get('emailAddress')
        except Exception:
            print("⚠ Could not get authenticated user email. Skipping email creation.")
            return []
        
        emails_created = []
        base_date = datetime.now() - timedelta(days=random.randint(1, 7))
        
        # Use unique members for each email (with replacement if email_count > member_count)
        if email_count <= len(members):
            # Use each member once, then shuffle
            selected_members = random.sample(members, email_count)
        else:
            # If we need more emails than members, use all members and then randomly select more
            selected_members = list(members) + random.choices(members, k=email_count - len(members))
            random.shuffle(selected_members)
        
        # Generate providers for email sending
        # Generate enough providers for all emails (with some extra for variety)
        providers = generate_mock_providers(max(email_count, 10))
        
        # Create a mapping of members to providers (some members may share providers)
        # This ensures consistency if same patient has multiple emails
        member_provider_map = {}
        for member in selected_members:
            if member["member_id"] not in member_provider_map:
                # Assign a random provider to this member (can be reused for multiple emails about same patient)
                member_provider_map[member["member_id"]] = random.choice(providers)
        
        # Query existing research reports to get reference_ids per member
        research_reference_map = {}  # member_id -> list of reference_ids
        if db_path:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT member_id, reference_id FROM research_reports")
                for row in cursor.fetchall():
                    member_id, ref_id = row
                    if member_id not in research_reference_map:
                        research_reference_map[member_id] = []
                    research_reference_map[member_id].append(ref_id)
                conn.close()
            except Exception as e:
                print(f"⚠ Warning: Could not query research reports for reference_ids: {e}")
                print("   Emails will use randomly generated reference_ids")
        
        for i in range(email_count):
            member = selected_members[i]
            # Use the same provider for all emails about the same patient
            provider = member_provider_map[member["member_id"]]
            is_appeal = random.random() < 0.7  # 70% appeals, 30% grievances
            
            # Use existing reference_id from research reports if available, otherwise generate new one
            if member["member_id"] in research_reference_map and research_reference_map[member["member_id"]]:
                reference_id = random.choice(research_reference_map[member["member_id"]])
            else:
                reference_id = str(random.randint(600000, 699999))
            
            letter = generate_appeal_grievance_letter(member, provider, reference_id, is_appeal)
            
            # Use provider email as sender (since providers send emails about patients)
            provider_email = provider['email']
            
            # Email body is just the letter
            # The From/Reply-To headers are set in the email headers (see below)
            formatted_body = letter
            
            subject = f"{'Appeal' if is_appeal else 'Grievance'} Request - Patient: {member['member_name']} - Ref: {reference_id}"
            
            try:
                # Send email TO recipient_email using provider email as reply-to
                # Note: Gmail API requires sender to be authenticated account, but we set reply-to
                # to provider email and format email to show provider as sender
                try:
                    from email.mime.text import MIMEText
                    import base64
                    
                    # Check if provider email is set up as a "Send As" alias
                    # Gmail API allows sending from verified aliases
                    send_as_addresses = gmail.service.users().settings().sendAs().list(userId='me').execute()
                    send_as_list = send_as_addresses.get('sendAs', [])
                    
                    # Find if provider email is in the send-as list
                    provider_send_as = None
                    for send_as in send_as_list:
                        if send_as.get('sendAsEmail') == provider_email:
                            provider_send_as = send_as
                            break
                    
                    # Create message
                    msg = MIMEText(formatted_body)
                    msg['To'] = recipient_email
                    msg['Subject'] = subject
                    msg['Reply-To'] = provider_email
                    
                    # If provider email is set up as send-as alias, use the alias's display name
                    # Otherwise, set From header manually (Gmail may override it)
                    if provider_send_as:
                        # Use the alias's configured display name, or fallback to provider name
                        alias_display_name = provider_send_as.get('displayName') or provider['provider_name']
                        msg['From'] = f"{alias_display_name} <{provider_email}>"
                        print(f"    ✓ Using verified alias: {provider_email} (display name: {alias_display_name})")
                    else:
                        # Set From header manually (Gmail will likely override to show authenticated sender)
                        msg['From'] = f"{provider['provider_name']} <{provider_email}>"
                        print(f"    ⚠ Alias {provider_email} not verified - will show as authenticated sender")
                    
                    # Encode message
                    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
                    
                    # Send using Gmail API
                    # If alias is verified, Gmail will use it; otherwise it will use authenticated account
                    message_response = gmail.service.users().messages().send(
                        userId='me',
                        body={'raw': raw_message}
                    ).execute()
                    
                    if provider_send_as:
                        print(f"    ✓ Sent from verified alias: {provider_email}")
                    else:
                        print(f"    ⚠ Sent from authenticated account (alias {provider_email} not verified)")
                    
                    message_id = message_response.get('id')
                    thread_id = message_response.get('threadId')
                    
                except Exception as api_error:
                    # Fallback to SimpleGmail if direct API fails
                    # Format email body to include provider info at top
                    email_with_header = f"""From: {provider['provider_name']} <{provider_email}>
Reply-To: {provider_email}
To: {recipient_email}
Subject: {subject}
Date: {base_date.strftime('%a, %d %b %Y %H:%M:%S %z')}

{formatted_body}"""
                    
                    message = gmail.send_message(
                        sender=authenticated_sender,
                        to=recipient_email,
                        subject=subject,
                        msg_plain=email_with_header
                    )
                    message_id = message.id
                    thread_id = message.thread_id
                
                # Try to add AG/Pending label to the sent message
                try:
                    # Get the message we just sent and add label
                    gmail.service.users().messages().modify(
                        userId='me',
                        id=message_id,
                        body={'addLabelIds': [pending_label.id]}
                    ).execute()
                except Exception as label_error:
                    # If label addition fails, that's okay - user can move manually
                    print(f"    ⚠ Could not auto-add AG/Pending label: {label_error}")
                    print(f"    💡 Please manually move this email to 'AG/Pending' label")
                
                emails_created.append({
                    "message_id": message_id,
                    "thread_id": thread_id,
                    "member_id": member["member_id"],
                    "member_name": member["member_name"],
                    "provider_email": provider_email,
                    "provider_name": provider["provider_name"],
                    "reference_id": reference_id,
                    "is_appeal": is_appeal
                })
                
                print(f"  ✓ Created email {i+1}/{email_count}: From {provider['provider_name']} ({provider_email}) about patient {member['member_name']}")
                
            except Exception as e:
                print(f"  ⚠ Failed to create email {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n✓ Created {len(emails_created)} mock emails")
        print(f"  All emails sent to: {recipient_email}")
        if pending_label:
            print(f"  Emails should be in 'AG/Pending' label (if auto-labeling worked)")
        else:
            print("  ⚠ Please manually move emails to 'AG/Pending' label")
        
        return emails_created
        
    except Exception as e:
        error_msg = str(e)
        print(f"⚠ Failed to create emails: {error_msg}")
        
        # Check if this is a token expiration/revocation error
        if "invalid_grant" in error_msg.lower() or "token has been expired or revoked" in error_msg.lower():
            token_file = Path("gmail_token.json")
            print("\n🔑 Gmail Token Issue Detected:")
            print("   The OAuth2 token has expired or been revoked.")
            print(f"   Solution: Delete the token file and re-authenticate:")
            print(f"   1. Delete: {token_file.absolute()}")
            print(f"   2. Re-run this script - it will trigger OAuth flow automatically")
            print(f"   3. Or run with --skip-emails to skip email creation")
        else:
            import traceback
            traceback.print_exc()
            print("  You can manually create emails in the AG/Pending folder or run this script with --skip-emails")
        
        return []


def main():
    parser = argparse.ArgumentParser(description="Setup Appeal Grievance database and mock data")
    parser.add_argument(
        "--db-path",
        type=str,
        default="projects/ensemble/data/ag/ag_database.db",
        help="Path to SQLite database file (default: projects/ensemble/data/ag/ag_database.db)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing tables and recreate (WARNING: deletes all data)"
    )
    parser.add_argument(
        "--email-count",
        type=int,
        default=5,
        help="Number of mock emails to create (default: 5)"
    )
    parser.add_argument(
        "--skip-emails",
        action="store_true",
        help="Skip email creation (useful if Gmail is not configured)"
    )
    parser.add_argument(
        "--recipient-email",
        type=str,
        default="topazagentkit@gmail.com",
        help="Recipient email address for mock emails (default: topazagentkit@gmail.com)"
    )
    parser.add_argument(
        "--response-recipient-email",
        type=str,
        default="topazagentkit@gmail.com",
        help="Recipient email address for decision letter responses (default: topazagentkit@gmail.com)"
    )
    parser.add_argument(
        "--skip-response-emails",
        action="store_true",
        help="Skip sending response emails (store in database only, useful for testing)"
    )
    parser.add_argument(
        "--member-count",
        type=int,
        default=5,
        help="Number of mock members to generate (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Detect project name for path resolution
    project_name = detect_project_name(Path.cwd())
    
    # Resolve paths intelligently (works from repo root or project_dir)
    db_path = resolve_script_path(args.db_path, project_name=project_name)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("Appeal Grievance Database Setup")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print(f"Reset mode: {args.reset}")
    print(f"Members to generate: {args.member_count}")
    print(f"Emails to create: {args.email_count}")
    print(f"Response recipient: {args.response_recipient_email}")
    print(f"Skip response emails: {args.skip_response_emails}")
    print()
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Reset if requested
    if args.reset:
        print("⚠ Resetting database (dropping all tables)...")
        cursor.execute("DROP TABLE IF EXISTS ag_requests")
        cursor.execute("DROP TABLE IF EXISTS claim_history")
        cursor.execute("DROP TABLE IF EXISTS research_reports")
        conn.commit()
        print("✓ Tables dropped")
    
    # Create schema
    print("\n1. Creating database schema...")
    create_database_schema(str(db_path))
    
    # Generate mock data
    print("\n2. Generating mock members...")
    members = generate_mock_members(args.member_count)
    print(f"✓ Generated {len(members)} mock members")
    
    print("\n3. Generating providers...")
    providers = generate_mock_providers(max(args.member_count * 2, 10))
    print(f"✓ Generated {len(providers)} mock providers")
    
    print("\n4. Generating claim history...")
    generate_mock_claim_history(cursor, members, provider_list=providers)
    
    print("\n5. Generating research reports...")
    generate_mock_research_reports(cursor, members)
    
    conn.commit()
    conn.close()
    
    # Create mock emails
    if not args.skip_emails:
        print("\n6. Creating mock emails in AG/Pending folder...")
        print(f"   Sending to: {args.recipient_email}")
        emails = create_mock_emails(members, args.email_count, args.skip_emails, args.recipient_email, str(db_path))
    else:
        print("\n5. Skipping email creation (--skip-emails flag set)")
        emails = []
    
    # Summary
    print("\n" + "=" * 70)
    print("Setup Complete!")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print(f"Members: {len(members)}")
    
    # Count records
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM claim_history")
    claim_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM research_reports")
    research_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"Claim History Records: {claim_count}")
    print(f"Research Reports: {research_count}")
    print(f"Mock Emails Created: {len(emails)}")
    
    if emails:
        print("\n⚠ Important: Please manually move the created emails to 'AG/Pending' label in Gmail,")
        print("   or configure Gmail filters to automatically label them.")
    
    print("\n📧 Response Email Configuration:")
    if args.skip_response_emails:
        print("   ✓ Response emails will be stored in database only (--skip-response-emails)")
    else:
        print(f"   ✓ Response emails will be sent to: {args.response_recipient_email}")
        print("   ⚠ Note: Mock customer emails don't exist, so responses go to test recipient")
    
    print("\n✓ Setup complete! You can now run the Appeal Grievance Processor pipeline.")


if __name__ == "__main__":
    main()

