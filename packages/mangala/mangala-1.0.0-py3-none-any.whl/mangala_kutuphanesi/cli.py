import os
from .oyun import MangalaTurkOyunu, metinler

def ekran_temizle():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    dil = 'tr'
    metin = metinler[dil]

    while True:
        ekran_temizle()
        print(metin['menu_baslik'])
        print(metin['menu_oyna'])
        print(metin['menu_kurallar'])
        print(metin['menu_cikis'])
        secim = input(metin['secim_yap'])

        if secim == '1':
            oyun = MangalaTurkOyunu(dil)
            while not oyun.oyun_bitti_mi:
                oyun.tahtayi_goster()
                try:
                    secim_str = input(metin['kuyu_sec_prompt'].format(oyun.mevcut_oyuncu))
                    kuyu = int(secim_str)
                    oyun.oyna(kuyu)
                except ValueError:
                    print(metin['gecersiz_sayi_girisi'])
            
            input(metin['kurallara_don'])
        
        elif secim == '2':
            ekran_temizle()
            print(metin['kurallar_metni'])
            input(metin['kurallara_don'])
        
        elif secim == '3':
            print(metin['cikis_mesaji'])
            break
        
        else:
            print(metin['gecersiz_secim'])
            input()

if __name__ == "__main__":
    main()
