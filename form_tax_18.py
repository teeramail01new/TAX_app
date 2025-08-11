import flet as ft
import psycopg2
import pandas as pd
from datetime import datetime
import os
from decimal import Decimal
import json
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, transparent
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from PIL import Image as PILImage
import io
import tempfile
import sqlite3
from typing import Tuple, Dict, List
try:
    # Optional import for in-app backup trigger
    from create_dqlite_database import backup_neon_to_sqlite  # type: ignore
except Exception:
    backup_neon_to_sqlite = None

class CrystalReportStyleRenderer:
    def __init__(self):
        self.connection_string = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
        self.template_pdf_path = "tax_form_template.pdf"
        self.template_image_path = "tax_form_background.jpg"
        self.output_dpi = 300  # High DPI for professional output
        self.init_database()
        self.setup_fonts()
        self.setup_report_engine()
        # Load custom coordinates for dynamic fields (e.g. เลขที่บัตร 1-5)
        self.coordinates_config = self.load_custom_coordinates()
        
    def setup_fonts(self):
        """Setup fonts similar to Crystal Reports"""
        try:
            # Register Thai font if available
            if os.path.exists('THSarabunNew.ttf'):
                pdfmetrics.registerFont(TTFont('THSarabunNew', 'THSarabunNew.ttf'))
                pdfmetrics.registerFont(TTFont('THSarabunNew-Bold', 'THSarabunNew.ttf'))  # Simulate bold
                self.thai_font = 'THSarabunNew'
                self.thai_font_bold = 'THSarabunNew-Bold'
            else:
                self.thai_font = 'Helvetica'
                self.thai_font_bold = 'Helvetica-Bold'
                
            # Additional fonts for different sections
            self.fonts = {
                'header': self.thai_font_bold,
                'data': self.thai_font,
                'small': self.thai_font,
                'bold': self.thai_font_bold
            }
        except Exception as e:
            print(f"Font setup error: {e}")
            self.thai_font = 'Helvetica'
            self.thai_font_bold = 'Helvetica-Bold'
    
    def setup_report_engine(self):
        """Initialize Crystal Reports-style report engine"""
        self.report_sections = {
            'page_header': {
                'height': 80,
                'elements': []
            },
            'report_header': {
                'height': 120,
                'elements': []
            },
            'detail_section': {
                'height': 400,
                'elements': []
            },
            'report_footer': {
                'height': 100,
                'elements': []
            },
            'page_footer': {
                'height': 50,
                'elements': []
            }
        }
        
    def load_custom_coordinates(self) -> dict:
        """Load coordinate configuration for dynamic text fields from pdf_coordinates.json.
        Falls back to sane defaults if file or keys are missing.
        Structure in file:
        {
          "crystal": {
            "card_numbers": {
              "card_number_1": {"x": 120, "y": 530, "size": 11, "width": 150, "align": "left"},
              ...
            }
          }
        }
        """
        default_cards = {
            f"card_number_{i}": {"x": 120 + (i - 1) * 80, "y": 530, "size": 11, "width": 70, "height": 20, "align": "left"}
            for i in range(1, 6)
        }
        cfg = {"crystal": {"card_numbers": default_cards}}
        try:
            if os.path.exists("pdf_coordinates.json"):
                with open("pdf_coordinates.json", "r", encoding="utf-8") as f:
                    file_cfg = json.load(f)
                # Merge (preserve defaults for missing keys)
                crystal = file_cfg.get("crystal", {})
                cards = crystal.get("card_numbers", {})
                for k, v in default_cards.items():
                    if k not in cards or not isinstance(cards[k], dict):
                        cards[k] = v
                    else:
                        for kk, vv in v.items():
                            cards[k].setdefault(kk, vv)
                cfg["crystal"]["card_numbers"] = cards
                return cfg
        except Exception as e:
            print(f"Coordinate config load error: {e}")
        return cfg

    def save_custom_coordinates(self, new_cards: dict) -> bool:
        """Persist updated coordinates for card number fields into pdf_coordinates.json."""
        try:
            # Load existing
            file_cfg = {}
            if os.path.exists("pdf_coordinates.json"):
                try:
                    with open("pdf_coordinates.json", "r", encoding="utf-8") as f:
                        file_cfg = json.load(f)
                except Exception:
                    file_cfg = {}
            if "crystal" not in file_cfg:
                file_cfg["crystal"] = {}
            file_cfg["crystal"]["card_numbers"] = new_cards
            with open("pdf_coordinates.json", "w", encoding="utf-8") as f:
                json.dump(file_cfg, f, ensure_ascii=False, indent=2)
            # Update in-memory
            self.coordinates_config = {"crystal": {"card_numbers": new_cards}}
            return True
        except Exception as e:
            print(f"Coordinate config save error: {e}")
            return False

    def get_card_fields_config(self) -> dict:
        """Return field configurations for card_number_1..5 using current coordinate config."""
        cards_cfg = self.coordinates_config.get("crystal", {}).get("card_numbers", {})
        result = {}
        for key, v in cards_cfg.items():
            result[key] = {
                "x": float(v.get("x", 120)),
                "y": float(v.get("y", 530)),
                "font": self.fonts.get("data", self.thai_font),
                "size": int(v.get("size", 11)),
                "width": float(v.get("width", 70)),
                "height": float(v.get("height", 20)),
                "align": v.get("align", "left")
            }
        return result

    def convert_pdf_to_background_image(self):
        """Convert PDF template to background image for Crystal Reports style rendering"""
        try:
            if not os.path.exists(self.template_pdf_path):
                return False
            # Lazy import to avoid hard dependency during runtime
            local_fitz = None
            try:
                import fitz as local_fitz  # type: ignore
            except Exception:
                print("PyMuPDF (fitz) not installed; skipping background conversion")
                return False

            print("Converting PDF to background image...")
            pdf_document = local_fitz.open(self.template_pdf_path)
            page = pdf_document[0]

            mat = local_fitz.Matrix(self.output_dpi / 72, self.output_dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            img_data = pix.tobytes("ppm")
            background_image = PILImage.open(io.BytesIO(img_data))
            if background_image.mode != 'RGB':
                background_image = background_image.convert('RGB')

            background_image.save(self.template_image_path, "JPEG", quality=98, optimize=True)
            pdf_document.close()
            print(f"Background created: {self.template_image_path}")
            return True
        except Exception as e:
            print(f"PDF conversion error: {e}")
            return False
    
    def create_crystal_report_pdf(self, data, output_path):
        """Create PDF using Crystal Reports methodology with background image"""
        try:
            # Convert template PDF to background if needed
            if not os.path.exists(self.template_image_path):
                self.convert_pdf_to_background_image()
            
            # Create PDF canvas
            c = canvas.Canvas(output_path, pagesize=A4)
            width, height = A4
            
            # Draw background image if available (Crystal Reports style)
            if os.path.exists(self.template_image_path):
                c.drawImage(self.template_image_path, 0, 0, width, height, 
                           preserveAspectRatio=True, mask='auto')
                print("Background image applied")
            
            # Crystal Reports style sections
            self.render_page_header(c, width, height, data)
            self.render_report_header(c, width, height, data)
            self.render_detail_section(c, width, height, data)
            self.render_report_footer(c, width, height, data)
            self.render_page_footer(c, width, height, data)
            
            c.save()
            return True, f"Crystal Reports style PDF created: {output_path}"
            
        except Exception as e:
            return False, f"Report generation error: {str(e)}"
    
    def render_page_header(self, canvas, width, height, data):
        """Render page header section (Crystal Reports style)"""
        # Page header is usually empty in this form, but could contain page numbers
        pass
    
    def render_report_header(self, canvas, width, height, data):
        """Render report header section with title and document info"""
        # Document reference information (similar to Crystal Reports subreports)
        canvas.setFont(self.fonts['data'], 12)
        
        # Book and certificate numbers
        if data.get('certificate_book_no'):
            canvas.drawString(120, height - 150, data.get('certificate_book_no', ''))
        if data.get('certificate_no'):
            canvas.drawString(220, height - 150, data.get('certificate_no', ''))
    
    def render_detail_section(self, canvas, width, height, data):
        """Render main detail section with form data (Crystal Reports style)"""
        # This is the main data section - equivalent to Crystal Reports Detail band
        
        # Define text fields with Crystal Reports style positioning
        fields_config = self.get_field_configurations()
        
        for field_name, config in fields_config.items():
            value = data.get(field_name, '')
            if value:
                self.render_text_field(canvas, config, str(value))
        
        # Render checkboxes
        self.render_checkboxes(canvas, data)
        
        # Render calculated fields (like Crystal Reports formulas)
        self.render_calculated_fields(canvas, data)
    
    def get_field_configurations(self):
        """Get field configurations similar to Crystal Reports field objects"""
        base_cfg = {
            'withholder_name': {
                'x': 150, 'y': 650, 'font': self.fonts['bold'], 'size': 12,
                'width': 300, 'height': 20, 'align': 'left'
            },
            'withholder_address': {
                'x': 150, 'y': 620, 'font': self.fonts['data'], 'size': 10,
                'width': 400, 'height': 40, 'align': 'left', 'multiline': True
            },
            'withholder_tax_id': {
                'x': 200, 'y': 580, 'font': self.fonts['data'], 'size': 11,
                'width': 150, 'height': 20, 'align': 'left'
            },
            'withholder_type': {
                'x': 450, 'y': 650, 'font': self.fonts['small'], 'size': 9,
                'width': 100, 'height': 20, 'align': 'left'
            },
            'withholdee_name': {
                'x': 150, 'y': 480, 'font': self.fonts['bold'], 'size': 12,
                'width': 300, 'height': 20, 'align': 'left'
            },
            'withholdee_address': {
                'x': 150, 'y': 450, 'font': self.fonts['data'], 'size': 10,
                'width': 400, 'height': 40, 'align': 'left', 'multiline': True
            },
            'withholdee_tax_id': {
                'x': 200, 'y': 410, 'font': self.fonts['data'], 'size': 11,
                'width': 150, 'height': 20, 'align': 'left'
            },
            'withholdee_type': {
                'x': 450, 'y': 480, 'font': self.fonts['small'], 'size': 9,
                'width': 100, 'height': 20, 'align': 'left'
            },
            'sequence_in_form': {
                'x': 180, 'y': 350, 'font': self.fonts['data'], 'size': 11,
                'width': 50, 'height': 20, 'align': 'center'
            },
            # Income table fields
            'income_type_1_amount': {
                'x': 350, 'y': 280, 'font': self.fonts['data'], 'size': 11,
                'width': 100, 'height': 20, 'align': 'right'
            },
            'income_type_1_tax': {
                'x': 460, 'y': 280, 'font': self.fonts['data'], 'size': 11,
                'width': 80, 'height': 20, 'align': 'right'
            },
            'income_type_2_amount': {
                'x': 350, 'y': 260, 'font': self.fonts['data'], 'size': 11,
                'width': 100, 'height': 20, 'align': 'right'
            },
            'income_type_2_tax': {
                'x': 460, 'y': 260, 'font': self.fonts['data'], 'size': 11,
                'width': 80, 'height': 20, 'align': 'right'
            },
            'income_type_3_amount': {
                'x': 350, 'y': 240, 'font': self.fonts['data'], 'size': 11,
                'width': 100, 'height': 20, 'align': 'right'
            },
            'income_type_3_tax': {
                'x': 460, 'y': 240, 'font': self.fonts['data'], 'size': 11,
                'width': 80, 'height': 20, 'align': 'right'
            },
            'income_type_4a_amount': {
                'x': 350, 'y': 220, 'font': self.fonts['data'], 'size': 11,
                'width': 100, 'height': 20, 'align': 'right'
            },
            'income_type_4a_tax': {
                'x': 460, 'y': 220, 'font': self.fonts['data'], 'size': 11,
                'width': 80, 'height': 20, 'align': 'right'
            },
            'income_type_4b_amount': {
                'x': 350, 'y': 200, 'font': self.fonts['data'], 'size': 11,
                'width': 100, 'height': 20, 'align': 'right'
            },
            'income_type_4b_tax': {
                'x': 460, 'y': 200, 'font': self.fonts['data'], 'size': 11,
                'width': 80, 'height': 20, 'align': 'right'
            },
            'income_type_5_amount': {
                'x': 350, 'y': 160, 'font': self.fonts['data'], 'size': 11,
                'width': 100, 'height': 20, 'align': 'right'
            },
            'income_type_5_tax': {
                'x': 460, 'y': 160, 'font': self.fonts['data'], 'size': 11,
                'width': 80, 'height': 20, 'align': 'right'
            },
            'income_type_6_amount': {
                'x': 350, 'y': 140, 'font': self.fonts['data'], 'size': 11,
                'width': 100, 'height': 20, 'align': 'right'
            },
            'income_type_6_tax': {
                'x': 460, 'y': 140, 'font': self.fonts['data'], 'size': 11,
                'width': 80, 'height': 20, 'align': 'right'
            },
            'income_type_6_description': {
                'x': 150, 'y': 120, 'font': self.fonts['small'], 'size': 9,
                'width': 200, 'height': 20, 'align': 'left'
            },
        }
        # Merge in dynamic card number fields
        base_cfg.update(self.get_card_fields_config())
        return base_cfg
    
    def render_text_field(self, canvas, config, value):
        """Render text field similar to Crystal Reports text objects"""
        canvas.setFont(config['font'], config['size'])
        
        x, y = config['x'], config['y']
        
        # Handle alignment (Crystal Reports style)
        if config['align'] == 'right':
            text_width = canvas.stringWidth(value, config['font'], config['size'])
            x = x + config['width'] - text_width
        elif config['align'] == 'center':
            text_width = canvas.stringWidth(value, config['font'], config['size'])
            x = x + (config['width'] - text_width) / 2
        
        # Handle multiline text
        if config.get('multiline', False):
            self.render_multiline_text(canvas, value, x, y, config)
        else:
            canvas.drawString(x, y, value)
    
    def render_multiline_text(self, canvas, text, x, y, config):
        """Render multiline text similar to Crystal Reports can grow fields"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            text_width = canvas.stringWidth(test_line, config['font'], config['size'])
            
            if text_width <= config['width']:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        line_height = config['size'] + 2
        for i, line in enumerate(lines):
            canvas.drawString(x, y - (i * line_height), line)
    
    def render_checkboxes(self, canvas, data):
        """Render checkboxes similar to Crystal Reports checkbox objects"""
        checkbox_size = 8
        
        # Form type checkboxes
        form_checkboxes = {
            'ภ.ง.ด.1ก': (170, 350),
            'ภ.ง.ด.1ก พิเศษ': (220, 350),
            'ภ.ง.ด.2': (280, 350),
            'ภ.ง.ด.3': (320, 350),
            'ภ.ง.ด.2ก': (170, 330),
            'ภ.ง.ด.3ก': (220, 330),
            'ภ.ง.ด.53': (280, 330)
        }
        
        selected_form = data.get('form_type', '')
        for form_type, (x, y) in form_checkboxes.items():
            # Draw checkbox
            canvas.rect(x, y, checkbox_size, checkbox_size, stroke=1, fill=0)
            
            # Draw check mark if selected
            if form_type == selected_form:
                canvas.line(x + 1, y + 1, x + checkbox_size - 1, y + checkbox_size - 1)
                canvas.line(x + checkbox_size - 1, y + 1, x + 1, y + checkbox_size - 1)
        
        # Issue type checkboxes
        issue_checkboxes = {
            'หักณที่จ่าย': (200, 80),
            'ออกให้ตลอดไป': (280, 80),
            'ออกให้ครั้งเดียว': (380, 80),
            'อื่น ๆ': (480, 80)
        }
        
        selected_issue = data.get('issue_type', '')
        for issue_type, (x, y) in issue_checkboxes.items():
            canvas.rect(x, y, checkbox_size, checkbox_size, stroke=1, fill=0)
            if issue_type == selected_issue:
                canvas.line(x + 1, y + 1, x + checkbox_size - 1, y + checkbox_size - 1)
                canvas.line(x + checkbox_size - 1, y + 1, x + 1, y + checkbox_size - 1)
    
    def render_calculated_fields(self, canvas, data):
        """Render calculated fields similar to Crystal Reports formula fields"""
        # Total fields (calculated)
        total_income = float(data.get('total_income', 0))
        total_tax = float(data.get('total_tax_withheld', 0))
        
        if total_income > 0:
            canvas.setFont(self.fonts['bold'], 12)
            canvas.drawRightString(450, 100, f"{total_income:,.2f}")
        
        if total_tax > 0:
            canvas.setFont(self.fonts['bold'], 12)
            canvas.drawRightString(540, 100, f"{total_tax:,.2f}")
        
        # Fund amounts
        funds = [
            ('provident_fund', 150, 60),
            ('social_security_fund', 300, 60),
            ('retirement_mutual_fund', 450, 60)
        ]
        
        canvas.setFont(self.fonts['data'], 10)
        for fund_key, x, y in funds:
            amount = float(data.get(fund_key, 0))
            if amount > 0:
                canvas.drawString(x, y, f"{amount:,.2f}")
    
    def render_report_footer(self, canvas, width, height, data):
        """Render report footer section"""
        # Signature section
        canvas.setFont(self.fonts['data'], 11)
        
        if data.get('signatory_name'):
            canvas.drawString(150, 120, data.get('signatory_name', ''))
        
        if data.get('issue_date'):
            canvas.drawString(350, 120, data.get('issue_date', ''))
        
        # Company seal indication
        if data.get('company_seal'):
            canvas.rect(400, 90, 80, 40, stroke=1, fill=0)
            canvas.setFont(self.fonts['small'], 8)
            canvas.drawCentredText(440, 110, "ประทับตรา")
    
    def render_page_footer(self, canvas, width, height, data):
        """Render page footer section"""
        # Legal notice at bottom
        canvas.setFont(self.fonts['small'], 8)
        legal_text = "หมายเหตุ เลขประจำตัวผู้เสียภาษีอากร (13 หลัก)"
        canvas.drawString(50, 30, legal_text)
    
    # Database methods (same as previous versions)
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

    # --- Import/CRUD helpers for Excel and grid operations ---
    def _get_table_columns(self, table_name: str):
        conn = self.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
                """,
                (table_name,),
            )
            cols = [r[0] for r in cursor.fetchall()]
            return cols
        except Exception:
            return []
        finally:
            cursor.close(); conn.close()

    def import_excel_to_db(self, excel_path: str) -> Tuple[bool, str, int]:
        """Import records from Excel into tax_withholding_certificates.
        Accepts file exported by the app (sheet 'Tax Certificates') or first sheet.
        Returns (ok, message, inserted_count).
        """
        try:
            try:
                df = pd.read_excel(excel_path, sheet_name='Tax Certificates')
            except Exception:
                df = pd.read_excel(excel_path)

            columns_db = self._get_table_columns('tax_withholding_certificates')
            if not columns_db:
                return False, 'ไม่พบคอลัมน์ของตารางในฐานข้อมูล', 0

            # Align DataFrame columns to DB columns; ignore extra columns
            common_cols = [c for c in df.columns if c in columns_db]
            if not common_cols:
                return False, 'โครงสร้างไฟล์ไม่ตรงกับฐานข้อมูล', 0
            df2 = df[common_cols].copy()

            # Convert booleans and NaNs
            df2 = df2.where(pd.notnull(df2), None)
            if 'company_seal' in df2.columns:
                df2['company_seal'] = df2['company_seal'].map(lambda v: bool(v) if v is not None else False)

            # Insert
            from psycopg2.extras import execute_values
            conn = self.get_connection()
            if not conn:
                return False, 'ไม่สามารถเชื่อมต่อฐานข้อมูล', 0
            try:
                cursor = conn.cursor()
                cols_csv = ','.join(common_cols)
                template = '(' + ','.join(['%s'] * len(common_cols)) + ')'
                values = [tuple(row[c] for c in common_cols) for _, row in df2.iterrows()]
                # Use execute_values for speed
                insert_sql = f'INSERT INTO tax_withholding_certificates ({cols_csv}) VALUES %s'
                execute_values(cursor, insert_sql, values, template=template)
                conn.commit()
                return True, f'นำเข้าข้อมูล {len(values)} รายการ', len(values)
            except Exception as e:
                conn.rollback()
                return False, f'เกิดข้อผิดพลาดในการนำเข้า: {e}', 0
            finally:
                cursor.close(); conn.close()
        except Exception as ex:
            return False, f'อ่านไฟล์ Excel ไม่สำเร็จ: {ex}', 0

    def delete_certificates(self, ids: List[int]) -> Tuple[bool, str, int]:
        if not ids:
            return True, 'ไม่มีรายการที่เลือก', 0
        conn = self.get_connection()
        if not conn:
            return False, 'เชื่อมต่อฐานข้อมูลไม่สำเร็จ', 0
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tax_withholding_certificates WHERE id = ANY(%s)', (ids,))
            affected = cursor.rowcount
            conn.commit()
            return True, f'ลบ {affected} รายการ', affected
        except Exception as e:
            conn.rollback()
            return False, f'ลบไม่สำเร็จ: {e}', 0
        finally:
            cursor.close(); conn.close()

    def update_certificate_basic(self, record_id: int, fields: dict) -> Tuple[bool, str]:
        if not fields:
            return True, 'ไม่มีการแก้ไข'
        allowed = {'withholder_name','withholdee_name','total_income','total_tax_withheld','issue_date'}
        items = [(k, v) for k, v in fields.items() if k in allowed]
        if not items:
            return False, 'ฟิลด์ที่แก้ไขไม่ได้รับอนุญาต'
        conn = self.get_connection()
        if not conn:
            return False, 'เชื่อมต่อฐานข้อมูลไม่สำเร็จ'
        try:
            cursor = conn.cursor()
            set_sql = ', '.join([f"{k}=%s" for k, _ in items])
            params = [v for _, v in items] + [record_id]
            cursor.execute(f'UPDATE tax_withholding_certificates SET {set_sql} WHERE id=%s', params)
            conn.commit()
            return True, 'บันทึกการแก้ไขเรียบร้อย'
        except Exception as e:
            conn.rollback()
            return False, f'แก้ไขไม่สำเร็จ: {e}'
        finally:
            cursor.close(); conn.close()

