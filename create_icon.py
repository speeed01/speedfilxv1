from PIL import Image, ImageDraw

# إنشاء صورة 512×512
img = Image.new('RGB', (512, 512), color='red')
draw = ImageDraw.Draw(img)

# رسم دائرة بيضاء
draw.ellipse([50, 50, 462, 462], fill='white')

# رسم مثلث أحمر (رمز التشغيل)
draw.polygon([(200, 150), (200, 362), (362, 256)], fill='red')

# حفظ الصورة
img.save('icon.png')
print("✅ تم إنشاء الأيقونة icon.png")
