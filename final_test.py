#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Test - ทดสอบสุดท้าย
"""

import json
import os

def main():
    print("🏁 FINAL TEST - LAST CHECK")
    print("=" * 40)
    
    # ตรวจสอบ temp file
    temp_file = "temp_dashboard_data.json"
    if os.path.exists(temp_file):
        try:
            with open(temp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print("✅ Temp file is valid JSON")
            print(f"📋 Data keys: {list(data.keys())}")
            
            if data.get('withholder_name'):
                print(f"✅ Withholder: {data['withholder_name']}")
            
            if data.get('transfer_record') and data['transfer_record'].get('name'):
                name = data['transfer_record']['name']
                surname = data['transfer_record']['surname']
                print(f"✅ Withholdee: {name} {surname}")
                
        except Exception as e:
            print(f"❌ Temp file error: {e}")
            return False
    else:
        print("❌ No temp file found")
        return False
    
    # ตรวจสอบโปรแกรมหลัก
    if os.path.exists("main_prgram_tax.py"):
        print("✅ Main program exists")
    else:
        print("❌ Main program not found")
        return False
    
    print("\n🎯 READY TO TEST!")
    print("1. กรุณารันโปรแกรม: python main_prgram_tax.py")
    print("2. ไปที่ tab 'แดชบอร์ด'")
    print("3. เลือกรายการใดก็ได้ (checkbox)")
    print("4. กดปุ่ม '🚀 นำข้อมูลไปเติมใน Crystal Report'")
    print("5. รอ 0.5 วินาที → ข้อมูลจะขึ้นเองใน 'ระบบพิกัด form PDF'")
    print("\n✅ AutoFill จะทำงานทันที ไม่ต้องกดปุ่มอื่น!")
    
    return True

if __name__ == "__main__":
    main()