def main(page: ft.Page):
    page.title = "Crystal Reports Style PDF Generator - Thai Tax Forms"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    page.window_resizable = True
    page.scroll = ft.ScrollMode.AUTO
    
    app = CrystalReportStyleRenderer()
    
    # Status messages
    status_text = ft.Text("พร้อมใช้งาน", size=14, color=ft.colors.GREEN_700)
    
    # Template status
    template_status = ft.Text("กำลังตรวจสอบเทมเพลต...", size=12)
    
    def check_template():
        if os.path.exists(app.template_image_path):
            template_status.value = f"✅ พบภาพพื้นหลัง: {app.template_image_path}"
            template_status.color = ft.colors.GREEN_700
        elif os.path.exists(app.template_pdf_path):
            template_status.value = f"🔄 พบ PDF เทมเพลต: {app.template_pdf_path}"
            template_status.color = ft.colors.BLUE_700
        else:
            template_status.value = f"⚠️ ไม่พบเทมเพลต (จะใช้โหมดโปร่งใส)"
            template_status.color = ft.colors.ORANGE_700
        page.update()
    
    check_template()
    
    # Form fields (simplified for space)
    withholder_name = ft.TextField(label="ชื่อผู้มีหน้าที่หักภาษี", width=400)
    withholder_address = ft.TextField(label="ที่อยู่ผู้มีหน้าที่หักภาษี", width=600, multiline=True, max_lines=3)
    withholder_tax_id = ft.TextField(label="เลขประจำตัวผู้เสียภาษี", width=200, max_length=13)
    withholder_type = ft.Dropdown(
        label="ประเภท", width=200,
        options=[ft.dropdown.Option("บุคคล"), ft.dropdown.Option("นิติบุคคล"), 
                ft.dropdown.Option("บริษัท"), ft.dropdown.Option("สมาคม")]
    )
    
    # Additional form fields...
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
    income_1_amount = ft.TextField(label="เงินเดือน", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
    income_1_tax = ft.TextField(label="ภาษี", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
    income_2_amount = ft.TextField(label="ค่าธรรมเนียม", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0")
    income_2_tax = ft.TextField(label="ภาษี", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
    
    # Fund fields
    provident_fund = ft.TextField(label="กบข.", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
    social_security_fund = ft.TextField(label="ประกันสังคม", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
    retirement_mutual_fund = ft.TextField(label="กองทุนเลี้ยงชีพ", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
    
    # Issue fields
    issue_type = ft.Dropdown(
        label="ประเภทการออกใบรับรอง", width=200,
        options=[ft.dropdown.Option("หักณที่จ่าย"), ft.dropdown.Option("ออกให้ตลอดไป")]
    )
    issue_date = ft.TextField(label="วันที่", width=200)
    signatory_name = ft.TextField(label="ชื่อผู้จ่ายเงิน", width=300)
    company_seal = ft.Checkbox(label="ประทับตรา", value=False)

    # Crystal Report extra fields: เลขที่บัตร 1-5 (not stored in DB; injected at render time)
    card_number_1 = ft.TextField(label="เลขที่บัตร 1", width=180)
    card_number_2 = ft.TextField(label="เลขที่บัตร 2", width=180)
    card_number_3 = ft.TextField(label="เลขที่บัตร 3", width=180)
    card_number_4 = ft.TextField(label="เลขที่บัตร 4", width=180)
    card_number_5 = ft.TextField(label="เลขที่บัตร 5", width=180)

    # Coordinate editor for the five card fields
    coord_inputs = {}
    def load_card_coord_fields_from_config():
        cards_cfg = app.coordinates_config.get("crystal", {}).get("card_numbers", {})
        for i in range(1, 6):
            key = f"card_number_{i}"
            cfg = cards_cfg.get(key, {})
            coord_inputs[key] = {
                "x": ft.TextField(label=f"X {i}", width=100, value=str(cfg.get("x", 120)), keyboard_type=ft.KeyboardType.NUMBER),
                "y": ft.TextField(label=f"Y {i}", width=100, value=str(cfg.get("y", 530)), keyboard_type=ft.KeyboardType.NUMBER),
                "size": ft.TextField(label=f"ขนาด {i}", width=100, value=str(cfg.get("size", 11)), keyboard_type=ft.KeyboardType.NUMBER),
                "width": ft.TextField(label=f"ความกว้าง {i}", width=120, value=str(cfg.get("width", 70)), keyboard_type=ft.KeyboardType.NUMBER),
                "align": ft.Dropdown(label=f"จัดวาง {i}", width=130, value=str(cfg.get("align", "left")), options=[
                    ft.dropdown.Option("left"), ft.dropdown.Option("center"), ft.dropdown.Option("right")
                ])
            }
    load_card_coord_fields_from_config()

    def save_card_coords(e):
        # Gather and persist
        new_cards = {}
        try:
            for i in range(1, 6):
                key = f"card_number_{i}"
                fields = coord_inputs[key]
                new_cards[key] = {
                    "x": float(fields["x"].value or 0),
                    "y": float(fields["y"].value or 0),
                    "size": int(float(fields["size"].value or 11)),
                    "width": float(fields["width"].value or 70),
                    "height": 20,
                    "align": fields["align"].value or "left",
                }
            ok = app.save_custom_coordinates(new_cards)
            status_text.value = ("✅ " if ok else "❌ ") + ("บันทึกพิกัดเลขที่บัตรแล้ว" if ok else "บันทึกพิกัดไม่สำเร็จ")
            status_text.color = ft.colors.GREEN_700 if ok else ft.colors.RED_700
            page.update()
        except Exception as ex:
            status_text.value = f"❌ เกิดข้อผิดพลาดในการบันทึกพิกัด: {ex}"
            status_text.color = ft.colors.RED_700
            page.update()

    # Menu: ปรับตำแหน่งฟิลด์ pdf – add 5 buttons after "ผู้จ่ายเงิน"
    selected_coord_field_label = ft.Text("ฟิลด์ที่เลือก: -", size=12, color=ft.colors.GREY_700)
    card_item_containers: Dict[str, ft.Container] = {}

    def build_card_coord_items():
        items = []
        for i in range(1, 6):
            key = f"card_number_{i}"
            container = ft.Container(
                content=ft.Row([
                    ft.Text(f"เลขที่บัตร {i}", weight=ft.FontWeight.BOLD),
                    coord_inputs[key]["x"],
                    coord_inputs[key]["y"],
                    coord_inputs[key]["size"],
                    coord_inputs[key]["width"],
                    coord_inputs[key]["align"],
                ], spacing=8, wrap=True),
                bgcolor=ft.colors.WHITE,
                padding=8,
                border_radius=6,
                border=ft.border.all(1, ft.colors.GREY_300),
            )
            card_item_containers[key] = container
            items.append(container)
        return items

    def select_coord_target(key: str, label: str):
        # Highlight selected card container if exists
        try:
            for k, c in card_item_containers.items():
                c.bgcolor = ft.colors.WHITE
                c.border = ft.border.all(1, ft.colors.GREY_300)
            if key in card_item_containers:
                c = card_item_containers[key]
                c.bgcolor = ft.colors.YELLOW_50
                c.border = ft.border.all(2, ft.colors.AMBER_500)
        except Exception:
            pass
        selected_coord_field_label.value = f"ฟิลด์ที่เลือก: {label}"
        page.update()

    btn_signatory = ft.OutlinedButton("ผู้จ่ายเงิน", on_click=lambda e: select_coord_target("signatory_name", "ผู้จ่ายเงิน"))
    btn_card_1 = ft.OutlinedButton("เลขที่บัตร 1", on_click=lambda e: select_coord_target("card_number_1", "เลขที่บัตร 1"))
    btn_card_2 = ft.OutlinedButton("เลขที่บัตร 2", on_click=lambda e: select_coord_target("card_number_2", "เลขที่บัตร 2"))
    btn_card_3 = ft.OutlinedButton("เลขที่บัตร 3", on_click=lambda e: select_coord_target("card_number_3", "เลขที่บัตร 3"))
    btn_card_4 = ft.OutlinedButton("เลขที่บัตร 4", on_click=lambda e: select_coord_target("card_number_4", "เลขที่บัตร 4"))
    btn_card_5 = ft.OutlinedButton("เลขที่บัตร 5", on_click=lambda e: select_coord_target("card_number_5", "เลขที่บัตร 5"))
    card_coord_list_controls = build_card_coord_items()
    
    # Total fields
    total_income_display = ft.TextField(label="รวมเงินที่จ่าย", width=200, read_only=True)
    total_tax_display = ft.TextField(label="รวมภาษีหัก", width=200, read_only=True)
    total_tax_text = ft.TextField(label="ตัวอักษร", width=400)
    
    last_certificate_id = None
    
    def calculate_totals():
        try:
            total_income = float(income_1_amount.value or 0) + float(income_2_amount.value or 0)
            total_tax = float(income_1_tax.value or 0) + float(income_2_tax.value or 0)
            
            total_income_display.value = f"{total_income:,.2f}"
            total_tax_display.value = f"{total_tax:,.2f}"
            page.update()
        except ValueError:
            pass
    
    # Event listeners
    for field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax]:
        field.on_change = lambda e: calculate_totals()
    
    def save_form(e):
        nonlocal last_certificate_id
        try:
            if not all([withholder_name.value, withholder_tax_id.value, 
                       withholdee_name.value, withholdee_tax_id.value]):
                status_text.value = "❌ กรุณากรอกข้อมูลที่จำเป็น"
                status_text.color = ft.colors.RED_700
                page.update()
                return
            
            data = (
                withholder_name.value, withholder_address.value, withholder_tax_id.value, withholder_type.value or "บุคคล",
                withholdee_name.value, withholdee_address.value, withholdee_tax_id.value, withholdee_type.value or "บุคคล",
                certificate_book_no.value, certificate_no.value, 
                int(sequence_in_form.value) if sequence_in_form.value else None, form_type.value,
                float(income_1_amount.value or 0), float(income_1_tax.value or 0),
                float(income_2_amount.value or 0), float(income_2_tax.value or 0),
                0, 0, 0, 0, 0, 0, None, None, 0, 0, 0, 0, None,  # Other income fields
                float(total_income_display.value.replace(',', '') or 0), 
                float(total_tax_display.value.replace(',', '') or 0), total_tax_text.value,
                float(provident_fund.value or 0), float(social_security_fund.value or 0), 
                float(retirement_mutual_fund.value or 0),
                issue_type.value, None, issue_date.value or None, 
                signatory_name.value, company_seal.value
            )
            
            certificate_id = app.save_certificate(data)
            
            if certificate_id:
                last_certificate_id = certificate_id
                status_text.value = f"✅ บันทึกเรียบร้อย (ID: {certificate_id})"
                status_text.color = ft.colors.GREEN_700
                generate_crystal_pdf_button.disabled = False
                page.update()
            
        except Exception as ex:
            status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
            status_text.color = ft.colors.RED_700
        
        page.update()
    
    def generate_crystal_pdf(e):
        nonlocal last_certificate_id
        
        if not last_certificate_id:
            status_text.value = "❌ กรุณาบันทึกข้อมูลก่อน"
            status_text.color = ft.colors.RED_700
            page.update()
            return
        
        try:
            cert_data = app.get_certificate_by_id(last_certificate_id)
            if cert_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_filename = f"crystal_report_{last_certificate_id}_{timestamp}.pdf"
                # Inject temporary card numbers (not stored in DB)
                cert_data.update({
                    "card_number_1": card_number_1.value or "",
                    "card_number_2": card_number_2.value or "",
                    "card_number_3": card_number_3.value or "",
                    "card_number_4": card_number_4.value or "",
                    "card_number_5": card_number_5.value or "",
                })
                success, message = app.create_crystal_report_pdf(cert_data, pdf_filename)
                
                if success:
                    status_text.value = f"✅ {message}"
                    status_text.color = ft.colors.GREEN_700
                    
                    # Show success dialog
                    def close_dialog(e):
                        dialog.open = False
                        page.update()
                    
                    dialog = ft.AlertDialog(
                        title=ft.Text("Crystal Reports Style PDF สร้างสำเร็จ! 📊", color=ft.colors.GREEN_700, size=18),
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.ANALYTICS, size=40, color=ft.colors.BLUE_700),
                                    ft.Column([
                                        ft.Text("PDF ถูกสร้างด้วยเทคนิค Crystal Reports!", weight=ft.FontWeight.BOLD),
                                        ft.Text("ใช้ภาพพื้นหลังต้นฉบับพร้อมระบบ Sections", color=ft.colors.BLUE_700)
                                    ], spacing=5)
                                ], spacing=10),
                                ft.Divider(),
                                ft.Column([
                                    ft.Row([ft.Icon(ft.icons.FOLDER, size=16, color=ft.colors.BLUE_700), 
                                           ft.Text(f"ไฟล์: {pdf_filename}", size=12, weight=ft.FontWeight.BOLD)]),
                                    ft.Row([ft.Icon(ft.icons.LOCATION_ON, size=16, color=ft.colors.BLUE_700), 
                                           ft.Text(f"ตำแหน่ง: {os.path.abspath(pdf_filename)}", size=12)]),
                                    ft.Row([ft.Icon(ft.icons.FINGERPRINT, size=16, color=ft.colors.BLUE_700), 
                                           ft.Text(f"ID: {last_certificate_id}", size=12)]),
                                ], spacing=8),
                                ft.Divider(),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("🏗️ เทคนิค Crystal Reports ที่ใช้:", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700),
                                        ft.Text("• Page Header / Report Header / Detail Section", size=12),
                                        ft.Text("• Report Footer / Page Footer Structure", size=12),
                                        ft.Text("• Field Objects with Precise Positioning", size=12),
                                        ft.Text("• Formula Fields for Calculations", size=12),
                                        ft.Text("• Background Image Integration", size=12),
                                        ft.Text("• Multi-line Text with Can Grow", size=12),
                                        ft.Text("• Professional Report Layout", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.colors.GREEN_50,
                                    padding=15,
                                    border_radius=10
                                )
                            ], spacing=15),
                            width=600
                        ),
                        actions=[
                            ft.TextButton("🎉 ยอดเยี่ยม!", on_click=close_dialog,
                                        style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE))
                        ]
                    )
                    page.dialog = dialog
                    dialog.open = True
                    
                else:
                    status_text.value = f"❌ {message}"
                    status_text.color = ft.colors.RED_700
            
        except Exception as ex:
            status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
            status_text.color = ft.colors.RED_700
        
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
                      issue_date, signatory_name, total_tax_text,
                      card_number_1, card_number_2, card_number_3, card_number_4, card_number_5]:
            if hasattr(field, 'value'):
                field.value = "0" if field in [income_1_amount, income_1_tax, income_2_amount, income_2_tax,
                                               provident_fund, social_security_fund, retirement_mutual_fund] else ""
        
        for dropdown in [withholder_type, withholdee_type, form_type, issue_type]:
            dropdown.value = None
        
        company_seal.value = False
        calculate_totals()
        page.update()
    
    def view_certificates(e):
        certificates = app.get_all_certificates()
        
        if not certificates:
            status_text.value = "ไม่มีข้อมูลในฐานข้อมูล"
            status_text.color = ft.colors.ORANGE_700
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
                cert_data = app.get_certificate_by_id(certificate_id)
                if cert_data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_filename = f"crystal_style_{certificate_id}_{timestamp}.pdf"
                    success, message = app.create_crystal_report_pdf(cert_data, pdf_filename)
                    
                    if success:
                        status_text.value = f"✅ Crystal PDF: {pdf_filename}"
                        status_text.color = ft.colors.GREEN_700
                    else:
                        status_text.value = f"❌ {message}"
                        status_text.color = ft.colors.RED_700
                        
            except Exception as ex:
                status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                status_text.color = ft.colors.RED_700
            
            dialog.open = False
            page.update()
        
        rows = []
        for cert in certificates:
            crystal_button = ft.IconButton(
                icon=ft.icons.ANALYTICS,
                tooltip="สร้าง Crystal Reports PDF",
                icon_color=ft.colors.GREEN_700,
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
                    ft.Text("📊 คลิกปุ่มเขียวเพื่อสร้าง PDF แบบ Crystal Reports", size=12, color=ft.colors.GREEN_700),
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
        style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE),
        disabled=True,
        tooltip="บันทึกข้อมูลก่อนเพื่อสร้าง PDF แบบ Crystal Reports"
    )

    # Backup database controls
    backup_filename = ft.TextField(label="SQLite backup filename", value="backup.db", width=260)
    backup_status = ft.Text("", size=12)

    def fallback_backup_neon_to_sqlite(pg_conn_str: str, sqlite_path: str) -> Tuple[bool, str, Dict[str, int]]:
        """Minimal in-file backup if external helper is not available."""
        counts = {"tax_withholding_certificates": 0, "audit_logs": 0}
        try:
            # Connect to Neon
            pg_conn = psycopg2.connect(pg_conn_str)
            pg_cur = pg_conn.cursor()

            # Prepare SQLite
            if os.path.exists(sqlite_path):
                os.remove(sqlite_path)
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_conn.execute("PRAGMA journal_mode=WAL;")
            sqlite_conn.execute("PRAGMA synchronous=NORMAL;")
            s = sqlite_conn.cursor()

            # Create tables in SQLite
            s.execute(
                """
                CREATE TABLE IF NOT EXISTS tax_withholding_certificates (
                    id INTEGER PRIMARY KEY,
                    withholder_name TEXT NOT NULL,
                    withholder_address TEXT NOT NULL,
                    withholder_tax_id TEXT NOT NULL,
                    withholder_type TEXT NOT NULL,
                    withholdee_name TEXT NOT NULL,
                    withholdee_address TEXT NOT NULL,
                    withholdee_tax_id TEXT NOT NULL,
                    withholdee_type TEXT NOT NULL,
                    certificate_book_no TEXT,
                    certificate_no TEXT,
                    sequence_in_form INTEGER,
                    form_type TEXT,
                    income_type_1_amount REAL DEFAULT 0,
                    income_type_1_tax REAL DEFAULT 0,
                    income_type_2_amount REAL DEFAULT 0,
                    income_type_2_tax REAL DEFAULT 0,
                    income_type_3_amount REAL DEFAULT 0,
                    income_type_3_tax REAL DEFAULT 0,
                    income_type_4a_amount REAL DEFAULT 0,
                    income_type_4a_tax REAL DEFAULT 0,
                    income_type_4b_amount REAL DEFAULT 0,
                    income_type_4b_tax REAL DEFAULT 0,
                    dividend_credit_type TEXT,
                    dividend_tax_rate REAL,
                    income_type_5_amount REAL DEFAULT 0,
                    income_type_5_tax REAL DEFAULT 0,
                    income_type_6_amount REAL DEFAULT 0,
                    income_type_6_tax REAL DEFAULT 0,
                    income_type_6_description TEXT,
                    total_income REAL DEFAULT 0,
                    total_tax_withheld REAL DEFAULT 0,
                    total_tax_withheld_text TEXT,
                    provident_fund REAL DEFAULT 0,
                    social_security_fund REAL DEFAULT 0,
                    retirement_mutual_fund REAL DEFAULT 0,
                    issue_type TEXT,
                    issue_type_other TEXT,
                    issue_date TEXT,
                    signatory_name TEXT,
                    company_seal INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                );
                """
            )
            s.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY,
                    table_name TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    record_id INTEGER,
                    old_values TEXT,
                    new_values TEXT,
                    user_info TEXT,
                    timestamp TEXT
                );
                """
            )
            s.execute(
                "CREATE INDEX IF NOT EXISTS idx_withholder_tax_id ON tax_withholding_certificates(withholder_tax_id);"
            )
            s.execute(
                "CREATE INDEX IF NOT EXISTS idx_withholdee_tax_id ON tax_withholding_certificates(withholdee_tax_id);"
            )

            # Copy data: tax_withholding_certificates
            pg_cur.execute("SELECT * FROM tax_withholding_certificates ORDER BY id")
            rows = pg_cur.fetchall()
            if rows:
                # Get column names for positional insert
                pg_cur.execute(
                    """
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'tax_withholding_certificates'
                    ORDER BY ordinal_position
                    """
                )
                columns = [r[0] for r in pg_cur.fetchall()]
                placeholders = ",".join(["?"] * len(columns))
                insert_sql = f"INSERT INTO tax_withholding_certificates ({','.join(columns)}) VALUES ({placeholders})"
                s.executemany(insert_sql, rows)
                counts["tax_withholding_certificates"] = len(rows)

            # Copy data: audit_logs (if exists)
            try:
                pg_cur.execute("SELECT * FROM audit_logs ORDER BY id")
                arows = pg_cur.fetchall()
                if arows:
                    pg_cur.execute(
                        """
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = 'audit_logs'
                        ORDER BY ordinal_position
                        """
                    )
                    acolumns = [r[0] for r in pg_cur.fetchall()]
                    placeholders = ",".join(["?"] * len(acolumns))
                    insert_sql = f"INSERT INTO audit_logs ({','.join(acolumns)}) VALUES ({placeholders})"
                    s.executemany(insert_sql, arows)
                    counts["audit_logs"] = len(arows)
            except Exception:
                pass

            sqlite_conn.commit()
            s.close(); sqlite_conn.close(); pg_cur.close(); pg_conn.close()
            return True, f"Backup completed to {os.path.abspath(sqlite_path)}", counts
        except Exception as ex:
            return False, f"Backup error: {ex}", counts

    def run_backup(e):
        path = (backup_filename.value or "backup.db").strip()
        try:
            if backup_neon_to_sqlite:
                ok, msg, counts = backup_neon_to_sqlite(app.connection_string, path)
            else:
                ok, msg, counts = fallback_backup_neon_to_sqlite(app.connection_string, path)
            backup_status.value = ("✅ " if ok else "❌ ") + msg + (f" | rows: {counts}" if counts else "")
            backup_status.color = ft.colors.GREEN_700 if ok else ft.colors.RED_700
        except Exception as ex:
            backup_status.value = f"❌ {ex}"
            backup_status.color = ft.colors.RED_700
        page.update()
    
    # Build the UI - main form content (existing)
    form_container = ft.Container(
        content=ft.Column([
                # Header with Crystal Reports info
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.ANALYTICS, size=40, color=ft.colors.GREEN_700),
                            ft.Column([
                                ft.Text("Crystal Reports Style PDF Generator", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Professional Report Engine with Background Image Support", size=14, color=ft.colors.GREY_700),
                                template_status
                            ], spacing=2)
                        ]),
                        ft.Divider(height=1, color=ft.colors.GREY_300),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.ARCHITECTURE, size=16, color=ft.colors.GREEN_700),
                                    ft.Text("เทคนิค Crystal Reports: Report Sections, Field Objects, Formula Fields, Background Integration", 
                                           size=12, color=ft.colors.GREEN_700, weight=ft.FontWeight.BOLD)
                                ], spacing=5),
                                ft.Row([
                                    ft.Icon(ft.icons.LAYERS, size=16, color=ft.colors.BLUE_700),
                                    ft.Text("• Page/Report Headers • Detail Section • Calculated Fields • Professional Layout • High DPI Output", 
                                           size=11, color=ft.colors.BLUE_700)
                                ], spacing=5)
                            ], spacing=5),
                            bgcolor=ft.colors.GREEN_50,
                            padding=15,
                            border_radius=10
                        )
                    ], spacing=10),
                    bgcolor=ft.colors.GREY_50,
                    border_radius=10,
                    padding=20,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Action buttons
                ft.Row([
                    ft.ElevatedButton("💾 บันทึกข้อมูล", on_click=save_form, 
                                    style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)),
                    generate_crystal_pdf_button,
                    ft.ElevatedButton("🗑️ เคลียร์ฟอร์ม", on_click=clear_form,
                                    style=ft.ButtonStyle(bgcolor=ft.colors.ORANGE_700, color=ft.colors.WHITE)),
                    ft.ElevatedButton("📋 ดูรายการ", on_click=view_certificates,
                                    style=ft.ButtonStyle(bgcolor=ft.colors.PURPLE_700, color=ft.colors.WHITE))
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
                                ft.Row([income_2_amount, income_2_tax], spacing=10),
                                ft.Divider(height=20, color=ft.colors.BLUE_700),
                                ft.Row([total_income_display, total_tax_display], spacing=10),
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
                                ft.Row([issue_type, issue_date], spacing=10),
                                ft.Row([signatory_name, company_seal], spacing=10)
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                # New section: เลขบัตรห้าตำแหน่ง (after funds & signature)
                ft.ExpansionTile(
                    title=ft.Text("เลขบัตรห้าตำแหน่ง", weight=ft.FontWeight.BOLD),
                    initially_expanded=False,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("กรอกข้อความเพื่อใส่ลง PDF (ไม่บันทึกฐานข้อมูล)", size=12, color=ft.colors.GREY_700),
                                ft.Row([card_number_1, card_number_2, card_number_3, card_number_4, card_number_5], spacing=10, wrap=True),
                            ], spacing=10),
                            padding=10,
                            bgcolor=ft.colors.GREY_50,
                            border_radius=10
                        )
                    ]
                ),
                
                # Crystal Reports methodology explanation
                ft.ExpansionTile(
                    title=ft.Text("📊 Crystal Reports Methodology", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("🏗️ เทคนิค Crystal Reports ที่นำมาใช้:", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700, size=16),
                                ft.Divider(),
                                
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("📋 Report Sections (แบ่งส่วนรายงาน):", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700),
                                        ft.Text("• Page Header: ส่วนหัวของหน้า (ว่าง)", size=12),
                                        ft.Text("• Report Header: ข้อมูลเอกสารอ้างอิง", size=12),
                                        ft.Text("• Detail Section: ข้อมูลหลักของฟอร์ม", size=12),
                                        ft.Text("• Report Footer: ลายเซ็นและวันที่", size=12),
                                        ft.Text("• Page Footer: หมายเหตุทางกฎหมาย", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.colors.GREEN_50,
                                    padding=10,
                                    border_radius=5
                                ),
                                
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("🎯 Field Objects (วัตถุฟิลด์):", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                                        ft.Text("• Text Objects: ตำแหน่งและการจัดรูปแบบที่แม่นยำ", size=12),
                                        ft.Text("• Font Management: การจัดการฟอนต์ไทยและอังกฤษ", size=12),
                                        ft.Text("• Alignment: Left, Right, Center alignment", size=12),
                                        ft.Text("• Can Grow Fields: ข้อความหลายบรรทัด", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.colors.BLUE_50,
                                    padding=10,
                                    border_radius=5
                                ),
                                
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("🧮 Formula Fields (ฟิลด์สูตร):", weight=ft.FontWeight.BOLD, color=ft.colors.PURPLE_700),
                                        ft.Text("• Calculated Totals: การคำนวณยอดรวมอัตโนมัติ", size=12),
                                        ft.Text("• Number Formatting: การจัดรูปแบบตัวเลข", size=12),
                                        ft.Text("• Conditional Logic: เงื่อนไขในการแสดงผล", size=12),
                                        ft.Text("• Data Validation: การตรวจสอบข้อมูล", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.colors.PURPLE_50,
                                    padding=10,
                                    border_radius=5
                                ),
                                
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("🖼️ Background Integration:", weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE_700),
                                        ft.Text("• PDF to Image Conversion: แปลง PDF เป็นภาพคุณภาพสูง", size=12),
                                        ft.Text("• High DPI Rendering: เรนเดอร์ 300 DPI สำหรับการพิมพ์", size=12),
                                        ft.Text("• Overlay Technique: วางข้อมูลทับภาพพื้นหลัง", size=12),
                                        ft.Text("• Professional Output: ผลลัพธ์ระดับมืออาชีพ", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.colors.ORANGE_50,
                                    padding=10,
                                    border_radius=5
                                ),
                                
                                ft.Divider(),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("⚙️ Technical Implementation:", weight=ft.FontWeight.BOLD, color=ft.colors.TEAL_700),
                                        ft.Text("pip install reportlab PyMuPDF", 
                                               style=ft.TextStyle(bgcolor=ft.colors.BLACK, color=ft.colors.WHITE, size=12)),
                                        ft.Text("• ReportLab Canvas API สำหรับการวาด", size=12),
                                        ft.Text("• PyMuPDF สำหรับแปลง PDF เป็นภาพ", size=12),
                                        ft.Text("• Section-based Rendering Architecture", size=12),
                                        ft.Text("• Professional Typography Support", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.colors.TEAL_50,
                                    padding=10,
                                    border_radius=5
                                ),
                            ], spacing=15),
                            padding=20
                        )
                    ]
                )
                ,
                # PDF coordinate tuning panel
                ft.ExpansionTile(
                    title=ft.Text("ปรับตำแหน่งฟิลด์ pdf", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                # Quick selection menu row (add 5 buttons after ผู้จ่ายเงิน)
                                ft.Row([
                                    ft.Text("เมนูเลือกฟิลด์อย่างรวดเร็ว:", weight=ft.FontWeight.BOLD),
                                    btn_signatory,
                                    btn_card_1,
                                    btn_card_2,
                                    btn_card_3,
                                    btn_card_4,
                                    btn_card_5,
                                ], spacing=8, wrap=True),
                                selected_coord_field_label,
                                ft.Text("ค่าชั่วคราวสำหรับใส่ใน PDF (ไม่บันทึกฐานข้อมูล)", size=12, color=ft.colors.GREY_700),
                                ft.Row([card_number_1, card_number_2, card_number_3, card_number_4, card_number_5], spacing=10, wrap=True),
                                ft.Divider(),
                                ft.Text("ตั้งค่าพิกัดตำแหน่งใน PDF", weight=ft.FontWeight.BOLD),
                                ft.Text("หน่วยเป็นจุด (pt) จากมุมซ้ายล่างของหน้า A4 ตามระบบของ ReportLab", size=11, color=ft.colors.GREY_700),
                                # ListView for coordinate items (append 5 new items for card numbers)
                                ft.ListView(
                                    expand=False,
                                    spacing=6,
                                    padding=ft.padding.all(0),
                                    controls=card_coord_list_controls
                                ),
                                ft.Row([
                                    ft.ElevatedButton("บันทึกพิกัด", icon=ft.icons.SAVE, on_click=save_card_coords,
                                                     style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)),
                                ], alignment=ft.MainAxisAlignment.START)
                            ], spacing=10),
                            padding=10,
                            bgcolor=ft.colors.BLUE_50,
                            border_radius=10
                        )
                    ]
                ),
                # Backup database tab
                ft.ExpansionTile(
                    title=ft.Text("💾 Backup database", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Backup Neon PostgreSQL to local SQLite (backup.db)", size=12),
                                ft.Row([backup_filename, ft.ElevatedButton("Run backup", icon=ft.icons.CLOUD_DOWNLOAD, on_click=run_backup)], spacing=10),
                                backup_status,
                                ft.Text("ไฟล์จะถูกบันทึกไว้ในโฟลเดอร์เดียวกับโปรแกรม", size=11, color=ft.colors.GREY_700),
                            ], spacing=10),
                            padding=10,
                            bgcolor=ft.colors.BLUE_50,
                            border_radius=10
                        )
                    ]
                )
                
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
        padding=20,
        expand=True
    )

    # Backup view content (separate tab)
    backup_container = ft.Container(
        content=ft.Column([
            ft.Text("สำรองข้อมูล", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("สำรองข้อมูลจาก Neon PostgreSQL ไปยังไฟล์ SQLite ภายในเครื่อง", size=12),
            ft.Row([backup_filename, ft.ElevatedButton("เริ่มสำรองข้อมูล", icon=ft.icons.CLOUD_DOWNLOAD, on_click=run_backup)], spacing=10),
            backup_status,
            ft.Text("ไฟล์จะถูกบันทึกในโฟลเดอร์เดียวกับโปรแกรม", size=11, color=ft.colors.GREY_700)
        ], spacing=12),
        padding=20,
        expand=True
    )

    # Import-from-Excel view content (new tab)
    imported_rows_state: List[tuple] = []  # local list to show in grid
    grid_rows: List[ft.DataRow] = []

    grid_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("ผู้หักภาษี")),
            ft.DataColumn(ft.Text("ผู้ถูกหักภาษี")),
            ft.DataColumn(ft.Text("ยอดรวม")),
            ft.DataColumn(ft.Text("ภาษีหัก")),
            ft.DataColumn(ft.Text("วันที่")),
        ],
        rows=[],
        column_spacing=12,
        data_row_max_height=42,
    )

    import_status = ft.Text("", size=12)

    def refresh_grid():
        nonlocal imported_rows_state
        # Load latest from DB
        rows = app.get_all_certificates()
        imported_rows_state = rows
        grid_table.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(r[0]))),
                ft.DataCell(ft.Text(r[1] or "")),
                ft.DataCell(ft.Text(r[2] or "")),
                ft.DataCell(ft.Text(f"{float(r[3]):,.2f}" if r[3] else "0")),
                ft.DataCell(ft.Text(f"{float(r[4]):,.2f}" if r[4] else "0")),
                ft.DataCell(ft.Text(str(r[5]) if r[5] else "")),
            ]) for r in rows
        ]
        page.update()

    def perform_import(path: str):
        ok, msg, count = app.import_excel_to_db(path)
        import_status.value = ("✅ " if ok else "❌ ") + msg
        import_status.color = ft.colors.GREEN_700 if ok else ft.colors.RED_700
        refresh_grid()

    def pick_excel_and_import(e):
        def on_res(res: ft.FilePickerResultEvent):
            if res.files:
                perform_import(res.files[0].path)
        picker = ft.FilePicker(on_result=on_res)
        page.overlay.append(picker)
        page.update()
        picker.pick_files(allowed_extensions=["xlsx"], dialog_title="เลือกไฟล์ Excel (transfer_records.xlsx)")

    def delete_selected(e):
        # For simplicity, remove last N rows equal to selection count placeholder
        # In a full implementation you’d add row selection handling; here we delete last row
        if not imported_rows_state:
            return
        last_id = imported_rows_state[0][0]
        ok, msg, _ = app.delete_certificates([last_id])
        import_status.value = ("✅ " if ok else "❌ ") + msg
        import_status.color = ft.colors.GREEN_700 if ok else ft.colors.RED_700
        refresh_grid()

    def add_empty_record(e):
        # Minimal add example; opens a blank row with defaults
        data = (
            "", "", "0000000000000", "บุคคล",
            "", "", "0000000000000", "บุคคล",
            None, None, None, None,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, None,
            0, 0, 0, 0, None,
            0, 0, None,
            0, 0, 0,
            None, None, None,
            None, False
        )
        new_id = app.save_certificate(data)
        import_status.value = "✅ เพิ่มรายการใหม่แล้ว" if new_id else "❌ เพิ่มรายการไม่สำเร็จ"
        import_status.color = ft.colors.GREEN_700 if new_id else ft.colors.RED_700
        refresh_grid()

    def edit_first_row(e):
        if not imported_rows_state:
            return
        rid = imported_rows_state[0][0]
        ok, msg = app.update_certificate_basic(rid, {"withholder_name": "แก้ไขชื่อ"})
        import_status.value = ("✅ " if ok else "❌ ") + msg
        import_status.color = ft.colors.GREEN_700 if ok else ft.colors.RED_700
        refresh_grid()

    import_container = ft.Container(
        content=ft.Column([
            ft.Text("นำเข้าจาก Excel", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("ไฟล์ตัวอย่าง: transfer_records.xlsx (โครงสร้างเดียวกับไฟล์ส่งออก)", size=12),
            ft.Row([
                ft.ElevatedButton("เลือกไฟล์และนำเข้า", icon=ft.icons.UPLOAD_FILE, on_click=pick_excel_and_import),
                ft.ElevatedButton("เพิ่ม", icon=ft.icons.ADD, on_click=add_empty_record),
                ft.ElevatedButton("แก้ไข (ตัวอย่าง)", icon=ft.icons.EDIT, on_click=edit_first_row),
                ft.ElevatedButton("ลบ (ตัวอย่าง)", icon=ft.icons.DELETE, on_click=delete_selected),
            ], spacing=10, wrap=True),
            import_status,
            ft.Container(content=grid_table, height=420, padding=10),
        ], spacing=12),
        padding=20,
        expand=True
    )
    refresh_grid()

    content_area = ft.Container(content=form_container, expand=True)

    def on_nav_change(e):
        idx = e.control.selected_index
        content_area.content = (
            form_container if idx == 0 else (
                import_container if idx == 1 else backup_container
            )
        )
        page.update()

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(icon=ft.icons.DESCRIPTION, label="แบบฟอร์ม"),
            ft.NavigationRailDestination(icon=ft.icons.FILE_UPLOAD, label="นำเข้าจาก Excel"),
            ft.NavigationRailDestination(icon=ft.icons.BACKUP, label="สำรองข้อมูล"),
        ],
        on_change=on_nav_change,
    )

    page.add(ft.Row([nav_rail, content_area], expand=True))

if __name__ == "__main__":
    # Installation requirements
    required_packages = """
    📊 Crystal Reports Style PDF Generator Requirements:
    pip install flet pandas psycopg2-binary reportlab PyMuPDF Pillow
    
    📄 Files needed:
    1. tax_form_template.pdf (your uploaded PDF template)
    2. THSarabunNew.ttf (Thai font - optional)
    
    🏗️ Crystal Reports Features Implemented:
    • Report Sections Architecture (Header/Detail/Footer)
    • Field Objects with precise positioning
    • Formula Fields for calculations
    • Background Image Integration
    • High DPI Professional Output
    • Multi-font Support
    • Conditional Rendering
    
    🎯 Crystal Reports Methodology:
    This implementation uses the same architectural patterns as Crystal Reports:
    - Section-based layout design
    - Field object positioning system
    - Formula field calculations
    - Background template integration
    - Professional typography
    - High-quality PDF output
    """
    print(required_packages)
    ft.app(target=main)