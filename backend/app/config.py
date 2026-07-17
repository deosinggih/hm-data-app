from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "hm_app.db"
SEED_FORM_HM = Path.home() / "Downloads" / "form HM.xlsx"

HM_POS_PATTERNS = ("DATA HM POS", "DATA HM")
STATUS_PATTERNS = ("STATUS",)
PO_UNIT_PATTERNS = ("PO UNIT", "MASTER PO", "PO")

BULAN_ID_PANJANG = (
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
)
HARI_ID = ("Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu")

FM_KEYS = (
    "RAIN", "SLIPPERY", "NO JOB", "FRONT PREPARATION",
    "DUMPING PREPARATION", "ROAD MAINTENANCE", "WAITING BLASTING",
)
POT_Z_EXCLUDE_KEYWORDS = ("HM ERROR", "HM SERAP", "GANTI UNIT", "SALAH INPUT")
JAM_PER_SHIFT = 12.0
MAX_STBY_PER_SHIFT = 2.0

COMPANY_NAME = "PT. Kayong Aluminium Nusantara"
COMPANY_ADDRESS_LINE1 = (
    "Gedung Bank Panin Lantai 2, Jalan Jendral Sudirman No. Kav 1, "
    "RT / RW 3, Kelurahan Gelora"
)
COMPANY_ADDRESS_LINE2 = (
    "Kecamatan Tanah Abang, Jakarta Pusat, Provinsi Daerah Khusus "
    "Ibukota Jakarta - 10270 Telp : (021) 7251344"
)

# Columns marked Input in form HM.xlsx (row 1)
INPUT_COLUMNS = [
    "DATE", "SHIFT", "VENDOR", "CODE UNIT", "HM START", "HM STOP",
    "HOURS START", "HOURS STOP", "JAM BD", "JAM STANDBY", "RITASE",
    "Fuel", "HM Pengisian", "LOCATED", "JOB DESCRIPTION",
    "OPERATORE NAME", "Keterangan", "EXP. DIFFERENCE",
]

EXP_DIFFERENCE_OPTIONS = [
    "", "HM Error", "HM Serap Unit", "Ganti Unit", "Salah Input",
]