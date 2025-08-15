#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Click Fix - แก้ไขให้กดปุ่มอัตโนมัติ
"""

import re

def fix_auto_click():
    print("🔧 Fixing auto-click functionality...")
    
    # อ่านไฟล์
    with open("main_prgram_tax.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # ค้นหาส่วนที่สร้างปุ่ม "ดึงข้อมูลที่เลือก"
    button_pattern = r'ft\.ElevatedButton\("⬇️ ดึงข้อมูลที่เลือก", on_click=lambda e: auto_fill_from_selected_dashboard\(\)'
    
    if button_pattern in content:
        print("✅ Found 'ดึงข้อมูลที่เลือก' button")
        
        # เพิ่มโค้ดที่กดปุ่มอัตโนมัติหลังจากสร้าง UI
        auto_click_code = '''
        # AUTO-CLICK: กดปุ่ม "ดึงข้อมูลที่เลือก" อัตโนมัติ
        def trigger_auto_fill():
            import time
            time.sleep(1.0)  # รอให้ UI พร้อม
            try:
                print("🔄 Auto-triggering: ดึงข้อมูลที่เลือก...")
                auto_fill_from_selected_dashboard()
                print("✅ Auto-fill triggered successfully!")
            except Exception as e:
                print(f"❌ Auto-fill error: {e}")
        
        # เริ่ม auto-trigger
        import threading
        threading.Thread(target=trigger_auto_fill, daemon=True).start()
        '''
        
        # หาตำแหน่งที่จะแทรกโค้ด (หลังจาก return crystal_tab)
        return_pattern = r'return crystal_tab'
        
        if return_pattern in content:
            # แทรกโค้ดก่อน return crystal_tab
            content = content.replace(
                'return crystal_tab',
                auto_click_code + '\n        return crystal_tab'
            )
            print("✅ Added auto-click code")
            
            # บันทึกไฟล์
            with open("main_prgram_tax.py", "w", encoding="utf-8") as f:
                f.write(content)
            
            print("✅ File updated successfully!")
            return True
        else:
            print("❌ Could not find 'return crystal_tab'")
            return False
    else:
        print("❌ Could not find 'ดึงข้อมูลที่เลือก' button")
        return False

if __name__ == "__main__":
    print("🚀 AUTO-CLICK FIX")
    print("=" * 30)
    
    success = fix_auto_click()
    
    if success:
        print("\n✅ FIX COMPLETED!")
        print("🔧 Added auto-click functionality")
        print("🚀 Now test: python main_prgram_tax.py")
        print("\nSteps:")
        print("1. Go to Dashboard tab")
        print("2. Select any row (checkbox)")  
        print("3. Click '🚀 นำข้อมูลไปเติมใน Crystal Report'")
        print("4. Wait 1 second → Data will auto-fill!")
    else:
        print("\n❌ FIX FAILED!")
        print("Could not apply auto-click fix")


