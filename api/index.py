from flask import Flask, render_template, request, abort
import requests
import json
import codecs
import math

from jinja2 import Environment, FileSystemLoader

import logging

# from decryptor import ManagerDecrypt

# get_ep 

import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

class ManagerDecrypt:
    def __init__(self):
        self.keys = [
            "mS9wR2qY7pK7vX5n",
            "fV3gK5vU7uG6hU5e",
            "oU0dI2lL2tK2dR9f",
        ]

        # Configuração baseada no script original
        self.config = {
            "sigBytes": 32,
            "words": [
                1884436332, 1295477057, 929846578, 1867920227,
                1144552015, 878792752, 1917597540, 1211458376
            ],
        }

    @staticmethod
    def reverse(value: str) -> str:
        """
        Reverte uma string.
        """
        return value[::-1]

    def decrypt_jwt(self, token: str) -> str:
        """
        Decifra um token JWT usando a lógica migrada do TypeScript.
        """
        try:
            # Extrai os últimos 64 caracteres como IV
            iv = token[-64:]
            iv_reversed = self.reverse(iv)

            # Ajusta o IV para os primeiros 16 bytes (128 bits)
            iv_bytes = iv_reversed.encode('utf-8')[:16]

            # Extrai o payload criptografado do token
            encrypted_payload = token[36:-64]
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_payload + '==')

            # Simula a chave (usando os "words" do config como base para gerar uma chave)
            key_bytes = b''.join(w.to_bytes(4, 'big') for w in self.config["words"])

            # Decifra usando AES com CBC
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
            decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
            return decrypted_bytes.decode('utf-8')

        except Exception as e:
            return f"Failed to decrypt: {e}"


# end get_ep

logging.basicConfig(level=logging.DEBUG)

# Inicializa o decryptor
decryptor = ManagerDecrypt()

# Define a função como filtro
def decrypt_jwt_filter(token):
    return decryptor.decrypt_jwt(token)

app = Flask(__name__)

# Registra o filtro no ambiente Jinja2 do Flask
app.jinja_env.filters["decrypt_jwt"] = decrypt_jwt_filter

@app.route('/')
def index():
    popular_animes_url = 'https://atv2.net/meuanimetv-74.php?populares'
    latest_episodes_url = 'https://atv2.net/meuanimetv-74.php?latest'
    
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
    anime_info_url = f'https://atv2.net/meuanimetv-74.php?info={id}'
    episodes_url = f'https://atv2.net/meuanimetv-74.php?cat_id={id}'

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
        search_url = f'https://atv2.net/meuanimetv-74.php?search={search_query}'
        search_response = requests.get(search_url)
        
        if search_response.status_code == 200:
            search_content = search_response.content.decode('utf-8-sig').lstrip('\ufeff')
            search_results = json.loads(search_content)
            return render_template('search_results.jinja', query=search_query, results=search_results)
    
    return render_template('search_results.jinja', query=search_query, results=None)

@app.route('/video/<int:id>')
def get_video_episodes(id):
    # URL da API
    episodes_url = f'https://atv2.net/meuanimetv-74.php?episodios={id}'
    logging.debug(f"Requesting URL: {episodes_url}")

    try:
        # Faz a requisição para a API
        episodes_response = requests.get(episodes_url, timeout=10)
        logging.debug(f"Response Status Code: {episodes_response.status_code}")

        # Verifica se a resposta é bem-sucedida
        if episodes_response.status_code == 200:
            content = episodes_response.content.decode('utf-8-sig', errors='replace').lstrip('\ufeff')
            logging.debug(f"API Response Content: {content}")

            try:
                # Parseia o JSON retornado pela API
                episodes_data = json.loads(content)
                logging.debug(f"Parsed JSON: {episodes_data}")

                # Verifica se os dados retornados não estão vazios
                if episodes_data and isinstance(episodes_data, list):
                    ep = episodes_data[0]  # Assume o primeiro item como válido
                    
                    # Decifra o token JWT, se existir
                    if 'mS9wR2qY7pK7vX5n' in ep and ep['mS9wR2qY7pK7vX5n']:
                        try:
                            decoded_video_url = decryptor.decrypt_jwt(ep['mS9wR2qY7pK7vX5n'])
                            ep['decoded_video_url'] = decoded_video_url
                            logging.debug(f"Decoded Video URL: {decoded_video_url}")
                        except Exception as e:
                            logging.error(f"Error decrypting JWT: {e}")
                            ep['decoded_video_url'] = None
                    else:
                        ep['decoded_video_url'] = None

                    return render_template('get_video_episodes.jinja', ep=ep)
                else:
                    logging.error("Empty or unexpected data structure in API response.")
                    return render_template(
                        'error.html',
                        error="A API retornou uma estrutura inesperada ou vazia."
                    ), 500
            except json.JSONDecodeError as e:
                logging.error(f"JSON Decode Error: {e}")
                return render_template(
                    'error.html',
                    error=f"Erro ao decodificar o JSON retornado pela API: {e}"
                ), 500
        else:
            logging.error(f"API returned status code {episodes_response.status_code}")
            return render_template(
                'error.html',
                error=f"A API retornou um erro com o status code {episodes_response.status_code}."
            ), episodes_response.status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Request Exception: {e}")
        return render_template(
            'error.html',
            error=f"Erro ao fazer a requisição para a API: {e}"
        ), 500
    except Exception as e:
        logging.error(f"Unexpected Error: {e}")
        return render_template(
            'error.html',
            error=f"Ocorreu um erro inesperado: {e}"
        ), 500
    
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

    api_url = f'https://atv2.net/meuanimetv-74.php'
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
    app.run()
