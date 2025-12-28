#!/usr/bin/env python3
"""Setup script for Supplier RFP Evaluation pipeline.

Creates SQLite database, initializes schema, and generates mock data:
- RFP document (PDF)
- Supplier response documents (PDFs)
- Requirements matrix
- Evaluation criteria and scoring rubric
- Benchmark data
- Compliance reference data
- Supplier profiles

Usage:
    python scripts/generate_rfp_mock_data.py [--db-path <path>] [--output-dir <dir>] [--reset] [--supplier-count <n>]
    uv run -m scripts.generate_rfp_mock_data --db-path projects/ensemble/data/rfp/rfp_database.db --reset
"""

import sqlite3
import os
import sys
import argparse
import random
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from topaz_agent_kit.utils.path_resolver import resolve_script_path, detect_project_name

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not available. PDF generation will be skipped.")
    print("Install with: pip install reportlab")


def get_topic_templates(topic: str) -> Dict[str, Any]:
    """Get topic-specific templates for requirements, criteria, and benchmarks.
    
    Returns a dictionary with topic-specific data templates.
    """
    topic_lower = topic.lower()
    
    # Base templates that can be customized per topic
    base_templates = {
        "cloud infrastructure": {
            "requirements": [
                {"category": "technical", "description": "99.9% uptime SLA", "priority": "mandatory", "weight": 10.0},
                {"category": "technical", "description": "Multi-region deployment capability", "priority": "mandatory", "weight": 10.0},
                {"category": "technical", "description": "Auto-scaling capabilities", "priority": "high", "weight": 8.0},
                {"category": "technical", "description": "Container orchestration support (Kubernetes)", "priority": "high", "weight": 8.0},
                {"category": "technical", "description": "Disaster recovery and backup solutions", "priority": "mandatory", "weight": 10.0},
                {"category": "functional", "description": "24/7 technical support", "priority": "mandatory", "weight": 9.0},
                {"category": "functional", "description": "API access and integration capabilities", "priority": "high", "weight": 7.0},
                {"category": "functional", "description": "Monitoring and alerting tools", "priority": "high", "weight": 7.0},
                {"category": "compliance", "description": "SOC 2 Type II certification", "priority": "mandatory", "weight": 10.0},
                {"category": "compliance", "description": "ISO 27001 certification", "priority": "high", "weight": 8.0},
                {"category": "compliance", "description": "GDPR compliance", "priority": "mandatory", "weight": 10.0},
                {"category": "delivery", "description": "Implementation within 90 days", "priority": "high", "weight": 8.0},
                {"category": "delivery", "description": "Migration support and planning", "priority": "high", "weight": 7.0},
            ],
            "pricing_range": {"min": 50000, "max": 500000, "average": 200000},
            "delivery_timeline": {"min_days": 60, "max_days": 180, "average_days": 120},
            "certifications": ["SOC 2 Type II", "ISO 27001", "GDPR", "HIPAA"],
        },
        "erp system": {
            "requirements": [
                {"category": "technical", "description": "Cloud-based SaaS deployment", "priority": "mandatory", "weight": 10.0},
                {"category": "technical", "description": "Integration with existing accounting systems", "priority": "mandatory", "weight": 10.0},
                {"category": "technical", "description": "Mobile app access", "priority": "high", "weight": 7.0},
                {"category": "functional", "description": "Financial management modules", "priority": "mandatory", "weight": 10.0},
                {"category": "functional", "description": "Inventory management", "priority": "mandatory", "weight": 9.0},
                {"category": "functional", "description": "Human resources management", "priority": "high", "weight": 8.0},
                {"category": "functional", "description": "Reporting and analytics dashboard", "priority": "high", "weight": 8.0},
                {"category": "compliance", "description": "SOX compliance", "priority": "mandatory", "weight": 10.0},
                {"category": "compliance", "description": "Data encryption at rest and in transit", "priority": "mandatory", "weight": 9.0},
                {"category": "delivery", "description": "Implementation within 120 days", "priority": "high", "weight": 8.0},
                {"category": "delivery", "description": "User training and documentation", "priority": "high", "weight": 7.0},
            ],
            "pricing_range": {"min": 100000, "max": 1000000, "average": 400000},
            "delivery_timeline": {"min_days": 90, "max_days": 240, "average_days": 150},
            "certifications": ["SOX", "SOC 2", "ISO 27001"],
        },
        "network equipment": {
            "requirements": [
                {"category": "technical", "description": "Gigabit Ethernet support", "priority": "mandatory", "weight": 10.0},
                {"category": "technical", "description": "PoE (Power over Ethernet) capability", "priority": "high", "weight": 8.0},
                {"category": "technical", "description": "VLAN support and management", "priority": "mandatory", "weight": 9.0},
                {"category": "technical", "description": "Wireless access point integration", "priority": "high", "weight": 7.0},
                {"category": "functional", "description": "Centralized management interface", "priority": "mandatory", "weight": 9.0},
                {"category": "functional", "description": "Remote monitoring capabilities", "priority": "high", "weight": 7.0},
                {"category": "compliance", "description": "FCC certification", "priority": "mandatory", "weight": 10.0},
                {"category": "compliance", "description": "CE marking for European markets", "priority": "medium", "weight": 6.0},
                {"category": "delivery", "description": "Delivery within 30 days", "priority": "high", "weight": 8.0},
                {"category": "delivery", "description": "Installation and configuration support", "priority": "high", "weight": 7.0},
            ],
            "pricing_range": {"min": 20000, "max": 200000, "average": 80000},
            "delivery_timeline": {"min_days": 14, "max_days": 60, "average_days": 30},
            "certifications": ["FCC", "CE", "UL"],
        },
    }
    
    # Try to match topic, default to cloud infrastructure if not found
    for key, template in base_templates.items():
        if key in topic_lower:
            return template
    
    # Default template (cloud infrastructure)
    return base_templates["cloud infrastructure"]


def populate_requirements(cursor, topic: str) -> None:
    """Populate requirements table based on topic."""
    template = get_topic_templates(topic)
    requirements = template["requirements"]
    
    for i, req in enumerate(requirements, 1):
        requirement_id = f"REQ-{i:03d}"
        cursor.execute("""
            INSERT OR REPLACE INTO requirements (requirement_id, category, description, priority, weight)
            VALUES (?, ?, ?, ?, ?)
        """, (requirement_id, req["category"], req["description"], req["priority"], req["weight"]))
    
    print(f"✓ Populated {len(requirements)} requirements")


def populate_evaluation_criteria(cursor) -> None:
    """Populate evaluation criteria table."""
    criteria = [
        {"criteria_id": "CRIT-001", "category": "technical", "weight": 35.0, "description": "Technical capability and solution fit"},
        {"criteria_id": "CRIT-002", "category": "pricing", "weight": 25.0, "description": "Total cost of ownership and pricing competitiveness"},
        {"criteria_id": "CRIT-003", "category": "delivery", "weight": 18.0, "description": "Delivery timeline and implementation approach"},
        {"criteria_id": "CRIT-004", "category": "compliance", "weight": 12.0, "description": "Compliance with regulatory and security requirements"},
        {"criteria_id": "CRIT-005", "category": "case_studies", "weight": 5.0, "description": "Relevance and quality of case studies demonstrating similar project experience"},
        {"criteria_id": "CRIT-006", "category": "references", "weight": 5.0, "description": "Client references and testimonials from similar projects"},
    ]
    
    for crit in criteria:
        cursor.execute("""
            INSERT OR REPLACE INTO evaluation_criteria (criteria_id, category, weight, description)
            VALUES (?, ?, ?, ?)
        """, (crit["criteria_id"], crit["category"], crit["weight"], crit["description"]))
    
    print(f"✓ Populated {len(criteria)} evaluation criteria")


def populate_scoring_rubric(cursor) -> None:
    """Populate scoring rubric table."""
    categories = ["technical", "pricing", "delivery", "compliance", "case_studies", "references"]
    levels = [
        {"score": 5, "label": "Excellent", "desc": "Exceeds all requirements significantly"},
        {"score": 4, "label": "Good", "desc": "Meets all requirements with some enhancements"},
        {"score": 3, "label": "Fair", "desc": "Meets basic requirements adequately"},
        {"score": 2, "label": "Poor", "desc": "Partially meets requirements with gaps"},
        {"score": 1, "label": "Unacceptable", "desc": "Fails to meet critical requirements"},
    ]
    
    rubric_id = 1
    for category in categories:
        for level in levels:
            cursor.execute("""
                INSERT OR REPLACE INTO scoring_rubric (rubric_id, criteria_category, score_level, description, qualitative_label)
                VALUES (?, ?, ?, ?, ?)
            """, (f"RUB-{rubric_id:03d}", category, level["score"], level["desc"], level["label"]))
            rubric_id += 1
    
    print(f"✓ Populated scoring rubric ({len(categories)} categories × {len(levels)} levels)")


