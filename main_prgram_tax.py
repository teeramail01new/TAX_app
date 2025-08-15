import flet as ft
# Compatibility aliases for different Flet versions (Icons/Colors vs icons/colors)
try:
    # On some versions attributes are CamelCase (Icons/Colors). Create lowercase aliases if needed.
    if not hasattr(ft, "colors") and hasattr(ft, "Colors"):
        setattr(ft, "colors", ft.Colors)
    if not hasattr(ft, "icons") and hasattr(ft, "Icons"):
        setattr(ft, "icons", ft.Icons)
except Exception:
    pass
import psycopg2
import pandas as pd
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import locale
import urllib.request
import tempfile
import os
import json
from decimal import Decimal
import sqlite3
from typing import Tuple, List

# Import the crystal report functionality from form_tax_18.py
try:
    from form_tax_18 import CrystalReportStyleRenderer
except ImportError:
    # Fallback minimal implementation if form_tax_18.py is not found
    class CrystalReportStyleRenderer:
        def __init__(self):
            self.connection_string = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
            self.template_pdf_path = "tax_form_template.pdf"
            self.template_image_path = "tax_form_background.jpg"
            self.output_dpi = 300
            self.init_database()
            self.setup_fonts()
            self.setup_report_engine()
        
        def setup_fonts(self):
            try:
                if os.path.exists('THSarabunNew.ttf'):
                    from reportlab.pdfbase.ttfonts import TTFont
                    from reportlab.pdfbase import pdfmetrics
                    pdfmetrics.registerFont(TTFont('THSarabunNew', 'THSarabunNew.ttf'))
                    self.thai_font = 'THSarabunNew'
                    self.thai_font_bold = 'THSarabunNew'
                else:
                    self.thai_font = 'Helvetica'
                    self.thai_font_bold = 'Helvetica-Bold'
            except:
                self.thai_font = 'Helvetica'
                self.thai_font_bold = 'Helvetica-Bold'
        
        def setup_report_engine(self):
            self.report_sections = {
                'page_header': {'height': 80, 'elements': []},
                'report_header': {'height': 120, 'elements': []},
                'detail_section': {'height': 400, 'elements': []},
                'report_footer': {'height': 100, 'elements': []},
                'page_footer': {'height': 50, 'elements': []}
            }
        
        def get_connection(self):
            try:
                conn = psycopg2.connect(self.connection_string)
                return conn
            except Exception as e:
                print(f"Database connection error: {e}")
                return None
        
        def init_database(self):
            conn = self.get_connection()
            if not conn:
                return False
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tax_withholding_certificates (
                        id SERIAL PRIMARY KEY,
                        withholder_name VARCHAR(255) NOT NULL,
                        withholder_address TEXT NOT NULL,
                        withholder_tax_id VARCHAR(13) NOT NULL,
                        withholder_type VARCHAR(50) NOT NULL,
                        withholdee_name VARCHAR(255) NOT NULL,
                        withholdee_address TEXT NOT NULL,
                        withholdee_tax_id VARCHAR(13) NOT NULL,
                        withholdee_type VARCHAR(50) NOT NULL,
                        certificate_book_no VARCHAR(50),
                        certificate_no VARCHAR(50),
                        sequence_in_form INTEGER,
                        form_type VARCHAR(20),
                        income_type_1_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_1_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_2_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_2_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_3_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_3_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_4a_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_4a_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_4b_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_4b_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_5_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_5_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_6_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_6_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_6_description TEXT,
                        total_income DECIMAL(15,2) DEFAULT 0,
                        total_tax_withheld DECIMAL(15,2) DEFAULT 0,
                        total_tax_withheld_text TEXT,
                        provident_fund DECIMAL(15,2) DEFAULT 0,
                        social_security_fund DECIMAL(15,2) DEFAULT 0,
                        retirement_mutual_fund DECIMAL(15,2) DEFAULT 0,
                        issue_type VARCHAR(50),
                        issue_type_other VARCHAR(100),
                        issue_date DATE,
                        signatory_name VARCHAR(255),
                        company_seal BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                ''')
                conn.commit()
                return True
            except Exception as e:
                print(f"Database initialization error: {e}")
                conn.rollback()
                return False
            finally:
                cursor.close()
                conn.close()
        
        def save_certificate(self, data):
            conn = self.get_connection()
            if not conn:
                return None
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tax_withholding_certificates (
                        withholder_name, withholder_address, withholder_tax_id, withholder_type,
                        withholdee_name, withholdee_address, withholdee_tax_id, withholdee_type,
                        certificate_book_no, certificate_no, sequence_in_form, form_type,
                        income_type_1_amount, income_type_1_tax,
                        income_type_2_amount, income_type_2_tax,
                        income_type_3_amount, income_type_3_tax,
                        income_type_4a_amount, income_type_4a_tax,
                        income_type_4b_amount, income_type_4b_tax,
                        income_type_5_amount, income_type_5_tax,
                        income_type_6_amount, income_type_6_tax, income_type_6_description,
                        total_income, total_tax_withheld, total_tax_withheld_text,
                        provident_fund, social_security_fund, retirement_mutual_fund,
                        issue_type, issue_type_other, issue_date, signatory_name, company_seal
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                ''', data)
                certificate_id = cursor.fetchone()[0]
                conn.commit()
                return certificate_id
            except Exception as e:
                print(f"Save certificate error: {e}")
                conn.rollback()
                return None
            finally:
                cursor.close()
                conn.close()
        
        def get_certificate_by_id(self, certificate_id):
            conn = self.get_connection()
            if not conn:
                return None
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tax_withholding_certificates WHERE id = %s", (certificate_id,))
                result = cursor.fetchone()
                if result:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'tax_withholding_certificates' 
                        ORDER BY ordinal_position
                    """)
                    columns = [row[0] for row in cursor.fetchall()]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                print(f"Get certificate error: {e}")
                return None
            finally:
                cursor.close()
                conn.close()
        
        def get_all_certificates(self):
            conn = self.get_connection()
            if not conn:
                return []
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, withholder_name, withholdee_name, total_income, 
                           total_tax_withheld, issue_date, created_at
                    FROM tax_withholding_certificates
                    ORDER BY created_at DESC
                    LIMIT 100;
                ''')
                return cursor.fetchall()
            except Exception as e:
                print(f"Get certificates error: {e}")
                return []
            finally:
                cursor.close()
                conn.close()
        
        def create_crystal_report_pdf(self, data, output_path):
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                from reportlab.lib.units import mm
                
                c = canvas.Canvas(output_path, pagesize=A4)
                width, height = A4
                
                # Simple text rendering for now
                c.setFont(self.thai_font, 12)
                c.drawString(100, height - 100, f"Certificate ID: {data.get('id', 'N/A')}")
                c.drawString(100, height - 120, f"Withholder: {data.get('withholder_name', 'N/A')}")
                c.drawString(100, height - 140, f"Withholdee: {data.get('withholdee_name', 'N/A')}")
                
                c.save()
                return True, f"Crystal Reports style PDF created: {output_path}"
            except Exception as e:
                return False, f"Report generation error: {str(e)}"

# Import the tax form functionality
try:
    from form_tax import NeonTaxWithholdingApp
except ImportError:
    # If form_tax.py is not available, create a minimal version
    class NeonTaxWithholdingApp:
        def __init__(self):
            self.connection_string = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
            self.init_database()

# Import the tax certificate functionality from program_tax_2.py
try:
    from program_tax_2 import NeonTaxWithholdingApp as TaxCertificateApp
except ImportError:
    # Fallback minimal implementation if program_tax_2.py is not found
    class TaxCertificateApp:
        def __init__(self):
            self.connection_string = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"

# Import the official tax form functionality from tax_form4.py
try:
    from tax_form4 import PDFTemplateFiller
except ImportError:
    # Fallback minimal implementation if tax_form4.py is not found
    class PDFTemplateFiller:
        def __init__(self):
            self.connection_string = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
            self.template_path = "tax_form_template.pdf"
            self.init_database()
            self.setup_fonts()
        
        def setup_fonts(self):
            try:
                if os.path.exists('THSarabunNew.ttf'):
                    from reportlab.pdfbase.ttfonts import TTFont
                    from reportlab.pdfbase import pdfmetrics
                    pdfmetrics.registerFont(TTFont('THSarabunNew', 'THSarabunNew.ttf'))
                    self.thai_font = 'THSarabunNew'
                else:
                    self.thai_font = 'Helvetica'
            except:
                self.thai_font = 'Helvetica'
        
        def get_connection(self):
            try:
                conn = psycopg2.connect(self.connection_string)
                return conn
            except Exception as e:
                print(f"Database connection error: {e}")
                return None
        
        def init_database(self):
            conn = self.get_connection()
            if not conn:
                return False
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tax_withholding_certificates (
                        id SERIAL PRIMARY KEY,
                        withholder_name VARCHAR(255) NOT NULL,
                        withholder_address TEXT NOT NULL,
                        withholder_tax_id VARCHAR(13) NOT NULL,
                        withholder_type VARCHAR(50) NOT NULL,
                        withholdee_name VARCHAR(255) NOT NULL,
                        withholdee_address TEXT NOT NULL,
                        withholdee_tax_id VARCHAR(13) NOT NULL,
                        withholdee_type VARCHAR(50) NOT NULL,
                        certificate_book_no VARCHAR(50),
                        certificate_no VARCHAR(50),
                        sequence_in_form INTEGER,
                        form_type VARCHAR(20),
                        income_type_1_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_1_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_2_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_2_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_3_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_3_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_4a_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_4a_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_4b_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_4b_tax DECIMAL(15,2) DEFAULT 0,
                        dividend_credit_type VARCHAR(100),
                        dividend_tax_rate DECIMAL(5,2),
                        income_type_5_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_5_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_6_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_6_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_6_description TEXT,
                        total_income DECIMAL(15,2) DEFAULT 0,
                        total_tax_withheld DECIMAL(15,2) DEFAULT 0,
                        total_tax_withheld_text TEXT,
                        provident_fund DECIMAL(15,2) DEFAULT 0,
                        social_security_fund DECIMAL(15,2) DEFAULT 0,
                        retirement_mutual_fund DECIMAL(15,2) DEFAULT 0,
                        issue_type VARCHAR(50),
                        issue_type_other VARCHAR(100),
                        issue_date DATE,
                        signatory_name VARCHAR(255),
                        company_seal BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                ''')
                conn.commit()
                return True
            except Exception as e:
                print(f"Database initialization error: {e}")
                conn.rollback()
                return False
            finally:
                cursor.close()
                conn.close()
        
        def save_certificate(self, data):
            conn = self.get_connection()
            if not conn:
                return None
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tax_withholding_certificates (
                        withholder_name, withholder_address, withholder_tax_id, withholder_type,
                        withholdee_name, withholdee_address, withholdee_tax_id, withholdee_type,
                        certificate_book_no, certificate_no, sequence_in_form, form_type,
                        income_type_1_amount, income_type_1_tax,
                        income_type_2_amount, income_type_2_tax,
                        income_type_3_amount, income_type_3_tax,
                        income_type_4a_amount, income_type_4a_tax,
                        income_type_4b_amount, income_type_4b_tax, dividend_credit_type, dividend_tax_rate,
                        income_type_5_amount, income_type_5_tax,
                        income_type_6_amount, income_type_6_tax, income_type_6_description,
                        total_income, total_tax_withheld, total_tax_withheld_text,
                        provident_fund, social_security_fund, retirement_mutual_fund,
                        issue_type, issue_type_other, issue_date, signatory_name, company_seal
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                ''', data)
                certificate_id = cursor.fetchone()[0]
                conn.commit()
                return certificate_id
            except Exception as e:
                print(f"Save certificate error: {e}")
                conn.rollback()
                return None
            finally:
                cursor.close()
                conn.close()
        
        def get_certificate_by_id(self, certificate_id):
            conn = self.get_connection()
            if not conn:
                return None
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tax_withholding_certificates WHERE id = %s", (certificate_id,))
                result = cursor.fetchone()
                if result:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'tax_withholding_certificates' 
                        ORDER BY ordinal_position
                    """)
                    columns = [row[0] for row in cursor.fetchall()]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                print(f"Get certificate error: {e}")
                return None
            finally:
                cursor.close()
                conn.close()
        
        def get_all_certificates(self):
            conn = self.get_connection()
            if not conn:
                return []
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, withholder_name, withholdee_name, total_income, 
                           total_tax_withheld, issue_date, created_at
                    FROM tax_withholding_certificates
                    ORDER BY created_at DESC
                    LIMIT 100;
                ''')
                return cursor.fetchall()
            except Exception as e:
                print(f"Get certificates error: {e}")
                return []
            finally:
                cursor.close()
                conn.close()
        
        def fill_pdf_template(self, data, output_path):
            """Fill PDF template with data and save to output_path"""
            try:
                # Ensure output_path is in the current working directory
                if not os.path.isabs(output_path):
                    output_path = os.path.join(os.getcwd(), output_path)
                
                # Create PDF document
                doc = SimpleDocTemplate(output_path, pagesize=A4)
                story = []
                
                # Register Thai font with multiple fallback options
                thai_font = 'Helvetica'  # Default fallback
                
                # List of possible Thai fonts to try
                thai_font_paths = [
                    'C:/Windows/Fonts/THSarabun.ttf',
                    'C:/Windows/Fonts/THSarabunNew.ttf',
                    'C:/Windows/Fonts/THSarabunPSK.ttf',
                    'C:/Windows/Fonts/THSarabunNewBold.ttf',
                    'C:/Windows/Fonts/THSarabunBold.ttf',
                    'C:/Windows/Fonts/THSarabunItalic.ttf',
                    'C:/Windows/Fonts/THSarabunNewItalic.ttf',
                    'C:/Windows/Fonts/THSarabunNewBoldItalic.ttf',
                    'C:/Windows/Fonts/THSarabunBoldItalic.ttf',
                    # Also try Linux/Mac paths
                    '/usr/share/fonts/truetype/thai/THSarabun.ttf',
                    '/System/Library/Fonts/Supplemental/THSarabun.ttf',
                    '/Library/Fonts/THSarabun.ttf'
                ]
                
                for font_path in thai_font_paths:
                    try:
                        if os.path.exists(font_path):
                            pdfmetrics.registerFont(TTFont('ThaiFont', font_path))
                            thai_font = 'ThaiFont'
                            break
                    except:
                        continue
                
                # Get styles with Thai font support
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    spaceAfter=30,
                    alignment=1,  # Center alignment
                    fontName=thai_font
                )
                subtitle_style = ParagraphStyle(
                    'CustomSubtitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    spaceAfter=20,
                    alignment=1,
                    fontName=thai_font
                )
                normal_style = ParagraphStyle(
                    'ThaiNormal',
                    parent=styles['Normal'],
                    fontName=thai_font,
                    fontSize=10
                )
                
                # Add title
                story.append(Paragraph("ใบรับรองการหักภาษี ณ ที่จ่าย", title_style))
                story.append(Spacer(1, 20))
                
                # Add generation date
                current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                story.append(Paragraph(f"วันที่สร้างเอกสาร: {current_date}", normal_style))
                story.append(Spacer(1, 30))
                
                # Add form information
                story.append(Paragraph("ข้อมูลผู้มีหน้าที่หักภาษี", subtitle_style))
                
                withholder_data = [
                    ['รายการ', 'ข้อมูล'],
                    ['ชื่อผู้มีหน้าที่หักภาษี', data.get('withholder_name', '')],
                    ['ที่อยู่', data.get('withholder_address', '')],
                    ['เลขประจำตัวผู้เสียภาษี', data.get('withholder_tax_id', '')],
                    ['ประเภท', data.get('withholder_type', '')]
                ]
                
                withholder_table = Table(withholder_data, colWidths=[2*inch, 3*inch])
                withholder_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), thai_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), thai_font),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                story.append(withholder_table)
                story.append(Spacer(1, 20))
                
                # Add withholdee information
                story.append(Paragraph("ข้อมูลผู้ถูกหักภาษี", subtitle_style))
                
                withholdee_data = [
                    ['รายการ', 'ข้อมูล'],
                    ['ชื่อผู้ถูกหักภาษี', data.get('withholdee_name', '')],
                    ['ที่อยู่', data.get('withholdee_address', '')],
                    ['เลขประจำตัวผู้เสียภาษี', data.get('withholdee_tax_id', '')],
                    ['ประเภท', data.get('withholdee_type', '')]
                ]
                
                withholdee_table = Table(withholdee_data, colWidths=[2*inch, 3*inch])
                withholdee_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), thai_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), thai_font),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                story.append(withholdee_table)
                story.append(Spacer(1, 20))
                
                # Add income and tax information
                story.append(Paragraph("รายละเอียดเงินได้และภาษี", subtitle_style))
                
                income_data = [
                    ['ประเภทเงินได้', 'จำนวนเงิน', 'ภาษีที่หัก'],
                    ['เงินเดือน/ค่าจ้าง', f"฿{data.get('income_type_1_amount', 0):,.2f}", f"฿{data.get('income_type_1_tax', 0):,.2f}"],
                    ['ค่าธรรมเนียม/ค่าสินค้า', f"฿{data.get('income_type_2_amount', 0):,.2f}", f"฿{data.get('income_type_2_tax', 0):,.2f}"],
                    ['ดอกเบี้ย', f"฿{data.get('income_type_3_amount', 0):,.2f}", f"฿{data.get('income_type_3_tax', 0):,.2f}"],
                    ['เงินปันผล (ก)', f"฿{data.get('income_type_4a_amount', 0):,.2f}", f"฿{data.get('income_type_4a_tax', 0):,.2f}"],
                    ['เงินปันผล (ข)', f"฿{data.get('income_type_4b_amount', 0):,.2f}", f"฿{data.get('income_type_4b_tax', 0):,.2f}"],
                    ['ค่าลิขสิทธิ์', f"฿{data.get('income_type_5_amount', 0):,.2f}", f"฿{data.get('income_type_5_tax', 0):,.2f}"],
                    ['อื่นๆ', f"฿{data.get('income_type_6_amount', 0):,.2f}", f"฿{data.get('income_type_6_tax', 0):,.2f}"],
                    ['รวม', f"฿{data.get('total_income', 0):,.2f}", f"฿{data.get('total_tax_withheld', 0):,.2f}"]
                ]
                
                income_table = Table(income_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
                income_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), thai_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), thai_font),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]))
                
                story.append(income_table)
                story.append(Spacer(1, 20))
                
                # Add additional information
                story.append(Paragraph("ข้อมูลเพิ่มเติม", subtitle_style))
                
                additional_data = [
                    ['รายการ', 'ข้อมูล'],
                    ['เลขที่หนังสือรับรอง', data.get('certificate_book_no', '')],
                    ['เลขที่ใบรับรอง', data.get('certificate_no', '')],
                    ['ลำดับในแบบฟอร์ม', str(data.get('sequence_in_form', ''))],
                    ['ประเภทแบบฟอร์ม', data.get('form_type', '')],
                    ['วันที่ออก', str(data.get('issue_date', ''))],
                    ['ชื่อผู้ลงนาม', data.get('signatory_name', '')],
                    ['มีตราประทับ', 'ใช่' if data.get('company_seal', False) else 'ไม่']
                ]
                
                additional_table = Table(additional_data, colWidths=[2*inch, 3*inch])
                additional_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), thai_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), thai_font),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                story.append(additional_table)
                
                # Build PDF
                doc.build(story)
                
                return True, f"PDF ถูกสร้างเรียบร้อยแล้ว: {output_path}"
                
            except Exception as e:
                return False, f"เกิดข้อผิดพลาด: {str(e)}"
            self.connection_string = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
        
        def get_connection(self):
            try:
                conn = psycopg2.connect(self.connection_string)
                return conn
            except Exception as e:
                print(f"Database connection error: {e}")
                return None
        
        def init_database(self):
            conn = self.get_connection()
            if not conn:
                return False
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tax_withholding_certificates (
                        id SERIAL PRIMARY KEY,
                        withholder_name VARCHAR(255) NOT NULL,
                        withholder_address TEXT NOT NULL,
                        withholder_tax_id VARCHAR(13) NOT NULL,
                        withholder_type VARCHAR(50) NOT NULL,
                        withholdee_name VARCHAR(255) NOT NULL,
                        withholdee_address TEXT NOT NULL,
                        withholdee_tax_id VARCHAR(13) NOT NULL,
                        withholdee_type VARCHAR(50) NOT NULL,
                        certificate_book_no VARCHAR(50),
                        certificate_no VARCHAR(50),
                        sequence_in_form INTEGER,
                        form_type VARCHAR(20),
                        income_type_1_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_1_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_2_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_2_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_3_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_3_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_4a_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_4a_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_4b_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_4b_tax DECIMAL(15,2) DEFAULT 0,
                        dividend_credit_type VARCHAR(100),
                        dividend_tax_rate DECIMAL(5,2),
                        income_type_5_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_5_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_6_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_6_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_6_description TEXT,
                        total_income DECIMAL(15,2) DEFAULT 0,
                        total_tax_withheld DECIMAL(15,2) DEFAULT 0,
                        total_tax_withheld_text TEXT,
                        provident_fund DECIMAL(15,2) DEFAULT 0,
                        social_security_fund DECIMAL(15,2) DEFAULT 0,
                        retirement_mutual_fund DECIMAL(15,2) DEFAULT 0,
                        issue_type VARCHAR(50),
                        issue_type_other VARCHAR(100),
                        issue_date DATE,
                        signatory_name VARCHAR(255),
                        company_seal BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                ''')
                conn.commit()
                return True
            except Exception as e:
                print(f"Database initialization error: {e}")
                conn.rollback()
                return False
            finally:
                cursor.close()
                conn.close()
        
        def save_certificate(self, data):
            conn = self.get_connection()
            if not conn:
                return None
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tax_withholding_certificates (
                        withholder_name, withholder_address, withholder_tax_id, withholder_type,
                        withholdee_name, withholdee_address, withholdee_tax_id, withholdee_type,
                        certificate_book_no, certificate_no, sequence_in_form, form_type,
                        income_type_1_amount, income_type_1_tax,
                        income_type_2_amount, income_type_2_tax,
                        income_type_3_amount, income_type_3_tax,
                        income_type_4a_amount, income_type_4a_tax,
                        income_type_4b_amount, income_type_4b_tax, dividend_credit_type, dividend_tax_rate,
                        income_type_5_amount, income_type_5_tax,
                        income_type_6_amount, income_type_6_tax, income_type_6_description,
                        total_income, total_tax_withheld, total_tax_withheld_text,
                        provident_fund, social_security_fund, retirement_mutual_fund,
                        issue_type, issue_type_other, issue_date, signatory_name, company_seal
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                ''', data)
                certificate_id = cursor.fetchone()[0]
                conn.commit()
                return certificate_id
            except Exception as e:
                print(f"Save certificate error: {e}")
                conn.rollback()
                return None
            finally:
                cursor.close()
                conn.close()
        
        def get_all_certificates(self):
            conn = self.get_connection()
            if not conn:
                return []
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, withholder_name, withholdee_name, total_income, 
                           total_tax_withheld, issue_date, created_at
                    FROM tax_withholding_certificates
                    ORDER BY created_at DESC
                    LIMIT 100;
                ''')
                return cursor.fetchall()
            except Exception as e:
                print(f"Get certificates error: {e}")
                return []
            finally:
                cursor.close()
                conn.close()
        
        def get_statistics(self):
            conn = self.get_connection()
            if not conn:
                return (0, 0, 0, 0, 0)
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) as total_certificates,
                           COALESCE(SUM(total_income), 0) as total_income_sum,
                           COALESCE(SUM(total_tax_withheld), 0) as total_tax_sum,
                           COUNT(DISTINCT withholder_tax_id) as unique_withholders,
                           COUNT(DISTINCT withholdee_tax_id) as unique_withholdees
                    FROM tax_withholding_certificates;
                ''')
                stats = cursor.fetchone()
                return stats if stats else (0, 0, 0, 0, 0)
            except Exception as e:
                print(f"Get statistics error: {e}")
                return (0, 0, 0, 0, 0)
            finally:
                cursor.close()
                conn.close()
        
        def get_certificate_by_id(self, certificate_id):
            conn = self.get_connection()
            if not conn:
                return None
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tax_withholding_certificates WHERE id = %s", (certificate_id,))
                result = cursor.fetchone()
                if result:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'tax_withholding_certificates' 
                        ORDER BY ordinal_position
                    """)
                    columns = [row[0] for row in cursor.fetchall()]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                print(f"Get certificate error: {e}")
                return None
            finally:
                cursor.close()
                conn.close()
        
        def generate_pdf_certificate(self, data, output_path):
            return True, f"PDF generated: {output_path}"
        def __init__(self):
            self.connection_string = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
            self.init_database()
            
        def get_connection(self):
            try:
                return psycopg2.connect(self.connection_string)
            except Exception as e:
                print(f"Database connection error: {e}")
                return None
        
        def init_database(self):
            conn = self.get_connection()
            if not conn:
                return False
                
            try:
                cursor = conn.cursor()
                
                # Create table for tax withholding certificates
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tax_withholding_certificates (
                        id SERIAL PRIMARY KEY,
                        withholder_name VARCHAR(255) NOT NULL,
                        withholder_address TEXT NOT NULL,
                        withholder_tax_id VARCHAR(13) NOT NULL,
                        withholder_type VARCHAR(50) NOT NULL,
                        withholdee_name VARCHAR(255) NOT NULL,
                        withholdee_address TEXT NOT NULL,
                        withholdee_tax_id VARCHAR(13) NOT NULL,
                        withholdee_type VARCHAR(50) NOT NULL,
                        certificate_book_no VARCHAR(50),
                        certificate_no VARCHAR(50),
                        sequence_in_form INTEGER,
                        form_type VARCHAR(20),
                        income_type_1_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_1_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_2_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_2_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_3_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_3_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_4a_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_4a_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_4b_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_4b_tax DECIMAL(15,2) DEFAULT 0,
                        dividend_credit_type VARCHAR(100),
                        dividend_tax_rate DECIMAL(5,2),
                        income_type_5_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_5_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_6_amount DECIMAL(15,2) DEFAULT 0,
                        income_type_6_tax DECIMAL(15,2) DEFAULT 0,
                        income_type_6_description TEXT,
                        total_income DECIMAL(15,2) DEFAULT 0,
                        total_tax_withheld DECIMAL(15,2) DEFAULT 0,
                        total_tax_withheld_text TEXT,
                        provident_fund DECIMAL(15,2) DEFAULT 0,
                        social_security_fund DECIMAL(15,2) DEFAULT 0,
                        retirement_mutual_fund DECIMAL(15,2) DEFAULT 0,
                        issue_type VARCHAR(50),
                        issue_type_other VARCHAR(100),
                        issue_date DATE,
                        signatory_name VARCHAR(255),
                        company_seal BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                ''')
                
                conn.commit()
                return True
                
            except Exception as e:
                print(f"Database initialization error: {e}")
                conn.rollback()
                return False
            finally:
                cursor.close()
                conn.close()
        
        def save_certificate(self, data):
            conn = self.get_connection()
            if not conn:
                return None
                
            try:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO tax_withholding_certificates (
                        withholder_name, withholder_address, withholder_tax_id, withholder_type,
                        withholdee_name, withholdee_address, withholdee_tax_id, withholdee_type,
                        certificate_book_no, certificate_no, sequence_in_form, form_type,
                        income_type_1_amount, income_type_1_tax,
                        income_type_2_amount, income_type_2_tax,
                        income_type_3_amount, income_type_3_tax,
                        income_type_4a_amount, income_type_4a_tax,
                        income_type_4b_amount, income_type_4b_tax, dividend_credit_type, dividend_tax_rate,
                        income_type_5_amount, income_type_5_tax,
                        income_type_6_amount, income_type_6_tax, income_type_6_description,
                        total_income, total_tax_withheld, total_tax_withheld_text,
                        provident_fund, social_security_fund, retirement_mutual_fund,
                        issue_type, issue_type_other, issue_date, signatory_name, company_seal
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                ''', data)
                
                certificate_id = cursor.fetchone()[0]
                conn.commit()
                return certificate_id
                
            except Exception as e:
                print(f"Save certificate error: {e}")
                conn.rollback()
                return None
            finally:
                cursor.close()
                conn.close()
        
        def get_all_certificates(self):
            conn = self.get_connection()
            if not conn:
                return []
                
            try:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, withholder_name, withholdee_name, total_income, 
                           total_tax_withheld, issue_date, created_at
                    FROM tax_withholding_certificates
                    ORDER BY created_at DESC
                    LIMIT 100;
                ''')
                
                certificates = cursor.fetchall()
                return certificates
                
            except Exception as e:
                print(f"Get certificates error: {e}")
                return []
            finally:
                cursor.close()
                conn.close()
        
        def get_statistics(self):
            conn = self.get_connection()
            if not conn:
                return (0, 0, 0, 0, 0)
                
            try:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_certificates,
                        COALESCE(SUM(total_income), 0) as total_income_sum,
                        COALESCE(SUM(total_tax_withheld), 0) as total_tax_sum,
                        COUNT(DISTINCT withholder_tax_id) as unique_withholders,
                        COUNT(DISTINCT withholdee_tax_id) as unique_withholdees
                    FROM tax_withholding_certificates
                    WHERE total_income > 0 OR total_tax_withheld > 0;
                ''')
                
                stats = cursor.fetchone()
                return stats if stats else (0, 0, 0, 0, 0)
                
            except Exception as e:
                print(f"Get statistics error: {e}")
                return (0, 0, 0, 0, 0)
            finally:
                cursor.close()
                conn.close()

# Set locale for Thai language support
try:
    locale.setlocale(locale.LC_ALL, 'th_TH.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Thai_Thailand.UTF-8')
    except:
        pass  # Use default locale if Thai locale not available

class TransferRecordsApp:
    def __init__(self):
        self.connection_string = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
        self.init_database()
        self.load_sample_data()
        # Attempt to auto-sync from external source table on first run (limited to 12 records)
        try:
            self.sync_from_source_table_on_start(limit=12)
        except Exception:
            pass
        
    def get_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(self.connection_string)
        
    def init_database(self):
        """Initialize PostgreSQL database and create table if not exists"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create table for transfer records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transfer_records (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                surname VARCHAR(255) NOT NULL,
                transfer_amount DECIMAL(15,2) NOT NULL,
                transfer_date VARCHAR(50) NOT NULL,
                id_card VARCHAR(20) NOT NULL,
                address TEXT NOT NULL,
                percent DECIMAL(5,2) NOT NULL,
                total_amount DECIMAL(15,2) NOT NULL,
                fee DECIMAL(15,2) NOT NULL,
                net_amount DECIMAL(15,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Ensure optional columns exist
        try:
            cursor.execute("ALTER TABLE IF NOT EXISTS transfer_records ADD COLUMN IF NOT EXISTS remark TEXT;")
        except Exception:
            pass
        
        conn.commit()
        conn.close()

    def _table_exists(self, cursor, table_name: str) -> bool:
        try:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name=%s)", (table_name,))
            row = cursor.fetchone()
            return bool(row and row[0])
        except Exception:
            return False

    def sync_from_source_table_on_start(self, limit: int = 12):
        """On app start: clear current transfer_records and pull up to 'limit' rows from 'tansfer_records' if it exists.
        Fallback: if 'tansfer_records' does not exist or fails, do nothing.
        """
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            if not self._table_exists(cur, 'tansfer_records'):
                return False, "no source table", 0

            # Try to select basic columns; if fails, stop gracefully
            try:
                cur.execute(
                    """
                    SELECT name, surname, transfer_amount, transfer_date, id_card, address, percent, remark
                    FROM tansfer_records
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,)
                )
                rows = cur.fetchall()
                has_remark = True
            except Exception:
                try:
                    cur.execute(
                        """
                        SELECT name, surname, transfer_amount, transfer_date, id_card, address, percent
                        FROM tansfer_records
                        ORDER BY 1 DESC
                        LIMIT %s
                        """,
                        (limit,)
                    )
                    rows = cur.fetchall()
                    has_remark = False
                except Exception:
                    return False, "cannot read source table", 0

            # Clear destination table
            try:
                cur.execute("TRUNCATE TABLE transfer_records RESTART IDENTITY;")
            except Exception:
                cur.execute("DELETE FROM transfer_records;")

            # Ensure remark exists on dest
            try:
                cur.execute("ALTER TABLE IF NOT EXISTS transfer_records ADD COLUMN IF NOT EXISTS remark TEXT;")
            except Exception:
                pass

            # Insert mapped rows
            inserted = 0
            for r in rows:
                try:
                    name, surname, transfer_amount, transfer_date, id_card, address, percent = r[:7]
                    remark = (r[7] if has_remark and len(r) > 7 else None)
                    total_amount = float(transfer_amount) * (1 + float(percent) / 100)
                    fee = total_amount - float(transfer_amount)
                    net_amount = float(transfer_amount)
                    cur.execute(
                        '''INSERT INTO transfer_records 
                           (name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount, remark)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                        (name, surname, float(transfer_amount), str(transfer_date), str(id_card), address, float(percent), total_amount, fee, net_amount, remark)
                    )
                    inserted += 1
                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    continue

            conn.commit()
            return True, "synced", inserted
        finally:
            try:
                cur.close(); conn.close()
            except Exception:
                pass

    def export_to_source_table(self, limit: int | None = None):
        """Save current transfer_records to 'tansfer_records' table (create if needed)."""
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            # Ensure source table exists
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS tansfer_records (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    surname VARCHAR(255) NOT NULL,
                    transfer_amount DECIMAL(15,2) NOT NULL,
                    transfer_date VARCHAR(50) NOT NULL,
                    id_card VARCHAR(20) NOT NULL,
                    address TEXT NOT NULL,
                    percent DECIMAL(5,2) NOT NULL,
                    total_amount DECIMAL(15,2) NOT NULL,
                    fee DECIMAL(15,2) NOT NULL,
                    net_amount DECIMAL(15,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    remark TEXT
                )
                '''
            )

            # Clear source
            try:
                cur.execute("TRUNCATE TABLE tansfer_records RESTART IDENTITY;")
            except Exception:
                cur.execute("DELETE FROM tansfer_records;")

            # Read from dest
            read_sql = '''SELECT name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount, created_at, remark FROM transfer_records ORDER BY created_at DESC'''
            if limit and limit > 0:
                read_sql += f" LIMIT {int(limit)}"
            cur.execute(read_sql)
            rows = cur.fetchall()

            # Insert into source
            for r in rows:
                cur.execute(
                    '''INSERT INTO tansfer_records 
                       (name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount, created_at, remark)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                    r
                )
            conn.commit()
            return True, f"saved {len(rows)} rows"
        except Exception as ex:
            try:
                conn.rollback()
            except Exception:
                pass
            return False, str(ex)
        finally:
            try:
                cur.close(); conn.close()
            except Exception:
                pass
        
    def load_sample_data(self):
        """Load sample data from PDF into database if table is empty"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM transfer_records")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Sample data from PDF
            sample_data = [
                ("วัชรินทร", "เจริญผล", 172854.00, "04/07/2025", "3800300262059", "38/135 หมู 3 ต.บอผุด อ.เกาะสมุย จ.สุราษฎรธานี", 3, 178200.00, 5346.00, 172854.00),
                ("ชนากานต", "ริตตา", 5000.00, "04/07/2025", "2400901034897", "185 หมู2 ต.กุดปลาดุก อ.ชื่นชม จ.มหาสารคาม", 3, 5154.64, 154.64, 5000.00),
                ("นัยนภนต", "ชวยเกิด", 172854.00, "04/07/2025", "3840300150137", "78หมู2 ค.ดอนสัก อ.ดอนสัก จ.สุราษฎรธานี", 3, 178200.00, 5346.00, 172854.00),
                ("บุลากร", "ลนทม", 14000.00, "05/07/2025", "1560300246831", "323 หมู4 ต.อางทอง อ.เชียงคํา จ.พะเยา", 3, 14432.99, 432.99, 14000.00),
                ("บุลากร", "ลนทม", 2000.00, "06/07/2025", "1560300246831", "323 หมู4 ต.อางทอง อ.เชียงคํา จ.พะเยา", 3, 2061.86, 61.86, 2000.00),
                ("อุทุมพร", "รัตนรักษ", 100000.00, "09/07/2025", "3840400237498", "232/3 หมู1 อมนํ้า อ.เกาะสมุย จ.สุราษฎรธานี", 3, 103092.78, 3092.78, 100000.00),
                ("อภิเชษฐ", "รัตนรักษ", 100000.00, "09/07/2025", "1849900289502", "232/3 หมู1 อมนํ้า อ.เกาะสมุย จ.สุราษฎรธานี", 3, 103092.78, 3092.78, 100000.00),
                ("ณัชชา", "เนตรวงศ", 7000.00, "11/07/2025", "1461300072037", "88 หมูที่ 7 ตศรีสมเด็จ อสมเด็จ จกาฬสินธุ", 3, 7216.49, 216.49, 7000.00),
                ("ชนากานต", "ริตตา", 6500.00, "12/07/2025", "2400901034897", "185 หมู2 ต.กุดปลาดุก อ.ชื่นชม จ.มหาสารคาม", 3, 6701.03, 201.03, 6500.00),
                ("วัชรินทร", "เจริญผล", 30000.00, "17/07/2025", "3800300262059", "38/135 หมู 3 ต.บอผุด อ.เกาะสมุย จ.สุราษฎรธานี", 3, 30927.84, 927.84, 30000.00),
                ("ชนากานต", "ริตตา", 5000.00, "22/07/2025", "2400901034897", "185 หมู2 ต.กุดปลาดุก อ.ชื่นชม จ.มหาสารคาม", 3, 5154.64, 154.64, 5000.00),
                ("ธนคล", "ทองสมสี", 40000.00, "28/07/2025", "1909802303755", "80/8 หมู4 ต.นาหมอ อนาหมอม จ.สงขลา", 3, 41237.11, 1237.11, 40000.00)
            ]
            
            cursor.executemany('''
                INSERT INTO transfer_records 
                (name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', sample_data)
            
            conn.commit()
        
        conn.close()
        
    def get_all_records(self):
        """Fetch all records from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='transfer_records' AND column_name='remark'
            """)
            has_remark = cursor.fetchone() is not None
        except Exception:
            has_remark = False

        if has_remark:
            cursor.execute('''
                SELECT id, name, surname, transfer_amount, transfer_date, id_card, address, 
                       percent, total_amount, fee, net_amount, created_at, remark
                FROM transfer_records
                ORDER BY created_at DESC
            ''')
        else:
            cursor.execute('''
                SELECT id, name, surname, transfer_amount, transfer_date, id_card, address, 
                       percent, total_amount, fee, net_amount, created_at
                FROM transfer_records
                ORDER BY created_at DESC
            ''')
        
        records = cursor.fetchall()
        conn.close()
        return records
        
    def get_statistics(self):
        """Calculate statistics from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as record_count,
                SUM(transfer_amount) as total_transfer,
                SUM(fee) as total_fees,
                SUM(net_amount) as total_net,
                SUM(total_amount) as grand_total
            FROM transfer_records
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        return stats
        
    def export_to_excel(self, file_path):
        """Export data to Excel file"""
        try:
            # Get data from database
            records = self.get_all_records()
            stats = self.get_statistics()
            
            # Create DataFrame
            columns = ['ชื่อ (Name)', 'นามสกุล (Surname)', 'จำนวนโอน (Transfer)', 
                      'วันที่ (Date)', 'เลขบัตรประชาชน (ID Card)', 'ที่อยู่ (Address)', 
                      'เปอร์เซ็นต์ (%)', 'ยอดรวม (Total)', 'ค่าธรรมเนียม (Fee)', 
                      'ยอดสุทธิ (Net)']
            
            df = pd.DataFrame(records, columns=columns)
            
            # Create Excel writer with multiple sheets
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='Transfer Records', index=False)
                
                # Summary sheet
                summary_data = {
                    'รายการ (Item)': ['จำนวนรายการทั้งหมด', 'ยอดโอนรวม', 'ค่าธรรมเนียมรวม', 'ยอดสุทธิรวม', 'ยอดเงินรวมทั้งหมด'],
                    'จำนวน (Amount)': [
                        f"{stats[0]:,} รายการ",
                        f"฿{stats[1]:,.2f}",
                        f"฿{stats[2]:,.2f}",
                        f"฿{stats[3]:,.2f}",
                        f"฿{stats[4]:,.2f}"
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Auto-adjust column widths
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            return True, f"ไฟล์ Excel ถูกสร้างเรียบร้อยแล้ว: {file_path}"
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}"
    
    def export_to_pdf(self, file_path):
        """Export data to PDF file"""
        try:
            # Get data from database
            records = self.get_all_records()
            stats = self.get_statistics()
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            story = []
            
            # Register Thai font with multiple fallback options
            thai_font = 'Helvetica'  # Default fallback
            
            # List of possible Thai fonts to try
            thai_font_paths = [
                'C:/Windows/Fonts/THSarabun.ttf',
                'C:/Windows/Fonts/THSarabunNew.ttf',
                'C:/Windows/Fonts/THSarabunPSK.ttf',
                'C:/Windows/Fonts/THSarabunNewBold.ttf',
                'C:/Windows/Fonts/THSarabunBold.ttf',
                'C:/Windows/Fonts/THSarabunItalic.ttf',
                'C:/Windows/Fonts/THSarabunNewItalic.ttf',
                'C:/Windows/Fonts/THSarabunNewBoldItalic.ttf',
                'C:/Windows/Fonts/THSarabunBoldItalic.ttf',
                # Also try Linux/Mac paths
                '/usr/share/fonts/truetype/thai/THSarabun.ttf',
                '/System/Library/Fonts/Supplemental/THSarabun.ttf',
                '/Library/Fonts/THSarabun.ttf'
            ]
            
            for font_path in thai_font_paths:
                try:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('ThaiFont', font_path))
                        thai_font = 'ThaiFont'
                        break
                except:
                    continue
            
            # If no Thai font found, try to download one
            if thai_font == 'Helvetica':
                try:
                    # Download a Thai font from Google Fonts or similar
                    font_url = "https://github.com/google/fonts/raw/main/ofl/sarabun/THSarabun-Regular.ttf"
                    temp_font_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ttf')
                    urllib.request.urlretrieve(font_url, temp_font_file.name)
                    pdfmetrics.registerFont(TTFont('ThaiFont', temp_font_file.name))
                    thai_font = 'ThaiFont'
                except:
                    pass  # Keep using Helvetica if download fails
            
            # Get styles with Thai font support
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1,  # Center alignment
                fontName=thai_font
            )
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=20,
                alignment=1,
                fontName=thai_font
            )
            normal_style = ParagraphStyle(
                'ThaiNormal',
                parent=styles['Normal'],
                fontName=thai_font,
                fontSize=10
            )
            
            # Add title
            story.append(Paragraph("รายงานข้อมูลการโอนเงิน", title_style))
            story.append(Spacer(1, 20))
            
            # Add generation date
            current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            story.append(Paragraph(f"วันที่สร้างรายงาน: {current_date}", normal_style))
            story.append(Spacer(1, 30))
            
            # Add summary statistics
            story.append(Paragraph("สรุปสถิติ", subtitle_style))
            
            summary_data = [
                ['รายการ', 'จำนวน'],
                ['จำนวนรายการทั้งหมด', f"{stats[0]:,} รายการ"],
                ['ยอดโอนรวม', f"฿{stats[1]:,.2f}"],
                ['ค่าธรรมเนียมรวม', f"฿{stats[2]:,.2f}"],
                ['ยอดสุทธิรวม', f"฿{stats[3]:,.2f}"],
                ['ยอดเงินรวมทั้งหมด', f"฿{stats[4]:,.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), thai_font),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), thai_font),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Add detailed records
            story.append(Paragraph("รายละเอียดการโอนเงิน", subtitle_style))
            
            # Prepare table data
            table_data = [['ชื่อ', 'นามสกุล', 'จำนวนโอน', 'วันที่', 'ค่าธรรมเนียม', 'ยอดสุทธิ']]
            
            for record in records:
                table_data.append([
                    record[0],  # name
                    record[1],  # surname
                    f"฿{record[2]:,.2f}",  # transfer_amount
                    record[3],  # date
                    f"฿{record[8]:,.2f}",  # fee
                    f"฿{record[9]:,.2f}"   # net_amount
                ])
            
            # Create table with appropriate column widths
            col_widths = [1.2*inch, 1.2*inch, 1*inch, 1*inch, 1*inch, 1*inch]
            data_table = Table(table_data, colWidths=col_widths)
            
            # Apply table styling
            data_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), thai_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), thai_font),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            story.append(data_table)
            
            # Build PDF
            doc.build(story)
            
            return True, f"ไฟล์ PDF ถูกสร้างเรียบร้อยแล้ว: {file_path}"
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}"

    # --- New: Import from Excel (Transfer Records) ---
    def import_from_excel(self, excel_path: str) -> Tuple[bool, str, int]:
        try:
            try:
                df = pd.read_excel(excel_path, sheet_name='Transfer Records')
            except Exception:
                df = pd.read_excel(excel_path)

            # Accept both Thai labeled columns (from our export) and raw DB-like columns
            col_map_variants = [
                {
                    'name': 'ชื่อ (Name)',
                    'surname': 'นามสกุล (Surname)',
                    'transfer_amount': 'จำนวนโอน (Transfer)',
                    'transfer_date': 'วันที่ (Date)',
                    'id_card': 'เลขบัตรประชาชน (ID Card)',
                    'address': 'ที่อยู่ (Address)',
                    'percent': 'เปอร์เซ็นต์ (%)',
                    'remark': 'หมายเหตุ'
                },
                {
                    'name': 'name',
                    'surname': 'surname',
                    'transfer_amount': 'transfer_amount',
                    'transfer_date': 'transfer_date',
                    'id_card': 'id_card',
                    'address': 'address',
                    'percent': 'percent',
                    'remark': 'remark'
                }
            ]

            used_map = None
            for cmap in col_map_variants:
                if all(col in df.columns for col in cmap.values()):
                    used_map = cmap
                    break
            if used_map is None:
                return False, 'โครงสร้างไฟล์ไม่ถูกต้อง (ไม่พบคอลัมน์ที่ต้องการ)', 0

            # Normalize rows for insert
            records: List[tuple] = []
            for _, row in df.iterrows():
                try:
                    name = str(row[used_map['name']]).strip()
                    surname = str(row[used_map['surname']]).strip()
                    transfer_amount = float(row[used_map['transfer_amount']] or 0)
                    transfer_date = str(row[used_map['transfer_date']]).strip()
                    id_card = str(row[used_map['id_card']]).strip()
                    address = str(row[used_map['address']]).strip()
                    percent = float(row[used_map['percent']] or 3.0)
                    remark = str(row.get(used_map.get('remark', ''), '')).strip() if used_map.get('remark') in df.columns else None
                    total_amount = transfer_amount * (1 + percent / 100)
                    fee = total_amount - transfer_amount
                    net_amount = transfer_amount
                    records.append((name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount, remark))
                except Exception:
                    # skip bad row
                    continue

            if not records:
                return False, 'ไม่มีข้อมูลเพื่อนำเข้า', 0

            conn = self.get_connection()
            cur = conn.cursor()
            # Ensure remark column exists
            try:
                cur.execute("ALTER TABLE IF NOT EXISTS transfer_records ADD COLUMN IF NOT EXISTS remark TEXT;")
            except Exception:
                pass
            cur.executemany(
                '''INSERT INTO transfer_records 
                   (name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount, remark)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                records
            )
            conn.commit()
            conn.close()
            return True, f"นำเข้าสำเร็จ {len(records)} รายการ", len(records)
        except Exception as ex:
            return False, f"นำเข้าไม่สำเร็จ: {ex}", 0

    def reset_from_excel(self, excel_path: str) -> Tuple[bool, str, int]:
        try:
            try:
                df = pd.read_excel(excel_path, sheet_name='Transfer Records')
            except Exception:
                df = pd.read_excel(excel_path)

            col_map_variants = [
                {
                    'name': 'ชื่อ (Name)',
                    'surname': 'นามสกุล (Surname)',
                    'transfer_amount': 'จำนวนโอน (Transfer)',
                    'transfer_date': 'วันที่ (Date)',
                    'id_card': 'เลขบัตรประชาชน (ID Card)',
                    'address': 'ที่อยู่ (Address)',
                    'percent': 'เปอร์เซ็นต์ (%)',
                    'remark': 'หมายเหตุ'
                },
                {
                    'name': 'name',
                    'surname': 'surname',
                    'transfer_amount': 'transfer_amount',
                    'transfer_date': 'transfer_date',
                    'id_card': 'id_card',
                    'address': 'address',
                    'percent': 'percent',
                    'remark': 'remark'
                }
            ]

            used_map = None
            for cmap in col_map_variants:
                if all(col in df.columns for col in [cmap['name'], cmap['surname'], cmap['transfer_amount'], cmap['transfer_date'], cmap['id_card'], cmap['address'], cmap['percent']]):
                    used_map = cmap
                    break
            if used_map is None:
                return False, 'โครงสร้างไฟล์ไม่ถูกต้อง (ไม่พบคอลัมน์ที่ต้องการ)', 0

            records: List[tuple] = []
            for _, row in df.iterrows():
                try:
                    name = str(row[used_map['name']]).strip()
                    surname = str(row[used_map['surname']]).strip()
                    transfer_amount = float(row[used_map['transfer_amount']] or 0)
                    transfer_date = str(row[used_map['transfer_date']]).strip()
                    id_card = str(row[used_map['id_card']]).strip()
                    address = str(row[used_map['address']]).strip()
                    percent = float(row[used_map['percent']] or 3.0)
                    remark = str(row.get(used_map.get('remark', ''), '')).strip() if used_map.get('remark') in df.columns else None
                    total_amount = transfer_amount * (1 + percent / 100)
                    fee = total_amount - transfer_amount
                    net_amount = transfer_amount
                    records.append((name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount, remark))
                except Exception:
                    continue

            conn = self.get_connection()
            cur = conn.cursor()
            try:
                cur.execute("TRUNCATE TABLE transfer_records RESTART IDENTITY;")
            except Exception:
                cur.execute("DELETE FROM transfer_records;")
            try:
                cur.execute("ALTER TABLE IF NOT EXISTS transfer_records ADD COLUMN IF NOT EXISTS remark TEXT;")
            except Exception:
                pass
            if records:
                cur.executemany(
                    '''INSERT INTO transfer_records 
                       (name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount, remark)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                    records
                )
            conn.commit(); conn.close()
            return True, f"รีเซ็ตและนำเข้า {len(records)} รายการ", len(records)
        except Exception as ex:
            return False, f"รีเซ็ตไม่สำเร็จ: {ex}", 0

    # --- New: Backup to local SQLite (backup.db) ---
    def backup_to_sqlite(self, sqlite_path: str = 'backup.db') -> Tuple[bool, str, int]:
        try:
            # Prepare SQLite
            if os.path.exists(sqlite_path):
                os.remove(sqlite_path)
            sconn = sqlite3.connect(sqlite_path)
            s = sconn.cursor()
            s.execute('''
                CREATE TABLE IF NOT EXISTS transfer_records (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    surname TEXT NOT NULL,
                    transfer_amount REAL NOT NULL,
                    transfer_date TEXT NOT NULL,
                    id_card TEXT NOT NULL,
                    address TEXT NOT NULL,
                    percent REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    fee REAL NOT NULL,
                    net_amount REAL NOT NULL,
                    created_at TEXT
                )
            ''')

            # Read from Neon
            records = self.get_all_records()
            # Normalize types for SQLite (convert Decimal/date/datetime)
            try:
                import datetime as _dt
                from decimal import Decimal as _Dec
                def _norm(val):
                    if isinstance(val, _Dec):
                        return float(val)
                    if isinstance(val, (_dt.date, _dt.datetime)):
                        return val.isoformat()
                    return val
                normalized_records = [tuple(_norm(v) for v in rec) for rec in records]
            except Exception:
                normalized_records = records
            if normalized_records:
                placeholders = ','.join(['?'] * 12)
                s.executemany(f'INSERT INTO transfer_records VALUES ({placeholders})', normalized_records)
            sconn.commit(); s.close(); sconn.close()
            return True, f"บันทึกสำรองไว้ที่ {os.path.abspath(sqlite_path)}", len(records)
        except Exception as ex:
            return False, f"สำรองข้อมูลไม่สำเร็จ: {ex}", 0
    
    def add_record(self, name, surname, transfer_amount, transfer_date, id_card, address, percent, remark=None):
        """Add a new record to database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Calculate derived values
            total_amount = transfer_amount * (1 + percent / 100)
            fee = total_amount - transfer_amount
            net_amount = transfer_amount
            
            try:
                cursor.execute("ALTER TABLE IF NOT EXISTS transfer_records ADD COLUMN IF NOT EXISTS remark TEXT;")
            except Exception:
                pass
            cursor.execute('''
                INSERT INTO transfer_records 
                (name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount, remark)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount, remark))
            
            conn.commit()
            conn.close()
            
            return True, "เพิ่มข้อมูลเรียบร้อยแล้ว"
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}"
    
    def update_record(self, record_id, name, surname, transfer_amount, transfer_date, id_card, address, percent, remark=None):
        """Update an existing record"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Calculate derived values
            total_amount = transfer_amount * (1 + percent / 100)
            fee = total_amount - transfer_amount
            net_amount = transfer_amount
            
            cursor.execute('''
                UPDATE transfer_records 
                SET name = %s, surname = %s, transfer_amount = %s, transfer_date = %s, 
                    id_card = %s, address = %s, percent = %s, total_amount = %s, 
                    fee = %s, net_amount = %s, remark = %s
                WHERE id = %s
            ''', (name, surname, transfer_amount, transfer_date, id_card, address, 
                  percent, total_amount, fee, net_amount, remark, record_id))
            
            conn.commit()
            conn.close()
            
            return True, "อัปเดตข้อมูลเรียบร้อยแล้ว"
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}"
    
    def delete_record(self, record_id):
        """Delete a record from database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM transfer_records WHERE id = %s', (record_id,))
            
            conn.commit()
            conn.close()
            
            return True, "ลบข้อมูลเรียบร้อยแล้ว"
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}"
    
    def get_record_by_id(self, record_id):
        """Get a specific record by ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, surname, transfer_amount, transfer_date, id_card, address, 
                       percent, total_amount, fee, net_amount, remark
                FROM transfer_records
                WHERE id = %s
            ''', (record_id,))
            
            record = cursor.fetchone()
            conn.close()
            
            return record
            
        except Exception as e:
            return None

def main(page: ft.Page):
    page.title = "Transfer Records Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1400
    page.window_height = 900
    page.window_resizable = True
    
    # Initialize app
    app = TransferRecordsApp()
    
    # On first load: auto-fill dashboard data from source table (limit 12)
    try:
        app.sync_from_source_table_on_start(limit=12)
    except Exception:
        pass

    # Get initial statistics (after sync)
    stats = app.get_statistics()
    
    # Status text
    status_text = ft.Text(
        "พร้อมใช้งาน",
        size=14,
        color=ft.Colors.GREEN_700
    )
    
    # Input fields for CRUD operations
    name_input = ft.TextField(
        label="ชื่อ",
        hint_text="กรอกชื่อ",
        width=200
    )
    
    surname_input = ft.TextField(
        label="นามสกุล",
        hint_text="กรอกนามสกุล",
        width=200
    )
    
    transfer_amount_input = ft.TextField(
        label="จำนวนโอน",
        hint_text="กรอกจำนวนเงิน",
        width=200
    )
    
    transfer_date_input = ft.TextField(
        label="วันที่",
        hint_text="dd/mm/yyyy",
        width=200
    )
    
    id_card_input = ft.TextField(
        label="เลขบัตรประชาชน",
        hint_text="กรอกเลขบัตรประชาชน",
        width=200
    )
    
    address_input = ft.TextField(
        label="ที่อยู่",
        hint_text="กรอกที่อยู่",
        width=400
    )
    
    percent_input = ft.TextField(
        label="เปอร์เซ็นต์",
        hint_text="กรอกเปอร์เซ็นต์",
        width=200
    )
    
    # Remark input (used in dashboard quick edit panel)
    remark_input = ft.TextField(
        label="หมายเหตุ",
        hint_text="ระบุหมายเหตุ (ถ้ามี)",
        width=300
    )
    
    record_id_input = ft.TextField(
        label="ID รายการ",
        hint_text="กรอก ID สำหรับแก้ไข/ลบ",
        width=200
    )
    
    # Statistics cards
    stats_cards = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Text("จำนวนรายการ", size=12, weight=ft.FontWeight.BOLD),
                ft.Text(f"{stats[0]:,}", size=20, color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
            padding=15,
            expand=True
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("ยอดโอนรวม", size=12, weight=ft.FontWeight.BOLD),
                ft.Text(f"฿{stats[1]:,.2f}", size=16, color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.GREEN_50,
            border_radius=10,
            padding=15,
            expand=True
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("ค่าธรรมเนียม", size=12, weight=ft.FontWeight.BOLD),
                ft.Text(f"฿{stats[2]:,.2f}", size=16, color=ft.Colors.ORANGE_700, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.ORANGE_50,
            border_radius=10,
            padding=15,
            expand=True
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("ยอดสุทธิ", size=12, weight=ft.FontWeight.BOLD),
                ft.Text(f"฿{stats[3]:,.2f}", size=16, color=ft.Colors.PURPLE_700, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.PURPLE_50,
            border_radius=10,
            padding=15,
            expand=True
        )
    ], spacing=10)
    
    # Data table
    def create_data_table():
        records = app.get_all_records()
        
        # Show first 10 records in preview
        preview_records = records[:10]
        
        columns = [
            ft.DataColumn(ft.Text("ชื่อ", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("นามสกุล", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("จำนวนโอน", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("วันที่", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("ค่าธรรมเนียม", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("ยอดสุทธิ", weight=ft.FontWeight.BOLD))
        ]
        
        rows = []
        for record in preview_records:
            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(record[1])),  # name
                    ft.DataCell(ft.Text(record[2])),  # surname
                    ft.DataCell(ft.Text(f"฿{record[3]:,.2f}")),  # transfer_amount
                    ft.DataCell(ft.Text(record[4])),  # date
                    ft.DataCell(ft.Text(f"฿{record[9]:,.2f}")),  # fee
                    ft.DataCell(ft.Text(f"฿{record[10]:,.2f}"))   # net_amount
                ])
            )
        
        if len(records) > 10:
            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text("...", style=ft.TextStyle(italic=True))),
                    ft.DataCell(ft.Text(f"และอีก {len(records)-10} รายการ", style=ft.TextStyle(italic=True))),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text(""))
                ])
            )
        
        return ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            column_spacing=20,
            heading_row_height=50,
            data_row_min_height=40,
            data_row_max_height=50,
            divider_thickness=1,
            show_bottom_border=True,
            show_checkbox_column=False
        )
    
    # State for dashboard selection → PDF fill
    row_checkboxes = {}
    selected_transfer_id_for_pdf = None

    def sync_transfer_remarks_from_excel_on_start():
        """Load 'remark' values from Excel into Neon DB at app start.
        Tries multiple common paths and handles absence gracefully.
        Expected Excel columns: at least 'id' and 'remark'. Other columns are ignored.
        """
        try:
            import pandas as pd
            import psycopg2
            # Candidate paths (handle typos and folder variants)
            candidates = [
                r"C:\\program_tax\\transfer_records_update.xlsx",
                r"C:\\program_tax\\transfer_records_update.xslx",
                r"C:\\program_tax\\transfer_record_update_xslx\\transfer_records_update.xlsx",
                r"C:\\program_tax\\transfer_record_update_xslx\\transfer_records_update.xslx",
            ]
            excel_path = None
            import os
            for p in candidates:
                if os.path.exists(p):
                    excel_path = p
                    break
            if not excel_path:
                return  # No file found → skip silently

            # Read excel
            try:
                df = pd.read_excel(excel_path)
            except Exception:
                return
            if df is None or df.empty:
                return
            # Normalize columns to str lower
            df.columns = [str(c).strip() for c in df.columns]
            cols = {c.lower(): c for c in df.columns}
            if 'id' not in cols or 'remark' not in cols:
                return  # cannot map without id/remark
            id_col = cols['id']
            remark_col = cols['remark']

            # Prepare updates
            updates = []
            for _, row in df.iterrows():
                rec_id = row.get(id_col)
                remark_val = row.get(remark_col)
                if rec_id is None:
                    continue
                # Only update when remark has a non-empty value
                if remark_val is None or str(remark_val).strip() == "":
                    continue
                try:
                    updates.append((str(remark_val), int(rec_id)))
                except Exception:
                    continue
            if not updates:
                return

            # Update Neon DB
            conn_str = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
            with psycopg2.connect(conn_str) as conn:
                with conn.cursor() as cur:
                    # Ensure column exists
                    cur.execute("ALTER TABLE IF NOT EXISTS transfer_records ADD COLUMN IF NOT EXISTS remark TEXT;")
                    # Batch update
                    for remark_val, rec_id in updates:
                        try:
                            cur.execute("UPDATE transfer_records SET remark=%s WHERE id=%s", (remark_val, rec_id))
                        except Exception:
                            try:
                                conn.rollback()
                            except Exception:
                                pass
                            continue
                    conn.commit()
        except Exception:
            # Fail silently to not break app startup
            pass

    # Run remark sync before building grids
    sync_transfer_remarks_from_excel_on_start()

    # Full data grid
    def create_full_data_grid():
        global selected_transfer_id_for_pdf
        nonlocal row_checkboxes
        records = app.get_all_records()

        def update_remark(rec_id: int, new_value) -> bool:
            try:
                import psycopg2
                conn_str = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
                with psycopg2.connect(conn_str) as conn:
                    with conn.cursor() as cur:
                        try:
                            cur.execute("ALTER TABLE IF NOT EXISTS transfer_records ADD COLUMN IF NOT EXISTS remark TEXT;")
                            cur.execute("UPDATE transfer_records SET remark=%s WHERE id=%s", (new_value, rec_id))
                            conn.commit()
                            return True
                        except Exception:
                            try:
                                conn.rollback()
                            except Exception:
                                pass
                            return False
            except Exception:
                return False

        def fetch_remark_by_id(rec_id: int) -> str:
            try:
                import psycopg2
                conn_str = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
                with psycopg2.connect(conn_str) as conn:
                    with conn.cursor() as cur:
                        try:
                            cur.execute("SELECT remark FROM transfer_records WHERE id=%s", (rec_id,))
                            row = cur.fetchone()
                            return str(row[0]) if row and row[0] is not None else ""
                        except Exception:
                            try:
                                conn.rollback()
                            except Exception:
                                pass
                            return ""
            except Exception:
                return ""
        
        columns = [
            ft.DataColumn(ft.Text("เลือก", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("ID", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("ชื่อ", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("นามสกุล", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("จำนวนโอน", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("วันที่โอน", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("เลขบัตรประชาชน", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("ที่อยู่", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("เปอร์เซ็นต์", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("ยอดรวม", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("ค่าธรรมเนียม", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("ยอดสุทธิ", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("หมายเหตุ", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("วันที่สร้าง", weight=ft.FontWeight.BOLD))
        ]
        
        rows = []
        row_checkboxes.clear()
        def make_on_change(rec_id: int):
            def _handler(e):
                global selected_transfer_id_for_pdf
                # Uncheck all others
                for rid, c in row_checkboxes.items():
                    if rid != rec_id and c.value:
                        c.value = False
                # Set selected id if checked, else clear
                selected_transfer_id_for_pdf = rec_id if e.control.value else None
                try:
                    page.update()
                except Exception:
                    pass
            return _handler

        def make_remark_toggle():
            def _handler(e: ft.ControlEvent):
                try:
                    meta = e.control.data or {}
                    rec_id = int(meta.get("rec_id"))
                    current_text = str(meta.get("remark") or "")
                    # Determine new value: check sets default remark if empty; uncheck clears remark
                    if bool(e.control.value):
                        new_val = current_text if current_text.strip() else "หมายเหตุ"
                    else:
                        new_val = None
                    if update_remark(rec_id, new_val):
                        e.control.tooltip = new_val or ""
                        # store back current value for subsequent toggles
                        e.control.data = {"rec_id": rec_id, "remark": new_val or ""}
                        try:
                            page.update()
                        except Exception:
                            pass
                except Exception:
                    pass
            return _handler

        for record in records:
            cb = ft.Checkbox(value=False, on_change=make_on_change(record[0]))
            row_checkboxes[record[0]] = cb
            # Resolve remark text from record tuple or fallback DB fetch
            remark_text = ""
            try:
                # remark exists when len(record) > 12 (index 12)
                remark_text = str(record[12]) if len(record) > 12 and record[12] is not None else ""
            except Exception:
                remark_text = ""
            if not remark_text:
                try:
                    remark_text = fetch_remark_by_id(int(record[0]))
                except Exception:
                    remark_text = ""

            cells = [
                ft.DataCell(cb),
                ft.DataCell(ft.Text(str(record[0]))),  # id
                ft.DataCell(ft.Text(record[1])),  # name
                ft.DataCell(ft.Text(record[2])),  # surname
                ft.DataCell(ft.Text(f"฿{record[3]:,.2f}")),  # transfer_amount
                ft.DataCell(ft.Text(record[4])),  # transfer_date
                ft.DataCell(ft.Text(record[5])),  # id_card
                ft.DataCell(ft.Text(record[6])),  # address
                ft.DataCell(ft.Text(f"{record[7]}%")),  # percent
                ft.DataCell(ft.Text(f"฿{record[8]:,.2f}")),  # total_amount
                ft.DataCell(ft.Text(f"฿{record[9]:,.2f}")),  # fee
                ft.DataCell(ft.Text(f"฿{record[10]:,.2f}")), # net_amount
            ]
            # remark checkbox cell
            cells.append(
                ft.DataCell(
                    ft.Checkbox(
                        value=bool((remark_text or "").strip()),
                        tooltip=remark_text or "",
                        data={"rec_id": int(record[0]), "remark": remark_text or ""},
                        on_change=make_remark_toggle()
                    )
                )
            )
            # created_at exists at index 11 if remark not selected; handle safely
            created_at_val = ""
            try:
                created_at_val = record[11].strftime("%d/%m/%Y %H:%M") if record[11] else ""
            except Exception:
                created_at_val = ""
            cells.append(ft.DataCell(ft.Text(created_at_val)))

            rows.append(ft.DataRow(cells=cells))
        
        dt = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            column_spacing=15,
            heading_row_height=50,
            data_row_min_height=40,
            data_row_max_height=50,
            divider_thickness=1,
            show_bottom_border=True,
            show_checkbox_column=False
        )
        # Wrap in horizontal scroll container so wide tables can be scrolled sideways
        return ft.Container(
            content=ft.Row([dt], scroll=ft.ScrollMode.AUTO),
            expand=True
        )
    
    # Initialize data tables
    data_table = create_data_table()
    full_data_grid = create_full_data_grid()
    
    # --- New Tabs: Import from Excel & Backup ---
    def create_import_excel_tab():
        import_status = ft.Text("", size=12)

        grid = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("ชื่อ")),
                ft.DataColumn(ft.Text("นามสกุล")),
                ft.DataColumn(ft.Text("จำนวนโอน")),
                ft.DataColumn(ft.Text("วันที่")),
                ft.DataColumn(ft.Text("สุทธิ")),
            ],
            rows=[],
            column_spacing=12,
        )

        def refresh_grid():
            rows = app.get_all_records()
            grid.rows = [
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(r[0]))),
                    ft.DataCell(ft.Text(r[1])),
                    ft.DataCell(ft.Text(r[2])),
                    ft.DataCell(ft.Text(f"฿{float(r[3]):,.2f}")),
                    ft.DataCell(ft.Text(r[4])),
                    ft.DataCell(ft.Text(f"฿{float(r[10]):,.2f}")),
                ]) for r in rows
            ]
            page.update()

        def pick_and_import(e):
            def on_res(res: ft.FilePickerResultEvent):
                if res.files:
                    ok, msg, count = app.import_from_excel(res.files[0].path)
                    import_status.value = ("✅ " if ok else "❌ ") + msg
                    import_status.color = ft.Colors.GREEN_700 if ok else ft.Colors.RED_700
                    # Also export current data to source table so next startup auto-fills from it
                    try:
                        sok, smsg = app.export_to_source_table()
                        if sok:
                            import_status.value += f" | บันทึกลงตารางต้นทางแล้ว"
                    except Exception:
                        pass
                    refresh_grid()
            picker = ft.FilePicker(on_result=on_res)
            page.overlay.append(picker)
            page.update()
            picker.pick_files(allowed_extensions=["xlsx"], dialog_title="เลือก transfer_records.xlsx")

        refresh_grid()

        crystal_tab = ft.Container(
            content=ft.Column([
                ft.Text("นำเข้าจาก Excel", size=22, weight=ft.FontWeight.BOLD),
                ft.Text("โครงสร้างไฟล์เหมือนกับไฟล์ที่ส่งออก (Transfer Records)", size=12),
                ft.Row([
                    ft.ElevatedButton("เลือกไฟล์และนำเข้า", icon=ft.icons.FILE_UPLOAD, on_click=pick_and_import),
                ], spacing=10),
                import_status,
                grid
            ], spacing=12),
            padding=20
        )
        return crystal_tab
    def create_backup_tab():
        backup_status = ft.Text("", size=12)
        filename = ft.TextField(label="SQLite backup filename", value="backup.db", width=260)

        def do_backup(e):
            ok, msg, count = app.backup_to_sqlite(filename.value or 'backup.db')
            backup_status.value = ("✅ " if ok else "❌ ") + msg + (f" | {count} rows" if ok else "")
            backup_status.color = ft.Colors.GREEN_700 if ok else ft.Colors.RED_700
            page.update()

        return ft.Container(
            content=ft.Column([
                ft.Text("สำรองข้อมูล", size=22, weight=ft.FontWeight.BOLD),
                ft.Text("สำรองข้อมูล transfer_records ไปยัง SQLite ภายในเครื่อง", size=12),
                ft.Row([filename, ft.ElevatedButton("เริ่มสำรองข้อมูล", icon=ft.icons.CLOUD_DOWNLOAD, on_click=do_backup)], spacing=10),
                backup_status
            ], spacing=12),
            padding=20
        )

    # New Tab: Import withholder addresses from Excel (Neon JSONB table)
    pending_withholder_import_data = None  # payload passed into crystal report tab
    def create_import_withholder_excel_tab():
        status = ft.Text("", size=12)
        info_text = ft.Text("ไฟล์ต้นทาง: C:\\program_tax\\tax_address.xlsx", size=12, color=ft.Colors.GREY_700)

        # Grid state
        current_columns: list[str] = []
        row_selection: dict[int, bool] = {}
        data_items: list[dict] = []
        data_table = ft.DataTable(columns=[], rows=[], column_spacing=12)

        DB_CONN_STR = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
        TABLE_NAME = "withholder_address_book"

        def get_conn():
            try:
                return psycopg2.connect(DB_CONN_STR)
            except Exception as ex:
                print(f"Withholder DB conn error: {ex}")
                return None

        def ensure_table():
            conn = get_conn()
            if not conn:
                return False
            try:
                cur = conn.cursor()
                
                # Create main table
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                        id SERIAL PRIMARY KEY,
                        data JSONB NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT now()
                    );
                    CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_created_at ON {TABLE_NAME}(created_at DESC);
                    """
                )
                
                # Create settings table for storing checkbox states
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS withholder_settings (
                        id SERIAL PRIMARY KEY,
                        setting_key VARCHAR(100) NOT NULL,
                        setting_value JSONB NOT NULL,
                        updated_at TIMESTAMPTZ DEFAULT now()
                    );
                    """)
                
                # Create index for settings table
                try:
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_withholder_settings_key ON withholder_settings(setting_key);")
                except Exception:
                    pass  # Index might already exist
                
                conn.commit()
                print("✅ Tables ensured successfully")
                return True
                
            except Exception as ex:
                print(f"❌ Ensure table error: {ex}")
                try:
                    conn.rollback()
                except Exception:
                    pass
                return False
            finally:
                try:
                    if 'cur' in locals():
                        cur.close()
                    if 'conn' in locals():
                        conn.close()
                except Exception:
                    pass

        def import_fixed_excel(path: str) -> tuple[bool, str, int, list[str]]:
            try:
                import pandas as pd
                if not os.path.exists(path):
                    return False, f"ไม่พบไฟล์: {path}", 0, []
                df = pd.read_excel(path)
                if df.empty:
                    return False, "ไฟล์ว่างเปล่า", 0, []
                # Normalize NaN to None
                df = df.where(pd.notnull(df), None)
                cols = list(df.columns)
                records = df.to_dict(orient="records")

                conn = get_conn()
                if not conn:
                    return False, "เชื่อมต่อฐานข้อมูลไม่สำเร็จ", 0, []
                try:
                    ensure_table()
                    from psycopg2.extras import execute_values, Json
                    cur = conn.cursor()
                    insert_sql = f"INSERT INTO {TABLE_NAME} (data) VALUES %s"
                    values = [(Json(r),) for r in records]
                    execute_values(cur, insert_sql, values)
                    conn.commit()
                    return True, f"นำเข้า {len(records)} รายการ", len(records), cols
                except Exception as ex:
                    conn.rollback()
                    return False, f"นำเข้าไม่สำเร็จ: {ex}", 0, []
                finally:
                    try:
                        cur.close(); conn.close()
                    except Exception:
                        pass
            except Exception as ex:
                return False, f"อ่าน Excel ไม่สำเร็จ: {ex}", 0, []

        def fetch_latest(limit: int = 100) -> tuple[list[str], list[dict]]:
            conn = get_conn()
            if not conn:
                return [], []
            try:
                ensure_table()
                cur = conn.cursor()
                cur.execute(f"SELECT data FROM {TABLE_NAME} ORDER BY created_at DESC, id DESC LIMIT %s", (limit,))
                rows = cur.fetchall()
                items = [r[0] for r in rows]
                # Determine columns: use keys from first row
                cols = []
                for item in items:
                    if isinstance(item, dict) and item:
                        cols = list(item.keys())
                        break
                return cols, items
            except Exception as ex:
                print(f"Fetch error: {ex}")
                return [], []
            finally:
                try:
                    cur.close(); conn.close()
                except Exception:
                    pass

        def refresh_grid():
            nonlocal current_columns
            cols, items = fetch_latest()
            # Save items to state
            nonlocal data_items, row_selection
            data_items = items
            
            # Ensure selection dict size and preserve saved states
            new_row_selection = {}
            for i in range(len(data_items)):
                # Preserve existing selection state if available
                new_row_selection[i] = row_selection.get(i, False)
            row_selection = new_row_selection
            
            if cols:
                current_columns = cols
            # Build columns
            data_table.columns = [ft.DataColumn(ft.Text("เลือก")), ft.DataColumn(ft.Text("#"))] + [ft.DataColumn(ft.Text(c)) for c in current_columns[:8]]
            # Build rows
            rows = []
            for idx, item in enumerate(data_items, start=1):
                # selection checkbox - ใช้สถานะที่บันทึกไว้
                def make_on_change(i: int):
                    return lambda e: row_selection.__setitem__(i, bool(e.control.value))
                checkbox = ft.Checkbox(value=row_selection.get(idx-1, False), on_change=make_on_change(idx-1))
                cells = [ft.DataCell(checkbox), ft.DataCell(ft.Text(str(idx)))]
                for c in current_columns[:8]:
                    v = item.get(c, "") if isinstance(item, dict) else ""
                    cells.append(ft.DataCell(ft.Text(str(v) if v is not None else "")))
                rows.append(ft.DataRow(cells=cells))
            data_table.rows = rows
            page.update()

        def import_now(e):
            ok, msg, cnt, cols = import_fixed_excel(r"C:\\program_tax\\tax_address.xlsx")
            status.value = ("✅ " if ok else "❌ ") + msg
            status.color = ft.Colors.GREEN_700 if ok else ft.Colors.RED_700
            if ok and cols:
                # Update current columns to what we saw in file
                nonlocal current_columns
                current_columns = cols
            refresh_grid()

        def map_withholder_fields(item: dict) -> dict:
            # Try to map likely columns to withholder fields
            def first_nonempty(keys: list[str]) -> str:
                for k in keys:
                    if k in item and item[k] not in (None, ""):
                        return str(item[k])
                return ""
            # Prefer exact field names from spec
            name = first_nonempty(["name_tax", "withholder_name", "name", "company_name", "company", "ผู้หักภาษี", "ชื่อผู้หักภาษี"])
            address = first_nonempty(["name_tax_address", "withholder_address", "address", "ที่อยู่", "ที่อยู่ผู้หักภาษี"])    
            tax_id_raw = first_nonempty(["name_tax_id_card", "withholder_tax_id", "tax_id", "เลขประจำตัวผู้เสียภาษี", "taxid"])
            tax_id = ''.join([ch for ch in tax_id_raw if ch.isdigit()])
            return {
                "withholder_name": name,
                "withholder_address": address,
                "withholder_tax_id": tax_id[:13] if tax_id else "",
            }

        def send_selected_to_crystal(e):
            # Collect first selected row
            selected_indices = [i for i, sel in row_selection.items() if sel]
            if not selected_indices:
                status.value = "❌ กรุณาเลือกรายการ"
                status.color = ft.Colors.RED_700
                page.update(); return
            idx0 = selected_indices[0]
            if idx0 < idx0 >= len(data_items):
                status.value = "❌ รายการไม่ถูกต้อง"
                status.color = ft.Colors.RED_700
                page.update(); return
            payload = map_withholder_fields(data_items[idx0])
            nonlocal pending_withholder_import_data
            pending_withholder_import_data = payload
            # Switch to crystal report tab
            try:
                nav_rail.selected_index = 1
                handle_nav_change(1)
                status.value = "✅ ส่งข้อมูลไปยัง ระบบพิกัด form PDF แล้ว"
                status.color = ft.Colors.GREEN_700
                page.update()
            except Exception as ex:
                status.value = f"❌ ไม่สามารถเปิดแท็บ ระบบพิกัด form PDF: {ex}"
                status.color = ft.Colors.RED_700
                page.update()

        def send_selected_to_pdf(e):
            # Collect first selected row
            selected_indices = [i for i, sel in row_selection.items() if sel]
            if not selected_indices:
                status.value = "❌ กรุณาเลือกรายการ"
                status.color = ft.Colors.RED_700
                page.update(); return
            idx0 = selected_indices[0]
            if idx0 < 0 or idx0 >= len(data_items):
                status.value = "❌ รายการไม่ถูกต้อง"
                status.color = ft.Colors.RED_700
                page.update(); return
            payload = map_withholder_fields(data_items[idx0])
            nonlocal pending_withholder_import_data
            pending_withholder_import_data = payload
            # Switch to PDF tab (tax form tab)
            try:
                nav_rail.selected_index = 5
                handle_nav_change(5)
                status.value = "✅ ส่งข้อมูลไปยัง ฟอร์มภาษี แล้ว"
                status.color = ft.Colors.GREEN_700
                page.update()
            except Exception as ex:
                status.value = f"❌ ไม่สามารถเปิดแท็บ ฟอร์มภาษี: {ex}"
                status.color = ft.Colors.RED_700
                page.update()

        def save_settings(e):
            """บันทึกการตั้งค่า checkbox states และข้อมูลผู้หักภาษีที่เลือก"""
            conn = get_conn()
            if not conn:
                status.value = "❌ เชื่อมต่อฐานข้อมูลไม่สำเร็จ"
                status.color = ft.Colors.RED_700
                page.update(); return
            
            try:
                cur = conn.cursor()
                
                # Collect selected items
                selected_indices = [i for i, sel in row_selection.items() if sel]
                if not selected_indices:
                    status.value = "❌ กรุณาเลือกรายการที่ต้องการบันทึก"
                    status.color = ft.Colors.RED_700
                    page.update(); return
                
                # Get first selected item
                idx0 = selected_indices[0]
                if idx0 < 0 or idx0 >= len(data_items):
                    status.value = "❌ รายการไม่ถูกต้อง"
                    status.color = ft.Colors.RED_700
                    page.update(); return
                
                # Map to withholder fields
                withholder_data = map_withholder_fields(data_items[idx0])
                
                # Save checkbox states
                checkbox_states = {
                    "row_selection": row_selection,
                    "selected_withholder": withholder_data,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Convert to JSON string for compatibility
                import json
                checkbox_states_json = json.dumps(checkbox_states)
                
                # Delete old settings first, then insert new ones
                cur.execute("DELETE FROM withholder_settings WHERE setting_key = 'checkbox_states'")
                
                # Insert new settings
                cur.execute("""
                    INSERT INTO withholder_settings (setting_key, setting_value) 
                    VALUES ('checkbox_states', %s::jsonb)
                    """, (checkbox_states_json,))
                
                conn.commit()
                
                # แสดงข้อมูลที่บันทึกได้ชัดเจนขึ้น
                withholder_name = withholder_data.get('withholder_name', 'N/A')
                status.value = f"✅ บันทึกการตั้งค่าเรียบร้อยแล้ว - ผู้หักภาษี: {withholder_name}"
                status.color = ft.Colors.GREEN_700
                page.update()
                
                print(f"✅ Settings saved successfully: {withholder_name}")
                
            except Exception as ex:
                try:
                    conn.rollback()
                except Exception:
                    pass
                status.value = f"❌ บันทึกการตั้งค่าไม่สำเร็จ: {ex}"
                status.color = ft.Colors.RED_700
                page.update()
                print(f"❌ Save settings error: {ex}")
            finally:
                try:
                    if 'cur' in locals():
                        cur.close()
                    if 'conn' in locals():
                        conn.close()
                except Exception:
                    pass

        def load_settings(e):
            """โหลดการตั้งค่าที่บันทึกไว้"""
            conn = get_conn()
            if not conn:
                status.value = "❌ เชื่อมต่อฐานข้อมูลไม่สำเร็จ"
                status.color = ft.Colors.RED_700
                page.update(); return
            
            try:
                cur = conn.cursor()
                cur.execute("SELECT setting_value FROM withholder_settings WHERE setting_key = 'checkbox_states'")
                result = cur.fetchone()
                
                if result:
                    settings = result[0]
                    # Restore checkbox states
                    nonlocal row_selection
                    row_selection = settings.get("row_selection", {})
                    
                    # แสดงข้อมูลการตั้งค่าที่โหลดมา
                    withholder_data = settings.get("selected_withholder", {})
                    if withholder_data:
                        status.value = f"✅ โหลดการตั้งค่าเรียบร้อยแล้ว - ผู้หักภาษี: {withholder_data.get('withholder_name', 'N/A')}"
                    else:
                        status.value = "✅ โหลดการตั้งค่าเรียบร้อยแล้ว"
                    status.color = ft.Colors.GREEN_700
                    
                    # Update grid to reflect restored states
                    refresh_grid()
                    
                    # แสดงข้อมูลเพิ่มเติมเกี่ยวกับการตั้งค่าที่โหลดมา
                    selected_count = sum(1 for sel in row_selection.values() if sel)
                    if selected_count > 0:
                        status.value += f" (เลือก {selected_count} รายการ)"
                        page.update()
                    
                else:
                    status.value = "ℹ️ ไม่พบการตั้งค่าที่บันทึกไว้"
                    status.color = ft.Colors.BLUE_700
                    page.update()
                    
            except Exception as ex:
                status.value = f"❌ โหลดการตั้งค่าไม่สำเร็จ: {ex}"
                status.color = ft.Colors.RED_700
                page.update()
                print(f"❌ Load settings error: {ex}")
            finally:
                try:
                    if 'cur' in locals():
                        cur.close()
                    if 'conn' in locals():
                        conn.close()
                except Exception:
                    pass

        # Initial load
        ensure_table()
        refresh_grid()
        
        # Auto-load saved settings on startup
        def auto_load_settings():
            """โหลดการตั้งค่าที่บันทึกไว้เมื่อเริ่มโปรแกรม"""
            try:
                conn = get_conn()
                if not conn:
                    return
                
                cur = conn.cursor()
                cur.execute("SELECT setting_value FROM withholder_settings WHERE setting_key = 'checkbox_states'")
                result = cur.fetchone()
                
                if result:
                    settings = result[0]
                    # Restore checkbox states
                    nonlocal row_selection
                    row_selection = settings.get("row_selection", {})
                    
                    # Update grid to reflect restored states
                    refresh_grid()
                    
                    # Update status with more detailed information
                    withholder_data = settings.get("selected_withholder", {})
                    selected_count = sum(1 for sel in row_selection.values() if sel)
                    
                    if withholder_data:
                        status.value = f"✅ โหลดการตั้งค่าที่บันทึกไว้แล้ว - ผู้หักภาษี: {withholder_data.get('withholder_name', 'N/A')} (เลือก {selected_count} รายการ)"
                    else:
                        status.value = f"✅ โหลดการตั้งค่าที่บันทึกไว้แล้ว (เลือก {selected_count} รายการ)"
                    status.color = ft.Colors.GREEN_700
                    
                    print(f"✅ Auto-loaded settings: {selected_count} items selected")
                    
            except Exception as ex:
                print(f"❌ Auto-load settings error: {ex}")
            finally:
                try:
                    if 'cur' in locals():
                        cur.close()
                    if 'conn' in locals():
                        conn.close()
                except Exception:
                    pass
        
        # Run auto-load after a short delay to ensure UI is ready
        import threading
        def delayed_auto_load():
            import time
            time.sleep(0.5)  # Wait for UI to be ready
            auto_load_settings()
        
        threading.Thread(target=delayed_auto_load, daemon=True).start()

        def clear_all_data(e):
            conn = get_conn()
            if not conn:
                status.value = "❌ เชื่อมต่อฐานข้อมูลไม่สำเร็จ"
                status.color = ft.Colors.RED_700
                page.update(); return
            try:
                cur = conn.cursor()
                cur.execute(f"TRUNCATE TABLE {TABLE_NAME}")
                conn.commit()
                status.value = "✅ ลบข้อมูลทั้งหมดแล้ว"
                status.color = ft.Colors.GREEN_700
                refresh_grid()
            except Exception as ex:
                try:
                    conn.rollback()
                except Exception:
                    pass
                status.value = f"❌ ลบข้อมูลไม่สำเร็จ: {ex}"
                status.color = ft.Colors.RED_700
                page.update()
            finally:
                try:
                    if 'cur' in locals():
                        cur.close()
                    if 'conn' in locals():
                        conn.close()
                except Exception:
                    pass

        def clear_settings(e):
            """ล้างการตั้งค่าทั้งหมด"""
            conn = get_conn()
            if not conn:
                status.value = "❌ เชื่อมต่อฐานข้อมูลไม่สำเร็จ"
                status.color = ft.Colors.RED_700
                page.update(); return
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM withholder_settings WHERE setting_key = 'checkbox_states'")
                conn.commit()
                
                # Clear local selection state
                nonlocal row_selection
                row_selection.clear()
                
                status.value = "✅ ล้างการตั้งค่าเรียบร้อยแล้ว"
                status.color = ft.Colors.GREEN_700
                refresh_grid()
                page.update()
                
            except Exception as ex:
                try:
                    conn.rollback()
                except Exception:
                    pass
                status.value = f"❌ ล้างการตั้งค่าไม่สำเร็จ: {ex}"
                status.color = ft.Colors.RED_700
                page.update()
            finally:
                try:
                    if 'cur' in locals():
                        cur.close()
                    if 'conn' in locals():
                        conn.close()
                except Exception:
                    pass

        def show_current_selection_status(e):
            """แสดงสถานะปัจจุบันของการเลือกใน datagridview"""
            selected_count = sum(1 for sel in row_selection.values() if sel)
            total_count = len(data_items)
            
            if selected_count > 0:
                selected_indices = [i for i, sel in row_selection.items() if sel]
                status.value = f"📊 สถานะปัจจุบัน: เลือก {selected_count}/{total_count} รายการ (แถว: {', '.join(map(str, [i+1 for i in selected_indices]))})"
                status.color = ft.Colors.BLUE_700
            else:
                status.value = f"📊 สถานะปัจจุบัน: ไม่ได้เลือกรายการใดๆ ({total_count} รายการทั้งหมด)"
                status.color = ft.Colors.GREY_700
            
            page.update()

        return ft.Container(
            content=ft.Column([
                ft.Text("ระบบตั้งค่าหัวกระดาษ", size=22, weight=ft.FontWeight.BOLD),
                info_text,
                
                # Main action buttons
                ft.Row([
                    ft.ElevatedButton("นำเข้าจาก tax_address.xlsx", icon=ft.icons.FILE_UPLOAD, on_click=import_now),
                    ft.ElevatedButton("รีเฟรช", icon=ft.icons.REFRESH, on_click=lambda e: refresh_grid()),
                    ft.ElevatedButton("ล้างข้อมูล", icon=ft.icons.DELETE, on_click=clear_all_data,
                                      style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("นำข้อมูลไปเติมใน Crystal Report", icon=ft.icons.ARROW_FORWARD, on_click=send_selected_to_crystal,
                                      style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)),
                ], spacing=10, wrap=True),
                
                # Settings management buttons
                ft.Container(
                    content=ft.Column([
                        ft.Text("การจัดการการตั้งค่า", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                        ft.Row([
                            ft.ElevatedButton(
                                "💾 บันทึกการตั้งค่า", 
                                icon=ft.icons.SAVE, 
                                on_click=save_settings,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                                width=180
                            ),
                            ft.ElevatedButton(
                                "📂 โหลดการตั้งค่า", 
                                icon=ft.icons.FOLDER_OPEN, 
                                on_click=load_settings,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                                width=180
                            ),
                            ft.ElevatedButton(
                                "🗑️ ล้างการตั้งค่า", 
                                icon=ft.icons.DELETE_SWEEP, 
                                on_click=clear_settings,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
                                width=180
                            ),
                        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row([
                            ft.ElevatedButton(
                                "📊 แสดงสถานะปัจจุบัน", 
                                icon=ft.icons.INFO_OUTLINE, 
                                on_click=show_current_selection_status,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE),
                                width=200
                            ),
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Text("เลือกข้อมูลผู้หักภาษีที่ต้องการ แล้วกดบันทึกการตั้งค่า", 
                               size=12, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
                    ], spacing=10),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=10,
                    padding=15,
                    margin=ft.margin.only(bottom=15)
                ),
                
                status,
                
                # Data table with scrollbar
                ft.Container(
                    content=ft.Column([
                        ft.Text("ข้อมูลผู้หักภาษี", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        ft.Container(
                            content=ft.Column([
                                data_table
                            ], scroll=ft.ScrollMode.AUTO, height=400, spacing=0, expand=True),
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            border_radius=5,
                            padding=10,
                            expand=True
                        )
                    ], spacing=10, expand=True),
                    padding=15, bgcolor=ft.Colors.GREY_50, border_radius=8,
                    expand=True
                ),
                
                # Action buttons for PDF
                ft.Row([
                    ft.ElevatedButton(
                        "นำข้อมูลไปเติมใน Crystal Report", 
                        icon=ft.icons.ARROW_FORWARD, 
                        on_click=send_selected_to_crystal,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                        width=250
                    ),
                    ft.ElevatedButton(
                        "นำข้อมูลไปเติมใน PDF", 
                        icon=ft.icons.PICTURE_AS_PDF, 
                        on_click=send_selected_to_pdf,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                        width=250
                    )
                ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=12),
            padding=20,
        )





    # Export Excel function
    def export_excel_clicked(e):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transfer_records_{timestamp}.xlsx"
            app.export_to_excel(filename)
            
            # Show success dialog
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("สำเร็จ"),
                content=ft.Text(f"ส่งออกไฟล์ Excel เรียบร้อยแล้ว\nไฟล์: {filename}"),
                actions=[
                    ft.TextButton("ตกลง", on_click=close_dialog)
                ]
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
            
        except Exception as e:
            # Show error dialog
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("เกิดข้อผิดพลาด"),
                content=ft.Text(f"ไม่สามารถส่งออกไฟล์ Excel ได้\n{str(e)}"),
                actions=[
                    ft.TextButton("ตกลง", on_click=close_dialog)
                ]
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
    
    # Export PDF function
    def export_pdf_clicked(e):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transfer_records_{timestamp}.pdf"
            app.export_to_pdf(filename)
            
            # Show success dialog
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("สำเร็จ"),
                content=ft.Text(f"ส่งออกไฟล์ PDF เรียบร้อยแล้ว\nไฟล์: {filename}"),
                actions=[
                    ft.TextButton("ตกลง", on_click=close_dialog)
                ]
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
            
        except Exception as e:
            # Show error dialog
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("เกิดข้อผิดพลาด"),
                content=ft.Text(f"ไม่สามารถส่งออกไฟล์ PDF ได้\n{str(e)}"),
                actions=[
                    ft.TextButton("ตกลง", on_click=close_dialog)
                ]
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
    
    # Refresh data function
    def refresh_data_clicked(e):
        nonlocal data_table, full_data_grid, stats_cards
        try:
            ok, msg, cnt = app.reset_from_excel(r"C:\\program_tax\\transfer_records_update.xlsx")
            status_text.value = ("✅ " if ok else "❌ ") + msg
            status_text.color = ft.Colors.GREEN_700 if ok else ft.Colors.RED_700
        except Exception as ex:
            status_text.value = f"❌ รีเซ็ตไม่สำเร็จ: {ex}"
            status_text.color = ft.Colors.RED_700

        new_stats = app.get_statistics()
        # Update statistics cards
        stats_cards.controls[0].content.controls[1].value = f"{new_stats[0]:,}"
        stats_cards.controls[1].content.controls[1].value = f"฿{new_stats[1]:,.2f}"
        stats_cards.controls[2].content.controls[1].value = f"฿{new_stats[2]:,.2f}"
        stats_cards.controls[3].content.controls[1].value = f"฿{new_stats[3]:,.2f}"

        # Recreate data tables
        data_table = create_data_table()
        full_data_grid = create_full_data_grid()

        # Update the current tab content
        if nav_rail.selected_index == 0:
            content_area.content = create_dashboard_tab()
        elif nav_rail.selected_index == 1:
            content_area.content = create_data_management_tab()
        elif nav_rail.selected_index == 2:
            content_area.content = create_all_data_tab()

        page.update()
    
    # Update UI after CRUD operations
    def update_ui_after_crud():
        """Update UI components after CRUD operations"""
        nonlocal data_table, full_data_grid, stats_cards
        new_stats = app.get_statistics()
        
        # Update statistics cards
        stats_cards.controls[0].content.controls[1].value = f"{new_stats[0]:,}"
        stats_cards.controls[1].content.controls[1].value = f"฿{new_stats[1]:,.2f}"
        stats_cards.controls[2].content.controls[1].value = f"฿{new_stats[2]:,.2f}"
        stats_cards.controls[3].content.controls[1].value = f"฿{new_stats[3]:,.2f}"
        
        # Recreate data tables
        data_table = create_data_table()
        full_data_grid = create_full_data_grid()
        
        # Update the current tab content
        if nav_rail.selected_index == 0:
            content_area.content = create_dashboard_tab()
        elif nav_rail.selected_index == 1:
            content_area.content = create_data_management_tab()
        elif nav_rail.selected_index == 2:
            content_area.content = create_all_data_tab()
        
        page.update()
    
    # CRUD Event Handlers
    def dashboard_load_selected_clicked(e):
        try:
            global selected_transfer_id_for_pdf
            if not selected_transfer_id_for_pdf:
                status_text.value = "❌ กรุณาเลือกแถวจากตารางก่อน"
                status_text.color = ft.Colors.RED_700
                page.update()
                return
            record = app.get_record_by_id(int(selected_transfer_id_for_pdf))
            if not record:
                status_text.value = "❌ ไม่พบข้อมูลจากรายการที่เลือก"
                status_text.color = ft.Colors.RED_700
                page.update()
                return
            # Fill fields
            record_id_input.value = str(record[0])
            name_input.value = record[1]
            surname_input.value = record[2]
            transfer_amount_input.value = str(record[3])
            transfer_date_input.value = record[4]
            id_card_input.value = record[5]
            address_input.value = record[6]
            percent_input.value = str(record[7])
            remark_input.value = record[11] or ""
            page.update()
        except Exception as ex:
            status_text.value = f"เกิดข้อผิดพลาด: {ex}"
            status_text.color = ft.Colors.RED_700
            page.update()

    def dashboard_add_clicked(e):
        try:
            if not name_input.value or not surname_input.value or not transfer_amount_input.value:
                raise ValueError("กรุณากรอกข้อมูลให้ครบถ้วน")
            transfer_amount = float(transfer_amount_input.value)
            percent = float(percent_input.value) if percent_input.value else 3.0
            ok, msg = app.add_record(
                name_input.value,
                surname_input.value,
                transfer_amount,
                transfer_date_input.value or "01/01/2025",
                id_card_input.value or "0000000000000",
                address_input.value or "ไม่ระบุ",
                percent,
                (remark_input.value or "").strip() or None
            )
            status_text.value = ("✅ " if ok else "❌ ") + msg
            status_text.color = ft.Colors.GREEN_700 if ok else ft.Colors.RED_700
            # Clear minimal fields after add
            record_id_input.value = ""
            name_input.value = ""; surname_input.value = ""; transfer_amount_input.value = ""
            transfer_date_input.value = ""; id_card_input.value = ""; address_input.value = ""
            percent_input.value = ""; remark_input.value = ""
            update_ui_after_crud()
        except Exception as ex:
            status_text.value = f"เกิดข้อผิดพลาด: {ex}"
            status_text.color = ft.Colors.RED_700
            page.update()

    def dashboard_update_clicked(e):
        try:
            if not record_id_input.value:
                raise ValueError("กรุณากรอก ID รายการที่จะอัปเดต")
            transfer_amount = float(transfer_amount_input.value or 0)
            percent = float(percent_input.value or 3.0)
            ok, msg = app.update_record(
                int(record_id_input.value),
                name_input.value or "",
                surname_input.value or "",
                transfer_amount,
                transfer_date_input.value or "",
                id_card_input.value or "",
                address_input.value or "",
                percent,
                (remark_input.value or "").strip() or None
            )
            status_text.value = ("✅ " if ok else "❌ ") + msg
            status_text.color = ft.Colors.GREEN_700 if ok else ft.Colors.RED_700
            update_ui_after_crud()
        except Exception as ex:
            status_text.value = f"เกิดข้อผิดพลาด: {ex}"
            status_text.color = ft.Colors.RED_700
            page.update()

    def dashboard_delete_clicked(e):
        try:
            if not record_id_input.value:
                raise ValueError("กรุณากรอก ID รายการที่จะลบ")
            ok, msg = app.delete_record(int(record_id_input.value))
            status_text.value = ("✅ " if ok else "❌ ") + msg
            status_text.color = ft.Colors.GREEN_700 if ok else ft.Colors.RED_700
            record_id_input.value = ""
            name_input.value = ""; surname_input.value = ""; transfer_amount_input.value = ""
            transfer_date_input.value = ""; id_card_input.value = ""; address_input.value = ""
            percent_input.value = ""; remark_input.value = ""
            update_ui_after_crud()
        except Exception as ex:
            status_text.value = f"เกิดข้อผิดพลาด: {ex}"
            status_text.color = ft.Colors.RED_700
            page.update()
    def add_record_clicked(e):
        try:
            # Validate required fields
            if not name_input.value or not surname_input.value or not transfer_amount_input.value:
                raise ValueError("กรุณากรอกข้อมูลให้ครบถ้วน")
            
            # Convert transfer_amount to float
            transfer_amount = float(transfer_amount_input.value)
            percent = float(percent_input.value) if percent_input.value else 3.0
            
            # Add record
            app.add_record(
                name_input.value,
                surname_input.value,
                transfer_amount,
                transfer_date_input.value or "01/01/2025",
                id_card_input.value or "0000000000000",
                address_input.value or "ไม่ระบุ",
                percent
            )
            
            # Clear input fields
            name_input.value = ""
            surname_input.value = ""
            transfer_amount_input.value = ""
            transfer_date_input.value = ""
            id_card_input.value = ""
            address_input.value = ""
            percent_input.value = ""
            
            # Update UI
            update_ui_after_crud()
            
            # Show success message
            status_text.value = "เพิ่มข้อมูลเรียบร้อยแล้ว"
            status_text.color = ft.Colors.GREEN_700
            page.update()
            
        except Exception as e:
            status_text.value = f"เกิดข้อผิดพลาด: {str(e)}"
            status_text.color = ft.Colors.RED_700
            page.update()
    
    def update_record_clicked(e):
        try:
            # Validate required fields
            if not record_id_input.value:
                raise ValueError("กรุณากรอก ID รายการ")
            if not name_input.value or not surname_input.value or not transfer_amount_input.value:
                raise ValueError("กรุณากรอกข้อมูลให้ครบถ้วน")
            
            # Convert values
            record_id = int(record_id_input.value)
            transfer_amount = float(transfer_amount_input.value)
            percent = float(percent_input.value) if percent_input.value else 3.0
            
            # Update record
            app.update_record(
                record_id,
                name_input.value,
                surname_input.value,
                transfer_amount,
                transfer_date_input.value or "01/01/2025",
                id_card_input.value or "0000000000000",
                address_input.value or "ไม่ระบุ",
                percent
            )
            
            # Clear input fields
            record_id_input.value = ""
            name_input.value = ""
            surname_input.value = ""
            transfer_amount_input.value = ""
            transfer_date_input.value = ""
            id_card_input.value = ""
            address_input.value = ""
            percent_input.value = ""
            
            # Update UI
            update_ui_after_crud()
            
            # Show success message
            status_text.value = "แก้ไขข้อมูลเรียบร้อยแล้ว"
            status_text.color = ft.Colors.GREEN_700
            page.update()
            
        except Exception as e:
            status_text.value = f"เกิดข้อผิดพลาด: {str(e)}"
            status_text.color = ft.Colors.RED_700
            page.update()
    
    def delete_record_clicked(e):
        try:
            # Validate required fields
            if not record_id_input.value:
                raise ValueError("กรุณากรอก ID รายการ")
            
            # Convert record_id to int
            record_id = int(record_id_input.value)
            
            # Delete record
            app.delete_record(record_id)
            
            # Clear input fields
            record_id_input.value = ""
            name_input.value = ""
            surname_input.value = ""
            transfer_amount_input.value = ""
            transfer_date_input.value = ""
            id_card_input.value = ""
            address_input.value = ""
            percent_input.value = ""
            
            # Update UI
            update_ui_after_crud()
            
            # Show success message
            status_text.value = "ลบข้อมูลเรียบร้อยแล้ว"
            status_text.color = ft.Colors.GREEN_700
            page.update()
            
        except Exception as e:
            status_text.value = f"เกิดข้อผิดพลาด: {str(e)}"
            status_text.color = ft.Colors.RED_700
            page.update()
    
    def load_record_clicked(e):
        try:
            # Validate required fields
            if not record_id_input.value:
                raise ValueError("กรุณากรอก ID รายการ")
            
            # Convert record_id to int
            record_id = int(record_id_input.value)
            
            # Get record
            record = app.get_record_by_id(record_id)
            
            if record:
                # Fill input fields
                name_input.value = record[0]
                surname_input.value = record[1]
                transfer_amount_input.value = str(record[2])
                transfer_date_input.value = record[3]
                id_card_input.value = record[4]
                address_input.value = record[5]
                percent_input.value = str(record[6])
                
                # Update UI
                page.update()
                
                # Show success message
                status_text.value = "โหลดข้อมูลเรียบร้อยแล้ว"
                status_text.color = ft.Colors.GREEN_700
                page.update()
            else:
                status_text.value = "ไม่พบข้อมูล"
                status_text.color = ft.Colors.RED_700
                page.update()
                
        except Exception as e:
            status_text.value = f"เกิดข้อผิดพลาด: {str(e)}"
            status_text.color = ft.Colors.RED_700
            page.update()
    
    # Create tab content functions
    def create_dashboard_tab():
        def set_selected_for_pdf(e=None):
            global selected_transfer_id_for_pdf
            # Choose the first checked row; if none, clear selection
            chosen = None
            for rec_id, cb in row_checkboxes.items():
                if cb.value:
                    chosen = rec_id
                    break
            selected_transfer_id_for_pdf = chosen
            try:
                page.update()
            except:
                pass

        def send_selected_to_crystal_from_dashboard(e):
            """ส่งข้อมูลที่เลือกจาก Dashboard ไปยัง Crystal Report tab - วิธีใหม่ที่ง่ายกว่า"""
            # Import required modules
            import json
            import os
            import traceback
            
            try:
                print(f"🚀 send_selected_to_crystal_from_dashboard called - วิธีใหม่")
                
                # วิธีใหม่: หา checkbox ที่ถูกเลือกโดยตรงจาก row_checkboxes
                selected_id = None
                for rec_id, cb in row_checkboxes.items():
                    if cb.value:
                        selected_id = rec_id
                        break
                
                if not selected_id:
                    print("⚠️ No row selected - ไม่มี checkbox ที่ถูกเลือก")
                    # Show error dialog
                    def close_dialog(e):
                        dialog.open = False
                        page.update()
                    
                    dialog = ft.AlertDialog(
                        title=ft.Text("⚠️ ไม่มีรายการที่เลือก"),
                        content=ft.Text("กรุณาเลือกรายการที่ต้องการในตารางด้านบนก่อน"),
                        actions=[ft.TextButton("ตกลง", on_click=close_dialog)]
                    )
                    page.dialog = dialog
                    dialog.open = True
                    page.update()
                    return
                
                print(f"✅ Row selected: {selected_id}")
                
                # วิธีใหม่: ใช้ข้อมูลจาก records ที่มีอยู่แล้วใน create_full_data_grid
                # เราไม่ต้องเรียก app.get_record_by_id อีกต่อไป
                records = app.get_all_records()
                selected_record = None
                for record in records:
                    if record[0] == selected_id:
                        selected_record = record
                        break
                
                if not selected_record:
                    print("❌ No record found in local records")
                    return
                
                print(f"📊 Selected record: {selected_record}")
                
                # Map the data to withholder format (selected_record is a tuple)
                withholder_data = {
                    'withholder_name': f"{selected_record[1] or ''} {selected_record[2] or ''}".strip(),
                    'withholder_address': selected_record[6] or '',
                    'withholder_tax_id': selected_record[5] or '',
                    'transfer_amount': selected_record[3] or 0,
                    'transfer_date': selected_record[4] or '',
                    'remark': selected_record[10] if len(selected_record) > 10 else ''
                }
                print(f"📦 Mapped withholder_data: {withholder_data}")
                
                # วิธีใหม่: ส่งข้อมูลผ่าน global variable ที่ง่ายกว่า
                # ใช้ชื่อที่ชัดเจนเพื่อหลีกเลี่ยงการชนกัน
                globals()['dashboard_to_crystal_data'] = withholder_data
                backup_data = globals().get('dashboard_to_crystal_data', None)
                if backup_data:
                    print(f"✅ Successfully stored withholder_data in globals: {backup_data}")
                else:
                    print("❌ Failed to store withholder_data in globals")
                
                # วิธีใหม่: ส่งข้อมูลผ่าน file system (ง่ายและเสถียร)
                # เพิ่มข้อมูล transfer record สำหรับ withholdee fields
                complete_data = {
                    'withholder_name': withholder_data['withholder_name'],
                    'withholder_address': withholder_data['withholder_address'],
                    'withholder_tax_id': withholder_data['withholder_tax_id'],
                    'transfer_record': {
                        'id': selected_record[0],
                        'name': selected_record[1] or '',
                        'surname': selected_record[2] or '',
                        # Convert Decimal to float to make it JSON-serializable
                        'transfer_amount': float(selected_record[3] or 0),
                        'transfer_date': selected_record[4] or '',
                        'id_card': selected_record[5] or '',
                        'address': selected_record[6] or '',
                        'percent': float(selected_record[7]) if len(selected_record) > 7 and selected_record[7] is not None else 0.0,
                        'total_amount': float(selected_record[8]) if len(selected_record) > 8 and selected_record[8] is not None else 0.0,
                        'fee': float(selected_record[9]) if len(selected_record) > 9 and selected_record[9] is not None else 0.0,
                        'remark': str(selected_record[10]) if len(selected_record) > 10 and selected_record[10] is not None else ''
                    }
                }

                temp_file_path = os.path.join(os.getcwd(), "temp_dashboard_data.json")
                try:
                    # Write atomically to avoid truncated/corrupted temp files
                    tmp_path = temp_file_path + ".tmp"
                    def _json_default(o):
                        from decimal import Decimal as _Dec
                        from datetime import datetime as _Dt
                        if isinstance(o, _Dec):
                            return float(o)
                        if isinstance(o, _Dt):
                            return o.isoformat()
                        return str(o)
                    with open(tmp_path, 'w', encoding='utf-8') as f:
                        json.dump(complete_data, f, ensure_ascii=False, indent=2, default=_json_default)
                    os.replace(tmp_path, temp_file_path)
                    print(f"💾 Successfully saved complete data to temp file: {temp_file_path}")
                    print(f"📄 File content: {complete_data}")
                except Exception as file_ex:
                    print(f"❌ Failed to save to temp file: {file_ex}")
                    try:
                        if 'tmp_path' in locals() and os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except Exception:
                        pass
                
                # Switch to Crystal Report tab
                print(f"🔄 Setting nav_rail.selected_index to 1")
                nav_rail.selected_index = 1
                print(f"🔄 Calling handle_nav_change(1)")
                handle_nav_change(1)
                print(f"🔄 Switched to Crystal Report tab (index 1)")
                
                # Show success dialog
                def close_dialog(e):
                    dialog.open = False
                    page.update()
                
                dialog = ft.AlertDialog(
                    title=ft.Text("✅ สำเร็จ"),
                    content=ft.Text(f"ส่งข้อมูลไปยัง Crystal Report แล้ว\nผู้หักภาษี: {withholder_data['withholder_name']}\nระบบจะเปลี่ยนไปยัง tab 'ระบบพิกัด form PDF' อัตโนมัติ"),
                    actions=[ft.TextButton("ตกลง", on_click=close_dialog)]
                )
                page.dialog = dialog
                dialog.open = True
                page.update()
                
            except Exception as ex:
                print(f"❌ Exception in send_selected_to_crystal_from_dashboard: {ex}")
                traceback.print_exc()
                # Show error dialog
                def close_dialog(e):
                    dialog.open = False
                    page.update()
                
                dialog = ft.AlertDialog(
                    title=ft.Text("❌ เกิดข้อผิดพลาด"),
                    content=ft.Text(f"ไม่สามารถส่งข้อมูลไปยัง Crystal Report ได้\n{str(ex)}"),
                    actions=[ft.TextButton("ตกลง", on_click=close_dialog)]
                )
                page.dialog = dialog
                dialog.open = True
                page.update()
                print(f"❌ Send to Crystal Report error: {ex}")



        def autofill_from_selection(e):
            """ส่งข้อมูลรายการที่เลือกไปเติมในแท็บ 'ระบบพิกัด form PDF' (ผู้ถูกหักภาษี) โดยไม่แสดง modal"""
            try:
                # 1) Find selected record
                selected_id = None
                for rec_id, cb in row_checkboxes.items():
                    if cb.value:
                        selected_id = rec_id
                        break
                if not selected_id:
                    status_text.value = "❌ กรุณาเลือกแถวจากตารางก่อน"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return

                # 2) Persist selection for Crystal Report tab auto-fill
                try:
                    global selected_transfer_id_for_pdf
                    selected_transfer_id_for_pdf = selected_id
                except Exception:
                    pass

                # 3) Optional: also provide dashboard data globally (withholdee only)
                try:
                    records = app.get_all_records()
                    selected_record = next((r for r in records if r[0] == selected_id), None)
                    if selected_record:
                        withholdee_payload = {
                            "transfer_record": {
                                "name": selected_record[1] or "",
                                "surname": selected_record[2] or "",
                                "transfer_amount": float(selected_record[3] or 0),
                                "date": selected_record[4] or "",
                                "id_card": selected_record[5] or "",
                                "address": selected_record[6] or "",
                                "percent": float(selected_record[7] or 0),
                                "total_amount": float((selected_record[8] or 0)),
                                "fee": float((selected_record[9] or 0)),
                            }
                        }
                        globals()["dashboard_to_crystal_data"] = withholdee_payload
                except Exception:
                    pass

                # 4) Switch to 'ระบบพิกัด form PDF' tab (index 1) where auto-fill runs
                status_text.value = f"✅ เลือก ID: {selected_id} → ส่งไปแท็บ 'ระบบพิกัด form PDF' เพื่อเติมข้อมูลผู้ถูกหักภาษี"
                status_text.color = ft.Colors.GREEN_700
                page.update()
                try:
                    handle_nav_change(1)
                except Exception:
                    try:
                        content_area.content = create_crystal_report_tab()
                        page.update()
                    except Exception:
                        pass

                # หลังสลับแท็บ ให้เรียกเติมทุกช่องใน panel อัตโนมัติ (เหมือนกดปุ่มดึงข้อมูลที่เลือก)
                try:
                    import threading, time
                    def _late_call_fill():
                        try:
                            time.sleep(0.6)  # รอให้แท็บสร้างเสร็จและฟังก์ชันพร้อมใน globals
                            f = globals().get('auto_fill_from_selected_dashboard')
                            if callable(f):
                                f()
                                try:
                                    page.update()
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    threading.Thread(target=_late_call_fill, daemon=True).start()
                except Exception:
                    pass

            except Exception as ex:
                status_text.value = f"❌ เกิดข้อผิดพลาด: {ex}"
                status_text.color = ft.Colors.RED_700
                page.update()

        # Buttons to use selection
        selection_bar = ft.Row([
            ft.ElevatedButton(
                text="🚀 Autofill",
                icon=ft.Icons.AUTO_FIX_HIGH,
                on_click=autofill_from_selection,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                tooltip="แสดงข้อมูลที่ถูกเลือกสำหรับ autofill ในฟอร์ม"
            ),
            ft.Text(lambda: f"เลือก ID: {selected_transfer_id_for_pdf}" if selected_transfer_id_for_pdf else "ยังไม่ได้เลือก",
                   size=12, color=ft.Colors.GREY_700)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.DASHBOARD, size=40, color=ft.Colors.BLUE_700),
                        ft.Column([
                            ft.Text("แดชบอร์ด", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text("ภาพรวมข้อมูลการโอนเงิน", size=14, color=ft.Colors.GREY_700)
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.START),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=10,
                    padding=20,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Statistics
                ft.Text("สถิติข้อมูล", size=18, weight=ft.FontWeight.BOLD),
                stats_cards,
                
                ft.Divider(height=30),
                
                ft.Divider(height=30),
                
                # All data grid (with selection checkbox)
                ft.Text("ข้อมูลทั้งหมด", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column([
                        full_data_grid,
                        selection_bar
                    ], scroll=ft.ScrollMode.AUTO),
                    height=400,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    padding=10
                ),
                
                # Quick action info
                ft.Container(
                    content=ft.Column([
                        ft.Text("🚀 การทำงานแบบอัตโนมัติ", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                        ft.Text("ปุ่ม 'นำข้อมูลไปเติมใน Crystal Report' จะทำงานแบบอัตโนมัติ:", size=12, color=ft.Colors.GREY_700),
                        ft.Text("• เปลี่ยน tab ไปยัง 'ระบบพิกัด form PDF' อัตโนมัติ", size=12, color=ft.Colors.GREEN_700),
                        ft.Text("• เติมข้อมูลผู้หักภาษีในฟอร์มโดยอัตโนมัติ", size=12, color=ft.Colors.GREEN_700),
                        ft.Text("• ไม่ต้องกดปุ่ม 'ดึงข้อมูลขึ้นมา' ซ้ำ", size=12, color=ft.Colors.GREEN_700)
                    ], spacing=5),
                    bgcolor=ft.Colors.PURPLE_50,
                    border_radius=8,
                    padding=15,
                    margin=ft.margin.only(top=15, bottom=15)
                )
                ,
                # Quick edit panel under the grid
                ft.Container(
                    content=ft.Column([
                        ft.Text("แก้ไขข้อมูลอย่างรวดเร็ว (Dashboard)", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            record_id_input,
                            ft.ElevatedButton(
                                text="⬇️ โหลดจากแถวที่เลือก",
                                icon=ft.Icons.DOWNLOAD,
                                on_click=dashboard_load_selected_clicked,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE),
                                width=180
                            )
                        ], spacing=10),
                        ft.Row([name_input, surname_input, percent_input], spacing=10),
                        ft.Row([transfer_amount_input, transfer_date_input], spacing=10),
                        ft.Row([id_card_input, remark_input], spacing=10),
                        address_input,
                        ft.Row([
                            ft.ElevatedButton(
                                text="➕ เพิ่ม",
                                icon=ft.Icons.ADD,
                                on_click=dashboard_add_clicked,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                                width=120
                            ),
                            ft.ElevatedButton(
                                text="✏️ แก้ไข",
                                icon=ft.Icons.EDIT,
                                on_click=dashboard_update_clicked,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                                width=120
                            ),
                            ft.ElevatedButton(
                                text="🗑️ ลบ",
                                icon=ft.Icons.DELETE,
                                on_click=dashboard_delete_clicked,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
                                width=120
                            )
                        ], spacing=10)
                    ], spacing=10),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=10,
                    padding=10
                ),
                
                ft.Divider(height=30),
                
                # Action buttons moved to bottom
                ft.Text("เครื่องมือเพิ่มเติม", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                ft.Row([
                    ft.ElevatedButton(
                        text="📁 ส่งออกเป็นไฟล์ Excel",
                        icon=ft.Icons.FILE_DOWNLOAD,
                        on_click=export_excel_clicked,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN_700,
                            color=ft.Colors.WHITE,
                            padding=15
                        ),
                        width=200
                    ),
                    ft.ElevatedButton(
                        text="📄 ส่งออกเป็นไฟล์ PDF",
                        icon=ft.Icons.PICTURE_AS_PDF,
                        on_click=export_pdf_clicked,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.RED_700,
                            color=ft.Colors.WHITE,
                            padding=15
                        ),
                        width=200
                    ),
                    ft.ElevatedButton(
                        text="🔄 รีเฟรชข้อมูล",
                        icon=ft.Icons.REFRESH,
                        on_click=refresh_data_clicked,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_700,
                            color=ft.Colors.WHITE,
                            padding=15
                        ),
                        width=150
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                
                ft.Divider(height=20),
                
                # Manual PDF selection (moved from top)
                ft.Text("เครื่องมือเพิ่มเติมสำหรับ PDF", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700),
                ft.Row([
                    ft.ElevatedButton(
                        text="✅ เลือกรายการเพื่อกรอก PDF",
                        icon=ft.Icons.CHECK_CIRCLE,
                        on_click=set_selected_for_pdf,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE, padding=15),
                        width=280
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                
                ft.Container(
                    content=ft.Column([
                        ft.Text("📋 วิธีการใช้งาน (เครื่องมือเก่า):", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700),
                        ft.Text("1. เลือกรายการที่ต้องการในตารางด้านบน", size=12, color=ft.Colors.GREY_700),
                        ft.Text("2. กดปุ่ม 'เลือกรายการเพื่อกรอก PDF' (เครื่องมือเก่า)", size=12, color=ft.Colors.GREY_700),
                        ft.Text("3. ใช้สำหรับการทำงานแบบเดิม (ไม่มีการเปลี่ยน tab อัตโนมัติ)", size=12, color=ft.Colors.GREY_700),
                        ft.Text("⚠️ แนะนำให้ใช้ปุ่ม 'นำข้อมูลไปเติมใน Crystal Report' แทน", size=12, color=ft.Colors.ORANGE_700, weight=ft.FontWeight.BOLD)
                    ], spacing=5),
                    bgcolor=ft.Colors.INDIGO_50,
                    border_radius=8,
                    padding=15,
                    margin=ft.margin.only(top=10)
                )
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def create_data_management_tab():
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.EDIT, size=40, color=ft.Colors.GREEN_700),
                        ft.Column([
                            ft.Text("จัดการข้อมูล", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text("เพิ่ม แก้ไข ลบ ข้อมูลการโอนเงิน", size=14, color=ft.Colors.GREY_700)
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.START),
                    bgcolor=ft.Colors.GREEN_50,
                    border_radius=10,
                    padding=20,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # CRUD Operations Section
                ft.Text("จัดการข้อมูล", size=18, weight=ft.FontWeight.BOLD),
                
                # Input fields
                ft.Container(
                    content=ft.Column([
                        ft.Text("ข้อมูลรายการ", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            record_id_input,
                            ft.ElevatedButton(
                                text="🔍 โหลดข้อมูล",
                                icon=ft.Icons.SEARCH,
                                on_click=load_record_clicked,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.ORANGE_700,
                                    color=ft.Colors.WHITE,
                                    padding=10
                                ),
                                width=120
                            )
                        ], spacing=10),
                        ft.Row([
                            name_input,
                            surname_input
                        ], spacing=10),
                        ft.Row([
                            transfer_amount_input,
                            transfer_date_input
                        ], spacing=10),
                        ft.Row([
                            id_card_input,
                            percent_input
                        ], spacing=10),
                        address_input,
                        
                        # CRUD Buttons
                        ft.Row([
                            ft.ElevatedButton(
                                text="➕ เพิ่มข้อมูล",
                                icon=ft.Icons.ADD,
                                on_click=add_record_clicked,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREEN_700,
                                    color=ft.Colors.WHITE,
                                    padding=15
                                ),
                                width=150
                            ),
                            ft.ElevatedButton(
                                text="✏️ แก้ไขข้อมูล",
                                icon=ft.Icons.EDIT,
                                on_click=update_record_clicked,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_700,
                                    color=ft.Colors.WHITE,
                                    padding=15
                                ),
                                width=150
                            ),
                            ft.ElevatedButton(
                                text="🗑️ ลบข้อมูล",
                                icon=ft.Icons.DELETE,
                                on_click=delete_record_clicked,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.RED_700,
                                    color=ft.Colors.WHITE,
                                    padding=15
                                ),
                                width=150
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
                    ], spacing=15),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=10,
                    padding=20,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Status
                ft.Container(
                    content=status_text,
                    alignment=ft.alignment.center,
                    padding=10
                )
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def create_all_data_tab():
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.TABLE_CHART, size=40, color=ft.Colors.PURPLE_700),
                        ft.Column([
                            ft.Text("ข้อมูลทั้งหมด", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text("แสดงข้อมูลการโอนเงินทั้งหมดในระบบ", size=14, color=ft.Colors.GREY_700)
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.START),
                    bgcolor=ft.Colors.PURPLE_50,
                    border_radius=10,
                    padding=20,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Full Data Grid
                ft.Text("ข้อมูลทั้งหมด", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column([
                        full_data_grid
                    ], scroll=ft.ScrollMode.AUTO),
                    height=600,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    padding=10
                )
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def create_tax_form_tab():
        # Initialize tax app
        tax_app = NeonTaxWithholdingApp()
        
        # Auto-fill withholder data from saved settings
        def auto_fill_withholder_data():
            """โหลดข้อมูลผู้หักภาษีที่บันทึกไว้มาเติมในฟอร์มอัตโนมัติ"""
            global pending_withholder_import_data
            
            try:
                if pending_withholder_import_data:
                    payload = pending_withholder_import_data
                    if payload.get('withholder_name'):
                        withholder_name.value = payload['withholder_name']
                    if payload.get('withholder_address'):
                        withholder_address.value = payload['withholder_address']
                    if payload.get('withholder_tax_id'):
                        withholder_tax_id.value = payload['withholder_tax_id']
                    
                    # Clear the pending data after use
                    pending_withholder_import_data = None
                    
                    print("✅ Auto-filled withholder data in tax form tab")
                    return True
                    
            except Exception as ex:
                print(f"❌ Auto-fill withholder data error: {ex}")
            return False
        
        # Run auto-fill after a short delay to ensure UI is ready
        import threading
        def delayed_auto_fill():
            import time
            time.sleep(0.5)  # Wait for UI to be ready
            auto_fill_withholder_data()
        
        threading.Thread(target=delayed_auto_fill, daemon=True).start()
        
        # Form fields - Withholder (ผู้มีหน้าที่หักภาษี)
        withholder_name = ft.TextField(label="ชื่อผู้มีหน้าที่หักภาษี", width=400)
        withholder_address = ft.TextField(label="ที่อยู่ผู้มีหน้าที่หักภาษี", width=600, multiline=True, max_lines=3)
        withholder_tax_id = ft.TextField(label="เลขประจำตัวผู้เสียภาษี (13 หลัก)", width=200, max_length=13)
        withholder_type = ft.Dropdown(
            label="ประเภท",
            width=200,
            options=[
                ft.dropdown.Option("บุคคล"),
                ft.dropdown.Option("นิติบุคคล"),
                ft.dropdown.Option("บริษัท"),
                ft.dropdown.Option("สมาคม"),
                ft.dropdown.Option("คณะบุคคล")
            ]
        )
        
        # Form fields - Withholdee (ผู้ถูกหักภาษี)
        withholdee_name = ft.TextField(label="ชื่อผู้ถูกหักภาษี", width=400)
        withholdee_address = ft.TextField(label="ที่อยู่ผู้ถูกหักภาษี", width=600, multiline=True, max_lines=3)
        withholdee_tax_id = ft.TextField(label="เลขประจำตัวผู้เสียภาษี (13 หลัก)", width=200, max_length=13)
        withholdee_type = ft.Dropdown(
            label="ประเภท",
            width=200,
            options=[
                ft.dropdown.Option("บุคคล"),
                ft.dropdown.Option("นิติบุคคล"),
                ft.dropdown.Option("บริษัท"),
                ft.dropdown.Option("สมาคม"),
                ft.dropdown.Option("คณะบุคคล")
            ]
        )
        
        # Document reference fields
        certificate_book_no = ft.TextField(label="เล่มที่", width=150)
        certificate_no = ft.TextField(label="เลขที่", width=150)
        sequence_in_form = ft.TextField(label="ลำดับที่ในแบบ", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        form_type = ft.Dropdown(
            label="ประเภทแบบ",
            width=200,
            options=[
                ft.dropdown.Option("ภ.ง.ด.1ก"),
                ft.dropdown.Option("ภ.ง.ด.1ก พิเศษ"),
                ft.dropdown.Option("ภ.ง.ด.2"),
                ft.dropdown.Option("ภ.ง.ด.3"),
                ft.dropdown.Option("ภ.ง.ด.2ก"),
                ft.dropdown.Option("ภ.ง.ด.3ก"),
                ft.dropdown.Option("ภ.ง.ด.53")
            ]
        )
        
        # Income type fields
        income_1_amount = ft.TextField(label="เงินเดือน ค่าจ้าง เบี้ยเลี้ยง โบนัส", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_1_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_2_amount = ft.TextField(label="ค่าธรรมเนียม ค่านายหน้า", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_2_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_3_amount = ft.TextField(label="ค่าแห่งลิขสิทธิ์", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_3_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_4a_amount = ft.TextField(label="ดอกเบี้ย", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_4a_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_4b_amount = ft.TextField(label="เงินปันผล เงินส่วนแบ่งกำไร", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_4b_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        dividend_credit_type = ft.Dropdown(
            label="ประเภทเครดิตภาษี",
            width=300,
            options=[
                ft.dropdown.Option("ได้รับเครดิตภาษี"),
                ft.dropdown.Option("ไม่ได้รับเครดิตภาษี")
            ]
        )
        
        dividend_tax_rate = ft.TextField(label="อัตราภาษีกำไรสุทธิ (%)", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        
        income_5_amount = ft.TextField(label="การจ่ายเงินได้ตามคำสั่งกรมสรรพากร", width=250, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_5_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_6_amount = ft.TextField(label="อื่น ๆ (จำนวนเงิน)", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_6_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_6_description = ft.TextField(label="อื่น ๆ (รายละเอียด)", width=300)
        
        # Fund fields
        provident_fund = ft.TextField(label="กบข./กสจ./กองทุนสงเคราะห์ครู", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        social_security_fund = ft.TextField(label="กองทุนประกันสังคม", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        retirement_mutual_fund = ft.TextField(label="กองทุนสำรองเลี้ยงชีพ", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        # Issue type
        issue_type = ft.Dropdown(
            label="ประเภทการออกใบรับรอง",
            width=200,
            options=[
                ft.dropdown.Option("หักณที่จ่าย"),
                ft.dropdown.Option("ออกให้ตลอดไป"),
                ft.dropdown.Option("ออกให้ครั้งเดียว"),
                ft.dropdown.Option("อื่น ๆ")
            ]
        )
        issue_type_other = ft.TextField(label="อื่น ๆ (ระบุ)", width=200)
        
        # Date and signature
        issue_date = ft.TextField(label="วันที่ออกหนังสือรับรอง (YYYY-MM-DD)", width=200)
        signatory_name = ft.TextField(label="ชื่อผู้จ่ายเงิน", width=300)
        company_seal = ft.Checkbox(label="ประทับตรานิติบุคคล", value=False)
        
        # Total fields (auto-calculated)
        total_income_display = ft.TextField(label="รวมเงินที่จ่าย", width=200, read_only=True)
        total_tax_display = ft.TextField(label="รวมภาษีที่หักนำส่ง", width=200, read_only=True)
        total_tax_text = ft.TextField(label="รวมภาษีที่หักนำส่ง (ตัวอักษร)", width=400)
        
        # Status text for tax form
        tax_status_text = ft.Text("พร้อมใช้งาน", size=14, color=ft.Colors.GREEN_700)
        
        def calculate_totals():
            """Calculate total income and tax"""
            try:
                total_income = (
                    float(income_1_amount.value or 0) +
                    float(income_2_amount.value or 0) +
                    float(income_3_amount.value or 0) +
                    float(income_4a_amount.value or 0) +
                    float(income_4b_amount.value or 0) +
                    float(income_5_amount.value or 0) +
                    float(income_6_amount.value or 0)
                )
                
                total_tax = (
                    float(income_1_tax.value or 0) +
                    float(income_2_tax.value or 0) +
                    float(income_3_tax.value or 0) +
                    float(income_4a_tax.value or 0) +
                    float(income_4b_tax.value or 0) +
                    float(income_5_tax.value or 0) +
                    float(income_6_tax.value or 0)
                )
                
                total_income_display.value = f"{total_income:,.2f}"
                total_tax_display.value = f"{total_tax:,.2f}"
                page.update()
                
            except ValueError:
                pass
        
        # Add event listeners for auto-calculation
        for field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax, 
                      income_3_amount, income_3_tax, income_4a_amount, income_4a_tax,
                      income_4b_amount, income_4b_tax, income_5_amount, income_5_tax,
                      income_6_amount, income_6_tax]:
            field.on_change = lambda e: calculate_totals()
        
        def save_tax_form(e):
            """Save tax form data to database"""
            try:
                # Validate required fields
                if not all([withholder_name.value, withholder_tax_id.value, 
                           withholdee_name.value, withholdee_tax_id.value]):
                    tax_status_text.value = "❌ กรุณากรอกข้อมูลที่จำเป็น"
                    tax_status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                # Validate tax ID format
                if len(withholder_tax_id.value) != 13 or not withholder_tax_id.value.isdigit():
                    tax_status_text.value = "❌ เลขประจำตัวผู้เสียภาษีผู้หักภาษีต้องเป็นตัวเลข 13 หลัก"
                    tax_status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                    
                if len(withholdee_tax_id.value) != 13 or not withholdee_tax_id.value.isdigit():
                    tax_status_text.value = "❌ เลขประจำตัวผู้เสียภาษีผู้ถูกหักภาษีต้องเป็นตัวเลข 13 หลัก"
                    tax_status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                # Prepare data
                data = (
                    withholder_name.value, withholder_address.value, withholder_tax_id.value, withholder_type.value or "บุคคล",
                    withholdee_name.value, withholdee_address.value, withholdee_tax_id.value, withholdee_type.value or "บุคคล",
                    certificate_book_no.value, certificate_no.value, 
                    int(sequence_in_form.value) if sequence_in_form.value else None, form_type.value,
                    float(income_1_amount.value) if (income_1_amount.value or "").strip() else 0.0,
                    float(income_1_tax.value) if (income_1_tax.value or "").strip() else 0.0,
                    float(income_2_amount.value) if (income_2_amount.value or "").strip() else 0.0,
                    float(income_2_tax.value) if (income_2_tax.value or "").strip() else 0.0,
                    float(income_3_amount.value or 0), float(income_3_tax.value or 0),
                    float(income_4a_amount.value or 0), float(income_4a_tax.value or 0),
                    float(income_4b_amount.value or 0), float(income_4b_tax.value or 0),
                    dividend_credit_type.value, float(dividend_tax_rate.value or 0),
                    float(income_5_amount.value or 0), float(income_5_tax.value or 0),
                    float(income_6_amount.value or 0), float(income_6_tax.value or 0), income_6_description.value,
                    float(total_income_display.value.replace(',', '') or 0), 
                    float(total_tax_display.value.replace(',', '') or 0), total_tax_text.value,
                    float(provident_fund.value) if (provident_fund.value or "").strip() else 0.0,
                    float(social_security_fund.value) if (social_security_fund.value or "").strip() else 0.0,
                    float(retirement_mutual_fund.value) if (retirement_mutual_fund.value or "").strip() else 0.0,
                    issue_type.value, issue_type_other.value, issue_date.value or None, 
                    signatory_name.value, company_seal.value
                )
                
                certificate_id = tax_app.save_certificate(data)
                
                if certificate_id:
                    tax_status_text.value = f"✅ บันทึกข้อมูลในฐานข้อมูลเรียบร้อยแล้ว (ID: {certificate_id})"
                    tax_status_text.color = ft.Colors.GREEN_700
                    
                    # Clear form
                    clear_tax_form(None)
                else:
                    tax_status_text.value = "❌ ไม่สามารถบันทึกข้อมูลได้"
                    tax_status_text.color = ft.Colors.RED_700
                    
            except Exception as ex:
                tax_status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                tax_status_text.color = ft.Colors.RED_700
            
            page.update()
        
        def clear_tax_form(e):
            """Clear all tax form fields"""
            for field in [withholder_name, withholder_address, withholder_tax_id,
                          withholdee_name, withholdee_address, withholdee_tax_id,
                          certificate_book_no, certificate_no, sequence_in_form,
                          income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                          income_3_amount, income_3_tax, income_4a_amount, income_4a_tax,
                          income_4b_amount, income_4b_tax, dividend_tax_rate,
                          income_5_amount, income_5_tax, income_6_amount, income_6_tax,
                          income_6_description, provident_fund, social_security_fund,
                          retirement_mutual_fund, issue_type_other, issue_date,
                          signatory_name, total_tax_text]:
                if hasattr(field, 'value'):
                    field.value = "0" if field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                                                   income_3_amount, income_3_tax, income_4a_amount, income_4a_tax,
                                                   income_4b_amount, income_4b_tax, income_5_amount, income_5_tax,
                                                   income_6_amount, income_6_tax, provident_fund, 
                                                   social_security_fund, retirement_mutual_fund] else ""
            
            for dropdown in [withholder_type, withholdee_type, form_type, dividend_credit_type, issue_type]:
                dropdown.value = None
            
            company_seal.value = False
            calculate_totals()
            page.update()
        
        def view_tax_certificates(e):
            """View saved tax certificates"""
            certificates = tax_app.get_all_certificates()
            
            if not certificates:
                tax_status_text.value = "ไม่มีข้อมูลหนังสือรับรองในฐานข้อมูล"
                tax_status_text.color = ft.Colors.ORANGE_700
                page.update()
                return
            
            # Create data table
            columns = [
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("ผู้หักภาษี")),
                ft.DataColumn(ft.Text("ผู้ถูกหักภาษี")),
                ft.DataColumn(ft.Text("ยอดรวม")),
                ft.DataColumn(ft.Text("ภาษีหัก")),
                ft.DataColumn(ft.Text("วันที่")),
                ft.DataColumn(ft.Text("สร้างเมื่อ"))
            ]
            
            rows = []
            for cert in certificates:
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(cert[0]))),
                    ft.DataCell(ft.Text(cert[1][:15] + "..." if len(cert[1]) > 15 else cert[1])),
                    ft.DataCell(ft.Text(cert[2][:15] + "..." if len(cert[2]) > 15 else cert[2])),
                    ft.DataCell(ft.Text(f"฿{cert[3]:,.2f}" if cert[3] else "0")),
                    ft.DataCell(ft.Text(f"฿{cert[4]:,.2f}" if cert[4] else "0")),
                    ft.DataCell(ft.Text(str(cert[5]) if cert[5] else "")),
                    ft.DataCell(ft.Text(str(cert[6])[:10] if cert[6] else ""))
                ]))
            
            data_table = ft.DataTable(columns=columns, rows=rows)
            
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text(f"รายการหนังสือรับรองการหักภาษี ({len(certificates)} รายการล่าสุด)"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("🗄️ ข้อมูลจาก PostgreSQL Database", size=12, color=ft.Colors.BLUE_700),
                        data_table
                    ], scroll=ft.ScrollMode.AUTO),
                    width=900,
                    height=500
                ),
                actions=[ft.TextButton("ปิด", on_click=close_dialog)]
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.DESCRIPTION, size=40, color=ft.Colors.ORANGE_700),
                        ft.Column([
                            ft.Text("ฟอร์มภาษี", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text("ระบบหนังสือรับรองการหักภาษี ณ ที่จ่าย", size=14, color=ft.Colors.GREY_700)
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.START),
                    bgcolor=ft.Colors.ORANGE_50,
                    border_radius=10,
                    padding=20,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Action buttons
                ft.Row([
                    ft.ElevatedButton("💾 บันทึกข้อมูล", on_click=save_tax_form, 
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("🗑️ เคลียร์ฟอร์ม", on_click=clear_tax_form,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("📋 ดูรายการ", on_click=view_tax_certificates,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                
                # Auto-fill status
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_700, size=20),
                        ft.Text("ข้อมูลผู้หักภาษีจะถูกเติมโดยอัตโนมัติเมื่อเลือกจาก Dashboard", 
                               size=12, color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD)
                    ], spacing=10),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=8,
                    padding=10,
                    margin=ft.margin.only(bottom=15)
                ),
                
                status_text,
                ft.Divider(),
                
                # Form sections
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลผู้มีหน้าที่หักภาษี ณ ที่จ่าย", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([withholder_name, withholder_type], spacing=10),
                                withholder_address,
                                withholder_tax_id
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลผู้ถูกหักภาษี ณ ที่จ่าย", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([withholdee_name, withholdee_type], spacing=10),
                                withholdee_address,
                                withholdee_tax_id
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลเอกสารอ้างอิง", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([certificate_book_no, certificate_no, sequence_in_form], spacing=10),
                                form_type
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("รายการเงินได้และภาษีที่หัก", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("1. เงินเดือน ค่าจ้าง เบี้ยเลี้ยง โบนัส ฯลฯ ตามมาตรา 40 (1)", weight=ft.FontWeight.BOLD),
                                ft.Row([income_1_amount, income_1_tax], spacing=10),
                                
                                ft.Divider(height=20),
                                ft.Text("2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ ตามมาตรา 40 (2)", weight=ft.FontWeight.BOLD),
                                ft.Row([income_2_amount, income_2_tax], spacing=10),
                                
                                ft.Divider(height=20),
                                ft.Text("3. ค่าแห่งลิขสิทธิ์ ฯลฯ ตามมาตรา 40 (3)", weight=ft.FontWeight.BOLD),
                                ft.Row([income_3_amount, income_3_tax], spacing=10),
                                
                                ft.Divider(height=20),
                                ft.Text("4. (ก) ดอกเบี้ย ฯลฯ ตามมาตรา 40 (4) (ก)", weight=ft.FontWeight.BOLD),
                                ft.Row([income_4a_amount, income_4a_tax], spacing=10),
                                
                                ft.Divider(height=20),
                                ft.Text("4. (ข) เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ ตามมาตรา 40 (4) (ข)", weight=ft.FontWeight.BOLD),
                                ft.Row([income_4b_amount, income_4b_tax], spacing=10),
                                ft.Row([dividend_credit_type, dividend_tax_rate], spacing=10),
                                
                                ft.Divider(height=20),
                                ft.Text("5. การจ่ายเงินได้ที่ต้องหักภาษี ณ ที่จ่าย ตามคำสั่งกรมสรรพากร", weight=ft.FontWeight.BOLD),
                                ft.Row([income_5_amount, income_5_tax], spacing=10),
                                
                                ft.Divider(height=20),
                                ft.Text("6. อื่น ๆ", weight=ft.FontWeight.BOLD),
                                ft.Row([income_6_amount, income_6_tax], spacing=10),
                                income_6_description,
                                
                                ft.Divider(height=30, color=ft.Colors.BLUE_700, thickness=2),
                                ft.Text("ยอดรวม", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                                ft.Row([total_income_display, total_tax_display], spacing=10),
                                total_tax_text
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("กองทุนต่าง ๆ", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("เงินที่จ่ายเข้า:", weight=ft.FontWeight.BOLD),
                                ft.Row([provident_fund, social_security_fund, retirement_mutual_fund], spacing=10)
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("การออกใบรับรองและลายเซ็น", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([issue_type, issue_type_other], spacing=10),
                                ft.Row([issue_date, signatory_name], spacing=10),
                                company_seal
                            ], spacing=10),
                            padding=10
                        )
                    ]
                )
                
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def create_tax_certificate_tab():
        """Create the tax certificate printing tab with functionality from program_tax_2.py"""
        # Initialize tax certificate app
        tax_cert_app = TaxCertificateApp()
        
        # Status message
        status_text = ft.Text("พร้อมใช้งาน", size=14, color=ft.Colors.GREEN_700)
        
        # Search and auto-fill functionality
        search_field = ft.TextField(
            label="🔍 ค้นหาด้วยชื่อหรือเลขประจำตัวผู้เสียภาษี",
            width=400,
            on_submit=lambda e: search_certificates()
        )
        
        def search_certificates():
            if not search_field.value:
                return
            
            certificates = tax_cert_app.get_all_certificates()
            if not certificates:
                status_text.value = "ไม่มีข้อมูลในฐานข้อมูล"
                status_text.color = ft.Colors.ORANGE_700
                page.update()
                return
            
            # Filter certificates based on search term
            search_term = search_field.value.lower()
            filtered_certs = []
            
            for cert in certificates:
                # Search in withholder name and withholdee name
                # get_all_certificates returns: id, withholder_name, withholdee_name, total_income, total_tax_withheld, issue_date, created_at
                withholder_name = str(cert[1]).lower() if cert[1] else ""
                withholdee_name = str(cert[2]).lower() if cert[2] else ""
                if (search_term in withholder_name or search_term in withholdee_name):
                    filtered_certs.append(cert)
            
            if not filtered_certs:
                status_text.value = f"ไม่พบข้อมูลที่ตรงกับ '{search_field.value}'"
                status_text.color = ft.Colors.ORANGE_700
                page.update()
                return
            
            # Show search results dialog
            show_search_results(filtered_certs)
        
        def show_search_results(certificates):
            """Show search results in a dialog for selection"""
            columns = [
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("ผู้หักภาษี")),
                ft.DataColumn(ft.Text("ผู้ถูกหักภาษี")),
                ft.DataColumn(ft.Text("ยอดรวม")),
                ft.DataColumn(ft.Text("เลือก"))
            ]
            
            def select_certificate(certificate_id):
                """Select a certificate to auto-fill the form"""
                cert_data = tax_cert_app.get_certificate_by_id(certificate_id)
                if cert_data:
                    auto_fill_form(cert_data)
                    status_text.value = f"✅ โหลดข้อมูลจากใบรับรอง ID: {certificate_id}"
                    status_text.color = ft.Colors.GREEN_700
                else:
                    status_text.value = f"❌ ไม่พบข้อมูลใบรับรอง ID: {certificate_id}"
                    status_text.color = ft.Colors.RED_700
                
                dialog.open = False
                page.update()
            
            rows = []
            for cert in certificates[:20]:  # Limit to 20 results
                select_button = ft.IconButton(
                    icon=ft.Icons.CHECK_CIRCLE,
                    tooltip="เลือกข้อมูลนี้",
                    icon_color=ft.Colors.GREEN_700,
                    on_click=lambda e, cert_id=cert[0]: select_certificate(cert_id)
                )
                
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(cert[0]))),
                    ft.DataCell(ft.Text(cert[1][:20] + "..." if len(cert[1]) > 20 else cert[1])),
                    ft.DataCell(ft.Text(cert[2][:20] + "..." if len(cert[2]) > 20 else cert[2])),
                    ft.DataCell(ft.Text(f"฿{cert[3]:,.2f}" if cert[3] else "0")),
                    ft.DataCell(select_button)
                ]))
            
            data_table = ft.DataTable(columns=columns, rows=rows)
            
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text(f"ผลการค้นหา ({len(certificates)} รายการ)"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("🔍 คลิกปุ่มเลือกเพื่อโหลดข้อมูลลงในฟอร์ม", size=12, color=ft.Colors.BLUE_700),
                        ft.Text(f"คำค้นหา: '{search_field.value}'", size=10, color=ft.Colors.GREY_700),
                        data_table
                    ], scroll=ft.ScrollMode.AUTO),
                    width=800,
                    height=400
                ),
                actions=[ft.TextButton("ปิด", on_click=close_dialog)]
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        def auto_fill_form(cert_data):
            """Auto-fill the form with data from selected certificate"""
            try:
                # Withholder information
                withholder_name.value = cert_data.get('withholder_name', '') or ""
                withholder_address.value = cert_data.get('withholder_address', '') or ""
                withholder_tax_id.value = cert_data.get('withholder_tax_id', '') or ""
                withholder_type.value = cert_data.get('withholder_type', '') or "บุคคล"
                
                # Withholdee information
                withholdee_name.value = cert_data.get('withholdee_name', '') or ""
                withholdee_address.value = cert_data.get('withholdee_address', '') or ""
                withholdee_tax_id.value = cert_data.get('withholdee_tax_id', '') or ""
                withholdee_type.value = cert_data.get('withholdee_type', '') or "บุคคล"
                
                # Document reference
                certificate_book_no.value = cert_data.get('certificate_book_no', '') or ""
                certificate_no.value = cert_data.get('certificate_no', '') or ""
                sequence_in_form.value = str(cert_data.get('sequence_in_form', '')) if cert_data.get('sequence_in_form') else ""
                form_type.value = cert_data.get('form_type', '') or ""
                
                # Income amounts and taxes
                income_1_amount.value = str(cert_data.get('income_type_1_amount', 0)) if cert_data.get('income_type_1_amount') else "0"
                income_1_tax.value = str(cert_data.get('income_type_1_tax', 0)) if cert_data.get('income_type_1_tax') else "0"
                income_2_amount.value = str(cert_data.get('income_type_2_amount', 0)) if cert_data.get('income_type_2_amount') else "0"
                income_2_tax.value = str(cert_data.get('income_type_2_tax', 0)) if cert_data.get('income_type_2_tax') else "0"
                income_3_amount.value = str(cert_data.get('income_type_3_amount', 0)) if cert_data.get('income_type_3_amount') else "0"
                income_3_tax.value = str(cert_data.get('income_type_3_tax', 0)) if cert_data.get('income_type_3_tax') else "0"
                income_4a_amount.value = str(cert_data.get('income_type_4a_amount', 0)) if cert_data.get('income_type_4a_amount') else "0"
                income_4a_tax.value = str(cert_data.get('income_type_4a_tax', 0)) if cert_data.get('income_type_4a_tax') else "0"
                income_4b_amount.value = str(cert_data.get('income_type_4b_amount', 0)) if cert_data.get('income_type_4b_amount') else "0"
                income_4b_tax.value = str(cert_data.get('income_type_4b_tax', 0)) if cert_data.get('income_type_4b_tax') else "0"
                
                dividend_credit_type.value = cert_data.get('dividend_credit_type', '') or ""
                dividend_tax_rate.value = str(cert_data.get('dividend_tax_rate', 0)) if cert_data.get('dividend_tax_rate') else ""
                
                income_5_amount.value = str(cert_data.get('income_type_5_amount', 0)) if cert_data.get('income_type_5_amount') else "0"
                income_5_tax.value = str(cert_data.get('income_type_5_tax', 0)) if cert_data.get('income_type_5_tax') else "0"
                income_6_amount.value = str(cert_data.get('income_type_6_amount', 0)) if cert_data.get('income_type_6_amount') else "0"
                income_6_tax.value = str(cert_data.get('income_type_6_tax', 0)) if cert_data.get('income_type_6_tax') else "0"
                income_6_description.value = cert_data.get('income_type_6_description', '') or ""
                
                # Totals
                total_income_display.value = f"{cert_data.get('total_income', 0):,.2f}" if cert_data.get('total_income') else "0.00"
                total_tax_display.value = f"{cert_data.get('total_tax_withheld', 0):,.2f}" if cert_data.get('total_tax_withheld') else "0.00"
                total_tax_text.value = cert_data.get('total_tax_withheld_text', '') or ""
                
                # Funds
                provident_fund.value = str(cert_data.get('provident_fund', 0)) if cert_data.get('provident_fund') else "0"
                social_security_fund.value = str(cert_data.get('social_security_fund', 0)) if cert_data.get('social_security_fund') else "0"
                retirement_mutual_fund.value = str(cert_data.get('retirement_mutual_fund', 0)) if cert_data.get('retirement_mutual_fund') else "0"
                
                # Issue information
                issue_type.value = cert_data.get('issue_type', '') or ""
                issue_type_other.value = cert_data.get('issue_type_other', '') or ""
                issue_date.value = str(cert_data.get('issue_date', '')) if cert_data.get('issue_date') else ""
                signatory_name.value = cert_data.get('signatory_name', '') or ""
                company_seal.value = cert_data.get('company_seal', False) if cert_data.get('company_seal') is not None else False
                
                # Recalculate totals
                calculate_totals()
                
                # Clear search field
                search_field.value = ""
                
                page.update()
                
            except Exception as e:
                status_text.value = f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {str(e)}"
                status_text.color = ft.Colors.RED_700
                page.update()
        
        def show_recent_certificates():
            """Show recent certificates for quick selection"""
            certificates = tax_cert_app.get_all_certificates()
            if not certificates:
                status_text.value = "ไม่มีข้อมูลในฐานข้อมูล"
                status_text.color = ft.Colors.ORANGE_700
                page.update()
                return
            
            # Get the 10 most recent certificates
            recent_certs = certificates[:10]
            
            columns = [
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("ผู้หักภาษี")),
                ft.DataColumn(ft.Text("ผู้ถูกหักภาษี")),
                ft.DataColumn(ft.Text("ยอดรวม")),
                ft.DataColumn(ft.Text("วันที่")),
                ft.DataColumn(ft.Text("เลือก"))
            ]
            
            def select_recent_certificate(certificate_id):
                """Select a recent certificate to auto-fill the form"""
                cert_data = tax_cert_app.get_certificate_by_id(certificate_id)
                if cert_data:
                    auto_fill_form(cert_data)
                    status_text.value = f"✅ โหลดข้อมูลจากใบรับรอง ID: {certificate_id}"
                    status_text.color = ft.Colors.GREEN_700
                else:
                    status_text.value = f"❌ ไม่พบข้อมูลใบรับรอง ID: {certificate_id}"
                    status_text.color = ft.Colors.RED_700
                
                dialog.open = False
                page.update()
            
            rows = []
            for cert in recent_certs:
                select_button = ft.IconButton(
                    icon=ft.Icons.CHECK_CIRCLE,
                    tooltip="เลือกข้อมูลนี้",
                    icon_color=ft.Colors.GREEN_700,
                    on_click=lambda e, cert_id=cert[0]: select_recent_certificate(cert_id)
                )
                
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(cert[0]))),
                    ft.DataCell(ft.Text(cert[1][:20] + "..." if len(cert[1]) > 20 else cert[1])),
                    ft.DataCell(ft.Text(cert[2][:20] + "..." if len(cert[2]) > 20 else cert[2])),
                    ft.DataCell(ft.Text(f"฿{cert[3]:,.2f}" if cert[3] else "0")),
                    ft.DataCell(ft.Text(str(cert[5])[:10] if cert[5] else "")),
                    ft.DataCell(select_button)
                ]))
            
            data_table = ft.DataTable(columns=columns, rows=rows)
            
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("ใบรับรองล่าสุด (10 รายการ)"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("⚡ คลิกปุ่มเลือกเพื่อโหลดข้อมูลลงในฟอร์ม", size=12, color=ft.Colors.BLUE_700),
                        ft.Text("แสดงใบรับรอง 10 รายการล่าสุด", size=10, color=ft.Colors.GREY_700),
                        data_table
                    ], scroll=ft.ScrollMode.AUTO),
                    width=900,
                    height=400
                ),
                actions=[ft.TextButton("ปิด", on_click=close_dialog)]
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        # Form fields for tax certificate
        withholder_name = ft.TextField(label="ชื่อผู้มีหน้าที่หักภาษี", width=400)
        withholder_address = ft.TextField(label="ที่อยู่ผู้มีหน้าที่หักภาษี", width=600, multiline=True, max_lines=3)
        withholder_tax_id = ft.TextField(label="เลขประจำตัวผู้เสียภาษี (13 หลัก)", width=200, max_length=13)
        withholder_type = ft.Dropdown(
            label="ประเภท",
            width=200,
            options=[
                ft.dropdown.Option("บุคคล"),
                ft.dropdown.Option("นิติบุคคล"),
                ft.dropdown.Option("บริษัท"),
                ft.dropdown.Option("สมาคม"),
                ft.dropdown.Option("คณะบุคคล")
            ]
        )
        
        # Withholdee fields
        withholdee_name = ft.TextField(label="ชื่อผู้ถูกหักภาษี", width=400)
        withholdee_address = ft.TextField(label="ที่อยู่ผู้ถูกหักภาษี", width=600, multiline=True, max_lines=3)
        withholdee_tax_id = ft.TextField(label="เลขประจำตัวผู้เสียภาษี (13 หลัก)", width=200, max_length=13)
        withholdee_type = ft.Dropdown(
            label="ประเภท",
            width=200,
            options=[
                ft.dropdown.Option("บุคคล"),
                ft.dropdown.Option("นิติบุคคล"),
                ft.dropdown.Option("บริษัท"),
                ft.dropdown.Option("สมาคม"),
                ft.dropdown.Option("คณะบุคคล")
            ]
        )
        
        # Document reference fields
        certificate_book_no = ft.TextField(label="เล่มที่", width=150)
        certificate_no = ft.TextField(label="เลขที่", width=150)
        sequence_in_form = ft.TextField(label="ลำดับที่ในแบบ", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        form_type = ft.Dropdown(
            label="ประเภทแบบ",
            width=200,
            options=[
                ft.dropdown.Option("ภ.ง.ด.1ก"),
                ft.dropdown.Option("ภ.ง.ด.1ก พิเศษ"),
                ft.dropdown.Option("ภ.ง.ด.2"),
                ft.dropdown.Option("ภ.ง.ด.3"),
                ft.dropdown.Option("ภ.ง.ด.2ก"),
                ft.dropdown.Option("ภ.ง.ด.3ก"),
                ft.dropdown.Option("ภ.ง.ด.53")
            ]
        )
        
        # Income type fields
        income_1_amount = ft.TextField(label="เงินเดือน ค่าจ้าง เบี้ยเลี้ยง โบนัส", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_1_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_2_amount = ft.TextField(label="ค่าธรรมเนียม ค่านายหน้า", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_2_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_3_amount = ft.TextField(label="ค่าแห่งลิขสิทธิ์", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_3_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_4a_amount = ft.TextField(label="ดอกเบี้ย", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_4a_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_4b_amount = ft.TextField(label="เงินปันผล เงินส่วนแบ่งกำไร", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_4b_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        dividend_credit_type = ft.Dropdown(
            label="ประเภทเครดิตภาษี",
            width=300,
            options=[
                ft.dropdown.Option("ได้รับเครดิตภาษี"),
                ft.dropdown.Option("ไม่ได้รับเครดิตภาษี")
            ]
        )
        
        dividend_tax_rate = ft.TextField(label="อัตราภาษีกำไรสุทธิ (%)", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        
        income_5_amount = ft.TextField(label="การจ่ายเงินได้ตามคำสั่งกรมสรรพากร", width=250, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_5_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_6_amount = ft.TextField(label="อื่น ๆ (จำนวนเงิน)", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_6_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_6_description = ft.TextField(label="อื่น ๆ (รายละเอียด)", width=300)
        
        # Fund fields
        provident_fund = ft.TextField(label="กบข./กสจ./กองทุนสงเคราะห์ครู", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        social_security_fund = ft.TextField(label="กองทุนประกันสังคม", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        retirement_mutual_fund = ft.TextField(label="กองทุนสำรองเลี้ยงชีพ", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        # Issue type
        issue_type = ft.Dropdown(
            label="ประเภทการออกใบรับรอง",
            width=200,
            options=[
                ft.dropdown.Option("หักณที่จ่าย"),
                ft.dropdown.Option("ออกให้ตลอดไป"),
                ft.dropdown.Option("ออกให้ครั้งเดียว"),
                ft.dropdown.Option("อื่น ๆ")
            ]
        )
        issue_type_other = ft.TextField(label="อื่น ๆ (ระบุ)", width=200)
        
        # Date and signature
        issue_date = ft.TextField(label="วันที่ออกหนังสือรับรอง (YYYY-MM-DD)", width=200)
        signatory_name = ft.TextField(label="ชื่อผู้จ่ายเงิน", width=300)
        company_seal = ft.Checkbox(label="ประทับตรานิติบุคคล", value=False)
        
        # Total fields (auto-calculated)
        total_income_display = ft.TextField(label="รวมเงินที่จ่าย", width=200, read_only=True)
        total_tax_display = ft.TextField(label="รวมภาษีที่หักนำส่ง", width=200, read_only=True)
        total_tax_text = ft.TextField(label="รวมภาษีที่หักนำส่ง (ตัวอักษร)", width=400)
        
        # Store the last saved certificate ID for PDF generation
        last_certificate_id = None
        
        def calculate_totals():
            """Calculate total income and tax"""
            try:
                total_income = (
                    float(income_1_amount.value or 0) +
                    float(income_2_amount.value or 0) +
                    float(income_3_amount.value or 0) +
                    float(income_4a_amount.value or 0) +
                    float(income_4b_amount.value or 0) +
                    float(income_5_amount.value or 0) +
                    float(income_6_amount.value or 0)
                )
                
                total_tax = (
                    float(income_1_tax.value or 0) +
                    float(income_2_tax.value or 0) +
                    float(income_3_tax.value or 0) +
                    float(income_4a_tax.value or 0) +
                    float(income_4b_tax.value or 0) +
                    float(income_5_tax.value or 0) +
                    float(income_6_tax.value or 0)
                )
                
                total_income_display.value = f"{total_income:,.2f}"
                total_tax_display.value = f"{total_tax:,.2f}"
                page.update()
                
            except ValueError:
                pass
        
        # Add event listeners for auto-calculation
        for field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax, 
                      income_3_amount, income_3_tax, income_4a_amount, income_4a_tax,
                      income_4b_amount, income_4b_tax, income_5_amount, income_5_tax,
                      income_6_amount, income_6_tax]:
            field.on_change = lambda e: calculate_totals()
        
        def save_certificate_form(e):
            """Save certificate form data to database"""
            nonlocal last_certificate_id
            try:
                # Validate required fields
                if not all([withholder_name.value, withholder_tax_id.value, 
                           withholdee_name.value, withholdee_tax_id.value]):
                    status_text.value = "❌ กรุณากรอกข้อมูลที่จำเป็น"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                # Validate tax ID format
                if len(withholder_tax_id.value) != 13 or not withholder_tax_id.value.isdigit():
                    status_text.value = "❌ เลขประจำตัวผู้เสียภาษีผู้หักภาษีต้องเป็นตัวเลข 13 หลัก"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                    
                if len(withholdee_tax_id.value) != 13 or not withholdee_tax_id.value.isdigit():
                    status_text.value = "❌ เลขประจำตัวผู้เสียภาษีผู้ถูกหักภาษีต้องเป็นตัวเลข 13 หลัก"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                # Prepare data
                data = (
                    withholder_name.value, withholder_address.value, withholder_tax_id.value, withholder_type.value or "บุคคล",
                    withholdee_name.value, withholdee_address.value, withholdee_tax_id.value, withholdee_type.value or "บุคคล",
                    certificate_book_no.value, certificate_no.value, 
                    int(sequence_in_form.value) if sequence_in_form.value else None, form_type.value,
                    float(income_1_amount.value) if (income_1_amount.value or "").strip() else 0.0,
                    float(income_1_tax.value) if (income_1_tax.value or "").strip() else 0.0,
                    float(income_2_amount.value) if (income_2_amount.value or "").strip() else 0.0,
                    float(income_2_tax.value) if (income_2_tax.value or "").strip() else 0.0,
                    float(income_3_amount.value or 0), float(income_3_tax.value or 0),
                    float(income_4a_amount.value or 0), float(income_4a_tax.value or 0),
                    float(income_4b_amount.value or 0), float(income_4b_tax.value or 0),
                    dividend_credit_type.value, float(dividend_tax_rate.value or 0),
                    float(income_5_amount.value or 0), float(income_5_tax.value or 0),
                    float(income_6_amount.value or 0), float(income_6_tax.value or 0), income_6_description.value,
                    float(total_income_display.value.replace(',', '') or 0), 
                    float(total_tax_display.value.replace(',', '') or 0), total_tax_text.value,
                    float(provident_fund.value) if (provident_fund.value or "").strip() else 0.0,
                    float(social_security_fund.value) if (social_security_fund.value or "").strip() else 0.0,
                    float(retirement_mutual_fund.value) if (retirement_mutual_fund.value or "").strip() else 0.0,
                    issue_type.value, issue_type_other.value, issue_date.value or None, 
                    signatory_name.value, company_seal.value
                )
                
                certificate_id = tax_cert_app.save_certificate(data)
                
                if certificate_id:
                    last_certificate_id = certificate_id
                    status_text.value = f"✅ บันทึกข้อมูลในฐานข้อมูลเรียบร้อยแล้ว (ID: {certificate_id})"
                    status_text.color = ft.Colors.GREEN_700
                    
                    # Enable PDF generation button
                    generate_pdf_button.disabled = False
                    page.update()
                    
                else:
                    status_text.value = "❌ ไม่สามารถบันทึกข้อมูลได้"
                    status_text.color = ft.Colors.RED_700
                    
            except Exception as ex:
                status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                status_text.color = ft.Colors.RED_700
            
            page.update()
        
        def generate_pdf_certificate(e):
            """Generate PDF certificate"""
            nonlocal last_certificate_id
            
            if not last_certificate_id:
                status_text.value = "❌ กรุณาบันทึกข้อมูลก่อนสร้าง PDF"
                status_text.color = ft.Colors.RED_700
                page.update()
                return
            
            try:
                cert_data = tax_cert_app.get_certificate_by_id(last_certificate_id)
                if cert_data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_filename = f"tax_certificate_{last_certificate_id}_{timestamp}.pdf"
                    success, message = tax_cert_app.generate_pdf_certificate(cert_data, pdf_filename)
                    
                    if success:
                        status_text.value = f"✅ {message}"
                        status_text.color = ft.Colors.GREEN_700
                    else:
                        status_text.value = f"❌ {message}"
                        status_text.color = ft.Colors.RED_700
                else:
                    status_text.value = f"❌ ไม่พบข้อมูลใบรับรอง ID: {last_certificate_id}"
                    status_text.color = ft.Colors.RED_700
                    
            except Exception as ex:
                status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                status_text.color = ft.Colors.RED_700
            
            page.update()
        
        def clear_certificate_form(e):
            """Clear all form fields"""
            nonlocal last_certificate_id
            last_certificate_id = None
            generate_pdf_button.disabled = True
            
            for field in [withholder_name, withholder_address, withholder_tax_id,
                          withholdee_name, withholdee_address, withholdee_tax_id,
                          certificate_book_no, certificate_no, sequence_in_form,
                          income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                          income_3_amount, income_3_tax, income_4a_amount, income_4a_tax,
                          income_4b_amount, income_4b_tax, dividend_tax_rate,
                          income_5_amount, income_5_tax, income_6_amount, income_6_tax,
                          income_6_description, provident_fund, social_security_fund,
                          retirement_mutual_fund, issue_type_other, issue_date,
                          signatory_name, total_tax_text]:
                if hasattr(field, 'value'):
                    field.value = "0" if field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                                                   income_3_amount, income_3_tax, income_4a_amount, income_4a_tax,
                                                   income_4b_amount, income_4b_tax, income_5_amount, income_5_tax,
                                                   income_6_amount, income_6_tax, provident_fund, 
                                                   social_security_fund, retirement_mutual_fund] else ""
            
            for dropdown in [withholder_type, withholdee_type, form_type, dividend_credit_type, issue_type]:
                dropdown.value = None
            
            company_seal.value = False
            calculate_totals()
            page.update()
        
        def view_certificates(e):
            """View saved certificates"""
            certificates = tax_cert_app.get_all_certificates()
            
            if not certificates:
                status_text.value = "ไม่มีข้อมูลหนังสือรับรองในฐานข้อมูล"
                status_text.color = ft.Colors.ORANGE_700
                page.update()
                return
            
            # Create data table
            columns = [
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("ผู้หักภาษี")),
                ft.DataColumn(ft.Text("ผู้ถูกหักภาษี")),
                ft.DataColumn(ft.Text("ยอดรวม")),
                ft.DataColumn(ft.Text("ภาษีหัก")),
                ft.DataColumn(ft.Text("วันที่")),
                ft.DataColumn(ft.Text("สร้างเมื่อ")),
                ft.DataColumn(ft.Text("PDF"))
            ]
            
            def generate_pdf_for_cert(certificate_id):
                try:
                    cert_data = tax_cert_app.get_certificate_by_id(certificate_id)
                    if cert_data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        pdf_filename = f"tax_certificate_{certificate_id}_{timestamp}.pdf"
                        success, message = tax_cert_app.generate_pdf_certificate(cert_data, pdf_filename)
                        
                        if success:
                            status_text.value = f"✅ สร้าง PDF เรียบร้อยแล้ว: {pdf_filename}"
                            status_text.color = ft.Colors.GREEN_700
                        else:
                            status_text.value = f"❌ {message}"
                            status_text.color = ft.Colors.RED_700
                    else:
                        status_text.value = f"❌ ไม่พบข้อมูลใบรับรอง ID: {certificate_id}"
                        status_text.color = ft.Colors.RED_700
                except Exception as ex:
                    status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                    status_text.color = ft.Colors.RED_700
                
                dialog.open = False
                page.update()
            
            rows = []
            for cert in certificates:
                pdf_button = ft.IconButton(
                    icon=ft.Icons.PICTURE_AS_PDF,
                    tooltip="สร้าง PDF",
                    icon_color=ft.Colors.RED_700,
                    on_click=lambda e, cert_id=cert[0]: generate_pdf_for_cert(cert_id)
                )
                
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(cert[0]))),
                    ft.DataCell(ft.Text(cert[1][:15] + "..." if len(cert[1]) > 15 else cert[1])),
                    ft.DataCell(ft.Text(cert[2][:15] + "..." if len(cert[2]) > 15 else cert[2])),
                    ft.DataCell(ft.Text(f"฿{cert[3]:,.2f}" if cert[3] else "0")),
                    ft.DataCell(ft.Text(f"฿{cert[4]:,.2f}" if cert[4] else "0")),
                    ft.DataCell(ft.Text(str(cert[5]) if cert[5] else "")),
                    ft.DataCell(ft.Text(str(cert[6])[:10] if cert[6] else "")),
                    ft.DataCell(pdf_button)
                ]))
            
            data_table = ft.DataTable(columns=columns, rows=rows)
            
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text(f"รายการหนังสือรับรองการหักภาษี ({len(certificates)} รายการล่าสุด)"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("🗄️ ข้อมูลจาก Neon PostgreSQL Database", size=12, color=ft.Colors.BLUE_700),
                        ft.Text("📄 คลิกปุ่ม PDF เพื่อสร้างใบรับรองในรูปแบบต้นฉบับ", size=12, color=ft.Colors.RED_700),
                        data_table
                    ], scroll=ft.ScrollMode.AUTO),
                    width=1000,
                    height=600
                ),
                actions=[ft.TextButton("ปิด", on_click=close_dialog)]
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        # PDF generation button (initially disabled)
        generate_pdf_button = ft.ElevatedButton(
            "📄 สร้าง PDF ใบรับรอง", 
            on_click=generate_pdf_certificate,
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
            disabled=True,
            tooltip="บันทึกข้อมูลก่อนเพื่อสร้าง PDF"
        )
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.PICTURE_AS_PDF, size=40, color=ft.Colors.RED_700),
                            ft.Column([
                                ft.Text("ระบบพิมพ์ใบกำกับภาษี - Tax Certificate Printing", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Tax Withholding Certificate PDF Generator", size=14, color=ft.Colors.GREY_700),
                                ft.Text("เชื่อมต่อกับ program_tax_2.py สำหรับสร้าง PDF ใบรับรองการหักภาษี", size=12, color=ft.Colors.BLUE_700)
                            ], spacing=2)
                        ]),
                        ft.Divider(height=1, color=ft.Colors.GREY_300)
                    ], spacing=10),
                    bgcolor=ft.Colors.RED_50,
                    border_radius=10,
                    padding=20,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Action buttons
                ft.Row([
                    ft.ElevatedButton("💾 บันทึกข้อมูล", on_click=save_certificate_form, 
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)),
                    generate_pdf_button,
                    ft.ElevatedButton("🗑️ เคลียร์ฟอร์ม", on_click=clear_certificate_form,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("📋 ดูรายการ", on_click=view_certificates,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("🔍 ค้นหาและโหลด", on_click=lambda e: search_certificates(),
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("⚡ โหลดเร็ว", on_click=lambda e: show_recent_certificates(),
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8, wrap=True),
                
                status_text,
                ft.Divider(),
                
                # Search section
                ft.Container(
                    content=ft.Column([
                        ft.Text("🔍 ค้นหาและโหลดข้อมูลจากฐานข้อมูล", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                        ft.Row([
                            search_field,
                            ft.ElevatedButton("🔍 ค้นหา", on_click=lambda e: search_certificates(),
                                            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)),
                            ft.ElevatedButton("⚡ ใบรับรองล่าสุด", on_click=lambda e: show_recent_certificates(),
                                            style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE))
                        ], spacing=10),
                        ft.Text("💡 ค้นหาด้วยชื่อผู้หักภาษี, ผู้ถูกหักภาษี, หรือเลขประจำตัวผู้เสียภาษี", size=12, color=ft.Colors.GREY_700)
                    ], spacing=10),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=10,
                    padding=15,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Form sections
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลผู้มีหน้าที่หักภาษี ณ ที่จ่าย", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([withholder_name, withholder_type], spacing=10),
                                withholder_address,
                                withholder_tax_id
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลผู้ถูกหักภาษี ณ ที่จ่าย", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([withholdee_name, withholdee_type], spacing=10),
                                withholdee_address,
                                withholdee_tax_id
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลเอกสารอ้างอิง", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([certificate_book_no, certificate_no, sequence_in_form], spacing=10),
                                form_type
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("รายการเงินได้และภาษีที่หัก", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("1. เงินเดือน ค่าจ้าง เบี้ยเลี้ยง โบนัส ฯลฯ ตามมาตรา 40 (1)", weight=ft.FontWeight.BOLD),
                                ft.Row([income_1_amount, income_1_tax], spacing=10),
                                
                                ft.Divider(height=20),
                                ft.Text("2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ ตามมาตรา 40 (2)", weight=ft.FontWeight.BOLD),
                                ft.Row([income_2_amount, income_2_tax], spacing=10),
                                
                                ft.Divider(height=20),
                                ft.Text("3. ค่าแห่งลิขสิทธิ์ ฯลฯ ตามมาตรา 40 (3)", weight=ft.FontWeight.BOLD),
                                ft.Row([income_3_amount, income_3_tax], spacing=10),
                                
                                ft.Divider(height=20),
                                ft.Text("4. (ก) ดอกเบี้ย ฯลฯ ตามมาตรา 40 (4) (ก)", weight=ft.FontWeight.BOLD),
                                ft.Row([income_4a_amount, income_4a_tax], spacing=10),
                                
                                ft.Divider(height=20),
                                ft.Text("4. (ข) เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ ตามมาตรา 40 (4) (ข)", weight=ft.FontWeight.BOLD),
                                ft.Row([income_4b_amount, income_4b_tax], spacing=10),
                                ft.Row([dividend_credit_type, dividend_tax_rate], spacing=10),
                                
                                ft.Divider(height=20),
                                ft.Text("5. การจ่ายเงินได้ที่ต้องหักภาษี ณ ที่จ่าย ตามคำสั่งกรมสรรพากร", weight=ft.FontWeight.BOLD),
                                ft.Row([income_5_amount, income_5_tax], spacing=10),
                                
                                ft.Divider(height=20),
                                ft.Text("6. อื่น ๆ", weight=ft.FontWeight.BOLD),
                                ft.Row([income_6_amount, income_6_tax], spacing=10),
                                income_6_description,
                                
                                ft.Divider(height=30, color=ft.Colors.BLUE_700, thickness=2),
                                ft.Text("ยอดรวม", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                                ft.Row([total_income_display, total_tax_display], spacing=10),
                                total_tax_text
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("กองทุนต่าง ๆ", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("เงินที่จ่ายเข้า:", weight=ft.FontWeight.BOLD),
                                ft.Row([provident_fund, social_security_fund, retirement_mutual_fund], spacing=10)
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("การออกใบรับรองและลายเซ็น", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([issue_type, issue_type_other], spacing=10),
                                ft.Row([issue_date, signatory_name], spacing=10),
                                company_seal
                            ], spacing=10),
                            padding=10
                        )
                    ]
                )
                
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def create_official_tax_form_tab():
        """Create the official tax form tab with PDF template functionality"""
        # Initialize the PDF template filler
        app = PDFTemplateFiller()
        
        # Status message
        status_text = ft.Text("พร้อมใช้งาน", size=14, color=ft.Colors.GREEN_700)
        
        # Template status
        template_status = ft.Text("กำลังตรวจสอบเทมเพลต...", size=12)
        
        def check_template():
            try:
                if hasattr(app, 'template_path') and os.path.exists(app.template_path):
                    template_status.value = f"✅ พบเทมเพลต PDF: {app.template_path}"
                    template_status.color = ft.Colors.GREEN_700
                else:
                    template_path = getattr(app, 'template_path', 'tax_form_template.pdf')
                    template_status.value = f"⚠️ ไม่พบเทมเพลต PDF: {template_path} (จะใช้โหมดสร้างใหม่)"
                    template_status.color = ft.Colors.ORANGE_700
            except Exception as e:
                template_status.value = f"⚠️ ไม่สามารถตรวจสอบเทมเพลตได้: {str(e)}"
                template_status.color = ft.Colors.RED_700
            page.update()
        
        check_template()
        
        # Prepare PDF preview image from form.pdf (optional) + file picker support
        def rasterize_pdf_to_png(path: str) -> str | None:
            try:
                import fitz as _fitz
                if not os.path.exists(path):
                    return None
                doc = _fitz.open(path)
                page0 = doc[0]
                pix = page0.get_pixmap(matrix=_fitz.Matrix(1.5, 1.5))
                out_png = tempfile.mktemp(suffix='.png')
                pix.save(out_png)
                doc.close()
                return out_png
            except Exception:
                return None

        pdf_path = os.path.abspath(os.path.join(os.getcwd(), 'form.pdf'))
        selected_pdf_path = pdf_path
        pdf_preview_img = rasterize_pdf_to_png(selected_pdf_path)
        def build_pdf_image():
            return ft.Image(src=(pdf_preview_img or ""), fit=ft.ImageFit.CONTAIN, width=595, height=842)
        def build_pdf_path_text():
            return ft.Text(value=f"ตำแหน่งไฟล์: {selected_pdf_path}", size=11, color=ft.Colors.GREY_600)
        pdf_image_control = build_pdf_image()
        pdf_path_text_control = build_pdf_path_text()

        def pick_pdf(e):
            def on_res(res: ft.FilePickerResultEvent):
                nonlocal selected_pdf_path, pdf_preview_img, pdf_image_control, pdf_path_text_control
                if res.files:
                    selected_pdf_path = res.files[0].path
                    pdf_preview_img = rasterize_pdf_to_png(selected_pdf_path)
                    pdf_image_control.src = pdf_preview_img or ""
                    pdf_path_text_control.value = f"ตำแหน่งไฟล์: {selected_pdf_path}"
                    page.update()
            picker = ft.FilePicker(on_result=on_res)
            page.overlay.append(picker)
            page.update()
            picker.pick_files(allowed_extensions=["pdf"], dialog_title="เลือกฟอร์ม PDF (form.pdf)")
        
        # Form fields
        withholder_name = ft.TextField(label="ชื่อผู้มีหน้าที่หักภาษี", width=400)
        withholder_address = ft.TextField(label="ที่อยู่ผู้มีหน้าที่หักภาษี", width=600, multiline=True, max_lines=3)
        withholder_tax_id = ft.TextField(label="เลขประจำตัวผู้เสียภาษี (13 หลัก)", width=200, max_length=13)
        withholder_type = ft.Dropdown(
            label="ประเภท", width=200,
            options=[ft.dropdown.Option("บุคคล"), ft.dropdown.Option("นิติบุคคล"), 
                    ft.dropdown.Option("บริษัท"), ft.dropdown.Option("สมาคม"), ft.dropdown.Option("คณะบุคคล")]
        )
        
        withholdee_name = ft.TextField(label="ชื่อผู้ถูกหักภาษี", width=400)
        withholdee_address = ft.TextField(label="ที่อยู่ผู้ถูกหักภาษี", width=600, multiline=True, max_lines=3)
        withholdee_tax_id = ft.TextField(label="เลขประจำตัวผู้เสียภาษี (13 หลัก)", width=200, max_length=13)
        withholdee_type = ft.Dropdown(
            label="ประเภท", width=200,
            options=[ft.dropdown.Option("บุคคล"), ft.dropdown.Option("นิติบุคคล"), 
                    ft.dropdown.Option("บริษัท"), ft.dropdown.Option("สมาคม"), ft.dropdown.Option("คณะบุคคล")]
        )
        
        certificate_book_no = ft.TextField(label="เล่มที่", width=150)
        certificate_no = ft.TextField(label="เลขที่", width=150)
        sequence_in_form = ft.TextField(label="ลำดับที่ในแบบ", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        form_type = ft.Dropdown(
            label="ประเภทแบบ", width=200,
            options=[ft.dropdown.Option("ภ.ง.ด.1ก"), ft.dropdown.Option("ภ.ง.ด.1ก พิเศษ"), 
                    ft.dropdown.Option("ภ.ง.ด.2"), ft.dropdown.Option("ภ.ง.ด.3"),
                    ft.dropdown.Option("ภ.ง.ด.2ก"), ft.dropdown.Option("ภ.ง.ด.3ก"), ft.dropdown.Option("ภ.ง.ด.53")]
        )
        
        # Income fields
        income_1_amount = ft.TextField(label="เงินเดือน ค่าจ้าง", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_1_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_2_amount = ft.TextField(label="ค่าธรรมเนียม ค่านายหน้า", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_2_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_3_amount = ft.TextField(label="ค่าแห่งลิขสิทธิ์", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_3_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_4a_amount = ft.TextField(label="ดอกเบี้ย", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_4a_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_4b_amount = ft.TextField(label="เงินปันผล เงินส่วนแบ่งกำไร", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_4b_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_5_amount = ft.TextField(label="การจ่ายเงินได้ตามคำสั่งกรมสรรพากร", width=250, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_5_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        income_6_amount = ft.TextField(label="อื่น ๆ (จำนวนเงิน)", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_6_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_6_description = ft.TextField(label="อื่น ๆ (รายละเอียด)", width=300)
        
        # Total fields
        total_income_display = ft.TextField(label="รวมเงินที่จ่าย", width=200, read_only=True)
        total_tax_display = ft.TextField(label="รวมภาษีที่หักนำส่ง", width=200, read_only=True)
        total_tax_text = ft.TextField(label="รวมภาษีที่หักนำส่ง (ตัวอักษร)", width=400)
        
        # Fund fields
        provident_fund = ft.TextField(label="กบข./กสจ./กองทุนสงเคราะห์ครู", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        social_security_fund = ft.TextField(label="กองทุนประกันสังคม", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        retirement_mutual_fund = ft.TextField(label="กองทุนสำรองเลี้ยงชีพ", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        # Issue fields
        issue_type = ft.Dropdown(
            label="ประเภทการออกใบรับรอง", width=200,
            options=[ft.dropdown.Option("หักณที่จ่าย"), ft.dropdown.Option("ออกให้ตลอดไป"),
                    ft.dropdown.Option("ออกให้ครั้งเดียว"), ft.dropdown.Option("อื่น ๆ")]
        )
        issue_type_other = ft.TextField(label="อื่น ๆ (ระบุ)", width=200)
        issue_date = ft.TextField(label="วันที่ออกหนังสือรับรอง (YYYY-MM-DD)", width=200)
        signatory_name = ft.TextField(label="ชื่อผู้จ่ายเงิน", width=300)
        company_seal = ft.Checkbox(label="ประทับตรานิติบุคคล", value=False)
        
        # Store last certificate ID
        last_certificate_id = None
        
        def calculate_totals():
            """Calculate total income and tax"""
            try:
                total_income = sum([
                    float(field.value or 0) for field in [
                        income_1_amount, income_2_amount, income_3_amount, 
                        income_4a_amount, income_4b_amount, income_5_amount, income_6_amount
                    ]
                ])
                
                total_tax = sum([
                    float(field.value or 0) for field in [
                        income_1_tax, income_2_tax, income_3_tax, 
                        income_4a_tax, income_4b_tax, income_5_tax, income_6_tax
                    ]
                ])
                
                total_income_display.value = f"{total_income:,.2f}"
                total_tax_display.value = f"{total_tax:,.2f}"
                page.update()
            except ValueError:
                pass
        
        # Add event listeners for auto-calculation
        for field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                      income_3_amount, income_3_tax, income_4a_amount, income_4a_tax,
                      income_4b_amount, income_4b_tax, income_5_amount, income_5_tax,
                      income_6_amount, income_6_tax]:
            field.on_change = lambda e: calculate_totals()
        
        def save_form(e):
            """Save form data to database"""
            nonlocal last_certificate_id
            try:
                # Validation
                if not all([withholder_name.value, withholder_tax_id.value, 
                           withholdee_name.value, withholdee_tax_id.value]):
                    status_text.value = "❌ กรุณากรอกข้อมูลที่จำเป็น"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                # Prepare data tuple
                data = (
                    withholder_name.value, withholder_address.value, withholder_tax_id.value, withholder_type.value or "บุคคล",
                    withholdee_name.value, withholdee_address.value, withholdee_tax_id.value, withholdee_type.value or "บุคคล",
                    certificate_book_no.value, certificate_no.value, 
                    int(sequence_in_form.value) if sequence_in_form.value else None, form_type.value,
                    float(income_1_amount.value) if (income_1_amount.value or "").strip() else 0.0,
                    float(income_1_tax.value) if (income_1_tax.value or "").strip() else 0.0,
                    float(income_2_amount.value) if (income_2_amount.value or "").strip() else 0.0,
                    float(income_2_tax.value) if (income_2_tax.value or "").strip() else 0.0,
                    float(income_3_amount.value or 0), float(income_3_tax.value or 0),
                    float(income_4a_amount.value or 0), float(income_4a_tax.value or 0),
                    float(income_4b_amount.value or 0), float(income_4b_tax.value or 0),
                    None, None,  # dividend fields
                    float(income_5_amount.value or 0), float(income_5_tax.value or 0),
                    float(income_6_amount.value or 0), float(income_6_tax.value or 0), income_6_description.value,
                    float(total_income_display.value.replace(',', '') or 0), 
                    float(total_tax_display.value.replace(',', '') or 0), total_tax_text.value,
                    float(provident_fund.value) if (provident_fund.value or "").strip() else 0.0,
                    float(social_security_fund.value) if (social_security_fund.value or "").strip() else 0.0,
                    float(retirement_mutual_fund.value) if (retirement_mutual_fund.value or "").strip() else 0.0,
                    issue_type.value, issue_type_other.value, issue_date.value or None, 
                    signatory_name.value, company_seal.value
                )
                
                certificate_id = app.save_certificate(data)
                
                if certificate_id:
                    last_certificate_id = certificate_id
                    status_text.value = f"✅ บันทึกข้อมูลเรียบร้อยแล้ว (ID: {certificate_id})"
                    status_text.color = ft.Colors.GREEN_700
                    generate_pdf_button.disabled = False
                    page.update()
                else:
                    status_text.value = "❌ ไม่สามารถบันทึกข้อมูลได้"
                    status_text.color = ft.Colors.RED_700
                    
            except Exception as ex:
                status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                status_text.color = ft.Colors.RED_700
            
            page.update()
        
        def generate_template_pdf(e):
            """Generate PDF using the exact template"""
            nonlocal last_certificate_id
            
            if not last_certificate_id:
                status_text.value = "❌ กรุณาบันทึกข้อมูลก่อนสร้าง PDF"
                status_text.color = ft.Colors.RED_700
                page.update()
                return
            
            try:
                cert_data = app.get_certificate_by_id(last_certificate_id)
                if cert_data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_filename = f"official_tax_form_{last_certificate_id}_{timestamp}.pdf"
                    success, message = app.fill_pdf_template(cert_data, pdf_filename)
                    
                    if success:
                        status_text.value = f"✅ {message}"
                        status_text.color = ft.Colors.GREEN_700
                        
                        # Show success dialog
                        def close_dialog(e):
                            dialog.open = False
                            page.update()
                        
                        dialog = ft.AlertDialog(
                            title=ft.Text("สร้าง PDF จากเทมเพลตราชการสำเร็จ! 🎯", color=ft.Colors.GREEN_700, size=18),
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.GAVEL, size=40, color=ft.Colors.BLUE_700),
                                        ft.Column([
                                            ft.Text("ไฟล์ PDF ถูกสร้างจากเทมเพลตราชการเรียบร้อยแล้ว!", weight=ft.FontWeight.BOLD),
                                            ft.Text("PDF ที่ได้จะมีรูปแบบเหมือนต้นฉบับของกรมสรรพากรทุกประการ", color=ft.Colors.BLUE_700)
                                        ], spacing=5)
                                    ], spacing=10),
                                    ft.Divider(),
                                    ft.Column([
                                        ft.Row([ft.Icon(ft.Icons.FOLDER, size=16, color=ft.Colors.BLUE_700), 
                                               ft.Text(f"ชื่อไฟล์: {pdf_filename}", size=12, weight=ft.FontWeight.BOLD)]),
                                        ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ft.Colors.BLUE_700), 
                                               ft.Text(f"ตำแหน่ง: {os.path.abspath(pdf_filename)}", size=12)]),
                                        ft.Row([ft.Icon(ft.Icons.FINGERPRINT, size=16, color=ft.Colors.BLUE_700), 
                                               ft.Text(f"ID ใบรับรอง: {last_certificate_id}", size=12)]),
                                    ], spacing=8),
                                    ft.Divider(),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("✨ คุณสมบัติพิเศษของ PDF ราชการ:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                                            ft.Text("• ใช้เทมเพลตต้นฉบับของกรมสรรพากรเป็นพื้นหลัง", size=12),
                                            ft.Text("• ข้อมูลถูกวางในตำแหน่งที่ถูกต้องตามแบบฟอร์ม", size=12),
                                            ft.Text("• สามารถใช้เป็นเอกสารราชการได้ทันที", size=12),
                                            ft.Text("• รองรับฟอนต์ไทยเพื่อความสวยงาม", size=12),
                                            ft.Text("• มีเครื่องหมายถูกในช่องที่เลือกอัตโนมัติ", size=12),
                                        ], spacing=5),
                                        bgcolor=ft.Colors.GREEN_50,
                                        padding=15,
                                        border_radius=10
                                    )
                                ], spacing=15),
                                width=600
                            ),
                            actions=[
                                ft.TextButton("🎉 ยอดเยี่ยม!", on_click=close_dialog,
                                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE))
                            ]
                        )
                        page.dialog = dialog
                        dialog.open = True
                        
                    else:
                        status_text.value = f"❌ {message}"
                        status_text.color = ft.Colors.RED_700
                else:
                    status_text.value = f"❌ ไม่พบข้อมูลใบรับรอง ID: {last_certificate_id}"
                    status_text.color = ft.Colors.RED_700
                    
            except Exception as ex:
                status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                status_text.color = ft.Colors.RED_700
            
            page.update()
        
        def clear_form(e):
            """Clear all form fields"""
            nonlocal last_certificate_id
            last_certificate_id = None
            generate_pdf_button.disabled = True
            
            # Clear all fields
            for field in [withholder_name, withholder_address, withholder_tax_id,
                          withholdee_name, withholdee_address, withholdee_tax_id,
                          certificate_book_no, certificate_no, sequence_in_form,
                          income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                          income_3_amount, income_3_tax, income_4a_amount, income_4a_tax,
                          income_4b_amount, income_4b_tax, income_5_amount, income_5_tax,
                          income_6_amount, income_6_tax, income_6_description,
                          provident_fund, social_security_fund, retirement_mutual_fund,
                          issue_type_other, issue_date, signatory_name, total_tax_text]:
                if hasattr(field, 'value'):
                    field.value = "0" if field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                                                   income_3_amount, income_3_tax, income_4a_amount, income_4a_tax,
                                                   income_4b_amount, income_4b_tax, income_5_amount, income_5_tax,
                                                   income_6_amount, income_6_tax, provident_fund, 
                                                   social_security_fund, retirement_mutual_fund] else ""
            
            for dropdown in [withholder_type, withholdee_type, form_type, issue_type]:
                dropdown.value = None
            
            company_seal.value = False
            calculate_totals()
            page.update()
        
        def view_certificates(e):
            """View saved certificates with template PDF generation"""
            certificates = app.get_all_certificates()
            
            if not certificates:
                status_text.value = "ไม่มีข้อมูลหนังสือรับรองในฐานข้อมูล"
                status_text.color = ft.Colors.ORANGE_700
                page.update()
                return
            
            columns = [
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("ผู้หักภาษี")),
                ft.DataColumn(ft.Text("ผู้ถูกหักภาษี")),
                ft.DataColumn(ft.Text("ยอดรวม")),
                ft.DataColumn(ft.Text("ภาษีหัก")),
                ft.DataColumn(ft.Text("วันที่")),
                ft.DataColumn(ft.Text("PDF เทมเพลต"))
            ]
            
            def generate_template_pdf_for_cert(certificate_id):
                try:
                    cert_data = app.get_certificate_by_id(certificate_id)
                    if cert_data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        pdf_filename = f"official_template_{certificate_id}_{timestamp}.pdf"
                        success, message = app.fill_pdf_template(cert_data, pdf_filename)
                        
                        if success:
                            status_text.value = f"✅ สร้าง PDF เทมเพลตราชการเรียบร้อย: {pdf_filename}"
                            status_text.color = ft.Colors.GREEN_700
                        else:
                            status_text.value = f"❌ {message}"
                            status_text.color = ft.Colors.RED_700
                    else:
                        status_text.value = f"❌ ไม่พบข้อมูลใบรับรอง ID: {certificate_id}"
                        status_text.color = ft.Colors.RED_700
                except Exception as ex:
                    status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                    status_text.color = ft.Colors.RED_700
                
                dialog.open = False
                page.update()
            
            rows = []
            for cert in certificates:
                pdf_button = ft.IconButton(
                    icon=ft.Icons.GAVEL,
                    tooltip="สร้าง PDF จากเทมเพลตราชการ",
                    icon_color=ft.Colors.BLUE_700,
                    on_click=lambda e, cert_id=cert[0]: generate_template_pdf_for_cert(cert_id)
                )
                
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(cert[0]))),
                    ft.DataCell(ft.Text(cert[1][:15] + "..." if len(cert[1]) > 15 else cert[1])),
                    ft.DataCell(ft.Text(cert[2][:15] + "..." if len(cert[2]) > 15 else cert[2])),
                    ft.DataCell(ft.Text(f"฿{cert[3]:,.2f}" if cert[3] else "0")),
                    ft.DataCell(ft.Text(f"฿{cert[4]:,.2f}" if cert[4] else "0")),
                    ft.DataCell(ft.Text(str(cert[5]) if cert[5] else "")),
                    ft.DataCell(pdf_button)
                ]))
            
            data_table = ft.DataTable(columns=columns, rows=rows)
            
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text(f"รายการหนังสือรับรองราชการ ({len(certificates)} รายการ)"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("🎯 คลิกปุ่มสีน้ำเงินเพื่อสร้าง PDF จากเทมเพลตราชการ", size=12, color=ft.Colors.BLUE_700),
                        data_table
                    ], scroll=ft.ScrollMode.AUTO),
                    width=1000,
                    height=600
                ),
                actions=[ft.TextButton("ปิด", on_click=close_dialog)]
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        # PDF generation button
        generate_pdf_button = ft.ElevatedButton(
            "📄 สร้าง PDF จากเทมเพลตราชการ", 
            on_click=generate_template_pdf,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
            disabled=True,
            tooltip="บันทึกข้อมูลก่อนเพื่อสร้าง PDF จากเทมเพลตราชการ"
        )
        
        return ft.Container(
            content=ft.Column([
                # Header with template info
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.GAVEL, size=40, color=ft.Colors.BLUE_700),
                            ft.Column([
                                ft.Text("ระบบใส่ข้อมูลในแบบฟอร์ม PDF ราชการ", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Official Thai Tax Form Template Filler - ใช้เทมเพลตต้นฉบับของกรมสรรพากร", size=14, color=ft.Colors.GREY_700),
                                template_status
                            ], spacing=2)
                        ]),
                        ft.Divider(height=1, color=ft.Colors.GREY_300),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.STAR, size=16, color=ft.Colors.BLUE_700),
                                    ft.Text("คุณสมบัติพิเศษ: ใส่ข้อมูลลงในแบบฟอร์ม PDF ต้นฉบับของกรมสรรพากรโดยตรง", 
                                           size=12, color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD)
                                ], spacing=5),
                                ft.Row([
                                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.GREEN_700),
                                    ft.Text("• ใช้เทมเพลตต้นฉบับเป็นพื้นหลัง • ข้อมูลวางตำแหน่งที่ถูกต้อง • รองรับฟอนต์ไทย • ใช้งานราชการได้ทันที", 
                                           size=11, color=ft.Colors.GREEN_700)
                                ], spacing=5)
                            ], spacing=5),
                            bgcolor=ft.Colors.BLUE_50,
                            padding=15,
                            border_radius=10
                        )
                    ], spacing=10),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=10,
                    padding=20,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Action buttons
                ft.Row([
                    ft.ElevatedButton("💾 บันทึกข้อมูล", on_click=save_form, 
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)),
                    generate_pdf_button,
                    ft.ElevatedButton("🗑️ เคลียร์ฟอร์ม", on_click=clear_form,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("📋 ดูรายการและสร้าง PDF", on_click=view_certificates,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True),
                
                status_text,
                ft.Divider(),
                
                # Form sections
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลผู้มีหน้าที่หักภาษี ณ ที่จ่าย", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([withholder_name, withholder_type], spacing=10),
                                withholder_address,
                                withholder_tax_id
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลผู้ถูกหักภาษี ณ ที่จ่าย", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([withholdee_name, withholdee_type], spacing=10),
                                withholdee_address,
                                withholdee_tax_id
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลเอกสารอ้างอิง", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([certificate_book_no, certificate_no, sequence_in_form], spacing=10),
                                form_type
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("รายการเงินได้และภาษีที่หัก", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("1. เงินเดือน ค่าจ้าง เบี้ยเลี้ยง โบนัส", weight=ft.FontWeight.BOLD),
                                ft.Row([income_1_amount, income_1_tax], spacing=10),
                                ft.Text("2. ค่าธรรมเนียม ค่านายหน้า", weight=ft.FontWeight.BOLD),
                                ft.Row([income_2_amount, income_2_tax], spacing=10),
                                ft.Text("3. ค่าแห่งลิขสิทธิ์", weight=ft.FontWeight.BOLD),
                                ft.Row([income_3_amount, income_3_tax], spacing=10),
                                ft.Text("4. (ก) ดอกเบี้ย", weight=ft.FontWeight.BOLD),
                                ft.Row([income_4a_amount, income_4a_tax], spacing=10),
                                ft.Text("4. (ข) เงินปันผล เงินส่วนแบ่งกำไร", weight=ft.FontWeight.BOLD),
                                ft.Row([income_4b_amount, income_4b_tax], spacing=10),
                                ft.Text("5. การจ่ายเงินได้ตามคำสั่งกรมสรรพากร", weight=ft.FontWeight.BOLD),
                                ft.Row([income_5_amount, income_5_tax], spacing=10),
                                ft.Text("6. อื่น ๆ", weight=ft.FontWeight.BOLD),
                                ft.Row([income_6_amount, income_6_tax], spacing=10),
                                income_6_description,
                                ft.Divider(height=30, color=ft.Colors.BLUE_700, thickness=2),
                                ft.Text("ยอดรวม", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                                ft.Row([total_income_display, total_tax_display], spacing=10),
                                total_tax_text
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("กองทุนต่าง ๆ", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Row([provident_fund, social_security_fund, retirement_mutual_fund], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("การออกใบรับรองและลายเซ็น", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([issue_type, issue_type_other], spacing=10),
                                ft.Row([issue_date, signatory_name], spacing=10),
                                company_seal
                            ], spacing=10),
                            padding=10
                        )
                    ]
                )
                
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def create_fill_jpg_form_tab():
        """Create the fill JPG form tab with functionality from form_tax_17.py"""
        # Initialize JPG form filler app
        try:
            from PIL import Image, ImageDraw, ImageFont
            jpg_app = ImageFormFiller()
        except Exception as e:
            # Fallback if PIL or PyMuPDF not available
            class ImageFormFiller:
                def __init__(self):
                    self.connection_string = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
                    self.template_image_path = "form.jpg"
                    self.init_database()
                
                def init_database(self):
                    conn = self.get_connection()
                    if not conn:
                        return False
                    try:
                        cursor = conn.cursor()
                        cursor.execute('''
                            CREATE TABLE IF NOT EXISTS tax_withholding_certificates (
                                id SERIAL PRIMARY KEY,
                                withholder_name VARCHAR(255) NOT NULL,
                                withholder_address TEXT NOT NULL,
                                withholder_tax_id VARCHAR(13) NOT NULL,
                                withholder_type VARCHAR(50) NOT NULL,
                                withholdee_name VARCHAR(255) NOT NULL,
                                withholdee_address TEXT NOT NULL,
                                withholdee_tax_id VARCHAR(13) NOT NULL,
                                withholdee_type VARCHAR(50) NOT NULL,
                                certificate_book_no VARCHAR(50),
                                certificate_no VARCHAR(50),
                                sequence_in_form INTEGER,
                                form_type VARCHAR(20),
                                income_type_1_amount DECIMAL(15,2) DEFAULT 0,
                                income_type_1_tax DECIMAL(15,2) DEFAULT 0,
                                income_type_2_amount DECIMAL(15,2) DEFAULT 0,
                                income_type_2_tax DECIMAL(15,2) DEFAULT 0,
                                income_type_3_amount DECIMAL(15,2) DEFAULT 0,
                                income_type_3_tax DECIMAL(15,2) DEFAULT 0,
                                income_type_4a_amount DECIMAL(15,2) DEFAULT 0,
                                income_type_4a_tax DECIMAL(15,2) DEFAULT 0,
                                income_type_4b_amount DECIMAL(15,2) DEFAULT 0,
                                income_type_4b_tax DECIMAL(15,2) DEFAULT 0,
                                dividend_credit_type VARCHAR(100),
                                dividend_tax_rate DECIMAL(5,2),
                                income_type_5_amount DECIMAL(15,2) DEFAULT 0,
                                income_type_5_tax DECIMAL(15,2) DEFAULT 0,
                                income_type_6_amount DECIMAL(15,2) DEFAULT 0,
                                income_type_6_tax DECIMAL(15,2) DEFAULT 0,
                                income_type_6_description TEXT,
                                total_income DECIMAL(15,2) DEFAULT 0,
                                total_tax_withheld DECIMAL(15,2) DEFAULT 0,
                                total_tax_withheld_text TEXT,
                                provident_fund DECIMAL(15,2) DEFAULT 0,
                                social_security_fund DECIMAL(15,2) DEFAULT 0,
                                retirement_mutual_fund DECIMAL(15,2) DEFAULT 0,
                                issue_type VARCHAR(50),
                                issue_type_other VARCHAR(100),
                                issue_date DATE,
                                signatory_name VARCHAR(255),
                                company_seal BOOLEAN DEFAULT FALSE,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            );
                        ''')
                        conn.commit()
                        return True
                    except Exception as e:
                        print(f"Database initialization error: {e}")
                        conn.rollback()
                        return False
                    finally:
                        cursor.close()
                        conn.close()
                
                def get_connection(self):
                    try:
                        import psycopg2
                        conn = psycopg2.connect(self.connection_string)
                        return conn
                    except Exception as e:
                        print(f"Database connection error: {e}")
                        return None
                
                def save_certificate(self, data):
                    conn = self.get_connection()
                    if not conn:
                        return None
                    try:
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO tax_withholding_certificates (
                                withholder_name, withholder_address, withholder_tax_id, withholder_type,
                                withholdee_name, withholdee_address, withholdee_tax_id, withholdee_type,
                                certificate_book_no, certificate_no, sequence_in_form, form_type,
                                income_type_1_amount, income_type_1_tax,
                                income_type_2_amount, income_type_2_tax,
                                income_type_3_amount, income_type_3_tax,
                                income_type_4a_amount, income_type_4a_tax,
                                income_type_4b_amount, income_type_4b_tax, dividend_credit_type, dividend_tax_rate,
                                income_type_5_amount, income_type_5_tax,
                                income_type_6_amount, income_type_6_tax, income_type_6_description,
                                total_income, total_tax_withheld, total_tax_withheld_text,
                                provident_fund, social_security_fund, retirement_mutual_fund,
                                issue_type, issue_type_other, issue_date, signatory_name, company_seal
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id;
                        ''', data)
                        certificate_id = cursor.fetchone()[0]
                        conn.commit()
                        return certificate_id
                    except Exception as e:
                        print(f"Save certificate error: {e}")
                        conn.rollback()
                        return None
                    finally:
                        cursor.close()
                        conn.close()
                
                def get_certificate_by_id(self, certificate_id):
                    conn = self.get_connection()
                    if not conn:
                        return None
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM tax_withholding_certificates WHERE id = %s", (certificate_id,))
                        result = cursor.fetchone()
                        if result:
                            cursor.execute("""
                                SELECT column_name FROM information_schema.columns 
                                WHERE table_name = 'tax_withholding_certificates' 
                                ORDER BY ordinal_position
                            """)
                            columns = [row[0] for row in cursor.fetchall()]
                            return dict(zip(columns, result))
                        return None
                    except Exception as e:
                        print(f"Get certificate error: {e}")
                        return None
                    finally:
                        cursor.close()
                        conn.close()
                
                def get_all_certificates(self):
                    conn = self.get_connection()
                    if not conn:
                        return []
                    try:
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT id, withholder_name, withholdee_name, total_income, 
                                   total_tax_withheld, issue_date, created_at
                            FROM tax_withholding_certificates
                            ORDER BY created_at DESC
                            LIMIT 100;
                        ''')
                        return cursor.fetchall()
                    except Exception as e:
                        print(f"Get certificates error: {e}")
                        return []
                    finally:
                        cursor.close()
                        conn.close()
                
                def fill_form_image(self, data, output_path):
                    """Fill form data onto background image and save as JPG"""
                    try:
                        # Create a simple JPG with text overlay
                        from PIL import Image, ImageDraw, ImageFont
                        
                        # Create a blank image as fallback
                        width, height = 2480, 3508  # A4 proportions
                        background = Image.new('RGB', (width, height), 'white')
                        draw = ImageDraw.Draw(background)
                        
                        # Try to load background image
                        if os.path.exists(self.template_image_path):
                            try:
                                background = Image.open(self.template_image_path)
                                background = background.convert('RGB')
                            except:
                                pass
                        
                        # Draw form data
                        try:
                            font = ImageFont.truetype("arial.ttf", 30)
                        except:
                            font = ImageFont.load_default()
                        
                        # Draw title
                        title = "หนังสือรับรองการหักภาษี ณ ที่จ่าย"
                        draw.text((width//2 - 200, 100), title, fill='black', font=font)
                        
                        # Draw form data
                        y_pos = 300
                        line_height = 50
                        
                        draw.text((100, y_pos), f"ผู้หักภาษี: {data.get('withholder_name', '')}", fill='black', font=font)
                        y_pos += line_height
                        draw.text((100, y_pos), f"ผู้ถูกหักภาษี: {data.get('withholdee_name', '')}", fill='black', font=font)
                        y_pos += line_height
                        draw.text((100, y_pos), f"ยอดรวม: ฿{float(data.get('total_income', 0)):,.2f}", fill='black', font=font)
                        y_pos += line_height
                        draw.text((100, y_pos), f"ภาษีหัก: ฿{float(data.get('total_tax_withheld', 0)):,.2f}", fill='black', font=font)
                        
                        # Save as JPG
                        background.save(output_path, "JPEG", quality=95)
                        return True, f"ไฟล์ JPG ถูกสร้างเรียบร้อยแล้ว: {output_path}"
                        
                    except Exception as e:
                        return False, f"เกิดข้อผิดพลาดในการสร้าง JPG: {str(e)}"
            
            jpg_app = ImageFormFiller()
        
        # Status messages
        status_text = ft.Text("พร้อมใช้งาน", size=14, color=ft.Colors.GREEN_700)
        
        # Template status
        template_status = ft.Text("กำลังตรวจสอบภาพพื้นหลัง...", size=12)
        
        def check_template():
            if os.path.exists(jpg_app.template_image_path):
                template_status.value = f"✅ พบภาพพื้นหลัง: {jpg_app.template_image_path}"
                template_status.color = ft.Colors.GREEN_700
            else:
                template_status.value = f"⚠️ ไม่พบภาพพื้นหลัง: {jpg_app.template_image_path} (จะสร้างพื้นหลังขาว)"
                template_status.color = ft.Colors.ORANGE_700
            page.update()
        
        check_template()

        # Top preview panel (A4) from form.jpg
        preview_note = ft.Text("แสดงแบบฟอร์มจาก form.jpg (A4)", size=12, color=ft.Colors.GREY_700)
        a4_preview = ft.Container(
            content=ft.Image(
                src=jpg_app.template_image_path if os.path.exists(jpg_app.template_image_path) else "",
                fit=ft.ImageFit.CONTAIN,
                width=595,
                height=842,
            ),
            width=595,
            height=842,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )
        preview_panel = ft.Container(
            content=ft.Column([preview_note, a4_preview], spacing=8),
            bgcolor=ft.Colors.GREY_50,
            padding=10,
            border_radius=8,
            margin=ft.margin.only(bottom=20)
        )
        
        # Form fields
        withholder_name = ft.TextField(label="ชื่อผู้มีหน้าที่หักภาษี", width=400)
        withholder_address = ft.TextField(label="ที่อยู่ผู้มีหน้าที่หักภาษี", width=600, multiline=True, max_lines=3)
        withholder_tax_id = ft.TextField(label="เลขประจำตัวผู้เสียภาษี (13 หลัก)", width=200, max_length=13)
        withholder_type = ft.Dropdown(
            label="ประเภท", width=200,
            options=[ft.dropdown.Option("บุคคล"), ft.dropdown.Option("นิติบุคคล"), 
                    ft.dropdown.Option("บริษัท"), ft.dropdown.Option("สมาคม"), ft.dropdown.Option("คณะบุคคล")]
        )
        
        withholdee_name = ft.TextField(label="ชื่อผู้ถูกหักภาษี", width=400)
        withholdee_address = ft.TextField(label="ที่อยู่ผู้ถูกหักภาษี", width=600, multiline=True, max_lines=3)
        withholdee_tax_id = ft.TextField(label="เลขประจำตัวผู้เสียภาษี (13 หลัก)", width=200, max_length=13)
        withholdee_type = ft.Dropdown(
            label="ประเภท", width=200,
            options=[ft.dropdown.Option("บุคคล"), ft.dropdown.Option("นิติบุคคล"), 
                    ft.dropdown.Option("บริษัท"), ft.dropdown.Option("สมาคม"), ft.dropdown.Option("คณะบุคคล")]
        )
        
        certificate_book_no = ft.TextField(label="เล่มที่", width=150)
        certificate_no = ft.TextField(label="เลขที่", width=150)
        sequence_in_form = ft.TextField(label="ลำดับที่ในแบบ", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        form_type = ft.Dropdown(
            label="ประเภทแบบ", width=200,
            options=[ft.dropdown.Option("ภ.ง.ด.1ก"), ft.dropdown.Option("ภ.ง.ด.1ก พิเศษ"), 
                    ft.dropdown.Option("ภ.ง.ด.2"), ft.dropdown.Option("ภ.ง.ด.3"),
                    ft.dropdown.Option("ภ.ง.ด.2ก"), ft.dropdown.Option("ภ.ง.ด.3ก"), ft.dropdown.Option("ภ.ง.ด.53")]
        )
        
        # Income fields
        income_1_amount = ft.TextField(label="เงินเดือน ค่าจ้าง", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_1_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_2_amount = ft.TextField(label="ค่าธรรมเนียม", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_2_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_3_amount = ft.TextField(label="ค่าลิขสิทธิ์", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_3_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_4a_amount = ft.TextField(label="ดอกเบี้ย", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_4a_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_4b_amount = ft.TextField(label="เงินปันผล", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_4b_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_5_amount = ft.TextField(label="ตามคำสั่งกรมสรรพากร", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_5_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_6_amount = ft.TextField(label="อื่น ๆ", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_6_tax = ft.TextField(label="ภาษีที่หัก", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        income_6_description = ft.TextField(label="รายละเอียดอื่น ๆ", width=300)
        
        # Fund fields
        provident_fund = ft.TextField(label="กบข./กสจ.", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        social_security_fund = ft.TextField(label="ประกันสังคม", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        retirement_mutual_fund = ft.TextField(label="กองทุนเลี้ยงชีพ", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        # Issue fields
        issue_type = ft.Dropdown(
            label="ประเภทการออกใบรับรอง", width=200,
            options=[ft.dropdown.Option("หักณที่จ่าย"), ft.dropdown.Option("ออกให้ตลอดไป"),
                    ft.dropdown.Option("ออกให้ครั้งเดียว"), ft.dropdown.Option("อื่น ๆ")]
        )
        issue_type_other = ft.TextField(label="อื่น ๆ (ระบุ)", width=200)
        issue_date = ft.TextField(label="วันที่ (YYYY-MM-DD)", width=200)
        signatory_name = ft.TextField(label="ชื่อผู้จ่ายเงิน", width=300)
        company_seal = ft.Checkbox(label="ประทับตรานิติบุคคล", value=False)
        
        # Total fields
        total_income_display = ft.TextField(label="รวมเงินที่จ่าย", width=200, read_only=True)
        total_tax_display = ft.TextField(label="รวมภาษีที่หักนำส่ง", width=200, read_only=True)
        total_tax_text = ft.TextField(label="รวมภาษีที่หักนำส่ง (ตัวอักษร)", width=400)
        
        # Store last certificate ID
        last_certificate_id = None
        
        def calculate_totals():
            """Calculate total income and tax"""
            try:
                total_income = sum([
                    float(field.value or 0) for field in [
                        income_1_amount, income_2_amount, income_3_amount, 
                        income_4a_amount, income_4b_amount, income_5_amount, income_6_amount
                    ]
                ])
                
                total_tax = sum([
                    float(field.value or 0) for field in [
                        income_1_tax, income_2_tax, income_3_tax, 
                        income_4a_tax, income_4b_tax, income_5_tax, income_6_tax
                    ]
                ])
                
                total_income_display.value = f"{total_income:,.2f}"
                total_tax_display.value = f"{total_tax:,.2f}"
                page.update()
            except ValueError:
                pass
        
        # Add event listeners for auto-calculation
        for field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                      income_3_amount, income_3_tax, income_4a_amount, income_4a_tax,
                      income_4b_amount, income_4b_tax, income_5_amount, income_5_tax,
                      income_6_amount, income_6_tax]:
            field.on_change = lambda e: calculate_totals()
        
        def save_form(e):
            """Save form data to database"""
            nonlocal last_certificate_id
            try:
                # Validation
                if not all([withholder_name.value, withholder_tax_id.value, 
                           withholdee_name.value, withholdee_tax_id.value]):
                    status_text.value = "❌ กรุณากรอกข้อมูลที่จำเป็น"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                # Prepare data tuple
                data = (
                    withholder_name.value, withholder_address.value, withholder_tax_id.value, withholder_type.value or "บุคคล",
                    withholdee_name.value, withholdee_address.value, withholdee_tax_id.value, withholdee_type.value or "บุคคล",
                    certificate_book_no.value, certificate_no.value, 
                    int(sequence_in_form.value) if sequence_in_form.value else None, form_type.value,
                    float(income_1_amount.value) if (income_1_amount.value or "").strip() else 0.0,
                    float(income_1_tax.value) if (income_1_tax.value or "").strip() else 0.0,
                    float(income_2_amount.value) if (income_2_amount.value or "").strip() else 0.0,
                    float(income_2_tax.value) if (income_2_tax.value or "").strip() else 0.0,
                    float(income_3_amount.value or 0), float(income_3_tax.value or 0),
                    float(income_4a_amount.value or 0), float(income_4a_tax.value or 0),
                    float(income_4b_amount.value or 0), float(income_4b_tax.value or 0),
                    None, None,  # dividend fields
                    float(income_5_amount.value or 0), float(income_5_tax.value or 0),
                    float(income_6_amount.value or 0), float(income_6_tax.value or 0), income_6_description.value,
                    float(total_income_display.value.replace(',', '') or 0), 
                    float(total_tax_display.value.replace(',', '') or 0), total_tax_text.value,
                    float(provident_fund.value) if (provident_fund.value or "").strip() else 0.0,
                    float(social_security_fund.value) if (social_security_fund.value or "").strip() else 0.0,
                    float(retirement_mutual_fund.value) if (retirement_mutual_fund.value or "").strip() else 0.0,
                    issue_type.value, issue_type_other.value, issue_date.value or None, 
                    signatory_name.value, company_seal.value
                )
                
                certificate_id = jpg_app.save_certificate(data)
                
                if certificate_id:
                    last_certificate_id = certificate_id
                    status_text.value = f"✅ บันทึกข้อมูลเรียบร้อยแล้ว (ID: {certificate_id})"
                    status_text.color = ft.Colors.GREEN_700
                    generate_jpg_button.disabled = False
                    page.update()
                else:
                    status_text.value = "❌ ไม่สามารถบันทึกข้อมูลได้"
                    status_text.color = ft.Colors.RED_700
                    
            except Exception as ex:
                status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                status_text.color = ft.Colors.RED_700
            
            page.update()
        
        def generate_jpg_image(e):
            """Generate JPG image from form data"""
            nonlocal last_certificate_id
            
            if not last_certificate_id:
                status_text.value = "❌ กรุณาบันทึกข้อมูลก่อนสร้าง JPG"
                status_text.color = ft.Colors.RED_700
                page.update()
                return
            
            try:
                cert_data = jpg_app.get_certificate_by_id(last_certificate_id)
                if cert_data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    jpg_filename = f"tax_form_filled_{last_certificate_id}_{timestamp}.jpg"
                    success, message = jpg_app.fill_form_image(cert_data, jpg_filename)
                    
                    if success:
                        status_text.value = f"✅ {message}"
                        status_text.color = ft.Colors.GREEN_700
                        
                        # Show success dialog with image info
                        def close_dialog(e):
                            dialog.open = False
                            page.update()
                        
                        dialog = ft.AlertDialog(
                            title=ft.Text("สร้างไฟล์ JPG สำเร็จ! 🖼️", color=ft.Colors.GREEN_700, size=18),
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.IMAGE, size=40, color=ft.Colors.BLUE_700),
                                        ft.Column([
                                            ft.Text("ไฟล์ JPG ใบรับรองการหักภาษี ณ ที่จ่าย ถูกสร้างเรียบร้อยแล้ว!", weight=ft.FontWeight.BOLD),
                                            ft.Text("ใช้ภาพพื้นหลังต้นฉบับของกรมสรรพากรเป็นฐาน", color=ft.Colors.BLUE_700)
                                        ], spacing=5)
                                    ], spacing=10),
                                    ft.Divider(),
                                    ft.Column([
                                        ft.Row([ft.Icon(ft.Icons.FOLDER, size=16, color=ft.Colors.BLUE_700), 
                                               ft.Text(f"ชื่อไฟล์: {jpg_filename}", size=12, weight=ft.FontWeight.BOLD)]),
                                        ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ft.Colors.BLUE_700), 
                                               ft.Text(f"ตำแหน่ง: {os.path.abspath(jpg_filename)}", size=12)]),
                                        ft.Row([ft.Icon(ft.Icons.FINGERPRINT, size=16, color=ft.Colors.BLUE_700), 
                                               ft.Text(f"ID ใบรับรอง: {last_certificate_id}", size=12)]),
                                        ft.Row([ft.Icon(ft.Icons.HIGH_QUALITY, size=16, color=ft.Colors.BLUE_700), 
                                               ft.Text("คุณภาพ: High Resolution", size=12)]),
                                    ], spacing=8),
                                    ft.Divider(),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("🎨 คุณสมบัติของไฟล์ JPG:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                                            ft.Text("• ใช้ภาพพื้นหลังต้นฉบับของกรมสรรพากร", size=12),
                                            ft.Text("• ข้อมูลวางในตำแหน่งที่แม่นยำ", size=12),
                                            ft.Text("• คุณภาพสูงเหมาะสำหรับการพิมพ์", size=12),
                                            ft.Text("• เครื่องหมายถูกในช่องที่เลือกอัตโนมัติ", size=12),
                                            ft.Text("• รองรับฟอนต์ไทยเพื่อความสวยงาม", size=12),
                                            ft.Text("• ใช้เป็นเอกสารราชการได้ทันที", size=12),
                                        ], spacing=5),
                                        bgcolor=ft.Colors.GREEN_50,
                                        padding=15,
                                        border_radius=10
                                    )
                                ], spacing=15),
                                width=600
                            ),
                            actions=[
                                ft.TextButton("🎉 เยี่ยมมาก!", on_click=close_dialog,
                                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE))
                            ]
                        )
                        page.dialog = dialog
                        dialog.open = True
                        
                    else:
                        status_text.value = f"❌ {message}"
                        status_text.color = ft.Colors.RED_700
                else:
                    status_text.value = f"❌ ไม่พบข้อมูลใบรับรอง ID: {last_certificate_id}"
                    status_text.color = ft.Colors.RED_700
                    
            except Exception as ex:
                status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                status_text.color = ft.Colors.RED_700
            
            page.update()
        
        def clear_form(e):
            """Clear all form fields"""
            nonlocal last_certificate_id
            last_certificate_id = None
            generate_jpg_button.disabled = True
            
            # Clear all fields
            for field in [withholder_name, withholder_address, withholder_tax_id,
                          withholdee_name, withholdee_address, withholdee_tax_id,
                          certificate_book_no, certificate_no, sequence_in_form,
                          income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                          income_3_amount, income_3_tax, income_4a_amount, income_4a_tax,
                          income_4b_amount, income_4b_tax, income_5_amount, income_5_tax,
                          income_6_amount, income_6_tax, income_6_description,
                          provident_fund, social_security_fund, retirement_mutual_fund,
                          issue_type_other, issue_date, signatory_name, total_tax_text]:
                if hasattr(field, 'value'):
                    field.value = "0" if field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                                                   income_3_amount, income_3_tax, income_4a_amount, income_4a_tax,
                                                   income_4b_amount, income_4b_tax, income_5_amount, income_5_tax,
                                                   income_6_amount, income_6_tax, provident_fund, 
                                                   social_security_fund, retirement_mutual_fund] else ""
            
            for dropdown in [withholder_type, withholdee_type, form_type, issue_type]:
                dropdown.value = None
            
            company_seal.value = False
            calculate_totals()
            page.update()
        
        def view_certificates(e):
            """View saved certificates with JPG generation option"""
            certificates = jpg_app.get_all_certificates()
            
            if not certificates:
                status_text.value = "ไม่มีข้อมูลหนังสือรับรองในฐานข้อมูล"
                status_text.color = ft.Colors.ORANGE_700
                page.update()
                return
            
            columns = [
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("ผู้หักภาษี")),
                ft.DataColumn(ft.Text("ผู้ถูกหักภาษี")),
                ft.DataColumn(ft.Text("ยอดรวม")),
                ft.DataColumn(ft.Text("ภาษีหัก")),
                ft.DataColumn(ft.Text("วันที่")),
                ft.DataColumn(ft.Text("สร้าง JPG"))
            ]
            
            def generate_jpg_for_cert(certificate_id):
                try:
                    cert_data = jpg_app.get_certificate_by_id(certificate_id)
                    if cert_data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        jpg_filename = f"tax_form_image_{certificate_id}_{timestamp}.jpg"
                        success, message = jpg_app.fill_form_image(cert_data, jpg_filename)
                        
                        if success:
                            status_text.value = f"✅ สร้าง JPG เรียบร้อย: {jpg_filename}"
                            status_text.color = ft.Colors.GREEN_700
                        else:
                            status_text.value = f"❌ {message}"
                            status_text.color = ft.Colors.RED_700
                    else:
                        status_text.value = f"❌ ไม่พบข้อมูลใบรับรอง ID: {certificate_id}"
                        status_text.color = ft.Colors.RED_700
                except Exception as ex:
                    status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                    status_text.color = ft.Colors.RED_700
                
                dialog.open = False
                page.update()
            
            rows = []
            for cert in certificates:
                jpg_button = ft.IconButton(
                    icon=ft.Icons.IMAGE,
                    tooltip="สร้าง JPG",
                    icon_color=ft.Colors.BLUE_700,
                    on_click=lambda e, cert_id=cert[0]: generate_jpg_for_cert(cert_id)
                )
                
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(cert[0]))),
                    ft.DataCell(ft.Text(cert[1][:15] + "..." if len(cert[1]) > 15 else cert[1])),
                    ft.DataCell(ft.Text(cert[2][:15] + "..." if len(cert[2]) > 15 else cert[2])),
                    ft.DataCell(ft.Text(f"฿{cert[3]:,.2f}" if cert[3] else "0")),
                    ft.DataCell(ft.Text(f"฿{cert[4]:,.2f}" if cert[4] else "0")),
                    ft.DataCell(ft.Text(str(cert[5]) if cert[5] else "")),
                    ft.DataCell(jpg_button)
                ]))
            
            data_table = ft.DataTable(columns=columns, rows=rows)
            
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text(f"รายการหนังสือรับรอง ({len(certificates)} รายการ)"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("🖼️ คลิกปุ่มสีฟ้าเพื่อสร้างไฟล์ JPG จากภาพพื้นหลังต้นฉบับ", size=12, color=ft.Colors.BLUE_700),
                        data_table
                    ], scroll=ft.ScrollMode.AUTO),
                    width=1000,
                    height=600
                ),
                actions=[ft.TextButton("ปิด", on_click=close_dialog)]
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        # JPG generation button
        generate_jpg_button = ft.ElevatedButton(
            "🖼️ สร้าง JPG จากภาพพื้นหลัง", 
            on_click=generate_jpg_image,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
            disabled=True,
            tooltip="บันทึกข้อมูลก่อนเพื่อสร้างไฟล์ JPG"
        )
        
        return ft.Container(
            content=ft.Column([
                # Header with image info and preview
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.IMAGE, size=40, color=ft.Colors.BLUE_700),
                            ft.Column([
                                ft.Text("ระบบสร้าง JPG จากแบบฟอร์มภาษี", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Thai Tax Form JPG Generator - ใช้ภาพพื้นหลังต้นฉบับของกรมสรรพากร", size=14, color=ft.Colors.GREY_700),
                                template_status
                            ], spacing=2)
                        ]),
                        ft.Divider(height=1, color=ft.Colors.GREY_300),
                        preview_panel,
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.HIGH_QUALITY, size=16, color=ft.Colors.BLUE_700),
                                    ft.Text("คุณสมบัติพิเศษ: สร้างไฟล์ JPG คุณภาพสูงจากภาพพื้นหลังต้นฉบับ", 
                                           size=12, color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD)
                                ], spacing=5),
                                ft.Row([
                                    ft.Icon(ft.Icons.VERIFIED, size=16, color=ft.Colors.GREEN_700),
                                    ft.Text("• ใช้ภาพต้นฉบับ • วางข้อมูลแม่นยำ • คุณภาพ High-Res • เครื่องหมายถูกอัตโนมัติ • ใช้งานราชการได้", 
                                           size=11, color=ft.Colors.GREEN_700)
                                ], spacing=5)
                            ], spacing=5),
                            bgcolor=ft.Colors.BLUE_50,
                            padding=15,
                            border_radius=10
                        )
                    ], spacing=10),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=10,
                    padding=20,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Action buttons
                ft.Row([
                    ft.ElevatedButton("💾 บันทึกข้อมูล", on_click=save_form, 
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)),
                    generate_jpg_button,
                    ft.ElevatedButton("🗑️ เคลียร์ฟอร์ม", on_click=clear_form,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("📋 ดูรายการและสร้าง JPG", on_click=view_certificates,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True),
                
                status_text,
                ft.Divider(),
                
                # Form sections
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลผู้มีหน้าที่หักภาษี ณ ที่จ่าย", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([withholder_name, withholder_type], spacing=10),
                                withholder_address,
                                withholder_tax_id
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลผู้ถูกหักภาษี ณ ที่จ่าย", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([withholdee_name, withholdee_type], spacing=10),
                                withholdee_address,
                                withholdee_tax_id
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลเอกสารอ้างอิง", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([certificate_book_no, certificate_no, sequence_in_form], spacing=10),
                                form_type
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("รายการเงินได้และภาษีที่หัก", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([income_1_amount, income_1_tax], spacing=10),
                                ft.Row([income_2_amount, income_2_tax], spacing=10),
                                ft.Row([income_3_amount, income_3_tax], spacing=10),
                                ft.Row([income_4a_amount, income_4a_tax], spacing=10),
                                ft.Row([income_4b_amount, income_4b_tax], spacing=10),
                                ft.Row([income_5_amount, income_5_tax], spacing=10),
                                ft.Row([income_6_amount, income_6_tax], spacing=10),
                                income_6_description,
                                ft.Divider(),
                                ft.Row([total_income_display, total_tax_display], spacing=10),
                                total_tax_text
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("กองทุนและประกัน", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Row([provident_fund, social_security_fund, retirement_mutual_fund], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("การออกใบรับรองและลายเซ็น", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([issue_type, issue_type_other], spacing=10),
                                ft.Row([issue_date, signatory_name], spacing=10),
                                company_seal
                            ], spacing=10),
                            padding=10
                        )
                    ]
                )
                
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def create_crystal_report_tab():
        print("🚀 create_crystal_report_tab() called - initializing Crystal Report tab")
        try:
            # Initialize crystal report renderer
            crystal_renderer = CrystalReportStyleRenderer()
            print("✅ CrystalReportStyleRenderer initialized successfully")
        except Exception as ex:
            print(f"❌ Error initializing CrystalReportStyleRenderer: {ex}")
            import traceback
            traceback.print_exc()
        
        # Status messages
        status_text = ft.Text("พร้อมใช้งาน", size=14, color=ft.Colors.GREEN_700)
        
        # Template status
        template_status = ft.Text("กำลังตรวจสอบเทมเพลต...", size=12)
        
        # Form fields for withholder data
        withholder_name = ft.TextField(label="ชื่อผู้มีหน้าที่หักภาษี", width=400)
        withholder_address = ft.TextField(label="ที่อยู่ผู้มีหน้าที่หักภาษี", width=600, multiline=True, max_lines=3)
        withholder_tax_id = ft.TextField(label="เลขประจำตัวผู้เสียภาษี", width=200, max_length=13)
        
        # Initialize pending_withholder_import_data for this tab
        pending_withholder_import_data = None
        
        # Import required modules at the top of the function
        import os
        import json
        import sys
        
        # PDF preview variables
        selected_pdf_path = os.path.join(os.getcwd(), "form.pdf")
        pdf_preview_img = None

        # UI controls for PDF preview
        pdf_path_text_control = ft.Text(value=f"ตำแหน่งไฟล์: {selected_pdf_path}", size=11, color=ft.Colors.GREY_600)
        pdf_image_control = ft.Text("ไม่พบ form.pdf หรือไม่สามารถแสดงตัวอย่างได้", color=ft.Colors.ORANGE_700)
        
        # Container references for real-time updates
        main_pdf_container = ft.Container(
            content=pdf_image_control,
            width=595,
            height=842,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5,
            padding=10,
            alignment=ft.alignment.center
        )
        coordinate_test_container = ft.Container()
        
        def check_template():
            if os.path.exists(crystal_renderer.template_image_path):
                template_status.value = f"✅ พบภาพพื้นหลัง: {crystal_renderer.template_image_path}"
                template_status.color = ft.Colors.GREEN_700
            elif os.path.exists(crystal_renderer.template_pdf_path):
                template_status.value = f"🔄 พบ PDF เทมเพลต: {crystal_renderer.template_pdf_path}"
                template_status.color = ft.Colors.BLUE_700
            else:
                template_status.value = f"⚠️ ไม่พบเทมเพลต (จะใช้โหมดโปร่งใส)"
                template_status.color = ft.Colors.ORANGE_700
            page.update()
        
        check_template()
        
        # Auto-fill withholder data from saved settings
        def auto_fill_withholder_data():
            """โหลดข้อมูลผู้หักภาษีที่บันทึกไว้มาเติมในฟอร์ม"""
            nonlocal pending_withholder_import_data
            try:
                conn = psycopg2.connect("postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require")
                cur = conn.cursor()
                
                # Get saved withholder data
                cur.execute("SELECT setting_value FROM withholder_settings WHERE setting_key = 'checkbox_states'")
                result = cur.fetchone()
                
                if result:
                    settings = result[0]
                    withholder_data = settings.get("selected_withholder", {})
                    
                    if withholder_data:
                        # Update status to show autofill success
                        status_text.value = f"✅ โหลดข้อมูลผู้หักภาษี: {withholder_data.get('withholder_name', 'N/A')}"
                        status_text.color = ft.Colors.GREEN_700
                        page.update()
                        
                        # Store data for use in form filling
                        pending_withholder_import_data = withholder_data
                        
                        # Update the page to reflect the loaded data
                        page.update()
                        
                        return True
                        
            except Exception as ex:
                print(f"Auto-fill withholder data error: {ex}")
            finally:
                try:
                    if 'cur' in locals():
                        cur.close()
                    if 'conn' in locals():
                        conn.close()
                except Exception:
                    pass
            return False
        
        # Run auto-fill after a short delay
        import threading
        def delayed_auto_fill():
            import time
            time.sleep(1.0)  # Wait for UI to be ready
            auto_fill_withholder_data()
        
        threading.Thread(target=delayed_auto_fill, daemon=True).start()
        
        # Auto-fill from pending data if available
        def auto_fill_from_pending_data():
            """โหลดข้อมูลจาก dashboard_to_crystal_data หรือ temp file มาเติมในฟอร์มทันที"""
            try:
                # วิธีใหม่: อ่านข้อมูลจาก dashboard_to_crystal_data
                dashboard_data = None
                
                print(f"🔍 Checking dashboard_to_crystal_data: {dashboard_data}")
                
                # ตรวจสอบข้อมูลจากหลายแหล่ง
                if not dashboard_data:
                    # ลองตรวจสอบจาก global variable อีกครั้ง
                    dashboard_data = globals().get('dashboard_to_crystal_data', None)
                    print(f"🔍 Checking global dashboard_to_crystal_data: {dashboard_data}")
                

                
                # วิธีใหม่: ลองอ่านข้อมูลจาก temp file
                if not dashboard_data:
                    temp_file_path = os.path.join(os.getcwd(), "temp_dashboard_data.json")
                    print(f"🔍 Checking temp file: {temp_file_path}")
                    
                    if os.path.exists(temp_file_path):
                        try:
                            with open(temp_file_path, 'r', encoding='utf-8') as f:
                                try:
                                    dashboard_data = json.load(f)
                                except json.JSONDecodeError as json_err:
                                    print(f"❌ JSON decode error: {json_err}")
                                    print("🔧 Recreating temp file...")
                                    # ลบไฟล์เสียและข้าม
                                    import os
                                    os.remove(temp_file_path)
                                    dashboard_data = None
                            print(f"💾 Successfully loaded data from temp file: {dashboard_data}")
                        except Exception as file_ex:
                            print(f"❌ Failed to load from temp file: {file_ex}")
                            dashboard_data = None
                    else:
                        print("⚠️ Temp file does not exist")
                
                if dashboard_data:
                    payload = dashboard_data
                    print(f"📦 Payload received from dashboard: {payload}")
                    
                    # ตรวจสอบว่าข้อมูลมีค่าที่ถูกต้องหรือไม่
                    if not payload.get('withholder_name') and not payload.get('withholder_address') and not payload.get('withholder_tax_id'):
                        print("⚠️ Dashboard data exists but has no valid content")
                        return False
                    
                    # เติมข้อมูลในฟอร์ม
                    if payload.get('withholder_name'):
                        withholder_name.value = payload['withholder_name']
                        print(f"✅ Set withholder_name: {payload['withholder_name']}")
                    if payload.get('withholder_address'):
                        withholder_address.value = payload['withholder_address']
                        print(f"✅ Set withholder_address: {payload['withholder_address']}")
                    if payload.get('withholder_tax_id'):
                        withholder_tax_id.value = payload['withholder_tax_id']
                        print(f"✅ Set withholder_tax_id: {payload['withholder_tax_id']}")
                    
                    # Update status
                    status_text.value = f"✅ โหลดข้อมูลผู้หักภาษีจาก Dashboard: {payload.get('withholder_name', 'N/A')}"
                    status_text.color = ft.Colors.GREEN_700
                    page.update()
                    
                    print("✅ Auto-filled withholder data from dashboard successfully")
                    return True
                else:
                    print("⚠️ No dashboard_to_crystal_data available from any source")
                    
            except Exception as ex:
                print(f"❌ Auto-fill from dashboard data error: {ex}")
                import traceback
                traceback.print_exc()
            return False
        
        # Run auto-fill from pending data after a short delay
        def delayed_pending_auto_fill():
            import time
            print("⏰ delayed_pending_auto_fill started - waiting 1.0 seconds...")
            time.sleep(1.0)  # Wait for UI to be ready
            
            # Try multiple times to get the data
            max_retries = 3
            for attempt in range(max_retries):
                print(f"⏰ Attempt {attempt + 1}/{max_retries} - calling auto_fill_from_pending_data...")
                result = auto_fill_from_pending_data()
                print(f"⏰ auto_fill_from_pending_data result: {result}")
                
                if result:
                    print("✅ Auto-fill successful, no need for more attempts")
                    break
                else:
                    if attempt < max_retries - 1:
                        print(f"⏰ Auto-fill failed, waiting 0.5 seconds before retry...")
                        time.sleep(0.5)
                    else:
                        print("❌ Auto-fill failed after all attempts")
        
        print("🧵 Starting delayed_pending_auto_fill thread...")
        threading.Thread(target=delayed_pending_auto_fill, daemon=True).start()
        print("✅ delayed_pending_auto_fill thread started")
        

        
        def rasterize_pdf_to_png(pdf_path):
            """Convert PDF first page to PNG for preview"""
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(pdf_path)
                page = doc[0]
                pix = page.get_pixmap()
                temp_png = os.path.join(os.getcwd(), "temp_pdf_preview.png")
                pix.save(temp_png)
                doc.close()
                return temp_png
            except ImportError:
                return None
            except Exception:
                return None
        
        def update_pdf_preview():
            """Update PDF preview image"""
            nonlocal pdf_preview_img, pdf_image_control, main_pdf_container
            if os.path.exists(selected_pdf_path):
                pdf_preview_img = rasterize_pdf_to_png(selected_pdf_path)
                if pdf_preview_img:
                    pdf_image_control = ft.Image(src=pdf_preview_img, fit=ft.ImageFit.CONTAIN, width=595, height=842)
                else:
                    pdf_image_control = ft.Text("ไม่สามารถแสดงตัวอย่าง PDF ได้ (ติดตั้ง PyMuPDF เพื่อดูตัวอย่าง)", color=ft.Colors.ORANGE_700)
            else:
                pdf_image_control = ft.Text("ไม่พบ form.pdf หรือไม่สามารถแสดงตัวอย่างได้", color=ft.Colors.ORANGE_700)
            
            # Update the main container with new content (only if it has been added to page)
            main_pdf_container.content = pdf_image_control
            # Use try-catch for update to prevent errors during initialization
            try:
                main_pdf_container.update()
            except:
                pass  # Container not added to page yet
        
        def reset_pdf_preview(e):
            """Reset to original PDF preview without overlay"""
            nonlocal pdf_preview_img, pdf_image_control, coordinate_test_viewer, main_pdf_container
            
            # Reset main PDF preview
            update_pdf_preview()
            
            # Update main container with original image
            if pdf_image_control:
                main_pdf_container.content = pdf_image_control
                try:
                    main_pdf_container.update()
                except:
                    pass  # Container might not be added to page yet
            
            # Reset coordinate test viewer
            coordinate_test_viewer.content = ft.Text("คลิก 'ทดสอบ' เพื่อดูตำแหน่งพิกัด", 
                                                   size=12, color=ft.Colors.GREY_500, 
                                                   text_align=ft.TextAlign.CENTER)
            try:
                coordinate_test_viewer.update()
            except:
                pass  # Container might not be added to page yet
            
            status_text.value = "✅ รีเซ็ตแสดงแบบฟอร์ม PDF ต้นฉบับแล้ว"
            status_text.color = ft.Colors.GREEN_700
            page.update()
        
        # Coordinate adjustment controls
        coordinate_fields = {}
        coordinate_tiles = {}

        # --- Database helpers for coordinate persistence ---
        DB_CONN_STR = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"

        def get_db_connection_for_coords():
            try:
                return psycopg2.connect(DB_CONN_STR)
            except Exception as db_ex:
                print(f"Coordinate DB connection error: {db_ex}")
                return None

        def ensure_coordinate_table():
            conn = get_db_connection_for_coords()
            if not conn:
                return False
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS coordinate (
                        field_id TEXT PRIMARY KEY,
                        x INTEGER NOT NULL,
                        y INTEGER NOT NULL,
                        size INTEGER NOT NULL,
                        updated_at TIMESTAMPTZ DEFAULT now()
                    );
                    """
                )
                conn.commit()
                return True
            except Exception as ex:
                print(f"Ensure coordinate table error: {ex}")
                return False
            finally:
                try:
                    cur.close()
                    conn.close()
                except:
                    pass

        def save_coordinates_to_db():
            conn = get_db_connection_for_coords()
            if not conn:
                raise RuntimeError("ไม่สามารถเชื่อมต่อฐานข้อมูลเพื่อบันทึกพิกัดได้")
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS coordinate (
                        field_id TEXT PRIMARY KEY,
                        x INTEGER NOT NULL,
                        y INTEGER NOT NULL,
                        size INTEGER NOT NULL,
                        updated_at TIMESTAMPTZ DEFAULT now()
                    );
                    """
                )
                upsert_sql = (
                    "INSERT INTO coordinate(field_id, x, y, size, updated_at) VALUES (%s,%s,%s,%s, now()) "
                    "ON CONFLICT(field_id) DO UPDATE SET x=EXCLUDED.x, y=EXCLUDED.y, size=EXCLUDED.size, updated_at=now()"
                )
                for field_id, controls in coordinate_fields.items():
                    x_val = int(controls['x'].value)
                    y_val = int(controls['y'].value)
                    size_val = int(controls['size'].value)
                    cur.execute(upsert_sql, (field_id, x_val, y_val, size_val))
                conn.commit()
            finally:
                try:
                    cur.close()
                    conn.close()
                except:
                    pass

        def load_coordinates_from_db_initial():
            conn = get_db_connection_for_coords()
            if not conn:
                return False
            try:
                cur = conn.cursor()
                cur.execute("SELECT field_id, x, y, size FROM coordinate")
                rows = cur.fetchall()
                changed_any = False
                for field_id, x_val, y_val, size_val in rows:
                    if field_id in coordinate_fields:
                        coordinate_fields[field_id]['x'].value = str(x_val)
                        coordinate_fields[field_id]['y'].value = str(y_val)
                        coordinate_fields[field_id]['size'].value = str(size_val)
                        changed_any = True
                if changed_any:
                    try:
                        page.update()
                    except:
                        pass
                return changed_any
            except Exception as ex:
                print(f"Load coordinates error: {ex}")
                return False
            finally:
                try:
                    cur.close()
                    conn.close()
                except:
                    pass
        
        def create_coordinate_controls():
            """Create coordinate adjustment controls for each field"""
            nonlocal coordinate_fields
            
            field_configs = [
                ("withholder_name", "ชื่อผู้มีหน้าที่หักภาษี", 120, 150, 10),
                ("withholder_address", "ที่อยู่ผู้มีหน้าที่หักภาษี", 120, 175, 8),
                ("withholder_tax_id", "เลขประจำตัวผู้เสียภาษี (ผู้หัก)", 120, 200, 10),
                ("withholdee_name", "ชื่อผู้ถูกหักภาษี", 120, 280, 10),
                ("withholdee_address", "ที่อยู่ผู้ถูกหักภาษี", 120, 305, 8),
                ("withholdee_tax_id", "เลขประจำตัวผู้เสียภาษี (ผู้ถูกหัก)", 120, 330, 10),
                ("certificate_book_no", "เล่มที่", 400, 120, 10),
                ("certificate_no", "เลขที่", 500, 120, 10),
                ("form_type", "ประเภทแบบ", 400, 140, 10),
                ("income_1_amount", "เงินเดือน - จำนวน", 280, 400, 10),
                ("income_1_tax", "เงินเดือน - ภาษี", 380, 400, 10),
                ("income_2_amount", "ค่าธรรมเนียม - จำนวน", 280, 425, 10),
                ("income_2_tax", "ค่าธรรมเนียม - ภาษี", 380, 425, 10),
                ("total_income", "รวมเงินที่จ่าย", 280, 480, 12),
                ("total_tax", "รวมภาษีหัก", 380, 480, 12),
                ("total_tax_text", "ตัวอักษร", 120, 510, 10),
                ("provident_fund", "กบข.", 280, 560, 10),
                ("social_security_fund", "ประกันสังคม", 380, 560, 10),
                ("retirement_mutual_fund", "กองทุนเลี้ยงชีพ", 480, 560, 10),
                ("issue_date", "วันที่", 400, 620, 10),
                ("signatory_name", "ผู้จ่ายเงิน", 400, 670, 10),
                ("fee_payment_date", "วันที่ชำระค่าธรรมเนียม", 480, 620, 10),
                # New dynamic card fields (เลขที่บัตร 1–10)
                ("card_number_1", "เลขที่บัตร 1", 120, 530, 10),
                ("card_number_2", "เลขที่บัตร 2", 180, 530, 10),
                ("card_number_3", "เลขที่บัตร 3", 240, 530, 10),
                ("card_number_4", "เลขที่บัตร 4", 300, 530, 10),
                ("card_number_5", "เลขที่บัตร 5", 360, 530, 10),
                ("card_number_6", "เลขที่บัตร 6", 420, 530, 10),
                ("card_number_7", "เลขที่บัตร 7", 480, 530, 10),
                ("card_number_8", "เลขที่บัตร 8", 540, 530, 10),
                ("card_number_9", "เลขที่บัตร 9", 600, 530, 10),
                ("card_number_10", "เลขที่บัตร 10", 660, 530, 10),
                # 13-digit ID positions for withholdee (ผู้ถูกหัก) - default row just below
                ("withholdee_id_1", "ผู้ถูกหัก 1", 120, 540, 10),
                ("withholdee_id_2", "ผู้ถูกหัก 2", 156, 540, 10),
                ("withholdee_id_3", "ผู้ถูกหัก 3", 192, 540, 10),
                ("withholdee_id_4", "ผู้ถูกหัก 4", 228, 540, 10),
                ("withholdee_id_5", "ผู้ถูกหัก 5", 264, 540, 10),
                ("withholdee_id_6", "ผู้ถูกหัก 6", 300, 540, 10),
                ("withholdee_id_7", "ผู้ถูกหัก 7", 336, 540, 10),
                ("withholdee_id_8", "ผู้ถูกหัก 8", 372, 540, 10),
                ("withholdee_id_9", "ผู้ถูกหัก 9", 408, 540, 10),
                ("withholdee_id_10", "ผู้ถูกหัก 10", 444, 540, 10),
                ("withholdee_id_11", "ผู้ถูกหัก 11", 480, 540, 10),
                ("withholdee_id_12", "ผู้ถูกหัก 12", 516, 540, 10),
                ("withholdee_id_13", "ผู้ถูกหัก 13", 552, 540, 10),
                # 13-digit ID positions for withholder (ผู้หัก) - default row below
                ("withholder_id_1", "ผู้หัก 1", 120, 560, 10),
                ("withholder_id_2", "ผู้หัก 2", 156, 560, 10),
                ("withholder_id_3", "ผู้หัก 3", 192, 560, 10),
                ("withholder_id_4", "ผู้หัก 4", 228, 560, 10),
                ("withholder_id_5", "ผู้หัก 5", 264, 560, 10),
                ("withholder_id_6", "ผู้หัก 6", 300, 560, 10),
                ("withholder_id_7", "ผู้หัก 7", 336, 560, 10),
                ("withholder_id_8", "ผู้หัก 8", 372, 560, 10),
                ("withholder_id_9", "ผู้หัก 9", 408, 560, 10),
                ("withholder_id_10", "ผู้หัก 10", 444, 560, 10),
                ("withholder_id_11", "ผู้หัก 11", 480, 560, 10),
                ("withholder_id_12", "ผู้หัก 12", 516, 560, 10),
                ("withholder_id_13", "ผู้หัก 13", 552, 560, 10),
                # Salary digit positions 1-10
                ("salary_pos_1", "เงินเดือน-ตำแหน่ง 1", 120, 395, 10),
                ("salary_pos_2", "เงินเดือน-ตำแหน่ง 2", 170, 395, 10),
                ("salary_pos_3", "เงินเดือน-ตำแหน่ง 3", 220, 395, 10),
                ("salary_pos_4", "เงินเดือน-ตำแหน่ง 4", 270, 395, 10),
                ("salary_pos_5", "เงินเดือน-ตำแหน่ง 5", 320, 395, 10),
                ("salary_pos_6", "เงินเดือน-ตำแหน่ง 6", 370, 395, 10),
                ("salary_pos_7", "เงินเดือน-ตำแหน่ง 7", 420, 395, 10),
                ("salary_pos_8", "เงินเดือน-ตำแหน่ง 8", 470, 395, 10),
                ("salary_pos_9", "เงินเดือน-ตำแหน่ง 9", 520, 395, 10),
                ("salary_pos_10", "เงินเดือน-ตำแหน่ง 10", 570, 395, 10),
                # Salary tax positions 1-8
                ("tax_pos_1", "ภาษีเงินเดือน-ตำแหน่ง 1", 120, 410, 10),
                ("tax_pos_2", "ภาษีเงินเดือน-ตำแหน่ง 2", 170, 410, 10),
                ("tax_pos_3", "ภาษีเงินเดือน-ตำแหน่ง 3", 220, 410, 10),
                ("tax_pos_4", "ภาษีเงินเดือน-ตำแหน่ง 4", 270, 410, 10),
                ("tax_pos_5", "ภาษีเงินเดือน-ตำแหน่ง 5", 320, 410, 10),
                ("tax_pos_6", "ภาษีเงินเดือน-ตำแหน่ง 6", 370, 410, 10),
                ("tax_pos_7", "ภาษีเงินเดือน-ตำแหน่ง 7", 420, 410, 10),
                ("tax_pos_8", "ภาษีเงินเดือน-ตำแหน่ง 8", 470, 410, 10),
                # Fee digit positions 1-10
                ("fee_pos_1", "ค่าธรรมเนียม-ตำแหน่ง 1", 120, 435, 10),
                ("fee_pos_2", "ค่าธรรมเนียม-ตำแหน่ง 2", 170, 435, 10),
                ("fee_pos_3", "ค่าธรรมเนียม-ตำแหน่ง 3", 220, 435, 10),
                ("fee_pos_4", "ค่าธรรมเนียม-ตำแหน่ง 4", 270, 435, 10),
                ("fee_pos_5", "ค่าธรรมเนียม-ตำแหน่ง 5", 320, 435, 10),
                ("fee_pos_6", "ค่าธรรมเนียม-ตำแหน่ง 6", 370, 435, 10),
                ("fee_pos_7", "ค่าธรรมเนียม-ตำแหน่ง 7", 420, 435, 10),
                ("fee_pos_8", "ค่าธรรมเนียม-ตำแหน่ง 8", 470, 435, 10),
                ("fee_pos_9", "ค่าธรรมเนียม-ตำแหน่ง 9", 520, 435, 10),
                ("fee_pos_10", "ค่าธรรมเนียม-ตำแหน่ง 10", 570, 435, 10),
                # Fee tax positions 1-8
                ("fee_tax_pos_1", "ภาษีค่าธรรมเนียม-ตำแหน่ง 1", 120, 450, 10),
                ("fee_tax_pos_2", "ภาษีค่าธรรมเนียม-ตำแหน่ง 2", 170, 450, 10),
                ("fee_tax_pos_3", "ภาษีค่าธรรมเนียม-ตำแหน่ง 3", 220, 450, 10),
                ("fee_tax_pos_4", "ภาษีค่าธรรมเนียม-ตำแหน่ง 4", 270, 450, 10),
                ("fee_tax_pos_5", "ภาษีค่าธรรมเนียม-ตำแหน่ง 5", 320, 450, 10),
                ("fee_tax_pos_6", "ภาษีค่าธรรมเนียม-ตำแหน่ง 6", 370, 450, 10),
                ("fee_tax_pos_7", "ภาษีค่าธรรมเนียม-ตำแหน่ง 7", 420, 450, 10),
                ("fee_tax_pos_8", "ภาษีค่าธรรมเนียม-ตำแหน่ง 8", 470, 450, 10),
                # Total income positions 1-10
                ("total_income_pos_1", "รวมเงิน-ตำแหน่ง 1", 120, 475, 10),
                ("total_income_pos_2", "รวมเงิน-ตำแหน่ง 2", 170, 475, 10),
                ("total_income_pos_3", "รวมเงิน-ตำแหน่ง 3", 220, 475, 10),
                ("total_income_pos_4", "รวมเงิน-ตำแหน่ง 4", 270, 475, 10),
                ("total_income_pos_5", "รวมเงิน-ตำแหน่ง 5", 320, 475, 10),
                ("total_income_pos_6", "รวมเงิน-ตำแหน่ง 6", 370, 475, 10),
                ("total_income_pos_7", "รวมเงิน-ตำแหน่ง 7", 420, 475, 10),
                ("total_income_pos_8", "รวมเงิน-ตำแหน่ง 8", 470, 475, 10),
                ("total_income_pos_9", "รวมเงิน-ตำแหน่ง 9", 520, 475, 10),
                ("total_income_pos_10", "รวมเงิน-ตำแหน่ง 10", 570, 475, 10),
                # Total tax positions 1-8
                ("total_tax_pos_1", "รวมภาษี-ตำแหน่ง 1", 120, 490, 10),
                ("total_tax_pos_2", "รวมภาษี-ตำแหน่ง 2", 170, 490, 10),
                ("total_tax_pos_3", "รวมภาษี-ตำแหน่ง 3", 220, 490, 10),
                ("total_tax_pos_4", "รวมภาษี-ตำแหน่ง 4", 270, 490, 10),
                ("total_tax_pos_5", "รวมภาษี-ตำแหน่ง 5", 320, 490, 10),
                ("total_tax_pos_6", "รวมภาษี-ตำแหน่ง 6", 370, 490, 10),
                ("total_tax_pos_7", "รวมภาษี-ตำแหน่ง 7", 420, 490, 10),
                ("total_tax_pos_8", "รวมภาษี-ตำแหน่ง 8", 470, 490, 10),
                # Dot positions 1-6
                ("dot_1", "dot 1", 120, 505, 10),
                ("dot_2", "dot 2", 160, 505, 10),
                ("dot_3", "dot 3", 200, 505, 10),
                ("dot_4", "dot 4", 240, 505, 10),
                ("dot_5", "dot 5", 280, 505, 10),
                ("dot_6", "dot 6", 320, 505, 10),
            ]
            
            coordinate_fields.clear()
            coordinate_controls = []
            
            for field_id, label, default_x, default_y, default_size in field_configs:
                x_control = ft.TextField(
                    label=f"X ({field_id})",
                    value=str(default_x),
                    width=80,
                    keyboard_type=ft.KeyboardType.NUMBER
                )
                y_control = ft.TextField(
                    label=f"Y ({field_id})",
                    value=str(default_y),
                    width=80,
                    keyboard_type=ft.KeyboardType.NUMBER
                )
                size_control = ft.TextField(
                    label=f"Size ({field_id})",
                    value=str(default_size),
                    width=80,
                    keyboard_type=ft.KeyboardType.NUMBER
                )
                
                coordinate_fields[field_id] = {
                    'x': x_control,
                    'y': y_control,
                    'size': size_control,
                    'label': label
                }
                
                tile = ft.ExpansionTile(
                        title=ft.Text(f"📍 {label}", size=12, weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(f"พิกัด: X={default_x}, Y={default_y}, ขนาด={default_size}", size=10),
                        controls=[
                            ft.Container(
                                content=ft.Row([
                                    x_control,
                                    y_control,
                                    size_control,
                                    ft.ElevatedButton(
                                        "ทดสอบ",
                                        on_click=lambda e, fid=field_id: test_single_field(fid),
                                        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_500, color=ft.Colors.WHITE)
                                    )
                                ], spacing=5),
                                padding=10
                            )
                        ],
                        initially_expanded=False
                    )
                coordinate_controls.append(tile)
                coordinate_tiles[field_id] = tile
            # Ensure DB table exists and try to load last saved coordinates into controls
            try:
                ensure_coordinate_table()
                loaded = load_coordinates_from_db_initial()
                if loaded:
                    status_text.value = "✅ โหลดพิกัดจากฐานข้อมูลแล้ว"
                    status_text.color = ft.Colors.GREEN_700
                else:
                    status_text.value = "ℹ️ ใช้ค่าพิกัดเริ่มต้น"
                    status_text.color = ft.Colors.ORANGE_700
                try:
                    page.update()
                except:
                    pass
            except Exception as ex:
                print(f"Initial coordinate DB load warning: {ex}")
            
            return coordinate_controls

        # Auto-load coordinates once after controls are created (DB -> JSON -> defaults)
        def initialize_coordinate_settings_once():
            try:
                # 1) Try DB first
                loaded_db = False
                try:
                    if ensure_coordinate_table():
                        loaded_db = load_coordinates_from_db_initial()
                except Exception as db_init_ex:
                    print(f"Coordinate DB init/load error: {db_init_ex}")

                if loaded_db:
                    status_text.value = (status_text.value + " | 📍 โหลดพิกัดจาก DB แล้ว") if status_text.value else "📍 โหลดพิกัดจาก DB แล้ว"
                    status_text.color = ft.Colors.GREEN_700
                    try:
                        page.update()
                    except:
                        pass
                    return

                # 2) Fallback to JSON file
                try:
                    import json, os
                    config_path = os.path.join(os.getcwd(), "pdf_coordinates.json")
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                        for field_id, coords in config_data.items():
                            if field_id in coordinate_fields:
                                coordinate_fields[field_id]['x'].value = str(coords.get('x', coordinate_fields[field_id]['x'].value))
                                coordinate_fields[field_id]['y'].value = str(coords.get('y', coordinate_fields[field_id]['y'].value))
                                coordinate_fields[field_id]['size'].value = str(coords.get('size', coordinate_fields[field_id]['size'].value))
                        status_text.value = (status_text.value + " | 📄 โหลดพิกัดจากไฟล์แล้ว") if status_text.value else "📄 โหลดพิกัดจากไฟล์แล้ว"
                        status_text.color = ft.Colors.GREEN_700
                        try:
                            page.update()
                        except:
                            pass
                        return
                except Exception as json_ex:
                    print(f"Coordinate JSON load error: {json_ex}")

                # 3) Otherwise keep defaults already set in controls
                status_text.value = (status_text.value + " | ℹ️ ใช้พิกัดเริ่มต้น") if status_text.value else "ℹ️ ใช้พิกัดเริ่มต้น"
                status_text.color = ft.Colors.ORANGE_700
                try:
                    page.update()
                except:
                    pass
            except Exception as init_ex:
                print(f"Coordinate init error: {init_ex}")
        
        # Add small PDF viewer for coordinate testing
        coordinate_test_viewer = ft.Container(
            content=ft.Text("คลิก 'ทดสอบ' เพื่อดูตำแหน่งพิกัด", 
                           size=12, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
            width=300,
            height=400,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5,
            padding=10,
            alignment=ft.alignment.center
        )

        def test_single_field(field_id):
            """Test positioning for a single field with large red circle marker"""
            try:
                if not os.path.exists(selected_pdf_path):
                    status_text.value = "❌ ไม่พบไฟล์ PDF ต้นฉบับ"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                import fitz
                
                # Get coordinates
                x = int(coordinate_fields[field_id]['x'].value)
                y = int(coordinate_fields[field_id]['y'].value)
                font_size = int(coordinate_fields[field_id]['size'].value)
                
                # Create test PDF with large red circle marker
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                temp_test_filename = f"temp_test_{field_id}_{timestamp}.pdf"
                temp_test_path = os.path.join(os.getcwd(), temp_test_filename)
                
                doc = fitz.open(selected_pdf_path)
                page_pdf = doc[0]
                rect = page_pdf.rect
                
                # Convert Y coordinate from top to bottom (PDF coordinate system)
                actual_y = rect.height - y
                
                # Draw very small red circle (3x smaller = ~17 pixel diameter = 8 pixel radius)
                circle_center = fitz.Point(x, actual_y)
                circle_radius = 8  # Very small circle for precise positioning
                
                # Draw small filled red circle with border
                page_pdf.draw_circle(circle_center, circle_radius, color=(1, 0, 0), fill=(1, 0.2, 0.2), width=2)
                
                # Add crosshair at center for precise positioning
                crosshair_size = 4
                # Horizontal line
                page_pdf.draw_line(fitz.Point(x - crosshair_size, actual_y), 
                                 fitz.Point(x + crosshair_size, actual_y), 
                                 color=(0, 0, 0), width=1)
                # Vertical line
                page_pdf.draw_line(fitz.Point(x, actual_y - crosshair_size), 
                                 fitz.Point(x, actual_y + crosshair_size), 
                                 color=(0, 0, 0), width=1)
                
                # Add field label near the circle (smaller text)
                label_text = f"{coordinate_fields[field_id]['label']}"
                label_point = fitz.Point(x + circle_radius + 5, actual_y - 5)
                page_pdf.insert_text(label_point, label_text, fontsize=8, color=(1, 0, 0))
                
                # Add coordinate info below the label (smaller text)
                coord_text = f"({x},{y})"
                coord_point = fitz.Point(x + circle_radius + 5, actual_y + 10)
                page_pdf.insert_text(coord_point, coord_text, fontsize=7, color=(0, 0, 0))
                
                # Convert to PNG instead of PDF and save with unique filename
                import time
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                microsecond = int(time.time() * 1000000) % 1000000
                png_filename = f"test_{field_id}_{timestamp}_{microsecond:06d}.png"
                png_path = os.path.join(os.getcwd(), png_filename)
                
                # Convert to PNG and save
                mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
                pix = page_pdf.get_pixmap(matrix=mat)
                pix.save(png_path)
                doc.close()
                
                # Update the preview to use PNG instead of PDF
                png_image_path = png_path
                
                # Force refresh both viewers with direct container updates
                nonlocal coordinate_test_viewer, pdf_preview_img, pdf_image_control, main_pdf_container, coordinate_test_container
                # Use PNG directly instead of converting from PDF
                if png_image_path:
                    # Create new image control with the PNG preview
                    new_image = ft.Image(
                        src=png_image_path, 
                        fit=ft.ImageFit.CONTAIN, 
                        width=595, 
                        height=842
                    )
                    
                    # Update main PDF container directly
                    main_pdf_container.content = new_image
                    try:
                        main_pdf_container.update()
                    except:
                        pass  # Container might not be added to page yet
                    
                    # Update small coordinate test viewer
                    coordinate_test_viewer.content = ft.Image(
                        src=png_image_path, 
                        fit=ft.ImageFit.CONTAIN, 
                        width=280, 
                        height=380
                    )
                    try:
                        coordinate_test_viewer.update()
                    except:
                        pass  # Container might not be added to page yet
                    
                    # Update the global reference
                    pdf_preview_img = png_image_path
                    pdf_image_control = new_image
                    
                    # Force page update to ensure changes are visible
                    try:
                        page.update()
                    except:
                        pass
                    
                else:
                    coordinate_test_viewer.content = ft.Text(
                        "ไม่สามารถแสดงตัวอย่างได้", 
                        size=10, 
                        color=ft.Colors.ORANGE_700,
                        text_align=ft.TextAlign.CENTER
                    )
                    try:
                        coordinate_test_viewer.update()
                    except:
                        pass  # Container might not be added to page yet
                
                # Don't clean up PNG files - keep them as log files
                # The PNG files serve as coordinate setting logs
                
                status_text.value = f"✅ ทดสอบ {coordinate_fields[field_id]['label']} - บันทึก PNG: {png_filename}"
                status_text.color = ft.Colors.GREEN_700
                
                # Force UI refresh
                page.update()
                
            except Exception as e:
                status_text.value = f"❌ ข้อผิดพลาดในการทดสอบ: {str(e)}"
                status_text.color = ft.Colors.RED_700
                page.update()
        
        def preview_all_coordinates(e):
            """Preview all fields with current coordinates using large red circles"""
            try:
                if not os.path.exists(selected_pdf_path):
                    status_text.value = "❌ ไม่พบไฟล์ PDF ต้นฉบับ"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                import fitz
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                temp_preview_filename = f"temp_preview_all_{timestamp}.pdf"
                temp_preview_path = os.path.join(os.getcwd(), temp_preview_filename)
                
                doc = fitz.open(selected_pdf_path)
                page_pdf = doc[0]
                rect = page_pdf.rect
                
                # Add very small red circles for all coordinate positions
                circle_radius = 8  # Very small circles (16 pixel diameter) for precise positioning
                for field_id, controls in coordinate_fields.items():
                    x = int(controls['x'].value)
                    y = int(controls['y'].value)
                    
                    # Convert Y coordinate from top to bottom (PDF coordinate system)
                    actual_y = rect.height - y
                    
                    # Draw red circle at the coordinate
                    circle_center = fitz.Point(x, actual_y)
                    page_pdf.draw_circle(circle_center, circle_radius, color=(1, 0, 0), fill=(1, 0.4, 0.4), width=3)
                    
                    # Add small crosshair at center
                    crosshair_size = 10
                    page_pdf.draw_line(fitz.Point(x - crosshair_size, actual_y), 
                                     fitz.Point(x + crosshair_size, actual_y), 
                                     color=(0, 0, 0), width=2)
                    page_pdf.draw_line(fitz.Point(x, actual_y - crosshair_size), 
                                     fitz.Point(x, actual_y + crosshair_size), 
                                     color=(0, 0, 0), width=2)
                    
                    # Add field ID label outside the circle
                    label_point = fitz.Point(x + circle_radius + 5, actual_y + 5)
                    page_pdf.insert_text(label_point, field_id[:10], fontsize=8, color=(0.8, 0, 0))
                
                doc.save(temp_preview_path)
                doc.close()
                
                # Force refresh both viewers with direct container updates
                nonlocal pdf_preview_img, pdf_image_control, coordinate_test_viewer, main_pdf_container
                pdf_preview_img = rasterize_pdf_to_png(temp_preview_path)
                if pdf_preview_img:
                    # Create new image control
                    new_image = ft.Image(src=pdf_preview_img, fit=ft.ImageFit.CONTAIN, width=595, height=842)
                    
                    # Update main PDF container directly
                    main_pdf_container.content = new_image
                    try:
                        main_pdf_container.update()
                    except:
                        pass  # Container might not be added to page yet
                    
                    # Update coordinate test viewer
                    coordinate_test_viewer.content = ft.Image(
                        src=pdf_preview_img, 
                        fit=ft.ImageFit.CONTAIN, 
                        width=280, 
                        height=380
                    )
                    try:
                        coordinate_test_viewer.update()
                    except:
                        pass  # Container might not be added to page yet
                    
                    # Update global reference
                    pdf_image_control = new_image
                    
                    # Force page update to ensure changes are visible
                    try:
                        page.update()
                    except:
                        pass
                
                # Clean up
                try:
                    os.remove(temp_preview_path)
                except:
                    pass
                
                status_text.value = "✅ แสดงตำแหน่งพิกัดทุกฟิลด์ด้วยวงกลมแดงขนาดใหญ่"
                status_text.color = ft.Colors.GREEN_700
                
                # Force UI refresh
                page.update()
                
            except Exception as e:
                status_text.value = f"❌ ข้อผิดพลาด: {str(e)}"
                status_text.color = ft.Colors.RED_700
                page.update()
        
        def save_coordinate_test_png(e):
            """Save PNG file with red/blue circles showing all coordinate positions"""
            try:
                if not os.path.exists(selected_pdf_path):
                    status_text.value = "❌ ไม่พบไฟล์ PDF ต้นฉบับ"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                import fitz
                import time
                
                # Create output filename with timestamp and microseconds for uniqueness
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                microsecond = int(time.time() * 1000000) % 1000000  # Add microseconds for uniqueness
                output_filename = f"coordinate_log_{timestamp}_{microsecond:06d}.png"
                output_path = os.path.join(os.getcwd(), output_filename)
                
                doc = fitz.open(selected_pdf_path)
                page_pdf = doc[0]
                rect = page_pdf.rect
                
                # Define default coordinates for unset fields (matching coordinate_fields names)
                default_coords = {
                    "withholder_name": (120, 150),
                    "withholder_address": (120, 175),
                    "withholder_tax_id": (120, 200),
                    "withholdee_name": (120, 280),
                    "withholdee_address": (120, 305),
                    "withholdee_tax_id": (120, 330),
                    "certificate_book_no": (400, 120),
                    "certificate_no": (500, 120),
                    "form_type": (400, 140),
                    "income_1_amount": (280, 400),
                    "income_1_tax": (380, 400),
                    "income_2_amount": (280, 425),
                    "income_2_tax": (380, 425),
                    "total_income": (280, 480),
                    "total_tax": (380, 480),
                    "total_tax_text": (120, 510),
                    "provident_fund": (280, 560),
                    "social_security_fund": (380, 560),
                    "retirement_mutual_fund": (480, 560),
                    "issue_date": (400, 620),
                    "signatory_name": (400, 670),
                    "fee_payment_date": (480, 620),
                    # Defaults for card numbers
                    "card_number_1": (120, 530),
                    "card_number_2": (180, 530),
                    "card_number_3": (240, 530),
                    "card_number_4": (300, 530),
                    "card_number_5": (360, 530),
                    "card_number_6": (420, 530),
                    "card_number_7": (480, 530),
                    "card_number_8": (540, 530),
                    "card_number_9": (600, 530),
                    "card_number_10": (660, 530),
                    # withholdee id 13 digits
                    "withholdee_id_1": (120, 540),
                    "withholdee_id_2": (156, 540),
                    "withholdee_id_3": (192, 540),
                    "withholdee_id_4": (228, 540),
                    "withholdee_id_5": (264, 540),
                    "withholdee_id_6": (300, 540),
                    "withholdee_id_7": (336, 540),
                    "withholdee_id_8": (372, 540),
                    "withholdee_id_9": (408, 540),
                    "withholdee_id_10": (444, 540),
                    "withholdee_id_11": (480, 540),
                    "withholdee_id_12": (516, 540),
                    "withholdee_id_13": (552, 540),
                    # withholder id 13 digits
                    "withholder_id_1": (120, 560),
                    "withholder_id_2": (156, 560),
                    "withholder_id_3": (192, 560),
                    "withholder_id_4": (228, 560),
                    "withholder_id_5": (264, 560),
                    "withholder_id_6": (300, 560),
                    "withholder_id_7": (336, 560),
                    "withholder_id_8": (372, 560),
                    "withholder_id_9": (408, 560),
                    "withholder_id_10": (444, 560),
                    "withholder_id_11": (480, 560),
                    "withholder_id_12": (516, 560),
                    "withholder_id_13": (552, 560)
                }
                
                # Very small circles for precise positioning (16px diameter)
                red_radius = 8  # For set coordinates (3x smaller)
                blue_radius = 8  # For unset/default coordinates (same size)
                
                # Track which fields have been set
                set_fields = set()
                
                # Add red circles for SET coordinate positions (only if different from defaults)
                for field_id, field_controls in coordinate_fields.items():
                    try:
                        x = int(field_controls['x'].value)
                        y = int(field_controls['y'].value)
                        
                        # Check if coordinates are different from defaults
                        is_customized = True
                        if field_id in default_coords:
                            default_x, default_y = default_coords[field_id]
                            if x == default_x and y == default_y:
                                is_customized = False
                        
                        if is_customized:  # Only show red circle if coordinates are customized
                            # Convert Y coordinate (top-down to bottom-up)
                            pdf_y = rect.height - y
                            
                            # Draw small filled red circle
                            circle_center = fitz.Point(x, pdf_y)
                            page_pdf.draw_circle(circle_center, red_radius, color=(1, 0, 0), fill=(1, 0.2, 0.2), width=2)
                            
                            # Add small black crosshair at center
                            crosshair_size = 4
                            page_pdf.draw_line(
                                fitz.Point(x - crosshair_size, pdf_y), 
                                fitz.Point(x + crosshair_size, pdf_y), 
                                color=(0, 0, 0), width=1
                            )
                            page_pdf.draw_line(
                                fitz.Point(x, pdf_y - crosshair_size), 
                                fitz.Point(x, pdf_y + crosshair_size), 
                                color=(0, 0, 0), width=1
                            )
                            
                            # Add field label
                            label_point = fitz.Point(x + red_radius + 5, pdf_y - 5)
                            page_pdf.insert_text(
                                label_point, 
                                f"{field_id}", 
                                fontsize=8, 
                                color=(1, 0, 0),
                                fontname="helv"
                            )
                            
                            set_fields.add(field_id)
                        
                    except (ValueError, KeyError):
                        continue  # Skip invalid coordinates
                
                # Add blue circles for UNSET/DEFAULT coordinate positions
                for field_id, (default_x, default_y) in default_coords.items():
                    # Check if this field was already shown as a red circle
                    if field_id not in set_fields:  # Only show blue if not already set as red
                        # Convert Y coordinate (top-down to bottom-up)
                        pdf_y = rect.height - default_y
                        
                        # Draw small blue circle for unset fields
                        circle_center = fitz.Point(default_x, pdf_y)
                        page_pdf.draw_circle(circle_center, blue_radius, color=(0, 0, 1), fill=(0.2, 0.2, 1), width=2)
                        
                        # Add small blue crosshair for unset fields
                        crosshair_size = 4
                        page_pdf.draw_line(
                            fitz.Point(default_x - crosshair_size, pdf_y), 
                            fitz.Point(default_x + crosshair_size, pdf_y), 
                            color=(0, 0, 1), width=1
                        )
                        page_pdf.draw_line(
                            fitz.Point(default_x, pdf_y - crosshair_size), 
                            fitz.Point(default_x, pdf_y + crosshair_size), 
                            color=(0, 0, 1), width=1
                        )
                        
                        # Add blue field label
                        label_point = fitz.Point(default_x + blue_radius + 5, pdf_y - 5)
                        page_pdf.insert_text(
                            label_point, 
                            f"{field_id}*", 
                            fontsize=7, 
                            color=(0, 0, 1),
                            fontname="helv"
                        )
                
                # Add summary header
                header_point = fitz.Point(30, 30)
                page_pdf.insert_text(
                    header_point, 
                    f"📍 Coordinate Settings Log - {timestamp}", 
                    fontsize=14, 
                    color=(0.5, 0, 0.5),
                    fontname="helv"
                )
                
                # Add legend
                legend_point = fitz.Point(30, 50)
                page_pdf.insert_text(
                    legend_point, 
                    "🔴 Red = Set Coordinates | 🔵 Blue = Default/Unset | * = Default Position", 
                    fontsize=10, 
                    color=(0, 0, 0),
                    fontname="helv"
                )
                
                # Convert to PNG and save
                mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
                pix = page_pdf.get_pixmap(matrix=mat)
                pix.save(output_path)
                
                doc.close()
                
                # Update viewer with the new PNG
                nonlocal pdf_preview_img, pdf_image_control, main_pdf_container
                pdf_preview_img = output_path
                new_image = ft.Image(src=pdf_preview_img, fit=ft.ImageFit.CONTAIN, width=595, height=842)
                main_pdf_container.content = new_image
                pdf_image_control = new_image
                
                # Update UI
                try:
                    main_pdf_container.update()
                    page.update()
                except:
                    pass
                
                status_text.value = f"✅ บันทึก PNG ทดสอบพิกัดเรียบร้อย: {output_filename}"
                status_text.color = ft.Colors.GREEN_700
                
                # Force page update
                try:
                    page.update()
                except:
                    pass
                    
            except Exception as ex:
                status_text.value = f"❌ เกิดข้อผิดพลาดในการบันทึก PNG: {str(ex)}"
                status_text.color = ft.Colors.RED_700
                try:
                    page.update()
                except:
                    pass

        def save_coordinates_config(e):
            """Save current coordinates to a config file"""
            try:
                config_data = {}
                for field_id, controls in coordinate_fields.items():
                    config_data[field_id] = {
                        'x': int(controls['x'].value),
                        'y': int(controls['y'].value),
                        'size': int(controls['size'].value)
                    }
                
                import json
                config_path = os.path.join(os.getcwd(), "pdf_coordinates.json")
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                
                # Also persist to Neon DB (coordinate table)
                try:
                    ensure_coordinate_table()
                    save_coordinates_to_db()
                    status_text.value = f"✅ บันทึกการตั้งค่าพิกัดแล้ว (ไฟล์ + DB): {config_path}"
                    status_text.color = ft.Colors.GREEN_700
                except Exception as ex:
                    status_text.value = f"⚠️ บันทึกไฟล์สำเร็จ แต่บันทึก DB ล้มเหลว: {str(ex)}"
                    status_text.color = ft.Colors.ORANGE_700
                page.update()
                
            except Exception as e:
                status_text.value = f"❌ ไม่สามารถบันทึกการตั้งค่าได้: {str(e)}"
                status_text.color = ft.Colors.RED_700
                page.update()
        
        def load_coordinates_config(e):
            """Load coordinates from config file"""
            try:
                import json
                config_path = os.path.join(os.getcwd(), "pdf_coordinates.json")
                
                if not os.path.exists(config_path):
                    # If no file, try DB instead
                    try:
                        ensure_coordinate_table()
                        loaded = load_coordinates_from_db_initial()
                        if loaded:
                            status_text.value = "✅ โหลดการตั้งค่าพิกัดจากฐานข้อมูลแล้ว"
                            status_text.color = ft.Colors.GREEN_700
                            page.update()
                            return
                        else:
                            status_text.value = "❌ ไม่พบไฟล์/ข้อมูลการตั้งค่า"
                            status_text.color = ft.Colors.ORANGE_700
                            page.update()
                            return
                    except Exception as ex:
                        status_text.value = f"❌ โหลดจาก DB ไม่สำเร็จ: {str(ex)}"
                        status_text.color = ft.Colors.RED_700
                        page.update()
                        return
                
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                for field_id, coords in config_data.items():
                    if field_id in coordinate_fields:
                        coordinate_fields[field_id]['x'].value = str(coords['x'])
                        coordinate_fields[field_id]['y'].value = str(coords['y'])
                        coordinate_fields[field_id]['size'].value = str(coords['size'])
                
                status_text.value = f"✅ โหลดการตั้งค่าพิกัดแล้ว: {config_path}"
                status_text.color = ft.Colors.GREEN_700
                page.update()
                
            except Exception as e:
                status_text.value = f"❌ ไม่สามารถโหลดการตั้งค่าได้: {str(e)}"
                status_text.color = ft.Colors.RED_700
                page.update()
        
        def pick_pdf(e):
            """Handle PDF file picking"""
            nonlocal selected_pdf_path
            file_picker = ft.FilePicker(on_result=lambda e: on_pdf_picked(e))
            page.overlay.append(file_picker)
            page.update()
            file_picker.pick_files(allowed_extensions=["pdf"], dialog_title="เลือกไฟล์ PDF")
        
        def on_pdf_picked(e):
            """Handle when PDF is picked"""
            nonlocal selected_pdf_path, main_pdf_container
            if e.files:
                selected_pdf_path = e.files[0].path
                pdf_path_text_control.value = f"ตำแหน่งไฟล์: {selected_pdf_path}"
                update_pdf_preview()
                # Ensure container is updated immediately
                main_pdf_container.content = pdf_image_control
                try:
                    main_pdf_container.update()
                except:
                    pass  # Container might not be added to page yet
        
        # Initialize PDF preview (don't call update immediately to avoid AssertionError)
        # update_pdf_preview()
        
        # Ensure main container has the initial content
        main_pdf_container.content = pdf_image_control
        
        # --- Thai font resolver for PDF text drawing ---
        def resolve_thai_font(doc) -> str | None:
            """Check for Thai font support - return None since font insertion methods are not available"""
            try:
                print("🔍 Checking Thai font support...")
                
                # Check if we have any font insertion methods
                has_insert_font = hasattr(doc, 'insert_font')
                has_insertFont = hasattr(doc, 'insertFont')
                
                print(f"📋 PyMuPDF methods: insert_font={has_insert_font}, insertFont={has_insertFont}")
                
                if not (has_insert_font or has_insertFont):
                    print("ℹ️ PyMuPDF version doesn't support font insertion - will use UTF-8 encoding")
                    return None
                
                # If methods are available, try to use them (for future compatibility)
                candidates = [
                    r"C:\Windows\Fonts\Tahoma.ttf",
                    r"C:\Windows\Fonts\tahoma.ttf", 
                    r"C:\Windows\Fonts\LeelawUI.ttf",
                ]
                
                for font_path in candidates:
                    if os.path.exists(font_path):
                        try:
                            if has_insert_font:
                                font_name = doc.insert_font(fontfile=font_path)
                            else:
                                font_name = doc.insertFont(fontfile=font_path)
                            print(f"✅ Using Thai font: {os.path.basename(font_path)} -> {font_name}")
                            return font_name
                        except Exception as fe:
                            print(f"❌ Failed to insert font {font_path}: {fe}")
                            continue
                
                print("⚠️ Font insertion available but failed - will use UTF-8 encoding")
                return None
                
            except Exception as e:
                print(f"❌ Font check error: {e}")
                return None
        
        def create_thai_pdf_with_reportlab(original_pdf_path, output_path, text_overlays):
            """Create Thai-enabled PDF using ReportLab overlaying on original PDF"""
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                import tempfile
                
                print("🎯 Using ReportLab for Thai text rendering...")
                
                # Find and register Thai font
                thai_font_name = None
                thai_fonts = [
                    ("Tahoma", r"C:\Windows\Fonts\tahoma.ttf"),
                    ("LeelawUI", r"C:\Windows\Fonts\LeelawUI.ttf"),
                    ("THSarabun", r"C:\Windows\Fonts\THSarabunNew.ttf"),
                ]
                
                for font_name, font_path in thai_fonts:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont(font_name, font_path))
                            thai_font_name = font_name
                            print(f"✅ Registered Thai font: {font_name}")
                            break
                        except Exception as e:
                            print(f"❌ Failed to register {font_name}: {e}")
                            continue
                
                # Create overlay PDF with Thai text
                temp_overlay = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_overlay.close()
                
                c = canvas.Canvas(temp_overlay.name, pagesize=A4)
                page_width, page_height = A4
                
                # Add text overlays
                for text, x, y, font_size in text_overlays:
                    if text and str(text).strip():
                        # Convert coordinates (PDF uses bottom-up Y-axis)
                        pdf_y = page_height - y
                        
                        if thai_font_name:
                            c.setFont(thai_font_name, font_size)
                        else:
                            c.setFont("Helvetica", font_size)
                        
                        # Draw text
                        c.drawString(x, pdf_y, str(text))
                        print(f"📝 Added to overlay: '{text}' at ({x}, {pdf_y}) with font: {thai_font_name or 'Helvetica'}")
                
                c.save()
                
                # Merge original PDF with overlay using PyMuPDF
                import fitz
                
                # Open original PDF
                original_doc = fitz.open(original_pdf_path)
                original_page = original_doc[0]
                
                # Open overlay PDF
                overlay_doc = fitz.open(temp_overlay.name)
                overlay_page = overlay_doc[0]
                
                # Merge overlay onto original
                original_page.show_pdf_page(original_page.rect, overlay_doc, 0)
                
                # Save result
                original_doc.save(output_path)
                original_doc.close()
                overlay_doc.close()
                
                # Clean up temp file
                os.unlink(temp_overlay.name)
                
                print(f"✅ Successfully created Thai PDF: {output_path}")
                return True
                
            except ImportError as e:
                print(f"❌ ReportLab not available: {e}")
                return False
            except Exception as e:
                print(f"❌ Error creating Thai PDF with ReportLab: {e}")
                return False

        def insert_thai_text(page, text, x, y, fontsize=12, color=(0,0,0), fontname=None):
            """Insert Thai text with proper encoding fallback"""
            try:
                import fitz  # Fix: import fitz here
                point = fitz.Point(x, y)
                
                # Method 1: Try with specific font if provided
                if fontname:
                    try:
                        page.insert_text(point, text, fontsize=fontsize, color=color, fontname=fontname)
                        print(f"📝 Inserted text with font {fontname}: '{text[:30]}...'")
                        return True
                    except Exception as e:
                        print(f"❌ Font insertion failed: {e}")
                
                # Method 2: Use UTF-8 encoding (works with PyMuPDF for Thai)
                try:
                    page.insert_text(point, text, fontsize=fontsize, color=color, encoding=1)
                    print(f"📝 Inserted text with UTF-8 encoding: '{text[:30]}...'")
                    return True
                except Exception as e:
                    print(f"❌ UTF-8 insertion failed: {e}")
                
                # Method 3: Default insertion (fallback)
                try:
                    page.insert_text(point, text, fontsize=fontsize, color=color)
                    print(f"📝 Inserted text with default method: '{text[:30]}...'")
                    return True
                except Exception as e:
                    print(f"❌ Default insertion failed: {e}")
                    return False
                
            except Exception as e:
                print(f"❌ Text insertion error: {e}")
                return False
        
        def check_database_encoding():
            """Check database encoding and test Thai text storage"""
            try:
                import psycopg2
                conn_str = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
                
                with psycopg2.connect(conn_str) as conn:
                    with conn.cursor() as cur:
                        # Check database encoding
                        cur.execute("SHOW server_encoding;")
                        db_encoding = cur.fetchone()[0]
                        print(f"🗄️ Database encoding: {db_encoding}")
                        
                        # Check client encoding
                        cur.execute("SHOW client_encoding;")
                        client_encoding = cur.fetchone()[0]
                        print(f"🖥️ Client encoding: {client_encoding}")
                        
                        # Test Thai text insertion and retrieval
                        test_thai = "บริษัท ทดสอบ จำกัด ภาษาไทย 🇹🇭"
                        cur.execute("SELECT %s as thai_test", (test_thai,))
                        retrieved = cur.fetchone()[0]
                        print(f"🧪 Original: {test_thai}")
                        print(f"🧪 Retrieved: {retrieved}")
                        print(f"🧪 Match: {test_thai == retrieved}")
                        
                        return db_encoding, client_encoding, test_thai == retrieved
                        
            except Exception as e:
                print(f"❌ Database encoding check failed: {e}")
                return None, None, False
        
        def test_thai_text_pdf(e):
            """Test function to generate Thai text in PDF for debugging"""
            try:
                # First check database encoding
                print("🔍 Checking database encoding...")
                db_enc, client_enc, thai_match = check_database_encoding()
                if db_enc:
                    print(f"📊 Database: {db_enc}, Client: {client_enc}, Thai test: {'✅' if thai_match else '❌'}")
                
                if not os.path.exists(selected_pdf_path):
                    status_text.value = "❌ ไม่พบไฟล์ PDF ต้นฉบับ"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                import fitz
                from datetime import datetime
                
                # Create test filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                test_filename = f"thai_test_{timestamp}.pdf"
                test_path = os.path.join(os.getcwd(), test_filename)
                
                # Open the original PDF
                doc = fitz.open(selected_pdf_path)
                page_pdf = doc[0]
                
                # Ensure Thai-capable font is available
                thai_fontname = resolve_thai_font(doc)
                print(f"🧪 Testing with font: {thai_fontname}")
                
                # Test Thai text samples
                thai_texts = [
                    ("บริษัท ทดสอบ จำกัด", 100, 150, 16),
                    ("เลขประจำตัวผู้เสียภาษี: 1234567890123", 100, 200, 12),
                    ("ที่อยู่: 123 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพมหานคร 10110", 100, 250, 10),
                    ("วันที่: ๑๕ มกราคม ๒๕๖๗", 100, 300, 14),
                    ("จำนวนเงิน: ๑๐,๐๐๐.๐๐ บาท", 100, 350, 12),
                    ("หมายเหตุ: ทดสอบการแสดงผลภาษาไทยในไฟล์ PDF", 100, 400, 10)
                ]
                
                # Insert test text using the new Thai text function
                for text, x, y, font_size in thai_texts:
                    insert_thai_text(page_pdf, text, x, y, font_size, (0, 0, 0), thai_fontname)
                
                # Add header text
                header_text = "🧪 การทดสอบฟอนต์ภาษาไทยใน PDF"
                insert_thai_text(page_pdf, header_text, 100, 100, 18, (1, 0, 0), thai_fontname)
                
                # Save the test PDF
                doc.save(test_path)
                doc.close()
                
                status_text.value = f"✅ ทดสอบภาษาไทยสำเร็จ: {test_filename}"
                status_text.color = ft.Colors.GREEN_700
                if not thai_fontname:
                    status_text.value += " (ใช้ฟอนต์เริ่มต้น)"
                if db_enc:
                    status_text.value += f" | DB: {db_enc}"
                page.update()
                
            except Exception as ex:
                status_text.value = f"❌ ข้อผิดพลาดในการทดสอบ: {str(ex)}"
                status_text.color = ft.Colors.RED_700
                page.update()
                print(f"🚫 Test error: {ex}")
        
        def fill_and_save_pdf(e):
            """Fill the displayed PDF with form data and save it"""
            try:
                if not all([withholder_name.value, withholder_tax_id.value, 
                           withholdee_name.value, withholdee_tax_id.value]):
                    status_text.value = "❌ กรุณากรอกข้อมูลที่จำเป็น"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                if not os.path.exists(selected_pdf_path):
                    status_text.value = "❌ ไม่พบไฟล์ PDF ต้นฉบับ"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                # Import required libraries
                try:
                    import fitz  # PyMuPDF
                except ImportError:
                    status_text.value = "❌ ขาดไลบรารี PyMuPDF (ติดตั้งด้วย: pip install PyMuPDF)"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                # Create output filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_name = withholdee_name.value.replace(' ', '_').replace('/', '_')
                output_filename = f"filled_form_{safe_name}_{timestamp}.pdf"
                output_path = os.path.join(os.getcwd(), output_filename)
                
                # Open the original PDF
                doc = fitz.open(selected_pdf_path)
                page_pdf = doc[0]
                
                # Ensure Thai-capable font is available
                thai_fontname = resolve_thai_font(doc)
                
                # Get page dimensions
                rect = page_pdf.rect
                page_width = rect.width
                page_height = rect.height
                
                # Get text placement coordinates from coordinate controls
                text_overlays = []
                for field_id, controls in coordinate_fields.items():
                    x = int(controls['x'].value)
                    y = int(controls['y'].value)  
                    font_size = int(controls['size'].value)
                    
                    # Get field value based on field_id
                    field_value = ""
                    if field_id == "withholder_name":
                        field_value = withholder_name.value or ""
                    elif field_id == "withholder_address":
                        field_value = withholder_address.value or ""
                    elif field_id == "withholder_tax_id":
                        field_value = withholder_tax_id.value or ""
                    elif field_id == "withholdee_name":
                        field_value = withholdee_name.value or ""
                    elif field_id == "withholdee_address":
                        field_value = withholdee_address.value or ""
                    elif field_id == "withholdee_tax_id":
                        field_value = withholdee_tax_id.value or ""
                    elif field_id == "certificate_book_no":
                        field_value = certificate_book_no.value or ""
                    elif field_id == "certificate_no":
                        field_value = certificate_no.value or ""
                    elif field_id == "form_type":
                        field_value = form_type.value or ""
                    elif field_id == "income_1_amount":
                        field_value = str(income_1_amount.value or "").strip()
                    elif field_id == "income_1_tax":
                        field_value = str(income_1_tax.value or "").strip()
                    elif field_id == "income_2_amount":
                        field_value = str(income_2_amount.value or "").strip()
                    elif field_id == "income_2_tax":
                        field_value = str(income_2_tax.value or "").strip()
                    elif field_id == "total_income":
                        field_value = total_income_display.value or "0"
                    elif field_id == "total_tax":
                        field_value = total_tax_display.value or "0"
                    elif field_id == "total_tax_text":
                        field_value = total_tax_text.value or ""
                    elif field_id == "provident_fund":
                        field_value = str(provident_fund.value or "").strip()
                    elif field_id == "social_security_fund":
                        field_value = str(social_security_fund.value or "").strip()
                    elif field_id == "retirement_mutual_fund":
                        field_value = str(retirement_mutual_fund.value or "").strip()
                    elif field_id == "issue_date":
                        field_value = issue_date.value or ""
                    elif field_id == "signatory_name":
                        field_value = signatory_name.value or ""
                    elif field_id == "fee_payment_date":
                        field_value = fee_payment_date.value or ""
                    # support dynamic card numbers (if user wants to overlay text there)
                    elif field_id == "card_number_1":
                        field_value = card_number_1.value or ""
                    elif field_id == "card_number_2":
                        field_value = card_number_2.value or ""
                    elif field_id == "card_number_3":
                        field_value = card_number_3.value or ""
                    elif field_id == "card_number_4":
                        field_value = card_number_4.value or ""
                    elif field_id == "card_number_5":
                        field_value = card_number_5.value or ""
                    elif field_id == "card_number_6":
                        field_value = card_number_6.value or ""
                    elif field_id == "card_number_7":
                        field_value = card_number_7.value or ""
                    elif field_id == "card_number_8":
                        field_value = card_number_8.value or ""
                    elif field_id == "card_number_9":
                        field_value = card_number_9.value or ""
                    elif field_id == "card_number_10":
                        field_value = card_number_10.value or ""
                    # withholdee 13 digits
                    elif field_id == "withholdee_id_1":
                        field_value = withholdee_id_1.value or ""
                    elif field_id == "withholdee_id_2":
                        field_value = withholdee_id_2.value or ""
                    elif field_id == "withholdee_id_3":
                        field_value = withholdee_id_3.value or ""
                    elif field_id == "withholdee_id_4":
                        field_value = withholdee_id_4.value or ""
                    elif field_id == "withholdee_id_5":
                        field_value = withholdee_id_5.value or ""
                    elif field_id == "withholdee_id_6":
                        field_value = withholdee_id_6.value or ""
                    elif field_id == "withholdee_id_7":
                        field_value = withholdee_id_7.value or ""
                    elif field_id == "withholdee_id_8":
                        field_value = withholdee_id_8.value or ""
                    elif field_id == "withholdee_id_9":
                        field_value = withholdee_id_9.value or ""
                    elif field_id == "withholdee_id_10":
                        field_value = withholdee_id_10.value or ""
                    elif field_id == "withholdee_id_11":
                        field_value = withholdee_id_11.value or ""
                    elif field_id == "withholdee_id_12":
                        field_value = withholdee_id_12.value or ""
                    elif field_id == "withholdee_id_13":
                        field_value = withholdee_id_13.value or ""
                    # withholder 13 digits
                    elif field_id == "withholder_id_1":
                        field_value = withholder_id_1.value or ""
                    elif field_id == "withholder_id_2":
                        field_value = withholder_id_2.value or ""
                    elif field_id == "withholder_id_3":
                        field_value = withholder_id_3.value or ""
                    elif field_id == "withholder_id_4":
                        field_value = withholder_id_4.value or ""
                    elif field_id == "withholder_id_5":
                        field_value = withholder_id_5.value or ""
                    elif field_id == "withholder_id_6":
                        field_value = withholder_id_6.value or ""
                    elif field_id == "withholder_id_7":
                        field_value = withholder_id_7.value or ""
                    elif field_id == "withholder_id_8":
                        field_value = withholder_id_8.value or ""
                    elif field_id == "withholder_id_9":
                        field_value = withholder_id_9.value or ""
                    elif field_id == "withholder_id_10":
                        field_value = withholder_id_10.value or ""
                    elif field_id == "withholder_id_11":
                        field_value = withholder_id_11.value or ""
                    elif field_id == "withholder_id_12":
                        field_value = withholder_id_12.value or ""
                    elif field_id == "withholder_id_13":
                        field_value = withholder_id_13.value or ""
                    # salary positions 1..10
                    elif field_id == "salary_pos_1":
                        field_value = salary_pos_1.value or ""
                    elif field_id == "salary_pos_2":
                        field_value = salary_pos_2.value or ""
                    elif field_id == "salary_pos_3":
                        field_value = salary_pos_3.value or ""
                    elif field_id == "salary_pos_4":
                        field_value = salary_pos_4.value or ""
                    elif field_id == "salary_pos_5":
                        field_value = salary_pos_5.value or ""
                    elif field_id == "salary_pos_6":
                        field_value = salary_pos_6.value or ""
                    elif field_id == "salary_pos_7":
                        field_value = salary_pos_7.value or ""
                    elif field_id == "salary_pos_8":
                        field_value = salary_pos_8.value or ""
                    elif field_id == "salary_pos_9":
                        field_value = salary_pos_9.value or ""
                    elif field_id == "salary_pos_10":
                        field_value = salary_pos_10.value or ""
                    # salary tax positions 1..8
                    elif field_id == "tax_pos_1":
                        field_value = tax_pos_1.value or ""
                    elif field_id == "tax_pos_2":
                        field_value = tax_pos_2.value or ""
                    elif field_id == "tax_pos_3":
                        field_value = tax_pos_3.value or ""
                    elif field_id == "tax_pos_4":
                        field_value = tax_pos_4.value or ""
                    elif field_id == "tax_pos_5":
                        field_value = tax_pos_5.value or ""
                    elif field_id == "tax_pos_6":
                        field_value = tax_pos_6.value or ""
                    elif field_id == "tax_pos_7":
                        field_value = tax_pos_7.value or ""
                    elif field_id == "tax_pos_8":
                        field_value = tax_pos_8.value or ""
                    # fee positions 1..10
                    elif field_id == "fee_pos_1":
                        field_value = fee_pos_1.value or ""
                    elif field_id == "fee_pos_2":
                        field_value = fee_pos_2.value or ""
                    elif field_id == "fee_pos_3":
                        field_value = fee_pos_3.value or ""
                    elif field_id == "fee_pos_4":
                        field_value = fee_pos_4.value or ""
                    elif field_id == "fee_pos_5":
                        field_value = fee_pos_5.value or ""
                    elif field_id == "fee_pos_6":
                        field_value = fee_pos_6.value or ""
                    elif field_id == "fee_pos_7":
                        field_value = fee_pos_7.value or ""
                    elif field_id == "fee_pos_8":
                        field_value = fee_pos_8.value or ""
                    elif field_id == "fee_pos_9":
                        field_value = fee_pos_9.value or ""
                    elif field_id == "fee_pos_10":
                        field_value = fee_pos_10.value or ""
                    # fee tax positions 1..8
                    elif field_id == "fee_tax_pos_1":
                        field_value = fee_tax_pos_1.value or ""
                    elif field_id == "fee_tax_pos_2":
                        field_value = fee_tax_pos_2.value or ""
                    elif field_id == "fee_tax_pos_3":
                        field_value = fee_tax_pos_3.value or ""
                    elif field_id == "fee_tax_pos_4":
                        field_value = fee_tax_pos_4.value or ""
                    elif field_id == "fee_tax_pos_5":
                        field_value = fee_tax_pos_5.value or ""
                    elif field_id == "fee_tax_pos_6":
                        field_value = fee_tax_pos_6.value or ""
                    elif field_id == "fee_tax_pos_7":
                        field_value = fee_tax_pos_7.value or ""
                    elif field_id == "fee_tax_pos_8":
                        field_value = fee_tax_pos_8.value or ""
                    # total income positions 1..10
                    elif field_id == "total_income_pos_1":
                        field_value = total_income_pos_1.value or ""
                    elif field_id == "total_income_pos_2":
                        field_value = total_income_pos_2.value or ""
                    elif field_id == "total_income_pos_3":
                        field_value = total_income_pos_3.value or ""
                    elif field_id == "total_income_pos_4":
                        field_value = total_income_pos_4.value or ""
                    elif field_id == "total_income_pos_5":
                        field_value = total_income_pos_5.value or ""
                    elif field_id == "total_income_pos_6":
                        field_value = total_income_pos_6.value or ""
                    elif field_id == "total_income_pos_7":
                        field_value = total_income_pos_7.value or ""
                    elif field_id == "total_income_pos_8":
                        field_value = total_income_pos_8.value or ""
                    elif field_id == "total_income_pos_9":
                        field_value = total_income_pos_9.value or ""
                    elif field_id == "total_income_pos_10":
                        field_value = total_income_pos_10.value or ""
                    # total tax positions 1..8
                    elif field_id == "total_tax_pos_1":
                        field_value = total_tax_pos_1.value or ""
                    elif field_id == "total_tax_pos_2":
                        field_value = total_tax_pos_2.value or ""
                    elif field_id == "total_tax_pos_3":
                        field_value = total_tax_pos_3.value or ""
                    elif field_id == "total_tax_pos_4":
                        field_value = total_tax_pos_4.value or ""
                    elif field_id == "total_tax_pos_5":
                        field_value = total_tax_pos_5.value or ""
                    elif field_id == "total_tax_pos_6":
                        field_value = total_tax_pos_6.value or ""
                    elif field_id == "total_tax_pos_7":
                        field_value = total_tax_pos_7.value or ""
                    elif field_id == "total_tax_pos_8":
                        field_value = total_tax_pos_8.value or ""
                    # dot 1..6
                    elif field_id == "dot_1":
                        field_value = dot_1.value or ""
                    elif field_id == "dot_2":
                        field_value = dot_2.value or ""
                    elif field_id == "dot_3":
                        field_value = dot_3.value or ""
                    elif field_id == "dot_4":
                        field_value = dot_4.value or ""
                    elif field_id == "dot_5":
                        field_value = dot_5.value or ""
                    elif field_id == "dot_6":
                        field_value = dot_6.value or ""
                    
                    if field_value:
                        # Convert Y coordinate from top to bottom (PDF coordinate system)
                        actual_y = page_height - y
                        text_overlays.append((field_value, x, actual_y, font_size))
                
                # Try ReportLab method first (best for Thai)
                print(f"📄 Processing {len(text_overlays)} text overlays...")
                success = create_thai_pdf_with_reportlab(selected_pdf_path, output_path, text_overlays)
                
                if success:
                    # ReportLab succeeded, skip PyMuPDF
                    doc.close()
                    status_text.value = f"✅ บันทึกแบบฟอร์มด้วย ReportLab เรียบร้อย: {output_filename}"
                    status_text.color = ft.Colors.GREEN_700
                    status_text.value += " (รองรับภาษาไทย 🇹🇭)"
                    page.update()
                    return
                
                # Fallback to PyMuPDF method if ReportLab fails
                print("🔄 Falling back to PyMuPDF method...")
                for text, x, y, font_size in text_overlays:
                    if text and str(text).strip():  # Only add non-empty text
                        success = insert_thai_text(page_pdf, str(text), x, y, font_size, (0, 0, 0), thai_fontname)
                        if not success:
                            print(f"⚠️ Failed to insert text: '{text}'")
                
                # Save the filled PDF
                doc.save(output_path)
                doc.close()
                
                status_text.value = f"✅ บันทึกแบบฟอร์มที่กรอกแล้วเรียบร้อย: {output_filename}"
                status_text.color = ft.Colors.GREEN_700
                if not thai_fontname:
                    status_text.value += " (คำเตือน: ไม่พบฟอนต์ไทย ใช้ฟอนต์เริ่มต้นแทน)"
                page.update()
                
            except Exception as e:
                status_text.value = f"❌ ข้อผิดพลาดในการกรอกแบบฟอร์ม: {str(e)}"
                status_text.color = ft.Colors.RED_700
                page.update()
        
        def preview_pdf_with_data(e):
            """Preview PDF with overlay data using current coordinate settings"""
            preview_all_coordinates(e)
        
        # Database record selection functionality
        db_records_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("ชื่อผู้จ่าย")),
                ft.DataColumn(ft.Text("ชื่อผู้รับ")),
                ft.DataColumn(ft.Text("จำนวนเงิน")),
                ft.DataColumn(ft.Text("วันที่")),
                ft.DataColumn(ft.Text("เลือก"))
            ],
            rows=[]
        )
        
        # Data selection dialog
        def show_data_selection_dialog():
            """Show dialog with database records for selection"""
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("เลือกข้อมูลจากฐานข้อมูล"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("เลือกรายการที่ต้องการโหลด:"),
                        ft.Container(
                            content=db_records_table,
                            width=800,
                            height=400,
                            padding=10
                        )
                    ], scroll=ft.ScrollMode.AUTO),
                    width=900,
                    height=500
                ),
                actions=[
                    ft.TextButton("ปิด", on_click=close_dialog)
                ]
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        def load_database_records():
            """Load all records and show in a selection dialog with data grid"""
            try:
                import psycopg2
                conn_str = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
                
                # Check available tables first
                available_tables = check_available_tables()
                possible_tables = ['tax_certificates', 'certificate_records', 'certificates', 'transfer_records', 'withholding_tax']
                table_to_use = None
                
                for table_name in possible_tables:
                    if table_name in available_tables:
                        table_to_use = table_name
                        break
                
                if not table_to_use:
                    status_text.value = f"❌ ไม่พบตารางข้อมูล (มีตาราง: {', '.join(available_tables)})"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                with psycopg2.connect(conn_str) as conn:
                    with conn.cursor() as cur:
                        # Get column information
                        cur.execute(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = '{table_to_use}'
                            ORDER BY ordinal_position
                        """)
                        columns = [col[0] for col in cur.fetchall()]
                        
                        # Get all records
                        cur.execute(f"SELECT * FROM {table_to_use} ORDER BY id DESC LIMIT 50")  # Limit to 50 most recent
                        records = cur.fetchall()
                        
                        if not records:
                            status_text.value = f"⚠️ ไม่พบข้อมูลในตาราง {table_to_use}"
                            status_text.color = ft.Colors.ORANGE_700
                            page.update()
                            return
                        
                        # Create data grid
                        data_rows = []
                        
                        # Create table columns - show first few important columns
                        display_columns = []
                        important_cols = ['id', 'withholder_name', 'holder_name', 'company_name', 'name', 
                                        'withholdee_name', 'holdee_name', 'employee_name',
                                        'certificate_no', 'cert_no', 'number', 'amount', 'salary_amount',
                                        'date', 'created_date', 'issue_date']
                        
                        # Build display columns based on what's available
                        col_indices = {}
                        for i, col in enumerate(columns[:8]):  # Show max 8 columns for readability
                            if col in important_cols or i < 5:  # Always show first 5 columns
                                display_columns.append(ft.DataColumn(ft.Text(col, size=11, weight=ft.FontWeight.BOLD)))
                                col_indices[col] = i
                        
                        # Build data rows
                        for record in records:
                            cells = []
                            for col in col_indices.keys():
                                idx = col_indices[col]
                                value = str(record[idx]) if record[idx] is not None else ""
                                # Truncate long values
                                if len(value) > 20:
                                    value = value[:17] + "..."
                                cells.append(ft.DataCell(ft.Text(value, size=10)))
                            
                            # Make row clickable
                            data_rows.append(ft.DataRow(
                                cells=cells,
                                on_select_changed=lambda e, rec=record, cols=columns: select_record_from_grid(rec, cols)
                            ))
                        
                        # Create the data table
                        data_grid = ft.DataTable(
                            columns=display_columns,
                            rows=data_rows,
                            border=ft.border.all(2, ft.Colors.GREY_400),
                            border_radius=8,
                            vertical_lines=ft.BorderSide(1, ft.Colors.GREY_300),
                            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_300),
                            heading_row_color=ft.Colors.BLUE_50,
                            heading_row_height=40,
                            data_row_min_height=35,
                            data_row_max_height=35,
                            column_spacing=10,
                        )
                        
                        # Create selection dialog
                        def close_dialog(e):
                            page.dialog.open = False
                            page.update()
                        
                        dialog_content = ft.Column([
                            ft.Text(f"🗂️ เลือกข้อมูลจากตาราง {table_to_use}", 
                                   size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                            ft.Text(f"พบข้อมูล {len(records)} รายการ (แสดง 50 รายการล่าสุด)", 
                                   size=12, color=ft.Colors.GREY_600),
                            ft.Container(
                                content=data_grid,
                                height=400,
                                width=800,
                                border=ft.border.all(1, ft.Colors.GREY_300),
                                border_radius=8,
                                padding=10,
                                bgcolor=ft.Colors.WHITE
                            ),
                            ft.Row([
                                ft.ElevatedButton("❌ ปิด", on_click=close_dialog,
                                               style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)),
                                ft.Text("👆 คลิกที่แถวเพื่อเลือกข้อมูล", size=12, color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        ], tight=True)
                        
                        # Show dialog
                        dialog = ft.AlertDialog(
                            title=ft.Text("📋 เลือกข้อมูลจากฐานข้อมูล"),
                            content=dialog_content,
                            modal=True
                        )
                        
                        page.dialog = dialog
                        dialog.open = True
                        page.update()
                        
            except Exception as ex:
                status_text.value = f"❌ ข้อผิดพลาดในการโหลดข้อมูล: {str(ex)}"
                status_text.color = ft.Colors.RED_700
                page.update()
                print(f"🚫 Load records error: {ex}")
        
        def select_record_from_grid(record, columns):
            """Fill form when user selects a record from the grid"""
            try:
                # Create data dictionary
                data_dict = dict(zip(columns, record))
                print(f"📊 Selected record: ID={record[0]}")
                
                # Use the same field mapping as auto_fill_first_record
                field_mappings = {
                    'withholder_name': ['withholder_name', 'holder_name', 'company_name', 'name'],
                    'withholder_address': ['withholder_address', 'holder_address', 'address'],
                    'withholder_tax_id': ['withholder_tax_id', 'holder_tax_id', 'tax_id'],
                    'withholdee_name': ['withholdee_name', 'holdee_name', 'employee_name'],
                    'withholdee_address': ['withholdee_address', 'holdee_address', 'employee_address'],
                    'withholdee_tax_id': ['withholdee_tax_id', 'holdee_tax_id', 'employee_tax_id'],
                    'certificate_book_no': ['certificate_book_no', 'book_no', 'book_number'],
                    'certificate_no': ['certificate_no', 'cert_no', 'number'],
                    'sequence_in_form': ['sequence_in_form', 'sequence', 'seq_no'],
                    'income_1_amount': ['income_1_amount', 'salary_amount', 'amount'],
                    'income_1_tax': ['income_1_tax', 'salary_tax', 'tax_amount'],
                    'income_2_amount': ['income_2_amount', 'bonus_amount', 'other_amount'],
                    'income_2_tax': ['income_2_tax', 'bonus_tax', 'other_tax'],
                    'issue_date': ['issue_date', 'date', 'created_date'],
                    'signatory_name': ['signatory_name', 'signer_name', 'issued_by']
                }
                
                def get_value_from_mapping(field_name):
                    possible_cols = field_mappings.get(field_name, [field_name])
                    for col in possible_cols:
                        if col in data_dict and data_dict[col] is not None:
                            return data_dict[col]
                    return ""
                
                # Fill all form fields
                withholder_name.value = str(get_value_from_mapping('withholder_name'))
                withholder_address.value = str(get_value_from_mapping('withholder_address'))
                withholder_tax_id.value = str(get_value_from_mapping('withholder_tax_id'))
                
                withholdee_name.value = str(get_value_from_mapping('withholdee_name'))
                withholdee_address.value = str(get_value_from_mapping('withholdee_address'))
                withholdee_tax_id.value = str(get_value_from_mapping('withholdee_tax_id'))
                # Auto-split 13-digit tax ID into 5 parts for card_number_1..5 (when auto-fill from dashboard)
                try:
                    taxid = ''.join([ch for ch in (withholdee_tax_id.value or '') if ch.isdigit()])
                    if len(taxid) == 13:
                        card_number_1.value = taxid[0]
                        card_number_2.value = taxid[1:5]
                        card_number_3.value = taxid[5:10]
                        card_number_4.value = taxid[10:12]
                        card_number_5.value = taxid[12]
                    else:
                        card_number_1.value = card_number_2.value = card_number_3.value = card_number_4.value = card_number_5.value = ""
                except Exception:
                    card_number_1.value = card_number_2.value = card_number_3.value = card_number_4.value = card_number_5.value = ""
                
                certificate_book_no.value = str(get_value_from_mapping('certificate_book_no'))
                certificate_no.value = str(get_value_from_mapping('certificate_no'))
                sequence_in_form.value = str(get_value_from_mapping('sequence_in_form'))
                
                income_1_amount.value = str(get_value_from_mapping('income_1_amount') or "0")
                income_1_tax.value = str(get_value_from_mapping('income_1_tax') or "0")
                income_2_amount.value = str(get_value_from_mapping('income_2_amount') or "0")
                income_2_tax.value = str(get_value_from_mapping('income_2_tax') or "0")
                
                provident_fund.value = "0"
                social_security_fund.value = "0"
                retirement_mutual_fund.value = "0"
                
                issue_date.value = str(get_value_from_mapping('issue_date'))
                signatory_name.value = str(get_value_from_mapping('signatory_name'))
                company_seal.value = False
                
                # Calculate totals
                try:
                    v1 = float(income_1_amount.value) if (income_1_amount.value or "").strip() else 0.0
                    v2 = float(income_2_amount.value) if (income_2_amount.value or "").strip() else 0.0
                    t1 = float(income_1_tax.value) if (income_1_tax.value or "").strip() else 0.0
                    t2 = float(income_2_tax.value) if (income_2_tax.value or "").strip() else 0.0
                    total_income = v1 + v2
                    total_tax = t1 + t2
                    total_income_display.value = f"{total_income:,.2f}"
                    total_tax_display.value = f"{total_tax:,.2f}"
                except:
                    total_income_display.value = "0.00"
                    total_tax_display.value = "0.00"
                
                # Close dialog
                page.dialog.open = False
                
                # Load coordinate settings
                load_coordinates_from_database()
                
                status_text.value = f"✅ โหลดข้อมูล ID: {record[0]} เรียบร้อย"
                status_text.color = ft.Colors.GREEN_700
                page.update()
                
                print(f"✅ Form filled with record ID: {record[0]}")
                
            except Exception as ex:
                status_text.value = f"❌ ข้อผิดพลาดในการเลือกข้อมูล: {str(ex)}"
                status_text.color = ft.Colors.RED_700
                page.update()
                print(f"🚫 Select record error: {ex}")
        
        def load_specific_record(cert_id):
            """Load specific record data into form fields and coordinates"""
            try:
                cert_data = crystal_renderer.get_certificate_by_id(cert_id)
                
                if cert_data:
                    # Fill form fields with database data
                    withholder_name.value = cert_data.get('withholder_name', '')
                    withholder_address.value = cert_data.get('withholder_address', '')
                    withholder_tax_id.value = cert_data.get('withholder_tax_id', '')
                    withholder_type.value = cert_data.get('withholder_type', '')
                    withholdee_name.value = cert_data.get('withholdee_name', '')
                    withholdee_address.value = cert_data.get('withholdee_address', '')
                    withholdee_tax_id.value = cert_data.get('withholdee_tax_id', '')
                    withholdee_type.value = cert_data.get('withholdee_type', '')
                    certificate_book_no.value = cert_data.get('certificate_book_no', '')
                    certificate_no.value = cert_data.get('certificate_no', '')
                    sequence_in_form.value = str(cert_data.get('sequence_in_form', ''))
                    form_type.value = cert_data.get('form_type', '')
                    income_1_amount.value = str(cert_data.get('income_type_1_amount', '0'))
                    income_1_tax.value = str(cert_data.get('income_type_1_tax', '0'))
                    income_2_amount.value = str(cert_data.get('income_type_2_amount', '0'))
                    income_2_tax.value = str(cert_data.get('income_type_2_tax', '0'))
                    provident_fund.value = str(cert_data.get('provident_fund', '0'))
                    social_security_fund.value = str(cert_data.get('social_security_fund', '0'))
                    retirement_mutual_fund.value = str(cert_data.get('retirement_mutual_fund', '0'))
                    issue_type.value = cert_data.get('issue_type', '')
                    issue_date.value = str(cert_data.get('issue_date', ''))
                    signatory_name.value = cert_data.get('signatory_name', '')
                    company_seal.value = cert_data.get('company_seal', False)
                    total_tax_text.value = cert_data.get('total_tax_withheld_text', '')
                    
                    # Calculate totals (need to define this function later)
                    try:
                        calculate_totals()
                    except:
                        pass  # Function might not be defined yet
                    
                    # Auto-load coordinate settings from database
                    load_coordinates_from_database()
                    
                    # Close dialog
                    page.dialog.open = False
                    
                    # Update the form
                    page.update()
                    
                    status_text.value = f"✅ โหลดข้อมูลแล้ว: {cert_data.get('withholdee_name', 'ไม่ระบุชื่อ')} (ID: {cert_id})"
                    status_text.color = ft.Colors.GREEN_700
                    page.update()
                else:
                    status_text.value = "❌ ไม่สามารถดึงข้อมูลได้"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    
            except Exception as e:
                status_text.value = f"❌ ข้อผิดพลาด: {str(e)}"
                status_text.color = ft.Colors.RED_700
                page.update()
        
        def load_coordinates_from_database():
            """Auto-load coordinate settings from database"""
            try:
                conn = get_db_connection_for_coords()
                if not conn:
                    return
                    
                cur = conn.cursor()
                cur.execute("SELECT field_id, x, y, size FROM coordinate")
                results = cur.fetchall()
                
                if results:
                    # Update coordinate controls with database values
                    for field_id, x, y, size in results:
                        if field_id in coordinate_fields:
                            coordinate_fields[field_id]['x'].value = str(x)
                            coordinate_fields[field_id]['y'].value = str(y)
                            coordinate_fields[field_id]['size'].value = str(size)
                
                # Auto-fill withholder data from saved settings
                try:
                    cur.execute("SELECT setting_value FROM withholder_settings WHERE setting_key = 'checkbox_states'")
                    result = cur.fetchone()
                    
                    if result:
                        settings = result[0]
                        withholder_data = settings.get("selected_withholder", {})
                        
                        if withholder_data:
                            # Fill withholder fields with saved data
                            if withholder_data.get('withholder_name'):
                                withholder_name.value = withholder_data['withholder_name']
                            if withholder_data.get('withholder_address'):
                                withholder_address.value = withholder_data['withholder_address']
                            if withholder_data.get('withholder_tax_id'):
                                withholder_tax_id.value = withholder_data['withholder_tax_id']
                            
                            # Update status
                            status_text.value = f"✅ โหลดข้อมูลผู้หักภาษี: {withholder_data.get('withholder_name', 'N/A')}"
                            status_text.color = ft.Colors.GREEN_700
                            
                            print("✅ Auto-filled withholder data from saved settings")
                except Exception as ex:
                    print(f"Auto-fill withholder data error: {ex}")
                
                # Update page after loading
                page.update()
                
            except Exception as ex:
                print(f"Load coordinates error: {ex}")
            finally:
                try:
                    if 'cur' in locals():
                        cur.close()
                    if 'conn' in locals():
                        conn.close()
                except Exception:
                    pass
        
        def load_from_database(e):
            """Load data from database to fill the form - now shows selection dialog"""
            load_database_records()
        
        def check_available_tables():
            """Check what tables exist in the database"""
            try:
                import psycopg2
                conn_str = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
                
                with psycopg2.connect(conn_str) as conn:
                    with conn.cursor() as cur:
                        # Check what tables exist
                        cur.execute("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = 'public'
                            ORDER BY table_name
                        """)
                        tables = cur.fetchall()
                        print("📋 Available tables in database:")
                        for table in tables:
                            print(f"  - {table[0]}")
                        return [table[0] for table in tables]
            except Exception as e:
                print(f"❌ Error checking tables: {e}")
                return []

        def auto_fill_first_record(e):
            """Auto-fill form with first record from database"""
            try:
                import psycopg2
                conn_str = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
                
                # First check available tables
                available_tables = check_available_tables()
                
                # Try different possible table names
                possible_tables = ['tax_certificates', 'certificate_records', 'certificates', 'transfer_records', 'withholding_tax']
                table_to_use = None
                
                for table_name in possible_tables:
                    if table_name in available_tables:
                        table_to_use = table_name
                        print(f"✅ Using table: {table_name}")
                        break
                
                if not table_to_use:
                    status_text.value = f"❌ ไม่พบตารางข้อมูลที่เหมาะสม (มีตาราง: {', '.join(available_tables)})"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                with psycopg2.connect(conn_str) as conn:
                    with conn.cursor() as cur:
                        # Get first record from the available table
                        # First, check what columns exist in the table
                        cur.execute(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = '{table_to_use}'
                            ORDER BY ordinal_position
                        """)
                        columns = [col[0] for col in cur.fetchall()]
                        print(f"📋 Columns in {table_to_use}: {columns}")
                        
                        # Get first record with available columns
                        cur.execute(f"SELECT * FROM {table_to_use} ORDER BY id ASC LIMIT 1")
                        
                        result = cur.fetchone()
                        if result:
                            # Create a mapping of column names to values
                            data_dict = dict(zip(columns, result))
                            print(f"📊 Data found: {len(result)} fields")
                            
                            # Fill form fields based on available data
                            # Use a flexible mapping approach
                            field_mappings = {
                                'withholder_name': ['withholder_name', 'holder_name', 'company_name', 'name'],
                                'withholder_address': ['withholder_address', 'holder_address', 'address'],
                                'withholder_tax_id': ['withholder_tax_id', 'holder_tax_id', 'tax_id'],
                                'withholdee_name': ['withholdee_name', 'holdee_name', 'employee_name'],
                                'withholdee_address': ['withholdee_address', 'holdee_address', 'employee_address'],
                                'withholdee_tax_id': ['withholdee_tax_id', 'holdee_tax_id', 'employee_tax_id'],
                                'certificate_book_no': ['certificate_book_no', 'book_no', 'book_number'],
                                'certificate_no': ['certificate_no', 'cert_no', 'number'],
                                'sequence_in_form': ['sequence_in_form', 'sequence', 'seq_no'],
                                'income_1_amount': ['income_1_amount', 'salary_amount', 'amount'],
                                'income_1_tax': ['income_1_tax', 'salary_tax', 'tax_amount'],
                                'income_2_amount': ['income_2_amount', 'bonus_amount', 'other_amount'],
                                'income_2_tax': ['income_2_tax', 'bonus_tax', 'other_tax'],
                                'issue_date': ['issue_date', 'date', 'created_date'],
                                'signatory_name': ['signatory_name', 'signer_name', 'issued_by']
                            }
                            
                            # Helper function to find value from multiple possible column names
                            def get_value_from_mapping(field_name):
                                possible_cols = field_mappings.get(field_name, [field_name])
                                for col in possible_cols:
                                    if col in data_dict and data_dict[col] is not None:
                                        return data_dict[col]
                                return ""
                            
                            # Fill the form fields
                            withholder_name.value = str(get_value_from_mapping('withholder_name'))
                            withholder_address.value = str(get_value_from_mapping('withholder_address'))
                            withholder_tax_id.value = str(get_value_from_mapping('withholder_tax_id'))
                            try:
                                fill_card_numbers_from_withholder_tax_id(None)
                            except Exception:
                                pass
                            
                            withholdee_name.value = str(get_value_from_mapping('withholdee_name'))
                            withholdee_address.value = str(get_value_from_mapping('withholdee_address'))
                            withholdee_tax_id.value = str(get_value_from_mapping('withholdee_tax_id'))
                            try:
                                fill_card_numbers_from_tax_id(None)
                            except Exception:
                                pass
                            
                            certificate_book_no.value = str(get_value_from_mapping('certificate_book_no'))
                            certificate_no.value = str(get_value_from_mapping('certificate_no'))
                            sequence_in_form.value = str(get_value_from_mapping('sequence_in_form'))
                            
                            income_1_amount.value = str(get_value_from_mapping('income_1_amount') or "0")
                            income_1_tax.value = str(get_value_from_mapping('income_1_tax') or "0")
                            income_2_amount.value = str(get_value_from_mapping('income_2_amount') or "0")
                            income_2_tax.value = str(get_value_from_mapping('income_2_tax') or "0")
                            
                            provident_fund.value = "0"
                            social_security_fund.value = "0"
                            retirement_mutual_fund.value = "0"
                            
                            issue_date.value = str(get_value_from_mapping('issue_date'))
                            signatory_name.value = str(get_value_from_mapping('signatory_name'))
                            company_seal.value = False
                            # If there is a pending withholder payload from the import tab, apply it now
                            try:
                                nonlocal pending_withholder_import_data
                                if pending_withholder_import_data:
                                    payload = pending_withholder_import_data
                                    if payload.get('withholder_name'):
                                        withholder_name.value = payload['withholder_name']
                                    if payload.get('withholder_address'):
                                        withholder_address.value = payload['withholder_address']
                                    if payload.get('withholder_tax_id'):
                                        withholder_tax_id.value = payload['withholder_tax_id']
                                        try:
                                            fill_card_numbers_from_withholder_tax_id(None)
                                        except Exception:
                                            pass
                                    pending_withholder_import_data = None
                            except Exception:
                                pass
                            
                            # Calculate totals
                            try:
                                v1 = float(income_1_amount.value) if (income_1_amount.value or "").strip() else 0.0
                                v2 = float(income_2_amount.value) if (income_2_amount.value or "").strip() else 0.0
                                t1 = float(income_1_tax.value) if (income_1_tax.value or "").strip() else 0.0
                                t2 = float(income_2_tax.value) if (income_2_tax.value or "").strip() else 0.0
                                total_income = v1 + v2
                                total_tax = t1 + t2
                                total_income_display.value = f"{total_income:,.2f}"
                                total_tax_display.value = f"{total_tax:,.2f}"
                            except:
                                total_income_display.value = "0.00"
                                total_tax_display.value = "0.00"
                            # Blank out zeros for numeric fields
                            try:
                                zero_like = {"0", "0.0", "0.00"}
                                for field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                                              provident_fund, social_security_fund, retirement_mutual_fund]:
                                    txt = (field.value or "").replace(",", "").strip()
                                    if txt in zero_like:
                                        field.value = ""
                            except Exception:
                                pass
                            
                            status_text.value = f"✅ โหลดข้อมูลรายการแรกจาก {table_to_use} เรียบร้อย"
                            status_text.color = ft.Colors.GREEN_700
                            
                            # Also load coordinate settings from database
                            load_coordinates_from_database()
                            
                            # Auto-fill withholder data from saved settings if available
                            try:
                                if pending_withholder_import_data:
                                    payload = pending_withholder_import_data
                                    if payload.get('withholder_name'):
                                        withholder_name.value = payload['withholder_name']
                                    if payload.get('withholder_address'):
                                        withholder_address.value = payload['withholder_address']
                                    if payload.get('withholder_tax_id'):
                                        withholder_tax_id.value = payload['withholder_tax_id']
                                    pending_withholder_import_data = None
                                    print("✅ Auto-filled withholder data from saved settings")
                            except Exception as ex:
                                print(f"Auto-fill withholder data error: {ex}")
                            
                            print(f"✅ Auto-filled form with first record from {table_to_use}")
                            
                        else:
                            status_text.value = f"⚠️ ไม่พบข้อมูลในตาราง {table_to_use}"
                            status_text.color = ft.Colors.ORANGE_700
                        
                        page.update()
                        
            except Exception as ex:
                status_text.value = f"❌ ข้อผิดพลาดในการโหลดข้อมูล: {str(ex)}"
                status_text.color = ft.Colors.RED_700
                page.update()
                print(f"🚫 Auto-fill error: {ex}")

        def auto_fill_from_selected_dashboard():
            """If a record was selected on the dashboard, load it into the form fields."""
            try:
                global selected_transfer_id_for_pdf
                
                # First check if we have data from temp file (higher priority)
                temp_file_path = os.path.join(os.getcwd(), "temp_dashboard_data.json")
                temp_data_loaded = False
                
                if os.path.exists(temp_file_path):
                    try:
                        with open(temp_file_path, 'r', encoding='utf-8') as f:
                            dashboard_data = json.load(f)
                        print(f"🔄 Found temp file data in auto_fill_from_selected_dashboard: {dashboard_data}")
                        
                        if dashboard_data and dashboard_data.get('withholder_name'):
                            # Use data from temp file (from dashboard button)
                            withholder_name.value = dashboard_data.get('withholder_name', '')
                            withholder_address.value = dashboard_data.get('withholder_address', '')
                            withholder_tax_id.value = dashboard_data.get('withholder_tax_id', '')
                            
                            status_text.value = f"✅ โหลดข้อมูลผู้หักภาษีจาก Dashboard: {dashboard_data.get('withholder_name', '')}"
                            status_text.color = ft.Colors.GREEN_700
                            page.update()
                            temp_data_loaded = True
                            print(f"✅ Loaded withholder data from temp file")
                    except Exception as file_ex:
                        print(f"❌ Failed to load temp file in auto_fill_from_selected_dashboard: {file_ex}")
                
                # If no temp data or temp data doesn't have withholder info, try selected_transfer_id_for_pdf
                if not temp_data_loaded and not selected_transfer_id_for_pdf:
                    print("⚠️ No temp data and no selected_transfer_id_for_pdf")
                    return
                    
                if not temp_data_loaded:
                    # Load from database using selected_transfer_id_for_pdf
                    import psycopg2
                    conn_str = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"

                    with psycopg2.connect(conn_str) as conn:
                        with conn.cursor() as cur:
                            # Try to fetch optional remark column if exists
                            try:
                                cur.execute(
                                """
                                SELECT id, name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount, created_at, remark
                                FROM transfer_records
                                WHERE id = %s
                                """,
                                    (selected_transfer_id_for_pdf,)
                                )
                            except Exception:
                                # Reset aborted transaction before fallback
                                try:
                                    conn.rollback()
                                except Exception:
                                    pass
                                cur.execute(
                                    """
                                    SELECT id, name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount, created_at
                                    FROM transfer_records
                                    WHERE id = %s
                                    """,
                                    (selected_transfer_id_for_pdf,)
                                )
                            rec = cur.fetchone()
                            if not rec:
                                return

                            # Unpack
                            # Unpack with optional remark at last position
                            _id, _name, _surname, _amount, _date, _idcard, _address, _percent, _total, _fee, _net, _created, *_rest = rec
                            _remark = _rest[0] if _rest else None

                            # Map to crystal report fields (fill what we have)
                            withholdee_name.value = f"{_name or ''} {_surname or ''}".strip()
                            withholdee_address.value = _address or ""
                            withholdee_tax_id.value = _idcard or ""
                            try:
                                fill_card_numbers_from_tax_id(None)
                            except Exception:
                                pass
                            # Helper to format numbers as empty when zero
                            def _fmt_amount(val):
                                try:
                                    v = float(val or 0)
                                    return "" if v == 0 else f"{v:.2f}"
                                except Exception:
                                    return ""
                            # Put transfer amount into income_1_amount for preview/fill convenience
                            income_1_amount.value = _fmt_amount(_amount)
                            # Map taxes: move fee tax into salary tax (income_1_tax), clear fee tax (income_2_tax)
                            if (_remark or "").strip() == "ค่าธรรมเนียม":
                                income_2_amount.value = ""
                                income_1_tax.value = _fmt_amount(_total or _fee)
                                income_2_tax.value = ""
                            elif (_remark or "").strip() == "เงินเดือน":
                                income_2_amount.value = _fmt_amount(_amount)
                                income_1_tax.value = ""
                                income_2_tax.value = ""
                            else:
                                # default behavior fallbacks
                                income_2_amount.value = ""
                                income_1_tax.value = _fmt_amount(_fee)
                                income_2_tax.value = ""
                            # Totals presentation (income total and tax total)
                            total_income_display.value = f"{float(_total or _amount or 0):,.2f}"
                            total_tax_display.value = f"{float(_fee or 0):,.2f}"
                            total_tax_text.value = ""
                            issue_date.value = str(_date) if _date else (issue_date.value or "")
                            certificate_no.value = str(_id)
                            # Always autofill dot markers
                            try:
                                dot_1.value = "."; dot_2.value = "."; dot_5.value = "."; dot_6.value = "."
                            except Exception:
                                pass

                            status_text.value = f"✅ โหลดจากแดชบอร์ด: ID {_id}"
                            status_text.color = ft.Colors.GREEN_700
                            page.update()
            except Exception as ex:
                print(f"Dashboard autofill error: {ex}")
        
        # Form fields
        print("📝 Creating form fields...")
        withholder_name = ft.TextField(label="ชื่อผู้มีหน้าที่หักภาษี", width=400)
        withholder_address = ft.TextField(label="ที่อยู่ผู้มีหน้าที่หักภาษี", width=600, multiline=True, max_lines=3)
        withholder_tax_id = ft.TextField(label="เลขประจำตัวผู้เสียภาษี", width=200, max_length=13)
        print("✅ Form fields created successfully")
        withholder_type = ft.Dropdown(
            label="ประเภท", width=200,
            options=[ft.dropdown.Option("บุคคล"), ft.dropdown.Option("นิติบุคคล"), 
                    ft.dropdown.Option("บริษัท"), ft.dropdown.Option("สมาคม")]
        )
        
        withholdee_name = ft.TextField(label="ชื่อผู้ถูกหักภาษี", width=400)
        withholdee_address = ft.TextField(label="ที่อยู่ผู้ถูกหักภาษี", width=600, multiline=True, max_lines=3)
        withholdee_tax_id = ft.TextField(label="เลขประจำตัวผู้เสียภาษี", width=200, max_length=13)
        withholdee_type = ft.Dropdown(
            label="ประเภท", width=200,
            options=[ft.dropdown.Option("บุคคล"), ft.dropdown.Option("นิติบุคคล")]
        )
        
        certificate_book_no = ft.TextField(label="เล่มที่", width=150)
        certificate_no = ft.TextField(label="เลขที่", width=150)
        sequence_in_form = ft.TextField(label="ลำดับที่ในแบบ", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        form_type = ft.Dropdown(
            label="ประเภทแบบ", width=200,
            options=[ft.dropdown.Option("ภ.ง.ด.1ก"), ft.dropdown.Option("ภ.ง.ด.2"), ft.dropdown.Option("ภ.ง.ด.3")]
        )
        
        # Income fields
        income_1_amount = ft.TextField(label="เงินเดือน", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="")
        income_1_tax = ft.TextField(label="ภาษี", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="")
        # Ten position boxes to split salary digits (ตำแหน่งที่ 1..10)
        salary_pos_1 = ft.TextField(label="ตำแหน่งที่ 1", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        salary_pos_2 = ft.TextField(label="ตำแหน่งที่ 2", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        salary_pos_3 = ft.TextField(label="ตำแหน่งที่ 3", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        salary_pos_4 = ft.TextField(label="ตำแหน่งที่ 4", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        salary_pos_5 = ft.TextField(label="ตำแหน่งที่ 5", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        salary_pos_6 = ft.TextField(label="ตำแหน่งที่ 6", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        salary_pos_7 = ft.TextField(label="ตำแหน่งที่ 7", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        salary_pos_8 = ft.TextField(label="ตำแหน่งที่ 8", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        salary_pos_9 = ft.TextField(label="ตำแหน่งที่ 9", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        salary_pos_10 = ft.TextField(label="ตำแหน่งที่ 10", width=70, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        # Ten position boxes for total income digits
        total_income_pos_1 = ft.TextField(label="รวมเงิน-ตำแหน่ง 1", width=80, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_income_pos_2 = ft.TextField(label="รวมเงิน-ตำแหน่ง 2", width=80, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_income_pos_3 = ft.TextField(label="รวมเงิน-ตำแหน่ง 3", width=80, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_income_pos_4 = ft.TextField(label="รวมเงิน-ตำแหน่ง 4", width=80, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_income_pos_5 = ft.TextField(label="รวมเงิน-ตำแหน่ง 5", width=80, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_income_pos_6 = ft.TextField(label="รวมเงิน-ตำแหน่ง 6", width=80, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_income_pos_7 = ft.TextField(label="รวมเงิน-ตำแหน่ง 7", width=80, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_income_pos_8 = ft.TextField(label="รวมเงิน-ตำแหน่ง 8", width=80, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_income_pos_9 = ft.TextField(label="รวมเงิน-ตำแหน่ง 9", width=80, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_income_pos_10 = ft.TextField(label="รวมเงิน-ตำแหน่ง 10", width=90, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        # Eight position boxes for total tax digits
        total_tax_pos_1 = ft.TextField(label="รวมภาษี-ตำแหน่ง 1", width=100, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_tax_pos_2 = ft.TextField(label="รวมภาษี-ตำแหน่ง 2", width=100, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_tax_pos_3 = ft.TextField(label="รวมภาษี-ตำแหน่ง 3", width=100, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_tax_pos_4 = ft.TextField(label="รวมภาษี-ตำแหน่ง 4", width=100, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_tax_pos_5 = ft.TextField(label="รวมภาษี-ตำแหน่ง 5", width=100, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_tax_pos_6 = ft.TextField(label="รวมภาษี-ตำแหน่ง 6", width=100, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_tax_pos_7 = ft.TextField(label="รวมภาษี-ตำแหน่ง 7", width=100, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        total_tax_pos_8 = ft.TextField(label="รวมภาษี-ตำแหน่ง 8", width=100, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        # Eight position boxes for salary tax digits
        tax_pos_1 = ft.TextField(label="ภาษี ตำแหน่งที่ 1", width=70, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        tax_pos_2 = ft.TextField(label="ภาษี ตำแหน่งที่ 2", width=70, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        tax_pos_3 = ft.TextField(label="ภาษี ตำแหน่งที่ 3", width=70, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        tax_pos_4 = ft.TextField(label="ภาษี ตำแหน่งที่ 4", width=70, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        tax_pos_5 = ft.TextField(label="ภาษี ตำแหน่งที่ 5", width=70, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        tax_pos_6 = ft.TextField(label="ภาษี ตำแหน่งที่ 6", width=70, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        tax_pos_7 = ft.TextField(label="ภาษี ตำแหน่งที่ 7", width=70, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        tax_pos_8 = ft.TextField(label="ภาษี ตำแหน่งที่ 8", width=70, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        # Ten position boxes for fee amount digits
        fee_pos_1 = ft.TextField(label="ค่าธรรมเนียม ตำแหน่งที่ 1", width=90, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_pos_2 = ft.TextField(label="ค่าธรรมเนียม ตำแหน่งที่ 2", width=90, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_pos_3 = ft.TextField(label="ค่าธรรมเนียม ตำแหน่งที่ 3", width=90, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_pos_4 = ft.TextField(label="ค่าธรรมเนียม ตำแหน่งที่ 4", width=90, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_pos_5 = ft.TextField(label="ค่าธรรมเนียม ตำแหน่งที่ 5", width=90, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_pos_6 = ft.TextField(label="ค่าธรรมเนียม ตำแหน่งที่ 6", width=90, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_pos_7 = ft.TextField(label="ค่าธรรมเนียม ตำแหน่งที่ 7", width=90, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_pos_8 = ft.TextField(label="ค่าธรรมเนียม ตำแหน่งที่ 8", width=90, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_pos_9 = ft.TextField(label="ค่าธรรมเนียม ตำแหน่งที่ 9", width=90, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_pos_10 = ft.TextField(label="ค่าธรรมเนียม ตำแหน่งที่ 10", width=100, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        # Eight position boxes for fee tax digits
        fee_tax_pos_1 = ft.TextField(label="ภาษีค่าธรรมเนียม ตำแหน่งที่ 1", width=130, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_tax_pos_2 = ft.TextField(label="ภาษีค่าธรรมเนียม ตำแหน่งที่ 2", width=130, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_tax_pos_3 = ft.TextField(label="ภาษีค่าธรรมเนียม ตำแหน่งที่ 3", width=130, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_tax_pos_4 = ft.TextField(label="ภาษีค่าธรรมเนียม ตำแหน่งที่ 4", width=130, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_tax_pos_5 = ft.TextField(label="ภาษีค่าธรรมเนียม ตำแหน่งที่ 5", width=130, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_tax_pos_6 = ft.TextField(label="ภาษีค่าธรรมเนียม ตำแหน่งที่ 6", width=130, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_tax_pos_7 = ft.TextField(label="ภาษีค่าธรรมเนียม ตำแหน่งที่ 7", width=130, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        fee_tax_pos_8 = ft.TextField(label="ภาษีค่าธรรมเนียม ตำแหน่งที่ 8", width=130, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        # Six dot boxes
        dot_1 = ft.TextField(label="dot 1", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        dot_2 = ft.TextField(label="dot 2", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        dot_3 = ft.TextField(label="dot 3", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        dot_4 = ft.TextField(label="dot 4", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        dot_5 = ft.TextField(label="dot 5", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        dot_6 = ft.TextField(label="dot 6", width=60, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        income_2_amount = ft.TextField(label="ค่าธรรมเนียม", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="")
        income_2_tax = ft.TextField(label="ภาษี", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="")
        
        # Fund fields
        provident_fund = ft.TextField(label="กบข.", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="")
        social_security_fund = ft.TextField(label="ประกันสังคม", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="")
        retirement_mutual_fund = ft.TextField(label="กองทุนเลี้ยงชีพ", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="")
        
        # Issue fields
        issue_type = ft.Dropdown(
            label="ประเภทการออกใบรับรอง", width=200,
            options=[ft.dropdown.Option("หักณที่จ่าย"), ft.dropdown.Option("ออกให้ตลอดไป")]
        )
        issue_date = ft.TextField(label="วันที่", width=200)
        fee_payment_date = ft.TextField(label="วันที่ชำระค่าธรรมเนียม", width=200)
        signatory_name = ft.TextField(label="ชื่อผู้จ่ายเงิน", width=300)
        company_seal = ft.Checkbox(label="ประทับตรา", value=False)
        # Extra inputs: เลขบัตร 10 ตำแหน่ง (ใช้ใส่ข้อความลง PDF ไม่บันทึกฐานข้อมูล)
        card_number_1 = ft.TextField(label="เลขที่บัตร 1", width=180)
        card_number_2 = ft.TextField(label="เลขที่บัตร 2", width=180)
        card_number_3 = ft.TextField(label="เลขที่บัตร 3", width=180)
        card_number_4 = ft.TextField(label="เลขที่บัตร 4", width=180)
        card_number_5 = ft.TextField(label="เลขที่บัตร 5", width=180)
        card_number_6 = ft.TextField(label="เลขที่บัตร 6", width=180)
        card_number_7 = ft.TextField(label="เลขที่บัตร 7", width=180)
        card_number_8 = ft.TextField(label="เลขที่บัตร 8", width=180)
        card_number_9 = ft.TextField(label="เลขที่บัตร 9", width=180)
        card_number_10 = ft.TextField(label="เลขที่บัตร 10", width=180)

        # New: 13-digit ID inputs for both withholdee (ผู้ถูกหัก) and withholder (ผู้หัก)
        withholdee_id_1 = ft.TextField(label="ผู้ถูกหัก 1", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholdee_id_2 = ft.TextField(label="ผู้ถูกหัก 2", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholdee_id_3 = ft.TextField(label="ผู้ถูกหัก 3", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholdee_id_4 = ft.TextField(label="ผู้ถูกหัก 4", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholdee_id_5 = ft.TextField(label="ผู้ถูกหัก 5", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholdee_id_6 = ft.TextField(label="ผู้ถูกหัก 6", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholdee_id_7 = ft.TextField(label="ผู้ถูกหัก 7", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholdee_id_8 = ft.TextField(label="ผู้ถูกหัก 8", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholdee_id_9 = ft.TextField(label="ผู้ถูกหัก 9", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholdee_id_10 = ft.TextField(label="ผู้ถูกหัก 10", width=46, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholdee_id_11 = ft.TextField(label="ผู้ถูกหัก 11", width=46, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholdee_id_12 = ft.TextField(label="ผู้ถูกหัก 12", width=46, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholdee_id_13 = ft.TextField(label="ผู้ถูกหัก 13", width=46, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)

        withholder_id_1 = ft.TextField(label="ผู้หัก 1", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholder_id_2 = ft.TextField(label="ผู้หัก 2", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholder_id_3 = ft.TextField(label="ผู้หัก 3", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholder_id_4 = ft.TextField(label="ผู้หัก 4", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholder_id_5 = ft.TextField(label="ผู้หัก 5", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholder_id_6 = ft.TextField(label="ผู้หัก 6", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholder_id_7 = ft.TextField(label="ผู้หัก 7", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholder_id_8 = ft.TextField(label="ผู้หัก 8", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholder_id_9 = ft.TextField(label="ผู้หัก 9", width=40, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholder_id_10 = ft.TextField(label="ผู้หัก 10", width=46, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholder_id_11 = ft.TextField(label="ผู้หัก 11", width=46, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholder_id_12 = ft.TextField(label="ผู้หัก 12", width=46, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)
        withholder_id_13 = ft.TextField(label="ผู้หัก 13", width=46, max_length=1, keyboard_type=ft.KeyboardType.NUMBER)

        def fill_card_numbers_from_tax_id(e=None):
            try:
                taxid = ''.join([ch for ch in (withholdee_tax_id.value or '') if ch.isdigit()])
                if len(taxid) == 13:
                    # Fill grouped 10 boxes into positions 1–5 from withholdee tax id
                    card_number_1.value = taxid[0]
                    card_number_2.value = taxid[1:5]
                    card_number_3.value = taxid[5:10]
                    card_number_4.value = taxid[10:12]
                    card_number_5.value = taxid[12]
                    # Cross-fill: put withholdee tax id into withholder 13 boxes
                    withholder_id_1.value = taxid[0]
                    withholder_id_2.value = taxid[1]
                    withholder_id_3.value = taxid[2]
                    withholder_id_4.value = taxid[3]
                    withholder_id_5.value = taxid[4]
                    withholder_id_6.value = taxid[5]
                    withholder_id_7.value = taxid[6]
                    withholder_id_8.value = taxid[7]
                    withholder_id_9.value = taxid[8]
                    withholder_id_10.value = taxid[9]
                    withholder_id_11.value = taxid[10]
                    withholder_id_12.value = taxid[11]
                    withholder_id_13.value = taxid[12]
                else:
                    card_number_1.value = card_number_2.value = card_number_3.value = card_number_4.value = card_number_5.value = ""
                    withholder_id_1.value = withholder_id_2.value = withholder_id_3.value = withholder_id_4.value = withholder_id_5.value = ""
                    withholder_id_6.value = withholder_id_7.value = withholder_id_8.value = withholder_id_9.value = withholder_id_10.value = ""
                    withholder_id_11.value = withholder_id_12.value = withholder_id_13.value = ""
                page.update()
            except Exception:
                card_number_1.value = card_number_2.value = card_number_3.value = card_number_4.value = card_number_5.value = ""
                withholder_id_1.value = withholder_id_2.value = withholder_id_3.value = withholder_id_4.value = withholder_id_5.value = ""
                withholder_id_6.value = withholder_id_7.value = withholder_id_8.value = withholder_id_9.value = withholder_id_10.value = ""
                withholder_id_11.value = withholder_id_12.value = withholder_id_13.value = ""
                page.update()

        def fill_card_numbers_from_withholder_tax_id(e=None):
            try:
                taxid = ''.join([ch for ch in (withholder_tax_id.value or '') if ch.isdigit()])
                if len(taxid) == 13:
                    # Cross-fill: put withholder tax id into withholdee 13 boxes
                    withholdee_id_1.value = taxid[0]
                    withholdee_id_2.value = taxid[1]
                    withholdee_id_3.value = taxid[2]
                    withholdee_id_4.value = taxid[3]
                    withholdee_id_5.value = taxid[4]
                    withholdee_id_6.value = taxid[5]
                    withholdee_id_7.value = taxid[6]
                    withholdee_id_8.value = taxid[7]
                    withholdee_id_9.value = taxid[8]
                    withholdee_id_10.value = taxid[9]
                    withholdee_id_11.value = taxid[10]
                    withholdee_id_12.value = taxid[11]
                    withholdee_id_13.value = taxid[12]
                else:
                    withholdee_id_1.value = withholdee_id_2.value = withholdee_id_3.value = withholdee_id_4.value = withholdee_id_5.value = ""
                    withholdee_id_6.value = withholdee_id_7.value = withholdee_id_8.value = withholdee_id_9.value = withholdee_id_10.value = ""
                    withholdee_id_11.value = withholdee_id_12.value = withholdee_id_13.value = ""
                page.update()
            except Exception:
                withholdee_id_1.value = withholdee_id_2.value = withholdee_id_3.value = withholdee_id_4.value = withholdee_id_5.value = ""
                withholdee_id_6.value = withholdee_id_7.value = withholdee_id_8.value = withholdee_id_9.value = withholdee_id_10.value = ""
                withholdee_id_11.value = withholdee_id_12.value = withholdee_id_13.value = ""
                page.update()
        
        # Total fields
        total_income_display = ft.TextField(label="รวมเงินที่จ่าย", width=200, read_only=True)
        total_tax_display = ft.TextField(label="รวมภาษีหัก", width=200, read_only=True)
        total_tax_text = ft.TextField(label="ตัวอักษร", width=400)
        
        last_certificate_id = None
        
        # --- Helper: Convert number to Thai Baht text ---
        def _thai_number_text(n: int) -> str:
            digits = ["ศูนย์", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
            positions = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน"]
            if n == 0:
                return "ศูนย์"
            parts = []
            million_unit = 0
            while n > 0:
                group = n % 1000000
                n //= 1000000
                txt = ""
                num = group
                pos = 0
                while num > 0:
                    d = num % 10
                    if d != 0:
                        word = digits[d]
                        if pos == 1:
                            if d == 2:
                                word = "ยี่"
                            elif d == 1:
                                word = ""
                            word += positions[pos]
                        elif pos == 0 and d == 1 and group > 10:
                            word = "เอ็ด"
                        else:
                            word += positions[pos]
                        txt = word + txt
                    pos += 1
                    num //= 10
                if million_unit > 0 and group == 0:
                    parts.insert(0, "ศูนย์ล้าน")
                elif million_unit > 0:
                    parts.insert(0, txt + "ล้าน")
                else:
                    parts.insert(0, txt)
                million_unit += 1
            return "".join(parts).strip()

        def _baht_text(amount: float) -> str:
            try:
                amt = float(amount or 0)
            except Exception:
                amt = 0.0
            baht = int(amt)
            satang = int(round((amt - baht) * 100))
            result = ""
            if baht > 0:
                result += _thai_number_text(baht) + "บาท"
            if satang > 0:
                result += _thai_number_text(satang) + "สตางค์"
            if result == "":
                result = "ศูนย์บาทถ้วน"
            if satang == 0 and baht > 0:
                result += "ถ้วน"
            return result

        def calculate_totals():
            try:
                v1 = float(income_1_amount.value) if (income_1_amount.value or "").strip() else 0.0
                v2 = float(income_2_amount.value) if (income_2_amount.value or "").strip() else 0.0
                t1 = float(income_1_tax.value) if (income_1_tax.value or "").strip() else 0.0
                t2 = float(income_2_tax.value) if (income_2_tax.value or "").strip() else 0.0
                total_income = v1 + v2
                total_tax = t1 + t2
                
                total_income_display.value = f"{total_income:,.2f}"
                total_tax_display.value = f"{total_tax:,.2f}"
                # Update Thai words for total income
                try:
                    total_tax_text.value = _baht_text(total_income)
                except Exception:
                    pass
                # Auto-split income_1_amount digits into salary_pos_1..10 (right aligned by last digits)
                try:
                    s = ''.join([ch for ch in (income_1_amount.value or '') if ch.isdigit()])
                    # keep up to 10 last digits
                    s = s[-10:]
                    slots = ["", "", "", "", "", "", "", "", "", ""]
                    # fill from rightmost
                    for i, ch in enumerate(reversed(s)):
                        slots[-(i+1)] = ch
                    salary_pos_1.value, salary_pos_2.value, salary_pos_3.value, salary_pos_4.value, salary_pos_5.value, \
                    salary_pos_6.value, salary_pos_7.value, salary_pos_8.value, salary_pos_9.value, salary_pos_10.value = slots
                except Exception:
                    pass
                # Auto-split taxes and fees similarly
                try:
                    ts = ''.join([ch for ch in (income_1_tax.value or '') if ch.isdigit()])[-8:]
                    tslots = ["", "", "", "", "", "", "", ""]
                    for i, ch in enumerate(reversed(ts)):
                        tslots[-(i+1)] = ch
                    tax_pos_1.value, tax_pos_2.value, tax_pos_3.value, tax_pos_4.value, tax_pos_5.value, tax_pos_6.value, tax_pos_7.value, tax_pos_8.value = tslots
                except Exception:
                    pass
                try:
                    fs = ''.join([ch for ch in (income_2_amount.value or '') if ch.isdigit()])[-10:]
                    fslots = ["", "", "", "", "", "", "", "", "", ""]
                    for i, ch in enumerate(reversed(fs)):
                        fslots[-(i+1)] = ch
                    fee_pos_1.value, fee_pos_2.value, fee_pos_3.value, fee_pos_4.value, fee_pos_5.value, \
                    fee_pos_6.value, fee_pos_7.value, fee_pos_8.value, fee_pos_9.value, fee_pos_10.value = fslots
                except Exception:
                    pass
                try:
                    fts = ''.join([ch for ch in (income_2_tax.value or '') if ch.isdigit()])[-8:]
                    ft_slots = ["", "", "", "", "", "", "", ""]
                    for i, ch in enumerate(reversed(fts)):
                        ft_slots[-(i+1)] = ch
                    fee_tax_pos_1.value, fee_tax_pos_2.value, fee_tax_pos_3.value, fee_tax_pos_4.value, fee_tax_pos_5.value, fee_tax_pos_6.value, fee_tax_pos_7.value, fee_tax_pos_8.value = ft_slots
                except Exception:
                    pass
                # Auto-split total income and total tax
                try:
                    tis = ''.join([ch for ch in (total_income_display.value or '') if ch.isdigit()])[-10:]
                    tislots = ["", "", "", "", "", "", "", "", "", ""]
                    for i, ch in enumerate(reversed(tis)):
                        tislots[-(i+1)] = ch
                    total_income_pos_1.value, total_income_pos_2.value, total_income_pos_3.value, total_income_pos_4.value, total_income_pos_5.value, \
                    total_income_pos_6.value, total_income_pos_7.value, total_income_pos_8.value, total_income_pos_9.value, total_income_pos_10.value = tislots
                except Exception:
                    pass
                try:
                    tts = ''.join([ch for ch in (total_tax_display.value or '') if ch.isdigit()])[-8:]
                    ttslots = ["", "", "", "", "", "", "", ""]
                    for i, ch in enumerate(reversed(tts)):
                        ttslots[-(i+1)] = ch
                    total_tax_pos_1.value, total_tax_pos_2.value, total_tax_pos_3.value, total_tax_pos_4.value, total_tax_pos_5.value, total_tax_pos_6.value, total_tax_pos_7.value, total_tax_pos_8.value = ttslots
                except Exception:
                    pass
                page.update()
            except ValueError:
                pass
        
        # Event listeners
        for field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax]:
            field.on_change = lambda e: calculate_totals()
        # Auto-fill 13-digit boxes and grouped boxes when tax IDs change (no button needed)
        try:
            withholdee_tax_id.on_change = lambda e: fill_card_numbers_from_tax_id(e)
            withholder_tax_id.on_change = lambda e: fill_card_numbers_from_withholder_tax_id(e)
        except Exception:
            pass
        
        # Helper: blank out zeros shown in numeric text fields
        def blank_out_zero_fields():
            zero_like = {"0", "0.0", "0.00"}
            for field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                          provident_fund, social_security_fund, retirement_mutual_fund]:
                try:
                    txt = (field.value or "").replace(",", "").strip()
                    if txt in zero_like:
                        field.value = ""
                except Exception:
                    continue
            try:
                page.update()
            except Exception:
                pass

        # Auto-load first record and coordinates on startup
        try:
            auto_fill_first_record(None)  # Pass None since we don't need the event
        except Exception as e:
            print(f"⚠️ Could not auto-load first record on startup: {e}")
            # Just load coordinates if record loading fails
            load_coordinates_from_database()
        # Ensure zero values are shown as blank on initial load
        blank_out_zero_fields()
        
        def save_form(e):
            nonlocal last_certificate_id
            try:
                if not all([withholder_name.value, withholder_tax_id.value, 
                           withholdee_name.value, withholdee_tax_id.value]):
                    status_text.value = "❌ กรุณากรอกข้อมูลที่จำเป็น"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return
                
                data = (
                    withholder_name.value, withholder_address.value, withholder_tax_id.value, withholder_type.value or "บุคคล",
                    withholdee_name.value, withholdee_address.value, withholdee_tax_id.value, withholdee_type.value or "บุคคล",
                    certificate_book_no.value, certificate_no.value, 
                    int(sequence_in_form.value) if sequence_in_form.value else None, form_type.value,
                    float(income_1_amount.value) if (income_1_amount.value or "").strip() else 0.0,
                    float(income_1_tax.value) if (income_1_tax.value or "").strip() else 0.0,
                    float(income_2_amount.value) if (income_2_amount.value or "").strip() else 0.0,
                    float(income_2_tax.value) if (income_2_tax.value or "").strip() else 0.0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None,  # Other income fields
                    float(total_income_display.value.replace(',', '') or 0), 
                    float(total_tax_display.value.replace(',', '') or 0), total_tax_text.value,
                    float(provident_fund.value) if (provident_fund.value or "").strip() else 0.0,
                    float(social_security_fund.value) if (social_security_fund.value or "").strip() else 0.0,
                    float(retirement_mutual_fund.value) if (retirement_mutual_fund.value or "").strip() else 0.0,
                    issue_type.value, None, issue_date.value or None, 
                    signatory_name.value, company_seal.value
                )
                
                certificate_id = crystal_renderer.save_certificate(data)
                
                if certificate_id:
                    last_certificate_id = certificate_id
                    status_text.value = f"✅ บันทึกเรียบร้อย (ID: {certificate_id})"
                    status_text.color = ft.Colors.GREEN_700
                    generate_crystal_pdf_button.disabled = False
                    page.update()
                
            except Exception as ex:
                status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                status_text.color = ft.Colors.RED_700
            
            page.update()
        
        def generate_crystal_pdf(e):
            nonlocal last_certificate_id
            
            if not last_certificate_id:
                status_text.value = "❌ กรุณาบันทึกข้อมูลก่อน"
                status_text.color = ft.Colors.RED_700
                page.update()
                return
            
            try:
                cert_data = crystal_renderer.get_certificate_by_id(last_certificate_id)
                if cert_data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_filename = f"crystal_report_{last_certificate_id}_{timestamp}.pdf"
                    success, message = crystal_renderer.create_crystal_report_pdf(cert_data, pdf_filename)
                    
                    if success:
                        status_text.value = f"✅ {message}"
                        status_text.color = ft.Colors.GREEN_700
                        
                        # Show success dialog
                        def close_dialog(e):
                            dialog.open = False
                            page.update()
                        
                        dialog = ft.AlertDialog(
                            title=ft.Text("Crystal Reports Style PDF สร้างสำเร็จ! 📊", color=ft.Colors.GREEN_700, size=18),
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.icons.ANALYTICS, size=40, color=ft.Colors.BLUE_700),
                                        ft.Column([
                                            ft.Text("PDF ถูกสร้างด้วยเทคนิค Crystal Reports!", weight=ft.FontWeight.BOLD),
                                            ft.Text("ใช้ภาพพื้นหลังต้นฉบับพร้อมระบบ Sections", color=ft.Colors.BLUE_700)
                                        ], spacing=5)
                                    ], spacing=10),
                                    ft.Divider(),
                                    ft.Column([
                                        ft.Row([ft.Icon(ft.icons.FOLDER, size=16, color=ft.Colors.BLUE_700), 
                                               ft.Text(f"ไฟล์: {pdf_filename}", size=12, weight=ft.FontWeight.BOLD)]),
                                        ft.Row([ft.Icon(ft.icons.LOCATION_ON, size=16, color=ft.Colors.BLUE_700), 
                                               ft.Text(f"ตำแหน่ง: {os.path.abspath(pdf_filename)}", size=12)]),
                                        ft.Row([ft.Icon(ft.icons.FINGERPRINT, size=16, color=ft.Colors.BLUE_700), 
                                               ft.Text(f"ID: {last_certificate_id}", size=12)]),
                                    ], spacing=8),
                                    ft.Divider(),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("🏗️ เทคนิค Crystal Reports ที่ใช้:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                                            ft.Text("• Page Header / Report Header / Detail Section", size=12),
                                            ft.Text("• Report Footer / Page Footer Structure", size=12),
                                            ft.Text("• Field Objects with Precise Positioning", size=12),
                                            ft.Text("• Formula Fields for Calculations", size=12),
                                            ft.Text("• Background Image Integration", size=12),
                                            ft.Text("• Multi-line Text with Can Grow", size=12),
                                            ft.Text("• Professional Report Layout", size=12),
                                        ], spacing=5),
                                        bgcolor=ft.Colors.GREEN_50,
                                        padding=15,
                                        border_radius=10
                                    )
                                ], spacing=15),
                                width=600
                            ),
                            actions=[
                                ft.TextButton("🎉 ยอดเยี่ยม!", on_click=close_dialog,
                                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE))
                            ]
                        )
                        page.dialog = dialog
                        dialog.open = True
                        
                    else:
                        status_text.value = f"❌ {message}"
                        status_text.color = ft.Colors.RED_700
                
            except Exception as ex:
                status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                status_text.color = ft.Colors.RED_700
            
            page.update()
        
        def clear_form(e):
            nonlocal last_certificate_id
            last_certificate_id = None
            generate_crystal_pdf_button.disabled = True
            
            # Clear fields
            for field in [withholder_name, withholder_address, withholder_tax_id,
                          withholdee_name, withholdee_address, withholdee_tax_id,
                          certificate_book_no, certificate_no, sequence_in_form,
                          income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                          provident_fund, social_security_fund, retirement_mutual_fund,
                          issue_date, signatory_name, total_tax_text]:
                if hasattr(field, 'value'):
                    field.value = "0" if field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                                                   provident_fund, social_security_fund, retirement_mutual_fund] else ""
            
            for dropdown in [withholder_type, withholdee_type, form_type, issue_type]:
                dropdown.value = None
            
            company_seal.value = False
            calculate_totals()
            page.update()
        
        def view_certificates(e):
            certificates = crystal_renderer.get_all_certificates()
            
            if not certificates:
                status_text.value = "ไม่มีข้อมูลในฐานข้อมูล"
                status_text.color = ft.Colors.ORANGE_700
                page.update()
                return
            
            columns = [
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("ผู้หักภาษี")),
                ft.DataColumn(ft.Text("ผู้ถูกหักภาษี")),
                ft.DataColumn(ft.Text("ยอดรวม")),
                ft.DataColumn(ft.Text("Crystal PDF"))
            ]
            
            def generate_crystal_for_cert(certificate_id):
                try:
                    cert_data = crystal_renderer.get_certificate_by_id(certificate_id)
                    if cert_data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        pdf_filename = f"crystal_style_{certificate_id}_{timestamp}.pdf"
                        success, message = crystal_renderer.create_crystal_report_pdf(cert_data, pdf_filename)
                        
                        if success:
                            status_text.value = f"✅ Crystal PDF: {pdf_filename}"
                            status_text.color = ft.Colors.GREEN_700
                        else:
                            status_text.value = f"❌ {message}"
                            status_text.color = ft.Colors.RED_700
                            
                except Exception as ex:
                    status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                    status_text.color = ft.Colors.RED_700
                
                dialog.open = False
                page.update()
            
            rows = []
            for cert in certificates:
                crystal_button = ft.IconButton(
                    icon=ft.icons.ANALYTICS,
                    tooltip="สร้าง Crystal Reports PDF",
                    icon_color=ft.Colors.GREEN_700,
                    on_click=lambda e, cert_id=cert[0]: generate_crystal_for_cert(cert_id)
                )
                
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(cert[0]))),
                    ft.DataCell(ft.Text(cert[1][:15] + "..." if len(cert[1]) > 15 else cert[1])),
                    ft.DataCell(ft.Text(cert[2][:15] + "..." if len(cert[2]) > 15 else cert[2])),
                    ft.DataCell(ft.Text(f"฿{cert[3]:,.2f}" if cert[3] else "0")),
                    ft.DataCell(crystal_button)
                ]))
            
            data_table = ft.DataTable(columns=columns, rows=rows)
            
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text(f"รายการใบรับรอง ({len(certificates)} รายการ)"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("📊 คลิกปุ่มเขียวเพื่อสร้าง PDF แบบ Crystal Reports", size=12, color=ft.Colors.GREEN_700),
                        data_table
                    ], scroll=ft.ScrollMode.AUTO),
                    width=900,
                    height=500
                ),
                actions=[ft.TextButton("ปิด", on_click=close_dialog)]
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        # Crystal Reports PDF generation button
        generate_crystal_pdf_button = ft.ElevatedButton(
            "📊 สร้าง Crystal Reports PDF", 
            on_click=generate_crystal_pdf,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            disabled=True,
            tooltip="บันทึกข้อมูลก่อนเพื่อสร้าง PDF แบบ Crystal Reports"
        )
        
        # Apply withholder payload from import tab
        def apply_withholder_payload(e):
            nonlocal pending_withholder_import_data
            try:
                if not pending_withholder_import_data:
                    status_text.value = "❌ ไม่มีข้อมูลผู้หักภาษีที่เลือกจากแท็บนำเข้า"
                    status_text.color = ft.Colors.RED_700
                    page.update();
                    return
                payload = pending_withholder_import_data or {}
                withholder_name.value = payload.get('withholder_name', '') or ''
                withholder_address.value = payload.get('withholder_address', '') or ''
                withholder_tax_id.value = payload.get('withholder_tax_id', '') or ''
                pending_withholder_import_data = None
                status_text.value = "✅ เติมข้อมูลผู้มีหน้าที่หักภาษีจากแท็บนำเข้าแล้ว"
                status_text.color = ft.Colors.GREEN_700
                page.update()
            except Exception as ex:
                status_text.value = f"❌ เติมข้อมูลไม่สำเร็จ: {ex}"
                status_text.color = ft.Colors.RED_700
                page.update()

        # Auto-fill ONLY withholdee from Dashboard selection (button handler)
        def auto_fill_from_selected_dashboard():
            try:
                # Preferred source: fetch by selected_transfer_id_for_pdf from Neon DB
                record = {}
                try:
                    selected_id = globals().get('selected_transfer_id_for_pdf', None)
                except Exception:
                    selected_id = None

                if selected_id:
                    try:
                        import psycopg2
                        conn_str = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
                        with psycopg2.connect(conn_str) as conn:
                            with conn.cursor() as cur:
                                try:
                                    cur.execute(
                                        """
                                        SELECT id, name, surname, transfer_amount, transfer_date, id_card, address, percent, total_amount, fee, net_amount
                                        FROM transfer_records
                                        WHERE id = %s
                                        """,
                                        (selected_id,)
                                    )
                                except Exception:
                                    conn.rollback()
                                    raise
                                row = cur.fetchone()
                                if row:
                                    record = {
                                        'id': row[0],
                                        'name': row[1],
                                        'surname': row[2],
                                        'transfer_amount': float(row[3] or 0),
                                        'transfer_date': row[4],
                                        'id_card': row[5],
                                        'address': row[6],
                                        'percent': float(row[7] or 0),
                                        'total_amount': float(row[8] or 0),
                                        'fee': float(row[9] or 0),
                                        'net_amount': float(row[10] or 0),
                                    }
                    except Exception as db_ex:
                        print(f"DB fetch error in auto_fill_from_selected_dashboard: {db_ex}")

                # Fallback: temp file or global payload
                if not record:
                    temp_file_path = os.path.join(os.getcwd(), "temp_dashboard_data.json")
                    dashboard_data = None
                    if os.path.exists(temp_file_path):
                        try:
                            with open(temp_file_path, 'r', encoding='utf-8') as f:
                                dashboard_data = json.load(f)
                        except Exception as file_ex:
                            print(f"❌ Failed to read temp_dashboard_data.json: {file_ex}")
                            dashboard_data = None
                    if dashboard_data is None:
                        dashboard_data = globals().get('dashboard_to_crystal_data', None)
                    if dashboard_data and dashboard_data.get('transfer_record'):
                        record = dashboard_data.get('transfer_record') or {}

                if not record:
                    status_text.value = "❌ ไม่พบข้อมูลจาก Dashboard/ฐานข้อมูล"
                    status_text.color = ft.Colors.RED_700
                    page.update()
                    return

                # Fill withholdee fields unconditionally so panel reflects the selected record immediately
                full_name = f"{record.get('name', '')} {record.get('surname', '')}".strip()
                withholdee_name.value = full_name
                withholdee_address.value = record.get('address', '') or ''
                withholdee_tax_id.value = record.get('id_card', '') or ''
                try:
                    # Ensure both 13-digit sections are populated
                    fill_card_numbers_from_tax_id(None)
                    fill_card_numbers_from_withholder_tax_id(None)
                except Exception:
                    pass
                # Also bring withholder data into the panel automatically (as if pressing the fill button)
                try:
                    apply_withholder_payload(None)
                except Exception:
                    pass
                try:
                    auto_fill_withholder_data()
                except Exception:
                    pass

                transfer_amount = 0.0
                fee = 0.0
                try:
                    transfer_amount = float(record.get('transfer_amount') or 0)
                except Exception:
                    pass
                try:
                    fee = float(record.get('fee') or 0)
                except Exception:
                    pass

                def _fmt_amount2(val):
                    try:
                        v = float(val or 0)
                        return "" if v == 0 else f"{v:.2f}"
                    except Exception:
                        return ""
                income_1_amount.value = _fmt_amount2(transfer_amount)
                # Move fee tax into salary tax field; clear fee tax
                income_1_tax.value = _fmt_amount2(fee)
                income_2_amount.value = ""
                income_2_tax.value = ""

                total_income_display.value = f"{transfer_amount:,.2f}"
                total_tax_display.value = f"{fee:,.2f}"

                # Fill date fields if missing (use transfer_date/date from selected record)
                try:
                    date_val = record.get('transfer_date') or record.get('date') or ""
                    if not (issue_date.value or '').strip():
                        issue_date.value = str(date_val) if date_val is not None else ''
                    # Do not auto-fill fee payment date; leave it blank
                    fee_payment_date.value = ''
                except Exception:
                    pass
                # Always autofill dot markers
                try:
                    dot_1.value = "."; dot_2.value = "."; dot_5.value = "."; dot_6.value = "."
                except Exception:
                    pass

                # Recompute digit slots
                try:
                    calculate_totals()
                except Exception:
                    pass

                status_text.value = "✅ โหลดผู้ถูกหักภาษีจากข้อมูลที่เลือกสำเร็จ (ไม่แก้ผู้หักภาษี/ไม่ทับค่าที่มีอยู่)"
                status_text.color = ft.Colors.GREEN_700
                page.update()

                # Auto-generate PDF immediately using current coordinates (no manual action required)
                try:
                    import threading, time
                    def _auto_generate_pdf():
                        try:
                            time.sleep(0.3)  # ensure UI values are set
                            fill_and_save_pdf(None)
                            print("✅ Auto-generated PDF after dashboard selection")
                        except Exception as gen_ex:
                            print(f"❌ Auto-generate PDF error: {gen_ex}")
                    threading.Thread(target=_auto_generate_pdf, daemon=True).start()
                except Exception as _th_ex:
                    print(f"❌ Could not start auto-generate thread: {_th_ex}")
            except Exception as ex:
                print(f"❌ Failed auto_fill_from_selected_dashboard: {ex}")
        # Make this fill function accessible globally so other tabs/threads can invoke it reliably
        try:
            globals()['auto_fill_from_selected_dashboard'] = auto_fill_from_selected_dashboard
        except Exception:
            pass
        
        return ft.Container(
            content=ft.Column([
                # Header with Crystal Reports info and PDF preview
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.ANALYTICS, size=40, color=ft.Colors.GREEN_700),
                            ft.Column([
                                ft.Text("Crystal Reports Style PDF Generator", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Professional Report Engine with Background Image Support", size=14, color=ft.Colors.GREY_700),
                                template_status
                            ], spacing=2)
                        ]),
                        ft.Divider(height=1, color=ft.Colors.GREY_300),
                        # PDF preview block (form.pdf -> image) + picker
                        ft.Container(
                            content=ft.Column([
                                ft.Text("แสดงตัวอย่างไฟล์ PDF (form.pdf)", size=12, color=ft.Colors.GREY_700),
                                ft.Row([
                                    pdf_path_text_control,
                                    ft.ElevatedButton("เลือกไฟล์ PDF", icon=ft.icons.UPLOAD_FILE, on_click=pick_pdf),
                                    ft.ElevatedButton("🔄 รีเซ็ต PDF", on_click=reset_pdf_preview,
                                                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_700, color=ft.Colors.WHITE)),
                                ], spacing=10),
                                main_pdf_container
                            ], spacing=8),
                            bgcolor=ft.Colors.GREY_50,
                            padding=10,
                            border_radius=8,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.ARCHITECTURE, size=16, color=ft.Colors.GREEN_700),
                                    ft.Text("เทคนิค Crystal Reports: Report Sections, Field Objects, Formula Fields, Background Integration", 
                                           size=12, color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD)
                                ], spacing=5),
                                ft.Row([
                                    ft.Icon(ft.icons.LAYERS, size=16, color=ft.Colors.BLUE_700),
                                    ft.Text("• Page/Report Headers • Detail Section • Calculated Fields • Professional Layout • High DPI Output", 
                                           size=11, color=ft.Colors.BLUE_700)
                                ], spacing=5)
                            ], spacing=5),
                            bgcolor=ft.Colors.GREEN_50,
                            padding=15,
                            border_radius=10
                        )
                    ], spacing=10),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=10,
                    padding=20,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Action buttons
                ft.Row([
                    ft.ElevatedButton("💾 บันทึกข้อมูล", on_click=save_form, 
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)),
                    generate_crystal_pdf_button,
                    ft.ElevatedButton("👁️ แสดง PDF", on_click=preview_pdf_with_data,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("📄 กรอกใน PDF", on_click=fill_and_save_pdf,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("🧪 ทดสอบภาษาไทย", on_click=test_thai_text_pdf,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.DEEP_ORANGE_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("📋 เลือกจากฐานข้อมูล", on_click=load_from_database,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("⬇️ ดึงข้อมูลที่เลือก", on_click=lambda e: auto_fill_from_selected_dashboard(),
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                                    tooltip="ดึงข้อมูลจากแถวที่เลือกในหน้าแรกมาใส่ผู้ถูกหักภาษี"),
                    ft.ElevatedButton("📥 ดึงข้อมูลผู้หักภาษี", on_click=apply_withholder_payload,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.TEAL_700, color=ft.Colors.WHITE),
                                    tooltip="นำข้อมูลผู้หักภาษีจากแท็บ\n'นำเข้าผู้หักภาษีจาก excel' มาเติม"),
                    ft.ElevatedButton("🚀 โหลดรายการแรก", on_click=auto_fill_first_record,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.PINK_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("🗑️ เคลียร์ฟอร์ม", on_click=clear_form,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE)),
                    ft.ElevatedButton("📋 ดูรายการ", on_click=view_certificates,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True),
                
                status_text,
                ft.Divider(),
                
                # Form sections
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลผู้มีหน้าที่หักภาษี", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([withholder_name, withholder_type], spacing=10),
                                withholder_address,
                                withholder_tax_id
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("ข้อมูลผู้ถูกหักภาษี", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([withholdee_name, withholdee_type], spacing=10),
                                withholdee_address,
                                withholdee_tax_id
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("เอกสารอ้างอิง", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([certificate_book_no, certificate_no, sequence_in_form], spacing=10),
                                form_type
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("รายการเงินได้และภาษี", weight=ft.FontWeight.BOLD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([income_1_amount, income_1_tax], spacing=10),
                                ft.Row([salary_pos_1, salary_pos_2, salary_pos_3, salary_pos_4, salary_pos_5,
                                        salary_pos_6, salary_pos_7, salary_pos_8, salary_pos_9, salary_pos_10], spacing=6, wrap=True),
                                ft.Row([tax_pos_1, tax_pos_2, tax_pos_3, tax_pos_4, tax_pos_5, tax_pos_6, tax_pos_7, tax_pos_8], spacing=6, wrap=True),
                                ft.Row([fee_pos_1, fee_pos_2, fee_pos_3, fee_pos_4, fee_pos_5,
                                        fee_pos_6, fee_pos_7, fee_pos_8, fee_pos_9, fee_pos_10], spacing=6, wrap=True),
                                ft.Row([fee_tax_pos_1, fee_tax_pos_2, fee_tax_pos_3, fee_tax_pos_4,
                                        fee_tax_pos_5, fee_tax_pos_6, fee_tax_pos_7, fee_tax_pos_8], spacing=6, wrap=True),
                                ft.Row([dot_1, dot_2, dot_3, dot_4, dot_5, dot_6], spacing=6, wrap=True),
                                ft.Row([income_2_amount, income_2_tax], spacing=10),
                                ft.Divider(height=20, color=ft.Colors.BLUE_700),
                                ft.Row([total_income_display, total_tax_display], spacing=10),
                                ft.Row([
                                    total_income_pos_1, total_income_pos_2, total_income_pos_3, total_income_pos_4, total_income_pos_5,
                                    total_income_pos_6, total_income_pos_7, total_income_pos_8, total_income_pos_9, total_income_pos_10
                                ], spacing=6, wrap=True),
                                ft.Row([
                                    total_tax_pos_1, total_tax_pos_2, total_tax_pos_3, total_tax_pos_4,
                                    total_tax_pos_5, total_tax_pos_6, total_tax_pos_7, total_tax_pos_8
                                ], spacing=6, wrap=True),
                                total_tax_text
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                
                ft.ExpansionTile(
                    title=ft.Text("กองทุนและลายเซ็น", weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([provident_fund, social_security_fund, retirement_mutual_fund], spacing=10),
                                ft.Row([issue_type, issue_date, fee_payment_date], spacing=10),
                                ft.Row([signatory_name, company_seal], spacing=10)
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                # New section: เลขบัตรสิบตำแหน่ง
                ft.ExpansionTile(
                    title=ft.Text("เลขบัตรสิบสามตำแหน่ง (ผู้หัก/ผู้ถูกหัก) + สิบตำแหน่ง (กลุ่ม)", weight=ft.FontWeight.BOLD),
                    initially_expanded=False,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("กรอกเลขประจำตัวผู้เสียภาษี 13 หลัก แยกช่อง และกล่องกลุ่ม 10 ช่อง (ใส่ลง PDF ไม่บันทึกฐานข้อมูล)", size=12, color=ft.Colors.GREY_700),
                                ft.Text("ผู้หักภาษี (13 หลัก)", weight=ft.FontWeight.BOLD),
                                ft.Row([withholdee_id_1, withholdee_id_2, withholdee_id_3, withholdee_id_4, withholdee_id_5, withholdee_id_6, withholdee_id_7, withholdee_id_8, withholdee_id_9, withholdee_id_10, withholdee_id_11, withholdee_id_12, withholdee_id_13], spacing=4, wrap=True),
                                ft.Text("ผู้ถูกหักภาษี (13 หลัก)", weight=ft.FontWeight.BOLD),
                                ft.Row([withholder_id_1, withholder_id_2, withholder_id_3, withholder_id_4, withholder_id_5, withholder_id_6, withholder_id_7, withholder_id_8, withholder_id_9, withholder_id_10, withholder_id_11, withholder_id_12, withholder_id_13], spacing=4, wrap=True),
                                ft.Divider(),
                                ft.Text("กล่อง 10 ช่อง (ใช้สำหรับรูปแบบตัดแบ่ง)", weight=ft.FontWeight.BOLD),
                                ft.Row([card_number_1, card_number_2, card_number_3, card_number_4, card_number_5], spacing=10, wrap=True),
                                ft.Row([card_number_6, card_number_7, card_number_8, card_number_9, card_number_10], spacing=10, wrap=True),
                                ft.Row([
                                    ft.ElevatedButton(
                                        "เติมเลขที่บัตร",
                                        icon=ft.icons.NUMBERS,
                                        on_click=fill_card_numbers_from_tax_id,
                                        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
                                    )
                                    ,
                                    ft.ElevatedButton(
                                        "เติมเลขที่บัตร (ผู้มีหน้าที่หักภาษี)",
                                        icon=ft.icons.NUMBERS,
                                        on_click=fill_card_numbers_from_withholder_tax_id,
                                        style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE)
                                    )
                                ])
                            ], spacing=10),
                            padding=10,
                            bgcolor=ft.Colors.GREY_50,
                            border_radius=10
                        )
                    ]
                ),
                
                # Crystal Reports methodology explanation
                ft.ExpansionTile(
                    title=ft.Text("📊 Crystal Reports Methodology", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("🏗️ เทคนิค Crystal Reports ที่นำมาใช้:", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700, size=16),
                                ft.Divider(),
                                
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("📋 Report Sections (แบ่งส่วนรายงาน):", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                                        ft.Text("• Page Header: ส่วนหัวของหน้า (ว่าง)", size=12),
                                        ft.Text("• Report Header: ข้อมูลเอกสารอ้างอิง", size=12),
                                        ft.Text("• Detail Section: ข้อมูลหลักของฟอร์ม", size=12),
                                        ft.Text("• Report Footer: ลายเซ็นและวันที่", size=12),
                                        ft.Text("• Page Footer: หมายเหตุทางกฎหมาย", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.Colors.GREEN_50,
                                    padding=10,
                                    border_radius=5
                                ),
                                
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("🎯 Field Objects (วัตถุฟิลด์):", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                                        ft.Text("• Text Objects: ตำแหน่งและการจัดรูปแบบที่แม่นยำ", size=12),
                                        ft.Text("• Font Management: การจัดการฟอนต์ไทยและอังกฤษ", size=12),
                                        ft.Text("• Alignment: Left, Right, Center alignment", size=12),
                                        ft.Text("• Can Grow Fields: ข้อความหลายบรรทัด", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.Colors.BLUE_50,
                                    padding=10,
                                    border_radius=5
                                ),
                                
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("🧮 Formula Fields (ฟิลด์สูตร):", weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                                        ft.Text("• Calculated Totals: การคำนวณยอดรวมอัตโนมัติ", size=12),
                                        ft.Text("• Number Formatting: การจัดรูปแบบตัวเลข", size=12),
                                        ft.Text("• Conditional Logic: เงื่อนไขในการแสดงผล", size=12),
                                        ft.Text("• Data Validation: การตรวจสอบข้อมูล", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.Colors.PURPLE_50,
                                    padding=10,
                                    border_radius=5
                                ),
                                
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("🖼️ Background Integration:", weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700),
                                        ft.Text("• PDF to Image Conversion: แปลง PDF เป็นภาพคุณภาพสูง", size=12),
                                        ft.Text("• High DPI Rendering: เรนเดอร์ 300 DPI สำหรับการพิมพ์", size=12),
                                        ft.Text("• Overlay Technique: วางข้อมูลทับภาพพื้นหลัง", size=12),
                                        ft.Text("• Professional Output: ผลลัพธ์ระดับมืออาชีพ", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.Colors.ORANGE_50,
                                    padding=10,
                                    border_radius=5
                                ),
                                
                                ft.Divider(),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("⚙️ Technical Implementation:", weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_700),
                                        ft.Text("pip install reportlab PyMuPDF", 
                                               style=ft.TextStyle(bgcolor=ft.Colors.BLACK, color=ft.Colors.WHITE, size=12)),
                                        ft.Text("• ReportLab Canvas API สำหรับการวาด", size=12),
                                        ft.Text("• PyMuPDF สำหรับแปลง PDF เป็นภาพ", size=12),
                                        ft.Text("• Section-based Rendering Architecture", size=12),
                                        ft.Text("• Professional Typography Support", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.Colors.TEAL_50,
                                    padding=10,
                                    border_radius=5
                                ),
                            ], spacing=15),
                            padding=20
                        )
                    ]
                ),
                
                # Coordinate adjustment panel
                ft.ExpansionTile(
                    title=ft.Text("⚙️ ปรับตำแหน่งฟิลด์ PDF", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                    subtitle=ft.Text("กำหนดพิกัด X, Y และขนาดตัวอักษรสำหรับแต่ละฟิลด์", size=11, color=ft.Colors.GREY_600),
                    initially_expanded=False,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                ft.Row([
                                    ft.ElevatedButton("🔍 ทดสอบทุกฟิลด์", on_click=preview_all_coordinates,
                                                    style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE)),
                                    ft.ElevatedButton("📸 บันทึกเป็น PNG", on_click=save_coordinate_test_png,
                                                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)),
                                    ft.ElevatedButton("💾 บันทึกการตั้งค่า", on_click=save_coordinates_config,
                                                    style=ft.ButtonStyle(bgcolor=ft.Colors.TEAL_700, color=ft.Colors.WHITE)),
                                    ft.ElevatedButton("📂 โหลดการตั้งค่า", on_click=load_coordinates_config,
                                                    style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE)),
                                ], spacing=10),
                # Quick-select buttons row: ผู้จ่ายเงิน + เลขที่บัตร 1–5
                ft.Row([
                    ft.Text("เมนูเลือกฟิลด์อย่างรวดเร็ว:", weight=ft.FontWeight.BOLD),
                    ft.OutlinedButton("ผู้จ่ายเงิน", on_click=lambda e: (test_single_field("signatory_name"))),
                    ft.OutlinedButton("วันที่ชำระค่าธรรมเนียม", on_click=lambda e: (test_single_field("fee_payment_date"))),
                    ft.OutlinedButton("ผู้ถูกหัก 13 หลัก", on_click=lambda e: [
                        test_single_field("withholdee_id_1"), test_single_field("withholdee_id_2"), test_single_field("withholdee_id_3"),
                        test_single_field("withholdee_id_4"), test_single_field("withholdee_id_5"), test_single_field("withholdee_id_6"),
                        test_single_field("withholdee_id_7"), test_single_field("withholdee_id_8"), test_single_field("withholdee_id_9"),
                        test_single_field("withholdee_id_10"), test_single_field("withholdee_id_11"), test_single_field("withholdee_id_12"),
                        test_single_field("withholdee_id_13")
                    ]),
                    ft.OutlinedButton("ผู้หัก 13 หลัก", on_click=lambda e: [
                        test_single_field("withholder_id_1"), test_single_field("withholder_id_2"), test_single_field("withholder_id_3"),
                        test_single_field("withholder_id_4"), test_single_field("withholder_id_5"), test_single_field("withholder_id_6"),
                        test_single_field("withholder_id_7"), test_single_field("withholder_id_8"), test_single_field("withholder_id_9"),
                        test_single_field("withholder_id_10"), test_single_field("withholder_id_11"), test_single_field("withholder_id_12"),
                        test_single_field("withholder_id_13")
                    ]),
                    ft.OutlinedButton("เลขที่บัตร 1", on_click=lambda e: (test_single_field("card_number_1"))),
                    ft.OutlinedButton("เลขที่บัตร 2", on_click=lambda e: (test_single_field("card_number_2"))),
                    ft.OutlinedButton("เลขที่บัตร 3", on_click=lambda e: (test_single_field("card_number_3"))),
                    ft.OutlinedButton("เลขที่บัตร 4", on_click=lambda e: (test_single_field("card_number_4"))),
                    ft.OutlinedButton("เลขที่บัตร 5", on_click=lambda e: (test_single_field("card_number_5"))),
                    ft.OutlinedButton("เลขที่บัตร 6", on_click=lambda e: (test_single_field("card_number_6"))),
                    ft.OutlinedButton("เลขที่บัตร 7", on_click=lambda e: (test_single_field("card_number_7"))),
                    ft.OutlinedButton("เลขที่บัตร 8", on_click=lambda e: (test_single_field("card_number_8"))),
                    ft.OutlinedButton("เลขที่บัตร 9", on_click=lambda e: (test_single_field("card_number_9"))),
                    ft.OutlinedButton("เลขที่บัตร 10", on_click=lambda e: (test_single_field("card_number_10"))),
                ], spacing=8, wrap=True),
                                ft.Row([
                                    # Coordinate controls on the left
                                    ft.Container(
                                        content=ft.Column(
                                            create_coordinate_controls(),
                                            scroll=ft.ScrollMode.AUTO,
                                            height=400
                                        ),
                                        border=ft.border.all(1, ft.Colors.GREY_300),
                                        border_radius=5,
                                        padding=10,
                                        expand=True
                                    ),
                                    # Small PDF viewer on the right
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("ตัวอย่างพิกัด", size=12, weight=ft.FontWeight.BOLD, 
                                                   color=ft.Colors.BLUE_700, text_align=ft.TextAlign.CENTER),
                                            coordinate_test_viewer
                                        ], spacing=5),
                                        padding=10
                                    )
                                ], spacing=10)
                            ], spacing=10),
                            padding=20
                        )
                    ]
                )

              ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20
        )

        # Thread 2: Auto-fill withholdee data from temp file or database
        def delayed_withholdee_auto_fill():
            import time
            print("⏰ delayed_withholdee_auto_fill started - waiting 1.5 seconds...")
            time.sleep(1.5)  # Wait for UI to be ready
            
            try:
                print("🔄 Checking for withholdee data to auto-fill...")
                
                # First, try to get data from temp file (from dashboard button)
                temp_file_path = os.path.join(os.getcwd(), "temp_dashboard_data.json")
                withholdee_filled = False
                
                if os.path.exists(temp_file_path):
                    try:
                        with open(temp_file_path, 'r', encoding='utf-8') as f:
                            dashboard_data = json.load(f)
                        print(f"🔍 Found temp file data for withholdee: {dashboard_data}")
                        
                        # Look for transfer record data to fill withholdee fields
                        if dashboard_data.get('transfer_record'):
                            record = dashboard_data['transfer_record']
                            name = record.get('name', '')
                            surname = record.get('surname', '')
                            full_name = f"{name} {surname}".strip()
                            
                            if full_name:
                                withholdee_name.value = full_name
                                withholdee_address.value = record.get('address', '')
                                withholdee_tax_id.value = record.get('id_card', '')
                                
                                # Fill income data
                                transfer_amount = record.get('transfer_amount', 0)
                                fee = record.get('fee', 0)
                                income_1_amount.value = f"{float(transfer_amount or 0):.2f}"
                                income_1_tax.value = "0.00"
                                income_2_amount.value = "0.00"
                                income_2_tax.value = f"{float(fee or 0):.2f}"
                                
                                # Update totals
                                total_income_display.value = f"{float(transfer_amount or 0):,.2f}"
                                total_tax_display.value = f"{float(fee or 0):,.2f}"
                                
                                status_text.value = f"✅ โหลดข้อมูลผู้ถูกหักภาษีจาก Dashboard: {full_name}"
                                status_text.color = ft.Colors.GREEN_700
                                page.update()
                                withholdee_filled = True
                                print(f"✅ Auto-filled withholdee data from temp file: {full_name}")
                    except Exception as file_ex:
                        print(f"❌ Failed to load temp file for withholdee: {file_ex}")
                
                # If no temp data, try using selected_transfer_id_for_pdf
                if not withholdee_filled:
                    print("🔄 No temp file data, trying auto_fill_from_selected_dashboard...")
                    auto_fill_from_selected_dashboard()
                    print("✅ auto_fill_from_selected_dashboard completed")
                
            except Exception as ex:
                print(f"❌ delayed_withholdee_auto_fill error: {ex}")

        # Initialize coordinate settings and auto-fill from dashboard selection (if any)
        try:
            initialize_coordinate_settings_once()
            
            # AUTO-CLICK ปุ่ม "ดึงข้อมูลที่เลือก" ง่ายๆ
            import threading
            def auto_click_button():
                import time
                time.sleep(0.8)  # รอให้ UI พร้อม
                print("🔄 Auto-clicking 'ดึงข้อมูลที่เลือก' button...")
                try:
                    _f = globals().get('auto_fill_from_selected_dashboard')
                    if callable(_f):
                        _f()  # เรียกฟังก์ชันเดียวกับปุ่ม
                    print("✅ Auto-click completed!")
                except Exception as e:
                    print(f"❌ Auto-click error: {e}")
            
            # เริ่ม auto-click
            threading.Thread(target=auto_click_button, daemon=True).start()
            print("✅ Auto-click thread started")
            
        except Exception as _init_err:
            print(f"Coordinate init hook error: {_init_err}")

        # AUTO-CLICK: กดปุ่ม "ดึงข้อมูลที่เลือก" อัตโนมัติทุกครั้งที่เปิด tab
        def force_auto_fill_every_time():
            import time
            time.sleep(0.3)  # รอให้ UI พร้อม (เร็วขึ้น)
            try:
                print("🚀 FORCE AUTO-FILL: กดปุ่ม 'ดึงข้อมูลที่เลือก' อัตโนมัติ...")
                _f = globals().get('auto_fill_from_selected_dashboard')
                if callable(_f):
                    _f()  # กดปุ่มให้อัตโนมัติ
                print("✅ Auto-fill completed - user ไม่ต้องกดปุ่มเอง!")
            except Exception as e:
                print(f"❌ Auto-fill error: {e}")
                # ถ้าไม่สำเร็จ ลองอีกครั้ง
                try:
                    time.sleep(0.3)
                    print("🔄 Retrying auto-fill...")
                    _f = globals().get('auto_fill_from_selected_dashboard')
                    if callable(_f):
                        _f()
                    print("✅ Retry successful!")
                except Exception as retry_e:
                    print(f"❌ Retry failed: {retry_e}")
        
        # เริ่ม auto-fill ทันทีทุกครั้งที่เปิด tab
        import threading
        threading.Thread(target=force_auto_fill_every_time, daemon=True).start()
        print("🚀 FORCE AUTO-FILL STARTED - ปุ่มจะถูกกดอัตโนมัติทุกครั้ง!")
        
        # เพิ่มการกดปุ่มอีกครั้งหลังจาก UI พร้อมสมบูรณ์
        def delayed_force_click():
            import time
            time.sleep(1.0)  # รอให้ UI พร้อมสมบูรณ์
            try:
                print("🔄 DELAYED FORCE CLICK: กดปุ่ม 'ดึงข้อมูลที่เลือก' อีกครั้ง...")
                _f = globals().get('auto_fill_from_selected_dashboard')
                if callable(_f):
                    _f()
                print("✅ Delayed force click completed!")
            except Exception as e:
                print(f"❌ Delayed force click error: {e}")
        
        # เริ่ม delayed force click
        threading.Thread(target=delayed_force_click, daemon=True).start()
        print("🚀 DELAYED FORCE CLICK STARTED!")

        # Ensure 13-digit boxes are auto-populated without button after UI is ready
        def delayed_fill_cards():
            try:
                import time
                time.sleep(0.6)
                try:
                    fill_card_numbers_from_withholder_tax_id(None)
                except Exception:
                    pass
                try:
                    fill_card_numbers_from_tax_id(None)
                except Exception:
                    pass
                try:
                    page.update()
                except Exception:
                    pass
            except Exception:
                pass
        try:
            threading.Thread(target=delayed_fill_cards, daemon=True).start()
        except Exception:
            pass
        
        return crystal_tab
    
    # Create navigation rail (add Import/Backup)
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD,
                label="แดชบอร์ด",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ANALYTICS_OUTLINED,
                selected_icon=ft.Icons.ANALYTICS,
                label="ระบบพิกัด form PDF",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="ระบบตั้งค่าหัวกระดาษ",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.EDIT_OUTLINED,
                selected_icon=ft.Icons.EDIT,
                label="จัดการข้อมูล",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.TABLE_CHART_OUTLINED,
                selected_icon=ft.Icons.TABLE_CHART,
                label="ข้อมูลทั้งหมด",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.DESCRIPTION_OUTLINED,
                selected_icon=ft.Icons.DESCRIPTION,
                label="ฟอร์มภาษี",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PICTURE_AS_PDF_OUTLINED,
                selected_icon=ft.Icons.PICTURE_AS_PDF,
                label="พิมพ์ใบกำกับถาษี",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.GAVEL_OUTLINED,
                selected_icon=ft.Icons.GAVEL,
                label="ใช้ฟอร์มราชการ",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.FILE_UPLOAD,
                selected_icon=ft.Icons.FILE_UPLOAD,
                label="นำเข้าจาก Excel",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.BACKUP,
                selected_icon=ft.Icons.BACKUP,
                label="สำรองข้อมูล",
            ),
        ],
        on_change=lambda e: handle_nav_change(e.control.selected_index)
    )
    
    # Content area
    content_area = ft.Container(
        content=create_dashboard_tab(),
        expand=True
    )
    
    def handle_nav_change(selected_index):
        print(f"🔄 handle_nav_change called with selected_index: {selected_index}")
        try:
            if selected_index == 0:
                print("📱 Switching to Dashboard tab")
                content_area.content = create_dashboard_tab()
            elif selected_index == 1:
                print("📱 Switching to Crystal Report tab (ระบบพิกัด form PDF)")
                content_area.content = create_crystal_report_tab()
                
                # FORCE AUTO-FILL ทันทีที่เปลี่ยน tab
                def force_auto_fill_on_tab_switch():
                    import time
                    time.sleep(0.8)  # รอให้ UI พร้อม
                    try:
                        print("🚀 TAB SWITCH AUTO-FILL: กดปุ่ม 'ดึงข้อมูลที่เลือก' อัตโนมัติ...")
                        # เรียกฟังก์ชันเดียวกับปุ่ม "ดึงข้อมูลที่เลือก"
                        _f = globals().get('auto_fill_from_selected_dashboard')
                        if callable(_f):
                            _f()
                            print("✅ Tab switch auto-fill completed!")
                        else:
                            print("⚠️ auto_fill_from_selected_dashboard not found in globals")
                    except Exception as e:
                        print(f"❌ Tab switch auto-fill error: {e}")
                
                # เริ่ม auto-fill ทันทีที่เปลี่ยน tab
                import threading
                threading.Thread(target=force_auto_fill_on_tab_switch, daemon=True).start()
                print("🚀 TAB SWITCH AUTO-FILL STARTED!")
            elif selected_index == 2:
                print("📱 Switching to Import Withholder Excel tab")
                content_area.content = create_import_withholder_excel_tab()
            elif selected_index == 3:
                print("📱 Switching to Data Management tab")
                content_area.content = create_data_management_tab()
            elif selected_index == 4:
                print("📱 Switching to All Data tab")
                content_area.content = create_all_data_tab()
            elif selected_index == 5:
                print("📱 Switching to Tax Form tab")
                content_area.content = create_tax_form_tab()
            elif selected_index == 6:
                print("📱 Switching to Tax Certificate tab")
                content_area.content = create_tax_certificate_tab()
            elif selected_index == 7:
                print("📱 Switching to Official Tax Form tab")
                content_area.content = create_official_tax_form_tab()
            elif selected_index == 8:
                print("📱 Switching to Import Excel tab")
                content_area.content = create_import_excel_tab()
            elif selected_index == 9:
                print("📱 Switching to Backup tab")
                content_area.content = create_backup_tab()
            print(f"✅ Tab switch completed, updating page...")
            page.update()
        except Exception as ex:
            print(f"❌ Error in handle_nav_change: {ex}")
            import traceback
            traceback.print_exc()
    
    # Main layout with navigation rail and scrollbar
    page.add(
        ft.Row([
            nav_rail,
            ft.VerticalDivider(width=1),
            content_area
        ], expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)