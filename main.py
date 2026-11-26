import asyncio
import html
import logging
import os
import random
import sqlite3
import threading
import time
from pathlib import Path

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

load_dotenv()

# ======================================================================
#  1) SOZLAMALAR
# ======================================================================
# ===================== .env dan o'qiladi =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")

try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)  # bot egasining Telegram ID si
except ValueError:
    ADMIN_ID = 0

DB_PATH = os.getenv("DB_PATH", "quiz.db")

# ===================== Sozlamalar =====================
OWNER_PHONE = "+998992924020"        # sovg'a olish uchun murojaat raqami
COIN_PER_ANSWER = 1                  # har bir to'g'ri javob uchun coin
UNLOCK_CORRECT = 60                  # keyingi daraja ochilishi uchun oldingi darajada kerakli to'g'ri javoblar

LEVEL_INFO = {
    1: ("🟢", "Boshlang'ich"),
    2: ("🔵", "O'rta"),
    3: ("🟠", "Yuqori"),
    4: ("🔴", "Murakkab"),
    5: ("⚫", "Ekspert"),
}

# kalit: (nomi, narxi coin hisobida)
PRIZES = {
    "phone": ("📱 Telefon raqam", 100),
    "money": ("💵 Pul", 300),
    "pubg": ("🎮 PUBG akkaunt", 500),
}

# ======================================================================
#  2) SAVOLLAR (500+ ta). Yangi savol: | bilan ajratilgan qator qo'shing
#     savol | TO'G'RI javob | xato 1 | xato 2 | xato 3
# ======================================================================
LEVEL1_RAW = r"""
# Format: savol | TO'G'RI javob | xato 1 | xato 2 | xato 3
CPU qisqartmasi nimani anglatadi? | Central Processing Unit | Computer Personal Unit | Central Program Utility | Control Processing Unit
Kompyuterning "miyasi" deb qaysi qurilma aytiladi? | Protsessor | Monitor | Klaviatura | Sichqoncha
RAM nima? | Tezkor xotira | Doimiy xotira | Video karta | Tarmoq kartasi
1 bayt necha bitga teng? | 8 | 2 | 4 | 16
1 kilobayt (ikkilik hisobda) necha baytga teng? | 1024 | 100 | 512 | 2000
Qaysi biri chiqarish qurilmasi? | Printer | Klaviatura | Skaner | Mikrofon
Qaysi biri kiritish qurilmasi? | Klaviatura | Monitor | Karnay | Proyektor
Windows qaysi kompaniya mahsuloti? | Microsoft | Apple | Google | IBM
macOS qaysi kompaniyaning operatsion tizimi? | Apple | Microsoft | Samsung | Intel
Android operatsion tizimini qaysi kompaniya rivojlantiradi? | Google | Apple | Microsoft | Nokia
Brauzerga misol qaysi? | Google Chrome | Microsoft Word | Photoshop | Excel
WWW nimani anglatadi? | World Wide Web | World Wide Window | Web Wide World | Wide World Windows
URL nima? | Veb-sahifa manzili | Dastur nomi | Parol turi | Fayl formati
Wi-Fi nima uchun ishlatiladi? | Simsiz tarmoqqa ulanish | Fayllarni arxivlash | Rasm tahrirlash | Ovoz yozish
Email manzilida qaysi belgi albatta bo'ladi? | @ | # | $ | %
Ctrl+C klavishlar birikmasi nima qiladi? | Nusxa oladi | Qirqib oladi | Joylashtiradi | Hammasini belgilaydi
Ctrl+V nima qiladi? | Joylashtiradi (Paste) | Nusxa oladi | Saqlaydi | Chop etadi
Ctrl+X nima qiladi? | Qirqib oladi | Nusxa oladi | Bekor qiladi | Ochadi
Ctrl+Z nima qiladi? | Oxirgi amalni bekor qiladi | Saqlaydi | Yopadi | Qidiradi
Ctrl+S nima qiladi? | Faylni saqlaydi | Chop etadi | Yopadi | Qidiradi
Ctrl+A nima qiladi? | Hammasini belgilaydi | Hammasini o'chiradi | Hammasini nusxalaydi | Yangi oyna ochadi
Windowsda o'chirilgan fayl odatda qayerga tushadi? | Savat (Recycle Bin) | Desktop | Documents | Downloads
.txt kengaytmali fayl qanday fayl? | Oddiy matn fayli | Rasm | Video | Dastur
.jpg kengaytmali fayl nima? | Rasm | Audio | Matn | Arxiv
.mp3 kengaytmali fayl nima? | Audio | Video | Rasm | Hujjat
.mp4 kengaytmali fayl nima? | Video | Audio | Jadval | Dastur
.exe kengaytma nimani bildiradi? | Bajariladigan dastur | Rasm | Matn | Musiqa
.zip fayl nima? | Siqilgan arxiv | Video | Rasm | Jadval
.pdf nima? | Hujjat formati | Dasturlash tili | Video formati | Operatsion tizim
Microsoft Excel nima uchun ishlatiladi? | Elektron jadvallar uchun | Matn yozish uchun | Rasm tahrirlash uchun | Brauzer sifatida
Microsoft Word nima uchun ishlatiladi? | Matn bilan ishlash uchun | Jadval hisoblash uchun | Video montaj uchun | Tarmoq sozlash uchun
PowerPoint nima uchun ishlatiladi? | Taqdimotlar tayyorlash | Dasturlash | Virusdan himoya | Fayl arxivlash
Kompyuter virusi nima? | Zararli dastur | Foydali dastur | Brauzer | Qurilma
Antivirus nima qiladi? | Zararli dasturlardan himoya qiladi | Internetni tezlashtiradi | Rasm chizadi | Fayl nusxalaydi
Qanday parol xavfsizroq? | Uzun va murakkab | Faqat ismingiz | 123456 | Tug'ilgan yilingiz
Qaysi parol eng zaif? | 123456 | T7#kP9!qZx | Mi$ol_2026_xK | rT5&uL2@nV
Ikkilik (binar) sanoq sistemasida qaysi raqamlar ishlatiladi? | 0 va 1 | 0 dan 9 gacha | 1 va 2 | 0 va 2
Ikkilik 10 soni o'nlik sistemada nechaga teng? | 2 | 10 | 1 | 4
Ikkilik 101 soni o'nlik sistemada nechaga teng? | 5 | 3 | 6 | 7
Dasturlash nima? | Kompyuterga buyruqlar yozish | Kompyuter yig'ish | Internet ulash | Rasm chizish
Dasturlash tiliga misol qaysi? | Python | Windows | Chrome | Wi-Fi
Python tilini kim yaratgan? | Guido van Rossum | Linus Torvalds | Bill Gates | Elon Musk
Linux yadrosini kim yaratgan? | Linus Torvalds | Guido van Rossum | Steve Jobs | Dennis Ritchie
Apple kompaniyasining asoschilaridan biri kim? | Steve Jobs | Bill Gates | Mark Zuckerberg | Larry Page
Microsoft asoschisi kim? | Bill Gates | Steve Jobs | Jeff Bezos | Tim Cook
Facebook asoschisi kim? | Mark Zuckerberg | Elon Musk | Larry Page | Jack Dorsey
Qidiruv tizimiga misol qaysi? | Google | Photoshop | Notepad | Paint
Telegram nima? | Messenjer | Antivirus | Brauzer | Dasturlash tili
HDD nima? | Qattiq disk | Tezkor xotira | Protsessor | Videokarta
SSD nima? | Qattiq holatdagi (flesh asosli) disk | Videokarta | Protsessor sovutgichi | Tarmoq kabeli
GPU nima? | Grafik protsessor | Markaziy protsessor | Tezkor xotira | Quvvat bloki
USB flesh-disk nima uchun kerak? | Ma'lumotlarni ko'chirish va saqlash | Internetga ulanish | Ovoz chiqarish | Rasm olish
Monitor qanday qurilma? | Tasvir chiqarish qurilmasi | Kiritish qurilmasi | Xotira qurilmasi | Tarmoq qurilmasi
Router nima qiladi? | Tarmoq trafigini yo'naltiradi | Ma'lumotni chop etadi | Rasm tahrirlaydi | Ovoz yozadi
Bluetooth nima uchun ishlatiladi? | Qisqa masofada simsiz aloqa uchun | Uzoq masofali telefon uchun | Fayl arxivlash uchun | Rasm chizish uchun
iOS qaysi kompaniyaning mobil operatsion tizimi? | Apple | Google | Samsung | Huawei
Ekran o'lchami uchun qaysi birlik ishlatiladi? | Dyuym | Kilogramm | Litr | Volt
Piksel nima? | Tasvirning eng kichik nuqtasi | Ovoz birligi | Xotira turi | Dastur nomi
1 megabayt (ikkilik hisobda) necha kilobayt? | 1024 | 100 | 512 | 2048
1 gigabayt (ikkilik hisobda) necha megabayt? | 1024 | 100 | 512 | 2048
Qaysi biri operatsion tizim? | Linux | Python | HTML | Excel
Qaysi biri dasturlash tili emas? | Windows | Java | C++ | Python
Fayl kengaytmasi nima? | Nomdagi nuqtadan keyingi qism | Fayl hajmi | Fayl yaratuvchisi | Fayl rangi
Papka (folder) nima uchun kerak? | Fayllarni guruhlash uchun | Fayllarni o'chirish uchun | Internetga ulanish uchun | Dastur yozish uchun
Desktop nima? | Ish stoli | Klaviatura | Printer | Ofis
Windowsda Task Manager qaysi tugmalar bilan ochiladi? | Ctrl+Shift+Esc | Alt+F4 | Ctrl+P | Shift+Tab
Alt+F4 nima qiladi (Windows)? | Faol oynani yopadi | Dastur o'rnatadi | Fayl ochadi | Ekranni suratga oladi
PrintScreen tugmasi nima qiladi? | Ekranning suratini oladi | Kompyuterni o'chiradi | Dasturni yopadi | Tovushni o'chiradi
Caps Lock nima qiladi? | Bosh harflarni yoqadi/o'chiradi | Tovushni o'chiradi | Ekranni qulflaydi | Internetni uzadi
Enter tugmasi odatda nima qiladi? | Buyruqni tasdiqlaydi yoki yangi qatorga o'tadi | Kompyuterni o'chiradi | Faylni o'chiradi | Dasturni yopadi
Kompyuter tarmog'i nima? | O'zaro bog'langan qurilmalar to'plami | Bitta kompyuter | Dastur turi | Fayl formati
LAN nima? | Mahalliy tarmoq | Global tarmoq | Simsiz quvvat | Dastur
Internet nima? | Global kompyuter tarmog'i | Bitta sayt | Brauzer | Qidiruv tizimi
Domen nomiga misol qaysi? | google.com | 192.168.1.1 | 8080 | C:\Windows
IP-manzil nima? | Tarmoqdagi qurilma manzili | Parol | Fayl nomi | Dastur versiyasi
HTTPS dagi "S" harfi nimani bildiradi? | Secure (xavfsiz) | Speed | Server | Simple
Bulutli saqlashga (cloud storage) misol qaysi? | Google Drive | Notepad | Paint | Calculator
Qaysi biri ijtimoiy tarmoq? | Instagram | Excel | Linux | Python
Qaysi biri video platforma? | YouTube | Word | Chrome | GitHub
GitHub nima uchun ishlatiladi? | Kodni saqlash va hamkorlikda ishlash | Rasm tahrirlash | Video ko'rish | O'yin o'ynash
Dasturlashda "bug" nima? | Dasturdagi xato | Yangi imkoniyat | Dastur nomi | Kompyuter turi
"Backup" nima? | Zaxira nusxa | Parol | Virus | Dastur yangilanishi
"Update" nima? | Yangilash | O'chirish | Nusxa olish | Qulflash
"Download" nima? | Internetdan yuklab olish | Internetga yuklash | O'chirish | Chop etish
"Upload" nima? | Internetga yuklash | Internetdan olish | O'chirish | Qidirish
Hotspot nima? | Telefon orqali internet tarqatish | Antivirus | Fayl turi | O'yin
Skaner nima qiladi? | Qog'ozdagi hujjatni raqamlashtiradi | Hujjat chop etadi | Tovush chiqaradi | Internetga ulaydi
Printer nima qiladi? | Hujjatni qog'ozga chop etadi | Skanerlaydi | Tovush yozadi | Internet beradi
Mikrofon qanday qurilma? | Ovoz kiritish qurilmasi | Tasvir chiqarish qurilmasi | Chop etish qurilmasi | Xotira qurilmasi
Veb-kamera nima uchun kerak? | Video tasvir olish uchun | Chop etish uchun | Ovoz chiqarish uchun | Fayl saqlash uchun
Kompyuterni "qayta ishga tushirish" ingliz tilida? | Restart | Shutdown | Sleep | Logout
"Shutdown" nima? | Kompyuterni o'chirish | Qayta yoqish | Uyqu rejimi | Tizimdan chiqish
Operatsion tizim nima qiladi? | Kompyuter resurslarini boshqaradi | Faqat o'yin o'ynaydi | Faqat internet beradi | Faqat chop etadi
Emoji nima? | Tasviriy belgilar | Parol turi | Fayl formati | Virus
Chrome qaysi kompaniyaning brauzeri? | Google | Microsoft | Apple | Mozilla
Firefox qaysi tashkilotning brauzeri? | Mozilla | Google | Microsoft | Yandex
Algoritm nima? | Masalani yechish qadamlari ketma-ketligi | Dastur nomi | Kompyuter turi | Virus
"Dastur" ingliz tilida qanday? | Program | Window | Screen | Folder
Ma'lumot (data) nima? | Qayta ishlanadigan axborot | Qurilma | Tarmoq | Parol
"Software" nima? | Dasturiy ta'minot | Apparat ta'minot | Kabel | Monitor
"Hardware" nima? | Apparat ta'minot (jismoniy qismlar) | Dasturiy ta'minot | Parol | Tarmoq turi
Klaviaturadagi Backspace tugmasi nima qiladi? | Kursor oldidagi belgini o'chiradi | Kompyuterni o'chiradi | Yangi qator ochadi | Faylni saqlaydi
"""

