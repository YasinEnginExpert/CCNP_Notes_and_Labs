"""
trTCM.py

Two-Rate Three-Colour Marker (RFC 2698) — Python Uygulaması

Renkler:
 - GREEN  = conform (Taahhütlü hız içinde)
 - YELLOW = exceed (Taahhütlü hız aşıldı ama peak hızı aşılmadı)
 - RED    = violate (Hem taahhütlü hem peak hız aşıldı)

Parametreler:
 - cir : Committed Information Rate (unit/s)
 - pir : Peak Information Rate      (unit/s)
 - cbs : Committed Burst Size      (unit)
 - pbs : Peak Burst Size           (unit)
"""

import time
from typing import Literal

Color = Literal["green", "yellow", "red"]

class TwoRateThreeColorMarker:
    def __init__(self,
                 cir: float, pir: float,
                 cbs: float, pbs: float,
                 unit: str = "bytes"):
        # Hızlar ve kovalar
        self.cir = cir    # Taahhütlü hız
        self.pir = pir    # Doruk hız
        self.cbs = cbs    # Taahhütlü patlama boyutu
        self.pbs = pbs    # Doruk patlama boyutu
        self.unit = unit

        # Başlangıçta her iki kova da tam dolu:
        self.tokens_c = cbs
        self.tokens_p = pbs

        # Zaman takibi
        self.last_update = time.time()

    def _add_tokens(self):
        """Zaman geçen kadar token üretir ve kovalara ekler."""
        now = time.time()
        elapsed = now - self.last_update
        if elapsed <= 0:
            return
        self.last_update = now

        # Üretilen token miktarı
        new_tokens_c = elapsed * self.cir
        new_tokens_p = elapsed * self.pir

        # Taahhütlü kova (C)
        self.tokens_c = min(self.tokens_c + new_tokens_c, self.cbs)
        # Doruk kova (P)
        self.tokens_p = min(self.tokens_p + new_tokens_p, self.pbs)

    def mark_packet(self, size: float) -> Color:
        """
        Gelen paketi işaretle:
          1) Eğer tokens_c ≥ size:
               → GREEN (conform)
               → tokens_c -= size
               → tokens_p -= size
          2) Elif tokens_p ≥ size:
               → YELLOW (exceed)
               → tokens_p -= size
          3) Aksi halde:
               → RED (violate)
        """
        # 1) Kovaları güncelle
        self._add_tokens()

        # 2) Green kontrolü
        if self.tokens_c >= size:
            self.tokens_c -= size
            # Green için peak kovasını da törpüle
            self.tokens_p = max(self.tokens_p - size, 0)
            return "green"

        # 3) Yellow kontrolü
        if self.tokens_p >= size:
            self.tokens_p -= size
            return "yellow"

        # 4) Red
        return "red"


def simulate_trTCM(cir, pir, cbs, pbs, pkt_size, interval, total_pkts):
    meter = TwoRateThreeColorMarker(cir, pir, cbs, pbs)
    header = (
        f"\n🧪 trTCM Simulation\n"
        f" CIR={cir}{meter.unit}/s, PIR={pir}{meter.unit}/s\n"
        f" CBS={cbs}{meter.unit}, PBS={pbs}{meter.unit}\n"
    )
    print(header)
    print("Idx |  C_before  |  P_before  | Pkt_sz | Color  |  C_after  |  P_after")
    print("----+------------+------------+--------+--------+-----------+-----------")

    for i in range(total_pkts):
        # Kova durumunu almadan önce token ekle
        meter._add_tokens()
        c_b, p_b = meter.tokens_c, meter.tokens_p

        color = meter.mark_packet(pkt_size)

        c_a, p_a = meter.tokens_c, meter.tokens_p
        print(f"{i:03d} | {c_b:10.0f} | {p_b:10.0f} | "
              f"{pkt_size:6.0f} | {color.upper():6} | "
              f"{c_a:9.0f} | {p_a:9.0f}")
        time.sleep(interval)


if __name__ == "__main__":
    # Örnek parametreler
    CIR        = 100_000   # 100 KB/s
    PIR        = 200_000   # 200 KB/s
    CBS        = 20_000    # 20 KB
    PBS        = 40_000    # 40 KB
    PKT_SIZE   = 15_000    # 15 KB
    INTERVAL   = 0.05      # 50 ms
    TOTAL_PKTS = 20

    simulate_trTCM(CIR, PIR, CBS, PBS, PKT_SIZE, INTERVAL, TOTAL_PKTS)
