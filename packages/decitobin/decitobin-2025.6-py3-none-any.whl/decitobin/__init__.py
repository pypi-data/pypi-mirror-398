import tkinter as tk
from tkinter import ttk

# Conversion functions
def dec2bin(n): return bin(int(n))[2:]
def bin2dec(b): return str(int(b, 2))
def hex2bin(h): return bin(int(h, 16))[2:].zfill(len(h)*4)
def bin2hex(b): return hex(int(b, 2))[2:].upper()
def ascii2bin(t): return ' '.join(bin(ord(c))[2:].zfill(8) for c in t)
def bin2ascii(b):
    chunks = b.split() if ' ' in b else [b[i:i+8] for i in range(0, len(b), 8)]
    return ''.join(chr(int(c, 2)) for c in chunks if len(c) == 8)
def dec2hex(n): return hex(int(n))[2:].upper()
def hex2dec(h): return str(int(h, 16))
def bin2oct(b): return oct(int(b, 2))[2:]
def oct2bin(o): return bin(int(o, 8))[2:]

# Decimal → Base-12
def dec2duodec(n):
    digits = "0123456789AB"  # hệ 12 dùng A=10, B=11
    n = int(n)
    if n == 0:
        return "0"
    result = ""
    while n > 0:
        result = digits[n % 12] + result
        n //= 12
    return result

# Base-12 → Decimal
def duodec2dec(d):
    digits = "0123456789AB"
    d = d.upper()
    value = 0
    for char in d:
        if char not in digits:
            raise ValueError("Ký tự không hợp lệ cho hệ 12")
        value = value * 12 + digits.index(char)
    return str(value)

# Conversion handler
def convert():
    mode = mode_select.get()
    data = input_field.get("1.0", tk.END).strip()

    try:
        if mode == "Decimal → Binary": result.set(dec2bin(data))
        elif mode == "Binary → Decimal": result.set(bin2dec(data))
        elif mode == "Hex → Binary": result.set(hex2bin(data))
        elif mode == "Binary → Hex": result.set(bin2hex(data))
        elif mode == "ASCII → Binary": result.set(ascii2bin(data))
        elif mode == "Binary → ASCII": result.set(bin2ascii(data))
        elif mode == "Decimal → Hex": result.set(dec2hex(data))
        elif mode == "Hex → Decimal": result.set(hex2dec(data))
        elif mode == "Binary → Octal": result.set(bin2oct(data))
        elif mode == "Octal → Binary": result.set(oct2bin(data))
        elif mode == "Decimal → Duodecimal": result.set(dec2duodec(data))
        elif mode == "Duodecimal → Decimal": result.set(duodec2dec(data))
        else: result.set("⚠️ Chọn kiểu chuyển đổi")
    except:
        result.set("⚠️ Đầu vào không hợp lệ")

# GUI setup
root = tk.Tk()
root.title("decitobin WebStyle 🧒🔢")
root.geometry("600x460")
root.configure(bg="#f2f2f2")

tk.Label(root, text="🔢 Data input:", font=("Segoe UI", 12), bg="#f2f2f2").pack(pady=(20,5))
input_field = tk.Text(root, height=3, width=60, font=("Consolas", 12))
input_field.pack()

tk.Label(root, text="🔀 Choose base:", font=("Segoe UI", 12), bg="#f2f2f2").pack(pady=5)
mode_select = ttk.Combobox(root, values=[
    "Decimal → Binary", "Binary → Decimal",
    "Hex → Binary", "Binary → Hex",
    "ASCII → Binary", "Binary → ASCII",
    "Decimal → Hex", "Hex → Decimal",
    "Binary → Octal", "Octal → Binary",
    "Decimal → Duodecimal", "Duodecimal → Decimal"
], state="readonly", font=("Segoe UI", 11))
mode_select.set("Decimal → Binary")
mode_select.pack()

tk.Button(root, text="📋 Copy Output", font=("Segoe UI", 12),
          command=lambda: root.clipboard_clear() or root.clipboard_append(result.get())).pack(pady=5)

tk.Button(root, text="➡️ Convert", font=("Segoe UI", 12), command=convert).pack(pady=10)

tk.Label(root, text="📤 Output:", font=("Segoe UI", 12), bg="#f2f2f2").pack()
output = tk.Label(root, textvariable=(result := tk.StringVar()), bg="#fff", fg="blue",
                  font=("Consolas", 12), wraplength=560, justify="left",
                  relief="solid", padx=10, pady=10)
output.pack(pady=5, fill=tk.X, padx=20)

root.mainloop()