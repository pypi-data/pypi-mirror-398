# mustafatik

مكتبة بايثون مساعدة لتوليد بيانات الأجهزة ووكلاء المستخدم (User-Agents) بشكل عشوائي ومحاكي للأجهزة الحقيقية.

## التثبيت

```bash
pip install mustafatik
```

## الاستخدام

```python
from mustafatik import mustafatik

# إنشاء كائن من المكتبة
device_generator = mustafatik()

# توليد بيانات جهاز عشوائية
device_data = device_generator._device()
print(device_data)
```

## المطور
مصطفى تليجرام: @PPH9P
