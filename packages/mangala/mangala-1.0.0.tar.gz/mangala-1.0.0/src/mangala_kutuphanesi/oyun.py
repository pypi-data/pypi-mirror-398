# mangala-paket/src/mangala_kutuphanesi/oyun.py

# --- Dil ve Metin Yönetimi ---
metinler = {
    'tr': {
        'menu_baslik': "--- TÜRK MANGALASI ---",
        'menu_oyna': "1. Oyna",
        'menu_kurallar': "2. Kurallar",
        'menu_cikis': "3. Çıkış",
        'secim_yap': "Seçiminiz: ",
        'gecersiz_secim': "Geçersiz seçim. Lütfen menüden bir numara girin.",
        'cikis_mesaji': "Oyundan çıkılıyor. Görüşmek üzere!",
        'oyun_basladi': "Türk Mangalası oyunu başladı!",
        'sira_oyuncuda': ">>> Sıra Oyuncu {}'de.",
        'kuyu_sec_prompt': "Oyuncu {}, oynamak istediğiniz kuyu (1-6): ",
        'gecersiz_sayi_girisi': "Lütfen geçerli bir sayı girin.",
        'gecersiz_kuyu_secimi': "Hata: Geçersiz kuyu numarası. Lütfen 1-6 arasında kendi kuyunuzu seçin.",
        'bos_kuyu_hatasi': "Hata: Boş bir kuyudan oynayamazsınız.",
        'tekrar_oynuyor': "Son taş hazineye geldi! Oyuncu {} tekrar oynuyor.",
        'rakip_ciftlendi': "Rakip kuyudaki taşları çiftledin! Oyuncu {} o kuyuyu kazandı.",
        'bos_kuyu_kazanci': "Kendi boş kuyuna son taşı attın! Oyuncu {} karşıdaki taşları kazandı.",
        'oyun_bitti_baslik': "\n" + "#"*20 + " OYUN BİTTİ " + "#"*20,
        'final_skor': "Final Skoru: Oyuncu 1 ({}) - Oyuncu 2 ({})",
        'kazanan_mesaji': "Kazanan: Oyuncu {}!",
        'berabere_mesaji': "Sonuç: Berabere!",
        'kurallara_don': "\nAna menüye dönmek için Enter'a basın...",
        'kurallar_metni': """
# Türk Mangala Kuralları

1. Oyun Malzemeleri
- 1 adet mangala tahtası: Her iki oyuncu için 6’şar küçük çukur ve 2 büyük depo (hazine) bulunur.
- 48 adet taş: Her küçük çukura 4 taş olacak şekilde dağıtılır.

2. Oyunun Amacı
- Kendi hazinenize mümkün olduğunca fazla taş toplamak. En çok taşı olan kazanır.

3. Oyun Akışı
- Sırası gelen oyuncu kendi tarafındaki bir kuyudan tüm taşları alır.
- Kuyuda 1 taş varsa, o taşı bir sonraki kuyuya bırakır.
- Kuyuda 1'den fazla taş varsa, 1 tanesini aldığı kuyuya geri bırakır, kalanları saat yönünün tersine (sağa doğru) birer birer dağıtır.
- Dağıtım kendi hazinesini de kapsar ama rakibin hazinesine taş bırakılmaz.

4. Özel Kazanma Kuralları
- TEKRAR OYNAMA: Dağıtılan son taş oyuncunun kendi hazinesine denk gelirse, oyuncu bir hak daha kazanır.
- RAKİBİN TAŞLARINI ALMA (ÇİFTLEME): Dağıtılan son taş, rakibin kuyusundaki taş sayısını çift yaparsa (2, 4, 6 gibi), oyuncu o kuyudaki tüm taşları kazanır ve kendi hazinesine koyar.
- BOŞ KUYU KURALI: Dağıtılan son taş, oyuncunun kendi tarafındaki boş bir kuyuya denk gelirse ve bu kuyunun karşısındaki rakip kuyuda taş varsa, oyuncu hem kendi taşını hem de rakibin karşısındaki kuyudaki tüm taşları kazanır.

5. Oyun Sonu
- Bir oyuncunun tarafındaki tüm küçük kuyular boşaldığında oyun biter.
- Diğer oyuncu, kendi tarafında kalan tüm taşları kendi hazinesine ekler.
- Hazinesinde en çok taşı olan oyuncu oyunu kazanır.
"""
    }
}

