# TikTok Signature Generator

هذا المشروع عبارة عن مكتبة بايثون لإنشاء توقيعات **x-gorgon** و **x-argus** الخاصة بتطبيق TikTok.  
المكتبة مفيدة لمحاكاة طلبات API الخاصة بـ TikTok باستخدام Python.

---

## الميزات

- إنشاء توقيع **x-gorgon** باستخدام كلاس `Gorgon`.
- إنشاء توقيع **x-argus** باستخدام كلاس `Argus`.
- دعم التواقيع على الطلبات GET و POST.
- سهولة تمرير `params`, `cookies`, `data`, و `payload`.
- إنشاء **x-ss-stub** تلقائيًا من بيانات الطلب.

---

## الملفات الرئيسية

- `TikSign.py` - يحتوي على كل الكلاسات والدوال لإنشاء التواقيع.


---

## المتطلبات

- Python 3.8 أو أعلى
- مكتبات بايثون:
  ```bash
  pip install uuid pycryptodome