LEVEL2_RAW = r"""
# Format: savol | TO'G'RI javob | xato 1 | xato 2 | xato 3
HTML nima? | Gipermatn belgilash tili | Ma'lumotlar bazasi | Operatsion tizim | Tarmoq protokoli
HTML da eng katta sarlavha tegi qaysi? | <h1> | <h6> | <head> | <title>
HTML da havola (link) yaratish tegi? | <a> | <link> | <href> | <url>
HTML da rasm qo'yish tegi? | <img> | <image> | <pic> | <src>
HTML da paragraf tegi? | <p> | <para> | <text> | <pg>
HTML da tartiblanmagan ro'yxat tegi? | <ul> | <ol> | <li> | <list>
HTML da jadval yaratish tegi? | <table> | <tab> | <grid> | <cell>
CSS nima uchun ishlatiladi? | Sahifaga stil berish uchun | Ma'lumotlar bazasi uchun | Serverda kod yozish uchun | Tarmoq sozlash uchun
CSS da matn rangini o'zgartiruvchi xususiyat? | color | font-color | text-color | fg-color
CSS da orqa fon rangini o'zgartiruvchi xususiyat? | background-color | bgcolor | color-back | back-color
CSS da shrift o'lchamini belgilovchi xususiyat? | font-size | text-size | font-style | size-font
JavaScript asosan qayerda ishlaydi? | Brauzerda (va Node.js da) | Faqat printerda | Faqat BIOS da | Faqat Excelda
Python da ekranga chiqarish funksiyasi? | print() | echo() | write() | show()
Python da izoh qaysi belgi bilan boshlanadi? | # | // | -- | /*
Python da ro'yxat (list) qaysi qavs bilan yoziladi? | [] | {} | () | <>
Python da lug'at (dict) qaysi qavs bilan yoziladi? | {} | [] | () | <>
Python da kortej (tuple) qaysi qavs bilan yoziladi? | () | [] | {} | <>
Python da 7 // 2 natijasi nechaga teng? | 3 | 3.5 | 4 | 2
Python da 7 % 2 natijasi nechaga teng? | 1 | 3 | 0 | 2
Python da 2 ** 3 natijasi nechaga teng? | 8 | 6 | 5 | 9
Python da len("salom") natijasi? | 5 | 4 | 6 | 3
Python da type(5) nimani qaytaradi? | int | str | float | bool
Python da type(5.0) nimani qaytaradi? | float | int | str | double
Python da "a" + "b" natijasi? | ab | a b | ba | xato
Python da shartli operator kalit so'zi? | if | when | case | check
Python da takrorlash (sikl) operatorlari? | for va while | loop va repeat | do va until | each va times
Python da funksiya e'lon qilish kalit so'zi? | def | func | function | fn
Python da faylni ochish uchun qaysi funksiya ishlatiladi? | open() | read() | load() | fopen()
Python da kutubxonani ulash kalit so'zi? | import | include | using | require
Python da funksiyadan qiymat qaytarish kalit so'zi? | return | back | give | out
Python da "bo'sh qiymat" qanday yoziladi? | None | Null | Nil | Void
Python da True va False qaysi turga mansub? | bool | str | list | bit
Python da input() funksiyasi nima qiladi? | Foydalanuvchidan ma'lumot oladi | Ekranga chiqaradi | Faylni ochadi | Dasturni to'xtatadi
Python da range(3) qaysi sonlarni beradi? | 0, 1, 2 | 1, 2, 3 | 0, 1, 2, 3 | 1, 2
Python da list oxiriga element qo'shish metodi? | append() | add() | push() | attach()
Python da stringni KATTA harflarga o'tkazish metodi? | upper() | big() | capital() | toUpper()
Python da int("12") + 3 natijasi? | 15 | 123 | 12 | xato
Python da "5" * 2 natijasi? | 55 | 10 | xato | 52
Python da qaysi nom o'zgaruvchi nomi sifatida yaroqsiz? | 2name | name2 | _name | my_name
Python da bo'sh list qanday yaratiladi? | [] | {} | () | None
Python fayllarining kengaytmasi? | .py | .pt | .python | .pyt
pip nima? | Python paket menejeri | Python o'yini | Matn muharriri | Brauzer
Git nima? | Versiyalarni boshqarish tizimi | Dasturlash tili | Brauzer | Antivirus
Git da yangi repozitoriy yaratish buyrug'i? | git init | git new | git start | git create
Git da o'zgarishlarni saqlash (commit) buyrug'i? | git commit | git save | git store | git record
Git da o'zgarishlarni masofaviy serverga yuborish buyrug'i? | git push | git send | git upload | git pull
Git da serverdan yangilanishlarni olish buyrug'i? | git pull | git get | git take | git commit
Git da repozitoriyni o'z kompyuteringizga nusxalash? | git clone | git copy | git download | git fetchall
Git da fayllarni commit ga tayyorlash buyrug'i? | git add | git put | git ready | git prepare
GitHub qaysi kompaniyaga tegishli? | Microsoft | Google | Apple | Amazon
.gitignore fayli nima uchun kerak? | Git kuzatmaydigan fayllarni ko'rsatish uchun | Parolni saqlash uchun | Dasturni ishga tushirish uchun | Kodni shifrlash uchun
.env faylida odatda nima saqlanadi? | Maxfiy sozlamalar (token, parol) | Rasmlar | Videolar | Musiqa
SQL nima? | Ma'lumotlar bazasi so'rov tili | Rasm formati | Brauzer | Operatsion tizim
SQL da ma'lumot tanlash buyrug'i? | SELECT | GET | FETCH | CHOOSE
SQL da yangi qator qo'shish buyrug'i? | INSERT | ADD | APPEND | PUT
SQL da ma'lumotni o'chirish buyrug'i? | DELETE | REMOVE | CUT | ERASE
SQL da ma'lumotni yangilash buyrug'i? | UPDATE | CHANGE | MODIFY | RENEW
SQL da shart qo'yish kalit so'zi? | WHERE | WHEN | FOR | THEN
Ma'lumotlar bazasi jadvalidagi gorizontal qator nima deyiladi? | Yozuv (row) | Ustun | Kalit | Indeks
Jadvaldagi ustun inglizcha qanday ataladi? | Column | Row | Cell | Table
Primary key nima? | Yozuvni noyob aniqlovchi kalit | Parol | Shifrlash kaliti | Jadval nomi
Qaysi biri ma'lumotlar bazasi? | MySQL | Chrome | Photoshop | Notepad
SQLite ning o'ziga xosligi nima? | Fayl ko'rinishidagi yengil baza | Faqat bulutda ishlaydi | Dasturlash tili | Operatsion tizim
Operatsion tizimning yadrosi nima deb ataladi? | Kernel | Shell | Driver | Bootloader
Drayver (driver) nima? | Qurilma bilan ishlash uchun dastur | Avtomobil haydovchisi | Antivirus | Brauzer
BIOS nima? | Kompyuter yoqilganda ishga tushadigan past darajali dastur | Brauzer | Matn muharriri | O'yin
Jarayon (process) nima? | Bajarilayotgan dastur | Fayl turi | Qurilma | Tarmoq
DNS nima qiladi? | Domen nomini IP-manzilga aylantiradi | Parolni shifrlaydi | Faylni siqadi | Rasm chizadi
HTTP nima? | Veb ma'lumot uzatish protokoli | Dasturlash tili | Fayl formati | Antivirus
80-port odatda qaysi protokolga tegishli? | HTTP | HTTPS | FTP | SSH
443-port odatda qaysi protokolga tegishli? | HTTPS | HTTP | FTP | SMTP
22-port odatda qaysi protokolga tegishli? | SSH | HTTP | DNS | SMTP
FTP nima uchun ishlatiladi? | Fayl uzatish uchun | Email yuborish uchun | Domen olish uchun | Video chat uchun
SMTP nima uchun ishlatiladi? | Email yuborish uchun | Fayl yuklash uchun | Veb sahifa ko'rish uchun | Domen olish uchun
localhost ning IP-manzili qaysi? | 127.0.0.1 | 192.168.0.1 | 8.8.8.8 | 255.255.255.0
8.8.8.8 qaysi kompaniyaning ommaviy DNS serveri? | Google | Microsoft | Apple | Samsung
ping buyrug'i nima uchun ishlatiladi? | Qurilma bilan aloqani tekshirish | Faylni o'chirish | Dastur o'rnatish | Parolni o'zgartirish
Linux da joriy papka yo'lini ko'rsatuvchi buyruq? | pwd | cwd | path | where
Linux da papka tarkibini ko'rish buyrug'i? | ls | see | open | show
Linux da yangi papka yaratish buyrug'i? | mkdir | newdir | createdir | folder
Linux da faylni o'chirish buyrug'i? | rm | del | erase | kill
Linux da boshqa papkaga o'tish buyrug'i? | cd | goto | move | enter
Windows buyruq qatorida (cmd) papka tarkibini ko'rish buyrug'i? | dir | ls | list | show
Excelda yig'indini hisoblovchi funksiya? | SUM | ADD | PLUS | TOTAL
Excelda o'rta arifmetikni hisoblovchi funksiya? | AVERAGE | MEAN | AVG | MID
Excelda formula qaysi belgi bilan boshlanadi? | = | # | @ | $
Mantiqiy "VA" operatori ingliz tilida? | AND | OR | NOT | XOR
Mantiqiy "YOKI" operatori ingliz tilida? | OR | AND | NOT | NAND
NOT True natijasi nima? | False | True | None | 1
True AND False natijasi nima? | False | True | None | Xato
True OR False natijasi nima? | True | False | None | Xato
Ikkilik 1111 soni o'nlikda nechaga teng? | 15 | 16 | 14 | 8
O'nlik 8 soni ikkilikda qanday yoziladi? | 1000 | 1010 | 0100 | 1100
O'n oltilik (hex) sanoq sistemasida nechta belgi ishlatiladi? | 16 | 10 | 8 | 12
Hex sistemasidagi A harfi o'nlikda nechaga teng? | 10 | 11 | 9 | 15
1920x1080 ekran o'lchami qanday ataladi? | Full HD | 4K | HD Ready | VGA
ASCII nima? | Belgilarni sonlar bilan kodlash jadvali | Dasturlash tili | Tarmoq protokoli | Antivirus
Unicode nima? | Dunyo tillari belgilari uchun kodlash standarti | Dasturlash tili | Rasm formati | Operatsion tizim
JSON nima? | Ma'lumot almashish formati | Dasturlash tili | Brauzer | Rasm formati
API nima? | Dasturlar o'zaro muloqot qiladigan interfeys | Antivirus | Qurilma | Fayl turi
"""