class MangalaTurkOyunu:
    def __init__(self, dil='tr'):
        self.tahta = [4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 4, 4, 4, 0]
        self.mevcut_oyuncu = 1
        self.oyun_bitti_mi = False
        self.kazanan = None
        self.dil = dil
        self.metin = metinler[dil]
        print(self.metin['oyun_basladi'])

    def _kendi_hazine_indeksi(self):
        return 6 if self.mevcut_oyuncu == 1 else 13

    def _rakip_hazine_indeksi(self):
        return 13 if self.mevcut_oyuncu == 1 else 6

    def _oyuncu_kuyulari_indeksleri(self):
        return range(0, 6) if self.mevcut_oyuncu == 1 else range(7, 13)

    def _rakip_kuyulari_indeksleri(self):
        return range(7, 13) if self.mevcut_oyuncu == 1 else range(0, 6)
    
    def _karsi_kuyu_indeksi(self, kuyu_indeksi):
        return 12 - kuyu_indeksi

    def _sira_degistir(self):
        self.mevcut_oyuncu = 2 if self.mevcut_oyuncu == 1 else 1

    def tahtayi_goster(self):
        oyuncu2_kuyular = " ".join(f"[{self.tahta[i]:2}]" for i in range(7, 13))
        oyuncu1_kuyular = " ".join(f"[{self.tahta[i]:2}]" for i in range(0, 6))
        
        kuyu_numaralari = "   ".join(str(i) for i in range(1, 7))

        print("\n" + "="*50)
        print("                 Oyuncu 2")
        print(f"        {kuyu_numaralari}")
        print(f"       {oyuncu2_kuyular}")
        print(f"   [{self.tahta[13]:2}] {' '*35} [{self.tahta[6]:2}]")
        print(f"       {oyuncu1_kuyular}")
        print(f"        {kuyu_numaralari}")
        print("                 Oyuncu 1")
        print("="*50)
        if not self.oyun_bitti_mi:
            print(self.metin['sira_oyuncuda'].format(self.mevcut_oyuncu))

    def oyna(self, kuyu_numarasi):
        if not (1 <= kuyu_numarasi <= 6):
            print(self.metin['gecersiz_kuyu_secimi'])
            return False

        kuyu_indeksi_offset = kuyu_numarasi - 1
        kuyu_indeksi = kuyu_indeksi_offset if self.mevcut_oyuncu == 1 else kuyu_indeksi_offset + 7

        taslar_elde = self.tahta[kuyu_indeksi]
        if taslar_elde == 0:
            print(self.metin['bos_kuyu_hatasi'])
            return False

        if taslar_elde == 1:
            self.tahta[kuyu_indeksi] = 0
        else:
            self.tahta[kuyu_indeksi] = 1
            taslar_elde -= 1
        
        mevcut_pozisyon = kuyu_indeksi

        while taslar_elde > 0:
            mevcut_pozisyon = (mevcut_pozisyon + 1) % 14
            if mevcut_pozisyon == self._rakip_hazine_indeksi():
                continue
            self.tahta[mevcut_pozisyon] += 1
            taslar_elde -= 1

        son_tasin_dustugu_kuyu = mevcut_pozisyon

        if son_tasin_dustugu_kuyu == self._kendi_hazine_indeksi():
            print(self.metin['tekrar_oynuyor'].format(self.mevcut_oyuncu))
            self._oyun_sonu_kontrolu()
            return True

        elif son_tasin_dustugu_kuyu in self._rakip_kuyulari_indeksleri():
            if self.tahta[son_tasin_dustugu_kuyu] % 2 == 0:
                print(self.metin['rakip_ciftlendi'].format(self.mevcut_oyuncu))
                kazanilan_taslar = self.tahta[son_tasin_dustugu_kuyu]
                self.tahta[self._kendi_hazine_indeksi()] += kazanilan_taslar
                self.tahta[son_tasin_dustugu_kuyu] = 0
        
        elif son_tasin_dustugu_kuyu in self._oyuncu_kuyulari_indeksleri():
            if self.tahta[son_tasin_dustugu_kuyu] == 1:
                karsi_kuyu = self._karsi_kuyu_indeksi(son_tasin_dustugu_kuyu)
                if self.tahta[karsi_kuyu] > 0:
                    print(self.metin['bos_kuyu_kazanci'].format(self.mevcut_oyuncu))
                    kazanilan_taslar = self.tahta[karsi_kuyu] + 1
                    self.tahta[self._kendi_hazine_indeksi()] += kazanilan_taslar
                    self.tahta[karsi_kuyu] = 0
                    self.tahta[son_tasin_dustugu_kuyu] = 0

        self._sira_degistir()
        self._oyun_sonu_kontrolu()
        return True

    def _oyun_sonu_kontrolu(self):
        if self.oyun_bitti_mi: return

        oyuncu1_kuyulari_bos = all(self.tahta[i] == 0 for i in range(0, 6))
        oyuncu2_kuyulari_bos = all(self.tahta[i] == 0 for i in range(7, 13))

        if oyuncu1_kuyulari_bos or oyuncu2_kuyulari_bos:
            self.oyun_bitti_mi = True
            
            if oyuncu1_kuyulari_bos:
                kalan_taslar = sum(self.tahta[i] for i in range(7, 13))
                self.tahta[13] += kalan_taslar
                for i in range(7, 13): self.tahta[i] = 0
            else: 
                kalan_taslar = sum(self.tahta[i] for i in range(0, 6))
                self.tahta[6] += kalan_taslar
                for i in range(0, 6): self.tahta[i] = 0
            
            skor1 = self.tahta[6]
            skor2 = self.tahta[13]
            
            if skor1 > skor2: self.kazanan = 1
            elif skor2 > skor1: self.kazanan = 2
            else: self.kazanan = "Berabere"
            
            print(self.metin['oyun_bitti_baslik'])
            self.tahtayi_goster()
            print(self.metin['final_skor'].format(skor1, skor2))
            if self.kazanan == "Berabere":
                print(self.metin['berabere_mesaji'])
            else:
                print(self.metin['kazanan_mesaji'].format(self.kazanan))
