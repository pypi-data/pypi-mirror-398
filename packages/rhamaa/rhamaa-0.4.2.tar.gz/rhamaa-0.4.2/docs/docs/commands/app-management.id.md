# Manajemen Aplikasi

Sistem manajemen aplikasi Rhamaa CLI memungkinkan Anda dengan mudah menambahkan aplikasi pre-built ke proyek Wagtail Anda. Bagian ini mencakup semua perintah terkait aplikasi dan workflow.

## Menambahkan Aplikasi Prebuilt

### `rhamaa startapp <NamaApp> --prebuild <key>`

Install aplikasi prebuilt dari ekosistem RhamaaCMS ke dalam `apps/<NamaApp>`.

```bash
rhamaa startapp <NamaApp> --prebuild <key>
```

#### Penggunaan Dasar

```bash
# Install aplikasi MQTT ke apps/iot
rhamaa startapp iot --prebuild mqtt

# Install aplikasi users ke apps/users
rhamaa startapp users --prebuild users

# Install aplikasi articles ke apps/articles
rhamaa startapp articles --prebuild articles
```

#### Opsi

| Opsi | Deskripsi |
|------|-----------|
| `--list` | Tampilkan semua aplikasi prebuilt yang tersedia |
| `--force`, `-f` | Timpa direktori tujuan jika sudah ada (untuk --prebuild) |

#### Contoh

```bash
# Tampilkan aplikasi yang tersedia
rhamaa startapp --list

# Paksa install ulang aplikasi prebuilt ke folder yang sama
rhamaa startapp iot --prebuild mqtt --force
```

## Melihat Aplikasi yang Tersedia

### Lihat Semua Aplikasi

```bash
rhamaa startapp --list
```

Ini menampilkan tabel terformat yang menunjukkan:

- **Nama Aplikasi**: Identifier yang digunakan untuk instalasi
- **Deskripsi**: Deskripsi singkat fungsionalitas aplikasi
- **Kategori**: Kategori aplikasi (IoT, Authentication, Content, dll.)

### Contoh Output

```
┌──────────────┬────────────────────────────────────┬─────────────────┐
│ Nama App     │ Deskripsi                          │ Kategori        │
├──────────────┼────────────────────────────────────┼─────────────────┤
│ mqtt         │ Integrasi IoT MQTT untuk Wagtail  │ IoT             │
│ users        │ Sistem manajemen user lanjutan     │ Authentication  │
│ articles     │ Manajemen blog dan artikel         │ Content         │
│ lms          │ Solusi LMS lengkap untuk Wagtail   │ Education       │
└──────────────┴────────────────────────────────────┴─────────────────┘
```

## Proses Instalasi

Ketika Anda menginstall aplikasi, Rhamaa CLI melakukan langkah-langkah berikut:

### 1. Validasi Proyek

- Memeriksa apakah Anda berada di direktori proyek Wagtail
- Mencari `manage.py` atau indikator proyek Django lainnya
- Menampilkan error jika tidak berada di proyek yang valid

### 2. Pemeriksaan Ketersediaan Aplikasi

- Memverifikasi aplikasi ada di registry
- Menampilkan pesan error jika aplikasi tidak ditemukan
- Menyarankan menggunakan `--list` untuk melihat aplikasi yang tersedia

### 3. Pemeriksaan Aplikasi yang Sudah Ada

- Memeriksa apakah aplikasi sudah ada di direktori `apps/`
- Meminta menggunakan flag `--force` jika aplikasi sudah ada
- Melewati instalasi kecuali dipaksa

### 4. Proses Download

- Download repository aplikasi dari GitHub
- Menampilkan progress bar dengan status download
- Menangani error jaringan dengan baik

### 5. Ekstraksi dan Instalasi

- Mengekstrak repository yang didownload
- Menempatkan file aplikasi di direktori `apps/<nama_aplikasi>/`
- Membersihkan file sementara
- Menampilkan pesan sukses instalasi

## Langkah Setelah Instalasi

Setelah menginstall aplikasi, Anda perlu:

### 1. Tambahkan ke INSTALLED_APPS

Edit file settings Django Anda:

```python
# settings/base.py atau settings.py
INSTALLED_APPS = [
    # ... aplikasi yang sudah ada
    'apps.mqtt',  # Tambahkan aplikasi yang diinstall
]
```

### 2. Jalankan Migrasi

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Kumpulkan File Static (jika diperlukan)

```bash
python manage.py collectstatic
```

