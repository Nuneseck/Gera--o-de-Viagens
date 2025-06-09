from flask import Flask, render_template, request, jsonify, send_from_directory, session
import json
import random
import os
import datetime
from functools import lru_cache
from pathlib import Path
import sys
from io import StringIO

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_123'

# ========== CONFIGURAÇÃO INICIAL ==========
def create_folder_structure():
    """Cria a estrutura de pastas necessária"""
    base_terrains = ['floresta', 'deserto', 'cidade', 'planicie', 'costa']
    default_categories = {
        "Humanoide|humanoide/tipos.json": 12,
        "Animal|animal/tipos.json": 8,
        "Monstro|monstro/tipos.json": 6,
        "Construto|construto/tipos.json": 4,
        "Morto-vivo|morto-vivo/tipos.json": 3,
        "Espirito|espirito/tipos.json": 2,
        "Lefeu|lefeu/tipos.json": 1
    }

    for terrain in base_terrains:
        Path(f'encounters/{terrain}/creatures').mkdir(parents=True, exist_ok=True)
        Path('encounters/caracteristicas').mkdir(parents=True, exist_ok=True)
        
        # Cria categories.json se não existir
        categories_file = f'encounters/{terrain}/creatures/categories.json'
        if not os.path.exists(categories_file):
            with open(categories_file, 'w', encoding='utf-8') as f:
                json.dump(default_categories, f, indent=2)
        
        # Cria arquivos básicos de criaturas
        creature_types = {
            'humanoide': ['tipos.json', 'condicoes.json', 'racas.json'],
            'animal': ['tipos.json', 'condicoes.json'],
            'monstro': ['tipos.json', 'condicoes.json'],
            'morto-vivo': ['tipos.json', 'condicoes.json'],
            'espirito': ['tipos.json', 'condicoes.json'],
            'construto': ['tipos.json', 'condicoes.json'],
            'lefeu': ['tipos.json', 'condicoes.json']
        }
        
        for folder, files in creature_types.items():
            Path(f'encounters/{terrain}/creatures/{folder}').mkdir(parents=True, exist_ok=True)
            for file in files:
                if not os.path.exists(f'encounters/{terrain}/creatures/{folder}/{file}'):
                    with open(f'encounters/{terrain}/creatures/{folder}/{file}', 'w', encoding='utf-8') as f:
                        if 'tipos' in file:
                            json.dump({
                                f"Exemplo de tipo de {folder} 1": 3,
                                f"Exemplo de tipo de {folder} 2": 2,
                                f"Exemplo de tipo de {folder} 3": 1
                            }, f, indent=2)
                        elif 'condicoes' in file:
                            json.dump({
                                f"Exemplo de condição de {folder} 1": 3,
                                f"Exemplo de condição de {folder} 2": 2,
                                f"Exemplo de condição de {folder} 3": 1
                            }, f, indent=2)
                        elif 'racas' in file and folder == 'humanoide':
                            json.dump({
                                "Humano": 5,
                                "Elfo": 3,
                                "Anão": 2,
                                "Outra raça": 1
                            }, f, indent=2)

        # Cria outros arquivos de encontro
        for file in ['false_alarms.json', 'anomalies.json', 'temporary_obstacles.json', 'events.json']:
            if not os.path.exists(f'encounters/{terrain}/{file}'):
                with open(f'encounters/{terrain}/{file}', 'w', encoding='utf-8') as f:
                    json.dump({"Exemplo": "Descrição do evento"}, f)

create_folder_structure()

