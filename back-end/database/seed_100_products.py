"""Afegeix 100 productes d'inventari categoritzats a la base de dades.

Executa des de back-end/database:
  python seed_100_products.py

Categories: 1=Plaques, 2=Sensors, 3=LED, 4=Components, 5=Displays, 6=Mòduls, 7=Motors i Servos, 8=Monitors
"""
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "db.sqlite3"

# (name, price, stock, category_id)
PRODUCTES_100 = [
    # Plaques (1) - 14 productes
    ("Raspberry Pi 4 Model B 2GB", 45.00, 25, 1),
    ("Raspberry Pi 4 Model B 4GB", 55.00, 18, 1),
    ("Raspberry Pi 4 Model B 8GB", 75.00, 12, 1),
    ("Raspberry Pi Zero 2 W", 15.00, 40, 1),
    ("Raspberry Pi Pico", 4.50, 80, 1),
    ("Arduino Uno Rev3", 22.50, 35, 1),
    ("Arduino Nano Every", 18.00, 42, 1),
    ("Arduino Mega 2560", 42.00, 15, 1),
    ("ESP32 Development Board", 12.99, 50, 1),
    ("ESP32-CAM", 9.99, 30, 1),
    ("ESP8266 NodeMCU", 7.50, 60, 1),
    ("STM32 Blue Pill", 4.20, 45, 1),
    ("BeagleBone Black", 65.00, 8, 1),
    # Sensors (2) - 14 productes
    ("Sensor DHT22 Temperatura i Humitat", 8.90, 55, 2),
    ("Sensor DHT11", 4.50, 70, 2),
    ("Sensor Ultrasonic HC-SR04", 3.50, 80, 2),
    ("Sensor PIR HC-SR501", 2.99, 65, 2),
    ("Sensor de Llum LDR", 1.20, 100, 2),
    ("Sensor de Gas MQ-2", 5.99, 40, 2),
    ("Sensor de So LM393", 3.20, 50, 2),
    ("Sensor Hall A3144", 0.89, 90, 2),
    ("Sensor de Flux d'Aigua", 4.99, 35, 2),
    ("Sensor de Distància VL53L0X", 12.00, 25, 2),
    ("Sensor BMP280 Pressió", 6.50, 45, 2),
    ("Sensor de Moviment MPU6050", 8.99, 38, 2),
    ("Sensor de Proximitat IR", 2.50, 60, 2),
    ("Sensor de pH", 18.00, 15, 2),
    # LED (3) - 12 productes
    ("LED RGB 5mm", 0.50, 200, 3),
    ("LED Blanc 5mm 1W", 0.35, 250, 3),
    ("Tira LED RGB 1m 30 LEDs", 12.99, 30, 3),
    ("Tira LED RGB 5m WS2812B", 22.00, 20, 3),
    ("LED Panel 12V 10W", 8.50, 45, 3),
    ("Bombeta LED E27 10W", 5.99, 80, 3),
    ("LED COB 50W", 6.50, 35, 3),
    ("LED Neopixel Ring 12 LEDs", 9.99, 25, 3),
    ("LED Infraroig 5mm", 0.25, 150, 3),
    ("LED UV 3W", 3.99, 40, 3),
    ("Driver LED 12V 3A", 4.50, 55, 3),
    ("Kit LED Assortit 500 unitats", 18.00, 15, 3),
    # Components (4) - 18 productes
    ("Resistència Pack 220Ω x 100", 2.99, 90, 4),
    ("Resistència Pack Assortit 1/4W", 4.50, 60, 4),
    ("Condensador Electrolític 100µF", 0.15, 200, 4),
    ("Condensador Ceràmic 100nF Pack", 1.99, 120, 4),
    ("Breadboard 830 punts", 5.99, 50, 4),
    ("Breadboard 400 punts", 3.50, 70, 4),
    ("Cable jumper pack M-M 40u", 4.50, 65, 4),
    ("Cable jumper M-F 40u", 4.99, 55, 4),
    ("Protoboard PCB Universal", 2.50, 80, 4),
    ("Interruptor Tactil 6x6mm", 0.20, 300, 4),
    ("Potenciòmetre 10kΩ", 1.50, 100, 4),
    ("Díode 1N4007 Pack 100", 2.00, 85, 4),
    ("Transistor NPN 2N2222 Pack", 3.00, 75, 4),
    ("Regulador LM7805 5V", 0.89, 95, 4),
    ("Relé 5V 1 canal", 2.99, 60, 4),
    ("Connector Barrel 5.5x2.1mm", 0.50, 150, 4),
    ("Font Alimentació 5V 2A", 6.99, 40, 4),
    # Displays (5) - 12 productes
    ("Display LCD 16x2 I2C", 8.50, 45, 5),
    ("Display LCD 20x4", 15.00, 25, 5),
    ("Display OLED 0.96\" I2C", 7.99, 50, 5),
    ("Display OLED 1.3\" SH1106", 12.00, 30, 5),
    ("Display TFT 1.8\" SPI", 9.50, 35, 5),
    ("Display 7 segments 4 dígits", 4.99, 55, 5),
    ("Display LED Matriu 8x8", 6.50, 40, 5),
    ("Pantalla Tàctil 2.4\"", 18.00, 20, 5),
    ("Display e-Paper 2.13\"", 25.00, 12, 5),
    ("Display Nextion 2.4\"", 35.00, 10, 5),
    ("Display TM1637 4 dígits", 3.99, 60, 5),
    ("Display Nokia 5110", 5.50, 45, 5),
    # Mòduls (6) - 14 productes
    ("Mòdul Bluetooth HC-05", 9.99, 35, 6),
    ("Mòdul Bluetooth HC-06", 7.50, 40, 6),
    ("Mòdul WiFi ESP-01S", 4.99, 55, 6),
    ("Mòdul RFID RC522", 6.99, 45, 6),
    ("Mòdul GPS NEO-6M", 14.00, 25, 6),
    ("Mòdul Lector SD", 5.50, 38, 6),
    ("Mòdul RTC DS3231", 4.50, 50, 6),
    ("Mòdul Rele 4 canals 5V", 8.99, 30, 6),
    ("Mòdul Step-Down LM2596", 2.99, 65, 6),
    ("Mòdul Step-Up MT3608", 2.50, 60, 6),
    ("Mòdul LoRa SX1278", 18.00, 15, 6),
    ("Mòdul Zigbee CC2530", 12.00, 22, 6),
    ("Mòdul IR Receptor VS1838B", 1.50, 80, 6),
    ("Mòdul Zumbador Actiu", 0.99, 100, 6),
    # Motors i Servos (7) - 10 productes
    ("Motor Servo SG90", 6.99, 45, 7),
    ("Motor Servo MG995", 12.00, 25, 7),
    ("Motor DC 3-6V amb rodes", 4.50, 55, 7),
    ("Driver L298N Dual H-Bridge", 5.99, 40, 7),
    ("Driver TB6612", 6.50, 35, 7),
    ("Motor Pas a Pas 28BYJ-48", 4.99, 50, 7),
    ("Driver ULN2003 Stepper", 2.99, 60, 7),
    ("Motor Vibratori 3V", 1.50, 90, 7),
    ("Reductor Motor DC 1:90", 8.00, 30, 7),
    ("Kit 4 motors + 4 rodes", 18.00, 20, 7),
    # Monitors (8) - 8 productes
    ("Monitor 24\" Full HD IPS", 149.00, 12, 8),
    ("Monitor 27\" QHD", 249.00, 8, 8),
    ("Monitor 32\" 4K UHD", 329.00, 6, 8),
    ("Monitor Portàtil 15.6\" USB-C", 159.00, 10, 8),
    ("Monitor Gaming 24\" 144Hz", 199.00, 9, 8),
    ("Monitor Curvat 27\"", 279.00, 5, 8),
    ("Monitor Professional 4K 32\"", 449.00, 4, 8),
    ("Monitor Compact 18.5\"", 89.00, 15, 8),
]


def main():
    if not DB_PATH.exists():
        print("No s'ha trobat db.sqlite3. Executa abans: python init_db.py")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Comprovar si existeix taula Category
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Category'")
    if not cur.fetchone():
        print("Executa abans la migració: python migrate_add_categories.py")
        conn.close()
        return
    assert len(PRODUCTES_100) == 100, f"La llista ha de tenir 100 productes, té {len(PRODUCTES_100)}"
    products_100 = PRODUCTES_100
    cur.executemany(
        "INSERT INTO Product(name, price, stock, category_id) VALUES(?,?,?,?)",
        products_100,
    )
    conn.commit()
    print(f"Inserits {len(products_100)} productes d'inventari categoritzats.")
    conn.close()


if __name__ == "__main__":
    main()
