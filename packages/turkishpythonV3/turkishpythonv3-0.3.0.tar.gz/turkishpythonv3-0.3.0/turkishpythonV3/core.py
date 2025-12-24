
import builtins

KOMUTLAR = {
    "çıktı": "print",
    "girdi": "input",
    "uzunluk": "len",
    "liste": "list",
    "ekle": "list.append",
    "sil": "list.remove",
    "eğer": "if",
    "değilse_eğer": "elif",
    "değilse": "else",
}

def çıktı(*a, **k): print(*a, **k)
def girdi(m=""): return input(m)
def uzunluk(x): return len(x)
def liste(*a): return list(a)
def ekle(x, y): x.append(y)
def sil(x, y): x.remove(y)

def çalıştır(kod: str):
    for tr, py in {
        "eğer ": "if ",
        "değilse_eğer ": "elif ",
        "değilse:": "else:"
    }.items():
        kod = kod.replace(tr, py)
    exec(kod, builtins.__dict__)

def help():
    print("TURKISHPYTHON V3 – TÜRKÇE ↔ PYTHON KOMUTLARI\n")
    for k, v in KOMUTLAR.items():
        print(f"{k:<15} -> {v}")
