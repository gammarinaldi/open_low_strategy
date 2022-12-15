# Open Low Strategy

Pre-requisite:
- Buat file `users.py` dan isi dengan format:
`list = ["email", "password", "pin"]`

- Buat task scheduler yg akan menjalankan sistem pada jam 09:01

How it works:
- Sistem akan melakukan scanning market jam 09:01 WIB, proses tsb berjalan sekitar ~20 detik, ketika saham yg memenuhi kriteria open == low ditemukan maka akan langsung melakukan buy HAKA, lalu sistem akan mengecek apakah pembelian berhasil, jika berhasil maka akan melakukan order sell di harga = buy price +3 tick.
