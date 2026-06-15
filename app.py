from flask import Flask, render_template, request, jsonify
import datetime
import os

# تعريف التطبيق (مهم جداً لـ Vercel)
app = Flask(__name__)

# محاولة استدعاء مكتبة قاعدة البيانات
try:
    from vercel_storage import kv
    # تحقق بسيط للتأكد من وجود الإعدادات في Vercel
    if not os.environ.get("VERCEL_KV_URL"):
        kv = None
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

    if not first_name or not last_name or not instagram:
        return jsonify({'status': 'error', 'message': 'الرجاء ملء جميع الحقول المطلوبة!'})

    if instagram.startswith('@'):
        instagram = instagram[1:]

    # توقيت التسجيل الحالي
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. إذا كانت قاعدة البيانات متصلة وجاهزة على Vercel
    if kv is not None:
        try:
            current_id = kv.incr('student_counter')
            formatted_id = f"{current_id:010d}"
            
            student_info = {
                'id': formatted_id,
                'name': f"{first_name} {last_name}",
                'instagram': f"@{instagram}",
                'registered_at': current_time
            }
            kv.set(f"student:{formatted_id}", student_info)
            
            return jsonify({
                'status': 'success',
                'message': 'تم التسجيل في قاعدة البيانات!',
                'user_id': formatted_id
            })
        except Exception as e:
            # إذا فشل الاتصال بالـ KV لسبب ما، ننتقل للحل البديل بالأسفل
            pass

    # 2. الحل البديل (في حال عدم ربط Storage أو التشغيل المحلي)
    DATA_FILE = '/tmp/students_local.txt' if os.environ.get('VERCEL') else 'students_local.txt'
    current_id = 1
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                current_id = len(f.readlines()) + 1
        except Exception:
            current_id = 1
            
    formatted_id = f"{current_id:010d}"
    record = f"ID: {formatted_id} | Name: {first_name} {last_name} | Insta: @{instagram} | Time: {current_time}\n"
    
    try:
        with open(DATA_FILE, 'a', encoding='utf-8') as f:
            f.write(record)
    except Exception:
        pass
        
    return jsonify({
        'status': 'success', 
        'message': 'تم التسجيل بنجاح!', 
        'user_id': formatted_id
    })

# هذا السطر ضروري لـ Vercel ليعرف أين يتوجه
app.index = app
