# token_bucket.py
from __future__ import annotations
import time
import threading
from dataclasses import dataclass, field
from typing import Literal, Callable


Unit = Literal["bytes", "bits"]


@dataclass
class TokenBucket:
    """CIR-Tc-Be tabanlı Token Bucket.

    Args:
        cir: Committed Information Rate (unit/s).
        tc:  Token yenileme aralığı (saniye).
        be:  Excess Burst (unit).
        unit: 'bytes' veya 'bits'
        start_full: Başlangıçta kovayı CB+Be kadar doldur.
    """
    cir: float
    tc: float
    be: int
    unit: Unit = "bytes"
    start_full: bool = True

    _tokens: float = field(init=False, repr=False)
    _capacity: float = field(init=False, repr=False)
    _lock: threading.Lock = field(init=False, repr=False, default_factory=threading.Lock)
    _last_update: float = field(init=False, repr=False, default_factory=time.time)

    def __post_init__(self):
        self.cb: float = self.cir * self.tc         # Committed Burst
        self._capacity = self.cb + self.be          # Toplam kova kapasitesi
        self._tokens = self._capacity if self.start_full else 0

    # ---------- İç mekanizma ----------
    def _add_tokens(self) -> None:
        """Geçen süreyi hesaplayıp kovaya token ekler."""
        now = time.time()
        elapsed = now - self._last_update
        if elapsed <= 0:
            return
        added = elapsed * self.cir
        self._tokens = min(self._tokens + added, self._capacity)
        self._last_update = now

    # ---------- Dış API ----------
    def check(self, size: int, mark_exceed: bool = True) -> Literal["conform", "exceed", "violate"]:
        """Paketi değerlendir.  
        * conform → CB içindeyse  
        * exceed  → CB bitti, Be’den yiyor  
        * violate → Toplam kapasite yetersiz
        """
        with self._lock:
            self._add_tokens()

            if self._tokens >= size:
                self._tokens -= size
                return "conform"

            elif mark_exceed and (self._tokens + self.be) >= size:
                # CB yetersiz, Excess Burst kullan
                deficit = size - self._tokens
                self.be -= deficit
                self._tokens = 0
                return "exceed"

            else:
                return "violate"

    # ---------- Yardımcılar ----------
    def __call__(self, func: Callable) -> Callable:
        """@TokenBucket(...) dekoratörü – fonksiyon çağrı frekansını sınırlar.

        Fonksiyon arg. uzunluğunu paket boyutu olarak kabul eder veya
        `size` kw-arg’ı verirseniz onu kullanır.
        """
        def wrapper(*args, **kwargs):
            pkt_size = kwargs.pop("size", 1)
            status = self.check(pkt_size)
            if status == "violate":
                raise RuntimeError("Rate-limit: packet dropped (violate)")
            return func(*args, **kwargs)
        return wrapper

    # Bilgilendirme
    @property
    def tokens(self) -> float:
        self._add_tokens()
        return self._tokens
"""
 -> conform satırları: CB içinde kalıyoruz, hem token hem patlama alanımız yeterli.

 -> exceed satırı ilk kez göründüğünde, CB dolmuş ama Be hâlâ var; cihaz renk işaretleyip (CoS/DSCP) iletebilir.

 -> violate satırları: CB + Be tamamen tükenmiş; cihaz paketi atar veya şekillendirici ise kuyruğa koyar.

"""





if __name__ == "__main__":
    tb = TokenBucket(cir=100_000,   # 1 Mbit/s ≈ 125 kB/s
                     tc=0.1,      # 125 ms 	Token’ların kovaya eklenme aralığı.
                     be=30_000,     # 32 kB excess 	Fazla patlama (Excess Burst) boyutu.
                     unit="bytes")  # Byte mı, bit mi?

    # Bir standart Ethernet çerçevesi uzunluğu. Her döngüde bu büyüklükte “paket” kovaya sunulacak.
    pkt = 5000  # 1 Ethernet frame (bytes)

    for i in range(30):
        status = tb.check(pkt)
        print(f"{i:02d}: {status:8} | tokens={tb.tokens:,.0f}")
        time.sleep(0.05)

"""
--------------
Senaryo 1
--------------
cir = 100_000      # 100 KB/s
tc  = 0.1          # 100 ms
be  = 0            # patlama yok
pkt = 1000         # 1000 byte paket
--------------
Senaryo 2
--------------
cir = 100_000      # 100 KB/s
tc  = 0.1          # 100 ms
be  = 30_000       # 30 KB excess
pkt = 5000         # 5 KB paket
--------------
Senaryo 3
--------------
cir = 20_000        # 20 KB/s
tc  = 0.1           # 100 ms
be  = 0
pkt = 10_000        # 10 KB paket
--------------
Senaryo 4
--------------
cir = 1_000_000     # 1 MB/s
tc  = 0.2           # 200 ms
be  = 100_000       # 100 KB
pkt = 20_000        # 20 KB/paket
--------------
Senaryo 5
--------------
"""



