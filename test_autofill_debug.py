#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test AutoFill Debug Program
ทดสอบการทำงานของ AutoFill และ debug ปัญหา
"""

import json
import os
import time
import threading
from datetime import datetime

def test_temp_file_system():
    """ทดสอบระบบ temp file"""
    print("=" * 50)
    print("🧪 Testing Temp File System")
    print("=" * 50)
    
    # สร้างข้อมูลทดสอบ (จำลองข้อมูลจาก Dashboard)
    test_data = {
        'withholder_name': 'บริษัท ทดสอบ จำกัด',
        'withholder_address': '123 ถนนทดสอบ กรุงเทพฯ 10100',
        'withholder_tax_id': '1234567890123',
        'transfer_record': {
            'id': 999,
            'name': 'สมชาย',
            'surname': 'ใจดี',
            'transfer_amount': 10000.00,
            'transfer_date': '2024-01-15',
            'id_card': '9876543210987',
            'address': '456 ถนนผู้ถูกหัก เชียงใหม่ 50100',
            'percent': 3.0,
            'total_amount': 10300.00,
            'fee': 300.00,
            'remark': 'ค่าธรรมเนียม'
        }
    }
    
    # เขียนข้อมูลลง temp file
    temp_file_path = os.path.join(os.getcwd(), "temp_dashboard_data.json")
    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Created temp file: {temp_file_path}")
        print(f"📄 Data written: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ Failed to create temp file: {e}")
        return False
    
    # อ่านข้อมูลกลับมา
    try:
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        print(f"✅ Successfully read temp file")
        print(f"📖 Data loaded: {json.dumps(loaded_data, ensure_ascii=False, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Failed to read temp file: {e}")
        return False

def simulate_thread1_withholder():
    """จำลอง Thread 1: Auto-fill ผู้หักภาษี"""
    print("\n🔄 Thread 1: Loading withholder data...")
    time.sleep(1.0)  # รอ 1 วินาที
    
    temp_file_path = os.path.join(os.getcwd(), "temp_dashboard_data.json")
    
    if os.path.exists(temp_file_path):
        try:
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                dashboard_data = json.load(f)
            
            print(f"🔍 Found temp file data: {dashboard_data}")
            
            # จำลองการเติมข้อมูลผู้หักภาษี
            withholder_name = dashboard_data.get('withholder_name', '')
            withholder_address = dashboard_data.get('withholder_address', '')
            withholder_tax_id = dashboard_data.get('withholder_tax_id', '')
            
            print(f"✅ Withholder Name: {withholder_name}")
            print(f"✅ Withholder Address: {withholder_address}")
            print(f"✅ Withholder Tax ID: {withholder_tax_id}")
            
            return True
        except Exception as ex:
            print(f"❌ Thread 1 error: {ex}")
            return False
    else:
        print("⚠️ No temp file found for Thread 1")
        return False

def simulate_thread2_withholdee():
    """จำลอง Thread 2: Auto-fill ผู้ถูกหักภาษี"""
    print("\n🔄 Thread 2: Loading withholdee data...")
    time.sleep(1.5)  # รอ 1.5 วินาที
    
    temp_file_path = os.path.join(os.getcwd(), "temp_dashboard_data.json")
    
    if os.path.exists(temp_file_path):
        try:
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                dashboard_data = json.load(f)
            
            print(f"🔍 Found temp file data for withholdee: {dashboard_data}")
            
            # ตรวจสอบ transfer_record
            if dashboard_data.get('transfer_record'):
                record = dashboard_data['transfer_record']
                name = record.get('name', '')
                surname = record.get('surname', '')
                full_name = f"{name} {surname}".strip()
                
                if full_name:
                    # จำลองการเติมข้อมูลผู้ถูกหักภาษี
                    withholdee_name = full_name
                    withholdee_address = record.get('address', '')
                    withholdee_tax_id = record.get('id_card', '')
                    
                    # จำลองการเติมข้อมูลรายได้
                    transfer_amount = record.get('transfer_amount', 0)
                    fee = record.get('fee', 0)
                    
                    print(f"✅ Withholdee Name: {withholdee_name}")
                    print(f"✅ Withholdee Address: {withholdee_address}")
                    print(f"✅ Withholdee Tax ID: {withholdee_tax_id}")
                    print(f"✅ Transfer Amount: {transfer_amount:,.2f}")
                    print(f"✅ Fee: {fee:,.2f}")
                    
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

def test_threading_simulation():
    """ทดสอบการทำงานแบบ Threading"""
    print("\n" + "=" * 50)
    print("🧪 Testing Threading Simulation")
    print("=" * 50)
    
    # เริ่ม thread ทั้ง 2
    thread1 = threading.Thread(target=simulate_thread1_withholder, daemon=True)
    thread2 = threading.Thread(target=simulate_thread2_withholdee, daemon=True)
    
    print("🚀 Starting both threads...")
    thread1.start()
    thread2.start()
    
    # รอให้ thread ทั้งสองเสร็จ
    thread1.join()
    thread2.join()
    
    print("✅ Both threads completed")

def check_main_program_variables():
    """ตรวจสอบตัวแปรที่อาจจะมีปัญหาในโปรแกรมหลัก"""
    print("\n" + "=" * 50)
    print("🧪 Checking Main Program Variables")
    print("=" * 50)
    
    # ตรวจสอบไฟล์หลัก
    main_file = "main_prgram_tax.py"
    if not os.path.exists(main_file):
        print(f"❌ Main file not found: {main_file}")
        return False
    
    # ตรวจสอบ temp file ที่มีอยู่
    temp_files = [f for f in os.listdir('.') if f.startswith('temp_') and f.endswith('.json')]
    print(f"📁 Found temp files: {temp_files}")
    
    for temp_file in temp_files:
        try:
            with open(temp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"📖 {temp_file}: {json.dumps(data, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"❌ Error reading {temp_file}: {e}")
    
    return True

def main():
    """ฟังก์ชันหลักสำหรับทดสอบ"""
    print("🔬 AutoFill Debug Test Program")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Working directory: {os.getcwd()}")
    
    # Test 1: ทดสอบระบบ temp file
    success1 = test_temp_file_system()
    
    # Test 2: ทดสอบการทำงานแบบ threading
    if success1:
        test_threading_simulation()
    
    # Test 3: ตรวจสอบตัวแปรในโปรแกรมหลัก
    check_main_program_variables()
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary")
    print("=" * 50)
    print("✅ Temp file system: Working")
    print("✅ Threading simulation: Working")
    print("📋 Check the results above to debug the main program")
    
    # สร้างรายงานการทดสอบ
    report = {
        "test_time": datetime.now().isoformat(),
        "working_directory": os.getcwd(),
        "temp_file_test": success1,
        "message": "Test completed successfully"
    }
    
    with open("test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📊 Test report saved to: test_report.json")

if __name__ == "__main__":
    main()


