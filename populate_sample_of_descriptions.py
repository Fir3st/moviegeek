import os

import django
import json
import requests
import time
import urllib.request
from tqdm import tqdm

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prs_project.settings')

django.setup()

from recommender.models import MovieDescriptions
NUMBER_OF_PAGES = 15760
start_date = "1970-01-01"


def get_descriptions():
    # MovieDescriptions.objects.all().delete()

    movies = download_movies()

    print('movie data downloaded')

    api_key = get_api_key()
    omdb_key = get_omdb_key()

    omdb_url = """http://www.omdbapi.com/?i=tt{}&apikey={}"""
    tmdb_url = """https://api.themoviedb.org/3/{}/tt{}?api_key={}&external_source=imdb_id"""
    movies = movies.split(sep="\n")

    for movie in tqdm(movies[1:]):
        m = movie.split(sep=",")
        r = requests.get(omdb_url.format(m[1], omdb_key))
        omdb_result = r.json()
        t = 'movie' if omdb_result.get('Type') == 'movie' else 'tv'
        r = requests.get(tmdb_url.format(t, m[1], api_key))
        tmdb_result = r.json()

        id = m[2]
        imdb_id = f"tt{m[1]}"
        print(f"Movie: {omdb_result.get('Title')}, id: {id}, IMDB ID: {imdb_id}")
        md = MovieDescriptions.objects.get_or_create(movie_id=id)[0]

        md.imdb_id = imdb_id
        md.title = omdb_result.get('Title')
        md.description = omdb_result.get('Plot')
        genres = tmdb_result['genres'] if 'genres' in tmdb_result else []
        md.genres = [genres[i].get('id') for i in range(len(genres))]
        if None != md.imdb_id:
            md.save()

        time.sleep(1)


def download_movies():
    URL = 'https://raw.githubusercontent.com/Fir3st/hybrid-recommender-app/master/server/src/utils/data/filtered/links.csv'
    response = urllib.request.urlopen(URL)
    data = response.read()
    return data.decode('utf-8')

def save_as_csv():
    url = """https://api.themoviedb.org/3/discover/movie?primary_release_date.gte=2016-01-01
    &primary_release_date.lte=2016-10-22&api_key={}&page={}"""
    api_key = get_api_key()

    file = open('data.json','w')

    films = []
    for page in range(1, NUMBER_OF_PAGES):
        r = requests.get(url.format(api_key, page))
        for film in r.json()['results']:
            f = dict()

            f['id'] = film['id']
            f['imdb_id'] = get_imdb_id(f['id'])
            f['title'] = film['title']
            f['description'] = film['overview']
            f['genres'] = film['genre_ids']
            films.append(f)
        print("{}: {}".format(page, r.json()))

    json.dump(films, file, sort_keys=True, indent=4)

    file.close()


def get_imdb_id(moviedb_id):
    url = """https://api.themoviedb.org/3/movie/{}?api_key={}"""

    r = requests.get(url.format(moviedb_id, get_api_key()))

    json = r.json()
    print(json)
    if 'imdb_id' not in json:
        return ''
    imdb_id = json['imdb_id']
    if imdb_id is not None:
        print(imdb_id)
        return imdb_id[2:]
    else:
        return ''


def get_api_key():
    # Load credentials
    cred = json.loads(open(".prs").read())
    return cred['themoviedb_apikey']


def get_omdb_key():
    # Load credentials
    cred = json.loads(open(".prs").read())
    return cred['omdb_key']


def get_popular_films_for_genre(genre_str):
    film_genres = {'drama': 18, 'action': 28, 'comedy': 35}
    genre = film_genres[genre_str]

    url = """https://api.themoviedb.org/3/discover/movie?sort_by=popularity.desc&with_genres={}&api_key={}"""
    api_key = get_api_key()
    r = requests.get(url.format(genre, api_key))
    print(r.json())
    films = []
    for film in r.json()['results']:
        id = film['id']
        imdb = get_imdb_id(id)
        print("{} {}".format(imdb, film['title']))
        films.append(imdb[2:])
    print(films)


if __name__ == '__main__':
    print("Starting MovieGeeks Population script...")
    get_descriptions()
    # get_popular_films_for_genre('comedy')
    # save_as_csv()
