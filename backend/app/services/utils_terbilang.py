def terbilang(n: int) -> str:
    """Angka ke kata Indonesia (sederhana, untuk narasi BA)."""
    satuan = ["", "Satu", "Dua", "Tiga", "Empat", "Lima", "Enam", "Tujuh", "Delapan", "Sembilan"]
    belasan = ["Sepuluh", "Sebelas", "Dua Belas", "Tiga Belas", "Empat Belas",
               "Lima Belas", "Enam Belas", "Tujuh Belas", "Delapan Belas", "Sembilan Belas"]

    def _below_thousand(x: int) -> str:
        if x == 0:
            return ""
        if x < 10:
            return satuan[x]
        if x < 20:
            return belasan[x - 10]
        if x < 100:
            puluh, sisa = divmod(x, 10)
            return f"{satuan[puluh]} Puluh" + (f" {satuan[sisa]}" if sisa else "")
        if x < 200:
            return "Seratus" + (f" {_below_thousand(x - 100)}" if x > 100 else "")
        ratus, sisa = divmod(x, 100)
        return f"{satuan[ratus]} Ratus" + (f" {_below_thousand(sisa)}" if sisa else "")

    if n == 0:
        return "Nol"
    if n < 1000:
        return _below_thousand(n).strip()
    if n < 1_000_000:
        ribu, sisa = divmod(n, 1000)
        head = "Seribu" if ribu == 1 else f"{_below_thousand(ribu)} Ribu"
        return (head + (f" {_below_thousand(sisa)}" if sisa else "")).strip()
    juta, sisa = divmod(n, 1_000_000)
    head = f"{_below_thousand(juta)} Juta"
    if sisa:
        return (head + " " + terbilang(sisa)).strip()
    return head.strip()