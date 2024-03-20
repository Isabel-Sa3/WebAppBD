import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from flask import render_template, Flask, abort, request
import logging
import db

APP = Flask(__name__)

# Start page
@APP.route('/')
def index():
    stats={}
    stats = db.execute('''
        SELECT * FROM
            (SELECT COUNT(*) n_animais FROM animais)
        JOIN
            (SELECT COUNT(*) n_recolha FROM recolha_animal)
        JOIN
            (SELECT COUNT(*) n_distritos FROM distritos)
        JOIN
            (SELECT COUNT(*) n_bairros FROM bairros)
    ''').fetchone()
    logging.info(stats)
    return render_template('index.html',stats=stats)

# --------------------------------------------------------

#distritos
@APP.route('/distritos/')
def listar_distritos():
    distritos = db.execute('''
        SELECT distritos.Distritos_id, distritos.Distrito, COUNT(*) num_bairros
        FROM distritos 
        JOIN bairros ON bairros.Distritos_id = distritos.Distritos_id
        GROUP BY distritos.Distritos_id
        ORDER BY distritos.Distritos_id
    ''').fetchall()
    return render_template('distritos-list.html', distritos=distritos)

@APP.route('/distritos/<int:codigo>/')
def distrito(codigo):
    # Obtém dados do distrito
    distritos = db.execute('''
        SELECT Distritos_id, Distrito
        FROM distritos 
        WHERE Distritos_id = ?
    ''', [codigo]).fetchone()
    # Obtém bairros no distrito
    bairros = db.execute('''
        SELECT Codigo_bairro, Bairro
        FROM bairros 
        JOIN distritos ON bairros.Distritos_id = distritos.Distritos_id
        WHERE distritos.Distritos_id = ?
        ORDER BY Codigo_bairro
    ''', [codigo]).fetchall()
    return render_template('distritos.html', 
                            distritos=distritos,
                            bairros=bairros)

@APP.route('/distritos/search/<expr>/')
def search_distritos(expr):
  search = { 'expr': expr }
  expr = '%' + expr + '%'
  distritos = db.execute(
      ''' 
      SELECT Distritos_id, distrito
      FROM distritos 
      WHERE distritos LIKE ?
      ''', [expr]).fetchall()
  return render_template('distritos-search.html',
           search=search,distritos=distritos)
# --------------------------------------------------------

#Bairros
@APP.route('/bairros/')
def listar_bairros():
    Bairros = db.execute(
    '''
    SELECT bairros.Codigo_bairro, Bairro, Distritos_id, count(*) n_recolhas
    FROM bairros
    JOIN recolha_animal on bairros.Codigo_bairro = recolha_animal.Codigo_bairro
    GROUP BY bairros.Codigo_bairro, Bairro, Distritos_id
    ORDER BY Bairro
    ''').fetchall()
    return render_template('bairros-list.html', Bairros=Bairros)

@APP.route('/bairros/<int:id>/')
def get_bairros(id):
    bairros = db.execute(
    '''
    SELECT bairros.Codigo_bairro, bairros.Bairro, bairros.Distritos_id,distritos.Distrito, count(*)
    FROM bairros
    JOIN distritos on bairros.Distritos_id = distritos.Distritos_id
    JOIN recolha_animal on bairros.Codigo_bairro = recolha_animal.Codigo_bairro
    WHERE bairros.Codigo_bairro = ?
    ''', [id]).fetchone()

    if bairros is None:
        abort(404, f'Bairro {id} não existe')

    recolha_animal = db.execute(
        '''
        SELECT RecolhaAnimal_id
        FROM recolha_animal join
        bairros on bairros.Codigo_bairro = recolha_animal.Codigo_bairro
        WHERE bairros.Codigo_bairro = ?
    ''', [id]).fetchall()
    
    animais = db.execute(
        '''
        SELECT Tipo_animal
        FROM animais natural join recolha_animal natural join bairros
        where Codigo_bairro = ?
        group by Tipo_animal
    ''', [id]).fetchall()
    
    return render_template('bairros.html', bairros=bairros, recolha_animal=recolha_animal, animais=animais)

@APP.route('/bairros/search/<expr>/')
def search_bairros(expr):
  search = { 'expr': expr }
  expr = '%' + expr + '%'
  bairros = db.execute(
      ''' 
      SELECT Codigo_bairro, Bairro
      FROM bairros
      WHERE Bairro LIKE ?
      ''', [expr]).fetchall()
  return render_template('bairros-search.html',
           search=search,bairros=bairros)
# --------------------------------------------------------

#Recolha
@APP.route('/recolhas/')
def listar_recolha():
    recolha_animal = db.execute(
    '''
    SELECT Codigo_bairro,RecolhaAnimal_id, Recepcao, Turno_recolha,Hora_recolha,Fim_recolha,Canal_de_entrada, Local_de_recolha,Execucao, Animal_id
    FROM recolha_animal 
    order by RecolhaAnimal_id
    ''').fetchall()
    return render_template('recolha-list.html', recolha_animal=recolha_animal)

@APP.route('/recolhas/<int:id>/')
def get_recolha(id):
    recolha_animal = db.execute(
    '''
    SELECT Codigo_bairro,RecolhaAnimal_id, Recepcao, Turno_recolha,Hora_recolha,Fim_recolha,Canal_de_entrada, Local_de_recolha,Execucao, Animal_id
    FROM recolha_animal 
    WHERE RecolhaAnimal_id = ?
    ''', [id]).fetchone()
    
    if recolha_animal is None:
        abort(404, f'Recolha {id} não existe')
    return render_template('recolha.html',  recolha_animal=recolha_animal)