def populate_benchmark_data(cursor, topic: str) -> None:
    """Populate benchmark data table based on topic."""
    template = get_topic_templates(topic)
    pricing_range = template["pricing_range"]
    delivery_timeline = template["delivery_timeline"]
    
    benchmarks = [
        {
            "benchmark_id": "BENCH-001",
            "category": "pricing",
            "metric_name": "Total Project Cost",
            "industry_average": pricing_range["average"],
            "best_in_class": pricing_range["min"],
            "acceptable_range": f"${pricing_range['min']:,} - ${pricing_range['max']:,}",
        },
        {
            "benchmark_id": "BENCH-002",
            "category": "delivery",
            "metric_name": "Implementation Timeline",
            "industry_average": delivery_timeline["average_days"],
            "best_in_class": delivery_timeline["min_days"],
            "acceptable_range": f"{delivery_timeline['min_days']} - {delivery_timeline['max_days']} days",
        },
    ]
    
    for bench in benchmarks:
        cursor.execute("""
            INSERT OR REPLACE INTO benchmark_data (benchmark_id, category, metric_name, industry_average, best_in_class, acceptable_range)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (bench["benchmark_id"], bench["category"], bench["metric_name"], 
              bench["industry_average"], bench["best_in_class"], bench["acceptable_range"]))
    
    print(f"✓ Populated {len(benchmarks)} benchmark metrics")


def populate_compliance_reference(cursor, topic: str) -> None:
    """Populate compliance reference table based on topic."""
    template = get_topic_templates(topic)
    certifications = template.get("certifications", [])
    
    compliance_items = []
    
    # Add certifications
    for cert in certifications:
        compliance_items.append({
            "compliance_id": f"COMP-{len(compliance_items) + 1:03d}",
            "requirement_type": "certification",
            "description": f"{cert} certification required",
            "mandatory": 1 if cert in ["SOC 2 Type II", "SOC 2", "FCC", "SOX", "GDPR"] else 0,
        })
    
    # Add common security requirements
    security_reqs = [
        {"desc": "Data encryption at rest", "mandatory": 1},
        {"desc": "Data encryption in transit (TLS 1.3+)", "mandatory": 1},
        {"desc": "Regular security audits", "mandatory": 0},
        {"desc": "Penetration testing", "mandatory": 0},
    ]
    
    for req in security_reqs:
        compliance_items.append({
            "compliance_id": f"COMP-{len(compliance_items) + 1:03d}",
            "requirement_type": "security",
            "description": req["desc"],
            "mandatory": req["mandatory"],
        })
    
    for comp in compliance_items:
        cursor.execute("""
            INSERT OR REPLACE INTO compliance_reference (compliance_id, requirement_type, description, mandatory)
            VALUES (?, ?, ?, ?)
        """, (comp["compliance_id"], comp["requirement_type"], comp["description"], comp["mandatory"]))
    
    print(f"✓ Populated {len(compliance_items)} compliance requirements")


def populate_supplier_profiles(cursor, count: int = 3) -> List[Dict[str, Any]]:
    """Populate supplier profiles table with randomized data."""
    # Expanded pool of supplier names for randomization
    supplier_names_pool = [
        "TechSolutions Pro",
        "Global Systems Inc",
        "Enterprise Partners LLC",
        "Premier Services Group",
        "Advanced Solutions Corp",
        "Innovation Dynamics",
        "Strategic Tech Solutions",
        "Digital Excellence Partners",
        "CloudFirst Technologies",
        "NextGen Enterprise Solutions",
        "Agile Systems Group",
        "Premier IT Services",
        "Transformative Solutions Inc",
        "Enterprise Cloud Services",
        "Advanced Digital Partners",
        "Strategic Business Technologies",
        "Innovation Labs LLC",
        "TechVenture Solutions",
        "Digital Transformation Group",
        "Enterprise Systems Pro",
    ]
    
    # Randomly select supplier names (no duplicates)
    supplier_names = random.sample(supplier_names_pool, min(count, len(supplier_names_pool)))
    
    certifications_pool = [
        "SOC 2 Type II", "ISO 27001", "GDPR", "HIPAA", "SOX", "FCC", "CE", "UL"
    ]
    
    geographic_coverage_options = [
        "North America",
        "Global",
        "North America, Europe",
        "North America, Europe, Asia-Pacific",
    ]
    
    suppliers = []
    for i in range(count):
        supplier_id = f"SUPPLIER-{i+1:03d}"
        supplier_name = supplier_names[i % len(supplier_names)]
        years_in_business = random.randint(5, 25)
        past_performance_score = round(random.uniform(3.0, 5.0), 2)
        
        # Assign certifications based on supplier index (variety)
        num_certs = random.randint(2, 5)
        certifications = random.sample(certifications_pool, min(num_certs, len(certifications_pool)))
        certifications_str = json.dumps(certifications)
        
        geographic_coverage = random.choice(geographic_coverage_options)
        
        cursor.execute("""
            INSERT OR REPLACE INTO supplier_profiles (supplier_id, supplier_name, years_in_business, 
                                         past_performance_score, certifications, geographic_coverage)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (supplier_id, supplier_name, years_in_business, past_performance_score, 
              certifications_str, geographic_coverage))
        
        suppliers.append({
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "years_in_business": years_in_business,
            "past_performance_score": past_performance_score,
            "certifications": certifications,
            "geographic_coverage": geographic_coverage,
        })
    
    print(f"✓ Populated {len(suppliers)} supplier profiles")
    return suppliers


def get_issuing_company_profile() -> Dict[str, Any]:
    """Generate a random issuing company profile."""
    company_names = [
        "Acme Corporation",
        "Global Industries Inc",
        "TechVentures LLC",
        "Enterprise Solutions Group",
        "Innovation Partners",
        "Strategic Business Systems",
        "Premier Technologies Corp",
        "Advanced Solutions Ltd",
        "Digital Transformation Co",
        "NextGen Enterprises",
    ]
    
    industries = [
        "Financial Services",
        "Healthcare",
        "Manufacturing",
        "Technology",
        "Retail",
        "Energy & Utilities",
        "Telecommunications",
        "Government",
        "Education",
        "Transportation & Logistics",
    ]
    
    company_name = random.choice(company_names)
    industry = random.choice(industries)
    employees = random.choice([500, 1000, 2000, 5000, 10000, 25000])
    founded_year = random.randint(1980, 2010)
    headquarters = random.choice([
        "New York, NY", "San Francisco, CA", "Chicago, IL", "Boston, MA",
        "Austin, TX", "Seattle, WA", "Atlanta, GA", "Dallas, TX"
    ])
    
    # Generate detailed company description (1-2 paragraphs)
    company_values = random.sample([
        "innovation", "excellence", "customer-centricity", "sustainability",
        "integrity", "collaboration", "agility", "quality"
    ], 3)
    
    achievements = random.choice([
        f"recognized as a leader in {industry.lower()}",
        f"awarded multiple industry accolades",
        f"serving {random.randint(100, 1000)}+ clients globally",
        f"generating over ${random.randint(100, 500)}M in annual revenue",
        f"expanding operations across {random.randint(5, 20)} countries"
    ])
    
    description_para1 = (
        f"{company_name} is a leading {industry.lower()} company with over {employees:,} employees "
        f"worldwide. Founded in {founded_year}, we have been at the forefront of innovation and "
        f"excellence in our industry for over {2024 - founded_year} years. Our headquarters are "
        f"located in {headquarters}, and we operate across multiple regions, serving clients "
        f"globally. We are committed to {company_values[0]}, {company_values[1]}, and "
        f"{company_values[2]}, which guide all our business decisions and partnerships."
    )
    
    description_para2 = (
        f"Over the years, we have {achievements}. Our organization has built a reputation for "
        f"delivering exceptional value to our stakeholders through strategic initiatives, "
        f"technological advancement, and a strong focus on operational excellence. We invest "
        f"significantly in research and development, employee development, and sustainable "
        f"business practices. As we continue to grow and evolve, we seek partners who share "
        f"our commitment to quality, innovation, and long-term value creation."
    )
    
    return {
        "company_name": company_name,
        "industry": industry,
        "employees": employees,
        "founded_year": founded_year,
        "headquarters": headquarters,
        "description": description_para1 + "\n\n" + description_para2
    }


def get_rfp_timeline() -> Dict[str, Any]:
    """Generate randomized RFP timeline with phases and dates."""
    base_date = datetime.now()
    
    # RFP release date (today or recent past)
    rfp_release_date = base_date - timedelta(days=random.randint(0, 7))
    
    # Question deadline (1-2 weeks after release)
    question_deadline = rfp_release_date + timedelta(days=random.randint(7, 14))
    
    # Proposal submission deadline (4-6 weeks after release)
    submission_deadline = rfp_release_date + timedelta(days=random.randint(28, 42))
    
    # Evaluation period (2-3 weeks)
    evaluation_start = submission_deadline + timedelta(days=1)
    evaluation_end = evaluation_start + timedelta(days=random.randint(14, 21))
    
    # Shortlist announcement (1 week after evaluation)
    shortlist_date = evaluation_end + timedelta(days=random.randint(5, 10))
    
    # Presentations/interviews (1-2 weeks after shortlist)
    presentation_start = shortlist_date + timedelta(days=random.randint(7, 14))
    presentation_end = presentation_start + timedelta(days=random.randint(5, 10))
    
    # Final evaluation (1 week after presentations)
    final_evaluation_end = presentation_end + timedelta(days=random.randint(5, 10))
    
    # Contract award (1-2 weeks after final evaluation)
    contract_award_date = final_evaluation_end + timedelta(days=random.randint(7, 14))
    
    return {
        "rfp_release_date": rfp_release_date,
        "question_deadline": question_deadline,
        "submission_deadline": submission_deadline,
        "evaluation_start": evaluation_start,
        "evaluation_end": evaluation_end,
        "shortlist_date": shortlist_date,
        "presentation_start": presentation_start,
        "presentation_end": presentation_end,
        "final_evaluation_end": final_evaluation_end,
        "contract_award_date": contract_award_date,
    }