LEVEL3_RAW = r"""
# Format: savol | TO'G'RI javob | xato 1 | xato 2 | xato 3
Python da list comprehension misoli qaysi? | [x*2 for x in range(3)] | for x in range(3): [x*2] | list(x*2 in range(3)) | [for x in range(3) x*2]
Python da [1, 2, 3][-1] natijasi? | 3 | 1 | 2 | xato
Python da "salom"[1:3] natijasi? | al | sa | alo | sal
Python da dict dan kalit bo'yicha qiymat olish? | d["kalit"] | d.kalit | d(kalit) | d->kalit
Python da set ning asosiy xususiyati? | Takrorlanmas elementlar to'plami | Tartiblangan ro'yxat | Faqat sonlar | O'zgarmas matn
Python da tuple va list orasidagi asosiy farq? | Tuple o'zgarmas (immutable) | List o'zgarmas | Farqi yo'q | Tuple faqat sonlarni saqlaydi
Python da xatolikni ushlash konstruksiyasi? | try / except | catch / throw | error / handle | if / error
Python da with open(...) ning afzalligi? | Fayl avtomatik yopiladi | Fayl tezroq o'qiladi | Fayl shifrlanadi | Fayl nusxalanadi
Python da lambda nima? | Nomsiz kichik funksiya | Sikl turi | Modul | Xato turi
Python da *args nima? | Ixtiyoriy sondagi pozitsion argumentlar | Kvadrat daraja | Izoh | Ko'paytirish belgisi
Python da **kwargs nima? | Ixtiyoriy sondagi nomli argumentlar | Ikki marta ko'paytirish | Izoh | Xato turi
Python da klass e'lon qilish kalit so'zi? | class | object | struct | type
Python da klass konstruktori metodi qanday nomlanadi? | __init__ | __start__ | constructor | __create__
Python da self nima? | Obyektning o'ziga havola | Global o'zgaruvchi | Modul nomi | Funksiya turi
OOP da "meros olish" ingliz tilida? | Inheritance | Encapsulation | Polymorphism | Abstraction
OOP da "inkapsulyatsiya" nima? | Ma'lumot va metodlarni birlashtirib himoyalash | Meros olish | Ko'p shakllilik | Siklni to'xtatish
OOP da "polimorfizm" nima? | Bir xil interfeysning turlicha bajarilishi | Faylni siqish | Ma'lumotni shifrlash | Xotirani tozalash
Python da tasodifiy son beruvchi modul? | random | math | os | sys
Python da JSON bilan ishlash moduli? | json | jsn | data | dict
Python da sana va vaqt bilan ishlash moduli? | datetime | clock | calendar_time | timer
Python da virtual muhit yaratish buyrug'i? | python -m venv venv | pip venv create | python venv new | venv install
requirements.txt fayli nima uchun kerak? | Loyiha kutubxonalari ro'yxati uchun | Parollar uchun | Rasmlar uchun | Loglar uchun
pip install nom buyrug'i nima qiladi? | Kutubxonani o'rnatadi | Kutubxonani o'chiradi | Kutubxonani faqat qidiradi | Python ni yangilaydi
Python da f-string misoli qaysi? | f"Salom {ism}" | "Salom {ism}".f() | f("Salom", ism) | format"Salom {ism}"
Python (PEP 8) da bir daraja uchun tavsiya etilgan probellar soni? | 4 | 2 | 8 | 3
Python da bool([]) natijasi? | False | True | None | Xato
Python da 0.1 + 0.2 == 0.3 natijasi? | False | True | None | Xato
Python da is va == orasidagi farq? | is obyekt aynanligini, == qiymatni solishtiradi | Farqi yo'q | is qiymatni, == turni solishtiradi | == faqat satrlar uchun
Python da generator yaratish uchun qaysi kalit so'z ishlatiladi? | yield | generate | emit | return_all
Python da dekorator qaysi belgi bilan yoziladi? | @ | # | & | $
JavaScript da o'zgaruvchi e'lon qilish kalit so'zlaridan biri? | let | int | dim | string
JavaScript da === operatori nima qiladi? | Qiymat va turni qat'iy solishtiradi | Qiymat beradi | Faqat turni solishtiradi | Xato beradi
JavaScript da konsolga chiqarish? | console.log() | print() | echo() | System.out()
JavaScript da massiv oxiriga element qo'shish metodi? | push() | append() | add() | insert()
DOM nima? | Sahifa elementlarining daraxtsimon modeli | Dasturlash tili | Ma'lumotlar bazasi | Server
Node.js nima? | JavaScript ni serverda ishga tushiruvchi muhit | Brauzer | Ma'lumotlar bazasi | CSS freymvorki
CSS Flexbox nima uchun ishlatiladi? | Elementlarni moslashuvchan joylashtirish uchun | Ma'lumot saqlash uchun | Server yozish uchun | Rasm siqish uchun
CSS da elementni id bo'yicha tanlash? | #nom | .nom | *nom | @nom
CSS da elementni klass bo'yicha tanlash? | .nom | #nom | *nom | &nom
Responsive dizayn nima? | Turli ekranlarga moslashadigan dizayn | Tez yuklanadigan sayt | Qorong'i rejim | Animatsiya
SQL da ikki jadvalni bog'lash uchun qaysi kalit so'z ishlatiladi? | JOIN | MERGE | LINK | CONNECT
SQL da natijani saralash uchun? | ORDER BY | SORT BY | GROUP BY | ARRANGE
SQL da natijani guruhlash uchun? | GROUP BY | ORDER BY | SET BY | CLUSTER BY
SQL da qatorlar sonini sanash funksiyasi? | COUNT() | NUMBER() | TOTAL() | LEN()
SQL da takrorlanmas qiymatlarni olish kalit so'zi? | DISTINCT | SINGLE | ONLY | ALONE
SQL da yangi jadval yaratish buyrug'i? | CREATE TABLE | NEW TABLE | MAKE TABLE | ADD TABLE
Foreign key (tashqi kalit) nima? | Boshqa jadvalga bog'lovchi kalit | Parol | Shifrlash kaliti | Indeks nomi
NoSQL ma'lumotlar bazasiga misol qaysi? | MongoDB | MySQL | PostgreSQL | SQLite
Redis asosan nima? | Xotirada ishlovchi kalit-qiymat ombori | Brauzer | Dasturlash tili | Operatsion tizim
REST API da ma'lumotni olish uchun odatda qaysi HTTP metodi ishlatiladi? | GET | SEND | FETCH | READ
Yangi resurs yaratish uchun odatda qaysi HTTP metodi ishlatiladi? | POST | GET | DELETE | HEAD
HTTP 404 kodi nimani bildiradi? | Sahifa topilmadi | Server xatosi | Muvaffaqiyatli | Ruxsat yo'q
HTTP 200 kodi nimani bildiradi? | Muvaffaqiyatli (OK) | Topilmadi | Server xatosi | Yo'naltirish
HTTP 500 kodi nimani bildiradi? | Serverning ichki xatosi | Topilmadi | OK | Ruxsat yo'q
HTTP 403 kodi nimani bildiradi? | Ruxsat taqiqlangan (Forbidden) | Topilmadi | OK | Yo'naltirish
HTTP 301 kodi nimani bildiradi? | Doimiy yo'naltirish | Topilmadi | OK | Server xatosi
JSON da matn qiymatlari qanday tirnoqda yoziladi? | Qo'sh tirnoq "..." | Qiyshiq qavs <...> | Kvadrat qavs [...] | Tirnoqsiz
Linux da fayl ruxsatlarini o'zgartiruvchi buyruq? | chmod | chperm | access | setmod
Linux da fayl tarkibini ekranga chiqaruvchi buyruq? | cat | echoall | view | open
Linux da matn ichidan qidiruvchi buyruq? | grep | seek | look | scan
Linux da buyruqni administrator huquqi bilan bajarish uchun? | sudo | super | admin | rootrun
Ubuntu da dastur o'rnatish uchun odatiy buyruq? | apt install | setup get | install apt | add package
Linux da jarayonni to'xtatuvchi buyruq? | kill | stopproc | end | cancel
SSH nima? | Xavfsiz masofaviy ulanish protokoli | Rasm formati | Dasturlash tili | Brauzer
Git da yangi shoxcha (branch) yaratib unga o'tish buyrug'i? | git checkout -b nom | git branch -go | git new nom | git switch --all
Git da shoxchalarni birlashtirish buyrug'i? | git merge | git join | git combine | git union
Git da commit tarixini ko'rish buyrug'i? | git log | git history | git past | git showall
Git da fayllar holatini ko'rish buyrug'i? | git status | git state | git info | git check
Pull request nima? | O'zgarishlarni asosiy shoxchaga qo'shishni so'rash | Parol so'rash | Fayl yuklash | Dasturni o'chirish
Docker nima? | Konteynerlashtirish platformasi | Dasturlash tili | Brauzer | Operatsion tizim
Docker image nima? | Konteyner yaratish uchun shablon | Rasm fayli | Video | Parol
Virtual mashina (VM) nima? | Dastur orqali emulyatsiya qilingan kompyuter | Haqiqiy jismoniy kompyuter | Antivirus | Rasm
OSI modelida nechta qatlam bor? | 7 | 5 | 4 | 8
TCP nima? | Ishonchli, ulanishga asoslangan protokol | Rasm formati | Brauzer | Antivirus
UDP ning TCP dan farqi nima? | Ulanishsiz va tezroq, yetkazish kafolatsiz | Sekinroq, lekin kafolatli | Faqat email uchun | Doim shifrlangan
MAC-manzil nima? | Tarmoq kartasining jismoniy manzili | IP versiyasi | Parol | Domen
Subnet mask 255.255.255.0 CIDR yozuvida qanday? | /24 | /8 | /16 | /32
IPv4 manzil necha bitdan iborat? | 32 | 64 | 128 | 16
IPv6 manzil necha bitdan iborat? | 128 | 32 | 64 | 256
DHCP nima qiladi? | Qurilmalarga IP manzilni avtomatik beradi | Domen nomini hal qiladi | Faylni siqadi | Parolni saqlaydi
Firewall (xavfsizlik devori) nima? | Tarmoq xavfsizligi uchun filtr | Brauzer | Disk turi | Dasturlash tili
VPN nima? | Shifrlangan virtual shaxsiy tarmoq | Antivirus | Disk | Dasturlash tili
Phishing nima? | Aldov orqali maxfiy ma'lumotni qo'lga kiritish | Fayl siqish | Tarmoq turi | Dastur turi
Ikki bosqichli autentifikatsiya (2FA) nima? | Kirishda qo'shimcha tasdiqlash | Ikki parol yozish | Ikkita antivirus | Ikki brauzer
HTTPS aloqaga nimani beradi? | Shifrlangan aloqa | Faqat tezlik | Faqat rasm | Reklama
Parolni ma'lumotlar bazasida saqlashning to'g'ri usuli? | Hesh (hash) qilib saqlash | Ochiq matnda | Rasm sifatida | Email bilan
Algoritmlarda "saralash" (sorting) nima? | Elementlarni tartibga solish | Elementlarni o'chirish | Elementlarni nusxalash | Elementlarni shifrlash
Bubble sort qanday ishlaydi? | Qo'shni elementlarni almashtirib saralaydi | Elementlarni tasodifiy tanlaydi | Faylni siqadi | Tarmoq orqali ishlaydi
Binary search qaysi massivda ishlaydi? | Saralangan | Tartibsiz | Faqat satrlardan iborat | Bo'sh
Binary search murakkabligi qanday? | O(log n) | O(n) | O(n²) | O(1)
Linear search murakkabligi qanday? | O(n) | O(1) | O(log n) | O(n log n)
Stack qaysi tamoyilda ishlaydi? | LIFO | FIFO | Tasodifiy | Saralangan
Queue (navbat) qaysi tamoyilda ishlaydi? | FIFO | LIFO | Tasodifiy | Teskari
Ko'pchilik tillarda massiv indeksi nechadan boshlanadi? | 0 | 1 | -1 | 2
Rekursiya nima? | Funksiyaning o'zini chaqirishi | Sikl turi | Xato turi | Fayl turi
Faktorial 5! nechaga teng? | 120 | 24 | 60 | 25
Fibonachchi: 0, 1, 1, 2, 3, 5, ... keyingi son nechta? | 8 | 7 | 6 | 9
Agile nima? | Moslashuvchan dasturiy ta'minot ishlab chiqish metodologiyasi | Dasturlash tili | Operatsion tizim | Brauzer
Scrum da qisqa ish davri nima deb ataladi? | Sprint | Round | Stage | Cycle
Frontend nima? | Foydalanuvchi ko'radigan qism | Server va baza qismi | Tarmoq kabeli | OS yadrosi
"""

