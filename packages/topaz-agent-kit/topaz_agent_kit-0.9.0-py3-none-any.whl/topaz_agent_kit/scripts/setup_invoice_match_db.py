#!/usr/bin/env python3
"""Setup script for Invoice Match Pro pipeline.

Creates SQLite database, initializes schema, and generates mock data:
- Purchase Orders (POs) with line items
- SOW/Receipts with line items
- Invoice PDF files

Usage:
    python scripts/setup_invoice_match_db.py [--db-path <path>] [--output-dir <dir>] [--reset]
    uv run -m scripts.setup_invoice_match_db --db-path projects/ensemble/data/invoices/invoice_match.db --output-dir projects/ensemble/data/invoices/pending
"""

import sqlite3
import os
import sys
import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from topaz_agent_kit.utils.path_resolver import resolve_script_path, detect_project_name

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not available. PDF generation will be skipped.")
    print("Install with: pip install reportlab")


def create_database_schema(db_path: str) -> None:
    """Create all database tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Purchase Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE NOT NULL,
            po_date DATE NOT NULL,
            vendor_name TEXT NOT NULL,
            vendor_id TEXT,
            status TEXT NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            currency TEXT DEFAULT 'USD',
            approver TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # PO Line Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS po_line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT NOT NULL,
            item_code TEXT,
            description TEXT NOT NULL,
            quantity DECIMAL(10, 2) NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            total DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (po_number) REFERENCES purchase_orders(po_number) ON DELETE CASCADE
        )
    """)
    
    # SOW/Receipts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sow_receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sow_number TEXT UNIQUE NOT NULL,
            po_number TEXT NOT NULL,
            receipt_date DATE NOT NULL,
            status TEXT NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            received_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (po_number) REFERENCES purchase_orders(po_number)
        )
    """)
    
    # SOW Line Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sow_line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sow_number TEXT NOT NULL,
            item_code TEXT,
            description TEXT NOT NULL,
            quantity_received DECIMAL(10, 2) NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            total DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (sow_number) REFERENCES sow_receipts(sow_number) ON DELETE CASCADE
        )
    """)
    
    # Invoice Processing tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_processing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_file TEXT NOT NULL,
            invoice_number TEXT,
            vendor_name TEXT,
            invoice_date DATE,
            total_amount DECIMAL(10, 2),
            po_number TEXT,
            sow_number TEXT,
            match_status TEXT NOT NULL,
            match_score DECIMAL(3, 2),
            final_location TEXT,
            processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by TEXT,
            notes TEXT,
            run_id TEXT,
            FOREIGN KEY (po_number) REFERENCES purchase_orders(po_number)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✓ Database schema created in {db_path}")


