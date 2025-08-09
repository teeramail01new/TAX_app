import flet as ft
import os
from datetime import datetime
from PIL import Image
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tempfile
import json

try:
    from PyPDF2 import PdfReader, PdfWriter
except Exception:
    PdfReader = None
    PdfWriter = None


class FormPDFDesigner:
    def __init__(self, canvas_w=800, canvas_h=1131):  # A4 aspect preview (approx)
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.bg_pdf_path = None
        self.bg_preview_path = None
        self.textboxes = []
        self.selected_id = None

    def load_pdf(self, pdf_path: str) -> bool:
        try:
            doc = fitz.open(pdf_path)
            page = doc[0]
            scale = 2
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = img.resize((self.canvas_w, self.canvas_h))
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            img.save(tmp.name, "PNG")
            self.bg_preview_path = tmp.name
            self.bg_pdf_path = pdf_path
            doc.close()
            return True
        except Exception as e:
            print("load_pdf error:", e)
            return False

    def add_box(self, x, y, w=200, h=30, text="", font_size=12):
        box_id = (self.textboxes[-1]["id"] + 1) if self.textboxes else 1
        self.textboxes.append({
            "id": box_id,
            "x": x, "y": y, "w": w, "h": h,
            "text": text, "font": font_size,
            "selected": False
        })
        return box_id

    def select(self, box_id):
        self.selected_id = box_id
        for b in self.textboxes:
            b["selected"] = (b["id"] == box_id)

    def move(self, box_id, dx, dy):
        for b in self.textboxes:
            if b["id"] == box_id:
                b["x"] = max(0, min(self.canvas_w - b["w"], b["x"] + dx))
                b["y"] = max(0, min(self.canvas_h - b["h"], b["y"] + dy))
                break

    def overlay_pdf(self, width_pt, height_pt):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        c = canvas.Canvas(tmp.name, pagesize=(width_pt, height_pt))
        for b in self.textboxes:
            if not b["text"]:
                continue
            x = b["x"] * width_pt / self.canvas_w
            y = height_pt - (b["y"] * height_pt / self.canvas_h) - b["font"] - 3
            c.setFont("Helvetica", b["font"])
            c.drawString(x + 2, y, b["text"]) 
        c.save()
        return tmp.name

    def export_pdf(self, out_path: str):
        if self.bg_pdf_path and PdfReader and PdfWriter:
            try:
                reader = PdfReader(self.bg_pdf_path)
                page = reader.pages[0]
                box = page.mediabox
                w_pt, h_pt = float(box.width), float(box.height)
                overlay_path = self.overlay_pdf(w_pt, h_pt)
                over_reader = PdfReader(overlay_path)
                page.merge_page(over_reader.pages[0])
                writer = PdfWriter()
                writer.add_page(page)
                with open(out_path, "wb") as f:
                    writer.write(f)
                os.unlink(overlay_path)
                return True, f"Saved: {out_path}"
            except Exception as e:
                return False, f"Merge error: {e}"
        else:
            # Fallback using preview + draw
            try:
                c = canvas.Canvas(out_path, pagesize=A4)
                w_pt, h_pt = A4
                if self.bg_preview_path:
                    c.drawImage(self.bg_preview_path, 0, 0, w_pt, h_pt)
                for b in self.textboxes:
                    if b["text"]:
                        x = b["x"] * w_pt / self.canvas_w
                        y = h_pt - (b["y"] * h_pt / self.canvas_h) - b["font"] - 3
                        c.setFont("Helvetica", b["font"])
                        c.drawString(x + 2, y, b["text"])
                c.save()
                return True, f"Saved: {out_path}"
            except Exception as e:
                return False, f"ReportLab error: {e}"