LEVEL4_RAW = r"""
# Format: savol | TO'G'RI javob | xato 1 | xato 2 | xato 3
Hash jadvalda o'rtacha qidirish murakkabligi? | O(1) | O(n) | O(log n) | O(n²)
Quicksort ning o'rtacha murakkabligi? | O(n log n) | O(n) | O(n²) | O(log n)
Quicksort ning eng yomon holat murakkabligi? | O(n²) | O(n log n) | O(n) | O(log n)
Merge sort ning murakkabligi? | O(n log n) | O(n²) | O(n) | O(log n)
Binary search tree (BST) da inorder aylanish nimani beradi? | Saralangan ketma-ketlikni | Teskari tartibni | Tasodifiy tartibni | Faqat barglarni
Muvozanatlangan BST da qidirish murakkabligi? | O(log n) | O(n) | O(1) | O(n²)
Min-heap da ildizda qaysi element turadi? | Eng kichik element | Eng katta element | O'rtacha element | Tasodifiy element
Graf nima? | Tugunlar va qirralar to'plami | Saralangan massiv | Matn fayl | Jadval
BFS (kenglik bo'yicha qidiruv) qaysi tuzilmadan foydalanadi? | Navbat (queue) | Stek | Heap | Massiv indeksi
DFS (chuqurlik bo'yicha qidiruv) odatda qaysi tuzilma yoki usuldan foydalanadi? | Stek yoki rekursiya | Navbat | Heap | Hash jadval
Dijkstra algoritmi nima uchun ishlatiladi? | Eng qisqa yo'l topish (manfiy bo'lmagan og'irliklarda) | Saralash | Shifrlash | Siqish
Bog'langan ro'yxat (linked list) boshiga element qo'shish murakkabligi? | O(1) | O(n) | O(log n) | O(n²)
Dinamik massivga (list) oxiriga qo'shishning amortizatsiyalangan murakkabligi? | O(1) | O(n) | O(log n) | O(n²)
Big-O notatsiya nimani ifodalaydi? | Algoritm o'sish tezligining yuqori chegarasini | Aniq ish vaqtini sekundlarda | Xotira turini | Dastur hajmini
Dinamik dasturlashning asosiy g'oyasi? | Qism masalalar natijasini saqlab qayta ishlatish | Tasodifiy tanlash | Faqat rekursiyasiz yozish | Shifrlash
Greedy (ochko'z) algoritm nima? | Har qadamda lokal eng yaxshi tanlov qiladi | Hamma variantni ko'rib chiqadi | Tasodifiy tanlaydi | Teskari yuradi
Python da GIL nima? | Bir vaqtda faqat bitta oqim bayt-kodni bajarishini ta'minlovchi qulf | Grafik kutubxona | Fayl turi | Xato turi
Python da def f(a=[]) ko'rinishidagi funksiyada qanday muammo bor? | Ro'yxat chaqiruvlar orasida umumiy bo'lib qoladi | Sintaksis xatosi | Sekin ishlaydi | Muammo yo'q
Python da copy.deepcopy nima qiladi? | Ichki obyektlarni ham to'liq nusxalaydi | Faqat havolani nusxalaydi | Faylni nusxalaydi | Obyektni o'chiradi
Python da async def nima uchun ishlatiladi? | Asinxron (korutina) funksiya yaratish uchun | Tezroq funksiya uchun | Klass yaratish uchun | Modul yuklash uchun
Python da await nima qiladi? | Korutina natijasini kutadi, event loop ni bloklamaydi | Dasturni butunlay to'xtatadi | Yangi oqim yaratadi | Faylni yopadi
asyncio da bir nechta korutinani parallel yurituvchi funksiya? | asyncio.gather() | asyncio.merge() | asyncio.together() | asyncio.parallel()
Python da threading qaysi turdagi vazifalar uchun mos keladi? | I/O bilan bog'liq vazifalar | Faqat GPU hisoblari | Faqat og'ir matematik hisoblar | Hech qaysi
Python da __str__ metodi nima uchun kerak? | Obyektning o'qiladigan matn ko'rinishi uchun | Obyektni o'chirish uchun | Obyektni yaratish uchun | Klassni meros qilish uchun
Python da @staticmethod nima? | self olmaydigan metod | Klass yaratadi | Xususiy metod | Generator
Python da @property nima qiladi? | Metodni atribut kabi chaqirishga imkon beradi | Metodni o'chiradi | Klassni meros qiladi | Siklni to'xtatadi
Python da list va generator orasidagi xotira farqi? | Generator qiymatlarni kerak bo'lganda hosil qiladi | List kamroq xotira oladi | Farqi yo'q | Generator hamma narsani saqlaydi
Python da with bloki qaysi protokolga tayanadi? | Context manager (__enter__ / __exit__) | Iterator | Decorator | Metaclass
Python da if __name__ == "__main__" tekshiruvi nima uchun? | Fayl to'g'ridan-to'g'ri ishga tushirilganini aniqlash uchun | Faylni o'chirish uchun | Modulni import qilish uchun | Xatoni ushlash uchun
pip freeze > requirements.txt buyrug'i nima qiladi? | O'rnatilgan paketlar ro'yxatini faylga yozadi | Paketlarni o'chiradi | Paketlarni yangilaydi | Muhitni yaratadi
ACID dagi "A" harfi nimani anglatadi? | Atomicity | Availability | Authentication | Allocation
ACID dagi "I" harfi nimani anglatadi? | Isolation | Integration | Indexing | Inheritance
ACID dagi "D" harfi nimani anglatadi? | Durability | Distribution | Dependency | Dominance
Ma'lumotlar bazasida tranzaksiya nima? | Bitta mantiqiy birlik sifatida bajariladigan amallar guruhi | Jadval nomi | Parol | Fayl
Normallashtirish (normalization) maqsadi nima? | Ma'lumotlar takrorlanishini kamaytirish | Doim tezlikni oshirish | Shifrlash | Zaxira nusxa olish
SQL da INDEX nima uchun ishlatiladi? | Qidirishni tezlashtirish uchun | Jadvalni o'chirish uchun | Parolni saqlash uchun | Zaxira nusxa olish uchun
SQL INNER JOIN nimani qaytaradi? | Ikkala jadvalda mos kelgan qatorlarni | Faqat chap jadvalni | Hamma qatorlarni | Faqat o'ng jadvalni
SQL LEFT JOIN nimani qaytaradi? | Chap jadvalning hamma qatorlarini va mos kelganlarini | Faqat mos kelganlarini | O'ng jadvalning hamma qatorini | Hech narsani
SQL da HAVING qachon ishlatiladi? | Guruhlangan natijaga shart qo'yishda | Jadval yaratishda | Indeks yaratishda | Jadval o'chirishda
SQL Injection nima? | So'rovga zararli SQL kod kiritish hujumi | Tarmoq sekinlashishi | Disk xatosi | Antivirus turi
SQL Injection dan himoyalanishning asosiy usuli? | Parametrlangan so'rovlardan foydalanish | Parolni uzun qilish | Antivirus o'rnatish | Ekranni qulflash
XSS nima? | Sahifaga zararli skript kiritish hujumi | Ma'lumotlar bazasi | Tarmoq protokoli | Dasturlash tili
CSRF nima? | Foydalanuvchi nomidan kutilmagan so'rov yuborishga majburlash hujumi | Parolni taxmin qilish | DNS hujumi | Disk xatosi
DDoS hujumi nima? | Ko'p manbadan serverni so'rovlar bilan to'ldirish | Parol o'g'irlash | Virus yozish | Fayl shifrlash
Brute force hujumi nima? | Parolni ketma-ket sinab ko'rish | Tarmoq kabelini uzish | Rasmni o'zgartirish | Dasturni nusxalash
Parol hesh qilishda "salt" (tuz) nima uchun ishlatiladi? | Bir xil parollar turlicha hesh bersin uchun | Parolni qisqartirish uchun | Parolni ochiq saqlash uchun | Tezlik uchun
Simmetrik shifrlashda nechta kalit ishlatiladi? | Bitta umumiy kalit | Ikkita (ochiq va yopiq) | Uchta | Kalitsiz
Asimmetrik shifrlashga misol qaysi? | RSA | AES | DES | XOR
AES qanday turdagi shifr? | Simmetrik | Asimmetrik | Hesh funksiya | Siqish algoritmi
SHA-256 nima? | Hesh funksiyasi | Shifrlash kaliti | Tarmoq protokoli | Dasturlash tili
TLS nima uchun ishlatiladi? | Tarmoq aloqasini shifrlash uchun | Fayl siqish uchun | Rasm tahrirlash uchun | Domen olish uchun
JWT nima? | Tokenga asoslangan autentifikatsiya formati | Dasturlash tili | Ma'lumotlar bazasi | Antivirus
OAuth nima uchun ishlatiladi? | Parol bermasdan ruxsat berish (delegatsiya) uchun | Fayl siqish uchun | DNS uchun | Hesh qilish uchun
REST da PUT metodi odatda nima qiladi? | Resursni to'liq yangilaydi yoki almashtiradi | Faqat o'qiydi | Faqat o'chiradi | Yo'naltiradi
Quyidagilardan qaysi HTTP metodi idempotent hisoblanadi? | GET | POST | PATCH | Hech biri
HTTP 401 kodi nimani bildiradi? | Autentifikatsiya talab qilinadi | Topilmadi | OK | Server xatosi
HTTP 429 kodi nimani bildiradi? | Juda ko'p so'rovlar yuborilgan | Topilmadi | OK | Server o'chgan
HTTP 502 kodi nimani bildiradi? | Bad Gateway | Not Found | OK | Forbidden
CORS nima? | Brauzerda boshqa domenga so'rovlarni boshqarish siyosati | Dasturlash tili | Ma'lumotlar bazasi | Antivirus
Cookie nima? | Brauzerda saqlanadigan kichik ma'lumot | Virus | Dastur | Disk
CDN nima? | Kontentni dunyo bo'ylab serverlardan yetkazish tarmog'i | Dasturlash tili | Ma'lumotlar bazasi | Antivirus
Load balancer nima qiladi? | Yukni serverlar o'rtasida taqsimlaydi | Parol saqlaydi | Fayl siqadi | Rasm chizadi
Webhook nima? | Voqea yuz berganda URL ga avtomatik so'rov yuborish | Brauzer | Ma'lumotlar bazasi | Antivirus
Telegram botlarda long polling nima? | Bot serverdan yangilanishlarni so'rab turadi | Bot telefonni uzadi | Bot faylni o'chiradi | Bot internetsiz ishlaydi
Kernel mode va user mode orasidagi farq? | Kernel mode to'liq tizim huquqiga ega | User mode to'liq huquqli | Farqi yo'q | Kernel faqat o'yin uchun
Deadlock nima? | Jarayonlar bir-birini kutib qotib qolishi | Dastur tez ishlashi | Xotira to'lishi | Disk xatosi
Race condition nima? | Bir vaqtdagi kirish tufayli natijaning kutilmagan bo'lishi | Tezlik musobaqasi | Xotira tozalash | Disk xatosi
Mutex nima? | Umumiy resursga bir vaqtda bitta oqim kirishini ta'minlovchi qulf | Fayl turi | Ma'lumotlar bazasi | Protokol
Virtual xotira nima? | Disk yordamida RAM ni kengaytirish mexanizmi | Videokarta xotirasi | Bulut | Flesh disk
Paging nima? | Xotirani teng bo'laklarga bo'lib boshqarish | Faylni siqish | Parol hesh | Tarmoq marshruti
Cache nima? | Tez kirish uchun vaqtinchalik tezkor xotira | Doimiy disk | Parol | Virus
Context switch nima? | Protsessorning bir jarayondan boshqasiga o'tishi | Brauzerni almashtirish | OS ni o'zgartirish | Parolni almashtirish
Unix da "zombie" jarayon nima? | Tugagan, lekin ota jarayon holatini o'qimagan jarayon | Virus | Tezkor jarayon | Yangi jarayon
Linux da fayl ruxsati 755 nimani bildiradi? | Egasi rwx, boshqalar r-x | Hamma uchun rwx | Faqat o'qish | Hech kim kira olmaydi
Linux da chmod 777 nima qiladi? | Hamma uchun to'liq ruxsat beradi | Faqat egasiga ruxsat beradi | Hech kimga ruxsat bermaydi | Faqat o'qishga ruxsat beradi
Linux da pipe (vertikal chiziq) belgisi nima qiladi? | Bir buyruq chiqishini boshqasiga kirish qiladi | Faylni o'chiradi | Izoh yozadi | Papka yaratadi
Linux da > belgisi nima qiladi? | Chiqishni faylga yo'naltiradi | Faylni o'chiradi | Qiymatlarni taqqoslaydi | Izoh yozadi
Linux da tail -f buyrug'i nima qiladi? | Fayl oxirini real vaqtda kuzatadi | Faylni o'chiradi | Faylni siqadi | Faylni nusxalaydi
cron nima? | Vazifalarni jadval bo'yicha ishga tushiruvchi xizmat | Antivirus | Brauzer | Ma'lumotlar bazasi
systemd nima? | Linuxda xizmatlarni boshqaruvchi tizim | Brauzer | Ma'lumotlar bazasi | Antivirus
Docker va virtual mashina orasidagi farq nima? | Docker konteynerlari host yadrosini ulashadi | Docker alohida to'liq OS yadrosini ishga tushiradi | Farqi yo'q | VM yengilroq
Dockerfile nima? | Image yaratish ko'rsatmalari fayli | Parol fayli | Rasm | Ma'lumotlar bazasi
docker-compose nima uchun ishlatiladi? | Ko'p konteynerli ilovalarni boshqarish uchun | Brauzer sifatida | Antivirus sifatida | Rasm tahrirlash uchun
CI/CD nima? | Uzluksiz integratsiya va yetkazib berish | Dasturlash tili | Ma'lumotlar bazasi | Antivirus
Git rebase nima qiladi? | Commitlarni yangi asos ustiga ko'chiradi | Faylni o'chiradi | Repozitoriyni nusxalaydi | Parolni o'zgartiradi
Git da merge conflict qachon yuz beradi? | Bir xil joy turlicha o'zgartirilganda | Fayl katta bo'lganda | Internet uzilganda | Parol xato bo'lganda
git stash nima qiladi? | O'zgarishlarni vaqtincha chetga saqlaydi | Fayllarni o'chiradi | Serverga push qiladi | Repozitoriyni clone qiladi
git reset --hard nima qiladi? | O'zgarishlarni tashlab, holatni commitga qaytaradi | Faqat ko'rsatadi | Push qiladi | Clone qiladi
Semantik versiyalashda (1.4.2) o'rtadagi 4 nimani bildiradi? | MINOR versiya | MAJOR versiya | PATCH versiya | Build raqami
"Singleton" dizayn pattern i nimani ta'minlaydi? | Klassning faqat bitta nusxasi bo'lishini | Ko'p nusxa yaratishni | Faylni siqishni | Parol hesh qilishni
"Observer" pattern nima? | Obyektlar o'zgarishdan xabardor qilinadi | Faylni o'chirish | Parolni shifrlash | Tarmoq marshruti
SOLID dagi "S" harfi nimani bildiradi? | Single Responsibility | Simple Structure | Secure System | Static Syntax
DRY printsipi nimani anglatadi? | Don't Repeat Yourself | Do Repeat Yourself | Data Run Yearly | Debug Right Yesterday
MVC dagi "C" harfi nimani bildiradi? | Controller | Compiler | Cache | Client
Regex da \d nimani bildiradi? | Raqam | Harf | Bo'sh joy | Nuqta
Regex da * belgisi nimani bildiradi? | Oldingi belgidan nol yoki ko'p marta | Aynan bir marta | Hech qachon | Kamida bir marta
Unit test nima? | Kodning kichik qismini alohida sinash | Butun tizimni sinash | Antivirus | Foydalanuvchi sinovi
Code review nima? | Kodni hamkasblar tomonidan ko'rib chiqish | Kodni o'chirish | Kodni nusxalash | Kodni shifrlash
Microservices nima? | Ilovani kichik mustaqil xizmatlarga bo'lish | Bitta katta dastur | Mikro-protsessor | Mikrofon turi
Monolit arxitektura nima? | Barcha qismlar bitta birlik sifatida ishlaydi | Ko'p mustaqil xizmat | Bulutli funksiya | Faqat frontend
"""