# ========== FUNÇÕES DE DEBUG ==========
def debug_category_probabilities(terrain='floresta', samples=100000):
    """Analisa as probabilidades reais de encontro por categoria"""
    try:
        with open(f'encounters/{terrain}/creatures/categories.json', 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
        
        # Novo formato simplificado
        if isinstance(categories_data, dict) and all('|' in key for key in categories_data.keys()):
            categories = list(categories_data.keys())
            weights = list(categories_data.values())
            
            results = {cat.split('|')[0]: 0 for cat in categories}
            
            for _ in range(samples):
                selected = select_by_weight(categories_data)
                category = selected.split('|')[0]
                results[category] += 1
            
            print(f"<br>=== DEBUG DE PROBABILIDADES ({terrain.upper()}) ===")
            print(f"Baseado em {samples} simulações:")
            total_weight = sum(weights)
            
            for category, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
                cat_weight = next(v for k, v in categories_data.items() if k.startswith(category))
                theoretical = cat_weight / total_weight
                actual = count / samples
                print(f"{category}: {actual:.2%} (Teórico: {theoretical:.2%} | Diferença: {(actual-theoretical):+.2f}%)")
            
            return results
        
        # Formato antigo com intervalos
        elif isinstance(categories_data, dict):
            results = {data['category']: 0 for data in categories_data.values()}
            
            for _ in range(samples):
                roll = random.randint(1, 20)
                for range_str, data in categories_data.items():
                    if '-' in range_str:
                        min_val, max_val = map(int, range_str.split('-'))
                        if min_val <= roll <= max_val:
                            results[data['category']] += 1
                            break
                    elif int(range_str) == roll:
                        results[data['category']] += 1
                        break
            
            print(f"<br>=== DEBUG DE PROBABILIDADES ({terrain.upper()}) ===")
            print(f"Baseado em {samples} simulações:")
            for category, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
                theoretical = calculate_theoretical_chance(categories_data, category)
                diff = (count/samples*100) - (theoretical*100)
                print(f"{category}: {count/samples:.2%} (Teórico: {theoretical:.2%} | Diferença: {diff:+.2f}%)")
            
            return results
        
        else:
            print("Formato de categories.json não reconhecido")
            return {}

    except Exception as e:
        print(f"Erro no debug: {str(e)}")
        return {}

def calculate_theoretical_chance(categories, target_category):
    """Calcula a probabilidade teórica de uma categoria"""
    total = 0
    for range_str, data in categories.items():
        if data['category'] == target_category:
            if '-' in range_str:
                min_val, max_val = map(int, range_str.split('-'))
                total += (max_val - min_val + 1)
            else:
                total += 1
    return total / 20

def debug_encounter_types(terrain='floresta', samples=10000):
    """Analisa a distribuição dos tipos de encontro"""
    try:
        config = json.load(open('tipos_encontro.json', encoding='utf-8'))
        terrain_config = config.get(terrain, {})
        
        # Se for o novo formato com pesos
        if isinstance(terrain_config, dict) and all(isinstance(v, int) for v in terrain_config.values()):
            results = {t: 0 for t in terrain_config.keys()}
            total = sum(terrain_config.values())
            
            for _ in range(samples):
                selected = select_by_weight(terrain_config)
                results[selected] += 1
            
            print(f"<br>=== DEBUG DE TIPOS DE ENCONTRO ({terrain.upper()}) ===")
            for encounter, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
                theoretical = terrain_config[encounter] / total
                print(f"{encounter}: {count/samples:.2%} (Teórico: {theoretical:.2%})")
        
        # Se for o formato antigo com intervalos
        else:
            results = {t: 0 for t in terrain_config.keys()}
            
            for _ in range(samples):
                roll = random.randint(1, 20)
                for encounter, range_values in terrain_config.items():
                    if isinstance(range_values, list) and len(range_values) == 2:
                        if range_values[0] <= roll <= range_values[1]:
                            results[encounter] += 1
                            break
                    elif isinstance(range_values, int) and roll == range_values:
                        results[encounter] += 1
                        break
            
            print(f"<br>=== DEBUG DE TIPOS DE ENCONTRO ({terrain.upper()}) ===")
            for encounter, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
                print(f"{encounter}: {count/samples:.2%}")
        
        return results
    except Exception as e:
        print(f"Erro no debug: {str(e)}")
        return {}

# ========== FUNÇÕES PRINCIPAIS ==========
def load_terrain_encounters(terrain):
    """Carrega encontros específicos do terreno"""
    return {
        'false_alarms': json.load(open(f'encounters/{terrain}/false_alarms.json', encoding='utf-8')),
        'anomalies': json.load(open(f'encounters/{terrain}/anomalies.json', encoding='utf-8')),
        'temporary_obstacles': json.load(open(f'encounters/{terrain}/temporary_obstacles.json', encoding='utf-8')),
        'events': json.load(open(f'encounters/{terrain}/events.json', encoding='utf-8'))
    }

def select_by_weight(options):
    """Seleciona uma opção baseada em pesos, aceitando tanto o formato novo quanto o antigo"""
    # Se for no formato {"descrição": peso, ...}
    if isinstance(options, dict):
        items = list(options.items())
        descriptions = [item[0] for item in items]
        weights = [item[1] for item in items]
    # Se for no formato antigo {"options": [{"description":..., "weight":...}, ...]}
    elif isinstance(options, dict) and 'options' in options:
        descriptions = [opt['description'] for opt in options['options']]
        weights = [opt['weight'] for opt in options['options']]
    # Se for no formato muito antigo {"1-3": "descrição", ...}
    elif isinstance(options, dict) and any('-' in k for k in options.keys()):
        # Converte para o formato de pesos iguais
        descriptions = list(options.values())
        weights = [1] * len(descriptions)
    else:
        return "Indefinido"
    
    total = sum(weights)
    r = random.uniform(0, total)
    upto = 0
    for i, weight in enumerate(weights):
        if upto + weight >= r:
            return descriptions[i]
        upto += weight
    return descriptions[-1]  # fallback

def roll_for_detail(file_path):
    """Rola detalhes específicos, compatível com vários formatos"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            details = json.load(f)
        
        return select_by_weight(details)
    except Exception as e:
        print(f"Erro ao rolar detalhe: {str(e)}")
        return "Indefinido"

def generate_creature(terrain):
    """Gera uma criatura com tipo e características"""
    try:
        with open(f'encounters/{terrain}/creatures/categories.json', 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
        
        # Se for o novo formato simplificado (com |)
        if isinstance(categories_data, dict) and all('|' in key for key in categories_data.keys()):
            selected = select_by_weight(categories_data)
            category, file_path = selected.split('|')
            category_data = {'category': category.strip(), 'file': file_path.strip()}
        # Se for o formato antigo com intervalos numéricos
        elif isinstance(categories_data, dict):
            roll = random.randint(1, 20)
            category_data = None
            for range_str, data in categories_data.items():
                if '-' in range_str:
                    min_val, max_val = map(int, range_str.split('-'))
                    if min_val <= roll <= max_val:
                        category_data = data
                        break
                elif int(range_str) == roll:
                    category_data = data
                    break
        else:
            return {'descricao': "Criatura desconhecida", 'tipo': None}

        if not category_data:
            return {'descricao': "Criatura desconhecida", 'tipo': None}

        folder_name = category_data['category'].lower().replace('í', 'i').replace(' ', '-')
        base_path = f'encounters/{terrain}/creatures/{folder_name}/'
        
        tipo = roll_for_detail(base_path + 'tipos.json')
        condicao = roll_for_detail(base_path + 'condicoes.json')
        
        if category_data['category'].lower() == 'humanoide':
            raca = roll_for_detail(base_path + 'racas.json')
            return {
                'descricao': f"Humanoide - {tipo} ({condicao}, {raca})",
                'tipo': 'humanoide'
            }
        
        return {
            'descricao': f"{category_data['category']} - {tipo} ({condicao})",
            'tipo': folder_name
        }

    except Exception as e:
        print(f"Erro ao gerar criatura: {str(e)}")
        return {'descricao': "Criatura indefinida", 'tipo': None}

def map_category_to_type(category):
    """Mapeia categorias para tipos de características"""
    mapeamento = {
        'Humanoide': 'humanoide',
        'Animal': 'animal',
        'Monstro': 'monstro',
        'Morto-vivo': 'morto-vivo',
        'Espirito': 'espirito',
        'Construto': 'construto',
        'Lefeu': 'lefeu'
    }
    return mapeamento.get(category, 'monstro')

def generate_single_encounter(is_night, terrain, encounter_type=None):
    """Gera um encontro completo com probabilidades por terreno"""
    try:
        encounters = load_terrain_encounters(terrain)
        type_names = {
            'false_alarm': 'Alarme falso',
            'creatures': 'Criaturas',
            'anomaly': 'Anomalia',
            'creatures_anomaly': 'Criaturas + Anomalia',
            'temporary_obstacle': 'Obstáculo temporário',
            'obstacle_creatures': 'Obstáculo + Criaturas',
            'event': 'Evento especial',
            'double_roll': 'Evento duplo'
        }

        if not encounter_type:
            config = json.load(open('tipos_encontro.json', encoding='utf-8'))
            terrain_config = config.get(terrain, {})
            
            # Novo formato com pesos
            if isinstance(terrain_config, dict) and all(isinstance(v, int) for v in terrain_config.values()):
                encounter_type = select_by_weight(terrain_config)
            # Formato antigo com intervalos
            else:
                roll = random.randint(1, 20)
                for encounter, range_values in terrain_config.items():
                    if isinstance(range_values, list) and len(range_values) == 2:
                        if range_values[0] <= roll <= range_values[1]:
                            encounter_type = encounter
                            break
                    elif isinstance(range_values, int) and roll == range_values:
                        encounter_type = encounter
                        break

        if not encounter_type:
            return {
                'description': "Encontro indefinido",
                'time_roll': random.randint(1, 20),
                'encounter_data': None
            }

        if encounter_type == 'false_alarm':
            options = encounters['false_alarms']
            chosen = random.choice(list(options.items()))
            return {
                'description': f"{type_names['false_alarm']}: {chosen[0]}",
                'time_roll': random.randint(1, 20),
                'encounter_data': None
            }
        
        elif encounter_type == 'creatures':
            creature_data = generate_creature(terrain)
            return {
                'description': f"{type_names['creatures']}: {creature_data['descricao']}",
                'time_roll': random.randint(1, 20),
                'encounter_data': {
                    'tipo': creature_data['tipo']
                }
            }
        
        elif encounter_type == 'anomaly':
            options = encounters['anomalies']
            chosen = random.choice(list(options.items()))
            return {
                'description': f"{type_names['anomaly']}: {chosen[0]}",
                'time_roll': random.randint(1, 20),
                'encounter_data': None
            }
        
        elif encounter_type == 'creatures_anomaly':
            creature_data = generate_creature(terrain)
            anomaly = random.choice(list(encounters['anomalies'].items()))
            return {
                'description': f"{type_names['creatures_anomaly']}: {creature_data['descricao']} e {anomaly[0]}",
                'time_roll': random.randint(1, 20),
                'encounter_data': {
                    'tipo': creature_data['tipo']
                }
            }
        
        elif encounter_type == 'temporary_obstacle':
            options = encounters['temporary_obstacles']
            chosen = random.choice(list(options.items()))
            return {
                'description': f"{type_names['temporary_obstacle']}: {chosen[0]}",
                'time_roll': random.randint(1, 20),
                'encounter_data': None
            }
        
        elif encounter_type == 'obstacle_creatures':
            obstacle = random.choice(list(encounters['temporary_obstacles'].items()))
            creature_data = generate_creature(terrain)
            return {
                'description': f"{type_names['obstacle_creatures']}: {obstacle[0]} e {creature_data['descricao']}",
                'time_roll': random.randint(1, 20),
                'encounter_data': {
                    'tipo': creature_data['tipo']
                }
            }
        
        elif encounter_type == 'event':
            options = encounters['events']
            chosen = random.choice(list(options.items()))
            return {
                'description': f"{type_names['event']}: {chosen[0]}",
                'time_roll': random.randint(1, 20),
                'encounter_data': None
            }
        
        elif encounter_type == 'double_roll':
            first = generate_single_encounter(is_night, terrain)
            second = generate_single_encounter(is_night, terrain)
            
            if not first or not second:
                return {
                    'description': "Evento duplo falhou",
                    'time_roll': random.randint(1, 20),
                    'encounter_data': None
                }
            
            first_desc = first['description'].split(": ", 1)[-1]
            second_desc = second['description'].split(": ", 1)[-1]
            return {
                'description': f"Evento duplo: {first_desc} e também {second_desc}",
                'time_roll': random.randint(1, 20),
                'encounter_data': None
            }
        
        return {
            'description': "Tipo de encontro desconhecido",
            'time_roll': random.randint(1, 20),
            'encounter_data': None
        }

    except Exception as e:
        print(f"Erro ao gerar encontro: {str(e)}")
        return {
            'description': "Erro no sistema",
            'time_roll': random.randint(1, 20),
            'encounter_data': None
        }

def save_to_txt(results, terrain, days, is_night):
    """Salva os resultados em arquivo TXT"""
    try:
        os.makedirs('logs', exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"viagem_{terrain}_{timestamp}.txt"
        full_path = os.path.join('logs', filename)
        
        content = f"=== Relatório de Viagem ===<br>"
        content += f"Terreno: {terrain}<br>Dias: {days}<br>Período: {'noite' if is_night else 'dia'}<br><br>"
        
        for r in results:
            content += f"Dia {r['day']}: "
            content += f"{r['encounter']} ({r['time_of_day']})<br>" if r['encounter'] else "Sem encontros<br>"
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"logs/{filename}"
    except Exception as e:
        print(f"Erro ao salvar TXT: {str(e)}")
        return None

@lru_cache(maxsize=8)
def load_characteristics_file(tipo: str) -> dict:
    """Carrega arquivos de características com cache"""
    arquivos = {
        'humanoide': 'humanoide.json',
        'animal': 'animal.json',
        'monstro': 'monstro.json',
        'espirito': 'espirito.json',
        'morto-vivo': 'mortos_vivo.json',
        'lefeu': 'lefeu.json',
        'constructo': 'construto.json'
    }
    
    arquivo = arquivos.get(tipo)
    if not arquivo:
        raise ValueError(f"Tipo {tipo} não suportado")
    
    caminho = os.path.join('encounters', 'caracteristicas', arquivo)
    
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)

# ========== ROTAS PRINCIPAIS ==========
@app.route('/')
def index():
    terrains = json.load(open('tipos_terreno.json', encoding='utf-8'))
    return render_template('index.html', terrains=terrains)

@app.route('/generate', methods=['POST', 'GET'])
def generate():
    terrains = json.load(open('tipos_terreno.json', encoding='utf-8'))
    
    if request.method == 'POST':
        terrain = request.form['terrain']
        days = int(request.form['days'])
        is_night = request.form.get('time') == 'night'
        
        session['viagem_params'] = {
            'terrain': terrain,
            'days': days,
            'is_night': is_night
        }
    else:
        params = session.get('viagem_params', {})
        terrain = params.get('terrain', 'floresta')
        days = params.get('days', 1)
        is_night = params.get('is_night', False)
    
    encounter_chance = 16 if is_night else 8
    results = []
    
    for day in range(1, days + 1):
        if random.randint(1, 20) <= encounter_chance:
            encounter_data = generate_single_encounter(is_night, terrain)
            
            horarios = json.load(open('horario.json', encoding='utf-8'))
            time_of_day = None
            
            for time, time_range in horarios.items():
                if isinstance(time_range, list):
                    if time_range[0] <= encounter_data['time_roll'] <= time_range[1]:
                        time_of_day = time
                        break
                elif time_range == encounter_data['time_roll']:
                    time_of_day = time
                    break
            
            results.append({
                'day': day,
                'encounter': encounter_data['description'],
                'time_of_day': time_of_day,
                'encounter_data': encounter_data['encounter_data']
            })
        else:
            results.append({
                'day': day,
                'encounter': None,
                'time_of_day': None,
                'encounter_data': None
            })
    
    txt_file = save_to_txt(results, terrains[terrain], days, is_night)
    caracteristicas_qtd = request.args.get('qtd_carac', default=1, type=int)
    
    return render_template('results.html',
                         results=results,
                         terrain=terrains[terrain],
                         days=days,
                         txt_file=txt_file,
                         qtd_caracteristicas=caracteristicas_qtd)

@app.route('/gerar-caracteristicas/<tipo>')
def gerar_caracteristicas(tipo):
    """Gera múltiplas características para o tipo especificado"""
    try:
        qtd = request.args.get('qtd', default=1, type=int)
        caracteristicas = load_characteristics_file(tipo)
        
        qtd = min(qtd, len(caracteristicas))
        resultados = []
        chaves = list(caracteristicas.keys())
        
        for _ in range(qtd):
            if not chaves:
                break
            chave = random.choice(chaves)
            resultados.append({
                'caracteristica': chave,
                'efeito': caracteristicas[chave]
            })
            chaves.remove(chave)
            
        return jsonify(resultados)
        
    except Exception as e:
        print(f"Erro ao gerar características: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/limpar-cache')
def limpar_cache():
    load_characteristics_file.cache_clear()
    return jsonify({'status': 'Cache de características limpo'})

@app.route('/logs/<filename>')
def serve_log(filename):
    return send_from_directory('logs', filename)

# ========== ROTAS DE DEBUG ==========
@app.route('/debug/probabilidades/<terrain>')
def debug_probabilidades_route(terrain):
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()
    
    debug_category_probabilities(terrain)
    
    sys.stdout = old_stdout
    return f"<pre>{buffer.getvalue()}</pre>"

@app.route('/debug/encontros/<terrain>')
def debug_encontros_route(terrain):
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()
    
    debug_encounter_types(terrain)
    
    sys.stdout = old_stdout
    return f"<pre>{buffer.getvalue()}</pre>"

@app.route('/debug/all')
def debug_all():
    results = []
    terrains = ['floresta', 'deserto', 'cidade', 'planicie', 'costa']
    
    for terrain in terrains:
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()
        debug_category_probabilities(terrain, samples=5000)
        sys.stdout = old_stdout
        results.append(f"<h2>{terrain.upper()}</h2><pre>{buffer.getvalue()}</pre>")
        
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()
        debug_encounter_types(terrain, samples=5000)
        sys.stdout = old_stdout
        results.append(f"<pre>{buffer.getvalue()}</pre><hr>")
    
    return ''.join(results)

# ============================================================ GERADOR DE HEXÁGONOS ======================================================================

def generate_assentamento(terrain):
    """Gera detalhes completos de um assentamento"""
    base_path = f'encounters/hex/{terrain}/assentamentos/'
    resultado = {
        'tipo_assentamento': roll_for_detail(base_path + 'tipos.json'),
        'ocupacao': roll_for_detail(base_path + 'ocupacao.json'),
        'condicoes': roll_for_detail(base_path + 'condicoes.json')
    }
    
    if resultado['ocupacao'] == 'Ocupado':
        resultado.update({
            'ocupantes': roll_for_detail(base_path + 'ocupantes.json')
        })
        detalhes = (f"Tipo: {resultado['tipo_assentamento']}<br>"
                   f"Ocupação: {resultado['ocupacao']}<br>"
                   f"Ocupantes: {resultado['ocupantes']}<br>"
                   f"Condições: {resultado['condicoes']}")
    else:
        resultado['motivo_abandono'] = roll_for_detail(base_path + 'abandono.json')
        detalhes = (f"Tipo: {resultado['tipo_assentamento']}<br>"
                   f"Ocupação: {resultado['ocupacao']}<br>"
                   f"Condições: {resultado['condicoes']}<br>"
                   f"Motivo do abandono: {resultado['motivo_abandono']}")
    
    return {
        'conteudo': f"Assentamento: {resultado['tipo_assentamento']}",
        'detalhes': detalhes
    }

def generate_ruina(terrain):
    """Gera detalhes completos de uma ruína"""
    base_path = f'encounters/hex/{terrain}/ruinas/'
    resultado = {
        'tipo_ruina': roll_for_detail(base_path + 'tipos.json'),
        'proposito_original': roll_for_detail(base_path + 'proposito_original.json'),
        'proposito_atual': roll_for_detail(base_path + 'proposito_atual.json'),
        'localizacao': roll_for_detail(base_path + 'localizacao.json'),
        'peculiaridade': roll_for_detail(base_path + 'peculiaridade.json'),
        'idade': roll_for_detail(base_path + 'idade.json'),
        'ocupacao': roll_for_detail(base_path + 'ocupacao.json'),
        'palavras_chave': select_multiple(base_path + 'palavras_chave.json', 1, 3)
    }
    
    if resultado['ocupacao'] == 'Ocupado':
        resultado['ocupantes'] = roll_for_detail(base_path + 'ocupantes.json')
    
    detalhes = (f"Tipo: {resultado['tipo_ruina']}<br>"
               f"Propósito Original: {resultado['proposito_original']}<br>"
               f"Propósito Atual: {resultado['proposito_atual']}<br>"
               f"Localização: {resultado['localizacao']}<br>"
               f"Peculiaridade: {resultado['peculiaridade']}<br>"
               f"Idade: {resultado['idade']}<br>"
               f"Ocupação: {resultado['ocupacao']}")
    
    if 'ocupantes' in resultado:
        detalhes += f"<br>Ocupantes: {resultado['ocupantes']}"
    
    detalhes += f"<br>Palavras-chave: {resultado['palavras_chave']}"
    
    return {
        'conteudo': f"Ruína: {resultado['tipo_ruina']}",
        'detalhes': detalhes,
        'tipo_especifico': 'ruina'
    }

def generate_obstaculo(terrain):
    """Gera detalhes completos de um obstáculo"""
    base_path = f'encounters/hex/{terrain}/obstaculo/'
    
    # Primeiro seleciona a categoria
    categoria = roll_for_detail(base_path + 'categorias.json')
    
    # Depois seleciona o obstáculo específico baseado na categoria
    if categoria == 'Perigos da floresta':
        obstaculo = roll_for_detail(base_path + 'perigos_floresta.json')
    elif categoria == 'Causado por humanoides':
        obstaculo = roll_for_detail(base_path + 'humanos.json')
    elif categoria == 'Sobrenatural':
        obstaculo = roll_for_detail(base_path + 'sobrenatural.json')
    elif categoria == 'Surto arcano':
        obstaculo = roll_for_detail(base_path + 'surto_arcano.json')
    else:
        obstaculo = roll_for_detail(base_path + 'outro.json')
    
    detalhes = f"Categoria: {categoria}<br>Obstáculo: {obstaculo}"
    
    return {
        'conteudo': f"Obstáculo: {obstaculo}",
        'detalhes': detalhes,
        'tipo_especifico': 'obstaculo'
    }

def generate_marco_paisagem(terrain):
    """Gera detalhes completos de um marco na paisagem"""
    base_path = f'encounters/hex/{terrain}/marco_paisagem/'
    
    # Seleciona o tipo de marco
    tipo_marco = roll_for_detail(base_path + 'tipos.json')
    
    # Gera detalhes específicos do tipo
    marco_path = f"{base_path}{tipo_marco}/"
    resultado = {
        'tipo_marco': tipo_marco,
        'entrada': roll_for_detail(marco_path + 'entrada.json'),
        'peculiaridade': roll_for_detail(base_path + 'peculiaridade.json'),
        'palavras_chave': select_multiple(base_path + 'palavras_chave.json', 0, 3)
    }
    
    # Adiciona campos específicos conforme o tipo
    if os.path.exists(marco_path + 'interior.json'):
        resultado['interior'] = roll_for_detail(marco_path + 'interior.json')
    
    if os.path.exists(marco_path + 'habitantes.json'):
        resultado['habitantes'] = roll_for_detail(marco_path + 'habitantes.json')
    
    if os.path.exists(marco_path + 'peculiaridade.json'):
        resultado['peculiaridade_especifica'] = roll_for_detail(marco_path + 'peculiaridade.json')
    
    # Construção da descrição
    detalhes = f"Tipo: {resultado['tipo_marco']}<br>"
    detalhes += f"Entrada: {resultado['entrada']}<br>"
    
    if 'interior' in resultado:
        detalhes += f"Interior: {resultado['interior']}<br>"
    
    if 'habitantes' in resultado:
        detalhes += f"Habitantes: {resultado['habitantes']}<br>"
    
    detalhes += f"Peculiaridade: {resultado['peculiaridade']}<br>"
    
    if 'peculiaridade_especifica' in resultado:
        detalhes += f"Peculiaridade Específica: {resultado['peculiaridade_especifica']}<br>"
    
    detalhes += f"Palavras-chave: {resultado['palavras_chave']}"
    
    return {
        'conteudo': f"Marco: {resultado['tipo_marco']}",
        'detalhes': detalhes,
        'tipo_especifico': 'marco_paisagem'
    }

def select_multiple(file_path, min_select=1, max_select=3):
    """Seleciona múltiplos itens de uma lista"""
    with open(file_path, 'r', encoding='utf-8') as f:
        options = json.load(f)
    
    if isinstance(options, dict):
        options = list(options.keys())
    
    num = random.randint(min_select, min(max_select, len(options)))
    selected = random.sample(options, num)
    return ", ".join(selected)

def generate_hex_description(terrain):
    """Gera uma descrição completa de um hexágono"""
    # Carrega a distribuição principal
    with open('encounters/hex/distribuicao.json', 'r', encoding='utf-8') as f:
        distribuicao = json.load(f)[terrain]
    
    # 1º Nível: Decide o tipo de conteúdo
    tipo_conteudo = select_by_weight(distribuicao)
    
    # Carrega tabelas específicas do terreno
    tabelas = load_hex_tables(terrain)
    
    # Gera elementos básicos (sempre presentes)
    resultado = {
        'terreno': terrain,
        'paisagem': select_by_weight(tabelas['paisagens']),
        'sons': select_by_weight(tabelas['sons']),
        'odores': select_by_weight(tabelas['odores']),
        'conteudo': None,
        'detalhes': None,
        'tipo': tipo_conteudo
    }
    
    # 2º Nível: Gera o conteúdo específico
    if tipo_conteudo == 'paisagem_mundana':
        resultado['conteudo'] = "Paisagem mundana"
        resultado['detalhes'] = "Nada de especial além da paisagem normal do terreno."
    
    elif tipo_conteudo == 'assentamento':
        resultado.update(generate_assentamento(terrain))
    
    elif tipo_conteudo == 'ruina':
        resultado.update(generate_ruina(terrain))
    
    elif tipo_conteudo == 'obstaculo':
        resultado.update(generate_obstaculo(terrain))
    
    elif tipo_conteudo == 'marco_paisagem':
        resultado.update(generate_marco_paisagem(terrain))
    
    elif tipo_conteudo == 'evento':
        resultado['conteudo'] = "Evento especial"
        resultado['detalhes'] = select_by_weight(tabelas['eventos'])
    
    elif tipo_conteudo == 'obstaculo_ruina':
        obstaculo = generate_obstaculo(terrain)
        ruina = generate_ruina(terrain)
        resultado['conteudo'] = f"{obstaculo['conteudo']} + {ruina['conteudo']}"
        resultado['detalhes'] = f"{obstaculo['detalhes']}<br><br>{ruina['detalhes']}"
    
    return resultado

def load_hex_tables(terrain):
    """Carrega TODAS as tabelas específicas do terreno"""
    tables = {}
    terrain_path = f'encounters/hex/{terrain}/'
    
    table_types = [
        'paisagens', 'sons', 'odores', 'eventos'
    ]
    
    for table in table_types:
        try:
            with open(terrain_path + f'{table}.json', 'r', encoding='utf-8') as f:
                tables[table] = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar {table}.json: {str(e)}")
            tables[table] = {"Erro": f"Arquivo {table}.json não encontrado ou inválido"}
    
    return tables

@app.route('/gerar-hexagono', methods=['GET', 'POST'])
def gerar_hexagono():
    terrains = json.load(open('tipos_terreno.json', encoding='utf-8'))
    
    if request.method == 'POST':
        terreno = request.form['terreno']
        hex_data = generate_hex_description(terreno)
        return render_template('hex_result.html', 
                            hex=hex_data, 
                            terrains=terrains,
                            format_details=format_hex_details)
    
    return render_template('hex_form.html', terrains=terrains)

def format_hex_details(hex_data):
    """Formata os detalhes do hexágono para exibição HTML"""
    if not hex_data['detalhes']:
        return ""
    
    if isinstance(hex_data['detalhes'], str):
        return hex_data['detalhes'].replace('<br>', '<br>')
    
    return str(hex_data['detalhes'])

if __name__ == '__main__':
    if os.environ.get('DEBUG') == '1':
        print("<br>=== INICIANDO DEBUG ===")
        debug_category_probabilities('floresta')
        debug_encounter_types('floresta')
    
    app.run(debug=True)

    # Acessa http://localhost:5000/debug/probabilidades/floresta ou http://localhost:5000/debug/all pra DEBUG