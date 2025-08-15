#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os

def create_test_data():
    """สร้างข้อมูลทดสอบ"""
    
    # ตั้งค่า selected_transfer_id_for_pdf
    test_id = 5
    
    # สร้างข้อมูลทดสอบสำหรับ temp file
    test_data = {
        "withholder_name": "บริษัท ทดสอบ จำกัด",
        "withholder_address": "123 ถนนทดสอบ กรุงเทพฯ 10100",
        "withholder_tax_id": "1234567890123",
        "transfer_record": {
            "id": test_id,
            "name": "สมชาย",
            "surname": "ใจดี", 
            "transfer_amount": 15000.0,
            "transfer_date": "2024-01-15",
            "id_card": "9876543210987",
            "address": "456 ถนนสุขใจ เชียงใหม่ 50100",
            "percent": 3.0,
            "total_amount": 15450.0,
            "fee": 450.0,
            "remark": "ค่าธรรมเนียม"
        }
    }
    
    # บันทึก temp file
    with open("temp_dashboard_data.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Created test data with ID: {test_id}")
    print(f"📋 Withholder: {test_data['withholder_name']}")
    print(f"📋 Withholdee: {test_data['transfer_record']['name']} {test_data['transfer_record']['surname']}")

def main():
    print("🔧 SETTING UP TEST DATA")
    print("=" * 30)
    
    create_test_data()
    
    print("\n✅ TEST DATA READY!")
    print("\n🚀 Now run: python main_prgram_tax.py")
    print("\nSteps to test auto-fill:")
    print("1. Go to 'แดชบอร์ด' tab")
    print("2. Select any row (checkbox)")
    print("3. Click '🚀 นำข้อมูลไปเติมใน Crystal Report'")
    print("4. → Tab will switch to 'ระบบพิกัด form PDF'")
    print("5. → After 1 second, data will auto-fill!")
    print("\n📋 Expected data:")
    print("- Withholder: บริษัท ทดสอบ จำกัด")
    print("- Withholdee: สมชาย ใจดี")
    print("- Amount: 15,000.00")
    print("- Fee: 450.00")

if __name__ == "__main__":
    main()