LEVEL5_RAW = r"""
# Format: savol | TO'G'RI javob | xato 1 | xato 2 | xato 3
CAP teoremasidagi "C" harfi nimani bildiradi? | Consistency | Concurrency | Caching | Compression
CAP teoremasi bo'yicha tarmoq bo'linishi (P) paytida nimani tanlashga to'g'ri keladi? | Consistency yoki Availability dan birini | Hech narsadan voz kechmaslik | Faqat tezlikni | Faqat xavfsizlikni
Raft nima? | Konsensus algoritmi | Saralash algoritmi | Shifr | Fayl tizimi
Paxos nima? | Taqsimlangan konsensus protokoli | Brauzer | Dasturlash tili | Ma'lumotlar bazasi
Eventual consistency nima? | Yangilanishlar to'xtagach replikalar oxir-oqibat bir xil bo'ladi | Har doim bir zumda bir xil bo'ladi | Hech qachon bir xil bo'lmaydi | Faqat bitta replika bo'ladi
Sharding nima? | Ma'lumotni bir nechta bazaga bo'lib joylash | Parolni shifrlash | Jadvalni o'chirish | Indeks yaratish
Replikatsiya nima? | Ma'lumotni bir nechta tugunda nusxalash | Ma'lumotni siqish | Ma'lumotni shifrlash | Ma'lumotni saralash
B-tree ma'lumotlar bazalarida nima uchun keng qo'llaniladi? | Disk bilan samarali ishlash uchun | Rasm saqlash uchun | Tarmoq uchun | Shifrlash uchun
MVCC nima? | Ko'p versiyali parallellikni boshqarish | Rasm formati | Tarmoq protokoli | Shifr turi
Dirty read nima? | Hali commit qilinmagan o'zgarishni o'qish | Xato so'rov | Disk xatosi | Parol xatosi
Eng qat'iy SQL izolyatsiya darajasi qaysi? | Serializable | Read Uncommitted | Read Committed | Repeatable Read
Phantom read nima? | Takroriy so'rovda yangi qatorlar paydo bo'lishi | Disk xatosi | O'chib ketgan jadval | Xato parol
Write-ahead logging (WAL) nima uchun ishlatiladi? | O'zgarishni avval logga yozib, chidamlilikni ta'minlash uchun | Rasm saqlash uchun | Shifrlash uchun | Internetni tezlashtirish uchun
Coffman shartlaridan biri qaysi (deadlock uchun)? | Hold and wait | Fast fetch | Soft lock | Round trip
"Dining philosophers" masalasi nimaga oid? | Sinxronizatsiya va deadlock | Tarmoq | Shifrlash | Saralash
Semafor va mutex orasidagi farq nima? | Semafor bir nechta ruxsatni hisoblashi mumkin | Mutex ko'p ruxsat beradi | Farqi yo'q | Semafor faqat fayllar uchun
Round Robin rejalashtirish algoritmi nima qiladi? | Har jarayonga navbat bilan vaqt kvanti beradi | Eng qisqa jarayonni birinchi bajaradi | Tasodifiy tanlaydi | Faqat eng muhimini bajaradi
TCP da ulanish o'rnatish jarayoni qanday ataladi? | Three-way handshake | Two-way ping | Four-step login | One-way call
Three-way handshake ketma-ketligi qanday? | SYN, SYN-ACK, ACK | ACK, SYN, FIN | SYN, ACK, FIN | FIN, ACK, SYN
TCP da ulanishni yopishda ishlatiladigan bayroq qaysi? | FIN | SYN | URG | NEW
TCP congestion control maqsadi nima? | Tarmoq tiqilib qolmasligini ta'minlash | Parolni himoyalash | Faylni siqish | Domen hal qilish
TCP slow start nima? | Yuborish tezligini sekin boshlab, asta oshirish | Sekin internet | Xatoli ulanish | Faylni sekin o'qish
QUIC protokoli qaysi transport protokoli ustiga qurilgan? | UDP | TCP | ICMP | ARP
HTTP/3 qaysi protokolga asoslanadi? | QUIC | SPDY | FTP | SMTP
HTTP/2 ning asosiy yangiliklaridan biri? | Bitta ulanishda multiplekslash | Faqat matn yuborish | UDP ishlatish | Shifrlashni olib tashlash
BGP nima uchun ishlatiladi? | Internet tarmoqlari (AS) o'rtasida marshrutlash uchun | Email uchun | Fayl uzatish uchun | Domen olish uchun
ARP nima qiladi? | IP manzilni MAC manzilga bog'laydi | Domenni IP ga aylantiradi | Parolni hesh qiladi | Faylni siqadi
NAT nima? | Ichki IP manzillarni tashqi manzilga o'girish | Parol saqlash | Fayl siqish | Domen olish
ICMP protokolining mashhur qo'llanilishi qaysi? | ping | Email | Fayl yuklash | Veb sahifa ko'rish
DNS da A yozuvi nimani ko'rsatadi? | Domenning IPv4 manzilini | Pochta serverini | Domen egasini | Parolni
DNS da MX yozuvi nimani ko'rsatadi? | Pochta serverini | IPv6 manzilni | Taxallusni | Matnni
DNS da CNAME yozuvi nima? | Domen uchun taxallus (alias) | IPv4 manzil | Pochta serveri | Parol
Diffie-Hellman algoritmi nima uchun ishlatiladi? | Ochiq kanalda umumiy kalit kelishish uchun | Faylni siqish uchun | Saralash uchun | Hesh qilish uchun
Forward secrecy nima? | Kalit keyin oshkor bo'lsa ham eski sessiyalar himoyalangan qoladi | Parolni uzoq qilish | Tez shifrlash | Zaxira nusxa olish
Hesh to'qnashuvi (collision) nima? | Ikki xil kirishga bir xil hesh chiqishi | Heshning o'chib ketishi | Parolning unutilishi | Disk xatosi
Quyidagilardan qaysi biri parol hesh qilish uchun maxsus mo'ljallangan? | bcrypt | MD5 | CRC32 | Base64
Base64 nima? | Kodlash usuli (shifr emas) | Shifrlash algoritmi | Hesh funksiya | Siqish algoritmi
Zero-day zaiflik nima? | Ishlab chiqaruvchiga noma'lum, tuzatilmagan zaiflik | Eski virus | Nol kunlik reklama | Disk xatosi
Least privilege printsipi nima? | Faqat kerakli minimal huquqni berish | Hammaga to'liq huquq berish | Parolsiz kirish | Faqat admin ishlatishi
Man-in-the-middle hujumi nima? | Aloqani oraliqda tinglash yoki o'zgartirish | Serverni o'chirish | Parolni taxmin qilish | Diskni shifrlash
Ransomware nima? | Ma'lumotni shifrlab to'lov talab qiluvchi zararli dastur | Antivirus | Brauzer | Disk turi
CPython da xotira boshqaruvi asosan qanday ishlaydi? | Havolalarni sanash va chiqindi yig'uvchi orqali | Faqat qo'lda | Xotira boshqarilmaydi | Faqat GPU orqali
Python da MRO nima? | Metodlarni qidirish tartibi (Method Resolution Order) | Modul turi | Xato turi | Generator turi
Python da MRO uchun qaysi algoritm ishlatiladi? | C3 linearizatsiya | Faqat DFS | BFS | Tasodifiy tanlash
Python da __slots__ nima uchun ishlatiladi? | Xotirani tejash va atributlarni cheklash uchun | Faylni siqish uchun | Internetni tezlashtirish uchun | Modul yuklash uchun
Python da metaclass nima? | Klasslarni yaratuvchi klass | Modul | Dekorator | Generator
Python da yield from nima uchun ishlatiladi? | Ichki generatorga delegatsiya qilish uchun | Funksiyani to'xtatish uchun | Faylni yopish uchun | Klass yaratish uchun
asyncio da event loop nima? | Asinxron vazifalarni rejalashtirib bajaruvchi sikl | Oddiy for sikli | Xato turi | Modul turi
asyncio kodida bloklovchi funksiya (masalan, time.sleep) chaqirilsa nima bo'ladi? | Butun event loop to'xtab qoladi | Hech narsa | Kod tezlashadi | Yangi loop yaratiladi
Python multiprocessing GIL cheklovini qanday aylanib o'tadi? | Alohida jarayonlar ishlatadi | Oqimlar sonini oshiradi | GIL ni o'chiradi | Xotirani siqadi
Python da lug'at (dict) kaliti bo'la oladigan tur qaysi? | Hashable tur (masalan, tuple) | Faqat list | Faqat set | Har qanday obyekt
Python da in tekshiruvi list ga nisbatan set da nega tezroq? | Hesh jadval ishlatiladi, o'rtacha O(1) | Tartiblangan bo'lgani uchun | Siqilgan bo'lgani uchun | Parallel ishlagani uchun
Python ning sorted() va list.sort() funksiyalari qaysi algoritmdan foydalanadi? | Timsort | Quicksort | Bubble sort | Heapsort
Timsort ning eng yomon holatdagi murakkabligi? | O(n log n) | O(n) | O(n²) | O(log n)
Nega 0.1 + 0.2 aniq 0.3 chiqmaydi? | Ikkilik tizimda aniq ifodalanmaydi | Python xatosi | Protsessor buzuq | Kutubxona yo'q
IEEE 754 nimani belgilaydi? | Suzuvchi nuqtali sonlar standartini | Wi-Fi standartini | Fayl tizimini | Email protokolini
UTF-8 da ASCII belgilar necha bayt egallaydi? | 1 bayt | 2 bayt | 4 bayt | 8 bayt
UTF-8 da bitta belgi uzunligi qanday? | 1 dan 4 baytgacha | Doim 2 bayt | Doim 4 bayt | Doim 1 bayt
Endianness nima? | Baytlar tartibi (big/little endian) | Tarmoq turi | Hesh turi | Parol turi
Kompilyator va interpretator orasidagi farq? | Kompilyator butun kodni oldindan tarjima qiladi | Interpretator oldindan tarjima qiladi | Farqi yo'q | Kompilyator faqat HTML bilan ishlaydi
JIT kompilyatsiya nima? | Dastur ishlash paytida mashina kodiga tarjima qilish | Oldindan to'liq tarjima | Qo'lda tarjima | Shifrlash
Lexer (tokenizer) vazifasi nima? | Matnni tokenlarga ajratish | Mashina kodi yaratish | Xatolarni tuzatish | Fayl siqish
AST nima? | Abstrakt sintaksis daraxti | Avtomatik sinov tizimi | Tarmoq protokoli | Fayl turi
Garbage collector nima qiladi? | Foydalanilmayotgan xotirani bo'shatadi | Faylni o'chiradi | Parolni o'zgartiradi | Virusni topadi
Stack va heap xotira orasidagi farq nima? | Stack tez va avtomatik boshqariladi, heap dinamik | Heap har doim tezroq | Farqi yo'q | Stack cheksiz
Stack overflow xatosi odatda nimadan kelib chiqadi? | Juda chuqur rekursiya yoki katta stek | Disk to'lishi | Internet uzilishi | Parol xatosi
Memory leak nima? | Keraksiz xotira bo'shatilmay qolishi | Xotira tezligi | Xotira shifrlanishi | Disk xatosi
Cache coherence nima? | Ko'p yadroli CPU keshlarining izchilligi | Disk keshi | Brauzer keshi | DNS keshi
CPU pipeline nima? | Buyruqlarni bosqichlarga bo'lib bir vaqtda bajarish | Sovutish tizimi | Xotira turi | Disk turi
Amdahl qonuni nimani ifodalaydi? | Parallellashtirishdan olinadigan tezlanish chegarasini | Xotira hajmini | Tarmoq tezligini | Disk ishini
Moore qonuni (an'anaviy) nima haqida? | Chipdagi tranzistorlar soni taxminan ikki yilda ikki barobar oshishi | Tarmoq tezligi | Disk hajmi | Parol uzunligi
P va NP masalasi (P = NP?) hozirgi holati qanday? | Hal etilmagan (millennium) masala | Isbotlangan | Rad etilgan | Dasturlash tili
NP-to'liq masalaga misol qaysi? | Sayohatchi sotuvchi masalasi (qaror varianti) | Ikki sonni qo'shish | Massivni saralash | Binary search
Halting problem nima haqida? | Dastur to'xtashini umumiy holda aniqlab bo'lmasligi haqida | Tarmoq haqida | Xotira haqida | Parol haqida
Turing mashinasi nima? | Hisoblash nazariyasidagi nazariy model | Real kompyuter | Dastur | Brauzer
Big-O da O(2^n) qanday o'sish hisoblanadi? | Eksponensial | Chiziqli | Logarifmik | Kvadrat
Quyidagilardan qaysi biri eng tez o'sadi? | O(n!) | O(n²) | O(n log n) | O(2^n)
Kruskal algoritmi nima uchun ishlatiladi? | Minimal ostov daraxtini topish uchun | Eng qisqa yo'l uchun | Saralash uchun | Shifrlash uchun
A* algoritmi nima uchun ishlatiladi? | Evristika bilan yo'l qidirish uchun | Shifrlash uchun | Saralash uchun | Siqish uchun
Huffman kodlash nima uchun ishlatiladi? | Ma'lumotni siqish uchun | Shifrlash uchun | Saralash uchun | Tarmoq uchun
Bloom filter nima? | Ehtimoliy to'plamga a'zolikni tekshirish tuzilmasi | Rasm filtri | Parol filtri | Spam filtri
Bloom filterda qaysi turdagi xato bo'lishi mumkin? | Yolg'on musbat (false positive) | Yolg'on manfiy (false negative) | Ikkalasi ham | Hech qaysi
LRU cache nima? | Eng uzoq ishlatilmagan elementni chiqarib tashlaydi | Eng ko'p ishlatilganini chiqaradi | Tasodifiy chiqaradi | Eng kattasini chiqaradi
Consistent hashing nima uchun kerak? | Tugun qo'shilganda minimal ma'lumot ko'chishi uchun | Parol hesh qilish uchun | Fayl siqish uchun | Rasm saqlash uchun
Message queue (Kafka, RabbitMQ) nima uchun ishlatiladi? | Xizmatlar orasida asinxron xabar almashish uchun | Rasm saqlash uchun | Parol uchun | Antivirus uchun
Event sourcing nima? | Holatni voqealar ketma-ketligi sifatida saqlash | Rasm saqlash | Parol saqlash | Tarmoq turi
CQRS nima? | O'qish va yozish modellarini ajratish | Parol hesh qilish | Fayl siqish | Domen olish
Circuit breaker pattern nima? | Xatoli xizmatga so'rovlarni vaqtincha to'xtatish | Elektr uzgich | Fayl turi | Parol turi
Rate limiting nima? | So'rovlar sonini cheklash | Tezlikni oshirish | Faylni siqish | Parol saqlash
Blue-green deployment nima? | Ikki muhit orasida o'tib, to'xtovsiz yangilash | Rang sozlash | Parol almashtirish | Antivirus turi
Kubernetes nima? | Konteynerlarni orkestratsiya qilish tizimi | Dasturlash tili | Ma'lumotlar bazasi | Brauzer
Kubernetes da eng kichik joylashtirish birligi nima? | Pod | Node | Cluster | Image
Infrastructure as Code (IaC) vositasiga misol? | Terraform | Photoshop | Chrome | Excel
Observability ning uchta ustuni qaysilar? | Log, metrika, trace | Parol, hesh, token | CPU, RAM, disk | Front, back, baza
Gradient tushishi (gradient descent) nima qiladi? | Yo'qotishni kamaytirish uchun parametrlarni yangilaydi | Ma'lumotni o'chiradi | Rasmni siqadi | Parolni hesh qiladi
Overfitting nima? | Model o'quv ma'lumotiga haddan ortiq moslashishi | Modelning tez ishlashi | Xotira to'lishi | Disk xatosi
Transformer arxitekturasidagi asosiy mexanizm qaysi? | Self-attention | Faqat convolution | Faqat recurrence | Decision tree
Supervised learning nima? | Belgilangan (labeled) ma'lumot bilan o'qitish | Belgisiz ma'lumot bilan o'qitish | Mukofot bilan o'qitish | Faqat tasvir bilan o'qitish
Reinforcement learning nima? | Mukofot va jazo orqali o'rganish | Belgilangan ma'lumot bilan o'qitish | Faqat klasterlash | Faqat regressiya
LLM qisqartmasi nimani anglatadi? | Large Language Model | Long Logic Machine | Linear Learning Method | Local Language Module
Idempotent operatsiya nima? | Bir necha marta bajarilsa ham natija bir xil qoladigan | Faqat bir marta bajariladigan | Tez bajariladigan | Shifrlangan
Docker konteyneri izolyatsiyasi Linux da qaysi mexanizmlarga tayanadi? | Namespaces va cgroups | BIOS va UEFI | DNS va DHCP | SMTP va FTP
Linux da inode nima? | Fayl metama'lumotlarini saqlovchi tuzilma | Tarmoq interfeysi | Jarayon identifikatori | Foydalanuvchi paroli
Python da dict tartibi qaysi versiyadan boshlab kafolatlangan (qo'shilish tartibida)? | Python 3.7 | Python 2.7 | Python 3.0 | Python 3.12
"""

