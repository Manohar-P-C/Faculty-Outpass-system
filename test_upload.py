import os
from app import app, save_photo, get_db
import werkzeug.datastructures
from io import BytesIO

# Create a dummy image
img_content = b"fake image content"
file = werkzeug.datastructures.FileStorage(
    stream=BytesIO(img_content),
    filename="manohar.jpeg",
    name="photo",
    content_type="image/jpeg",
)

with app.app_context():
    photo = save_photo({"photo": file}, "photo")
    print(f"Saved photo as: {photo}")
    
    if photo:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE faculty SET photo=%s WHERE email=%s", (photo, "manohar472007@gmail.com"))
        conn.commit()
        print("Updated database")
        cursor.close()
        conn.close()
