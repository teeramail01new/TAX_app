 # Form fields (abbreviated for space)
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
                status_text.color = ft.colors.RED_700
                page.update()
                return
            
            # Prepare data tuple
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
                None, None,  # dividend fields
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
                last_certificate_id = certificate_id
                status_text.value = f"✅ บันทึกข้อมูลเรียบร้อยแล้ว (ID: {certificate_id})"
                status_text.color = ft.colors.GREEN_700
                generate_jpg_button.disabled = False
                page.update()
            else:
                status_text.value = "❌ ไม่สามารถบันทึกข้อมูลได้"
                status_text.color = ft.colors.RED_700
                
        except Exception as ex:
            status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
            status_text.color = ft.colors.RED_700
        
        page.update()
    
    def generate_jpg_image(e):
        """Generate JPG image from form data"""
        nonlocal last_certificate_id
        
        if not last_certificate_id:
            status_text.value = "❌ กรุณาบันทึกข้อมูลก่อนสร้าง JPG"
            status_text.color = ft.colors.RED_700
            page.update()
            return
        
        try:
            cert_data = app.get_certificate_by_id(last_certificate_id)
            if cert_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                jpg_filename = f"tax_form_filled_{last_certificate_id}_{timestamp}.jpg"
                success, message = app.fill_form_image(cert_data, jpg_filename)
                
                if success:
                    status_text.value = f"✅ {message}"
                    status_text.color = ft.colors.GREEN_700
                    
                    # Show success dialog with image info
                    def close_dialog(e):
                        dialog.open = False
                        page.update()
                    
                    dialog = ft.AlertDialog(
                        title=ft.Text("สร้างไฟล์ JPG สำเร็จ! 🖼️", color=ft.colors.GREEN_700, size=18),
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.IMAGE, size=40, color=ft.colors.BLUE_700),
                                    ft.Column([
                                        ft.Text("ไฟล์ JPG ใบรับรองการหักภาษี ณ ที่จ่าย ถูกสร้างเรียบร้อยแล้ว!", weight=ft.FontWeight.BOLD),
                                        ft.Text("ใช้ภาพพื้นหลังต้นฉบับของกรมสรรพากรเป็นฐาน", color=ft.colors.BLUE_700)
                                    ], spacing=5)
                                ], spacing=10),
                                ft.Divider(),
                                ft.Column([
                                    ft.Row([ft.Icon(ft.icons.FOLDER, size=16, color=ft.colors.BLUE_700), 
                                           ft.Text(f"ชื่อไฟล์: {jpg_filename}", size=12, weight=ft.FontWeight.BOLD)]),
                                    ft.Row([ft.Icon(ft.icons.LOCATION_ON, size=16, color=ft.colors.BLUE_700), 
                                           ft.Text(f"ตำแหน่ง: {os.path.abspath(jpg_filename)}", size=12)]),
                                    ft.Row([ft.Icon(ft.icons.FINGERPRINT, size=16, color=ft.colors.BLUE_700), 
                                           ft.Text(f"ID ใบรับรอง: {last_certificate_id}", size=12)]),
                                    ft.Row([ft.Icon(ft.icons.HIGH_QUALITY, size=16, color=ft.colors.BLUE_700), 
                                           ft.Text("คุณภาพ: High Resolution (3x zoom)", size=12)]),
                                ], spacing=8),
                                ft.Divider(),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("🎨 คุณสมบัติของไฟล์ JPG:", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700),
                                        ft.Text("• ใช้ภาพพื้นหลังต้นฉบับของกรมสรรพากร", size=12),
                                        ft.Text("• ข้อมูลวางในตำแหน่งที่แม่นยำ", size=12),
                                        ft.Text("• คุณภาพสูงเหมาะสำหรับการพิมพ์", size=12),
                                        ft.Text("• เครื่องหมายถูกในช่องที่เลือกอัตโนมัติ", size=12),
                                        ft.Text("• รองรับฟอนต์ไทยเพื่อความสวยงาม", size=12),
                                        ft.Text("• ใช้เป็นเอกสารราชการได้ทันที", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.colors.GREEN_50,
                                    padding=15,
                                    border_radius=10
                                )
                            ], spacing=15),
                            width=600
                        ),
                        actions=[
                            ft.TextButton("🎉 เยี่ยมมาก!", on_click=close_dialog,
                                        style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE))
                        ]
                    )
                    page.dialog = dialog
                    dialog.open = True
                    
                else:
                    status_text.value = f"❌ {message}"
                    status_text.color = ft.colors.RED_700
            else:
                status_text.value = f"❌ ไม่พบข้อมูลใบรับรอง ID: {last_certificate_id}"
                status_text.color = ft.colors.RED_700
                
        except Exception as ex:
            status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
            status_text.color = ft.colors.RED_700
        
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
        certificates = app.get_all_certificates()
        
        if not certificates:
            status_text.value = "ไม่มีข้อมูลหนังสือรับรองในฐานข้อมูล"
            status_text.color = ft.colors.ORANGE_700
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
                cert_data = app.get_certificate_by_id(certificate_id)
                if cert_data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    jpg_filename = f"tax_form_image_{certificate_id}_{timestamp}.jpg"
                    success, message = app.fill_form_image(cert_data, jpg_filename)
                    
                    if success:
                        status_text.value = f"✅ สร้าง JPG เรียบร้อย: {jpg_filename}"
                        status_text.color = ft.colors.GREEN_700
                    else:
                        status_text.value = f"❌ {message}"
                        status_text.color = ft.colors.RED_700
                else:
                    status_text.value = f"❌ ไม่พบข้อมูลใบรับรอง ID: {certificate_id}"
                    status_text.color = ft.colors.RED_700
            except Exception as ex:
                status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
                status_text.color = ft.colors.RED_700
            
            dialog.open = False
            page.update()
        
        rows = []
        for cert in certificates:
            jpg_button = ft.IconButton(
                icon=ft.icons.IMAGE,
                tooltip="สร้าง JPG",
                icon_color=ft.colors.BLUE_700,
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
                    ft.Text("🖼️ คลิกปุ่มสีฟ้าเพื่อสร้างไฟล์ JPG จากภาพพื้นหลังต้นฉบับ", size=12, color=ft.colors.BLUE_700),
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
        style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
        disabled=True,
        tooltip="บันทึกข้อมูลก่อนเพื่อสร้างไฟล์ JPG"
    )
    
    # Build the UI
    page.add(
        ft.Container(
            content=ft.Column([
                # Header with image info
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.IMAGE, size=40, color=ft.colors.BLUE_700),
                            ft.Column([
                                ft.Text("ระบบสร้าง JPG จากแบบฟอร์มภาษี", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Thai Tax Form JPG Generator - ใช้ภาพพื้นหลังต้นฉบับของกรมสรรพากร", size=14, color=ft.colors.GREY_700),
                                template_status
                            ], spacing=2)
                        ]),
                        ft.Divider(height=1, color=ft.colors.GREY_300),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.HIGH_QUALITY, size=16, color=ft.colors.BLUE_700),
                                    ft.Text("คุณสมบัติพิเศษ: สร้างไฟล์ JPG คุณภาพสูงจากภาพพื้นหลังต้นฉบับ", 
                                           size=12, color=ft.colors.BLUE_700, weight=ft.FontWeight.BOLD)
                                ], spacing=5),
                                ft.Row([
                                    ft.Icon(ft.icons.VERIFIED, size=16, color=ft.colors.GREEN_700),
                                    ft.Text("• ใช้ภาพต้นฉบับ • วางข้อมูลแม่นยำ • คุณภาพ High-Res • เครื่องหมายถูกอัตโนมัติ • ใช้งานราชการได้", 
                                           size=11, color=ft.colors.GREEN_700)
                                ], spacing=5)
                            ], spacing=5),
                            bgcolor=ft.colors.BLUE_50,
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
                    ft.ElevatedButton("💾 บันทึกข้อมูل", on_click=save_form, 
                                    style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)),
                    generate_jpg_button,
                    ft.ElevatedButton("🗑️ เคลียร์ฟอร์ม", on_click=clear_form,
                                    style=ft.ButtonStyle(bgcolor=ft.colors.ORANGE_700, color=ft.colors.WHITE)),
                    ft.ElevatedButton("📋 ดูรายการและสร้าง JPG", on_click=view_certificates,
                                    style=ft.ButtonStyle(bgcolor=ft.colors.PURPLE_700, color=ft.colors.WHITE))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True),
                
                status_text,
                ft.Divider(),
                
                # Form sections (condensed for space)
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
                                ft.Rowimport flet as ft
