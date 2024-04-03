from flask import Flask, render_template, request, abort
import requests
import json
import codecs
import math


app = Flask(__name__)

@app.route('/')
def index():
    popular_animes_url = 'https://appanimeplus.tk/play-api.php?populares'
    latest_episodes_url = 'https://appanimeplus.tk/play-api.php?latest'
    
    popular_response = requests.get(popular_animes_url)
    latest_response = requests.get(latest_episodes_url)
    
    if popular_response.status_code == 200 and latest_response.status_code == 200:
        popular_content = popular_response.content.decode('utf-8-sig').lstrip('\ufeff')
        popular_animes = json.loads(popular_content)[:15]  # Limita para os 15 primeiros animes

        latest_content = latest_response.content.decode('utf-8-sig').lstrip('\ufeff')
        latest_episodes = json.loads(latest_content)[:15] 
                
        return render_template('index.jinja', popular_animes=popular_animes, latest_episodes=latest_episodes)
    else:
        abort(404)  # Redireciona para a página de erro 404

@app.route('/anime/<int:id>')
def get_anime(id):
    anime_info_url = f'https://appanimeplus.tk/play-api.php?info={id}'
    episodes_url = f'https://appanimeplus.tk/play-api.php?cat_id={id}'

    anime_response = requests.get(anime_info_url)
    episodes_response = requests.get(episodes_url)
    
    if anime_response.status_code == 200 and episodes_response.status_code == 200:
        anime_content = anime_response.content.decode('utf-8-sig').lstrip('\ufeff')
        anime_data = json.loads(anime_content)

        episodes_content = episodes_response.content.decode('utf-8-sig').lstrip('\ufeff')
        episodes_data = json.loads(episodes_content)

        return render_template('get_anime.jinja', anime=anime_data[0], episodes=episodes_data)
    else:
        abort(404)  # Redireciona para a página de erro 404

@app.route('/search')
def search_anime():
    search_query = request.args.get('query')

    if search_query:
        search_url = f'https://appanimeplus.tk/play-api.php?search={search_query}'
        search_response = requests.get(search_url)
        
        if search_response.status_code == 200:
            search_content = search_response.content.decode('utf-8-sig').lstrip('\ufeff')
            search_results = json.loads(search_content)
            return render_template('search_results.jinja', query=search_query, results=search_results)
    
    return render_template('search_results.jinja', query=search_query, results=None)

@app.route('/video/<int:id>')
def get_video_episodes(id):
    episodes_url = f'https://appanimeplus.tk/play-api.php?episodios={id}'
    episodes_response = requests.get(episodes_url)
    
    if episodes_response.status_code == 200:
        content = episodes_response.content.decode('utf-8-sig')  # Remove o BOM se estiver presente
        clean_content = content.lstrip('\ufeff')  # Remove o BOM no início da string, se necessário
        episodes_data = json.loads(clean_content)
        return render_template('get_video_episodes.jinja', video_id=id, episodes=episodes_data)
    else:
        abort(404)  # Redireciona para a página de erro 404
 
    
# Pagina de erro 404
@app.errorhandler(404)
def page_not_found(error):
    return render_template('error404.jinja'), 404

@app.route('/animes/')
def list_animes():
    page = request.args.get('page', default=1, type=int)
    items_per_page = 24  # Quantidade de animes por página

    start_index = (page - 1) * items_per_page
    end_index = page * items_per_page

    api_url = f'https://appanimeplus.tk/play-api.php'
    response = requests.get(api_url, params={'page': page})

    if response.status_code == 200:
        # Remover o BOM se estiver presente
        content = response.content.decode('utf-8-sig')

        all_animes = json.loads(content)
        animes_for_page = all_animes[start_index:end_index]

        total_pages = len(all_animes) // items_per_page

        return render_template('animes.jinja', animes=animes_for_page, total_pages=total_pages, current_page=page)
    else:
        return render_template('error.html'), 500  # Página de erro em caso de falha na requisição
    
if __name__ == '__main__':
    app.run(debug=True)