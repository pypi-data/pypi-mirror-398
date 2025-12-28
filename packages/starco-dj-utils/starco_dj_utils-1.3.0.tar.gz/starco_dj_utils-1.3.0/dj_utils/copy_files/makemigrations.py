import os
import subprocess
import sys

def build_migrations():
    # 1️⃣ ست کردن محیط build
    os.environ["DJANGO_ENV"] = "build"

    # 2️⃣ اطمینان از مسیر پروژه
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.chdir(BASE_DIR)

    # 3️⃣ اجرای دستور makemigrations با subprocess
    try:
        print("🔧 Starting makemigrations in build environment...")
        subprocess.check_call([sys.executable, "manage.py", "makemigrations"])
        print("✅ Migrations created successfully!")
    except subprocess.CalledProcessError as e:
        print("❌ Error while making migrations:", e)
        sys.exit(1)


if __name__ == "__main__":
    build_migrations()