import psycopg2
import pandas as pd
from datetime import datetime
import os
from decimal import Decimal
import json
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF for PDF to image conversion
import io
import tempfile

class ImageFormFiller:
    def __init__(self):
        self.connection_string = "postgresql://neondb_owner:npg_BidDY7RA4zWX@ep-long-haze-a17mcg70-pooler.ap-southeast-1.aws.neon.tech/program_tax?sslmode=require&channel_binding=require"
        self.template_pdf_path = "tax_form_template.pdf"
        self.template_image_path = "tax_form_background.jpg"
        self.init_database()
        self.setup_fonts()
        self.convert_pdf_to_image()
        
    def setup_fonts(self):
        """Setup Thai fonts for image generation"""
        try:
            # Try to load Thai font
            if os.path.exists('THSarabunNew.ttf'):
                self.thai_font_path = 'THSarabunNew.ttf'
            else:
                # Try system fonts or create fallback
                self.thai_font_path = None
                print("Thai font not found. Using default font.")
        except:
            self.thai_font_path = None
    
    def get_font(self, size=12, bold=False):
        """Get font object for PIL drawing"""
        try:
            if self.thai_font_path:
                if bold:
                    # For bold, we'll use regular font and draw text multiple times for thickness
                    return ImageFont.truetype(self.thai_font_path, size)
                else:
                    return ImageFont.truetype(self.thai_font_path, size)
            else:
                # Fallback to default font
                return ImageFont.load_default()
        except:
            return ImageFont.load_default()
    
    def convert_pdf_to_image(self):
        """Convert PDF template to high-resolution image background"""
        try:
            if os.path.exists(self.template_pdf_path) and not os.path.exists(self.template_image_path):
                print("Converting PDF template to image...")
                
                # Open PDF and convert first page to image
                pdf_document = fitz.open(self.template_pdf_path)
                page = pdf_document[0]
                
                # Render page as image with high DPI for quality
                mat = fitz.Matrix(3.0, 3.0)  # 3x zoom for high resolution
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("ppm")
                background_image = Image.open(io.BytesIO(img_data))
                
                # Convert to RGB if necessary and save as JPG
                if background_image.mode != 'RGB':
                    background_image = background_image.convert('RGB')
                
                background_image.save(self.template_image_path, "JPEG", quality=95)
                pdf_document.close()
                
                print(f"Template converted to: {self.template_image_path}")
                return True
                
            elif os.path.exists(self.template_image_path):
                print(f"Using existing background image: {self.template_image_path}")
                return True
            else:
                print("No template found. Will create blank background.")
                return False
                
        except Exception as e:
            print(f"PDF conversion error: {e}")
            return False
    
    def create_blank_background(self, width=2480, height=3508):
        """Create blank A4 background if no template available"""
        background = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(background)
        
        # Draw basic form structure
        font = self.get_font(48, bold=True)
        title = "หนังสือรับรองการหักภาษี ณ ที่จ่าย ตามมาตรา 50 ทวิ แห่งประมวลรัษฎากร"
        
        # Calculate text position for center alignment
        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        
        draw.text((x, 100), title, fill='black', font=font)
        
        # Draw form sections
        draw.rectangle([100, 200, width-100, 400], outline='black', width=3)
        draw.rectangle([100, 450, width-100, 650], outline='black', width=3)
        draw.rectangle([100, 700, width-100, 2800], outline='black', width=3)
        
        return background
    
    def fill_form_image(self, data, output_path):
        """Fill form data onto background image and save as JPG"""
        try:
            # Load background image or create blank
            if os.path.exists(self.template_image_path):
                background = Image.open(self.template_image_path)
                print(f"Using background image: {self.template_image_path}")
            else:
                background = self.create_blank_background()
                print("Using blank background")
            
            # Convert to RGB if not already
            if background.mode != 'RGB':
                background = background.convert('RGB')
            
            # Create drawing context
            draw = ImageDraw.Draw(background)
            
            # Define precise coordinates for text placement (adjust based on your form)
            # These coordinates are scaled for high-resolution image
            positions = self.get_text_positions(background.size)
            
            # Fill in all the data
            self.draw_form_data(draw, data, positions)
            
            # Draw checkboxes
            self.draw_checkboxes(draw, data, positions)
            
            # Save as high-quality JPG
            background.save(output_path, "JPEG", quality=95, optimize=True)
            
            return True, f"ไฟล์ JPG ถูกสร้างเรียบร้อยแล้ว: {output_path}"
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาดในการสร้าง JPG: {str(e)}"
    
    def get_text_positions(self, image_size):
        """Get text positions scaled to image size"""
        width, height = image_size
        
        # Scale positions based on image size (assuming A4 proportions)
        scale_x = width / 2480  # Base width
        scale_y = height / 3508  # Base height
        
        return {
            # Withholder section (scaled coordinates)
            'withholder_name': (int(400 * scale_x), int(420 * scale_y)),
            'withholder_address': (int(400 * scale_x), int(480 * scale_y)),
            'withholder_tax_id': (int(520 * scale_x), int(390 * scale_y)),
            'withholder_type': (int(1800 * scale_x), int(420 * scale_y)),
            
            # Document reference
            'book_no': (int(320 * scale_x), int(320 * scale_y)),
            'cert_no': (int(500 * scale_x), int(320 * scale_y)),
            
            # Withholdee section
            'withholdee_name': (int(400 * scale_x), int(630 * scale_y)),
            'withholdee_address': (int(400 * scale_x), int(690 * scale_y)),
            'withholdee_tax_id': (int(520 * scale_x), int(600 * scale_y)),
            'withholdee_type': (int(1800 * scale_x), int(630 * scale_y)),
            
            # Form reference
            'sequence_form': (int(250 * scale_x), int(780 * scale_y)),
            'form_type_pos': (int(400 * scale_x), int(780 * scale_y)),
            
            # Income table (6 rows)
            'income_1_amount': (int(1400 * scale_x), int(950 * scale_y)),
            'income_1_tax': (int(1800 * scale_x), int(950 * scale_y)),
            'income_2_amount': (int(1400 * scale_x), int(1020 * scale_y)),
            'income_2_tax': (int(1800 * scale_x), int(1020 * scale_y)),
            'income_3_amount': (int(1400 * scale_x), int(1090 * scale_y)),
            'income_3_tax': (int(1800 * scale_x), int(1090 * scale_y)),
            'income_4a_amount': (int(1400 * scale_x), int(1160 * scale_y)),
            'income_4a_tax': (int(1800 * scale_x), int(1160 * scale_y)),
            'income_4b_amount': (int(1400 * scale_x), int(1230 * scale_y)),
            'income_4b_tax': (int(1800 * scale_x), int(1230 * scale_y)),
            'income_5_amount': (int(1400 * scale_x), int(1800 * scale_y)),
            'income_5_tax': (int(1800 * scale_x), int(1800 * scale_y)),
            'income_6_amount': (int(1400 * scale_x), int(1900 * scale_y)),
            'income_6_tax': (int(1800 * scale_x), int(1900 * scale_y)),
            'income_6_desc': (int(400 * scale_x), int(1950 * scale_y)),
            
            # Totals
            'total_income': (int(1400 * scale_x), int(2050 * scale_y)),
            'total_tax': (int(1800 * scale_x), int(2050 * scale_y)),
            'total_tax_text': (int(400 * scale_x), int(2120 * scale_y)),
            
            # Funds
            'provident_fund': (int(650 * scale_x), int(2250 * scale_y)),
            'social_security': (int(1100 * scale_x), int(2250 * scale_y)),
            'retirement_fund': (int(1550 * scale_x), int(2250 * scale_y)),
            
            # Signature section
            'issue_type_pos': (int(400 * scale_x), int(2350 * scale_y)),
            'signatory': (int(600 * scale_x), int(2450 * scale_y)),
            'issue_date': (int(1200 * scale_x), int(2450 * scale_y)),
            
            # Checkbox positions for form types
            'checkbox_1ก': (int(350 * scale_x), int(780 * scale_y)),
            'checkbox_1ก_special': (int(450 * scale_x), int(780 * scale_y)),
            'checkbox_2': (int(550 * scale_x), int(780 * scale_y)),
            'checkbox_3': (int(650 * scale_x), int(780 * scale_y)),
            'checkbox_2ก': (int(350 * scale_x), int(810 * scale_y)),
            'checkbox_3ก': (int(450 * scale_x), int(810 * scale_y)),
            'checkbox_53': (int(550 * scale_x), int(810 * scale_y)),
            
            # Issue type checkboxes
            'checkbox_withhold': (int(350 * scale_x), int(2350 * scale_y)),
            'checkbox_permanent': (int(500 * scale_x), int(2350 * scale_y)),
            'checkbox_once': (int(650 * scale_x), int(2350 * scale_y)),
            'checkbox_other': (int(800 * scale_x), int(2350 * scale_y)),
        }
    
    def draw_form_data(self, draw, data, positions):
        """Draw all form data on the image"""
        # Regular font for most text
        font_regular = self.get_font(30)  # Larger font for high-res image
        font_small = self.get_font(24)
        font_bold = self.get_font(32, bold=True)
        
        # Helper function to draw text safely
        def draw_text_safe(pos_key, text, font=font_regular, fill='black'):
            if pos_key in positions and text:
                pos = positions[pos_key]
                # For bold effect, draw text multiple times slightly offset
                if font == font_bold:
                    for offset in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                        draw.text((pos[0] + offset[0], pos[1] + offset[1]), str(text), fill=fill, font=font)
                else:
                    draw.text(pos, str(text), fill=fill, font=font)
        
        # Draw all form fields
        draw_text_safe('withholder_name', data.get('withholder_name', ''), font_bold)
        draw_text_safe('withholder_address', data.get('withholder_address', ''), font_regular)
        draw_text_safe('withholder_tax_id', data.get('withholder_tax_id', ''), font_regular)
        draw_text_safe('withholder_type', data.get('withholder_type', ''), font_small)
        
        draw_text_safe('book_no', data.get('certificate_book_no', ''), font_regular)
        draw_text_safe('cert_no', data.get('certificate_no', ''), font_regular)
        
        draw_text_safe('withholdee_name', data.get('withholdee_name', ''), font_bold)
        draw_text_safe('withholdee_address', data.get('withholdee_address', ''), font_regular)
        draw_text_safe('withholdee_tax_id', data.get('withholdee_tax_id', ''), font_regular)
        draw_text_safe('withholdee_type', data.get('withholdee_type', ''), font_small)
        
        draw_text_safe('sequence_form', data.get('sequence_in_form', ''), font_regular)
        
        # Income amounts and taxes
        if float(data.get('income_type_1_amount', 0)) > 0:
            draw_text_safe('income_1_amount', f"{float(data.get('income_type_1_amount', 0)):,.2f}", font_regular)
            draw_text_safe('income_1_tax', f"{float(data.get('income_type_1_tax', 0)):,.2f}", font_regular)
        
        if float(data.get('income_type_2_amount', 0)) > 0:
            draw_text_safe('income_2_amount', f"{float(data.get('income_type_2_amount', 0)):,.2f}", font_regular)
            draw_text_safe('income_2_tax', f"{float(data.get('income_type_2_tax', 0)):,.2f}", font_regular)
        
        if float(data.get('income_type_3_amount', 0)) > 0:
            draw_text_safe('income_3_amount', f"{float(data.get('income_type_3_amount', 0)):,.2f}", font_regular)
            draw_text_safe('income_3_tax', f"{float(data.get('income_type_3_tax', 0)):,.2f}", font_regular)
        
        if float(data.get('income_type_4a_amount', 0)) > 0:
            draw_text_safe('income_4a_amount', f"{float(data.get('income_type_4a_amount', 0)):,.2f}", font_regular)
            draw_text_safe('income_4a_tax', f"{float(data.get('income_type_4a_tax', 0)):,.2f}", font_regular)
        
        if float(data.get('income_type_4b_amount', 0)) > 0:
            draw_text_safe('income_4b_amount', f"{float(data.get('income_type_4b_amount', 0)):,.2f}", font_regular)
            draw_text_safe('income_4b_tax', f"{float(data.get('income_type_4b_tax', 0)):,.2f}", font_regular)
        
        if float(data.get('income_type_5_amount', 0)) > 0:
            draw_text_safe('income_5_amount', f"{float(data.get('income_type_5_amount', 0)):,.2f}", font_regular)
            draw_text_safe('income_5_tax', f"{float(data.get('income_type_5_tax', 0)):,.2f}", font_regular)
        
        if float(data.get('income_type_6_amount', 0)) > 0:
            draw_text_safe('income_6_amount', f"{float(data.get('income_type_6_amount', 0)):,.2f}", font_regular)
            draw_text_safe('income_6_tax', f"{float(data.get('income_type_6_tax', 0)):,.2f}", font_regular)
            draw_text_safe('income_6_desc', data.get('income_type_6_description', ''), font_small)
        
        # Totals
        draw_text_safe('total_income', f"{float(data.get('total_income', 0)):,.2f}", font_bold)
        draw_text_safe('total_tax', f"{float(data.get('total_tax_withheld', 0)):,.2f}", font_bold)
        draw_text_safe('total_tax_text', data.get('total_tax_withheld_text', ''), font_regular)
        
        # Funds
        if float(data.get('provident_fund', 0)) > 0:
            draw_text_safe('provident_fund', f"{float(data.get('provident_fund', 0)):,.2f}", font_regular)
        if float(data.get('social_security_fund', 0)) > 0:
            draw_text_safe('social_security', f"{float(data.get('social_security_fund', 0)):,.2f}", font_regular)
        if float(data.get('retirement_mutual_fund', 0)) > 0:
            draw_text_safe('retirement_fund', f"{float(data.get('retirement_mutual_fund', 0)):,.2f}", font_regular)
        
        # Signature
        draw_text_safe('signatory', data.get('signatory_name', ''), font_regular)
        draw_text_safe('issue_date', data.get('issue_date', ''), font_regular)
    
    def draw_checkboxes(self, draw, data, positions):
        """Draw checkboxes and check marks"""
        checkbox_size = 25  # Size for high-res image
        
        def draw_checkbox(pos_key, is_checked=False):
            if pos_key in positions:
                pos = positions[pos_key]
                # Draw checkbox square
                draw.rectangle([pos[0], pos[1], pos[0] + checkbox_size, pos[1] + checkbox_size], 
                             outline='black', width=2)
                
                # Draw check mark if checked
                if is_checked:
                    # Draw X mark
                    draw.line([pos[0] + 5, pos[1] + 5, pos[0] + checkbox_size - 5, pos[1] + checkbox_size - 5], 
                             fill='black', width=3)
                    draw.line([pos[0] + checkbox_size - 5, pos[1] + 5, pos[0] + 5, pos[1] + checkbox_size - 5], 
                             fill='black', width=3)
        
        # Form type checkboxes
        form_type = data.get('form_type', '')
        draw_checkbox('checkbox_1ก', form_type == 'ภ.ง.ด.1ก')
        draw_checkbox('checkbox_1ก_special', form_type == 'ภ.ง.ด.1ก พิเศษ')
        draw_checkbox('checkbox_2', form_type == 'ภ.ง.ด.2')
        draw_checkbox('checkbox_3', form_type == 'ภ.ง.ด.3')
        draw_checkbox('checkbox_2ก', form_type == 'ภ.ง.ด.2ก')
        draw_checkbox('checkbox_3ก', form_type == 'ภ.ง.ด.3ก')
        draw_checkbox('checkbox_53', form_type == 'ภ.ง.ด.53')
        
        # Issue type checkboxes
        issue_type = data.get('issue_type', '')
        draw_checkbox('checkbox_withhold', issue_type == 'หักณที่จ่าย')
        draw_checkbox('checkbox_permanent', issue_type == 'ออกให้ตลอดไป')
        draw_checkbox('checkbox_once', issue_type == 'ออกให้ครั้งเดียว')
        draw_checkbox('checkbox_other', issue_type == 'อื่น ๆ')
    
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

