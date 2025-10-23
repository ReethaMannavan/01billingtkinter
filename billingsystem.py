import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os
import pandas as pd

DB_NAME = "billing.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            date TEXT,
            total REAL,
            gst REAL,
            grand_total REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            item_name TEXT,
            qty INTEGER,
            price REAL,
            total REAL,
            FOREIGN KEY(invoice_id) REFERENCES invoices(invoice_id)
        )
    """)
    conn.commit()
    conn.close()


class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Billing & Invoice Management System - Trendy Gadgets")
        self.root.geometry("1100x700")
        self.root.configure(bg="#f5f6fa")
        self.items = []

        # ---------- HEADER ---------- #
        title = tk.Label(root, text="🧾 Billing & Invoice Management System",
                         font=("Segoe UI", 22, "bold"), bg="#004aad", fg="white", pady=15)
        title.pack(fill="x")

        # ---------- CUSTOMER DETAILS ---------- #
        frame1 = tk.Frame(root, bg="#f5f6fa")
        frame1.pack(fill="x", pady=15)
        tk.Label(frame1, text="Customer Name:", font=("Segoe UI", 12), bg="#f5f6fa").grid(row=0, column=0, padx=10, sticky="e")
        self.customer_entry = tk.Entry(frame1, font=("Segoe UI", 12), width=35, justify="center")
        self.customer_entry.grid(row=0, column=1, padx=10)

        # ---------- ITEM ENTRY ---------- #
        frame2 = tk.Frame(root, bg="#f5f6fa")
        frame2.pack(fill="x", pady=15)
        tk.Label(frame2, text="Item Name", font=("Segoe UI", 12, "bold"), bg="#f5f6fa").grid(row=0, column=0, padx=10)
        tk.Label(frame2, text="Qty", font=("Segoe UI", 12, "bold"), bg="#f5f6fa").grid(row=0, column=1, padx=10)
        tk.Label(frame2, text="Price", font=("Segoe UI", 12, "bold"), bg="#d1e7ff", relief="ridge", width=10).grid(row=0, column=2, padx=10)

        self.item_name = tk.Entry(frame2, font=("Segoe UI", 12), justify="center", width=25)
        self.item_qty = tk.Entry(frame2, font=("Segoe UI", 12), justify="center", width=10)
        self.item_price = tk.Entry(frame2, font=("Segoe UI", 12), justify="center", width=10, bg="#e8f4ff")

        self.item_name.grid(row=1, column=0, padx=10, pady=5)
        self.item_qty.grid(row=1, column=1, padx=10, pady=5)
        self.item_price.grid(row=1, column=2, padx=10, pady=5)

        tk.Button(frame2, text="Add Item", command=self.add_item, bg="#004aad", fg="white",
                  font=("Segoe UI", 11, "bold"), width=14).grid(row=1, column=3, padx=10)

        # ---------- ITEM TABLE ---------- #
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), anchor="center")
        style.configure("Treeview", font=("Segoe UI", 11), rowheight=28)
        self.tree = ttk.Treeview(root, columns=("Item", "Qty", "Price", "Total"), show="headings", height=10)
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(pady=15, fill="x", padx=20)

        # ---------- TOTALS ---------- #
        frame3 = tk.Frame(root, bg="#f5f6fa")
        frame3.pack(fill="x", pady=10)
        self.subtotal_var = tk.StringVar(value="0.00")
        self.gst_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")

        tk.Label(frame3, text="Subtotal:", font=("Segoe UI", 12), bg="#f5f6fa").grid(row=0, column=0, padx=10)
        tk.Entry(frame3, textvariable=self.subtotal_var, state="readonly", width=15, justify="center").grid(row=0, column=1)
        tk.Label(frame3, text="GST (18%):", font=("Segoe UI", 12), bg="#f5f6fa").grid(row=0, column=2, padx=10)
        tk.Entry(frame3, textvariable=self.gst_var, state="readonly", width=15, justify="center").grid(row=0, column=3)
        tk.Label(frame3, text="Grand Total:", font=("Segoe UI", 12, "bold"), bg="#f5f6fa").grid(row=0, column=4, padx=10)
        tk.Entry(frame3, textvariable=self.total_var, state="readonly", width=15,
                 font=("Segoe UI", 12, "bold"), justify="center").grid(row=0, column=5)

        # ---------- BUTTONS ---------- #
        frame4 = tk.Frame(root, bg="#f5f6fa")
        frame4.pack(fill="x", pady=15)
        btns = [
            ("Save Invoice", self.save_invoice, "#28a745"),
            ("Generate PDF", self.generate_pdf, "#007bff"),
            ("Sales Report", self.view_sales_report, "#6f42c1"),
            ("Clear", self.clear_all, "#dc3545")
        ]
        for i, (text, cmd, color) in enumerate(btns):
            tk.Button(frame4, text=text, command=cmd, bg=color, fg="white",
                      font=("Segoe UI", 11, "bold"), width=18).grid(row=0, column=i, padx=10)

    # ---------------- CORE FUNCTIONS ---------------- #
    def add_item(self):
        name, qty, price = self.item_name.get(), self.item_qty.get(), self.item_price.get()
        if not (name and qty and price):
            messagebox.showwarning("Input Error", "Please enter all item details.")
            return
        try:
            qty, price = int(qty), float(price)
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity or price format.")
            return

        total = qty * price
        self.items.append((name, qty, price, total))
        self.tree.insert("", "end", values=(name, qty, f"{price:.2f}", f"{total:.2f}"))
        self.update_totals()

        self.item_name.delete(0, tk.END)
        self.item_qty.delete(0, tk.END)
        self.item_price.delete(0, tk.END)

    def update_totals(self):
        subtotal = sum(i[3] for i in self.items)
        gst = subtotal * 0.18
        total = subtotal + gst
        self.subtotal_var.set(f"{subtotal:.2f}")
        self.gst_var.set(f"{gst:.2f}")
        self.total_var.set(f"{total:.2f}")

    def save_invoice(self):
        if not self.items:
            messagebox.showwarning("No Items", "Add items before saving invoice.")
            return
        customer = self.customer_entry.get() or "Walk-in Customer"
        date = datetime.now().strftime("%Y-%m-%d")
        subtotal, gst, grand_total = map(float, (self.subtotal_var.get(), self.gst_var.get(), self.total_var.get()))

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO invoices (customer_name, date, total, gst, grand_total) VALUES (?, ?, ?, ?, ?)",
                    (customer, date, subtotal, gst, grand_total))
        invoice_id = cur.lastrowid
        for item in self.items:
            cur.execute("INSERT INTO items (invoice_id, item_name, qty, price, total) VALUES (?, ?, ?, ?, ?)",
                        (invoice_id, item[0], item[1], item[2], item[3]))
        conn.commit()
        conn.close()
        messagebox.showinfo("Saved", f"Invoice #{invoice_id} saved successfully.")
        self.generate_pdf(invoice_id)

    def generate_pdf(self, invoice_id=None):
        if not self.items:
            messagebox.showwarning("No Items", "Add items before generating invoice.")
            return
        invoice_id = invoice_id or "TEMP"
        file_name = f"Invoice_{invoice_id}.pdf"
        file_path = os.path.join(os.getcwd(), file_name)

        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # Header
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width / 2, height - 80, "INVOICE")

        # Company Info
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 110, "Trendy Gadgets")
        c.drawString(50, height - 125, "13, North Street, Chennai, India")
        c.drawString(50, height - 140, "Phone: +91 9876543210 | Email: info@trendy.com")

        # Invoice Info
        c.drawRightString(width - 50, height - 110, f"Invoice No: {invoice_id}")
        c.drawRightString(width - 50, height - 125, f"Date: {datetime.now().strftime('%d-%m-%Y')}")

        # Table Header
        y = height - 180
        c.setFillColor(colors.lightgrey)
        c.rect(45, y - 15, width - 90, 20, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 11)
        headers = ["Item", "Qty", "Price", "Total"]
        x_positions = [60, 270, 370, 470]
        for i, header in enumerate(headers):
            c.drawString(x_positions[i], y - 5, header)

        # Table Rows
        c.setFont("Helvetica", 10)
        y -= 30
        for item in self.items:
            c.drawString(60, y, item[0])
            c.drawRightString(320, y, str(item[1]))
            c.drawRightString(420, y, f"{item[2]:.2f}")
            c.drawRightString(520, y, f"{item[3]:.2f}")
            y -= 20

        # Totals
        y -= 10
        c.line(50, y, width - 50, y)
        y -= 20
        c.drawRightString(470, y, "Subtotal:")
        c.drawRightString(520, y, f"{float(self.subtotal_var.get()):.2f}")
        y -= 20
        c.drawRightString(470, y, "GST (18%):")
        c.drawRightString(520, y, f"{float(self.gst_var.get()):.2f}")
        y -= 20
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(470, y, "Grand Total:")
        c.drawRightString(520, y, f"{float(self.total_var.get()):.2f}")

        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(width / 2, 50, "Thank you for your business!")

        c.save()
        messagebox.showinfo("PDF Generated", f"Invoice saved as {file_name}")

    def view_sales_report(self):
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM invoices", conn)
        conn.close()
        if df.empty:
            messagebox.showinfo("No Data", "No invoices found.")
            return
        today = datetime.now().strftime("%Y-%m-%d")
        month = datetime.now().strftime("%Y-%m")
        daily = df[df['date'] == today]['grand_total'].sum()
        monthly = df[df['date'].str.startswith(month)]['grand_total'].sum()
        report_text = f"Daily Sales ({today}): ₹{daily:.2f}\nMonthly Sales ({month}): ₹{monthly:.2f}"
        messagebox.showinfo("Sales Report", report_text)
        df.to_excel("Sales_Report.xlsx", index=False)
        messagebox.showinfo("Exported", "Full sales report saved as Sales_Report.xlsx")

    def clear_all(self):
        self.customer_entry.delete(0, tk.END)
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.items.clear()
        self.update_totals()


if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()