def main(page: ft.Page):
    page.title = "Form PDF Drag&Drop"
    page.window_width = 1200
    page.window_height = 900
    page.scroll = ft.ScrollMode.AUTO

    app = FormPDFDesigner()
    status = ft.Text("พร้อมใช้งาน", color=ft.colors.GREEN_700)

    txt = ft.TextField(label="ข้อความ", value="ตัวอย่างข้อความ", width=250)
    w = ft.TextField(label="กว้าง(px)", value="200", width=120, keyboard_type=ft.KeyboardType.NUMBER)
    h = ft.TextField(label="สูง(px)", value="30", width=120, keyboard_type=ft.KeyboardType.NUMBER)
    fz = ft.TextField(label="ฟอนต์(pt)", value="12", width=120, keyboard_type=ft.KeyboardType.NUMBER)

    stack = ft.Stack(width=app.canvas_w, height=app.canvas_h)

    def rebuild():
        layers = []
        if app.bg_preview_path and os.path.exists(app.bg_preview_path):
            layers.append(ft.Image(src=app.bg_preview_path, width=app.canvas_w, height=app.canvas_h, fit=ft.ImageFit.COVER))
        for b in app.textboxes:
            border = ft.colors.RED_700 if b.get("selected") else ft.colors.BLUE_700
            def make_on_tap(id=b["id"]):
                return lambda e: (app.select(id), rebuild())
            def make_on_drag(id=b["id"]):
                return lambda e: (app.move(id, e.delta_x, e.delta_y), rebuild())
            layers.append(
                ft.GestureDetector(
                    content=ft.Container(
                        left=b["x"], top=b["y"], width=b["w"], height=b["h"],
                        bgcolor=ft.colors.WHITE,
                        border=ft.border.all(2, border),
                        content=ft.Text(b["text"], size=12)
                    ),
                    on_tap=make_on_tap(),
                    on_pan_update=make_on_drag(),
                )
            )
        stack.controls = layers
        page.update()

    def autoload_form():
        if os.path.exists("form.pdf"):
            if app.load_pdf("form.pdf"):
                status.value = "✅ โหลด form.pdf สำเร็จ"
                status.color = ft.colors.GREEN_700
                rebuild()
            else:
                status.value = "❌ โหลด form.pdf ไม่สำเร็จ"
                status.color = ft.colors.RED_700
            page.update()

    def pick_pdf(e):
        def on_res(res: ft.FilePickerResultEvent):
            if res.files:
                path = res.files[0].path
                if app.load_pdf(path):
                    status.value = f"✅ โหลด: {os.path.basename(path)}"
                    status.color = ft.colors.GREEN_700
                    rebuild()
                else:
                    status.value = "❌ โหลดไม่สำเร็จ"
                    status.color = ft.colors.RED_700
                page.update()
        picker = ft.FilePicker(on_result=on_res)
        page.overlay.append(picker)
        page.update()
        picker.pick_files(allowed_extensions=["pdf"], dialog_title="เลือก form.pdf")

    def add_box_click(e):
        try:
            _w, _h, _fz = int(w.value), int(h.value), int(fz.value)
        except ValueError:
            status.value = "❌ กรอกตัวเลขให้ถูกต้อง"
            status.color = ft.colors.RED_700
            page.update()
            return
        box_id = app.add_box((app.canvas_w - _w)//2, (app.canvas_h - _h)//2, _w, _h, txt.value, _fz)
        app.select(box_id)
        rebuild()
        status.value = f"✅ เพิ่ม Textbox #{box_id}"
        status.color = ft.colors.GREEN_700
        page.update()

    def save_changes(e):
        if app.selected_id is None:
            status.value = "❌ ยังไม่ได้เลือก Textbox"
            status.color = ft.colors.RED_700
            page.update()
            return
        for b in app.textboxes:
            if b["id"] == app.selected_id:
                b["text"] = txt.value
                b["w"] = int(w.value or b["w"]) 
                b["h"] = int(h.value or b["h"]) 
                b["font"] = int(fz.value or b["font"]) 
                break
        rebuild()
        status.value = "✅ อัปเดตแล้ว"
        status.color = ft.colors.GREEN_700
        page.update()

    def export_click(e):
        if not app.bg_pdf_path:
            status.value = "❌ กรุณาโหลด form.pdf ก่อน"
            status.color = ft.colors.RED_700
            page.update()
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = f"filled_{ts}.pdf"
        ok, msg = app.export_pdf(out)
        status.value = ("✅ " if ok else "❌ ") + msg
        status.color = ft.colors.GREEN_700 if ok else ft.colors.RED_700
        page.update()

    def save_layout(e):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"layout_{ts}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"bg": app.bg_pdf_path, "boxes": app.textboxes}, f, ensure_ascii=False, indent=2)
        status.value = f"✅ บันทึกเลย์เอาต์: {path}"
        status.color = ft.colors.GREEN_700
        page.update()

    def load_layout(e):
        def on_res(res: ft.FilePickerResultEvent):
            if res.files:
                path = res.files[0].path
                try:
                    data = json.load(open(path, "r", encoding="utf-8"))
                    bg = data.get("bg")
                    if bg and os.path.exists(bg):
                        app.load_pdf(bg)
                    app.textboxes = data.get("boxes", [])
                    app.selected_id = None
                    rebuild()
                    status.value = f"✅ โหลดเลย์เอาต์: {path}"
                    status.color = ft.colors.GREEN_700
                except Exception as ex:
                    status.value = f"❌ โหลดเลย์เอาต์ไม่สำเร็จ: {ex}"
                    status.color = ft.colors.RED_700
                page.update()
        picker = ft.FilePicker(on_result=on_res)
        page.overlay.append(picker)
        page.update()
        picker.pick_files(allowed_extensions=["json"], dialog_title="โหลดเลย์เอาต์")

    sidebar = ft.Container(
        width=360,
        content=ft.Column([
            ft.Text("ใช้ form.pdf เป็นพื้นหลัง", weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.ElevatedButton("เลือก form.pdf", icon=ft.icons.UPLOAD_FILE, on_click=pick_pdf),
            ]),
            ft.Divider(),
            ft.Text("Textbox", weight=ft.FontWeight.BOLD),
            txt,
            ft.Row([w, h], spacing=8),
            fz,
            ft.Row([
                ft.ElevatedButton("เพิ่ม Textbox", icon=ft.icons.ADD, on_click=add_box_click),
                ft.ElevatedButton("บันทึกการแก้ไข", icon=ft.icons.SAVE, on_click=save_changes),
            ], spacing=10),
            ft.Row([
                ft.ElevatedButton("ส่งออก PDF", icon=ft.icons.PICTURE_AS_PDF, on_click=export_click),
                ft.OutlinedButton("บันทึกเลย์เอาต์", icon=ft.icons.SAVE, on_click=save_layout),
                ft.OutlinedButton("โหลดเลย์เอาต์", icon=ft.icons.FOLDER_OPEN, on_click=load_layout),
            ], spacing=10, wrap=True),
            status,
        ], spacing=10),
    )

    page.add(ft.Row([sidebar, ft.Container(content=stack)], expand=True))
    if os.path.exists("form.pdf"):  # autoload
        autoload_form()


if __name__ == "__main__":
    print("Form PDF Drag&Drop - pip install flet pillow PyMuPDF reportlab PyPDF2")
    ft.app(target=main)
