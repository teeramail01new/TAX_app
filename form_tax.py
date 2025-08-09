import flet as ft
import psycopg2
import pandas as pd
from datetime import datetime
import os
from decimal import Decimal
import json

class NeonTaxWithholdingApp:
    def __init__(self):
        self.connection_string = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
        self.init_database()
        
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(self.connection_string)
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def init_database(self):
        """Initialize PostgreSQL database and create tables"""
        conn = self.get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Create table for tax withholding certificates
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tax_withholding_certificates (
                    id SERIAL PRIMARY KEY,
                    
                    -- ผู้มีหน้าที่หักภาษี ณ ที่จ่าย (Tax Withholder)
                    withholder_name VARCHAR(255) NOT NULL,
                    withholder_address TEXT NOT NULL,
                    withholder_tax_id VARCHAR(13) NOT NULL,
                    withholder_type VARCHAR(50) NOT NULL,
                    
                    -- ผู้ถูกหักภาษี ณ ที่จ่าย (Tax Withholdee)
                    withholdee_name VARCHAR(255) NOT NULL,
                    withholdee_address TEXT NOT NULL,
                    withholdee_tax_id VARCHAR(13) NOT NULL,
                    withholdee_type VARCHAR(50) NOT NULL,
                    
                    -- เอกสารอ้างอิง (Document Reference)
                    certificate_book_no VARCHAR(50),
                    certificate_no VARCHAR(50),
                    sequence_in_form INTEGER,
                    form_type VARCHAR(20),
                    
                    -- รายการเงินได้และภาษี (Income and Tax Details)
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
                    
                    -- ยอดรวม (Totals)
                    total_income DECIMAL(15,2) DEFAULT 0,
                    total_tax_withheld DECIMAL(15,2) DEFAULT 0,
                    total_tax_withheld_text TEXT,
                    
                    -- กองทุนต่าง ๆ (Funds)
                    provident_fund DECIMAL(15,2) DEFAULT 0,
                    social_security_fund DECIMAL(15,2) DEFAULT 0,
                    retirement_mutual_fund DECIMAL(15,2) DEFAULT 0,
                    
                    -- การออกใบรับรอง (Certificate Issuance)
                    issue_type VARCHAR(50),
                    issue_type_other VARCHAR(100),
                    
                    -- วันที่และลายเซ็น (Date and Signature)
                    issue_date DATE,
                    signatory_name VARCHAR(255),
                    company_seal BOOLEAN DEFAULT FALSE,
                    
                    -- Metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Create index on tax IDs for faster searches
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_withholder_tax_id 
                ON tax_withholding_certificates(withholder_tax_id);
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_withholdee_tax_id 
                ON tax_withholding_certificates(withholdee_tax_id);
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_issue_date 
                ON tax_withholding_certificates(issue_date);
            ''')
            
            # Create a table for audit logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    table_name VARCHAR(100) NOT NULL,
                    operation VARCHAR(20) NOT NULL,
                    record_id INTEGER,
                    old_values JSONB,
                    new_values JSONB,
                    user_info TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Create a statistics view
            cursor.execute('''
                CREATE OR REPLACE VIEW certificate_statistics AS
                SELECT 
                    COUNT(*) as total_certificates,
                    SUM(total_income) as total_income_sum,
                    SUM(total_tax_withheld) as total_tax_sum,
                    AVG(total_income) as avg_income,
                    AVG(total_tax_withheld) as avg_tax,
                    MIN(issue_date) as earliest_date,
                    MAX(issue_date) as latest_date,
                    COUNT(DISTINCT withholder_tax_id) as unique_withholders,
                    COUNT(DISTINCT withholdee_tax_id) as unique_withholdees
                FROM tax_withholding_certificates
                WHERE total_income > 0 OR total_tax_withheld > 0;
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
        """Save tax withholding certificate to database"""
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
            
            # Log the insert operation
            cursor.execute('''
                INSERT INTO audit_logs (table_name, operation, record_id, new_values)
                VALUES (%s, %s, %s, %s);
            ''', ('tax_withholding_certificates', 'INSERT', certificate_id, json.dumps(dict(zip([
                'withholder_name', 'withholder_address', 'withholder_tax_id', 'withholder_type',
                'withholdee_name', 'withholdee_address', 'withholdee_tax_id', 'withholdee_type'
            ], data[:8])))))
            
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
        """Get all certificates from database"""
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
        """Get database statistics"""
        conn = self.get_connection()
        if not conn:
            return (0, 0, 0, 0, 0)
            
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT total_certificates, total_income_sum, total_tax_sum, 
                       unique_withholders, unique_withholdees
                FROM certificate_statistics;
            ''')
            
            stats = cursor.fetchone()
            return stats if stats else (0, 0, 0, 0, 0)
            
        except Exception as e:
            print(f"Get statistics error: {e}")
            return (0, 0, 0, 0, 0)
        finally:
            cursor.close()
            conn.close()
    
    def search_certificates(self, search_term):
        """Search certificates by name or tax ID"""
        conn = self.get_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, withholder_name, withholdee_name, total_income, 
                       total_tax_withheld, issue_date, created_at
                FROM tax_withholding_certificates
                WHERE withholder_name ILIKE %s 
                   OR withholdee_name ILIKE %s
                   OR withholder_tax_id LIKE %s
                   OR withholdee_tax_id LIKE %s
                ORDER BY created_at DESC
                LIMIT 50;
            ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            
            certificates = cursor.fetchall()
            return certificates
            
        except Exception as e:
            print(f"Search certificates error: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def export_to_excel(self, file_path, date_from=None, date_to=None):
        """Export certificates to Excel with optional date filtering"""
        conn = self.get_connection()
        if not conn:
            return False, "ไม่สามารถเชื่อมต่อฐานข้อมูลได้"
            
        try:
            # Build query with optional date filtering
            base_query = "SELECT * FROM tax_withholding_certificates"
            params = []
            
            if date_from and date_to:
                base_query += " WHERE issue_date BETWEEN %s AND %s"
                params = [date_from, date_to]
            elif date_from:
                base_query += " WHERE issue_date >= %s"
                params = [date_from]
            elif date_to:
                base_query += " WHERE issue_date <= %s"
                params = [date_to]
            
            base_query += " ORDER BY created_at DESC"
            
            df = pd.read_sql_query(base_query, conn, params=params)
            
            # Create summary statistics
            stats_query = "SELECT * FROM certificate_statistics"
            stats_df = pd.read_sql_query(stats_query, conn)
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='Tax Certificates', index=False)
                
                # Statistics sheet
                stats_df.to_excel(writer, sheet_name='Statistics', index=False)
                
                # Summary by month sheet
                if not df.empty and 'issue_date' in df.columns:
                    df['issue_date'] = pd.to_datetime(df['issue_date'])
                    monthly_summary = df.groupby(df['issue_date'].dt.to_period('M')).agg({
                        'total_income': ['count', 'sum', 'mean'],
                        'total_tax_withheld': ['sum', 'mean']
                    }).round(2)
                    monthly_summary.to_excel(writer, sheet_name='Monthly Summary')
                
                # Auto-adjust column widths for all sheets
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
            print(f"Export error: {e}")
            return False, f"เกิดข้อผิดพลาดในการส่งออก: {str(e)}"
        finally:
            conn.close()
    
    def backup_database(self, backup_path):
        """Create a backup of the database"""
        try:
            conn = self.get_connection()
            if not conn:
                return False, "ไม่สามารถเชื่อมต่อฐานข้อมูลได้"
            
            # Export all tables to JSON
            backup_data = {}
            
            cursor = conn.cursor()
            
            # Backup certificates
            cursor.execute("SELECT * FROM tax_withholding_certificates ORDER BY id")
            certificates = cursor.fetchall()
            
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tax_withholding_certificates' ORDER BY ordinal_position")
            columns = [row[0] for row in cursor.fetchall()]
            
            backup_data['certificates'] = [dict(zip(columns, row)) for row in certificates]
            
            # Backup audit logs
            cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 1000")
            logs = cursor.fetchall()
            
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'audit_logs' ORDER BY ordinal_position")
            log_columns = [row[0] for row in cursor.fetchall()]
            
            backup_data['audit_logs'] = [dict(zip(log_columns, row)) for row in logs]
            
            # Save to JSON file
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            return True, f"สำรองข้อมูลเรียบร้อยแล้ว: {backup_path}"
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาดในการสำรองข้อมูล: {str(e)}"
        finally:
            if conn:
                cursor.close()
                conn.close()

def main(page: ft.Page):
    page.title = "ระบบหนังสือรับรองการหักภาษี ณ ที่จ่าย (Neon Database)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    page.window_resizable = True
    page.scroll = ft.ScrollMode.AUTO
    
    app = NeonTaxWithholdingApp()
    
    # Database connection status
    connection_status = ft.Text("🔄 กำลังตรวจสอบการเชื่อมต่อ...", size=12)
    
    def check_connection():
        conn = app.get_connection()
        if conn:
            connection_status.value = "✅ เชื่อมต่อ Neon Database สำเร็จ"
            connection_status.color = ft.colors.GREEN_700
            conn.close()
        else:
            connection_status.value = "❌ ไม่สามารถเชื่อมต่อ Neon Database ได้"
            connection_status.color = ft.colors.RED_700
        page.update()
    
    # Check connection on startup
    check_connection()
    
    # Status message
    status_text = ft.Text("พร้อมใช้งาน", size=14, color=ft.colors.GREEN_700)
    
    # Search functionality
    search_field = ft.TextField(
        label="🔍 ค้นหาด้วยชื่อหรือเลขประจำตัวผู้เสียภาษี",
        width=400,
        on_submit=lambda e: search_certificates()
    )
    
    def search_certificates():
        if not search_field.value:
            return
        
        results = app.search_certificates(search_field.value)
        show_search_results(results)
    
    def show_search_results(results):
        if not results:
            status_text.value = "ไม่พบข้อมูลที่ค้นหา"
            status_text.color = ft.colors.ORANGE_700
            page.update()
            return
        
        # Create results table
        columns = [
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("ผู้หักภาษี")),
            ft.DataColumn(ft.Text("ผู้ถูกหักภาษี")),
            ft.DataColumn(ft.Text("ยอดรวม")),
            ft.DataColumn(ft.Text("ภาษีหัก")),
            ft.DataColumn(ft.Text("วันที่"))
        ]
        
        rows = []
        for cert in results:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(cert[0]))),
                ft.DataCell(ft.Text(cert[1][:20] + "..." if len(cert[1]) > 20 else cert[1])),
                ft.DataCell(ft.Text(cert[2][:20] + "..." if len(cert[2]) > 20 else cert[2])),
                ft.DataCell(ft.Text(f"฿{cert[3]:,.2f}" if cert[3] else "0")),
                ft.DataCell(ft.Text(f"฿{cert[4]:,.2f}" if cert[4] else "0")),
                ft.DataCell(ft.Text(str(cert[5]) if cert[5] else ""))
            ]))
        
        results_table = ft.DataTable(columns=columns, rows=rows)
        
        def close_search_dialog(e):
            search_dialog.open = False
            page.update()
        
        search_dialog = ft.AlertDialog(
            title=ft.Text(f"ผลการค้นหา ({len(results)} รายการ)"),
            content=ft.Container(
                content=ft.Column([results_table], scroll=ft.ScrollMode.AUTO),
                width=800,
                height=400
            ),
            actions=[ft.TextButton("ปิด", on_click=close_search_dialog)]
        )
        
        page.dialog = search_dialog
        search_dialog.open = True
        page.update()
    
    # Form fields (same as before but with additional features)
    # ... (keeping all the form fields from the previous version)
    
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
    
    # Statistics display
    def update_statistics():
        stats = app.get_statistics()
        if stats:
            stats_display.value = f"""
📊 สถิติฐานข้อมูล Neon:
• จำนวนใบรับรอง: {stats[0]:,} ฉบับ
• ยอดรวมเงินได้: ฿{stats[1]:,.2f}
• ยอดรวมภาษีหัก: ฿{stats[2]:,.2f}
• จำนวนผู้หักภาษี: {stats[3]:,} ราย
• จำนวนผู้ถูกหักภาษี: {stats[4]:,} ราย
            """.strip()
        else:
            stats_display.value = "ไม่สามารถโหลดสถิติได้"
        page.update()
    
    stats_display = ft.Text("กำลังโหลดสถิติ...", size=12)
    update_statistics()
    
    def save_form(e):
        """Save form data to Neon database"""
        try:
            # Validate required fields
            if not all([withholder_name.value, withholder_tax_id.value, 
                       withholdee_name.value, withholdee_tax_id.value]):
                status_text.value = "❌ กรุณากรอกข้อมูลที่จำเป็น"
                status_text.color = ft.colors.RED_700
                page.update()
                return
            
            # Validate tax ID format
            if len(withholder_tax_id.value) != 13 or not withholder_tax_id.value.isdigit():
                status_text.value = "❌ เลขประจำตัวผู้เสียภาษีผู้หักภาษีต้องเป็นตัวเลข 13 หลัก"
                status_text.color = ft.colors.RED_700
                page.update()
                return
                
            if len(withholdee_tax_id.value) != 13 or not withholdee_tax_id.value.isdigit():
                status_text.value = "❌ เลขประจำตัวผู้เสียภาษีผู้ถูกหักภาษีต้องเป็นตัวเลข 13 หลัก"
                status_text.color = ft.colors.RED_700
                page.update()
                return
            
            # Prepare data
            data = (
                withholder_name.value, withholder_address.value, withholder_tax_id.value, withholder_type.value or "บุคคล",
                withholdee_name.value, withholdee_address.value, withholdee_tax_id.value, withholdee_type.value or "บุคคล",
                certificate_book_no.value, certificate_no.value, 
                int(sequence_in_form.value) if sequence_in_form.value else None, form_type.value,
                float(income_1_amount.value or 0), float(income_1_tax.value or 0),
                float(income_2_amount.value or 0), float(income_2_tax.value or 0),
                float(income_3_amount.value or 0), float(income_3_tax.value or 0),
                float(income_4a_amount.value or 0), float(income_4a_tax.value or 0),
                float(income_4b_amount.value or 0), float(income_4b_tax.value or 0),
                dividend_credit_type.value, float(dividend_tax_rate.value or 0),
                float(income_5_amount.value or 0), float(income_5_tax.value or 0),
                float(income_6_amount.value or 0), float(income_6_tax.value or 0), income_6_description.value,
                float(total_income_display.value.replace(',', '') or 0), 
                float(total_tax_display.value.replace(',', '') or 0), total_tax_text.value,
                float(provident_fund.value or 0), float(social_security_fund.value or 0), 
                float(retirement_mutual_fund.value or 0),
                issue_type.value, issue_type_other.value, issue_date.value or None, 
                signatory_name.value, company_seal.value
            )
            
            certificate_id = app.save_certificate(data)
            
            if certificate_id:
                status_text.value = f"✅ บันทึกข้อมูลใน Neon Database เรียบร้อยแล้ว (ID: {certificate_id})"
                status_text.color = ft.colors.GREEN_700
                
                # Update statistics
                update_statistics()
                
                # Clear form
                clear_form(None)
            else:
                status_text.value = "❌ ไม่สามารถบันทึกข้อมูลได้"
                status_text.color = ft.colors.RED_700
                
        except Exception as ex:
            status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
            status_text.color = ft.colors.RED_700
        
        page.update()
    
    def clear_form(e):
        """Clear all form fields"""
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
    
    def export_excel(e):
        """Export data to Excel from Neon database"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"neon_tax_certificates_{timestamp}.xlsx"
            success, message = app.export_to_excel(filename)
            
            if success:
                status_text.value = f"✅ {message}"
                status_text.color = ft.colors.GREEN_700
                
                # Show success dialog with file info
                def close_dialog(e):
                    dialog.open = False
                    page.update()
                
                dialog = ft.AlertDialog(
                    title=ft.Text("ส่งออกข้อมูลสำเร็จ!", color=ft.colors.GREEN_700),
                    content=ft.Text(f"""
ไฟล์ Excel ถูกสร้างเรียบร้อยแล้ว!

📁 ชื่อไฟล์: {filename}
📍 ตำแหน่ง: {os.path.abspath(filename)}
🗄️ ข้อมูลจาก: Neon PostgreSQL Database

ไฟล์ประกอบด้วย:
• แผ่น Tax Certificates: ข้อมูลใบรับรองทั้งหมด
• แผ่น Statistics: สถิติสรุป
• แผ่น Monthly Summary: สรุปรายเดือน
                    """.strip()),
                    actions=[ft.TextButton("ตกลง", on_click=close_dialog)]
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
    
    def view_certificates(e):
        """View saved certificates from Neon database"""
        certificates = app.get_all_certificates()
        
        if not certificates:
            status_text.value = "ไม่มีข้อมูลหนังสือรับรองใน Neon Database"
            status_text.color = ft.colors.ORANGE_700
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
                    ft.Text("🗄️ ข้อมูลจาก Neon PostgreSQL Database", size=12, color=ft.colors.BLUE_700),
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
    
    def backup_database(e):
        """Create backup of Neon database"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"neon_backup_{timestamp}.json"
            
            success, message = app.backup_database(backup_filename)
            
            if success:
                status_text.value = f"✅ {message}"
                status_text.color = ft.colors.GREEN_700
            else:
                status_text.value = f"❌ {message}"
                status_text.color = ft.colors.RED_700
                
        except Exception as ex:
            status_text.value = f"❌ เกิดข้อผิดพลาดในการสำรองข้อมูล: {str(ex)}"
            status_text.color = ft.colors.RED_700
        
        page.update()
    
    def refresh_connection(e):
        """Refresh database connection"""
        check_connection()
        update_statistics()
    
    # Build the UI
    page.add(
        ft.Container(
            content=ft.Column([
                # Header with database info
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.CLOUD_OUTLINED, size=40, color=ft.colors.BLUE_700),
                            ft.Column([
                                ft.Text("ระบบหนังสือรับรองการหักภาษี ณ ที่จ่าย", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Tax Withholding Certificate System with Neon PostgreSQL", size=14, color=ft.colors.GREY_700),
                                connection_status
                            ], spacing=2)
                        ]),
                        stats_display
                    ], spacing=10),
                    bgcolor=ft.colors.BLUE_50,
                    border_radius=10,
                    padding=20,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Search and action buttons
                ft.Row([
                    search_field,
                    ft.ElevatedButton("🔍 ค้นหา", on_click=lambda e: search_certificates(),
                                    style=ft.ButtonStyle(bgcolor=ft.colors.INDIGO_700, color=ft.colors.WHITE))
                ], spacing=10),
                
                ft.Row([
                    ft.ElevatedButton("💾 บันทึกข้อมูล", on_click=save_form, 
                                    style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)),
                    ft.ElevatedButton("🗑️ เคลียร์ฟอร์ม", on_click=clear_form,
                                    style=ft.ButtonStyle(bgcolor=ft.colors.ORANGE_700, color=ft.colors.WHITE)),
                    ft.ElevatedButton("📋 ดูรายการ", on_click=view_certificates,
                                    style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)),
                    ft.ElevatedButton("📁 ส่งออก Excel", on_click=export_excel,
                                    style=ft.ButtonStyle(bgcolor=ft.colors.PURPLE_700, color=ft.colors.WHITE)),
                    ft.ElevatedButton("💾 สำรองข้อมูล", on_click=backup_database,
                                    style=ft.ButtonStyle(bgcolor=ft.colors.TEAL_700, color=ft.colors.WHITE)),
                    ft.ElevatedButton("🔄 รีเฟรช", on_click=refresh_connection,
                                    style=ft.ButtonStyle(bgcolor=ft.colors.GREY_700, color=ft.colors.WHITE))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8, wrap=True),
                
                status_text,
                ft.Divider(),
                
                # Form sections (same structure as before)
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
                                
                                ft.Divider(height=30, color=ft.colors.BLUE_700, thickness=2),
                                ft.Text("ยอดรวม", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
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
    )

if __name__ == "__main__":
    # Required packages installation note
    required_packages = """
    Required packages for Neon PostgreSQL version:
    pip install flet pandas openpyxl psycopg2-binary
    
    Database: Neon PostgreSQL
    Connection: Secure SSL connection to ap-southeast-1 region
    """
    print(required_packages)
    ft.app(target=main)