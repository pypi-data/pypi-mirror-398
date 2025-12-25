# Panduan Cepat

Mulai menggunakan Rhamaa CLI dalam hitungan menit! Panduan ini akan memandu Anda membuat proyek Wagtail pertama dan menambahkan aplikasi pre-built.

## Langkah 1: Buat Proyek Pertama Anda

Buat proyek Wagtail baru menggunakan template RhamaaCMS:

```bash
rhamaa start BlogSaya
```

Perintah ini akan:

- Download template RhamaaCMS
- Membuat direktori baru bernama `BlogSaya`
- Setup struktur proyek Wagtail dasar
- Konfigurasi pengaturan dan dependensi awal

!!! success "Proyek Berhasil Dibuat!"
    Anda akan melihat pesan sukses dengan logo Rhamaa CLI dan konfirmasi bahwa proyek Anda telah dibuat.

## Langkah 2: Navigasi ke Proyek Anda

```bash
cd BlogSaya
```

## Langkah 3: Setup Environment Anda

Buat dan aktifkan virtual environment:

```bash
# Buat virtual environment
python -m venv .venv

# Aktifkan
# Di Linux/Mac:
source .venv/bin/activate
# Di Windows:
# .venv\Scripts\activate

# Install dependensi
pip install -r requirements.txt
```

## Langkah 4: Jelajahi Aplikasi yang Tersedia

Lihat aplikasi pre-built apa saja yang tersedia:

```bash
rhamaa startapp --list
```

Anda akan melihat tabel yang menampilkan aplikasi yang tersedia seperti:

- **mqtt** - Integrasi IoT MQTT
- **users** - Manajemen user lanjutan
- **articles** - Sistem blog dan artikel
- **lms** - Learning Management System

## Langkah 5: Tambahkan Aplikasi Pertama Anda

Mari tambahkan aplikasi articles untuk fungsionalitas blog:

```bash
rhamaa startapp articles --prebuild articles
```

Ini akan:

- Download aplikasi articles dari GitHub
- Extract ke direktori `apps/` Anda (apps/articles)
- Menampilkan langkah selanjutnya untuk konfigurasi

## Langkah 6: Konfigurasi Aplikasi

Ikuti instruksi yang ditampilkan setelah instalasi:

1. **Tambahkan ke INSTALLED_APPS** di pengaturan Anda:

```python
# settings/base.py atau settings.py
INSTALLED_APPS = [
    # ... aplikasi yang sudah ada
    'apps.articles',  # Cocok dengan apps/<nama>
]
```

2. **Jalankan migrasi**:

```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Buat superuser**:

```bash
python manage.py createsuperuser
```

## Langkah 7: Jalankan Development Server

```bash
python manage.py runserver
```

Kunjungi `http://127.0.0.1:8000/admin/` untuk mengakses interface admin Wagtail.

## Apa Selanjutnya?

### Tambahkan Lebih Banyak Aplikasi

Jelajahi aplikasi lain yang tersedia:

```bash
# Tambahkan manajemen user
rhamaa startapp users --prebuild users

# Tambahkan kemampuan IoT
rhamaa startapp iot --prebuild mqtt

# Tambahkan fungsionalitas LMS
rhamaa startapp lms --prebuild lms
```

### Dapatkan Informasi Aplikasi

Pelajari lebih lanjut tentang aplikasi sebelum menginstall:

```bash
rhamaa startapp --list
# Lalu buka repo app yang ditampilkan untuk detailnya
```

### Perintah Registry

Grup perintah `registry` berdiri sendiri sudah deprecated. Gunakan:

```bash
rhamaa startapp --list
```

## Workflow Umum

### Memulai Proyek Blog

```bash
rhamaa start BlogSaya
cd BlogSaya
rhamaa startapp articles --prebuild articles
# Konfigurasi dan jalankan migrasi
```

### Memulai Proyek IoT

```bash
rhamaa start DashboardIoT
cd DashboardIoT
rhamaa startapp iot --prebuild mqtt
rhamaa startapp users --prebuild users
# Konfigurasi pengaturan MQTT dan jalankan migrasi
```

### Memulai Platform Edukasi

```bash
rhamaa start PlatformEdu
cd PlatformEdu
rhamaa startapp lms --prebuild lms
rhamaa startapp users --prebuild users
# Konfigurasi pengaturan LMS dan jalankan migrasi
```

## Tips untuk Sukses

!!! tip "Struktur Proyek"
    Rhamaa CLI membuat aplikasi di direktori `apps/`. Ini menjaga proyek Anda tetap terorganisir dan mengikuti best practices Django.

!!! tip "Instalasi Paksa"
    Jika Anda perlu menginstall ulang aplikasi prebuilt ke folder yang sama, gunakan flag `--force`:
    ```bash
    rhamaa startapp articles --prebuild articles --force
    ```

!!! tip "Cek Tipe Proyek"
    Rhamaa CLI secara otomatis mendeteksi apakah Anda berada di proyek Wagtail sebelum mengizinkan instalasi aplikasi.

## Pemecahan Masalah

### Aplikasi Sudah Ada

Jika Anda melihat "App already exists" saat instalasi prebuilt, gunakan flag `--force` untuk menimpa:

```bash
rhamaa startapp articles --prebuild articles --force
```

### Bukan Proyek Wagtail

Pastikan Anda berada di direktori root proyek Wagtail Anda (tempat `manage.py` berada).

### Masalah Download

Jika download gagal, periksa koneksi internet Anda dan coba lagi. CLI akan menampilkan pesan error yang detail.

## Langkah Selanjutnya

- Pelajari lebih lanjut tentang [Manajemen Proyek](../commands/project-management.md)
- Jelajahi fitur [Manajemen Aplikasi](../commands/app-management.md)
- Lihat [Aplikasi yang Tersedia](../apps/index.md) secara detail
- Baca tentang [Kontribusi](../development/contributing.md) ke ekosistem