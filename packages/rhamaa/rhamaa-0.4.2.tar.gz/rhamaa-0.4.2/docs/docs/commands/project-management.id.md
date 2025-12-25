# Manajemen Proyek

Rhamaa CLI menyediakan perintah yang powerful untuk membuat dan mengelola proyek Wagtail. Bagian ini mencakup semua perintah terkait proyek dan penggunaannya.

## Membuat Proyek Baru

### `rhamaa start`

Buat proyek Wagtail baru menggunakan template RhamaaCMS.

```bash
rhamaa start <NamaProyek>
```

**Contoh:**
```bash
rhamaa start BlogSaya
```

#### Apa yang dilakukan:

1. **Download Template**: Mengambil template RhamaaCMS terbaru dari GitHub
2. **Membuat Proyek**: Menggunakan perintah `start` Wagtail dengan template
3. **Setup Struktur**: Mengkonfigurasi proyek dengan best practices RhamaaCMS
4. **Memberikan Feedback**: Menampilkan progress dan konfirmasi sukses

#### Fitur Template:

Template RhamaaCMS mencakup:

- **Setup Django/Wagtail Modern**: Versi terbaru dan best practices
- **Struktur Terorganisir**: Organisasi app yang logis dan manajemen settings
- **Development Tools**: Dependensi development yang sudah dikonfigurasi
- **Production Ready**: Settings untuk deployment dan scaling
- **Dokumentasi**: README dan instruksi setup

### Struktur Proyek

Ketika Anda membuat proyek dengan `rhamaa start`, Anda mendapatkan:

```
ProyekSaya/
├── ProyekSaya/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/                    # Direktori untuk custom apps
├── static/                  # File static
├── media/                   # File media
├── templates/               # File template
├── requirements.txt         # Dependensi Python
├── manage.py               # Script manajemen Django
└── README.md               # Dokumentasi proyek
```

## Membuat Django Apps

### `rhamaa startapp`

Buat Django app baru dengan struktur RhamaaCMS dalam proyek Anda.

```bash
rhamaa startapp <NamaApp>
```

**Contoh:**
```bash
rhamaa startapp blog
```

#### Fitur:

- **Layout Terstruktur**: Membuat apps di direktori `apps/`
- **Standar RhamaaCMS**: Mengikuti konvensi app RhamaaCMS
- **Siap Pakai**: Termasuk setup model, view, dan admin dasar

## Validasi Proyek

Rhamaa CLI secara otomatis memvalidasi environment proyek Anda:

### Deteksi Proyek Wagtail

Sebelum mengizinkan operasi tertentu, Rhamaa CLI memeriksa apakah Anda berada di proyek Wagtail yang valid dengan mencari:

- File `manage.py`
- File settings Django
- Indikator proyek umum

### Error Handling

Jika Anda tidak berada di proyek Wagtail, Anda akan melihat:

```
Error: This doesn't appear to be a Wagtail project.
Please run this command from the root of your Wagtail project.
```

## Best Practices

### Penamaan Proyek

- Gunakan **PascalCase** untuk nama proyek: `BlogSaya`, `WebsitePerusahaan`
- Hindari spasi dan karakter khusus
- Buat nama yang deskriptif tapi ringkas

### Struktur Direktori

- Simpan custom apps di direktori `apps/`
- Gunakan direktori `static/` untuk file static
- Simpan template di direktori `templates/`
- Simpan file media di `media/` (untuk development)

### Manajemen Settings

Template RhamaaCMS menggunakan settings berbasis environment:

- `base.py` - Settings umum
- `dev.py` - Settings development
- `production.py` - Settings production

## Penggunaan Lanjutan

### Template Kustom

Meskipun Rhamaa CLI menggunakan template RhamaaCMS secara default, Anda masih bisa menggunakan sistem template native Wagtail:

```bash
wagtail start --template=https://github.com/your-org/your-template.git ProyekSaya
```

### Environment Variables

Setup environment variables untuk proyek Anda:

```bash
# File .env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
```

## Pemecahan Masalah

### Masalah Download Template

Jika download template gagal:

1. **Cek Koneksi Internet**: Pastikan Anda memiliki koneksi yang stabil
2. **Akses GitHub**: Verifikasi Anda bisa mengakses GitHub
3. **Instalasi Wagtail**: Pastikan Wagtail terinstall

### Error Permission

Di beberapa sistem, Anda mungkin memerlukan permission yang lebih tinggi:

```bash
sudo rhamaa start ProyekSaya
```

Atau gunakan virtual environment:

```bash
python -m venv myenv
source myenv/bin/activate  # Linux/Mac
pip install rhamaa wagtail
rhamaa start ProyekSaya
```

### Proyek Sudah Ada

Jika direktori dengan nama yang sama sudah ada:

```
Error: Directory 'ProyekSaya' already exists
```

Pilih nama yang berbeda atau hapus direktori yang ada.

## Integrasi dengan Tools Lain

### Version Control

Inisialisasi repository Git setelah pembuatan proyek:

```bash
rhamaa start ProyekSaya
cd ProyekSaya
git init
git add .
git commit -m "Initial commit"
```

### Setup IDE

Template RhamaaCMS bekerja dengan baik dengan:

- **VS Code**: Termasuk ekstensi yang direkomendasikan
- **PyCharm**: Deteksi proyek Django
- **Sublime Text**: Syntax highlighting Python

### Deployment

Template siap untuk deployment ke:

- **Heroku**: Termasuk Procfile dan requirements
- **Docker**: Dockerfile disertakan
- **Traditional Hosting**: Konfigurasi WSGI siap

## Langkah Selanjutnya

Setelah membuat proyek Anda:

1. **Setup Environment**: Buat virtual environment dan install dependensi
2. **Tambahkan Aplikasi**: Gunakan `rhamaa add` untuk install apps pre-built
3. **Konfigurasi Settings**: Sesuaikan settings untuk kebutuhan Anda
4. **Jalankan Migrasi**: Setup database
5. **Buat Superuser**: Akses interface admin

Lihat bagian [Manajemen App](app-management.md) untuk menambahkan aplikasi pre-built ke proyek Anda.