def _parse(level, raw):
    items = []
    for num, line in enumerate(raw.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(" | ")]
        if len(parts) != 5 or not all(parts) or len(set(parts[1:])) != 4:
            raise ValueError(f"{level}-daraja, {num}-qator noto'g'ri: {line!r}")
        items.append((parts[0], parts[1:]))  # (savol, [to'g'ri, xato, xato, xato])
    return items


QUESTIONS = {
    1: _parse(1, LEVEL1_RAW),
    2: _parse(2, LEVEL2_RAW),
    3: _parse(3, LEVEL3_RAW),
    4: _parse(4, LEVEL4_RAW),
    5: _parse(5, LEVEL5_RAW),
}
TOTAL = sum(len(v) for v in QUESTIONS.values())

# ======================================================================
#  3) MA'LUMOTLAR BAZASI (SQLite)
# ======================================================================
_lock = threading.RLock()
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_conn.row_factory = sqlite3.Row

with _lock, _conn:
    _conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY,
            full_name TEXT,
            username  TEXT,
            coins     INTEGER NOT NULL DEFAULT 0,
            score     INTEGER NOT NULL DEFAULT 0,
            wrong     INTEGER NOT NULL DEFAULT 0,
            joined    REAL
        );
        CREATE TABLE IF NOT EXISTS solved (
            user_id INTEGER,
            level   INTEGER,
            qidx    INTEGER,
            PRIMARY KEY (user_id, level, qidx)
        );
        CREATE TABLE IF NOT EXISTS pending (
            user_id INTEGER PRIMARY KEY,
            level   INTEGER,
            qidx    INTEGER,
            perm    TEXT
        );
        CREATE TABLE IF NOT EXISTS orders (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            prize   TEXT,
            cost    INTEGER,
            status  TEXT DEFAULT 'new',
            created REAL
        );
        """
    )


# ---------------- foydalanuvchilar ----------------
def upsert_user(u):
    name = (u.full_name or "Noma'lum")[:64]
    with _lock, _conn:
        _conn.execute(
            """INSERT INTO users(user_id, full_name, username, joined) VALUES(?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET full_name=excluded.full_name,
                                                  username=excluded.username""",
            (u.id, name, u.username, time.time()),
        )


def get_user(uid):
    with _lock:
        return _conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()


# ---------------- savollar / javoblar ----------------
def solved_set(uid, level):
    with _lock:
        rows = _conn.execute(
            "SELECT qidx FROM solved WHERE user_id=? AND level=?", (uid, level)
        ).fetchall()
    return {r["qidx"] for r in rows}


def solved_count(uid, level):
    with _lock:
        return _conn.execute(
            "SELECT COUNT(*) FROM solved WHERE user_id=? AND level=?", (uid, level)
        ).fetchone()[0]


def add_correct(uid, level, qidx):
    """Birinchi marta to'g'ri javob bo'lsagina coin beradi. True/False qaytaradi."""
    with _lock, _conn:
        cur = _conn.execute(
            "INSERT OR IGNORE INTO solved(user_id, level, qidx) VALUES(?,?,?)",
            (uid, level, qidx),
        )
        if cur.rowcount == 0:
            return False
        _conn.execute(
            "UPDATE users SET coins=coins+?, score=score+1 WHERE user_id=?",
            (COIN_PER_ANSWER, uid),
        )
        return True


def add_wrong(uid):
    with _lock, _conn:
        _conn.execute("UPDATE users SET wrong=wrong+1 WHERE user_id=?", (uid,))


def set_pending(uid, level, qidx, perm):
    with _lock, _conn:
        _conn.execute(
            "INSERT OR REPLACE INTO pending(user_id, level, qidx, perm) VALUES(?,?,?,?)",
            (uid, level, qidx, perm),
        )


def pop_pending(uid, level, qidx):
    """Mos keladigan savol bo'lsa o'chirib, variantlar tartibini qaytaradi."""
    with _lock, _conn:
        row = _conn.execute("SELECT * FROM pending WHERE user_id=?", (uid,)).fetchone()
        if not row or row["level"] != level or row["qidx"] != qidx:
            return None
        _conn.execute("DELETE FROM pending WHERE user_id=?", (uid,))
        return row["perm"]


# ---------------- reyting ----------------
def top(limit=10):
    with _lock:
        return _conn.execute(
            """SELECT user_id, full_name, score FROM users WHERE score>0
               ORDER BY score DESC, joined ASC LIMIT ?""",
            (limit,),
        ).fetchall()


def rank(uid):
    with _lock:
        return _conn.execute(
            """SELECT COUNT(*)+1 FROM users
               WHERE score > (SELECT score FROM users WHERE user_id=?)""",
            (uid,),
        ).fetchone()[0]


# ---------------- sovg'a buyurtmalari ----------------
def create_order(uid, prize, cost):
    """Coin yetarli bo'lsa yechib, buyurtma yaratadi. Yetmasa None."""
    with _lock, _conn:
        row = _conn.execute("SELECT coins FROM users WHERE user_id=?", (uid,)).fetchone()
        if not row or row["coins"] < cost:
            return None
        _conn.execute("UPDATE users SET coins=coins-? WHERE user_id=?", (cost, uid))
        cur = _conn.execute(
            "INSERT INTO orders(user_id, prize, cost, status, created) VALUES(?,?,?,?,?)",
            (uid, prize, cost, "new", time.time()),
        )
        return cur.lastrowid


def get_order(order_id):
    with _lock:
        return _conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()


def finish_order(order_id):
    """Buyurtmani 'berildi' deb belgilaydi (faqat yangi bo'lsa)."""
    with _lock, _conn:
        cur = _conn.execute(
            "UPDATE orders SET status='done' WHERE id=? AND status='new'", (order_id,)
        )
        return cur.rowcount == 1


def cancel_order(order_id, status):
    """Yangi buyurtmani bekor qiladi va coinni qaytaradi."""
    with _lock, _conn:
        row = _conn.execute(
            "SELECT * FROM orders WHERE id=? AND status='new'", (order_id,)
        ).fetchone()
        if not row:
            return False
        _conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        _conn.execute(
            "UPDATE users SET coins=coins+? WHERE user_id=?", (row["cost"], row["user_id"])
        )
        return True


# ---------------- admin statistika ----------------
def stats():
    with _lock:
        users = _conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        answers = _conn.execute("SELECT COALESCE(SUM(score),0) FROM users").fetchone()[0]
        new_orders = _conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status='new'"
        ).fetchone()[0]
        done_orders = _conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status='done'"
        ).fetchone()[0]
    return users, answers, new_orders, done_orders