### 4. Konfigurasi Tambahan

Periksa file README aplikasi untuk kebutuhan konfigurasi spesifik:

```bash
cat apps/mqtt/README.md
```

## Struktur Direktori Aplikasi

Aplikasi yang diinstall ditempatkan di direktori `apps/`:

```
proyek_anda/
├── apps/
│   ├── __init__.py
│   ├── mqtt/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── admin.py
│   │   ├── urls.py
│   │   ├── templates/
│   │   ├── static/
│   │   └── README.md
│   └── users/
│       ├── __init__.py
│       ├── models.py
│       └── ...
└── manage.py
```

## Instalasi Paksa (Force)

### Kapan Menggunakan `--force`

Gunakan flag `--force` ketika Anda ingin:

- **Reinstall** aplikasi dengan update
- **Menimpa** instalasi yang rusak
- **Mengganti** aplikasi yang dimodifikasi dengan yang asli

### Contoh

```bash
rhamaa startapp iot --prebuild mqtt --force
```

### Apa yang Terjadi

- Menghapus direktori aplikasi yang ada
- Download dan install versi segar
- Mempertahankan file proyek Anda yang lain

!!! warning "Peringatan Kehilangan Data"
    Menggunakan `--force` akan menghapus modifikasi lokal pada aplikasi. Pastikan untuk backup perubahan kustom.

## Error Handling

### Error Umum dan Solusi

#### "Bukan Proyek Wagtail"

```
Error: This doesn't appear to be a Wagtail project.
Please run this command from the root of your Wagtail project.
```

**Solusi**: Navigasi ke direktori root proyek Anda (tempat `manage.py` berada).

#### "Aplikasi Tidak Ditemukan"

```
Error: App 'myapp' not found in registry.
Use 'rhamaa startapp --list' to see available apps.
```

**Solusi**: Periksa aplikasi yang tersedia dengan `rhamaa startapp --list` dan gunakan nama aplikasi yang benar.

#### "Aplikasi Sudah Ada"

```
Warning: App 'mqtt' already exists in apps/ directory.
Use --force flag to overwrite existing app.
```

**Solusi**: Gunakan `rhamaa startapp iot --prebuild mqtt --force` untuk reinstall.

#### "Download Gagal"

```
Failed to download repository.
Please check your internet connection and try again.
```

**Solusi**: Periksa koneksi internet dan akses GitHub Anda.

## Best Practices

### Sebelum Instalasi

1. **Backup Proyek Anda**: Terutama saat menggunakan `--force`
2. **Periksa Dependensi**: Review kebutuhan aplikasi
3. **Rencanakan Integrasi**: Pahami bagaimana aplikasi cocok dengan proyek Anda

### Setelah Instalasi

1. **Baca Dokumentasi**: Periksa file README aplikasi
2. **Test Fungsionalitas**: Verifikasi aplikasi bekerja sesuai harapan
3. **Kustomisasi Settings**: Konfigurasi pengaturan spesifik aplikasi
4. **Update Requirements**: Tambahkan dependensi baru

### Manajemen Aplikasi

1. **Jaga Aplikasi Tetap Update**: Reinstall aplikasi secara berkala untuk update
2. **Dokumentasikan Penggunaan**: Catat aplikasi mana yang telah Anda install
3. **Version Control**: Commit aplikasi ke repository Anda
4. **Konsistensi Environment**: Install aplikasi yang sama di semua environment

## Contoh Integrasi

### Setup Blog

```bash
rhamaa start BlogSaya
cd BlogSaya
rhamaa startapp articles --prebuild articles
rhamaa startapp users --prebuild users
# Konfigurasi dan jalankan migrasi
```

### Dashboard IoT

```bash
rhamaa start DashboardIoT
cd DashboardIoT
rhamaa startapp iot --prebuild mqtt
rhamaa startapp users --prebuild users
# Konfigurasi pengaturan MQTT
```

### Platform Edukasi

```bash
rhamaa start PlatformEdu
cd PlatformEdu
rhamaa startapp lms --prebuild lms
rhamaa startapp users --prebuild users
rhamaa startapp articles --prebuild articles
# Konfigurasi pengaturan LMS
```

## Langkah Selanjutnya

- Pelajari tentang [Sistem Registry](registry.md)
- Jelajahi [Aplikasi yang Tersedia](../apps/index.md) secara detail
- Periksa [Pemecahan Masalah](../help/troubleshooting.md) untuk masalah umum