def get_rfp_questions(topic: str) -> List[str]:
    """Generate topic-specific questions for RFP respondents with randomization."""
    topic_lower = topic.lower()
    
    # Generic questions that can be adapted to topic
    generic_question_templates = [
        "What is your company's experience with {topic} projects in the past 3 years? Please provide at least 3 relevant case studies.",
        "Describe your project management methodology and how you ensure timely delivery of complex {topic} implementations.",
        "What is your approach to risk management and how do you handle project delays or scope changes in {topic} projects?",
        "What resources (team size, roles, expertise) will you allocate to this {topic} project? Please provide organizational chart.",
        "How do you ensure knowledge transfer and training for our team during and after {topic} implementation?",
        "What is your approach to quality assurance and testing for {topic} solutions? Describe your testing methodologies.",
        "How do you handle data migration and what is your strategy for minimizing downtime during {topic} implementation?",
        "What is your disaster recovery and business continuity plan for {topic} solutions?",
        "Describe your change management process and how you handle scope modifications in {topic} projects.",
        "What ongoing support and maintenance services do you provide post-implementation for {topic} solutions?",
        "How do you ensure security and compliance throughout the {topic} project lifecycle?",
        "What is your approach to integration with existing systems for {topic} solutions? Describe your integration capabilities.",
        "How do you measure project success and what KPIs do you track for {topic} implementations?",
        "What is your escalation process for issues and how quickly do you respond to critical problems in {topic} projects?",
        "Describe your pricing model for {topic} solutions and any potential hidden costs or additional fees.",
        "What is your approach to project governance and stakeholder communication for {topic} implementations?",
        "How do you handle change requests and scope modifications during {topic} implementation?",
        "What is your strategy for ensuring user adoption and change management for {topic} solutions?",
        "Describe your approach to documentation and knowledge management for {topic} projects.",
        "What is your policy on subcontracting and how do you manage vendor relationships for {topic} projects?",
    ]
    
    # Apply topic to generic questions
    question_pool = [q.format(topic=topic.lower()) for q in generic_question_templates]
    
    # Always include case studies and references questions (mandatory)
    mandatory_questions = [
        f"Please provide detailed case studies (minimum 3) of similar {topic.lower()} projects completed in the past 3 years. Each case study should include: project scope, challenges faced, solutions implemented, outcomes achieved, and client information (with permission to contact).",
        f"Please provide at least 3 client references from similar {topic.lower()} projects. Include: client name, contact person, phone number, email, project description, and project completion date. We will contact these references as part of our evaluation process.",
    ]
    
    # Topic-specific question pools (more comprehensive)
    cloud_questions = [
        "What cloud platforms (AWS, Azure, GCP, etc.) do you support and what is your multi-cloud strategy?",
        "How do you ensure high availability and what SLA guarantees do you provide for cloud infrastructure?",
        "What is your approach to cloud security, data protection, and compliance (SOC 2, ISO 27001, etc.)?",
        "How do you handle cloud cost optimization, resource management, and budget control?",
        "What is your approach to cloud migration strategy, including assessment, planning, and execution phases?",
        "How do you ensure cloud scalability and auto-scaling capabilities for varying workloads?",
        "What is your disaster recovery and backup strategy for cloud-based solutions?",
        "How do you handle cloud vendor lock-in and ensure portability across platforms?",
    ]
    
    erp_software_questions = [
        "What is your approach to customization vs. configuration for ERP/software solutions?",
        "How do you handle software updates, version upgrades, and backward compatibility?",
        "What is your strategy for API development and third-party integrations?",
        "How do you ensure software scalability and performance under load?",
        "What is your approach to data migration from legacy systems to new ERP/software?",
        "How do you handle user interface customization and user experience design?",
        "What is your strategy for handling custom workflows and business process automation?",
        "How do you ensure data integrity and consistency across integrated modules?",
    ]
    
    network_equipment_questions = [
        "What network equipment vendors and models do you support (Cisco, Juniper, Aruba, etc.)?",
        "How do you ensure network redundancy and failover capabilities?",
        "What is your approach to network security, including firewall configuration and intrusion detection?",
        "How do you handle network capacity planning and bandwidth management?",
        "What is your strategy for network monitoring, alerting, and performance optimization?",
        "How do you ensure network compliance with industry standards and regulations?",
        "What is your approach to network documentation and change management?",
        "How do you handle network troubleshooting and support for critical issues?",
    ]
    
    ai_platform_questions = [
        "What AI/ML frameworks and platforms do you support (TensorFlow, PyTorch, Azure ML, AWS SageMaker, etc.)?",
        "How do you ensure AI model accuracy, performance, and continuous improvement?",
        "What is your approach to AI ethics, bias mitigation, and responsible AI practices?",
        "How do you handle AI model deployment, versioning, and A/B testing?",
        "What is your strategy for AI data pipeline management and data quality assurance?",
        "How do you ensure AI system explainability and interpretability?",
        "What is your approach to AI security, including model protection and adversarial attack prevention?",
        "How do you handle AI model monitoring, drift detection, and retraining workflows?",
    ]
    
    construction_questions = [
        "What types of construction projects have you completed and what is your experience with projects of similar scale?",
        "How do you ensure construction safety compliance and risk management?",
        "What is your approach to project scheduling, resource allocation, and timeline management?",
        "How do you handle construction material procurement and supply chain management?",
        "What is your strategy for quality control and inspection during construction phases?",
        "How do you ensure compliance with building codes, permits, and regulatory requirements?",
        "What is your approach to construction site management and coordination with subcontractors?",
        "How do you handle change orders and scope modifications during construction?",
    ]
    
    marketing_questions = [
        "What marketing channels and platforms do you specialize in (digital, traditional, social media, etc.)?",
        "How do you measure marketing campaign effectiveness and ROI?",
        "What is your approach to brand strategy and brand positioning?",
        "How do you handle marketing analytics, reporting, and data-driven decision making?",
        "What is your strategy for content creation, content marketing, and SEO?",
        "How do you ensure brand consistency across all marketing channels and touchpoints?",
        "What is your approach to marketing automation and campaign management?",
        "How do you handle crisis communication and reputation management?",
    ]
    
    # Select topic-specific questions
    topic_specific_questions = []
    if "cloud" in topic_lower or "infrastructure" in topic_lower:
        topic_specific_questions = random.sample(cloud_questions, min(4, len(cloud_questions)))
    elif "erp" in topic_lower or "software" in topic_lower or "crm" in topic_lower:
        topic_specific_questions = random.sample(erp_software_questions, min(4, len(erp_software_questions)))
    elif "network" in topic_lower or "equipment" in topic_lower:
        topic_specific_questions = random.sample(network_equipment_questions, min(4, len(network_equipment_questions)))
    elif "ai" in topic_lower or "agentic" in topic_lower or "machine learning" in topic_lower:
        topic_specific_questions = random.sample(ai_platform_questions, min(4, len(ai_platform_questions)))
    elif "construction" in topic_lower:
        topic_specific_questions = random.sample(construction_questions, min(4, len(construction_questions)))
    elif "marketing" in topic_lower:
        topic_specific_questions = random.sample(marketing_questions, min(4, len(marketing_questions)))
    
    # Select base questions (fewer since we have topic-specific ones)
    selected_questions = random.sample(question_pool, min(9, len(question_pool)))
    
    # Add topic-specific questions
    selected_questions.extend(topic_specific_questions)
    
    # Add mandatory case studies and references questions
    selected_questions.extend(mandatory_questions)
    
    # Shuffle but keep case studies and references questions prominent (near the end)
    random.shuffle(selected_questions)
    # Move case studies and references to end for emphasis
    for q in mandatory_questions:
        if q in selected_questions:
            selected_questions.remove(q)
            selected_questions.append(q)
    
    return selected_questions[:15]