# ======================================================================
#  4) BOT
# ======================================================================
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! .env faylni tekshiring.")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

LETTERS = "ABCD"

# ---------------- tugma matnlari ----------------
BTN_QUIZ = "🎮 Quiz boshlash"
BTN_TOP = "🏆 Reyting"
BTN_ME = "💰 Mening hisobim"
BTN_SHOP = "🎁 Sovg'alar"
BTN_CONTACT = "📞 Murojaat"
BTN_HELP = "ℹ️ Yordam"

MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_QUIZ)],
        [KeyboardButton(text=BTN_TOP), KeyboardButton(text=BTN_ME)],
        [KeyboardButton(text=BTN_SHOP), KeyboardButton(text=BTN_CONTACT)],
        [KeyboardButton(text=BTN_HELP)],
    ],
    resize_keyboard=True,
)

HELP_TEXT = (
    "ℹ️ <b>Bot haqida</b>\n\n"
    f"Bu IT bo'yicha quiz bot. Jami <b>{TOTAL}</b> ta savol, <b>{len(QUESTIONS)}</b> ta daraja.\n"
    f"✅ Har bir to'g'ri javob uchun <b>{COIN_PER_ANSWER}</b> coin beriladi.\n"
    f"🔓 Keyingi daraja ochilishi uchun oldingi darajada kamida "
    f"<b>{UNLOCK_CORRECT}</b> ta to'g'ri javob kerak.\n"
    "🎁 Yig'ilgan coinlarga sovg'a olishingiz mumkin.\n\n"
    "Pastdagi tugmalardan foydalaning 👇"
)


# ---------------- yordamchi funksiyalar ----------------
def need_for(level):
    return min(UNLOCK_CORRECT, len(QUESTIONS[level]))


def is_unlocked(uid, level):
    if level == 1:
        return True
    return solved_count(uid, level - 1) >= need_for(level - 1)


def user_link(u):
    name = html.escape(u["full_name"] or "Noma'lum")
    uname = f" (@{html.escape(u['username'])})" if u["username"] else ""
    return f'<a href="tg://user?id={u["user_id"]}">{name}</a>{uname}'


def levels_kb(uid):
    rows = []
    for lvl, (icon, name) in LEVEL_INFO.items():
        done = solved_count(uid, lvl)
        total = len(QUESTIONS[lvl])
        if is_unlocked(uid, lvl):
            text = f"{icon} {lvl}-daraja · {name} ({done}/{total})"
        else:
            text = f"🔒 {lvl}-daraja · {name}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"lvl:{lvl}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_question(chat_id, uid, level):
    solved = solved_set(uid, level)
    left = [i for i in range(len(QUESTIONS[level])) if i not in solved]
    if not left:
        nxt = ""
        if level < len(QUESTIONS):
            nxt = f"\nKeyingi {level + 1}-darajani tanlashingiz mumkin."
        await bot.send_message(
            chat_id,
            f"🎉 Siz {level}-darajadagi <b>barcha savollarni</b> yechdingiz!{nxt}",
            reply_markup=levels_kb(uid),
        )
        return

    qidx = random.choice(left)
    text, options = QUESTIONS[level][qidx]  # options[0] - to'g'ri javob
    order = list(range(4))
    random.shuffle(order)
    set_pending(uid, level, qidx, "".join(map(str, order)))

    icon, name = LEVEL_INFO[level]
    body = (
        f"{icon} <b>{level}-daraja · {name}</b>   "
        f"({len(solved)}/{len(QUESTIONS[level])})\n\n"
        f"❓ <b>{html.escape(text)}</b>\n\n"
    )
    for pos, orig in enumerate(order):
        body += f"<b>{LETTERS[pos]})</b> {html.escape(options[orig])}\n"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=LETTERS[p], callback_data=f"a:{level}:{qidx}:{p}")
                for p in range(4)
            ]
        ]
    )
    await bot.send_message(chat_id, body, reply_markup=kb)


# ---------------- /start va menyu ----------------
@dp.message(CommandStart())
async def cmd_start(m: Message):
    upsert_user(m.from_user)
    await m.answer(
        f"Assalomu alaykum, <b>{html.escape(m.from_user.full_name)}</b>! 👋\n\n"
        "IT quiz botiga xush kelibsiz!\n"
        f"To'g'ri javob berib coin yig'ing va sovg'alarga almashtiring.\n\n{HELP_TEXT}",
        reply_markup=MENU,
    )


