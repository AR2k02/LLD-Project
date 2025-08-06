import os
import json
import pymysql
from dotenv import load_dotenv

load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


connection = pymysql.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

cursor = connection.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS components (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    specs JSON NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS builds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    components_list JSON NOT NULL
)
""")

print("Database and tables initialized.")


components_data = [
    # CPUs - only socket and TDP (for basic info)
    ("Intel Core i5-12400F", "CPU", {"socket": "LGA1700", "tdp": "65W"}),
    ("AMD Ryzen 5 5600X", "CPU", {"socket": "AM4", "tdp": "65W"}),
    ("Intel Core i7-12700K", "CPU", {"socket": "LGA1700", "tdp": "125W"}),
    ("AMD Ryzen 7 5800X", "CPU", {"socket": "AM4", "tdp": "105W"}),
    
    # GPUs - only interface and TDP
    ("NVIDIA RTX 3060", "GPU", {"interface": "PCIe 4.0", "tdp": "170W"}),
    ("AMD RX 6700 XT", "GPU", {"interface": "PCIe 4.0", "tdp": "230W"}),
    ("NVIDIA RTX 4070", "GPU", {"interface": "PCIe 4.0", "tdp": "200W"}),
    ("AMD RX 7600", "GPU", {"interface": "PCIe 4.0", "tdp": "165W"}),
    
    # RAM - only type and speed (what's checked in validation)
    ("Corsair Vengeance 16GB DDR4", "RAM", {"type": "DDR4", "speed": "3200MHz"}),
    ("G.Skill Trident Z 32GB DDR4", "RAM", {"type": "DDR4", "speed": "3600MHz"}),
    ("Corsair Dominator 32GB DDR5", "RAM", {"type": "DDR5", "speed": "5600MHz"}),
    ("Kingston Fury 16GB DDR5", "RAM", {"type": "DDR5", "speed": "4800MHz"}),
    
    # Motherboards - simplified compatibility specs
    ("ASUS B550M-A WiFi", "Motherboard", {
        "socket": "AM4", 
        "ram_support": "DDR4",
        "max_ram_speed": "4400MHz",
        "pcie_support": "Yes",
        "sata_support": "Yes",
        "nvme_support": "Yes"
    }),
    ("MSI Z690-A PRO", "Motherboard", {
        "socket": "LGA1700", 
        "ram_support": "DDR4/DDR5",
        "max_ram_speed": "5333MHz",
        "pcie_support": "Yes",
        "sata_support": "Yes",
        "nvme_support": "Yes"
    }),
    ("ASUS ROG B650E-I", "Motherboard", {
        "socket": "AM5", 
        "ram_support": "DDR5",
        "max_ram_speed": "6000MHz",
        "pcie_support": "Yes",
        "sata_support": "Yes",
        "nvme_support": "Yes"
    }),
    ("MSI X670E-A PRO", "Motherboard", {
        "socket": "AM5", 
        "ram_support": "DDR5",
        "max_ram_speed": "6400MHz",
        "pcie_support": "Yes",
        "sata_support": "Yes",
        "nvme_support": "Yes"
    }),
    
    # Storage - only interface (what's checked in validation)
    ("Samsung 970 EVO Plus 1TB", "Storage", {"interface": "NVMe"}),
    ("Seagate Barracuda 2TB", "Storage", {"interface": "SATA"}),
    ("WD Blue SN570 500GB", "Storage", {"interface": "NVMe"}),
    ("Crucial MX4 1TB", "Storage", {"interface": "SATA"})
]


for name, type_, specs in components_data:
    cursor.execute(
        "INSERT INTO components (name, type, specs) VALUES (%s, %s, %s)",
        (name, type_, json.dumps(specs))
    )

print(f" {len(components_data)} components inserted.")


builds_data = [
    ("Gaming Build Intel", [1, 5, 9, 13, 17]),   # i5-12400F, RTX 3060, DDR4 16GB, B550M-A, NVMe 1TB
    ("Gaming Build AMD", [2, 6, 10, 14, 18]),    # Ryzen 5600X, RX 6700XT, DDR4 32GB, Z690-A, HDD 2TB
    ("High-End Intel", [3, 7, 11, 15, 19]),      # i7-12700K, RTX 4070, DDR5 32GB, ROG B650E-I, NVMe 500GB
    ("High-End AMD", [4, 8, 12, 16, 20]),        # Ryzen 7 5800X, RX 7600, DDR5 16GB, X670E-A, SATA SSD
    ("Budget Build", [1, 8, 9, 13, 18]),         # i5-12400F, RX 7600, DDR4 16GB, B550M-A, HDD 2TB
    ("Compact Build", [2, 5, 12, 15, 17]),       # Ryzen 5600X, RTX 3060, DDR5 16GB, ROG B650E-I, NVMe 1TB
    ("Workstation", [4, 6, 11, 16, 19]),         # Ryzen 7 5800X, RX 6700XT, DDR5 32GB, X670E-A, NVMe 500GB
    ("Entry Level", [1, 8, 9, 14, 20]),          # i5-12400F, RX 7600, DDR4 16GB, Z690-A, SATA SSD
]

for name, comp_ids in builds_data:
    cursor.execute(
        "INSERT INTO builds (name, components_list) VALUES (%s, %s)",
        (name, json.dumps(comp_ids))
    )

print(f" {len(builds_data)} builds inserted.")

connection.commit()
cursor.close()
connection.close()
print(" Data committed and connection closed.")
