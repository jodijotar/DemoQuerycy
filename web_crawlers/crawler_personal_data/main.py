import sys
import json
import re
import info_camara
import info_tse

print('''

 
 
▓█████▄▓█████ ███▄ ▄███▓▒█████   █████  █    ██▓█████ ██▀███▓██   ██▓▄████▓██   ██▓
▒██▀ ██▓█   ▀▓██▒▀█▀ ██▒██▒  ██▒██▓  ██▒██  ▓██▓█   ▀▓██ ▒ ██▒██  ██▒██▀ ▀█▒██  ██▒
░██   █▒███  ▓██    ▓██▒██░  ██▒██▒  ██▓██  ▒██▒███  ▓██ ░▄█ ▒▒██ ██▒▓█    ▄▒██ ██░             
░▓█▄   ▒▓█  ▄▒██    ▒██▒██   ██░██  █▀ ▓▓█  ░██▒▓█  ▄▒██▀▀█▄  ░ ▐██▓▒▓▓▄ ▄██░ ▐██▓░     
░▒████▓░▒████▒██▒   ░██░ ████▓▒░▒███▒█▄▒▒█████▓░▒████░██▓ ▒██▒░ ██▒▓▒ ▓███▀ ░ ██▒▓░
 ▒▒▓  ▒░░ ▒░ ░ ▒░   ░  ░ ▒░▒░▒░░░ ▒▒░ ▒░▒▓▒ ▒ ▒░░ ▒░ ░ ▒▓ ░▒▓░ ██▒▒▒░ ░▒ ▒  ░██▒▒▒ 
 ░ ▒  ▒ ░ ░  ░  ░      ░ ░ ▒ ▒░ ░ ▒░  ░░░▒░ ░ ░ ░ ░  ░ ░▒ ░ ▒▓██ ░▒░  ░  ▒ ▓██ ░▒░ 
 ░ ░  ░   ░  ░      ░  ░ ░ ░ ▒    ░   ░ ░░░ ░ ░   ░    ░░   ░▒ ▒ ░░ ░      ▒ ▒ ░░  
   ░      ░  ░      ░      ░ ░     ░      ░       ░  ░  ░    ░ ░    ░ ░    ░ ░     
 ░                                                           ░ ░    ░      ░ ░     


                            your digital democracy is running by
                                     --Agile Krakens                                         
''')

def scrap(url, url2):
    dados_string = info_camara.personal_data(url)
    dados_presenca = info_camara.presence_stats(url)
    comissoes = info_camara.comissoes(url)
    
    dados = {
        'nome': re.search(r'civil:(.*)', dados_string).group(1).strip(),
        'nome_social': info_tse.nome_social(url2),
        'data_nasc': info_tse.data_nasc(url2),
        'ocupação': info_tse.ocupacao(url2),
        'partido': info_camara.partido(url),
        'telefone': re.findall(r'\(\d{2}\)\s\d{4}-\d{4}', dados_string),
        'email': re.search(r'E-mail:(.*)', dados_string).group(1).strip() if re.search(r'E-mail:(.*)', dados_string) else '',
        'comissoes': re.findall(r'Cargo: (.*?) \((.*?)\)\nComissão: (.*?)-', comissoes),
        'presencas': [x for x in dados_presenca[:dados_presenca.index('Falta')] if x.isdigit()],
        'ausencias': [x for x in dados_presenca[dados_presenca.index('Falta'):] if x.isdigit()],
        'mandatos': info_tse.hist_mandatos(url2)
    }

    file = f"{dados['nome'].replace(' ', '_').lower()}.json"
    
    with open(f"C:/Users/guilh/Desktop/Faculdade/demoquerycy/src/data/json_files{file}", 'w', encoding='utf-8') as json_file:
        json.dump(dados, json_file, ensure_ascii=False, indent=4)
        
    print(f"\n{dados['nome_social']} data collected!")
    print(f"{dados['nome']}\n{dados['ocupação']}\n{dados['partido']}\n{dados['telefone']}\n{dados['email']}\n{dados['mandatos']}")

def read_urls(urls_file, urls2_file):
    with open(urls_file, 'r') as f1, open(urls2_file, 'r') as f2:
        urls = f1.read().splitlines()
        urls2 = f2.read().splitlines()

    for url, url2 in zip(urls, urls2):
        try:
            scrap(url, url2)
        except Exception as e:
            print(f"fail to process: {e}")

read_urls('camara_endpoints.txt', 'tse_endpoints.txt')