def generate_rfp_pdf(topic: str, requirements: List[Dict], criteria: List[Dict], output_path: Path) -> tuple:
    """Generate RFP PDF document."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError(
            "reportlab is required for PDF generation but is not installed. "
            "Install it with: pip install reportlab"
        )
    
    filename = "rfp_document.pdf"
    filepath = output_path / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Table header style with white text
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    # Generate randomized company profile and timeline
    issuing_company = get_issuing_company_profile()
    rfp_timeline = get_rfp_timeline()
    
    # TITLE PAGE
    story.append(Paragraph("Request for Proposal", title_style))
    story.append(Paragraph(topic, title_style))
    story.append(Spacer(1, 0.4 * inch))
    
    # Title page details
    title_details = ParagraphStyle(
        'TitleDetails',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    story.append(Paragraph(f"Issued by: {issuing_company['company_name']}", title_details))
    story.append(Paragraph(f"RFP Release Date: {rfp_timeline['rfp_release_date'].strftime('%B %d, %Y')}", title_details))
    story.append(Paragraph(f"Proposal Submission Deadline: {rfp_timeline['submission_deadline'].strftime('%B %d, %Y')}", title_details))
    story.append(Spacer(1, 0.5 * inch))
    
    # Company info on title page
    story.append(Paragraph(issuing_company['company_name'], ParagraphStyle('TitleCompany', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER)))
    story.append(Paragraph(issuing_company['headquarters'], ParagraphStyle('TitleLocation', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.grey)))
    story.append(Spacer(1, 0.3 * inch))
    
    story.append(PageBreak())
    
    # TABLE OF CONTENTS
    story.append(Paragraph("Table of Contents", heading_style))
    story.append(Spacer(1, 0.2 * inch))
    
    toc_items = [
        ("1.", "About the Issuing Organization"),
        ("2.", "RFP Timeline and Process"),
        ("3.", "Executive Summary"),
        ("4.", "Project Scope"),
        ("5.", "Project Scope & Requirements"),
        ("6.", "Evaluation Criteria"),
        ("7.", "Pricing Structure"),
        ("8.", "Delivery Timeline Requirements"),
        ("9.", "Compliance Requirements"),
        ("10.", "Questions for Respondents"),
        ("11.", "Submission Instructions"),
    ]
    
    toc_data = []
    for num, item in toc_items:
        toc_data.append([
            Paragraph(f"{num} {item}", styles['Normal'])
        ])
    
    toc_table = Table(toc_data, colWidths=[6 * inch])
    toc_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(toc_table)
    story.append(Spacer(1, 0.3 * inch))
    
    story.append(PageBreak())
    
    # Issuing Company Profile
    story.append(Paragraph("About the Issuing Organization", heading_style))
    story.append(Paragraph(issuing_company['description'], styles['Normal']))
    story.append(Spacer(1, 0.1 * inch))
    
    company_details = (
        f"<b>Company:</b> {issuing_company['company_name']}\n"
        f"<b>Industry:</b> {issuing_company['industry']}\n"
        f"<b>Employees:</b> {issuing_company['employees']:,}\n"
        f"<b>Founded:</b> {issuing_company['founded_year']}\n"
        f"<b>Headquarters:</b> {issuing_company['headquarters']}"
    )
    story.append(Paragraph(company_details, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # RFP Timeline and Process
    story.append(Paragraph("RFP Timeline and Process", heading_style))
    
    timeline_phases = [
        {
            "phase": "RFP Release",
            "date": rfp_timeline['rfp_release_date'],
            "description": "RFP published and made available to potential suppliers. All documentation and requirements are provided.",
        },
        {
            "phase": "Question Submission Deadline",
            "date": rfp_timeline['question_deadline'],
            "description": "Last date for suppliers to submit questions or clarifications. All questions and answers will be published as an addendum.",
        },
        {
            "phase": "Proposal Submission Deadline",
            "date": rfp_timeline['submission_deadline'],
            "description": "Final deadline for proposal submission. Late submissions will not be accepted. Proposals must be submitted in PDF format via the specified portal.",
        },
        {
            "phase": "Evaluation Period",
            "date": rfp_timeline['evaluation_start'],
            "end_date": rfp_timeline['evaluation_end'],
            "description": "Our evaluation team will review all proposals against the stated criteria. This includes technical evaluation, pricing analysis, and reference checks.",
        },
        {
            "phase": "Shortlist Announcement",
            "date": rfp_timeline['shortlist_date'],
            "description": "Shortlisted suppliers will be notified. We expect to shortlist 3-5 suppliers for the next phase.",
        },
        {
            "phase": "Presentations & Interviews",
            "date": rfp_timeline['presentation_start'],
            "end_date": rfp_timeline['presentation_end'],
            "description": "Shortlisted suppliers will be invited for presentations and Q&A sessions. This allows us to clarify technical approaches and assess team capabilities.",
        },
        {
            "phase": "Final Evaluation",
            "date": rfp_timeline['presentation_end'] + timedelta(days=1),
            "end_date": rfp_timeline['final_evaluation_end'],
            "description": "Final review of shortlisted proposals, presentation outcomes, and contract negotiations with preferred supplier(s).",
        },
        {
            "phase": "Contract Award",
            "date": rfp_timeline['contract_award_date'],
            "description": "Contract will be awarded to the selected supplier. All participants will be notified of the outcome.",
        },
    ]
    
    # Create timeline table with proper formatting and word wrapping
    timeline_data = []
    for phase in timeline_phases:
        if "end_date" in phase:
            date_str = f"{phase['date'].strftime('%b %d')} - {phase['end_date'].strftime('%b %d, %Y')}"
        else:
            date_str = phase['date'].strftime('%b %d, %Y')
        
        # Use Paragraph for text wrapping in table cells
        phase_para = Paragraph(f"<b>{phase['phase']}</b>", styles['Normal'])
        date_para = Paragraph(date_str, styles['Normal'])
        desc_para = Paragraph(phase['description'], styles['Normal'])
        
        timeline_data.append([phase_para, date_para, desc_para])
    
    # Adjust column widths to fit page (letter size is 8.5 inches, minus margins ~1 inch each side = 6.5 inches usable)
    timeline_table = Table(timeline_data, colWidths=[1.5 * inch, 1.3 * inch, 3.7 * inch])
    timeline_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.lightgrey]),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(timeline_table)
    story.append(Spacer(1, 0.2 * inch))
    
    timeline_note = (
        "<b>Important Notes:</b>\n"
        f"• All dates are subject to change. Any changes will be communicated via addendum.\n"
        f"• Contract award is expected on or before {rfp_timeline['contract_award_date'].strftime('%B %d, %Y')}.\n"
        f"• Project implementation is expected to begin within 30 days of contract award.\n"
        f"• Questions about the timeline should be submitted before {rfp_timeline['question_deadline'].strftime('%B %d, %Y')}."
    )
    story.append(Paragraph(timeline_note, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(
        f"This Request for Proposal (RFP) seeks qualified suppliers to provide {topic.lower()} "
        "solutions. We are looking for partners who can deliver high-quality, compliant, and "
        "cost-effective solutions that meet our organizational needs.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Project Scope (with randomization)
    story.append(Paragraph("Project Scope", heading_style))
    
    scope_objectives = [
        f"We are seeking a comprehensive {topic.lower()} solution that will support our organization's strategic objectives.",
        f"Our goal is to implement a robust {topic.lower()} solution that enhances operational efficiency and drives business value.",
        f"We require an enterprise-grade {topic.lower()} solution that aligns with our digital transformation initiatives.",
    ]
    
    scope_items_pool = [
        "Full implementation and deployment of the proposed solution",
        "Integration with existing systems and infrastructure",
        "Data migration and transition planning",
        "User training and change management support",
        "Ongoing support and maintenance services",
        "Documentation and knowledge transfer",
        "Customization and configuration as needed",
        "Performance optimization and tuning",
        "Security assessment and hardening",
        "Disaster recovery and backup solutions",
    ]
    
    selected_scope_items = random.sample(scope_items_pool, random.randint(6, 8))
    
    story.append(Paragraph(
        f"<b>Objective:</b> {random.choice(scope_objectives)} The solution must be scalable, secure, "
        "and aligned with industry best practices.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "<b>Scope Includes:</b>",
        styles['Normal']
    ))
    for item in selected_scope_items:
        story.append(Paragraph(f"• {item}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Project Scope & Requirements
    story.append(Paragraph("Project Scope & Requirements", heading_style))
    
    # Group requirements by category
    req_by_category = {}
    for req in requirements:
        cat = req["category"]
        if cat not in req_by_category:
            req_by_category[cat] = []
        req_by_category[cat].append(req)
    
    for category in ["technical", "functional", "compliance", "delivery"]:
        if category in req_by_category:
            story.append(Paragraph(f"<b>{category.title()} Requirements</b>", styles['Heading3']))
            # Header row with white text
            req_data = [[
                Paragraph("Priority", table_header_style),
                Paragraph("Description", table_header_style),
                Paragraph("Weight", table_header_style)
            ]]
            for req in req_by_category[category]:
                # Use Paragraph for description to enable word wrapping
                desc_para = Paragraph(req["description"], styles['Normal'])
                req_data.append([
                    Paragraph(req["priority"].title(), styles['Normal']),
                    desc_para,
                    Paragraph(f"{req['weight']:.1f}", styles['Normal'])
                ])
            
            # Adjust column widths to fit page
            req_table = Table(req_data, colWidths=[1.0 * inch, 4.2 * inch, 0.8 * inch])
            req_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(req_table)
            story.append(Spacer(1, 0.15 * inch))
    
    story.append(PageBreak())
    
    # Evaluation Criteria
    story.append(Paragraph("Evaluation Criteria", heading_style))
    # Header row with white text
    crit_data = [[
        Paragraph("Category", table_header_style),
        Paragraph("Weight (%)", table_header_style),
        Paragraph("Description", table_header_style)
    ]]
    for crit in criteria:
        # Use Paragraph for description to enable word wrapping
        desc_para = Paragraph(crit["description"], styles['Normal'])
        crit_data.append([
            Paragraph(crit["category"].title(), styles['Normal']),
            Paragraph(f"{crit['weight']:.1f}%", styles['Normal']),
            desc_para
        ])
    
    # Adjust column widths to fit page
    crit_table = Table(crit_data, colWidths=[1.3 * inch, 0.9 * inch, 4.3 * inch])
    crit_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(crit_table)
    story.append(Spacer(1, 0.2 * inch))
    
    # Pricing Structure Section
    story.append(Paragraph("Pricing Structure", heading_style))
    story.append(Paragraph(
        "Suppliers should provide detailed pricing breakdowns including:",
        styles['Normal']
    ))
    story.append(Paragraph("• One-time implementation costs", styles['Normal']))
    story.append(Paragraph("• Recurring subscription or maintenance fees", styles['Normal']))
    story.append(Paragraph("• Additional service costs", styles['Normal']))
    story.append(Paragraph("• Payment terms and conditions", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Delivery Timeline Requirements
    story.append(Paragraph("Delivery Timeline Requirements", heading_style))
    story.append(Paragraph(
        "Suppliers should provide a detailed implementation timeline with key milestones, "
        "including project kickoff, development phases, testing, and go-live dates.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(PageBreak())
    
    # RFP Questions for Respondents
    story.append(Paragraph("Questions for Respondents", heading_style))
    story.append(Paragraph(
        "Please provide detailed answers to the following questions in your proposal response. "
        "These answers will be evaluated as part of the selection process.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15 * inch))
    
    rfp_questions = get_rfp_questions(topic)
    for i, question in enumerate(rfp_questions, 1):
        story.append(Paragraph(
            f"<b>Q{i}:</b> {question}",
            styles['Normal']
        ))
        story.append(Spacer(1, 0.1 * inch))
    
    story.append(PageBreak())
    
    # Compliance Requirements
    story.append(Paragraph("Compliance Requirements", heading_style))
    story.append(Paragraph(
        "Please provide attestations and documentation for the following:",
        styles['Normal']
    ))
    story.append(Paragraph("• Security certifications and compliance standards", styles['Normal']))
    story.append(Paragraph("• Data protection and privacy measures", styles['Normal']))
    story.append(Paragraph("• Geographic data residency requirements", styles['Normal']))
    story.append(Paragraph("• Business continuity and disaster recovery capabilities", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Submission Instructions
    story.append(Paragraph("Submission Instructions", heading_style))
    story.append(Paragraph(
        "Please submit your proposal in PDF format by the specified deadline. "
        "Include all required documentation, pricing details, and compliance attestations.",
        styles['Normal']
    ))
    
    doc.build(story)
    return str(filepath)


def generate_supplier_response_pdf(
    supplier_profile: Dict[str, Any],
    supplier_index: int,
    rfp_requirements: List[Dict],
    topic: str,
    template: Dict[str, Any],
    output_path: Path,
    rfp_questions: List[str]
) -> str:
    """Generate supplier response PDF with variation strategy."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError(
            "reportlab is required for PDF generation but is not installed. "
            "Install it with: pip install reportlab"
        )
    
    filename = f"supplier_{supplier_index}_response.pdf"
    filepath = output_path / filename
    
    # Variation strategies: 0=Premium, 1=Balanced, 2=Budget
    strategy = (supplier_index - 1) % 3
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Table header style with white text
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    # Title page for supplier response
    title_style_supplier = ParagraphStyle(
        'SupplierTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph("Proposal Response", title_style_supplier))
    story.append(Paragraph(topic, title_style_supplier))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"Submitted by: {supplier_profile['supplier_name']}", ParagraphStyle('TitleDetails', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.4 * inch))
    
    # Company info on title page
    story.append(Paragraph(supplier_profile['supplier_name'], ParagraphStyle('TitleCompany', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER)))
    story.append(Paragraph(f"{supplier_profile['years_in_business']} Years in Business", ParagraphStyle('TitleLocation', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.grey)))
    story.append(Paragraph(f"Geographic Coverage: {supplier_profile['geographic_coverage']}", ParagraphStyle('TitleLocation', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.grey)))
    story.append(Spacer(1, 0.3 * inch))
    
    story.append(PageBreak())
    
    # Cover Letter
    story.append(Paragraph("Cover Letter", heading_style))
    story.append(Paragraph(topic, styles['Heading3']))
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph(
        f"Dear Procurement Team,\n\n"
        f"{supplier_profile['supplier_name']} is pleased to submit our proposal for the {topic} RFP. "
        f"With {supplier_profile['years_in_business']} years of experience and a proven track record "
        f"(Performance Score: {supplier_profile['past_performance_score']}/5.0), we are confident "
        f"in our ability to deliver exceptional results.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.3 * inch))
    
    # Company Background (Detailed)
    story.append(Paragraph("Company Background", heading_style))
    
    company_background = (
        f"{supplier_profile['supplier_name']} was founded in {2024 - supplier_profile['years_in_business']} "
        f"and has grown to become a leading provider of {topic.lower()} solutions. "
        f"With over {supplier_profile['years_in_business']} years of industry experience, we have successfully "
        f"delivered projects for {random.randint(50, 500)}+ clients across {supplier_profile['geographic_coverage']}.\n\n"
        f"Our company employs over {random.randint(100, 1000)} professionals, including certified architects, "
        f"engineers, and project managers. We maintain a {supplier_profile['past_performance_score']}/5.0 "
        f"customer satisfaction rating and have received industry recognition for innovation and excellence.\n\n"
        f"<b>Key Strengths:</b>\n"
        f"• Proven track record with {random.randint(20, 100)} similar projects completed in the past 3 years\n"
        f"• {supplier_profile['years_in_business']}+ years of cumulative experience in the industry\n"
        f"• Comprehensive certifications: {', '.join(supplier_profile.get('certifications', [])[:5])}\n"
        f"• Global presence with operations in {supplier_profile['geographic_coverage']}\n"
        f"• Dedicated support teams available {random.choice(['24/7', 'during business hours', 'extended hours'])}"
    )
    
    story.append(Paragraph(company_background, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    story.append(PageBreak())
    
    # Detailed Delivery Approach
    story.append(Paragraph("Delivery Approach & Methodology", heading_style))
    
    if strategy == 0:  # Premium
        approach_text = (
            "Our premium solution leverages cutting-edge technology and industry best practices. "
            "We provide comprehensive architecture design, advanced security features, and "
            "enterprise-grade scalability. Our approach includes dedicated technical resources, "
            "24/7 support, and proactive monitoring.\n\n"
            "<b>Implementation Methodology:</b>\n"
            "We follow an agile, iterative approach with continuous stakeholder engagement. Our methodology "
            "includes:\n"
            "• Discovery and requirements analysis phase with detailed documentation\n"
            "• Architecture design and technical specification development\n"
            "• Incremental development with regular demos and feedback cycles\n"
            "• Comprehensive testing including unit, integration, and user acceptance testing\n"
            "• Phased rollout with pilot groups before full deployment\n"
            "• Post-implementation optimization and continuous improvement"
        )
        pricing_multiplier = 1.3
        delivery_days = template["delivery_timeline"]["min_days"]
        team_size = random.randint(8, 15)
    elif strategy == 1:  # Balanced
        approach_text = (
            "Our balanced solution provides solid technical capabilities with cost-effective "
            "implementation. We follow industry standards and proven methodologies. Our approach "
            "includes standard support hours, comprehensive documentation, and regular updates.\n\n"
            "<b>Implementation Methodology:</b>\n"
            "We employ a structured, phase-based approach:\n"
            "• Requirements gathering and analysis\n"
            "• Solution design and configuration\n"
            "• Development and customization\n"
            "• Testing and quality assurance\n"
            "• Deployment and go-live support\n"
            "• Training and knowledge transfer"
        )
        pricing_multiplier = 1.0
        delivery_days = template["delivery_timeline"]["average_days"]
        team_size = random.randint(5, 10)
    else:  # Budget
        approach_text = (
            "Our cost-effective solution meets all mandatory requirements while providing "
            "essential functionality. We focus on core features and efficient implementation. "
            "Our approach includes standard support during business hours and self-service resources.\n\n"
            "<b>Implementation Methodology:</b>\n"
            "We use a streamlined, efficient approach:\n"
            "• Requirements documentation\n"
            "• Standard configuration and setup\n"
            "• Basic customization as needed\n"
            "• Testing and validation\n"
            "• Deployment with basic support\n"
            "• Self-service training materials"
        )
        pricing_multiplier = 0.7
        delivery_days = template["delivery_timeline"]["max_days"]
        team_size = random.randint(3, 6)
    
    story.append(Paragraph(approach_text, styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Resourcing Needs
    story.append(Paragraph("Project Team & Resourcing", heading_style))
    
    roles = ["Project Manager", "Solution Architect", "Senior Developer", "QA Engineer", "Business Analyst"]
    if strategy == 0:
        roles.extend(["DevOps Engineer", "Security Specialist", "Change Management Consultant"])
    elif strategy == 1:
        roles.extend(["Integration Specialist"])
    
    resource_text = (
        f"We will allocate a dedicated team of {team_size} professionals to ensure successful delivery:\n\n"
    )
    for i, role in enumerate(roles[:team_size], 1):
        resource_text += f"{i}. {role}: {random.choice(['Full-time', 'Part-time', 'As needed'])} allocation\n"
    
    resource_text += (
        f"\n<b>Team Structure:</b>\n"
        f"• Project Manager: Overall coordination and stakeholder management\n"
        f"• Technical Lead: Architecture and technical oversight\n"
        f"• Development Team: Implementation and customization\n"
        f"• QA Team: Testing and quality assurance\n"
        f"• Support Team: Post-implementation support and maintenance"
    )
    
    story.append(Paragraph(resource_text, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Pricing Breakdown
    story.append(Paragraph("Pricing Breakdown", heading_style))
    
    base_price = template["pricing_range"]["average"]
    total_price = base_price * pricing_multiplier
    
    pricing_items = [
        {"desc": "Implementation & Setup", "amount": total_price * 0.3},
        {"desc": "Annual Subscription (Year 1)", "amount": total_price * 0.5},
        {"desc": "Training & Documentation", "amount": total_price * 0.1},
        {"desc": "Support & Maintenance (Year 1)", "amount": total_price * 0.1},
    ]
    
    # Use Paragraph objects for proper text wrapping with white header text
    pricing_data = [[
        Paragraph("Item", table_header_style),
        Paragraph("Amount", table_header_style)
    ]]
    for item in pricing_items:
        pricing_data.append([
            Paragraph(item["desc"], styles['Normal']),
            Paragraph(f"${item['amount']:,.2f}", styles['Normal'])
        ])
    pricing_data.append([
        Paragraph("Total (Year 1)", ParagraphStyle('TableTotal', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold')),
        Paragraph(f"${total_price:,.2f}", ParagraphStyle('TableTotal', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold'))
    ])
    
    pricing_table = Table(pricing_data, colWidths=[4 * inch, 2 * inch])
    pricing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -2), 8),
        ('GRID', (0, 0), (-1, -2), 1, colors.grey),
        ('LINEBELOW', (0, -2), (-1, -2), 2, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(pricing_table)
    story.append(Spacer(1, 0.15 * inch))
    
    pricing_notes = (
        "<b>Payment Terms:</b> 30% upon contract signing, 40% upon completion of development phase, "
        "30% upon successful go-live. All prices are in USD and exclude applicable taxes.\n\n"
        "<b>Additional Costs:</b> Travel expenses (if required), third-party licenses, and custom "
        "integrations beyond standard scope will be quoted separately."
    )
    story.append(Paragraph(pricing_notes, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    story.append(PageBreak())
    
    # Detailed Delivery Timeline
    story.append(Paragraph("Detailed Delivery Timeline", heading_style))
    
    milestones = [
        {"phase": "Project Kickoff", "days": 7, "desc": "Team introduction, project charter, initial planning"},
        {"phase": "Requirements Analysis", "days": int(delivery_days * 0.2), "desc": "Detailed requirements gathering, gap analysis, documentation"},
        {"phase": "Design & Architecture", "days": int(delivery_days * 0.15), "desc": "Solution design, technical specifications, architecture review"},
        {"phase": "Development/Implementation", "days": int(delivery_days * 0.4), "desc": "Core development, customization, integration work"},
        {"phase": "Testing & Quality Assurance", "days": int(delivery_days * 0.15), "desc": "Unit testing, integration testing, UAT preparation"},
        {"phase": "Go-Live & Support", "days": int(delivery_days * 0.1), "desc": "Deployment, cutover, post-go-live support"},
    ]
    
    # Use Paragraph objects for proper text wrapping with white header text
    timeline_data = [[
        Paragraph("Phase", table_header_style),
        Paragraph("Duration", table_header_style),
        Paragraph("Key Activities", table_header_style)
    ]]
    for milestone in milestones:
        timeline_data.append([
            Paragraph(milestone["phase"], styles['Normal']),
            Paragraph(f"{milestone['days']} days", styles['Normal']),
            Paragraph(milestone["desc"], styles['Normal'])
        ])
    timeline_data.append([
        Paragraph("Total Implementation", ParagraphStyle('TableTotal', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold')),
        Paragraph(f"{delivery_days} days", ParagraphStyle('TableTotal', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold')),
        Paragraph("End-to-end project delivery", styles['Normal'])
    ])
    
    timeline_table = Table(timeline_data, colWidths=[1.6 * inch, 0.9 * inch, 3.5 * inch])
    timeline_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(timeline_table)
    story.append(Spacer(1, 0.2 * inch))
    
    timeline_note = (
        "<b>Timeline Notes:</b>\n"
        f"• Project duration: {delivery_days} calendar days from kickoff to go-live\n"
        "• Milestones are sequential with some overlap for efficiency\n"
        "• Regular status updates provided weekly\n"
        "• Change requests may impact timeline and will be managed through formal change control"
    )
    story.append(Paragraph(timeline_note, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    story.append(PageBreak())
    
    # Answers to RFP Questions
    story.append(Paragraph("Answers to RFP Questions", heading_style))
    story.append(Paragraph(
        "Below are our detailed responses to the questions posed in the RFP:",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15 * inch))
    
    # Track if we've handled case studies and references
    case_studies_handled = False
    references_handled = False
    
    # Create answer quality distribution (some detailed, some brief)
    # Assign quality levels: 0=detailed (2-3 paragraphs), 1=moderate (1 paragraph), 2=brief (few lines)
    num_questions = len(rfp_questions)
    quality_levels = []
    # Strategy 0 (Premium): More detailed answers
    if strategy == 0:
        quality_levels = [0] * (num_questions // 3) + [1] * (num_questions // 3) + [2] * (num_questions - 2 * (num_questions // 3))
    # Strategy 1 (Balanced): Mix
    elif strategy == 1:
        quality_levels = [0] * (num_questions // 4) + [1] * (num_questions // 2) + [2] * (num_questions - 3 * (num_questions // 4))
    # Strategy 2 (Budget): More brief answers
    else:
        quality_levels = [0] * (num_questions // 5) + [1] * (num_questions // 3) + [2] * (num_questions - (num_questions // 5) - (num_questions // 3))
    
    random.shuffle(quality_levels)
    
    # Generate answers to ALL questions with varied detail
    for i, question in enumerate(rfp_questions, 1):
        answer_prefix = f"Q{i}: {question}\n\n"
        quality = quality_levels[i - 1] if i <= len(quality_levels) else random.choice([0, 1, 2])
        
        # Check if this is case studies or references question
        is_case_studies = "case stud" in question.lower()
        is_references = "reference" in question.lower() and "case stud" not in question.lower()
        
        if is_case_studies and not case_studies_handled:
            case_studies_handled = True
            if strategy == 0:  # Premium - provide detailed case studies
                answer = (
                    f"<b>Case Studies:</b>\n\n"
                    f"We are pleased to provide {random.randint(3, 5)} detailed case studies of similar projects:\n\n"
                    f"<b>Case Study 1:</b> {random.choice(['Enterprise Cloud Migration', 'Digital Transformation', 'Infrastructure Modernization'])} "
                    f"for a {random.choice(['Fortune 500', 'mid-market', 'enterprise'])} client in {random.choice(['Financial Services', 'Healthcare', 'Manufacturing'])}. "
                    f"Project scope: {random.randint(50, 200)} users, {random.choice(['$500K', '$1M', '$2M'])} budget, completed in {random.randint(6, 18)} months. "
                    f"Key outcomes: {random.randint(20, 40)}% cost reduction, {random.randint(30, 50)}% performance improvement, zero downtime migration.\n\n"
                    f"<b>Case Study 2:</b> {random.choice(['ERP Implementation', 'System Integration', 'Platform Modernization'])} "
                    f"for a {random.choice(['global', 'regional', 'national'])} organization. "
                    f"Delivered on-time and on-budget, achieving {random.randint(95, 99)}% user satisfaction. "
                    f"Client reference available upon request.\n\n"
                    f"<b>Case Study 3:</b> {random.choice(['Legacy System Replacement', 'Cloud Infrastructure', 'Digital Platform'])} "
                    f"project completed successfully with {random.randint(15, 30)}% under budget. "
                    f"All deliverables met or exceeded expectations. Detailed case study document attached.\n\n"
                    f"Additional case studies and detailed project documentation are available upon request."
                )
            elif strategy == 1:  # Balanced - will provide later
                answer = (
                    f"<b>Case Studies:</b>\n\n"
                    f"We have completed {random.randint(15, 40)} similar projects in the past 3 years. "
                    f"Due to confidentiality agreements with some clients, we are in the process of obtaining "
                    f"permissions to share detailed case studies. We will provide at least 3 comprehensive "
                    f"case studies within {random.randint(5, 10)} business days of your request, or during "
                    f"the presentation phase if shortlisted. We can provide high-level summaries immediately "
                    f"upon request."
                )
            else:  # Budget - limited or unable
                answer = (
                    f"<b>Case Studies:</b>\n\n"
                    f"We have experience with {random.randint(5, 15)} similar projects. However, due to "
                    f"client confidentiality restrictions and the proprietary nature of some implementations, "
                    f"we are unable to provide detailed case studies at this time. We can provide general "
                    f"project descriptions and outcomes without client names. Alternatively, we can discuss "
                    f"our approach and methodologies in detail during presentations if shortlisted."
                )
        
        elif is_references and not references_handled:
            references_handled = True
            if strategy == 0:  # Premium - provide references
                answer = (
                    f"<b>Client References:</b>\n\n"
                    f"We are pleased to provide {random.randint(3, 5)} client references:\n\n"
                    f"<b>Reference 1:</b> {random.choice(['ABC Corporation', 'XYZ Industries', 'Global Systems Inc'])} - "
                    f"Contact: {random.choice(['John Smith', 'Sarah Johnson', 'Michael Chen'])} "
                    f"({random.choice(['VP IT', 'CIO', 'Director of Operations'])}), "
                    f"Phone: +1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}, "
                    f"Email: reference1@{random.choice(['example.com', 'clientcorp.com'])}. "
                    f"Project: {random.choice(['Cloud Migration', 'ERP Implementation'])} completed {random.randint(6, 24)} months ago.\n\n"
                    f"<b>Reference 2:</b> {random.choice(['TechVentures LLC', 'Enterprise Solutions', 'Premier Services'])} - "
                    f"Contact: {random.choice(['Emily Davis', 'Robert Wilson', 'Lisa Anderson'])} "
                    f"({random.choice(['CTO', 'VP Engineering', 'IT Director'])}), "
                    f"Phone: +1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}, "
                    f"Email: reference2@{random.choice(['example.com', 'clientcorp.com'])}. "
                    f"Project: {random.choice(['Digital Transformation', 'Infrastructure Upgrade'])} completed {random.randint(3, 18)} months ago.\n\n"
                    f"<b>Reference 3:</b> {random.choice(['Innovation Partners', 'Strategic Systems', 'Advanced Solutions'])} - "
                    f"Contact: {random.choice(['David Brown', 'Jennifer Martinez', 'Christopher Lee'])} "
                    f"({random.choice(['VP Technology', 'Director IT', 'Chief Architect'])}), "
                    f"Phone: +1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}, "
                    f"Email: reference3@{random.choice(['example.com', 'clientcorp.com'])}. "
                    f"Project: {random.choice(['System Integration', 'Platform Modernization'])} completed {random.randint(9, 30)} months ago.\n\n"
                    f"All references have been notified and are available for contact. Additional references available upon request."
                )
            elif strategy == 1:  # Balanced - will provide later
                answer = (
                    f"<b>Client References:</b>\n\n"
                    f"We have strong relationships with our clients and have completed {random.randint(15, 40)} successful projects. "
                    f"We are currently reaching out to our clients to obtain their consent for reference checks. "
                    f"We expect to provide at least 3 client references within {random.randint(7, 14)} business days, "
                    f"or we can coordinate reference calls during the evaluation phase if shortlisted. "
                    f"We can provide client names and project descriptions immediately, with contact information "
                    f"to follow once permissions are obtained."
                )
            else:  # Budget - unable to provide
                answer = (
                    f"<b>Client References:</b>\n\n"
                    f"While we have completed several projects in this domain, many of our clients have strict "
                    f"non-disclosure agreements that prevent us from sharing their contact information or project "
                    f"details publicly. We understand this is a standard requirement, and we are working to "
                    f"obtain permissions. However, we may not be able to provide the requested number of references "
                    f"at this stage. We can provide general testimonials and discuss our experience during "
                    f"presentations if shortlisted. We appreciate your understanding of these confidentiality constraints."
                )
        
        else:
            # Regular question answers with varied detail levels
            if quality == 0:  # Detailed (2-3 paragraphs)
                if strategy == 0:  # Premium
                    answer = (
                        f"{supplier_profile['supplier_name']} has extensive experience in this domain, with over "
                        f"{random.randint(25, 75)} similar projects completed in the past 3 years. Our approach "
                        f"combines industry best practices with innovative solutions tailored to each client's unique "
                        f"needs. We maintain a dedicated team of {random.randint(50, 200)} specialists and have "
                        f"proven methodologies that ensure consistent, high-quality delivery.\n\n"
                        f"Our methodology emphasizes {random.choice(['agile', 'iterative', 'phased'])} implementation "
                        f"with continuous stakeholder engagement. We utilize {random.choice(['industry-standard', 'proprietary', 'best-practice'])} "
                        f"frameworks and tools to ensure project success. Our track record includes a {random.randint(95, 99)}% "
                        f"success rate, with projects delivered on-time and within budget.\n\n"
                        f"Key differentiators include our focus on {random.choice(['innovation', 'quality', 'customer satisfaction'])} "
                        f"and our ability to {random.choice(['scale rapidly', 'adapt to changing requirements', 'deliver value early'])}. "
                        f"We invest significantly in training, tools, and processes to maintain our competitive edge."
                    )
                elif strategy == 1:  # Balanced
                    answer = (
                        f"We have successfully delivered {random.randint(15, 40)} similar projects over the past 3 years. "
                        f"Our team of {random.randint(30, 100)} professionals follows established methodologies and "
                        f"industry standards. We maintain a {random.randint(90, 95)}% project success rate and have "
                        f"strong references from satisfied clients.\n\n"
                        f"Our approach focuses on {random.choice(['proven methodologies', 'standard practices', 'industry best practices'])} "
                        f"while remaining flexible to client needs. We ensure regular communication, comprehensive "
                        f"documentation, and thorough testing throughout the project lifecycle."
                    )
                else:  # Budget
                    answer = (
                        f"We have experience with {random.randint(5, 20)} similar projects. Our team follows standard "
                        f"industry practices and maintains a focus on cost-effective delivery while meeting all "
                        f"mandatory requirements.\n\n"
                        f"We prioritize {random.choice(['essential functionality', 'core requirements', 'basic needs'])} "
                        f"and ensure reliable delivery within agreed timelines."
                    )
            
            elif quality == 1:  # Moderate (1 paragraph)
                if strategy == 0:
                    answer = (
                        f"{supplier_profile['supplier_name']} has extensive experience in this domain. "
                        f"We have completed {random.randint(25, 75)} similar projects in the past 3 years, "
                        f"with a {random.randint(95, 99)}% success rate. Our approach combines industry best "
                        f"practices with innovative solutions tailored to each client's unique needs. "
                        f"We maintain a dedicated team of {random.randint(50, 200)} specialists and have "
                        f"proven methodologies that ensure consistent, high-quality delivery."
                    )
                elif strategy == 1:
                    answer = (
                        f"We have successfully delivered {random.randint(15, 40)} similar projects over the "
                        f"past 3 years. Our team of {random.randint(30, 100)} professionals follows "
                        f"established methodologies and industry standards. We maintain a {random.randint(90, 95)}% "
                        f"project success rate and have strong references from satisfied clients."
                    )
                else:
                    answer = (
                        f"We have experience with {random.randint(5, 20)} similar projects. Our team follows "
                        f"standard industry practices and maintains a focus on cost-effective delivery while "
                        f"meeting all mandatory requirements."
                    )
            
            else:  # Brief (few lines)
                if strategy == 0:
                    answer = (
                        f"We have completed {random.randint(25, 75)} similar projects with a {random.randint(95, 99)}% "
                        f"success rate. Our team of {random.randint(50, 200)} specialists follows industry best practices."
                    )
                elif strategy == 1:
                    answer = (
                        f"We have delivered {random.randint(15, 40)} similar projects. Our team follows established "
                        f"methodologies and maintains a {random.randint(90, 95)}% success rate."
                    )
                else:
                    answer = (
                        f"We have experience with {random.randint(5, 20)} similar projects and follow standard "
                        f"industry practices."
                    )
        
        story.append(Paragraph(f"<b>{answer_prefix}</b>{answer}", styles['Normal']))
        story.append(Spacer(1, 0.15 * inch))
        
        # Add page break if we've answered many questions (to avoid overly long pages)
        if i % 8 == 0 and i < num_questions:
            story.append(PageBreak())
    
    story.append(PageBreak())
    
    # Compliance Attestations
    story.append(Paragraph("Compliance Attestations", heading_style))
    
    certs = supplier_profile.get("certifications", [])
    compliance_text = "We attest compliance with the following requirements:\n\n"
    for cert in certs:
        compliance_text += f"• {cert} certified\n"
    compliance_text += (
        f"\n<b>Geographic Coverage:</b> {supplier_profile['geographic_coverage']}\n\n"
        f"<b>Security Measures:</b>\n"
        f"• Data encryption at rest and in transit\n"
        f"• Regular security audits and penetration testing\n"
        f"• Access controls and identity management\n"
        f"• Incident response and breach notification procedures\n\n"
        f"<b>Business Continuity:</b>\n"
        f"• {random.choice(['99.9%', '99.95%', '99.99%'])} uptime SLA\n"
        f"• Redundant systems and failover capabilities\n"
        f"• Regular backup and disaster recovery testing"
    )
    
    story.append(Paragraph(compliance_text, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Contact Information
    story.append(Paragraph("Contact Information", heading_style))
    contact_text = (
        f"<b>{supplier_profile['supplier_name']}</b>\n\n"
        f"Contact Person: {random.choice(['John Smith', 'Sarah Johnson', 'Michael Chen', 'Emily Davis'])}\n"
        f"Title: {random.choice(['VP of Sales', 'Director of Business Development', 'Account Executive'])}\n"
        f"Email: contact@{supplier_profile['supplier_name'].lower().replace(' ', '')}.com\n"
        f"Phone: +1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}\n"
        f"Website: www.{supplier_profile['supplier_name'].lower().replace(' ', '')}.com"
    )
    story.append(Paragraph(contact_text, styles['Normal']))
    
    doc.build(story)
    return str(filepath)


def create_database_schema(db_path: str) -> None:
    """Create all database tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Requirements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requirements (
            requirement_id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            weight REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Evaluation criteria table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_criteria (
            criteria_id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            weight REAL NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Scoring rubric table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scoring_rubric (
            rubric_id TEXT PRIMARY KEY,
            criteria_category TEXT NOT NULL,
            score_level INTEGER NOT NULL,
            description TEXT NOT NULL,
            qualitative_label TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Benchmark data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_data (
            benchmark_id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            industry_average REAL,
            best_in_class REAL,
            acceptable_range TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Compliance reference table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compliance_reference (
            compliance_id TEXT PRIMARY KEY,
            requirement_type TEXT NOT NULL,
            description TEXT NOT NULL,
            mandatory INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Supplier profiles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supplier_profiles (
            supplier_id TEXT PRIMARY KEY,
            supplier_name TEXT NOT NULL,
            years_in_business INTEGER,
            past_performance_score REAL,
            certifications TEXT,
            geographic_coverage TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Evaluation results table (for tracking pipeline runs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_results (
            evaluation_id TEXT PRIMARY KEY,
            run_id TEXT,
            supplier_id TEXT NOT NULL,
            technical_score REAL,
            pricing_score REAL,
            delivery_score REAL,
            compliance_score REAL,
            total_score REAL,
            recommendation TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES supplier_profiles(supplier_id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requirements_category ON requirements(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requirements_priority ON requirements(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evaluation_criteria_category ON evaluation_criteria(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scoring_rubric_category ON scoring_rubric(criteria_category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_benchmark_category ON benchmark_data(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_compliance_type ON compliance_reference(requirement_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evaluation_results_supplier ON evaluation_results(supplier_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evaluation_results_run ON evaluation_results(run_id)")
    
    conn.commit()
    conn.close()
    print("✓ Database schema created")


def main():
    parser = argparse.ArgumentParser(description="Setup Supplier RFP Evaluation database and mock data")
    parser.add_argument(
        "--db-path",
        type=str,
        default="projects/ensemble/data/rfp/rfp_database.db",
        help="Path to SQLite database file (default: projects/ensemble/data/rfp/rfp_database.db)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="projects/ensemble/data/rfp",
        help="Base directory for generated files (default: projects/ensemble/data/rfp)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing tables and recreate (WARNING: deletes all data)"
    )
    parser.add_argument(
        "--supplier-count",
        type=int,
        default=3,
        help="Number of supplier responses to generate (default: 3)"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="Cloud Infrastructure",
        help="RFP topic (default: 'Agentic AI Platform Build')"
    )
    
    args = parser.parse_args()
    
    # Use arguments directly (no interactive prompts)
    topic = args.topic if args.topic else "Agentic AI Platform Build"
    output_dir = args.output_dir
    supplier_count = args.supplier_count
    
    # Detect project name for path resolution
    project_name = detect_project_name(Path.cwd())
    
    # Resolve paths intelligently (works from repo root or project_dir)
    db_path = resolve_script_path(args.db_path, project_name=project_name)
    output_path = resolve_script_path(output_dir, project_name=project_name)
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.mkdir(parents=True, exist_ok=True)
    supplier_responses_dir = output_path / "supplier_responses"
    supplier_responses_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 70)
    print("Supplier RFP Evaluation Database Setup")
    print("=" * 70)
    print(f"\nTopic: {topic}")
    print(f"Database: {db_path}")
    print(f"Output directory: {output_path}")
    print(f"Reset mode: {args.reset}")
    print(f"Supplier responses: {supplier_count}")
    print()
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Reset if requested
    if args.reset:
        print("⚠ Resetting database (dropping all tables)...")
        cursor.execute("DROP TABLE IF EXISTS evaluation_results")
        cursor.execute("DROP TABLE IF EXISTS supplier_profiles")
        cursor.execute("DROP TABLE IF EXISTS compliance_reference")
        cursor.execute("DROP TABLE IF EXISTS benchmark_data")
        cursor.execute("DROP TABLE IF EXISTS scoring_rubric")
        cursor.execute("DROP TABLE IF EXISTS evaluation_criteria")
        cursor.execute("DROP TABLE IF EXISTS requirements")
        conn.commit()
        print("✓ Tables dropped")
    
    # Create schema
    print("\n1. Creating database schema...")
    create_database_schema(str(db_path))
    
    # Get topic template
    template = get_topic_templates(topic)
    
    # Populate database tables
    print("\n2. Populating requirements...")
    populate_requirements(cursor, topic)
    
    print("\n3. Populating evaluation criteria...")
    populate_evaluation_criteria(cursor)
    
    print("\n4. Populating scoring rubric...")
    populate_scoring_rubric(cursor)
    
    print("\n5. Populating benchmark data...")
    populate_benchmark_data(cursor, topic)
    
    print("\n6. Populating compliance reference...")
    populate_compliance_reference(cursor, topic)
    
    print("\n7. Populating supplier profiles...")
    suppliers = populate_supplier_profiles(cursor, supplier_count)
    
    conn.commit()
    
    # Get requirements and criteria for PDF generation
    cursor.execute("SELECT * FROM requirements ORDER BY category, requirement_id")
    requirements_data = []
    for row in cursor.fetchall():
        requirements_data.append({
            "category": row[1],
            "description": row[2],
            "priority": row[3],
            "weight": row[4],
        })
    
    cursor.execute("SELECT * FROM evaluation_criteria ORDER BY criteria_id")
    criteria_data = []
    for row in cursor.fetchall():
        criteria_data.append({
            "category": row[1],
            "weight": row[2],
            "description": row[3],
        })
    
    conn.close()
    
    # Generate PDFs
    if REPORTLAB_AVAILABLE:
        print("\n8. Cleaning up existing PDF files...")
        # Delete existing RFP PDF
        rfp_pdf_file = output_path / "rfp_document.pdf"
        if rfp_pdf_file.exists():
            rfp_pdf_file.unlink()
            print(f"  ✓ Removed existing: {rfp_pdf_file.name}")
        
        # Delete all existing supplier response PDFs
        existing_supplier_pdfs = list(supplier_responses_dir.glob("supplier_*_response.pdf"))
        for pdf_file in existing_supplier_pdfs:
            pdf_file.unlink()
        if existing_supplier_pdfs:
            print(f"  ✓ Removed {len(existing_supplier_pdfs)} existing supplier response PDF(s)")
        
        print("\n9. Generating RFP PDF document...")
        issuing_company = None
        rfp_timeline = None
        try:
            rfp_pdf_path, issuing_company, rfp_timeline = generate_rfp_pdf(topic, requirements_data, criteria_data, output_path)
            print(f"✓ Generated: {Path(rfp_pdf_path).name}")
        except Exception as e:
            print(f"⚠ Failed to generate RFP PDF: {e}")
            # Fallback if PDF generation fails
            issuing_company = get_issuing_company_profile()
            rfp_timeline = get_rfp_timeline()
        
        # Get RFP questions for supplier responses (randomized)
        rfp_questions = get_rfp_questions(topic)
        
        print(f"\n10. Generating {supplier_count} supplier response PDFs...")
        for i, supplier in enumerate(suppliers, 1):
            try:
                supplier_pdf_path = generate_supplier_response_pdf(
                    supplier, i, requirements_data, topic, template, supplier_responses_dir, rfp_questions
                )
                print(f"  ✓ Generated: {Path(supplier_pdf_path).name}")
            except Exception as e:
                print(f"  ⚠ Failed to generate supplier {i} PDF: {e}")
    else:
        print("\n⚠ Skipping PDF generation (reportlab not available)")
    
    # Summary
    print("\n" + "=" * 70)
    print("Setup Complete!")
    print("=" * 70)
    print(f"\nTopic: {topic}")
    print(f"Database: {db_path}")
    print(f"Output directory: {output_path}")
    
    # Count records
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM requirements")
    req_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM supplier_profiles")
    supplier_profile_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM evaluation_criteria")
    criteria_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM benchmark_data")
    benchmark_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM compliance_reference")
    compliance_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\nDatabase Records:")
    print(f"  Requirements: {req_count}")
    print(f"  Evaluation Criteria: {criteria_count}")
    print(f"  Supplier Profiles: {supplier_profile_count}")
    print(f"  Benchmark Metrics: {benchmark_count}")
    print(f"  Compliance Requirements: {compliance_count}")
    
    if REPORTLAB_AVAILABLE:
        print(f"\nGenerated Files:")
        print(f"  RFP Document: {output_path / 'rfp_document.pdf'}")
        print(f"  Supplier Responses: {supplier_responses_dir}")
        for i in range(1, supplier_count + 1):
            print(f"    - supplier_{i}_response.pdf")
    
    print("\n✓ Setup complete! You can now run the Supplier RFP Evaluation pipeline.")


if __name__ == "__main__":
    main()

