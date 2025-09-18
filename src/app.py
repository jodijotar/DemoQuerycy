from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
from itertools import cycle
from db import get_db_connection
import graphics
import math

app = Flask(__name__)

JSON_DIR = 'data/json_files'

def carregar_politicos():
    """Loads and sorts politician data from JSON files."""
    dados = []
    for filename in sorted(os.listdir(JSON_DIR)):
        if filename.endswith('.json'):
            file_path = os.path.join(JSON_DIR, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    dados.append(json.load(f))
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading or parsing {filename}: {e}. Skipping file.")
            
    return sorted(dados, key=lambda x: x['nome'][5:])


@app.route('/')
def index():
    """Renders the home page with a carousel of politicians."""
    politicos = carregar_politicos()
    num_cards_per_slide = 4
    slides = [politicos[i:i + num_cards_per_slide] for i in range(0, len(politicos), num_cards_per_slide)]
    return render_template('home.html', slides=slides)

@app.route('/pagina-politicos')
def pagina_politicos():
    """Renders the page that lists all politicians."""
    politicos = carregar_politicos()
    return render_template('politicos.html', politicos=sorted(politicos, key=lambda p: p['nome']))

@app.route('/perfil/<nome>')
def perfil(nome):
    """Renders the initial profile page, fetching only initial data."""
    json_path = os.path.join(JSON_DIR, f"{nome}.json")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            
            total_presenca = sum(int(dados['presencas'][i]) for i in range(1, len(dados['presencas']), 2))
            total_ausencia = sum(int(dados['ausencias'][i]) for i in range(1, len(dados['ausencias']), 2))
            
            total_sessoes = total_presenca + total_ausencia
            if total_sessoes > 0:
                porcentagem_presenca = round(total_presenca * 100 / total_sessoes, 2)
                porcentagem_ausencia = round(total_ausencia * 100 / total_sessoes, 2)
            else:
                porcentagem_presenca = 0
                porcentagem_ausencia = 0

            grafico = graphics.gerar_grafico(nome_autor=dados['nome'])

            # This route now ONLY fetches the filter types. The table data is loaded via API.
            connection = get_db_connection()
            cursor = connection.cursor()
            query_tipos = "SELECT DISTINCT tipo FROM public_records WHERE autor = %s AND ano >= 2020"
            cursor.execute(query_tipos, (dados['nome'],))
            tipos_proposicao = [row[0] for row in cursor.fetchall()]

    except FileNotFoundError:
        return "Perfil não encontrado", 404
    except Exception as e:
        return f"Ocorreu um erro: {str(e)}", 500
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'connection' in locals() and connection is not None:
            connection.close()
        
    return render_template(
        'perfil.html',
        perfil=dados,
        porcentagem_presenca=porcentagem_presenca,
        porcentagem_ausencia=porcentagem_ausencia,
        grafico=grafico,
        tipos_proposicao=sorted(tipos_proposicao)
    )

@app.route('/api/proposicoes/<autor_nome>')
def api_proposicoes(autor_nome):
    """API endpoint to get paginated and filtered propositions."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    filter_type = request.args.get('tipo', 'todos')
    offset = (page - 1) * per_page
    
    connection = get_db_connection()
    cursor = connection.cursor()

    base_query = "FROM public_records WHERE autor = %s AND ano >= 2020"
    params = [autor_nome]
    if filter_type != 'todos':
        base_query += " AND tipo = %s"
        params.append(filter_type)

    count_query = f"SELECT COUNT(*) {base_query}"
    cursor.execute(count_query, tuple(params))
    total_items = cursor.fetchone()[0]
    total_pages = math.ceil(total_items / per_page)

    data_query = f"SELECT processo, ano, tipo, data, situacao, arquivo, assunto {base_query} ORDER BY data DESC LIMIT %s OFFSET %s"
    cursor.execute(data_query, tuple(params + [per_page, offset]))
    proposicoes = cursor.fetchall()
    
    cursor.close()
    connection.close()

    proposicoes_list = [{"processo": p[0], "ano": p[1], "tipo": p[2], "data": format_date(p[3]), "situacao": p[4], "arquivo": p[5], "assunto": p[6]} for p in proposicoes]
    
    return jsonify({'proposicoes': proposicoes_list, 'total_pages': total_pages, 'current_page': page})

@app.route('/api/leis/<autor_nome>')
def api_leis(autor_nome):
    """API endpoint to get paginated law projects."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    connection = get_db_connection()
    cursor = connection.cursor()

    count_query = "SELECT COUNT(*) FROM law_records WHERE autor = %s AND ano >= 2020"
    cursor.execute(count_query, (autor_nome,))
    total_items = cursor.fetchone()[0]
    total_pages = math.ceil(total_items / per_page)

    data_query = "SELECT numero, ano, tema, resumo, data, situacao FROM law_records WHERE autor = %s AND ano >= 2020 ORDER BY data DESC LIMIT %s OFFSET %s"
    cursor.execute(data_query, (autor_nome, per_page, offset))
    leis = cursor.fetchall()
    
    cursor.close()
    connection.close()

    leis_list = [{"numero": l[0], "ano": l[1], "tema": l[2], "resumo": l[3], "data": format_date(l[4]), "situacao": l[5]} for l in leis]
    
    return jsonify({'leis': leis_list, 'total_pages': total_pages, 'current_page': page})
    
@app.template_filter('format_date')
def format_date(value):
    """Jinja2 filter to format date strings for display."""
    if isinstance(value, str):
        try:
            dt_object = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return dt_object.strftime('%d/%m/%Y')
        except ValueError:
            try:
                dt_object = datetime.strptime(value, '%Y-%m-%d')
                return dt_object.strftime('%d/%m/%Y')
            except ValueError:
                return value
    elif isinstance(value, datetime):
        return value.strftime('%d/%m/%Y')
    return value

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)