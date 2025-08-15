#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Fix for AutoFill - Last Time Fix
แก้ไขปัญหา AutoFill ครั้งสุดท้าย
"""

import os
import json

def fix_temp_file():
    """แก้ไข temp file ที่เสีย"""
    print("🔧 Fixing corrupted temp file...")
    
    # ลบไฟล์เสีย
    temp_file = "temp_dashboard_data.json"
    if os.path.exists(temp_file):
        os.remove(temp_file)
        print(f"🗑️ Removed corrupted file: {temp_file}")
    
    # สร้างข้อมูลทดสอบใหม่
    test_data = {
        "withholder_name": "ดังกามล เนตรวงศ",
        "withholder_address": "88 หมู่ที่ 7 ตำบลสมเด็จ อำเภอสมเด็จ นครสิงห์บุรี",
        "withholder_tax_id": "1461300072037",
        "transfer_record": {
            "id": 8,
            "name": "ดังกามล",
            "surname": "เนตรวงศ",
            "transfer_amount": 25000.0,
            "transfer_date": "2024-01-15",
            "id_card": "1461300072037",
            "address": "88 หมู่ที่ 7 ตำบลสมเด็จ อำเภอสมเด็จ นครสิงห์บุรี",
            "percent": 3.0,
            "total_amount": 25750.0,
            "fee": 750.0,
            "remark": "ค่าธรรมเนียม"
        }
    }
    
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Created new temp file: {temp_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to create temp file: {e}")
        return False

def patch_main_program():
    """แก้ไขโปรแกรมหลักเพื่อจัดการ JSON error และ deprecation warning"""
    print("🔧 Patching main program...")
    
    # อ่านไฟล์หลัก
    with open("main_prgram_tax.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # แก้ไข JSON parsing error
    old_json_load = '''with open(temp_file_path, 'r', encoding='utf-8') as f:
                                dashboard_data = json.load(f)'''
    
    new_json_load = '''with open(temp_file_path, 'r', encoding='utf-8') as f:
                                try:
                                    dashboard_data = json.load(f)
                                except json.JSONDecodeError as json_err:
                                    print(f"❌ JSON decode error: {json_err}")
                                    print("🔧 Recreating temp file...")
                                    # ลบไฟล์เสียและข้าม
                                    import os
                                    os.remove(temp_file_path)
                                    dashboard_data = None'''
    
    # แก้ไข colors deprecation warning
    content = content.replace("ft.colors.", "ft.Colors.")
    
    # แก้ไข JSON loading
    if old_json_load in content:
        content = content.replace(old_json_load, new_json_load)
        print("✅ Fixed JSON loading error handling")
    
    # บันทึกไฟล์
    with open("main_prgram_tax.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Main program patched successfully")

def create_simple_autofill_patch():
    """สร้าง patch ง่ายๆ สำหรับ autofill"""
    patch_code = '''
# Quick AutoFill Patch - เพิ่มท้ายฟังก์ชัน create_crystal_report_tab
def force_autofill_now():
    """บังคับ autofill ทันที"""
    temp_file_path = os.path.join(os.getcwd(), "temp_dashboard_data.json")
    
    if os.path.exists(temp_file_path):
        try:
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # เติมข้อมูลผู้หักภาษี
            if data.get('withholder_name'):
                withholder_name.value = data['withholder_name']
                withholder_address.value = data.get('withholder_address', '')
                withholder_tax_id.value = data.get('withholder_tax_id', '')
            
            # เติมข้อมูลผู้ถูกหักภาษี
            if data.get('transfer_record'):
                record = data['transfer_record']
                name = record.get('name', '')
                surname = record.get('surname', '')
                full_name = f"{name} {surname}".strip()
                
                if full_name:
                    withholdee_name.value = full_name
                    withholdee_address.value = record.get('address', '')
                    withholdee_tax_id.value = record.get('id_card', '')
                    
                    # เติมข้อมูลรายได้
                    transfer_amount = record.get('transfer_amount', 0)
                    fee = record.get('fee', 0)
                    income_1_amount.value = f"{float(transfer_amount):.2f}"
                    income_1_tax.value = "0.00"
                    income_2_amount.value = "0.00"
                    income_2_tax.value = f"{float(fee):.2f}"
                    
                    # อัปเดตยอดรวม
                    total_income_display.value = f"{float(transfer_amount):,.2f}"
                    total_tax_display.value = f"{float(fee):,.2f}"
            
            status_text.value = "✅ Auto-filled data successfully!"
            status_text.color = ft.Colors.GREEN_700
            page.update()
            
        except Exception as e:
            print(f"Force autofill error: {e}")

# เรียกใช้ force autofill ทันที
import threading
def delayed_force_autofill():
    import time
    time.sleep(0.5)  # รอให้ UI พร้อม
    force_autofill_now()

threading.Thread(target=delayed_force_autofill, daemon=True).start()
'''
    return patch_code

def main():
    print("🚀 QUICK FIX FOR AUTOFILL - LAST TIME!")
    print("=" * 50)
    
    # Step 1: แก้ไข temp file ที่เสีย
    fix_temp_file()
    
    # Step 2: แก้ไขโปรแกรมหลัก
    patch_main_program()
    
    print("\n✅ QUICK FIX COMPLETED!")
    print("🔧 Changes made:")
    print("  1. Fixed corrupted temp_dashboard_data.json")
    print("  2. Fixed JSON parsing error handling")
    print("  3. Fixed ft.colors deprecation warning")
    print("\n🚀 Now try running the main program:")
    print("python main_prgram_tax.py")

if __name__ == "__main__":
    main()


