from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import os
import uuid
import re
from PIL import Image, ImageEnhance
import pytesseract
import fitz  

app = Flask(__name__)

BASE_DIR = '/home/HOMINCHOI/mysite'
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'receipts.db')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS receipts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  category TEXT, name TEXT, spent_amount INTEGER, 
                  support_cost INTEGER, people_count INTEGER, 
                  image_filename TEXT, date TEXT)''')
    
    # 순차적 업데이트
    try: c.execute("ALTER TABLE receipts ADD COLUMN purpose TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass 
    try: c.execute("ALTER TABLE receipts ADD COLUMN is_settled INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass 
    try: c.execute("ALTER TABLE receipts ADD COLUMN team TEXT DEFAULT '미지정'")
    except sqlite3.OperationalError: pass 
    try: c.execute("ALTER TABLE receipts ADD COLUMN has_hardcopy INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass 
    # 🚀 총무 전용 메모 컬럼 추가
    try: c.execute("ALTER TABLE receipts ADD COLUMN memo TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass 

    c.execute('''CREATE TABLE IF NOT EXISTS incomes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT, source TEXT, amount INTEGER)''')

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ocr-scan', methods=['POST'])
def ocr_scan():
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "파일이 첨부되지 않았습니다."}), 400
    
    file = request.files['image']
    
    try:
        filename = file.filename.lower()
        extracted_text = ""
        
        if filename.endswith('.pdf'):
            doc = fitz.open(stream=file.read(), filetype="pdf")
            for page in doc:
                extracted_text += page.get_text()
        else:
            img = Image.open(file.stream)
            img.thumbnail((800, 800))
            img = img.convert('L')
            img = img.point(lambda x: 0 if x < 140 else 255, '1')
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789,-./'
            extracted_text = pytesseract.image_to_string(img, lang='eng', config=custom_config)
        
        numbers = re.findall(r'\b\d{1,3}(?:,\d{3})+|\b\d{4,7}', extracted_text)
        parsed_amounts = []
        for num in numbers:
            clean_num = int(num.replace(',', ''))
            if 1000 <= clean_num <= 4200000:
                parsed_amounts.append(clean_num)
                
        date_pattern = r'(20[12]\d)[-./\s]+(\d{1,2})[-./\s]+(\d{1,2})'
        date_match = re.search(date_pattern, extracted_text)
        detected_date = ""
        if date_match:
            y, m, d = date_match.groups()
            detected_date = f"{y}-{int(m):02d}-{int(d):02d}"

        return jsonify({
            "status": "success",
            "raw_text": extracted_text,
            "detected_amounts": parsed_amounts,
            "detected_date": detected_date
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_receipt():
    team = request.form.get('team', '')
    category = request.form.get('category', '')
    purpose = request.form.get('purpose', '')
    name = request.form.get('name')
    spent_amount = int(request.form.get('spentAmount'))
    support_cost = int(request.form.get('supportCost'))
    people_count = int(request.form.get('peopleCount', 0))
    file = request.files.get('image')

    filename = ""
    if file:
        ext = file.filename.split('.')[-1]
        filename = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    date_str = request.form.get('date')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO receipts 
                 (team, category, purpose, name, spent_amount, support_cost, people_count, image_filename, date, is_settled, has_hardcopy, memo) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, '')""",
              (team, category, purpose, name, spent_amount, support_cost, people_count, filename, date_str))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success"})

@app.route('/api/receipts', methods=['GET'])
def get_receipts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # memo 열까지 가져오도록 SELECT 수정
    c.execute("SELECT id, team, category, purpose, name, spent_amount, support_cost, people_count, image_filename, date, is_settled, has_hardcopy, memo FROM receipts ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    receipts = []
    for r in rows:
        receipts.append({
            "id": r[0], "team": r[1], "category": r[2], "purpose": r[3], "name": r[4], 
            "spentAmount": r[5], "supportCost": r[6], 
            "peopleCount": r[7], "imageUrl": f"/uploads/{r[8]}" if r[8] else "",
            "date": r[9], "isSettled": bool(r[10]), "hasHardcopy": bool(r[11]),
            "memo": r[12] if r[12] else ""
        })
    return jsonify(receipts)

@app.route('/api/receipts/<int:receipt_id>', methods=['PUT'])
def update_receipt_all(receipt_id):
    data = request.json
    team = data.get('team')
    category = data.get('category')
    purpose = data.get('purpose')
    name = data.get('name')
    spent_amount = int(data.get('spent_amount', 0))
    people_count = int(data.get('people_count', 0))
    date_val = data.get('date')
    memo = data.get('memo', '') # 🚀 메모 수정값 받기

    support_cost = spent_amount
    if category == '모임지원비' and spent_amount > people_count * 12000:
        support_cost = people_count * 12000

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""UPDATE receipts 
                 SET team = ?, category = ?, purpose = ?, name = ?, spent_amount = ?, support_cost = ?, people_count = ?, date = ?, memo = ?
                 WHERE id = ?""", 
              (team, category, purpose, name, spent_amount, support_cost, people_count, date_val, memo, receipt_id))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success"})

@app.route('/api/receipts/<int:receipt_id>/settle', methods=['PUT'])
def update_receipt_settle(receipt_id):
    is_settled = request.json.get('is_settled')
    settled_val = 1 if is_settled else 0
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE receipts SET is_settled = ? WHERE id = ?", (settled_val, receipt_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/receipts/<int:receipt_id>/hardcopy', methods=['PUT'])
def update_receipt_hardcopy(receipt_id):
    has_hardcopy = request.json.get('has_hardcopy')
    hardcopy_val = 1 if has_hardcopy else 0
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE receipts SET has_hardcopy = ? WHERE id = ?", (hardcopy_val, receipt_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/receipts/<int:receipt_id>', methods=['DELETE'])
def delete_receipt(receipt_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT image_filename FROM receipts WHERE id = ?", (receipt_id,))
    row = c.fetchone()
    if row and row[0]:
        image_path = os.path.join(UPLOAD_FOLDER, row[0])
        if os.path.exists(image_path):
            os.remove(image_path)
            
    c.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/incomes', methods=['GET'])
def get_incomes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, date, source, amount FROM incomes ORDER BY date DESC, id DESC")
    rows = c.fetchall()
    conn.close()
    incomes = [{"id": r[0], "date": r[1], "source": r[2], "amount": r[3]} for r in rows]
    return jsonify(incomes)

@app.route('/api/incomes', methods=['POST'])
def add_income():
    data = request.json
    date_val = data.get('date')
    source = data.get('source')
    amount = int(data.get('amount', 0))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO incomes (date, source, amount) VALUES (?, ?, ?)", (date_val, source, amount))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/incomes/<int:income_id>', methods=['DELETE'])
def delete_income(income_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM incomes WHERE id = ?", (income_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)