import subprocess
import sys
import os
import shutil

EXE_NAME    = "installer_DETROIT_UZBEK"
MAIN_SCRIPT = "installer.py"
ICON_FILE   = "icon.ico"
BG_IMAGE    = "background.png"
AVATAR_FILE = "Muhammadsaid.png"

FAYL_D30    = "BigFile_PC.d30"
FAYL_IDX    = "BigFile_PC.idx"

EXTRA_IMAGES = [
    "telegram.png",
    "youtube.png",
    "phone.png",
    "install.png",
    "restore.png",
]

EXTRA_FILES = [
    "README(Majburiy).txt",
]

PYSIDE6_HIDDEN = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtNetwork",
]


def check_pkg(import_name):
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def install_pkg(pip_name):
    print(f"  ? {pip_name} o'rnatilmoqda...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "-q"])


def file_mb(path):
    return os.path.getsize(path) / 1024 / 1024


def add_data_arg(src, dest="."):
    return f"--add-data={src}{os.pathsep}{dest}"


print("=" * 56)
print("  Detroit Uzbek Mod — PySide6 Single .exe Builder")
print("  (ONEFILE mode — Yagona mustaqil .exe)")
print("=" * 56)

packages = {
    "pyinstaller": "pyinstaller",
    "PySide6":     "PySide6",
}
for import_name, pip_name in packages.items():
    if not check_pkg(import_name):
        install_pkg(pip_name)
    else:
        print(f"  v {pip_name} mavjud")

print()
missing_critical = []
for f in [MAIN_SCRIPT, BG_IMAGE, FAYL_D30, FAYL_IDX]:
    if not os.path.exists(f):
        missing_critical.append(f)
        print(f"  x TOPILMADI (ZARURIY): {f}")
    else:
        print(f"  v {f}  ({file_mb(f):.1f} MB)")

has_icon   = os.path.exists(ICON_FILE)
has_avatar = os.path.exists(AVATAR_FILE)

icon_status   = "(mavjud)" if has_icon   else "(yo'q — icon olmaydi)"
avatar_status = "(mavjud)" if has_avatar else "(yo'q — avatar ko'rinmaydi)"
icon_mark     = "v" if has_icon   else "!"
avatar_mark   = "v" if has_avatar else "!"

print(f"  {icon_mark} {ICON_FILE}   {icon_status}")
print(f"  {avatar_mark} {AVATAR_FILE}  {avatar_status}")

for img in EXTRA_IMAGES:
    status = "(mavjud)" if os.path.exists(img) else "(yo'q)"
    mark   = "v"       if os.path.exists(img) else "!"
    print(f"  {mark} {img}  {status}")

for ef in EXTRA_FILES:
    status = "(mavjud)" if os.path.exists(ef) else "(yo'q — README ochilmaydi)"
    mark   = "v"       if os.path.exists(ef) else "!"
    print(f"  {mark} {ef}  {status}")

if missing_critical:
    print(f"\n  x Quyidagi zaruriy fayllar yo'q: {missing_critical}")
    input("  Enter bosing...")
    sys.exit(1)

print("\n  ? Eski build tozalanmoqda...")
dist_exe = os.path.join("dist", f"{EXE_NAME}.exe")
if os.path.exists("build"):
    shutil.rmtree("build", ignore_errors=True)
if os.path.exists(dist_exe):
    os.remove(dist_exe)

spec_file = f"{EXE_NAME}.spec"
if os.path.exists(spec_file):
    os.remove(spec_file)

add_data = [
    add_data_arg(BG_IMAGE),
    add_data_arg(FAYL_D30),
    add_data_arg(FAYL_IDX),
]
if has_icon:
    add_data.append(add_data_arg(ICON_FILE))
if has_avatar:
    add_data.append(add_data_arg(AVATAR_FILE))
for img in EXTRA_IMAGES:
    if os.path.exists(img):
        add_data.append(add_data_arg(img))
for ef in EXTRA_FILES:
    if os.path.exists(ef):
        add_data.append(add_data_arg(ef))

icon_arg = [f"--icon={ICON_FILE}"] if has_icon else []

hidden = [f"--hidden-import={h}" for h in PYSIDE6_HIDDEN]

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onefile",
    "--windowed",
    f"--name={EXE_NAME}",
    *icon_arg,
    *add_data,
    *hidden,
    "--collect-all=PySide6",
    "--clean",
    MAIN_SCRIPT,
]

print("  ? PyInstaller yagona .exe faylga siqib yig'moqda...")
print("  (Fayllarni bitta paketga siqish tufayli 1-3 daqiqa vaqt olishi mumkin)\n")
result = subprocess.run(cmd)

if result.returncode == 0:
    if os.path.exists(dist_exe):
        exe_size = file_mb(dist_exe)

        print("\n" + "=" * 56)
        print(f"  v  MUVAFFAQIYATLI!")
        print(f"  Fayl : dist\\{EXE_NAME}.exe")
        print(f"  Hajm : {exe_size:.1f} MB")
        print("=" * 56)
        print(f"""
  TARQATISH:
  ----------------------------------------------------------
  dist\\ papkasi ichidagi {EXE_NAME}.exe faylini 
  to'g'ridan-to'g'ri foydalanuvchilarga berishingiz mumkin. 
  
  Hech qanday ZIP yoki qo'shimcha papka shart emas!
  ----------------------------------------------------------
""")
    else:
        print("\n  !  Build tugadi lekin dist\\ ichida .exe fayl topilmadi.")
else:
    print("\n  x  Build xato bilan tugadi.")

input("\n  Enter bosing...")