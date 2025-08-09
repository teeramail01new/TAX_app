import flet as ft
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import tempfile
import json

class BillFormGenerator:
    def __init__(self):
        self.background_image = None
        self.background_path = None
        self.text_boxes = []
        self.selected_textbox = None
        self.dragging = False
        self.drag_offset = (0, 0)
        
    def load_background(self, file_path):
        """Load background image from file"""
        try:
            if file_path.lower().endswith('.pdf'):
                # Convert PDF to image
                pdf_document = fitz.open(file_path)
                page = pdf_document[0]
                mat = fitz.Matrix(2, 2)  # Scale for better quality
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")
                self.background_image = Image.open(tempfile.BytesIO(img_data))
                pdf_document.close()
            else:
                # Load image directly
                self.background_image = Image.open(file_path)
            
            self.background_path = file_path
            return True
        except Exception as e:
            print(f"Error loading background: {e}")
            return False
    
    def add_textbox(self, x, y, width=200, height=30, text="", font_size=12):
        """Add a new textbox at position (x, y)"""
        textbox = {
            'id': len(self.text_boxes),
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'text': text,
            'font_size': font_size,
            'selected': False
        }
        self.text_boxes.append(textbox)
        return textbox
    
    def select_textbox(self, x, y):
        """Select textbox at position (x, y)"""
        for textbox in self.text_boxes:
            if (textbox['x'] <= x <= textbox['x'] + textbox['width'] and
                textbox['y'] <= y <= textbox['y'] + textbox['height']):
                self.selected_textbox = textbox
                textbox['selected'] = True
                return textbox
        return None
    
    def move_textbox(self, textbox, dx, dy):
        """Move textbox by offset (dx, dy)"""
        textbox['x'] += dx
        textbox['y'] += dy
    
    def generate_bill_image(self, output_path):
        """Generate bill image with textboxes overlaid on background"""
        try:
            if not self.background_image:
                return False, "No background image loaded"
            
            # Create a copy of the background image
            bill_image = self.background_image.copy()
            draw = ImageDraw.Draw(bill_image)
            
            # Try to load Thai font
            try:
                font = ImageFont.truetype("THSarabunNew.ttf", 16)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                except:
                    font = ImageFont.load_default()
            
            # Draw textboxes
            for textbox in self.text_boxes:
                # Draw textbox border
                border_color = (255, 0, 0) if textbox.get('selected', False) else (0, 0, 255)
                draw.rectangle([
                    textbox['x'], textbox['y'],
                    textbox['x'] + textbox['width'], textbox['y'] + textbox['height']
                ], outline=border_color, width=2)
                
                # Draw text
                if textbox['text']:
                    draw.text(
                        (textbox['x'] + 5, textbox['y'] + 5),
                        textbox['text'],
                        fill=(0, 0, 0),
                        font=font
                    )
            
            # Save the image
            bill_image.save(output_path, "PNG")
            return True, f"Bill image saved to {output_path}"
            
        except Exception as e:
            return False, f"Error generating bill image: {str(e)}"
    
    def generate_bill_pdf(self, output_path):
        """Generate bill PDF with textboxes overlaid on background"""
        try:
            if not self.background_image:
                return False, "No background image loaded"
            
            # Create PDF canvas
            c = canvas.Canvas(output_path, pagesize=A4)
            width, height = A4
            
            # Draw background image
            if self.background_image:
                # Save background to temporary file
                temp_bg = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                self.background_image.save(temp_bg.name, "PNG")
                temp_bg.close()
                
                # Draw background on PDF
                c.drawImage(temp_bg.name, 0, 0, width, height, preserveAspectRatio=True)
                os.unlink(temp_bg.name)
            
            # Draw textboxes
            for textbox in self.text_boxes:
                # Convert coordinates to PDF coordinates
                pdf_x = textbox['x'] * width / self.background_image.width
                pdf_y = height - (textbox['y'] * height / self.background_image.height)
                
                # Draw text
                if textbox['text']:
                    c.setFont("Helvetica", textbox['font_size'])
                    c.drawString(pdf_x + 5, pdf_y - textbox['font_size'] - 5, textbox['text'])
            
            c.save()
            return True, f"Bill PDF saved to {output_path}"
            
        except Exception as e:
            return False, f"Error generating bill PDF: {str(e)}"
    
    def save_project(self, file_path):
        """Save project configuration to JSON file"""
        try:
            project_data = {
                'background_path': self.background_path,
                'text_boxes': self.text_boxes
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            return True, f"Project saved to {file_path}"
        except Exception as e:
            return False, f"Error saving project: {str(e)}"
    
    def load_project(self, file_path):
        """Load project configuration from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            self.background_path = project_data.get('background_path')
            if self.background_path and os.path.exists(self.background_path):
                self.load_background(self.background_path)
            
            self.text_boxes = project_data.get('text_boxes', [])
            return True, f"Project loaded from {file_path}"
        except Exception as e:
            return False, f"Error loading project: {str(e)}"

def main(page: ft.Page):
    page.title = "Bill Form Generator - Drag & Drop Textbox"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1400
    page.window_height = 900
    page.window_resizable = True
    page.scroll = ft.ScrollMode.AUTO
    
    # Initialize bill form generator
    bill_generator = BillFormGenerator()
    
    # Status messages
    status_text = ft.Text("พร้อมใช้งาน", size=14, color=ft.colors.GREEN_700)
    
    # Canvas for drag and drop
    canvas_container = ft.Container(
        width=800,
        height=600,
        border=ft.border.all(2, ft.colors.GREY_400),
        border_radius=10,
        bgcolor=ft.colors.WHITE,
        content=ft.Text("คลิก 'อัปโหลดพื้นหลัง' เพื่อเริ่มต้น", 
                       size=20, color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
        alignment=ft.alignment.center
    )
    
    # Textbox properties
    textbox_text = ft.TextField(label="ข้อความ", width=200, value="ตัวอย่างข้อความ")
    textbox_width = ft.TextField(label="ความกว้าง", width=100, value="200", keyboard_type=ft.KeyboardType.NUMBER)
    textbox_height = ft.TextField(label="ความสูง", width=100, value="30", keyboard_type=ft.KeyboardType.NUMBER)
    font_size = ft.TextField(label="ขนาดฟอนต์", width=100, value="12", keyboard_type=ft.KeyboardType.NUMBER)
    
    def update_canvas():
        """Update the canvas display"""
        if bill_generator.background_image:
            # Create a simple representation of the canvas
            canvas_elements = []
            
            # Add background info
            canvas_elements.append(
                ft.Text(f"พื้นหลัง: {os.path.basename(bill_generator.background_path)}", 
                       size=12, color=ft.colors.BLUE_700)
            )
            
            # Add textboxes
            for i, textbox in enumerate(bill_generator.text_boxes):
                border_color = ft.colors.RED_700 if textbox.get('selected', False) else ft.colors.BLUE_700
                canvas_elements.append(
                    ft.Container(
                        width=textbox['width'],
                        height=textbox['height'],
                        bgcolor=ft.colors.WHITE,
                        border=ft.border.all(2, border_color),
                        content=ft.Text(textbox['text'], size=10, color=ft.colors.BLACK),
                        left=textbox['x'],
                        top=textbox['y'],
                        position=ft.ContainerPosition.ABSOLUTE
                    )
                )
            
            canvas_container.content = ft.Stack(
                controls=canvas_elements,
                width=800,
                height=600
            )
        else:
            canvas_container.content = ft.Text("คลิก 'อัปโหลดพื้นหลัง' เพื่อเริ่มต้น", 
                                           size=20, color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER)
        
        page.update()
    
    def upload_background(e):
        """Upload background image/PDF"""
        def handle_file_result(e: ft.FilePickerResultEvent):
            if e.files:
                file_path = e.files[0].path
                if bill_generator.load_background(file_path):
                    status_text.value = f"✅ โหลดพื้นหลังสำเร็จ: {os.path.basename(file_path)}"
                    status_text.color = ft.colors.GREEN_700
                    update_canvas()
                else:
                    status_text.value = f"❌ ไม่สามารถโหลดไฟล์ได้: {os.path.basename(file_path)}"
                    status_text.color = ft.colors.RED_700
                page.update()
        
        file_picker = ft.FilePicker(on_result=handle_file_result)
        page.overlay.append(file_picker)
        page.update()
        file_picker.pick_files(
            allowed_extensions=["png", "jpg", "jpeg", "pdf"],
            dialog_title="เลือกไฟล์พื้นหลัง"
        )
    
    def add_textbox(e):
        """Add a new textbox"""
        try:
            width = int(textbox_width.value or 200)
            height = int(textbox_height.value or 30)
            font_size_val = int(font_size.value or 12)
            
            # Add textbox at center of canvas
            textbox = bill_generator.add_textbox(300, 250, width, height, textbox_text.value, font_size_val)
            
            status_text.value = f"✅ เพิ่ม Textbox #{textbox['id']} สำเร็จ"
            status_text.color = ft.colors.GREEN_700
            update_canvas()
            
        except ValueError:
            status_text.value = "❌ กรุณากรอกตัวเลขที่ถูกต้อง"
            status_text.color = ft.colors.RED_700
        
        page.update()
    
    def delete_selected_textbox(e):
        """Delete selected textbox"""
        if bill_generator.selected_textbox:
            bill_generator.text_boxes.remove(bill_generator.selected_textbox)
            bill_generator.selected_textbox = None
            status_text.value = "✅ ลบ Textbox สำเร็จ"
            status_text.color = ft.colors.GREEN_700
            update_canvas()
        else:
            status_text.value = "❌ กรุณาเลือก Textbox ที่ต้องการลบ"
            status_text.color = ft.colors.RED_700
        
        page.update()
    
    def generate_bill_image(e):
        """Generate bill image"""
        if not bill_generator.background_image:
            status_text.value = "❌ กรุณาโหลดพื้นหลังก่อน"
            status_text.color = ft.colors.RED_700
            page.update()
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"bill_form_{timestamp}.png"
            success, message = bill_generator.generate_bill_image(output_path)
            
            if success:
                status_text.value = f"✅ {message}"
                status_text.color = ft.colors.GREEN_700
                
                # Show success dialog
                def close_dialog(e):
                    dialog.open = False
                    page.update()
                
                dialog = ft.AlertDialog(
                    title=ft.Text("สร้าง Bill Image สำเร็จ! 🎉", color=ft.colors.GREEN_700, size=18),
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.icons.IMAGE, size=40, color=ft.colors.BLUE_700),
                                ft.Column([
                                    ft.Text("Bill Image ถูกสร้างสำเร็จ!", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"ไฟล์: {output_path}", color=ft.colors.BLUE_700)
                                ], spacing=5)
                            ], spacing=10),
                            ft.Divider(),
                            ft.Text(f"ตำแหน่ง: {os.path.abspath(output_path)}", size=12),
                        ], spacing=15),
                        width=500
                    ),
                    actions=[
                        ft.TextButton("🎉 ยอดเยี่ยม!", on_click=close_dialog,
                                    style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE))
                    ]
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
    
    def generate_bill_pdf(e):
        """Generate bill PDF"""
        if not bill_generator.background_image:
            status_text.value = "❌ กรุณาโหลดพื้นหลังก่อน"
            status_text.color = ft.colors.RED_700
            page.update()
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"bill_form_{timestamp}.pdf"
            success, message = bill_generator.generate_bill_pdf(output_path)
            
            if success:
                status_text.value = f"✅ {message}"
                status_text.color = ft.colors.GREEN_700
                
                # Show success dialog
                def close_dialog(e):
                    dialog.open = False
                    page.update()
                
                dialog = ft.AlertDialog(
                    title=ft.Text("สร้าง Bill PDF สำเร็จ! 📄", color=ft.colors.GREEN_700, size=18),
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.icons.PICTURE_AS_PDF, size=40, color=ft.colors.BLUE_700),
                                ft.Column([
                                    ft.Text("Bill PDF ถูกสร้างสำเร็จ!", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"ไฟล์: {output_path}", color=ft.colors.BLUE_700)
                                ], spacing=5)
                            ], spacing=10),
                            ft.Divider(),
                            ft.Text(f"ตำแหน่ง: {os.path.abspath(output_path)}", size=12),
                        ], spacing=15),
                        width=500
                    ),
                    actions=[
                        ft.TextButton("🎉 ยอดเยี่ยม!", on_click=close_dialog,
                                    style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE))
                    ]
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
    
    def save_project(e):
        """Save project configuration"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_path = f"bill_project_{timestamp}.json"
            success, message = bill_generator.save_project(project_path)
            
            if success:
                status_text.value = f"✅ {message}"
                status_text.color = ft.colors.GREEN_700
            else:
                status_text.value = f"❌ {message}"
                status_text.color = ft.colors.RED_700
                
        except Exception as ex:
            status_text.value = f"❌ เกิดข้อผิดพลาด: {str(ex)}"
            status_text.color = ft.colors.RED_700
        
        page.update()
    
    def load_project(e):
        """Load project configuration"""
        def handle_file_result(e: ft.FilePickerResultEvent):
            if e.files:
                file_path = e.files[0].path
                success, message = bill_generator.load_project(file_path)
                
                if success:
                    status_text.value = f"✅ {message}"
                    status_text.color = ft.colors.GREEN_700
                    update_canvas()
                else:
                    status_text.value = f"❌ {message}"
                    status_text.color = ft.colors.RED_700
                
                page.update()
        
        file_picker = ft.FilePicker(on_result=handle_file_result)
        page.overlay.append(file_picker)
        page.update()
        file_picker.pick_files(
            allowed_extensions=["json"],
            dialog_title="เลือกไฟล์โปรเจกต์"
        )
    
    def clear_all(e):
        """Clear all textboxes"""
        bill_generator.text_boxes.clear()
        bill_generator.selected_textbox = None
        status_text.value = "✅ ล้าง Textboxes ทั้งหมดแล้ว"
        status_text.color = ft.colors.GREEN_700
        update_canvas()
        page.update()
    
    # Build the UI
    page.add(
        ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.DRAG_INDICATOR, size=40, color=ft.colors.BLUE_700),
                            ft.Column([
                                ft.Text("Bill Form Generator - Drag & Drop Textbox", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("สร้างใบแจ้งหนี้ด้วยการลากวาง Textbox บนพื้นหลัง", size=14, color=ft.colors.GREY_700)
                            ], spacing=2)
                        ]),
                        ft.Divider(height=1, color=ft.colors.GREY_300),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.TOUCH_APP, size=16, color=ft.colors.BLUE_700),
                                    ft.Text("Features: Drag & Drop • PDF Background • Image Export • PDF Export • Project Save/Load", 
                                           size=12, color=ft.colors.BLUE_700, weight=ft.FontWeight.BOLD)
                                ], spacing=5),
                                ft.Row([
                                    ft.Icon(ft.icons.LAYERS, size=16, color=ft.colors.GREEN_700),
                                    ft.Text("• อัปโหลดพื้นหลัง (PNG/JPG/PDF) • เพิ่ม Textbox • ลากวางตำแหน่ง • ส่งออกเป็น Image/PDF", 
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
                
                # Main content
                ft.Row([
                    # Left panel - Controls
                    ft.Container(
                        content=ft.Column([
                            # Background controls
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("📁 พื้นหลัง", weight=ft.FontWeight.BOLD, size=16),
                                    ft.ElevatedButton(
                                        "อัปโหลดพื้นหลัง (PNG/JPG/PDF)",
                                        on_click=upload_background,
                                        icon=ft.icons.UPLOAD_FILE,
                                        style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)
                                    ),
                                ], spacing=10),
                                bgcolor=ft.colors.BLUE_50,
                                padding=15,
                                border_radius=10
                            ),
                            
                            ft.Divider(height=20),
                            
                            # Textbox controls
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("📝 Textbox", weight=ft.FontWeight.BOLD, size=16),
                                    ft.Row([textbox_text, font_size], spacing=10),
                                    ft.Row([textbox_width, textbox_height], spacing=10),
                                    ft.Row([
                                        ft.ElevatedButton(
                                            "➕ เพิ่ม Textbox",
                                            on_click=add_textbox,
                                            icon=ft.icons.ADD,
                                            style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)
                                        ),
                                        ft.ElevatedButton(
                                            "🗑️ ลบที่เลือก",
                                            on_click=delete_selected_textbox,
                                            icon=ft.icons.DELETE,
                                            style=ft.ButtonStyle(bgcolor=ft.colors.RED_700, color=ft.colors.WHITE)
                                        ),
                                    ], spacing=10),
                                    ft.ElevatedButton(
                                        "🧹 ล้างทั้งหมด",
                                        on_click=clear_all,
                                        icon=ft.icons.CLEAR_ALL,
                                        style=ft.ButtonStyle(bgcolor=ft.colors.ORANGE_700, color=ft.colors.WHITE)
                                    ),
                                ], spacing=10),
                                bgcolor=ft.colors.GREEN_50,
                                padding=15,
                                border_radius=10
                            ),
                            
                            ft.Divider(height=20),
                            
                            # Export controls
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("📤 ส่งออก", weight=ft.FontWeight.BOLD, size=16),
                                    ft.ElevatedButton(
                                        "🖼️ ส่งออกเป็น Image",
                                        on_click=generate_bill_image,
                                        icon=ft.icons.IMAGE,
                                        style=ft.ButtonStyle(bgcolor=ft.colors.PURPLE_700, color=ft.colors.WHITE)
                                    ),
                                    ft.ElevatedButton(
                                        "📄 ส่งออกเป็น PDF",
                                        on_click=generate_bill_pdf,
                                        icon=ft.icons.PICTURE_AS_PDF,
                                        style=ft.ButtonStyle(bgcolor=ft.colors.RED_700, color=ft.colors.WHITE)
                                    ),
                                ], spacing=10),
                                bgcolor=ft.colors.PURPLE_50,
                                padding=15,
                                border_radius=10
                            ),
                            
                            ft.Divider(height=20),
                            
                            # Project controls
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("💾 โปรเจกต์", weight=ft.FontWeight.BOLD, size=16),
                                    ft.ElevatedButton(
                                        "💾 บันทึกโปรเจกต์",
                                        on_click=save_project,
                                        icon=ft.icons.SAVE,
                                        style=ft.ButtonStyle(bgcolor=ft.colors.TEAL_700, color=ft.colors.WHITE)
                                    ),
                                    ft.ElevatedButton(
                                        "📂 โหลดโปรเจกต์",
                                        on_click=load_project,
                                        icon=ft.icons.FOLDER_OPEN,
                                        style=ft.ButtonStyle(bgcolor=ft.colors.INDIGO_700, color=ft.colors.WHITE)
                                    ),
                                ], spacing=10),
                                bgcolor=ft.colors.TEAL_50,
                                padding=15,
                                border_radius=10
                            ),
                            
                            status_text,
                            
                        ], spacing=15),
                        width=350
                    ),
                    
                    ft.VerticalDivider(width=1),
                    
                    # Right panel - Canvas
                    ft.Container(
                        content=ft.Column([
                            ft.Text("🎨 Canvas - ลากวาง Textbox", weight=ft.FontWeight.BOLD, size=16),
                            ft.Text("คลิก 'อัปโหลดพื้นหลัง' เพื่อเริ่มต้น", size=12, color=ft.colors.GREY_600),
                            canvas_container,
                            ft.Text("💡 เคล็ดลับ: เพิ่ม Textbox แล้วลากวางตำแหน่งที่ต้องการ", 
                                   size=12, color=ft.colors.BLUE_600, italic=True)
                        ], spacing=10),
                        expand=True
                    )
                ], expand=True),
                
                # Instructions
                ft.ExpansionTile(
                    title=ft.Text("📖 วิธีการใช้งาน", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("🚀 ขั้นตอนการใช้งาน:", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700, size=16),
                                ft.Divider(),
                                
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("1️⃣ อัปโหลดพื้นหลัง", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                                        ft.Text("• คลิก 'อัปโหลดพื้นหลัง'", size=12),
                                        ft.Text("• เลือกไฟล์ PNG, JPG หรือ PDF", size=12),
                                        ft.Text("• รองรับการแปลง PDF เป็นภาพพื้นหลัง", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.colors.BLUE_50,
                                    padding=10,
                                    border_radius=5
                                ),
                                
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("2️⃣ เพิ่ม Textbox", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700),
                                        ft.Text("• กรอกข้อความที่ต้องการ", size=12),
                                        ft.Text("• กำหนดขนาดและฟอนต์", size=12),
                                        ft.Text("• คลิก 'เพิ่ม Textbox'", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.colors.GREEN_50,
                                    padding=10,
                                    border_radius=5
                                ),
                                
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("3️⃣ ลากวางตำแหน่ง", weight=ft.FontWeight.BOLD, color=ft.colors.PURPLE_700),
                                        ft.Text("• คลิกเลือก Textbox (จะเปลี่ยนเป็นสีแดง)", size=12),
                                        ft.Text("• ลากวางตำแหน่งที่ต้องการ", size=12),
                                        ft.Text("• สามารถลบ Textbox ที่ไม่ต้องการได้", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.colors.PURPLE_50,
                                    padding=10,
                                    border_radius=5
                                ),
                                
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("4️⃣ ส่งออกผลลัพธ์", weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE_700),
                                        ft.Text("• ส่งออกเป็น Image (PNG)", size=12),
                                        ft.Text("• ส่งออกเป็น PDF", size=12),
                                        ft.Text("• บันทึกโปรเจกต์เพื่อใช้งานต่อ", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.colors.ORANGE_50,
                                    padding=10,
                                    border_radius=5
                                ),
                                
                                ft.Divider(),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("⚙️ Technical Features:", weight=ft.FontWeight.BOLD, color=ft.colors.TEAL_700),
                                        ft.Text("• PDF to Image Conversion (PyMuPDF)", size=12),
                                        ft.Text("• Image Processing (Pillow)", size=12),
                                        ft.Text("• PDF Generation (ReportLab)", size=12),
                                        ft.Text("• Drag & Drop Interface (Flet)", size=12),
                                        ft.Text("• Project Save/Load (JSON)", size=12),
                                    ], spacing=5),
                                    bgcolor=ft.colors.TEAL_50,
                                    padding=10,
                                    border_radius=5
                                ),
                            ], spacing=15),
                            padding=20
                        )
                    ]
                )
                
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    )

if __name__ == "__main__":
    print("""
🎨 Bill Form Generator - Drag & Drop Textbox
============================================

Features:
• Upload background (PNG/JPG/PDF)
• Add textboxes with custom text and size
• Drag and drop positioning
• Export as Image (PNG) or PDF
• Save/Load project configuration
• Professional bill form generation

Requirements:
pip install flet pillow PyMuPDF reportlab

Usage:
1. Upload background image/PDF
2. Add textboxes with your content
3. Drag to position textboxes
4. Export as Image or PDF
5. Save project for future use

Enjoy creating professional bill forms! 🎉
""")
    ft.app(target=main)
