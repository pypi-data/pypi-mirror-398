# Instalasi

Panduan ini akan membantu Anda menginstall Rhamaa CLI di sistem Anda.

## Prasyarat

Sebelum menginstall Rhamaa CLI, pastikan Anda memiliki:

- **Python 3.7+** terinstall di sistem Anda
- **pip** package manager
- **Wagtail** terinstall (untuk membuat proyek)

!!! tip "Cek Versi Python"
    ```bash
    python --version
    # atau
    python3 --version
    ```

## Metode Instalasi

### Metode 1: Install dari PyPI (Direkomendasikan)

Install versi stabil terbaru dari PyPI:

```bash
pip install rhamaa
```

Untuk versi pre-release terbaru:

```bash
pip install --pre rhamaa
```

### Metode 2: Install Versi Spesifik

Install versi tertentu:

```bash
pip install rhamaa==0.1.0b1
```

### Metode 3: Instalasi Development

Untuk development atau mendapatkan fitur terbaru:

```bash
# Clone repository
git clone https://github.com/RhamaaCMS/RhamaaCLI.git
cd RhamaaCLI

# Buat virtual environment
python -m venv .venv

# Aktifkan virtual environment
# Di Linux/Mac:
source .venv/bin/activate
# Di Windows:
# .venv\Scripts\activate

# Install dalam mode development
pip install -e .
```

## Verifikasi Instalasi

Setelah instalasi, verifikasi bahwa Rhamaa CLI berfungsi:

```bash
rhamaa --help
```

Anda harus melihat logo Rhamaa CLI dan informasi bantuan.

## Menginstall Wagtail (Diperlukan)

Rhamaa CLI memerlukan Wagtail untuk membuat proyek baru. Install secara global:

```bash
pip install wagtail
```

Atau install di virtual environment tempat Anda berencana bekerja.

## Setup Virtual Environment

Disarankan untuk menggunakan virtual environment untuk proyek Anda:

```bash
# Buat virtual environment baru
python -m venv myproject-env

# Aktifkan
# Di Linux/Mac:
source myproject-env/bin/activate
# Di Windows:
# myproject-env\Scripts\activate

# Install Rhamaa CLI dan Wagtail
pip install rhamaa wagtail
```

## Pemecahan Masalah

### Error Permission

Jika Anda mengalami error permission di Linux/Mac:

```bash
pip install --user rhamaa
```

### Command Not Found

Jika perintah `rhamaa` tidak ditemukan setelah instalasi:

1. Periksa apakah direktori instalasi ada di PATH Anda
2. Coba gunakan `python -m rhamaa` sebagai gantinya
3. Install ulang dengan flag `--user`

### Masalah Versi Python

Rhamaa CLI memerlukan Python 3.7+. Jika Anda memiliki beberapa versi Python:

```bash
python3 -m pip install rhamaa
```

## Langkah Selanjutnya

Setelah terinstall, lanjutkan ke [Panduan Quick Start](quick-start.md) untuk membuat proyek pertama Anda.

## Update

Untuk update ke versi terbaru:

```bash
pip install --upgrade rhamaa
```

Untuk mengecek versi saat ini:

```bash
pip show rhamaa
```