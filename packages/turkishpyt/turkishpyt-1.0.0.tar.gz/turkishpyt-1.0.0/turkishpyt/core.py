
import time, math, random, statistics, os, sys, datetime, json

# ================== TEMEL ==================
def çıktı(*a, **k): print(*a, **k)
def girdi(m=""): return input(m)
def uzunluk(x): return len(x)
def tür(x): return type(x)
def kimlik(x): return id(x)
def hashle(x): return hash(x)
def doğru_mu(x): return bool(x)
def hepsi(x): return all(x)
def herhangi(x): return any(x)
def say(x): return len(x)
def göster(x): return repr(x)
def karakter(x): return chr(x)
def kod(x): return ord(x)
def çalıştır(x): exec(x)

# ================== KOLEKSİYON ==================
def liste(*a): return list(a)
def sözlük(**k): return dict(k)
def küme(*a): return set(a)
def demet(*a): return tuple(a)
def aralık(*a): return range(*a)
def sırala(x): return sorted(x)
def tersine(x): return list(reversed(x))
def ekle(x, y): x.append(y)
def sil(x, y): x.remove(y)
def temizle(x): x.clear()
def kopyala(x): return x.copy()
def birleştir(x, y): x.extend(y)
def sayısı(x, y): return x.count(y)
def index(x, y): return x.index(y)
def anahtarlar(x): return list(x.keys())
def değerler(x): return list(x.values())
def öğeler(x): return list(x.items())
def güncelle(x, y): x.update(y)
def eşsiz(x): return list(set(x))

# ================== SAYISAL ==================
def toplam(x): return sum(x)
def en_büyük(x): return max(x)
def en_küçük(x): return min(x)
def mutlak(x): return abs(x)
def yuvarla(x, n=0): return round(x, n)
def üs(a, b): return pow(a, b)
def karekök(x): return math.sqrt(x)
def taban(x): return math.floor(x)
def tavan(x): return math.ceil(x)
def kalan(a, b): return a % b
def ortalama(x): return statistics.mean(x)
def medyan(x): return statistics.median(x)
def varyans(x): return statistics.variance(x)
def faktoriyel(x): return math.factorial(x)
def sinüs(x): return math.sin(x)
def kosinüs(x): return math.cos(x)
def tanjant(x): return math.tan(x)
def logaritma(x, b=10): return math.log(x, b)

# ================== METİN ==================
def büyük_harf(x): return x.upper()
def küçük_harf(x): return x.lower()
def böl(x, a=" "): return x.split(a)
def birleştir_metin(x, a=""): return a.join(x)
def değiştir(x, a, b): return x.replace(a, b)
def başlıyor_mu(x, a): return x.startswith(a)
def bitiyor_mu(x, a): return x.endswith(a)
def içeriyor_mu(x, a): return a in x
def kırp(x): return x.strip()
def sağ_kırp(x): return x.rstrip()
def sol_kırp(x): return x.lstrip()
def sayı_mı(x): return x.isdigit()
def harf_mi(x): return x.isalpha()
def alfasayısal_mı(x): return x.isalnum()
def başlık(x): return x.title()
def ilk_büyük(x): return x.capitalize()
def sayıya_çevir(x): return int(x)
def yazıya_çevir(x): return str(x)
def formatla(x, *a, **k): return x.format(*a, **k)

# ================== ZAMAN ==================
def bekle(s): time.sleep(s)
def şimdi(): return datetime.datetime.now()
def zaman(): return time.time()
def ölç(): return time.perf_counter()

# ================== RASTGELE ==================
def rastgele_sayı(a, b): return random.randint(a, b)
def rastgele_ondalık(): return random.random()
def rastgele_seç(x): return random.choice(x)
def karıştır(x): random.shuffle(x)

# ================== DOSYA / JSON ==================
def json_yükle(yol):
    with open(yol, "r", encoding="utf-8") as f:
        return json.load(f)

def json_kaydet(yol, veri):
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)

# ================== SİSTEM ==================
def klasör(): return os.getcwd()
def değiştir(yol): os.chdir(yol)
def listele(yol="."): return os.listdir(yol)
def var_mı(yol): return os.path.exists(yol)
def dosya_mı(yol): return os.path.isfile(yol)
def klasör_mü(yol): return os.path.isdir(yol)
def oluştur(yol): os.mkdir(yol)
def sil_dosya(yol): os.remove(yol)
def çalıştır_sistem(x): os.system(x)
def çık(): sys.exit()

# ================== HELP ==================
def help():
    print("TURKISHPYT – TÜRKÇE PYTHON KOMUTLARI")