@APP.route('/recolhas/pesquisa_avancada/<tipo>/<valor>/')
def animais_recolhas(tipo, valor):
    if tipo == 'bairro':
        search = {'expr': valor}
        valor = '%' + valor + '%'
        recolha_animal = db.execute(
            '''
            SELECT recolha_animal.RecolhaAnimal_id, bairros.Bairro AS Nome
            FROM recolha_animal
            JOIN bairros on recolha_animal.Codigo_bairro = bairros.Codigo_bairro
            WHERE bairros.Bairro LIKE ?
            ''', [valor]).fetchall()
    elif tipo == 'distrito':
        search = {'expr': valor}
        valor = '%' + valor + '%'
        recolha_animal = db.execute(
            '''
            SELECT recolha_animal.RecolhaAnimal_id, distritos.Distrito AS Nome
            FROM recolha_animal
            JOIN bairros on recolha_animal.Codigo_bairro = bairros.Codigo_bairro
            JOIN distritos on bairros.Distritos_id= distritos.Distritos_id
            WHERE distritos.Distrito LIKE  ?
            ''', [valor]).fetchall()
    elif tipo == 'animal':
        search = {'expr': valor}
        valor = '%' + valor + '%'
        recolha_animal = db.execute(
            '''
            SELECT recolha_animal.RecolhaAnimal_id, animais.Tipo_animal AS Nome
            FROM recolha_animal
            JOIN animais on animais.Animal_id = recolha_animal.Animal_id
            WHERE animais.Tipo_animal LIKE ?
            ''', [valor]).fetchall()
    else:
        # Handle invalid search type
        abort(404)

    return render_template('recolha-search.html', search=search, recolha_animal=recolha_animal)

# --------------------------------------------------------

#Animais
@APP.route('/animais/')
def list_animais():
    animais = db.execute(
        '''
        SELECT Animal_id, Tipo_animal,N_animais,Peso_aproximado,Microchip
        FROM animais
        ORDER BY Animal_id
        '''
    ).fetchall()
    result = db.execute(
    '''
    SELECT Tipo_animal, COUNT(*) AS total_animais
    FROM animais
    GROUP BY Tipo_animal
    ''').fetchall()
    return render_template('animais-list.html', animais=animais, result=result)

@APP.route('/animais/<int:id>')
def get_animais(id):
    animais = db.execute(
    '''
        SELECT Animal_id, Tipo_animal,N_animais,Peso_aproximado,Microchip
        FROM animais
        Where  Animal_id=?
    ''', [id]).fetchone()

    if animais is None:
        abort(404, f'Atividade {id} não existe')    

    return render_template('animais.html', animais=animais)

@APP.route('/animais/search/')
def animais_pesquisa():
    return render_template('animais-search.html')

@APP.route('/animais/searchResult/')
def pesquisa_animais():
    Tipo_animal = request.args.get('Tipo_animal', default='', type=str)
    peso_min = request.args.get('peso_min', default=0, type=float)
    
    animais = db.execute(
        '''
        SELECT Animal_id, Tipo_animal, N_animais, Peso_aproximado, Microchip
        FROM animais
        WHERE Tipo_animal LIKE ? AND Peso_aproximado >= ?
        ''', ['%' + Tipo_animal + '%', peso_min]
    ).fetchall()

    return render_template('animais-search-result.html', animais=animais, Tipo_animal=Tipo_animal, peso_min=peso_min)

#Tipo de animais
@APP.route('/tipo_animais/')
def list_tip_animais():
    tipo = db.execute(
    '''
    SELECT Tipo_animal, COUNT(*) AS total_animais, avg(peso_aproximado) as avg, min(peso_aproximado) as min, max(peso_aproximado) as max
    FROM animais
    GROUP BY Tipo_animal
    ''').fetchall()
    return render_template('tipo_animais.html',  tipo=tipo)

# --------------------------------------------------------
@APP.route('/recolhas/pesquisa_avancada/')
def adv_search_recolhas():
    return render_template('recolha-adv-search.html')

#----------------------------------------------------------

# Para as páginas de pesquisa de especies para uma dada localidade
@APP.route('/especie-para-distrito/search/<expr>')
def esp_distr(expr):
    search = { 'expr': expr }
    expr = '%' + expr + '%'
    dicionario=db.execute(
        '''
        SELECT animais.Tipo_animal as animal, distritos.Distrito as territorio,distritos.Distritos_id as id, count(recolha_animal.RecolhaAnimal_id) as n_recolha
        FROM animais
        join recolha_animal  on animais.Animal_id=recolha_animal.Animal_id
        join bairros on recolha_animal.Codigo_bairro=bairros.Codigo_bairro
        join distritos on bairros.Distritos_id=distritos.Distritos_id
        where animais.Tipo_animal like ?
        group by animais.Tipo_animal, distritos.Distrito;
        ''', [expr]).fetchall()
    if (dicionario is None):
        abort(404, f'Animal {expr} não existe')
    return render_template('localidade_animal.html',dicionario=dicionario, search=search)

@APP.route('/especie-para-bairro/search/<expr>')
def bair_para_esp(expr):
    search = { 'expr': expr }
    expr = '%' + expr + '%'
    dicionario=db.execute(
        '''
        SELECT animais.Tipo_animal as animal, bairros.Bairro as territorio,bairros.Codigo_bairro as id, count(recolha_animal.RecolhaAnimal_id) as n_recolha
        FROM animais
        join recolha_animal  on animais.Animal_id=recolha_animal.Animal_id
        join bairros on recolha_animal.Codigo_bairro=bairros.Codigo_bairro
        where animais.Tipo_animal like ?
        group by animais.Tipo_animal, bairros.Bairro;
        ''', [expr]).fetchall()
    if (dicionario is None):
        abort(404, f'Animal {expr} não existe')
    return render_template('localidade animal_bairro.html',dicionario=dicionario, search=search)