"""
srTCM.py

Single Rate Two-Colour Marker (RFC 2697) — Python Uygulaması

Renkler:
 - GREEN  = conform (CB içinde)
 - YELLOW = exceed (CB aşıldı)

Kova (bucket) kapasitesi: CB = CIR × Tc
Token üretim hızı: CIR (unit/saniye)
"""

import time
from typing import Literal

Color = Literal["green", "yellow"]

class SingleRateTwoColourMarker:
    def __init__(self, cir: float, tc: float, unit: str = "bytes"):
        """
        cir : Committed Information Rate (token üretim hızı, unit/s)
        tc  : Token yenileme aralığı (saniye)
        unit: "bytes" veya "bits" (yalnızca dokümantasyon için)
        """
        self.cir = cir
        self.tc = tc
        self.unit = unit

        # CB = CIR × Tc  → kovanın ana (green) bölümü
        self.cb = self.cir * self.tc  

        # capacity == CB (Two-color’da ekstra Be yok)
        self.capacity = self.cb  

        # Başlangıçta kova dolu kabul edilir
        self.tokens = self.capacity  

        # Son token ekleme zamanı
        self.last_update = time.time()

    def _add_tokens(self):
        """
        Zamana bağlı olarak kovaya yeni token ekle.
        elapsed = geçen süre (saniye)
        added   = elapsed × CIR  → üretilen token
        """
        now = time.time()
        elapsed = now - self.last_update
        if elapsed <= 0:
            return

        added = elapsed * self.cir
        # Kova doluluk oranını capacity'yi aşmadan güncelle
        self.tokens = min(self.tokens + added, self.capacity)
        self.last_update = now

    def mark_packet(self, size: int) -> Color:
        """
        Gelen paketi işaretle:
         - Eğer tokens ≥ size → GREEN (conform)
         - Aksi halde           → YELLOW (exceed)
        """
        # 1) Son ekleme zamanından bu yana geçen token'ları kova ekle
        self._add_tokens()

        # 2) Kova yeterliyse green, token düş
        if self.tokens >= size:
            self.tokens -= size
            return "green"

        # 3) Yeterli değilse yellow
        return "yellow"


def simulate_srTCM(
    cir: float,
    tc: float,
    pkt_size: int,
    interval: float,
    total_pkts: int
):
    """
    basit bir trafik simülasyonu:
     - cir       : token/saniye
     - tc        : saniyede kaç defa toplu ekleme
     - pkt_size  : her paketin boyutu (unit cinsinden)
     - interval  : paketler arası bekleme (saniye)
     - total_pkts: gönderilecek toplam paket sayısı
    """
    meter = SingleRateTwoColourMarker(cir, tc)
    print("\n🧪 srTCM Simulation Start")
    print(f"  CIR={cir:.0f} {meter.unit}/s | Tc={tc}s | CB={meter.cb:.0f} {meter.unit}\n")
    print("Idx |   Time   |  Tokens_before  | Packet_size | Color")
    print("----+----------+-----------------+-------------+--------")

    for i in range(total_pkts):
        # Klasifikasyondan önce güncel token sayısını al
        meter._add_tokens()
        tokens_before = meter.tokens

        color = meter.mark_packet(pkt_size)

        # Rapor
        print(f"{i:03d} | {time.strftime('%H:%M:%S')} | "
              f"{tokens_before:15.0f} | {pkt_size:11d} | {color.upper()}")

        time.sleep(interval)


if __name__ == "__main__":
    # Örnek parametreler:
    CIR        = 200_000   # 200 KB/s
    TC         = 0.1       # 100 ms
    PACKET_SZ  = 20000    # 50 KB
    INTERVAL   = 0.05      # 50 ms aralıkla trafik
    TOTAL_PKTS = 100

    simulate_srTCM(CIR, TC, PACKET_SZ, INTERVAL, TOTAL_PKTS)
