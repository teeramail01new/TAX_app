#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
โปรแกรมทดสอบการเขียนฟอนต์ไทยลง PDF
ทดสอบหลายวิธีในการเขียนข้อความภาษาไทยใน PDF
"""

import os
import sys
from datetime import datetime

def test_method_1_pymupdf():
    """ทดสอบด้วย PyMuPDF (fitz)"""
    print("🧪 วิธีที่ 1: ทดสอบด้วย PyMuPDF")
    try:
        import fitz
        
        # สร้าง PDF ใหม่
        doc = fitz.open()
        page = doc.new_page()
        
        # ข้อความทดสอบ
        thai_text = "สวัสดีครับ นี่คือการทดสอบฟอนต์ไทย 🇹🇭"
        print(f"📝 ข้อความทดสอบ: {thai_text}")
        
        # ลองหา Thai font ในระบบ
        thai_fonts = [
            r"C:\Windows\Fonts\tahoma.ttf",
            r"C:\Windows\Fonts\Tahoma.ttf", 
            r"C:\Windows\Fonts\THSarabunNew.ttf",
            r"C:\Windows\Fonts\NotoSansThai-Regular.ttf",
            r"C:\Windows\Fonts\LeelawUI.ttf",
            r"C:\Windows\Fonts\LilyUPC.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\ARIALUNI.TTF"
        ]
        
        y_pos = 100
        font_found = False
        
        for font_path in thai_fonts:
            if os.path.exists(font_path):
                try:
                    print(f"🔍 พบฟอนต์: {font_path}")
                    
                    # ลองทุกวิธีที่เป็นไปได้
                    methods = [
                        lambda: doc.insert_font(fontfile=font_path),
                        lambda: doc.insertFont(fontfile=font_path),
                        lambda: doc.insert_font(fontname="thai", fontfile=font_path),
                        lambda: doc.insertFont(fontname="thai", fontfile=font_path),
                    ]
                    
                    for i, method in enumerate(methods):
                        try:
                            font_name = method()
                            print(f"✅ วิธีที่ {i+1} สำเร็จ: {font_name}")
                            
                            # เขียนข้อความ
                            point = fitz.Point(50, y_pos)
                            page.insert_text(point, f"[{os.path.basename(font_path)}] {thai_text}", 
                                           fontsize=16, fontname=font_name, color=(0, 0, 0))
                            y_pos += 30
                            font_found = True
                            break
                            
                        except Exception as e:
                            print(f"❌ วิธีที่ {i+1} ล้มเหลว: {e}")
                            continue
                    
                    if font_found:
                        break
                        
                except Exception as e:
                    print(f"❌ ไม่สามารถใช้ฟอนต์ {font_path}: {e}")
                    continue
        
        # ลองเขียนด้วยฟอนต์เริ่มต้น + UTF-8
        if not font_found:
            print("⚠️ ไม่พบฟอนต์ไทย ลองใช้ฟอนต์เริ่มต้น + UTF-8")
            try:
                point = fitz.Point(50, y_pos)
                page.insert_text(point, f"[Default + UTF-8] {thai_text}", 
                               fontsize=16, encoding=1, color=(1, 0, 0))
                y_pos += 30
            except Exception as e:
                print(f"❌ ฟอนต์เริ่มต้น + UTF-8 ล้มเหลว: {e}")
        
        # ลองเขียนด้วยฟอนต์เริ่มต้นธรรมดา
        try:
            point = fitz.Point(50, y_pos)
            page.insert_text(point, f"[Default] {thai_text}", 
                           fontsize=16, color=(0, 0, 1))
            y_pos += 30
        except Exception as e:
            print(f"❌ ฟอนต์เริ่มต้นธรรมดา ล้มเหลว: {e}")
        
        # บันทึกไฟล์
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_thai_pymupdf_{timestamp}.pdf"
        doc.save(filename)
        doc.close()
        
        print(f"✅ บันทึกไฟล์สำเร็จ: {filename}")
        return True
        
    except ImportError:
        print("❌ ไม่พบ PyMuPDF (fitz)")
        return False
    except Exception as e:
        print(f"❌ ข้อผิดพลาด PyMuPDF: {e}")
        return False

def test_method_2_reportlab():
    """ทดสอบด้วย ReportLab"""
    print("\n🧪 วิธีที่ 2: ทดสอบด้วย ReportLab")
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # สร้าง PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_thai_reportlab_{timestamp}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        
        # ข้อความทดสอบ
        thai_text = "สวัสดีครับ นี่คือการทดสอบฟอนต์ไทย 🇹🇭"
        print(f"📝 ข้อความทดสอบ: {thai_text}")
        
        # ลองลงทะเบียนฟอนต์ไทย
        thai_fonts = [
            (r"C:\Windows\Fonts\tahoma.ttf", "Tahoma"),
            (r"C:\Windows\Fonts\Tahoma.ttf", "Tahoma2"), 
            (r"C:\Windows\Fonts\THSarabunNew.ttf", "THSarabun"),
            (r"C:\Windows\Fonts\NotoSansThai-Regular.ttf", "NotoThai"),
            (r"C:\Windows\Fonts\LeelawUI.ttf", "Leelaw"),
            (r"C:\Windows\Fonts\arial.ttf", "Arial"),
            (r"C:\Windows\Fonts\ARIALUNI.TTF", "ArialUni")
        ]
        
        y_pos = 750
        font_registered = False
        
        for font_path, font_name in thai_fonts:
            if os.path.exists(font_path):
                try:
                    print(f"🔍 พบฟอนต์: {font_path}")
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    print(f"✅ ลงทะเบียนฟอนต์สำเร็จ: {font_name}")
                    
                    # เขียนข้อความ
                    c.setFont(font_name, 16)
                    c.drawString(50, y_pos, f"[{font_name}] {thai_text}")
                    y_pos -= 30
                    font_registered = True
                    
                except Exception as e:
                    print(f"❌ ไม่สามารถลงทะเบียนฟอนต์ {font_name}: {e}")
                    continue
        
        # ลองใช้ฟอนต์เริ่มต้น
        if not font_registered:
            print("⚠️ ไม่สามารถลงทะเบียนฟอนต์ไทย ใช้ฟอนต์เริ่มต้น")
        
        try:
            c.setFont("Helvetica", 16)
            c.drawString(50, y_pos, f"[Helvetica] {thai_text}")
            y_pos -= 30
        except Exception as e:
            print(f"❌ ฟอนต์ Helvetica ล้มเหลว: {e}")
        
        c.save()
        print(f"✅ บันทึกไฟล์สำเร็จ: {filename}")
        return True
        
    except ImportError:
        print("❌ ไม่พบ ReportLab")
        return False
    except Exception as e:
        print(f"❌ ข้อผิดพลาด ReportLab: {e}")
        return False

def test_method_3_pypdf():
    """ทดสอบด้วย PyPDF2/PyPDF4"""
    print("\n🧪 วิธีที่ 3: ทดสอบด้วย PyPDF2")
    try:
        import PyPDF2
        print("📌 PyPDF2 ใช้สำหรับอ่าน/รวม PDF ไม่ใช่สร้างข้อความใหม่")
        print("✅ PyPDF2 พร้อมใช้งาน (สำหรับการรวม PDF)")
        return True
        
    except ImportError:
        print("❌ ไม่พบ PyPDF2")
        return False

def check_system_fonts():
    """ตรวจสอบฟอนต์ในระบบ"""
    print("\n🔍 ตรวจสอบฟอนต์ไทยในระบบ:")
    
    font_paths = [
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\Tahoma.ttf",
        r"C:\Windows\Fonts\THSarabunNew.ttf", 
        r"C:\Windows\Fonts\NotoSansThai-Regular.ttf",
        r"C:\Windows\Fonts\LeelawUI.ttf",
        r"C:\Windows\Fonts\LeelUIsl.ttf",
        r"C:\Windows\Fonts\LilyUPC.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\ARIALUNI.TTF",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\Calibri.ttf"
    ]
    
    found_fonts = []
    for font_path in font_paths:
        if os.path.exists(font_path):
            print(f"✅ {font_path}")
            found_fonts.append(font_path)
        else:
            print(f"❌ {font_path}")
    
    print(f"\n📊 พบฟอนต์ทั้งหมด: {len(found_fonts)} ฟอนต์")
    return found_fonts

def check_encoding():
    """ตรวจสอบการเข้ารหัส"""
    print("\n🔍 ตรวจสอบการเข้ารหัส:")
    
    thai_text = "สวัสดีครับ ทดสอบภาษาไทย 🇹🇭"
    
    print(f"📝 ข้อความต้นฉบับ: {thai_text}")
    print(f"📊 ความยาว: {len(thai_text)} ตัวอักษร")
    print(f"🔢 UTF-8 bytes: {thai_text.encode('utf-8')}")
    print(f"🔢 UTF-16 bytes: {thai_text.encode('utf-16')}")
    
    # ตรวจสอบ encoding ของไฟล์
    print(f"📄 File encoding: {sys.stdout.encoding}")
    print(f"💻 System encoding: {sys.getdefaultencoding()}")

def main():
    """ฟังก์ชันหลัก"""
    print("=" * 60)
    print("🇹🇭 โปรแกรมทดสอบการเขียนฟอนต์ไทยลง PDF")
    print("=" * 60)
    
    # ตรวจสอบการเข้ารหัส
    check_encoding()
    
    # ตรวจสอบฟอนต์ในระบบ
    found_fonts = check_system_fonts()
    
    if not found_fonts:
        print("\n❌ ไม่พบฟอนต์ในระบบ! โปรแกรมอาจทำงานไม่ถูกต้อง")
        return
    
    # ทดสอบแต่ละวิธี
    results = []
    
    # ทดสอบ PyMuPDF
    results.append(("PyMuPDF", test_method_1_pymupdf()))
    
    # ทดสอบ ReportLab
    results.append(("ReportLab", test_method_2_reportlab()))
    
    # ทดสอบ PyPDF2
    results.append(("PyPDF2", test_method_3_pypdf()))
    
    # สรุปผล
    print("\n" + "=" * 60)
    print("📊 สรุปผลการทดสอบ")
    print("=" * 60)
    
    for method, success in results:
        status = "✅ สำเร็จ" if success else "❌ ล้มเหลว"
        print(f"{method}: {status}")
    
    print(f"\n📁 ไฟล์ทดสอบจะถูกบันทึกในโฟลเดอร์: {os.getcwd()}")
    print("🔍 กรุณาเปิดไฟล์ PDF ที่สร้างขึ้นเพื่อตรวจสอบว่าภาษาไทยแสดงอย่างถูกต้องหรือไม่")

if __name__ == "__main__":
    main()
