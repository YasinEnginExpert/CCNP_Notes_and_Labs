import time
from typing import Literal

Color = Literal["green", "yellow", "red"]

class SingleRateThreeColorMarker:
    """
    RFC 2697 Single-Rate Three-Colour Marker (Color-Blind mode).

    - cir : Committed Information Rate (unit/saniye)
    - cbs : Committed Burst Size (unit)
    - ebs : Excess Burst Size (unit)
    - unit: 'bytes' veya 'bits' (sadece dokümantasyon amaçlı)
    """
    def __init__(self, cir: float, cbs: float, ebs: float, unit: str = "bytes"):
        self.cir = cir
        self.cbs = cbs
        self.ebs = ebs
        self.unit = unit

        # Başlangıçta her iki kova da tam dolu:
        self.tc = self.cbs   # Tc(0) = CBS
        self.te = self.ebs   # Te(0) = EBS
        self.last_update = time.time()

    def _add_tokens(self):
        """
        Zaman içinde token ekleme (C ve E kovalarına):
        - dt × CIR kadar token üretilir.
        - Önce C (Tc < CBS ise), artan token'lar orada kullanılır.
        - Kalan token'lar E (Te < EBS ise) kovaya eklenir.
        """
        now = time.time()
        elapsed = now - self.last_update
        if elapsed <= 0:
            return
        self.last_update = now

        new_tokens = elapsed * self.cir

        # 1) Committed bucket (C)
        if self.tc < self.cbs:
            add_c = min(self.cbs - self.tc, new_tokens)
            self.tc += add_c
            new_tokens -= add_c

        # 2) Excess bucket (E)
        if new_tokens > 0 and self.te < self.ebs:
            add_e = min(self.ebs - self.te, new_tokens)
            self.te += add_e

    def mark_packet(self, size: float) -> Color:
        """
        Gelen paketi işaretle:
        - Eğer Tc ≥ size   → GREEN, Tc = Tc - size
        - elif Te ≥ size   → YELLOW, Te = Te - size
        - else             → RED (hiçbir kova azaltılmaz)

        Bu adımlar, “packet metering” kısmını oluşturur :contentReference[oaicite:1]{index=1}.
        """
        # 1) Yeni token ekle
        self._add_tokens()

        # 2) Renkli sınıflandırma
        if self.tc >= size:
            self.tc -= size
            return "green"
        elif self.te >= size:
            self.te -= size
            return "yellow"
        else:
            return "red"


def simulate_srTCM(
    cir: float,
    cbs: float,
    ebs: float,
    pkt_size: float,
    interval: float,
    total: int
):
    """
    Basit simülasyon:
     - cir, cbs, ebs: Marker parametreleri
     - pkt_size     : Her paketin boyutu
     - interval     : Paketler arası bekleme (s)
     - total        : Toplam paket sayısı
    """
    meter = SingleRateThreeColorMarker(cir, cbs, ebs)
    print(f"\n🧪 srTCM Simulation: CIR={cir}{meter.unit}/s, CBS={cbs}{meter.unit}, EBS={ebs}{meter.unit}\n")
    print("Idx |  Tc_before  |  Te_before  | Pkt_size | Color  |  Tc_after  |  Te_after")
    print("----+-------------+-------------+----------+--------+-------------+-------------")

    for i in range(total):
        meter._add_tokens()
        tc_b, te_b = meter.tc, meter.te
        color = meter.mark_packet(pkt_size)
        tc_a, te_a = meter.tc, meter.te

        print(f"{i:03d} | {tc_b:11.0f} | {te_b:11.0f} | {pkt_size:8.0f} | "
              f"{color.upper():6} | {tc_a:11.0f} | {te_a:11.0f}")
        time.sleep(interval)


if __name__ == "__main__":
    # Örnek kullanım:
    CIR       = 100_000    # 100 KB/s
    CBS       = 20_000     # 20 KB
    EBS       = 30_000     # 30 KB
    PKT_SIZE  = 15_000     # 15 KB
    INTERVAL  = 0.05       # 50 ms
    TOTAL_PKTS= 20

    simulate_srTCM(CIR, CBS, EBS, PKT_SIZE, INTERVAL, TOTAL_PKTS)
