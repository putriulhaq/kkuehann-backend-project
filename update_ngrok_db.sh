#!/bin/bash

# Jalankan ngrok dan simpan output ke file
ngrok tcp 5432 > ngrok.log 2>&1 &

# Tunggu sebentar agar ngrok memiliki waktu untuk memulai
sleep 10  # Menunggu 10 detik

# Periksa apakah ngrok berjalan menggunakan tasklist
if ! tasklist | grep -q "ngrok.exe"
then
    echo "Ngrok gagal dijalankan"
    exit 1
fi

# Tampilkan isi file log untuk debugging
echo "Isi file ngrok.log:"
cat ngrok.log

# Ekstrak URL lengkap dari output ngrok
NGROK_URL=$(grep -o 'tcp://[^:]*:[0-9]*' ngrok.log)

if [ -z "$NGROK_URL" ]
then
    echo "Gagal mendapatkan URL dari ngrok"
    echo "Mencoba metode alternatif..."
    # Metode alternatif menggunakan API ngrok
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'tcp://[^"]*')
fi

if [ -z "$NGROK_URL" ]
then
    echo "Masih gagal mendapatkan URL dari ngrok"
    exit 1
fi

echo "Ngrok berjalan pada: $NGROK_URL"

# Ekstrak host dan port dari URL ngrok
NGROK_HOST=$(echo $NGROK_URL | sed 's|tcp://||' | cut -d: -f1)
NGROK_PORT=$(echo $NGROK_URL | sed 's|tcp://||' | cut -d: -f2)

# Perbarui DATABASE_URL di file .env
sed -i "s|DATABASE_URL=.*|DATABASE_URL='postgres://postgres:admin@$NGROK_HOST:$NGROK_PORT/kkuehann'|" .env

echo "File .env telah diperbarui dengan DATABASE_URL baru"
echo "DATABASE_URL='postgres://postgres:admin@$NGROK_HOST:$NGROK_PORT/kkuehann'"

# Jalankan aplikasi Python
echo "Menjalankan aplikasi Python..."
python app.py &
# Biarkan ngrok tetap berjalan
wait