def main(page: ft.Page):
    page.title = "ระบบสร้าง JPG จากแบบฟอร์มภาษี - Image Background"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    page.window_resizable = True
    page.scroll = ft.ScrollMode.AUTO
    
    app = ImageFormFiller()
    
    # Status messages
    status_text = ft.Text("พร้อมใช้งาน", size=14, color=ft.colors.GREEN_700)
    
    # Template status
    template_status = ft.Text("กำลังตรวจสอบเทมเพลต...", size=12)
    
    def check_template():
        if os.path.exists(app.template_image_path):
            template_status.value = f"✅ พบภาพพื้นหลัง: {app.template_image_path}"
            template_status.color = ft.colors.GREEN_700
        elif os.path.exists(app.template_pdf_path):
            template_status.value = f"🔄 พบ PDF เทมเพลต: {app.template_pdf_path} (จะแปลงเป็นภาพ)"
            template_status.color = ft.colors.BLUE_700
        else:
            template_status.value = f"⚠️ ไม่พบเทมเพลต (จะสร้างพื้นหลังขาว)"
            template_status.color = ft.colors.ORANGE_700
        page.update()
    
    check_template()
    
    # Form fields (abbreviated for space)
    withholder_name = ft.TextField(label="ชื่อผู้มีหน้าที่หักภาษี", width=400)
    withholder_address = ft.TextField(label="ที่อยู่ผู้มี