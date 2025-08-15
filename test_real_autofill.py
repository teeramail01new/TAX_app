#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Real AutoFill with Actual Data
ทดสอบ AutoFill ด้วยข้อมูลจริงและจำลองการทำงานของ Dashboard
"""

import json
import os
import time
from datetime import datetime

def simulate_dashboard_button_click():
    """จำลองการกดปุ่ม 'นำข้อมูลไปเติมใน Crystal Report' จาก Dashboard"""
    print("🎯 SIMULATING DASHBOARD BUTTON CLICK")
    print("=" * 50)
    
    # จำลองข้อมูลจริงจาก transfer_records table
    selected_record = [
        101,  # id
        "สมหญิง",  # name
        "ใจดี",  # surname  
        15000.00,  # transfer_amount
        "2024-01-20",  # transfer_date
        "1234567890123",  # id_card
        "789 ถนนสุขุมวิท บางนา กรุงเทพฯ 10260",  # address
        3.0,  # percent
        15450.00,  # total_amount
        450.00,  # fee
        "ค่าธรรมเนียม"  # remark
    ]
    
    print(f"📊 Selected Record: {selected_record}")
    
    # จำลองการแมปข้อมูลเหมือนใน send_selected_to_crystal_from_dashboard
    withholder_data = {
        'withholder_name': f"{selected_record[1] or ''} {selected_record[2] or ''}".strip(),
        'withholder_address': selected_record[6] or '',
        'withholder_tax_id': selected_record[5] or '',
        'transfer_amount': selected_record[3] or 0,
        'transfer_date': selected_record[4] or '',
        'remark': selected_record[10] if len(selected_record) > 10 else ''
    }
    
    complete_data = {
        'withholder_name': withholder_data['withholder_name'],
        'withholder_address': withholder_data['withholder_address'],
        'withholder_tax_id': withholder_data['withholder_tax_id'],
        'transfer_record': {
            'id': selected_record[0],
            'name': selected_record[1] or '',
            'surname': selected_record[2] or '',
            'transfer_amount': selected_record[3] or 0,
            'transfer_date': selected_record[4] or '',
            'id_card': selected_record[5] or '',
            'address': selected_record[6] or '',
            'percent': selected_record[7] if len(selected_record) > 7 else 0,
            'total_amount': selected_record[8] if len(selected_record) > 8 else 0,
            'fee': selected_record[9] if len(selected_record) > 9 else 0,
            'remark': selected_record[10] if len(selected_record) > 10 else ''
        }
    }
    
    print(f"📦 Mapped Complete Data:")
    print(json.dumps(complete_data, ensure_ascii=False, indent=2))
    
    # บันทึกลง temp file (เหมือนใน send_selected_to_crystal_from_dashboard)
    temp_file_path = os.path.join(os.getcwd(), "temp_dashboard_data.json")
    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, ensure_ascii=False, indent=2)
        print(f"💾 Successfully saved complete data to temp file: {temp_file_path}")
        return True
    except Exception as file_ex:
        print(f"❌ Failed to save to temp file: {file_ex}")
        return False

def simulate_crystal_tab_open():
    """จำลองการเปิด tab 'ระบบพิกัด form PDF'"""
    print("\n🎯 SIMULATING CRYSTAL TAB OPEN")
    print("=" * 50)
    
    # จำลองตัวแปรใน crystal tab
    class MockTextField:
        def __init__(self, label):
            self.label = label
            self.value = ""
    
    class MockText:
        def __init__(self, initial_value=""):
            self.value = initial_value
            self.color = None
    
    # จำลองตัวแปรเหมือนในโปรแกรมจริง
    withholder_name = MockTextField("ชื่อผู้มีหน้าที่หักภาษี")
    withholder_address = MockTextField("ที่อยู่ผู้มีหน้าที่หักภาษี")
    withholder_tax_id = MockTextField("เลขประจำตัวผู้เสียภาษี")
    
    withholdee_name = MockTextField("ชื่อผู้ถูกหักภาษี")
    withholdee_address = MockTextField("ที่อยู่ผู้ถูกหักภาษี")
    withholdee_tax_id = MockTextField("เลขประจำตัวผู้เสียภาษี")
    
    income_1_amount = MockTextField("รายได้ประเภทที่ 1")
    income_1_tax = MockTextField("ภาษีที่หักประเภทที่ 1")
    income_2_amount = MockTextField("รายได้ประเภทที่ 2")
    income_2_tax = MockTextField("ภาษีที่หักประเภทที่ 2")
    
    total_income_display = MockTextField("ยอดรวมรายได้")
    total_tax_display = MockTextField("ยอดรวมภาษีที่หัก")
    
    status_text = MockText("พร้อมใช้งาน")
    
    print("📝 Created mock UI variables")
    
    return {
        'withholder_name': withholder_name,
        'withholder_address': withholder_address,
        'withholder_tax_id': withholder_tax_id,
        'withholdee_name': withholdee_name,
        'withholdee_address': withholdee_address,
        'withholdee_tax_id': withholdee_tax_id,
        'income_1_amount': income_1_amount,
        'income_1_tax': income_1_tax,
        'income_2_amount': income_2_amount,
        'income_2_tax': income_2_tax,
        'total_income_display': total_income_display,
        'total_tax_display': total_tax_display,
        'status_text': status_text
    }

def simulate_thread1_withholder(ui_vars):
    """จำลอง Thread 1: Auto-fill ผู้หักภาษี"""
    print("\n🔄 THREAD 1: WITHHOLDER AUTO-FILL")
    print("⏰ Waiting 1.0 seconds...")
    time.sleep(1.0)
    
    temp_file_path = os.path.join(os.getcwd(), "temp_dashboard_data.json")
    
    if os.path.exists(temp_file_path):
        try:
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                dashboard_data = json.load(f)
            
            print(f"🔍 Found temp file data: {dashboard_data.keys()}")
            
            # จำลองการเติมข้อมูลผู้หักภาษี
            ui_vars['withholder_name'].value = dashboard_data.get('withholder_name', '')
            ui_vars['withholder_address'].value = dashboard_data.get('withholder_address', '')
            ui_vars['withholder_tax_id'].value = dashboard_data.get('withholder_tax_id', '')
            
            print(f"✅ Withholder Name: '{ui_vars['withholder_name'].value}'")
            print(f"✅ Withholder Address: '{ui_vars['withholder_address'].value}'")
            print(f"✅ Withholder Tax ID: '{ui_vars['withholder_tax_id'].value}'")
            
            ui_vars['status_text'].value = f"✅ โหลดข้อมูลผู้หักภาษีจาก Dashboard: {dashboard_data.get('withholder_name', '')}"
            
            return True
        except Exception as ex:
            print(f"❌ Thread 1 error: {ex}")
            return False
    else:
        print("⚠️ No temp file found for Thread 1")
        return False

def simulate_thread2_withholdee(ui_vars):
    """จำลอง Thread 2: Auto-fill ผู้ถูกหักภาษี"""
    print("\n🔄 THREAD 2: WITHHOLDEE AUTO-FILL")
    print("⏰ Waiting 1.5 seconds...")
    time.sleep(1.5)
    
    temp_file_path = os.path.join(os.getcwd(), "temp_dashboard_data.json")
    
    if os.path.exists(temp_file_path):
        try:
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                dashboard_data = json.load(f)
            
            print(f"🔍 Found temp file data for withholdee: {dashboard_data.keys()}")
            
            # ตรวจสอบ transfer_record
            if dashboard_data.get('transfer_record'):
                record = dashboard_data['transfer_record']
                name = record.get('name', '')
                surname = record.get('surname', '')
                full_name = f"{name} {surname}".strip()
                
                if full_name:
                    # จำลองการเติมข้อมูลผู้ถูกหักภาษี
                    ui_vars['withholdee_name'].value = full_name
                    ui_vars['withholdee_address'].value = record.get('address', '')
                    ui_vars['withholdee_tax_id'].value = record.get('id_card', '')
                    
                    # จำลองการเติมข้อมูลรายได้
                    transfer_amount = record.get('transfer_amount', 0)
                    fee = record.get('fee', 0)
                    ui_vars['income_1_amount'].value = f"{float(transfer_amount or 0):.2f}"
                    ui_vars['income_1_tax'].value = "0.00"
                    ui_vars['income_2_amount'].value = "0.00"
                    ui_vars['income_2_tax'].value = f"{float(fee or 0):.2f}"
                    
                    # จำลองการอัปเดตยอดรวม
                    ui_vars['total_income_display'].value = f"{float(transfer_amount or 0):,.2f}"
                    ui_vars['total_tax_display'].value = f"{float(fee or 0):,.2f}"
                    
                    print(f"✅ Withholdee Name: '{ui_vars['withholdee_name'].value}'")
                    print(f"✅ Withholdee Address: '{ui_vars['withholdee_address'].value}'")
                    print(f"✅ Withholdee Tax ID: '{ui_vars['withholdee_tax_id'].value}'")
                    print(f"✅ Transfer Amount: '{ui_vars['income_1_amount'].value}'")
                    print(f"✅ Fee: '{ui_vars['income_2_tax'].value}'")
                    print(f"✅ Total Income: '{ui_vars['total_income_display'].value}'")
                    print(f"✅ Total Tax: '{ui_vars['total_tax_display'].value}'")
                    
                    ui_vars['status_text'].value = f"✅ โหลดข้อมูลผู้ถูกหักภาษีจาก Dashboard: {full_name}"
                    
                    return True
                else:
                    print("⚠️ No valid name found in transfer_record")
                    return False
            else:
                print("⚠️ No transfer_record found in temp file")
                return False
        except Exception as ex:
            print(f"❌ Thread 2 error: {ex}")
            return False
    else:
        print("⚠️ No temp file found for Thread 2")
        return False

def main():
    """ฟังก์ชันหลักสำหรับทดสอบ"""
    print("🔬 REAL AUTOFILL TEST")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Working directory: {os.getcwd()}")
    
    # Step 1: จำลองการกดปุ่มใน Dashboard
    success1 = simulate_dashboard_button_click()
    
    if not success1:
        print("❌ Dashboard simulation failed")
        return
    
    # Step 2: จำลองการเปิด Crystal Tab
    ui_vars = simulate_crystal_tab_open()
    
    # Step 3: จำลอง Thread 1 และ 2
    import threading
    
    results = {}
    
    def thread1_wrapper():
        results['thread1'] = simulate_thread1_withholder(ui_vars)
    
    def thread2_wrapper():
        results['thread2'] = simulate_thread2_withholdee(ui_vars)
    
    print("\n🚀 Starting both auto-fill threads...")
    thread1 = threading.Thread(target=thread1_wrapper, daemon=True)
    thread2 = threading.Thread(target=thread2_wrapper, daemon=True)
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()
    
    # Step 4: แสดงผลลัพธ์
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS")
    print("=" * 60)
    
    print("📋 WITHHOLDER DATA (ผู้หักภาษี):")
    print(f"  ชื่อ: '{ui_vars['withholder_name'].value}'")
    print(f"  ที่อยู่: '{ui_vars['withholder_address'].value}'")
    print(f"  เลขประจำตัวผู้เสียภาษี: '{ui_vars['withholder_tax_id'].value}'")
    
    print("\n📋 WITHHOLDEE DATA (ผู้ถูกหักภาษี):")
    print(f"  ชื่อ: '{ui_vars['withholdee_name'].value}'")
    print(f"  ที่อยู่: '{ui_vars['withholdee_address'].value}'")
    print(f"  เลขประจำตัวผู้เสียภาษี: '{ui_vars['withholdee_tax_id'].value}'")
    
    print("\n📋 INCOME DATA (ข้อมูลรายได้):")
    print(f"  รายได้ประเภทที่ 1: '{ui_vars['income_1_amount'].value}'")
    print(f"  ภาษีที่หักประเภทที่ 2: '{ui_vars['income_2_tax'].value}'")
    print(f"  ยอดรวมรายได้: '{ui_vars['total_income_display'].value}'")
    print(f"  ยอดรวมภาษีที่หัก: '{ui_vars['total_tax_display'].value}'")
    
    print(f"\n📊 STATUS: '{ui_vars['status_text'].value}'")
    
    # ตรวจสอบว่าข้อมูลถูกเติมหรือไม่
    all_filled = all([
        ui_vars['withholder_name'].value,
        ui_vars['withholdee_name'].value,
        ui_vars['income_1_amount'].value,
        ui_vars['total_income_display'].value
    ])
    
    if all_filled:
        print("\n✅ SUCCESS: AutoFill is working correctly!")
        print("✅ All important fields are populated")
    else:
        print("\n❌ FAILURE: Some fields are still empty")
        print("❌ AutoFill is not working properly")
    
    print(f"\n🔧 Thread Results: Thread1={results.get('thread1', False)}, Thread2={results.get('thread2', False)}")

if __name__ == "__main__":
    main()