def generate_mock_pos(cursor, count: int = 15) -> list:
    """Generate mock Purchase Orders."""
    vendors = [
        ("ABC Corp", "VEND-001"),
        ("XYZ Industries", "VEND-002"),
        ("Tech Solutions Inc", "VEND-003"),
        ("Global Services Ltd", "VEND-004"),
        ("Digital Systems", "VEND-005"),
    ]
    
    services = [
        ("SRV-001", "Cloud Infrastructure Setup", 500.00),
        ("SRV-002", "Software Development Services", 750.00),
        ("SRV-003", "Data Migration Services", 600.00),
        ("SRV-004", "System Integration", 850.00),
        ("SRV-005", "Technical Consulting", 400.00),
        ("SRV-006", "Security Audit", 1200.00),
        ("SRV-007", "Performance Optimization", 550.00),
    ]
    
    pos = []
    base_date = datetime.now() - timedelta(days=60)
    
    for i in range(count):
        po_number = f"PO-2024-{100 + i:03d}"
        vendor_name, vendor_id = random.choice(vendors)
        po_date = base_date + timedelta(days=random.randint(0, 50))
        
        # Generate line items
        num_items = random.randint(1, 4)
        line_items = random.sample(services, num_items)
        
        total_amount = 0.0
        for item_code, description, base_price in line_items:
            quantity = random.randint(5, 20)
            unit_price = base_price + random.uniform(-50, 50)
            total_amount += quantity * unit_price
        
        cursor.execute("""
            INSERT INTO purchase_orders 
            (po_number, po_date, vendor_name, vendor_id, status, total_amount, currency, approver)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (po_number, po_date.strftime("%Y-%m-%d"), vendor_name, vendor_id, "approved", 
              round(total_amount, 2), "USD", "John Doe"))
        
        # Insert line items
        for item_code, description, base_price in line_items:
            quantity = random.randint(5, 20)
            unit_price = base_price + random.uniform(-50, 50)
            item_total = quantity * unit_price
            
            cursor.execute("""
                INSERT INTO po_line_items 
                (po_number, item_code, description, quantity, unit_price, total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (po_number, item_code, description, quantity, round(unit_price, 2), round(item_total, 2)))
        
        pos.append({
            "po_number": po_number,
            "vendor_name": vendor_name,
            "total_amount": total_amount,
            "po_date": po_date
        })
    
    return pos


def generate_mock_sows(cursor, pos: list, count: int = 12) -> list:
    """Generate mock SOW/Receipts for some POs."""
    # Select some POs to have SOWs (not all)
    pos_with_sow = random.sample(pos, min(count, len(pos)))
    
    sows = []
    base_date = datetime.now() - timedelta(days=30)
    
    for po in pos_with_sow:
        sow_number = f"SOW-2024-{200 + len(sows):03d}"
        receipt_date = po["po_date"] + timedelta(days=random.randint(5, 20))
        
        # Get PO line items
        cursor.execute("SELECT * FROM po_line_items WHERE po_number = ?", (po["po_number"],))
        po_items = cursor.fetchall()
        
        # Create SOW with same or partial items
        sow_total = 0.0
        sow_items = []
        
        for item in po_items:
            # item tuple: (id, po_number, item_code, description, quantity, unit_price, total)
            # Indices:     0    1          2          3           4         5           6
            item_code = item[2]
            description = item[3]
            quantity = float(item[4])  # Ensure it's a float
            unit_price = float(item[5])  # Ensure it's a float
            
            # Sometimes receive full quantity, sometimes partial
            if random.random() > 0.3:  # 70% chance to include item
                quantity_received = quantity if random.random() > 0.2 else quantity * random.uniform(0.7, 0.95)
                item_total = quantity_received * unit_price
                sow_total += item_total
                sow_items.append((item_code, description, quantity_received, unit_price, item_total))
        
        cursor.execute("""
            INSERT INTO sow_receipts 
            (sow_number, po_number, receipt_date, status, total_amount, received_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sow_number, po["po_number"], receipt_date.strftime("%Y-%m-%d"), "completed",
              round(sow_total, 2), "Jane Smith"))
        
        # Insert SOW line items
        for item_code, description, qty, price, total in sow_items:
            cursor.execute("""
                INSERT INTO sow_line_items 
                (sow_number, item_code, description, quantity_received, unit_price, total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sow_number, item_code, description, round(qty, 2), round(price, 2), round(total, 2)))
        
        sows.append({
            "sow_number": sow_number,
            "po_number": po["po_number"],
            "total_amount": sow_total
        })
    
    return sows


def generate_invoice_pdf(output_dir: str, invoice_data: dict) -> str:
    """Generate a PDF invoice file."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError(
            "reportlab is required for PDF generation but is not installed. "
            "Install it with: pip install reportlab"
        )
    
    filename = f"{invoice_data['invoice_number']}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Choose a layout variant based on invoice number for structural diversity
    variant_index = hash(invoice_data['invoice_number']) % 3
    
    if variant_index == 0:
        # Variant A: Classic table-based invoice
        story.append(Paragraph("INVOICE", styles['Title']))
        story.append(Spacer(1, 0.2 * inch))

        header_data = [
            ["Invoice Number:", invoice_data['invoice_number']],
            ["Invoice Date:", invoice_data['invoice_date']],
            ["Due Date:", invoice_data['due_date']],
            ["Vendor:", invoice_data['vendor_name']],
            ["PO Reference:", invoice_data.get('po_reference', 'N/A')],
        ]
        header_table = Table(header_data, colWidths=[2 * inch, 4 * inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.3 * inch))

        story.append(Paragraph("Line Items", styles['Heading2']))
        line_item_data = [["Description", "Quantity", "Unit Price", "Total"]]
        for item in invoice_data['line_items']:
            line_item_data.append([
                item['description'],
                str(item['quantity']),
                f"${item['unit_price']:.2f}",
                f"${item['total']:.2f}",
            ])

        item_table = Table(line_item_data, colWidths=[3 * inch, 1 * inch, 1.5 * inch, 1.5 * inch])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 0.2 * inch))

        total_data = [
            ["Subtotal:", f"${invoice_data['total_amount']:.2f}"],
            ["Tax:", f"${invoice_data.get('tax_amount', 0):.2f}"],
            ["Total:", f"${invoice_data['total_amount'] + invoice_data.get('tax_amount', 0):.2f}"],
        ]
        total_table = Table(total_data, colWidths=[4 * inch, 2 * inch])
        total_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
        ]))
        story.append(total_table)

    elif variant_index == 1:
        # Variant B: Letterhead-style with two-column info layout
        story.append(Paragraph(invoice_data['vendor_name'], styles['Title']))
        story.append(Paragraph("Invoice", styles['Heading2']))
        story.append(Spacer(1, 0.15 * inch))

        header_data = [
            ["Invoice #", invoice_data['invoice_number'], "Invoice Date", invoice_data['invoice_date']],
            ["PO Reference", invoice_data.get('po_reference', 'N/A'), "Due Date", invoice_data['due_date']],
        ]
        header_table = Table(header_data, colWidths=[1.3 * inch, 2.2 * inch, 1.3 * inch, 2.2 * inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.25 * inch))

        story.append(Paragraph("Charges", styles['Heading2']))
        line_item_data = [["Qty", "Description", "Unit Price", "Line Total"]]
        for item in invoice_data['line_items']:
            line_item_data.append([
                str(item['quantity']),
                item['description'],
                f"${item['unit_price']:.2f}",
                f"${item['total']:.2f}",
            ])

        item_table = Table(line_item_data, colWidths=[0.8 * inch, 3.2 * inch, 1.2 * inch, 1.3 * inch])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 0.2 * inch))

        total_data = [
            ["Subtotal", f"${invoice_data['total_amount']:.2f}"],
            ["Tax", f"${invoice_data.get('tax_amount', 0):.2f}"],
            ["Amount Due", f"${invoice_data['total_amount'] + invoice_data.get('tax_amount', 0):.2f}"],
        ]
        total_table = Table(total_data, colWidths=[4 * inch, 2 * inch])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        story.append(total_table)

    else:
        # Variant C: Minimal layout with paragraph metadata and compact items table
        story.append(Paragraph("Invoice Summary", styles['Title']))
        story.append(Spacer(1, 0.1 * inch))

        meta_paragraph = (
            f"Invoice <b>{invoice_data['invoice_number']}</b> for vendor "
            f"<b>{invoice_data['vendor_name']}</b> dated {invoice_data['invoice_date']} "
            f"with due date {invoice_data['due_date']}. "
            f"PO reference: {invoice_data.get('po_reference', 'N/A')}."
        )
        story.append(Paragraph(meta_paragraph, styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("Details", styles['Heading3']))
        line_item_data = [["Description", "Qty", "Price", "Total"]]
        for item in invoice_data['line_items']:
            line_item_data.append([
                item['description'],
                str(item['quantity']),
                f"${item['unit_price']:.2f}",
                f"${item['total']:.2f}",
            ])

        item_table = Table(line_item_data, colWidths=[3.2 * inch, 0.8 * inch, 1.2 * inch, 1.3 * inch])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('LINEBELOW', (0, 0), (-1, 0), 0.75, colors.black),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 0.2 * inch))

        total_text = (
            f"Total amount due: <b>${invoice_data['total_amount'] + invoice_data.get('tax_amount', 0):.2f}</b> "
            f"(including tax ${invoice_data.get('tax_amount', 0):.2f})."
        )
        story.append(Paragraph(total_text, styles['Normal']))
    
    doc.build(story)
    return filepath


def generate_mock_invoices(output_dir: str, pos: list, sows: list, count: int = 8) -> list:
    """Generate mock invoice PDFs."""
    os.makedirs(output_dir, exist_ok=True)
    
    invoices = []
    base_date = datetime.now() - timedelta(days=20)
    
    # Create some invoices that match POs perfectly
    for i, po in enumerate(pos[:min(3, len(pos))]):
        invoice_data = {
            "invoice_number": f"INV-2024-{1000 + i:03d}",
            "vendor_name": po["vendor_name"],
            "invoice_date": (po["po_date"] + timedelta(days=random.randint(10, 25))).strftime("%Y-%m-%d"),
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "total_amount": po["total_amount"],  # Perfect match
            "po_reference": po["po_number"],
            "tax_amount": 0.0,
            "line_items": [
                {"description": f"Service Item {j+1}", "quantity": 10, "unit_price": po["total_amount"]/10, "total": po["total_amount"]/10}
                for j in range(1)
            ]
        }
        filepath = generate_invoice_pdf(output_dir, invoice_data)
        invoices.append(invoice_data)
        print(f"  ✓ Generated: {os.path.basename(filepath)}")
    
    # Create some invoices with less amount (should approve)
    for i, po in enumerate(pos[3:min(6, len(pos))]):
        invoice_data = {
            "invoice_number": f"INV-2024-{1003 + i:03d}",
            "vendor_name": po["vendor_name"],
            "invoice_date": (po["po_date"] + timedelta(days=random.randint(10, 25))).strftime("%Y-%m-%d"),
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "total_amount": round(po["total_amount"] * random.uniform(0.85, 0.95), 2),  # Less than PO
            "po_reference": po["po_number"],
            "tax_amount": 0.0,
            "line_items": [
                {"description": f"Partial Service {j+1}", "quantity": 8, "unit_price": po["total_amount"]/10, "total": po["total_amount"]/10 * 0.9}
                for j in range(1)
            ]
        }
        filepath = generate_invoice_pdf(output_dir, invoice_data)
        invoices.append(invoice_data)
        print(f"  ✓ Generated: {os.path.basename(filepath)}")
    
    # Create some invoices with more amount (needs clarification)
    for i, po in enumerate(pos[6:min(8, len(pos))]):
        invoice_data = {
            "invoice_number": f"INV-2024-{1006 + i:03d}",
            "vendor_name": po["vendor_name"],
            "invoice_date": (po["po_date"] + timedelta(days=random.randint(10, 25))).strftime("%Y-%m-%d"),
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "total_amount": round(po["total_amount"] * random.uniform(1.05, 1.15), 2),  # More than PO
            "po_reference": po["po_number"],
            "tax_amount": 0.0,
            "line_items": [
                {"description": f"Service Overrun {j+1}", "quantity": 12, "unit_price": po["total_amount"]/10, "total": po["total_amount"]/10 * 1.1}
                for j in range(1)
            ]
        }
        filepath = generate_invoice_pdf(output_dir, invoice_data)
        invoices.append(invoice_data)
        print(f"  ✓ Generated: {os.path.basename(filepath)}")
    
    # Create invoice with non-existent PO (needs clarification)
    invoice_data = {
        "invoice_number": f"INV-2024-{1010:03d}",
        "vendor_name": "Unknown Vendor",
        "invoice_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "total_amount": 3500.00,
        "po_reference": "PO-2024-999",  # Non-existent
        "tax_amount": 0.0,
        "line_items": [
            {"description": "Mystery Service", "quantity": 7, "unit_price": 500.00, "total": 3500.00}
        ]
    }
    filepath = generate_invoice_pdf(output_dir, invoice_data)
    invoices.append(invoice_data)
    print(f"  ✓ Generated: {os.path.basename(filepath)}")
    
    return invoices


def main():
    parser = argparse.ArgumentParser(description="Setup Invoice Match Pro database and mock data")
    parser.add_argument("--db-path", default="data/invoice_match.db",
                       help="Path to SQLite database file (default: data/invoice_match.db)")
    parser.add_argument("--output-dir", default="data/invoices/pending",
                       help="Directory for generated invoice PDFs (default: data/invoices/pending)")
    parser.add_argument("--reset", action="store_true",
                       help="Reset database (delete existing and recreate)")
    parser.add_argument("--po-count", type=int, default=15,
                       help="Number of mock POs to generate (default: 15)")
    parser.add_argument("--sow-count", type=int, default=12,
                       help="Number of mock SOWs to generate (default: 12)")
    parser.add_argument("--invoice-count", type=int, default=8,
                       help="Number of mock invoices to generate (default: 8)")
    
    args = parser.parse_args()
    
    # Detect project name for path resolution
    project_name = detect_project_name(Path.cwd())
    
    # Resolve paths intelligently (works from repo root or project_dir)
    db_path = resolve_script_path(args.db_path, project_name=project_name)
    output_dir = resolve_script_path(args.output_dir, project_name=project_name)
    
    # Reset database if requested
    if args.reset and db_path.exists():
        db_path.unlink()
        print(f"✓ Removed existing database: {db_path}")
    
    # Create database directory if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create database and schema
    create_database_schema(str(db_path))
    
    # Generate mock data
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print(f"\nGenerating {args.po_count} mock Purchase Orders...")
    pos = generate_mock_pos(cursor, args.po_count)
    print(f"✓ Generated {len(pos)} POs")
    
    print(f"\nGenerating {args.sow_count} mock SOW/Receipts...")
    sows = generate_mock_sows(cursor, pos, args.sow_count)
    print(f"✓ Generated {len(sows)} SOWs")
    
    conn.commit()
    conn.close()
    
    print(f"\nGenerating {args.invoice_count} mock invoice PDFs...")
    invoices = generate_mock_invoices(str(output_dir), pos, sows, args.invoice_count)
    print(f"✓ Generated {len(invoices)} invoice files in {output_dir}")
    
    # Create output folders at same level as pending folder
    base_dir = output_dir.parent
    for folder in ["approved", "declined", "clarification"]:
        folder_path = base_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created folder: {folder_path}")
    
    print(f"\n✓ Setup complete!")
    print(f"  Database: {db_path}")
    print(f"  Invoices: {output_dir}")
    print(f"\nYou can now run the Invoice Match Pro pipeline!")


if __name__ == "__main__":
    main()

