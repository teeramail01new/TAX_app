#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Main Program Issues
ตรวจสอบปัญหาในโปรแกรมหลัก main_prgram_tax.py
"""

import os
import json
import re
from datetime import datetime

def check_variable_definitions():
    """ตรวจสอบการประกาศตัวแปรที่จำเป็น"""
    print("=" * 60)
    print("🔍 Checking Variable Definitions in Main Program")
    print("=" * 60)
    
    main_file = "main_prgram_tax.py"
    if not os.path.exists(main_file):
        print(f"❌ Main file not found: {main_file}")
        return False
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ตรวจสอบการประกาศตัวแปรที่สำคัญ
    variables_to_check = [
        'withholder_name',
        'withholder_address', 
        'withholder_tax_id',
        'withholdee_name',
        'withholdee_address',
        'withholdee_tax_id',
        'income_1_amount',
        'income_2_tax',
        'total_income_display',
        'total_tax_display',
        'status_text'
    ]
    
    print("🔍 Searching for variable definitions...")
    for var in variables_to_check:
        # หาการประกาศตัวแปร ft.TextField
        pattern = rf'{var}\s*=\s*ft\.TextField'
        matches = re.findall(pattern, content)
        if matches:
            print(f"✅ {var}: Found {len(matches)} definition(s)")
        else:
            print(f"❌ {var}: NOT FOUND")
    
    return True

def check_thread_function_locations():
    """ตรวจสอบตำแหน่งของฟังก์ชัน thread"""
    print("\n" + "=" * 60)
    print("🔍 Checking Thread Function Locations")
    print("=" * 60)
    
    main_file = "main_prgram_tax.py"
    with open(main_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # หาฟังก์ชัน delayed_pending_auto_fill
    delayed_pending_found = False
    delayed_withholdee_found = False
    
    for i, line in enumerate(lines, 1):
        if 'def delayed_pending_auto_fill' in line:
            print(f"✅ delayed_pending_auto_fill found at line {i}")
            delayed_pending_found = True
        elif 'def delayed_withholdee_auto_fill' in line:
            print(f"✅ delayed_withholdee_auto_fill found at line {i}")
            delayed_withholdee_found = True
        elif 'delayed_pending_auto_fill()' in line and 'def' not in line:
            print(f"🔄 delayed_pending_auto_fill called at line {i}")
        elif 'delayed_withholdee_auto_fill()' in line and 'def' not in line:
            print(f"🔄 delayed_withholdee_auto_fill called at line {i}")
    
    if not delayed_pending_found:
        print("❌ delayed_pending_auto_fill function NOT FOUND")
    if not delayed_withholdee_found:
        print("❌ delayed_withholdee_auto_fill function NOT FOUND")
    
    return delayed_pending_found and delayed_withholdee_found

def check_crystal_report_tab_scope():
    """ตรวจสอบขอบเขตของตัวแปรใน create_crystal_report_tab"""
    print("\n" + "=" * 60)
    print("🔍 Checking Crystal Report Tab Variable Scope")
    print("=" * 60)
    
    main_file = "main_prgram_tax.py"
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # หาฟังก์ชัน create_crystal_report_tab
    crystal_tab_match = re.search(r'def create_crystal_report_tab\(\):(.*?)(?=\n    def|\nclass|\Z)', content, re.DOTALL)
    
    if not crystal_tab_match:
        print("❌ create_crystal_report_tab function NOT FOUND")
        return False
    
    crystal_tab_content = crystal_tab_match.group(1)
    
    # ตรวจสอบการประกาศตัวแปรใน crystal tab
    variables_to_check = [
        'withholder_name',
        'withholder_address', 
        'withholder_tax_id',
        'withholdee_name',
        'withholdee_address',
        'withholdee_tax_id'
    ]
    
    print("🔍 Checking variable declarations in create_crystal_report_tab...")
    for var in variables_to_check:
        if f'{var} = ft.TextField' in crystal_tab_content:
            print(f"✅ {var}: Properly declared in crystal tab")
        else:
            print(f"❌ {var}: NOT declared in crystal tab")
    
    # ตรวจสอบว่า delayed_withholdee_auto_fill สามารถเข้าถึงตัวแปรได้หรือไม่
    if 'delayed_withholdee_auto_fill' in crystal_tab_content:
        print("✅ delayed_withholdee_auto_fill is defined inside crystal tab (can access variables)")
    else:
        print("❌ delayed_withholdee_auto_fill is NOT defined inside crystal tab (cannot access variables)")
    
    return True

def create_simple_test_case():
    """สร้างกรณีทดสอบง่ายๆ"""
    print("\n" + "=" * 60)
    print("🧪 Creating Simple Test Case")
    print("=" * 60)
    
    # สร้างข้อมูลทดสอบจริงจาก Dashboard
    test_record = [
        123,  # id
        "ทดสอบ",  # name
        "ระบบ",  # surname
        5000.00,  # transfer_amount
        "2024-01-15",  # transfer_date
        "1234567890123",  # id_card
        "123 ถนนทดสอบ กรุงเทพฯ",  # address
        3.0,  # percent
        5150.00,  # total_amount
        150.00,  # fee
        "ค่าธรรมเนียม"  # remark
    ]
    
    # จำลองการทำงานของ send_selected_to_crystal_from_dashboard
    withholder_data = {
        'withholder_name': f"{test_record[1] or ''} {test_record[2] or ''}".strip(),
        'withholder_address': test_record[6] or '',
        'withholder_tax_id': test_record[5] or '',
        'transfer_amount': test_record[3] or 0,
        'transfer_date': test_record[4] or '',
        'remark': test_record[10] if len(test_record) > 10 else ''
    }
    
    complete_data = {
        'withholder_name': withholder_data['withholder_name'],
        'withholder_address': withholder_data['withholder_address'],
        'withholder_tax_id': withholder_data['withholder_tax_id'],
        'transfer_record': {
            'id': test_record[0],
            'name': test_record[1] or '',
            'surname': test_record[2] or '',
            'transfer_amount': test_record[3] or 0,
            'transfer_date': test_record[4] or '',
            'id_card': test_record[5] or '',
            'address': test_record[6] or '',
            'percent': test_record[7] if len(test_record) > 7 else 0,
            'total_amount': test_record[8] if len(test_record) > 8 else 0,
            'fee': test_record[9] if len(test_record) > 9 else 0,
            'remark': test_record[10] if len(test_record) > 10 else ''
        }
    }
    
    # บันทึกข้อมูลทดสอบ
    temp_file_path = "temp_dashboard_data.json"
    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Created test data: {temp_file_path}")
        print(f"📄 Test data content:")
        print(json.dumps(complete_data, ensure_ascii=False, indent=2))
        return True
    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        return False

def analyze_threading_issues():
    """วิเคราะห์ปัญหา threading"""
    print("\n" + "=" * 60)
    print("🔍 Analyzing Threading Issues")
    print("=" * 60)
    
    main_file = "main_prgram_tax.py"
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ตรวจสอบการใช้ threading
    threading_patterns = [
        r'import threading',
        r'threading\.Thread',
        r'thread.*\.start\(\)',
        r'daemon=True'
    ]
    
    for pattern in threading_patterns:
        matches = re.findall(pattern, content)
        if matches:
            print(f"✅ {pattern}: Found {len(matches)} occurrence(s)")
        else:
            print(f"❌ {pattern}: NOT FOUND")
    
    # ตรวจสอบการเรียกใช้ page.update()
    page_update_matches = re.findall(r'page\.update\(\)', content)
    print(f"📊 page.update() calls: {len(page_update_matches)}")
    
    return True

def main():
    """ฟังก์ชันหลัก"""
    print("🔬 Main Program Debug Analysis")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Working directory: {os.getcwd()}")
    
    # ตรวจสอบการประกาศตัวแปร
    check_variable_definitions()
    
    # ตรวจสอบตำแหน่งฟังก์ชัน thread
    check_thread_function_locations()
    
    # ตรวจสอบขอบเขตตัวแปรใน crystal tab
    check_crystal_report_tab_scope()
    
    # วิเคราะห์ปัญหา threading
    analyze_threading_issues()
    
    # สร้างกรณีทดสอบ
    create_simple_test_case()
    
    print("\n" + "=" * 60)
    print("🎯 Debug Analysis Complete")
    print("=" * 60)
    print("📋 Check the results above to identify the specific issue")
    print("🔧 Most likely issues:")
    print("   1. Variables not declared in crystal tab scope")
    print("   2. Thread functions defined outside variable scope")
    print("   3. Missing page.update() calls")
    print("   4. Import issues with threading module")

if __name__ == "__main__":
    main()


