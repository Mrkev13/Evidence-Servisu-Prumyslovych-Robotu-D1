import pyodbc

class RobotRepository:
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def _get_connection(self):
        """Pomocná metoda pro otevření brány do DB"""
        return pyodbc.connect(self.connection_string)

    # --- ZÁKLADNÍ SQL DOTAZY (SELECT) ---
    
    def get_vsechny_roboty(self):
        """Vrátí seznam všech robotů (používá VIEW z SQL)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        # Tady využíváme tvoje SQL View
        cursor.execute("SELECT * FROM View_RobotOverview")
        data = cursor.fetchall()
        conn.close()
        return data

    def get_sklad_dilu(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT PartID, PartName, StockQuantity, Price FROM Parts")
        data = cursor.fetchall()
        conn.close()
        return data

    # --- TRANSAKCE (Povinný bod zadání) ---
    
    def pridat_servis_s_dilem(self, robot_id, part_id, quantity, popis):
        """
        Transakce: 
        1. Vytvoří záznam o servisu.
        2. Odečte použitý díl ze skladu.
        3. Přidá vazbu do M:N tabulky.
        Pokud něco selže, vrátí vše zpět (ROLLBACK).
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Začínáme transakci (děje se automaticky v pyodbc, dokud nedáme commit)
            
            # Krok A: Vložení hlavičky servisu
            cursor.execute("INSERT INTO ServiceLogs (RobotID, Description) OUTPUT INSERTED.LogID VALUES (?, ?)", (robot_id, popis))
            log_id = cursor.fetchone()[0] # Získáme ID nového servisu
            
            # Krok B: Odečtení ze skladu (kontrola jestli nejdem do minusu by mela byt v SQL Checku, ale tady to stačí)
            cursor.execute("UPDATE Parts SET StockQuantity = StockQuantity - ? WHERE PartID = ?", (quantity, part_id))
            
            # Krok C: Zápis do vazební tabulky
            cursor.execute("INSERT INTO ServiceLog_Parts (LogID, PartID, QuantityUsed) VALUES (?, ?, ?)", (log_id, part_id, quantity))
            
            # Pokud jsme došli sem, vše je OK. Potvrdíme.
            conn.commit()
            print("Transakce úspěšná: Servis zapsán, sklad aktualizován.")
            return True
            
        except Exception as e:
            # Něco se pokazilo (např. neexistující ID), vracíme změny zpět!
            conn.rollback()
            print(f"Chyba transakce: {e}")
            return False
        finally:
            conn.close()
    
    # ... (Tady končí tvoje metoda pridat_servis_s_dilem) ...

    # --- REPORT (Povinný bod: Agregovaná data) ---
    def get_report_cen(self):
        """Vrátí data z VIEW_ServiceCosts (součty cen servisů)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        # Předpokládá, že jsi vytvořil ten VIEW z mého SQL skriptu
        # Pokud ne, uděláme jednoduchý součet v SQL
        try:
            cursor.execute("""
                SELECT r.ModelName, COUNT(s.LogID) as PocetServisu, SUM(p.Price * slp.QuantityUsed) as CelkovaCena
                FROM ServiceLogs s
                JOIN Robots r ON s.RobotID = r.RobotID
                JOIN ServiceLog_Parts slp ON s.LogID = slp.LogID
                JOIN Parts p ON slp.PartID = p.PartID
                GROUP BY r.ModelName
            """)
            return cursor.fetchall()
        except:
            return []
        finally:
            conn.close()

    # --- IMPORT (Povinný bod: Import z CSV) ---
    def import_dilu_z_csv(self, cesta_k_souboru):
        import csv
        conn = self._get_connection()
        cursor = conn.cursor()
        counter = 0
        try:
            with open(cesta_k_souboru, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader) # Přeskočit hlavičku
                for row in reader:
                    # Očekáváme CSV: Nazev, Cena, Pocet
                    # row[0] = Nazev, row[1] = Cena, row[2] = Pocet
                    cursor.execute(
                        "INSERT INTO Parts (PartName, Price, StockQuantity) VALUES (?, ?, ?)", 
                        (row[0], float(row[1]), int(row[2]))
                    )
                    counter += 1
            conn.commit()
            return f"Úspěšně importováno {counter} položek."
        except Exception as e:
            conn.rollback()
            return f"Chyba importu: {e}"
        finally:
            conn.close()