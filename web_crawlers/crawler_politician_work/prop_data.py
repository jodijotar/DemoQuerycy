import requests
import time
import pymysql
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class PublicRecord:
    def __init__(self, processo, ano, tipo, assunto, data, situacao, arquivo, autor):
        self.processo = processo
        self.ano = ano
        self.tipo = tipo
        self.assunto = assunto
        self.data = self.parse_date(data)
        self.situacao = situacao
        self.arquivo = arquivo
        self.autor = autor

    @staticmethod
    def parse_date(data):
        return datetime.strptime(data, "%d/%m/%Y %H:%M:%S") if data else None

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='admin',
        password='qwerty',
        database='db',
        port=3306,
        ssl_disabled=True
    )

def save_to_mysql(records):
    if not records:
        return

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            for record in records:
                sql = """
                INSERT INTO public_records (processo, ano, tipo, assunto, data, situacao, arquivo, autor)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    processo = VALUES(processo), ano = VALUES(ano), tipo = VALUES(tipo),
                    assunto = VALUES(assunto), data = VALUES(data), situacao = VALUES(situacao),
                    arquivo = VALUES(arquivo), autor = VALUES(autor);
                """
                cursor.execute(sql, (
                    record.processo, record.ano, record.tipo, record.assunto,
                    record.data, record.situacao, record.arquivo, record.autor
                ))
            connection.commit()
            print(f" --- Successfully saved {len(records)} records to the database. --- ")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        connection.close()

def fetch_and_save_single_target(url, autor_id, ano):
    """Fetches all paginated records for a single author/year and saves them."""
    all_records_for_target = []
    page = 1
    while page is not None:
        endpoint = f"{url}?autorID={autor_id}&ano={ano}&pag={page}"
        try:
            response = requests.get(endpoint, timeout=15) # Add a timeout for safety
            response.raise_for_status()  # This will raise an error for bad responses (4xx or 5xx)

            json_data = response.json()
            data_items = json_data.get('Data', [])

            if not data_items and page == 1:
                print(f"No data found for autor {autor_id} in {ano}. Moving on.")
                return

            for item in data_items:

                if not item:
                    continue

                record = PublicRecord(
                    processo=item.get('processo'), ano=item.get('ano'), tipo=item.get('tipo'),
                    assunto=item.get('assunto'), data=item.get('data'), situacao=item.get('situacao'),
                    arquivo=item.get('arquivo'), autor=item.get('AutorRequerenteDados', {}).get('nomeRazao')
                )
                all_records_for_target.append(record)
            
            print(f"Collected {len(data_items)} items from {endpoint}")

            pagination_info = json_data.get('Paginacao', {})
            next_page = pagination_info.get('proxima')
            page = int(next_page) if next_page else None

        except requests.exceptions.RequestException as e:
            print(f"Error requesting {endpoint}: {e}")
            break # Stop trying this target on a network error
        except ValueError: # Catches errors if the response isn't valid JSON
            print(f"Error parsing JSON from {endpoint}. Content was: {response.text[:100]}")
            break
        
        time.sleep(0.5) # A small polite delay between pages
    
    # Save the collected records immediately after finishing all pages for this target.
    if all_records_for_target:
        save_to_mysql(all_records_for_target)

# The main function now orchestrates the concurrent execution.
def main():
    url = 'https://camarasempapel.camarasjc.sp.gov.br/api/publico/proposicao/'
    autor_ids = [1137, 1140, 1141, 1144, 1145, 1148, 1151, 1152, 1156, 1160, 1274, 3702, 3703, 3704, 3705, 3706, 3707, 3708, 3709, 3710, 4140]
    anos = [2020, 2021, 2022, 2023, 2024]
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [executor.submit(fetch_and_save_single_target, url, autor_id, ano) for autor_id in autor_ids for ano in anos]
        
        for future in as_completed(tasks):
            try:
                future.result()
            except Exception as e:
                print(f"A task generated an unexpected exception: {e}")

    print("\n--- All scraping tasks are complete. ---")

if __name__ == "__main__":
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE public_records MODIFY autor VARCHAR(100);")
        connection.commit()
        print("Database schema verified: `autor` column is VARCHAR(100).")
    except Exception as e:
        print(f"Could not alter table (this might be okay if already altered): {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

    main()