@dp.message(F.text == BTN_HELP)
async def btn_help(m: Message):
    upsert_user(m.from_user)
    await m.answer(HELP_TEXT, reply_markup=MENU)


@dp.message(F.text == BTN_QUIZ)
async def btn_quiz(m: Message):
    upsert_user(m.from_user)
    await m.answer("📚 Darajani tanlang:", reply_markup=levels_kb(m.from_user.id))


@dp.message(F.text == BTN_ME)
async def btn_me(m: Message):
    upsert_user(m.from_user)
    u = get_user(m.from_user.id)
    total_answers = u["score"] + u["wrong"]
    percent = round(u["score"] * 100 / total_answers) if total_answers else 0
    lines = [
        "💰 <b>Mening hisobim</b>\n",
        f"🪙 Coin: <b>{u['coins']}</b>",
        f"✅ To'g'ri javoblar: <b>{u['score']}</b>",
        f"❌ Xato javoblar: <b>{u['wrong']}</b>",
        f"📈 Aniqlik: <b>{percent}%</b>",
        f"🏅 Reytingdagi o'rningiz: <b>{rank(u['user_id'])}</b>",
        "\n<b>Darajalar:</b>",
    ]
    for lvl, (icon, name) in LEVEL_INFO.items():
        lines.append(
            f"{icon} {lvl}-daraja: {solved_count(u['user_id'], lvl)}/{len(QUESTIONS[lvl])}"
        )
    await m.answer("\n".join(lines), reply_markup=MENU)


@dp.message(F.text == BTN_TOP)
async def btn_top(m: Message):
    upsert_user(m.from_user)
    rows = top(10)
    if not rows:
        await m.answer("Hozircha reyting bo'sh. Birinchi bo'lib javob bering! 🚀", reply_markup=MENU)
        return
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>O'quvchilar reytingi (TOP 10)</b>\n"]
    for i, r in enumerate(rows):
        mark = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{mark} {html.escape(r['full_name'] or 'Noma`lum')} — <b>{r['score']}</b> ball")
    me = get_user(m.from_user.id)
    lines.append(f"\n👤 Sizning o'rningiz: <b>{rank(me['user_id'])}</b> ({me['score']} ball)")
    await m.answer("\n".join(lines), reply_markup=MENU)


@dp.message(F.text == BTN_CONTACT)
async def btn_contact(m: Message):
    await m.answer(
        f"📞 Murojaat uchun: <b>{OWNER_PHONE}</b>\n"
        "Coinga sovg'a olganingizdan keyin ham shu raqam orqali bog'lanishingiz mumkin.",
        reply_markup=MENU,
    )


# ---------------- sovg'alar ----------------
def shop_kb():
    rows = [
        [InlineKeyboardButton(text=f"{name} — {cost} coin", callback_data=f"prize:{key}")]
        for key, (name, cost) in PRIZES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(F.text == BTN_SHOP)
async def btn_shop(m: Message):
    upsert_user(m.from_user)
    u = get_user(m.from_user.id)
    await m.answer(
        f"🎁 <b>Sovg'alar do'koni</b>\n\n🪙 Sizning coinlaringiz: <b>{u['coins']}</b>\n\n"
        "Kerakli sovg'ani tanlang 👇",
        reply_markup=shop_kb(),
    )


@dp.callback_query(F.data.startswith("prize:"))
async def cb_prize(c: CallbackQuery):
    key = c.data.split(":")[1]
    if key not in PRIZES:
        await c.answer()
        return
    name, cost = PRIZES[key]
    upsert_user(c.from_user)
    u = get_user(c.from_user.id)
    if u["coins"] < cost:
        await c.answer(
            f"Coin yetarli emas! Kerak: {cost}, sizda: {u['coins']}", show_alert=True
        )
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, olaman", callback_data=f"buy:{key}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="shopcancel"),
            ]
        ]
    )
    await c.message.answer(
        f"{name} uchun <b>{cost}</b> coin yechiladi.\nTasdiqlaysizmi?", reply_markup=kb
    )
    await c.answer()


@dp.callback_query(F.data == "shopcancel")
async def cb_shopcancel(c: CallbackQuery):
    await c.message.edit_text("Bekor qilindi.")
    await c.answer()


@dp.callback_query(F.data.startswith("buy:"))
async def cb_buy(c: CallbackQuery):
    key = c.data.split(":")[1]
    if key not in PRIZES:
        await c.answer()
        return
    name, cost = PRIZES[key]
    order_id = create_order(c.from_user.id, key, cost)
    if not order_id:
        await c.answer("Coin yetarli emas!", show_alert=True)
        return

    await c.message.edit_text(
        f"✅ <b>So'rovingiz qabul qilindi!</b>\n\n"
        f"🎁 Sovg'a: {name}\n🪙 Yechildi: {cost} coin\n🧾 Buyurtma raqami: <b>#{order_id}</b>\n\n"
        f"Bot egasi siz bilan bog'lanadi. Murojaat uchun: <b>{OWNER_PHONE}</b>"
    )
    await c.answer("Qabul qilindi ✅")

    # --- admin (bot egasi)ga xabar ---
    u = get_user(c.from_user.id)
    if ADMIN_ID:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Berildi", callback_data=f"adm_done:{order_id}"),
                    InlineKeyboardButton(text="🚫 Rad etish", callback_data=f"adm_rej:{order_id}"),
                ]
            ]
        )
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🔔 <b>Yangi sovg'a so'rovi #{order_id}</b>\n\n"
                f"👤 {user_link(u)}\n🆔 <code>{u['user_id']}</code>\n"
                f"🎁 {name}\n🪙 {cost} coin\n✅ To'g'ri javoblari: {u['score']}",
                reply_markup=kb,
            )
        except Exception as e:  # admin botni /start qilmagan bo'lishi mumkin
            logging.error("Adminga xabar yuborib bo'lmadi: %s", e)
    else:
        logging.warning("ADMIN_ID sozlanmagan! Buyurtma #%s adminga yuborilmadi.", order_id)


@dp.callback_query(F.data.startswith("adm_"))
async def cb_admin(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("Ruxsat yo'q", show_alert=True)
        return
    action, oid = c.data.split(":")
    order = get_order(int(oid))
    if not order:
        await c.answer("Buyurtma topilmadi", show_alert=True)
        return
    name = PRIZES.get(order["prize"], (order["prize"], 0))[0]

    if action == "adm_done":
        if not finish_order(order["id"]):
            await c.answer("Bu buyurtma allaqachon yopilgan", show_alert=True)
            return
        await c.message.edit_text(c.message.html_text + "\n\n✅ <b>BERILDI</b>")
        note = f"🎉 Sovg'angiz ({name}) berildi! Savollar bo'lsa: {OWNER_PHONE}"
    else:
        if not cancel_order(order["id"], "rejected"):
            await c.answer("Bu buyurtma allaqachon yopilgan", show_alert=True)
            return
        await c.message.edit_text(c.message.html_text + "\n\n🚫 <b>RAD ETILDI (coin qaytarildi)</b>")
        note = (
            f"😔 #{order['id']} buyurtmangiz ({name}) bajarilmadi, "
            f"{order['cost']} coin hisobingizga qaytarildi. Murojaat: {OWNER_PHONE}"
        )
    await c.answer("Bajarildi")
    try:
        await bot.send_message(order["user_id"], note)
    except Exception:
        pass


@dp.message(Command("stats"))
async def cmd_stats(m: Message):
    if m.from_user.id != ADMIN_ID:
        return
    users, answers, new_o, done_o = stats()
    await m.answer(
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"✅ Jami to'g'ri javoblar: <b>{answers}</b>\n"
        f"🆕 Yangi buyurtmalar: <b>{new_o}</b>\n"
        f"🎁 Berilgan sovg'alar: <b>{done_o}</b>"
    )


@dp.message(Command("id"))
async def cmd_id(m: Message):
    await m.answer(f"Sizning Telegram ID: <code>{m.from_user.id}</code>")


# ---------------- quiz ----------------
@dp.callback_query(F.data.startswith("lvl:"))
async def cb_level(c: CallbackQuery):
    level = int(c.data.split(":")[1])
    upsert_user(c.from_user)
    if level not in QUESTIONS:
        await c.answer()
        return
    if not is_unlocked(c.from_user.id, level):
        await c.answer(
            f"🔒 Bu daraja yopiq. {level - 1}-darajada kamida "
            f"{need_for(level - 1)} ta to'g'ri javob bering.",
            show_alert=True,
        )
        return
    await c.answer()
    await send_question(c.message.chat.id, c.from_user.id, level)


@dp.callback_query(F.data.startswith("a:"))
async def cb_answer(c: CallbackQuery):
    _, level, qidx, pos = c.data.split(":")
    level, qidx, pos = int(level), int(qidx), int(pos)
    uid = c.from_user.id
    upsert_user(c.from_user)

    perm = pop_pending(uid, level, qidx)
    if perm is None:
        await c.answer("Bu savolga allaqachon javob berilgan.", show_alert=True)
        return

    text, options = QUESTIONS[level][qidx]
    order = [int(ch) for ch in perm]
    correct_pos = order.index(0)
    chosen_ok = order[pos] == 0

    body = f"❓ <b>{html.escape(text)}</b>\n\n"
    for p, orig in enumerate(order):
        mark = "✅" if p == correct_pos else ("❌" if p == pos else "▫️")
        body += f"{mark} <b>{LETTERS[p]})</b> {html.escape(options[orig])}\n"

    if chosen_ok:
        gained = add_correct(uid, level, qidx)
        if gained:
            body += f"\n🎉 <b>To'g'ri!</b> +{COIN_PER_ANSWER} coin"
        else:
            body += "\n✅ To'g'ri (bu savol oldin yechilgan, coin berilmaydi)"
    else:
        add_wrong(uid)
        body += f"\n😔 <b>Noto'g'ri.</b> To'g'ri javob: <b>{LETTERS[correct_pos]}</b>"

    u = get_user(uid)
    body += f"\n🪙 Coinlaringiz: <b>{u['coins']}</b>"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Keyingi savol", callback_data=f"nxt:{level}")],
            [InlineKeyboardButton(text="📚 Darajalar", callback_data="levels")],
        ]
    )
    await c.message.edit_text(body, reply_markup=kb)
    await c.answer("✅ To'g'ri!" if chosen_ok else "❌ Noto'g'ri")

    # yangi daraja ochilganini xabar qilish
    if chosen_ok and level < len(QUESTIONS):
        if solved_count(uid, level) == need_for(level):
            await bot.send_message(
                c.message.chat.id,
                f"🔓 Tabriklaymiz! <b>{level + 1}-daraja</b> ochildi!",
                reply_markup=levels_kb(uid),
            )


@dp.callback_query(F.data.startswith("nxt:"))
async def cb_next(c: CallbackQuery):
    level = int(c.data.split(":")[1])
    await c.answer()
    await send_question(c.message.chat.id, c.from_user.id, level)


@dp.callback_query(F.data == "levels")
async def cb_levels(c: CallbackQuery):
    await c.answer()
    await c.message.answer("📚 Darajani tanlang:", reply_markup=levels_kb(c.from_user.id))


# ---------------- boshqa har qanday xabar ----------------
@dp.message()
async def fallback(m: Message):
    await m.answer(
        "Uzr, sizni tushunmadim 😕\nBotdan foydalanish uchun quyidagilardan birini tanlang:",
        reply_markup=MENU,
    )


async def main():
    if not ADMIN_ID:
        logging.warning("ADMIN_ID .env da yo'q — sovg'a so'rovlari egasiga yuborilmaydi!")
    logging.info("Savollar yuklandi: %s ta", TOTAL)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
