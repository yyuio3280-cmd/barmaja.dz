from flask import Flask, render_template, request, jsonify
import datetime
import os
from vercel_kv import KV

app = Flask(__name__)

# الاتصال التلقائي بقاعدة بيانات Vercel KV السحابية
try:
    kv = KV()
except Exception:
    kv = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    instagram = request.form.get('instagram', '').strip()

    # التحقق من أن المستخدم ملأ جميع الحقول
    if not first_name or not last_name or not instagram:
        return jsonify({'status': 'error', 'message': 'الرجاء ملء جميع الحقول المطلوب!'})

    # إزالة رمز @ إذا قام الطالب بكتابته تلقائيًا
    if instagram.startswith('@'):
        instagram = instagram[1:]

    try:
        # إذا كنا نقوم بالتجربة محليًا ولم نربط Vercel KV بعد، نستخدم ملف مؤقت تجريبي
        if kv is None:
            # طريقة تجريبية فقط للـ Localhost
            DATA_FILE = 'students_local_dev.txt'
            current_id = 1
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    current_id = len(f.readlines()) + 1
            
            formatted_id = f"{current_id:010d}"
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            record = f"ID: {formatted_id} | Name: {first_name} {last_name} | Insta: @{instagram} | Time: {current_time}\n"
            
            with open(DATA_FILE, 'a', encoding='utf-8') as f:
                f.write(record)
                
            return jsonify({'status': 'success', 'message': 'تم الحفظ محليًا (بيئة تجريبية)!', 'user_id': formatted_id})

        # --- البيئة الرسمية الحية على Vercel ---
        # 1. زيادة العداد التصاعدي بمقدار 1 في السحاب (يبدأ من 1 لو كان فارغًا)
        current_id = kv.incr('student_counter')
        
        # 2. تنسيق الرقم التعريفي ليصبح مكونًا من 10 خانات (مثال: 0000000001)
        formatted_id = f"{current_id:010d}"
        
        # 3. تسجيل توقيت العملية الحالي
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 4. حفظ بيانات الطالب بشكل منظم داخل الـ KV
        student_info = {
            'id': formatted_id,
            'name': f"{first_name} {last_name}",
            'instagram': f"@{instagram}",
            'registered_at': current_time
        }
        
        # تخزين البيانات بمفتاح فريد يعتمد على الرقم التعريفي للطالب
        kv.set(f"student:{formatted_id}", student_info)

        return jsonify({
            'status': 'success',
            'message': 'تم التسجيل بنجاح في قاعدة البيانات السحابية!',
            'user_id': formatted_id
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'خطأ في السيرفر أو قاعدة البيانات: {str(e)}'})
