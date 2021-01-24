from flask import Flask, render_template, request, url_for, make_response, session, redirect, flash
from flask_login import login_required, current_user
from mysql_db import MySQL
import mysql.connector as connector

app = Flask(__name__)
application = app

app.config.from_pyfile('config.py')

mysql = MySQL(app)

from auth import bp as auth_bp, init_login_manager, check_rights

init_login_manager(app)
app.register_blueprint(auth_bp)

def load_genres():
    cursor = mysql.connection.cursor(named_tuple=True)
    cursor.execute('SELECT id, name FROM exam_genres;')
    roles = cursor.fetchall()
    cursor.close()
    return roles

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/films')
def films():
    cursor = mysql.connection.cursor(named_tuple=True)
    cursor.execute(
        'SELECT id, name, description, production_year FROM exam_films;')
    films = cursor.fetchall()
    cursor.execute('SELECT t3.name AS g_name, t1.id as f_id FROM exam_films t1 JOIN exam_films_genres t2 ON t1.id=t2.film_id JOIN exam_genres t3 ON t2.genre_id=t3.id ;')
    genres = cursor.fetchall()
    cursor.execute('SELECT COUNT(t1.id) AS ct, t2.id FROM exam_reviews t1 JOIN exam_films t2 ON t1.film_id=t2.id GROUP BY t2.id;')
    reviews = cursor.fetchall()
    cursor.close()
    return render_template('films/index.html', films=films, genres=genres, reviews=reviews)

@app.route('/films/<int:film_id>')
@check_rights('show')
@login_required
def show(film_id):
    cursor = mysql.connection.cursor(named_tuple=True)
    cursor.execute('SELECT * FROM exam_films WHERE id = %s;', (film_id,))
    film = cursor.fetchone()
    cursor.execute('SELECT t1.review_text, t1.rating, t1.date_added, t2.last_name, t2.first_name FROM exam_reviews t1 JOIN exam_users t2 ON t1.user_id=t2.id WHERE film_id = %s;', (film_id,))
    reviews = cursor.fetchall()
    cursor.execute('SELECT t3.name AS g_name, t1.id as f_id FROM exam_films t1 JOIN exam_films_genres t2 ON t1.id=t2.film_id JOIN exam_genres t3 ON t2.genre_id=t3.id ;')
    genres = cursor.fetchall()
    cursor.close()
    return render_template('films/show.html', film=film, reviews=reviews, genres=genres)


@app.route('/films/<int:film_id>/delete', methods=['POST'])
@check_rights('delete')
@login_required
def delete(film_id):
    with mysql.connection.cursor(named_tuple=True) as cursor:
        try:
            cursor.execute('DELETE FROM exam_films WHERE id = %s;', (film_id,))
        except connector.errors.DatabaseError:
            flash('Не удалось удалить запись.', 'danger')
            return redirect(url_for('films'))
        mysql.connection.commit()
        flash('Запись была успешно удалена.', 'success')
    return redirect(url_for('films'))

@app.route('/films/<int:film_id>/edit')
@check_rights('edit')
@login_required
def edit(film_id):
    cursor = mysql.connection.cursor(named_tuple=True)
    cursor.execute('SELECT * FROM exam_films WHERE id = %s;', (film_id,))
    film = cursor.fetchone()
    cursor.close()
    return render_template('films/edit.html', film=film, genres=load_genres())

@app.route('/films/<int:film_id>/update', methods=['POST'])
@check_rights('edit')
@login_required
def update(film_id):
    name = request.form.get('name') or None
    description = request.form.get('description') or None
    production_year = request.form.get('production_year') or None
    country = request.form.get('country') or None
    director = request.form.get('director') or None
    screenwriter = request.form.get('screenwriter') or None
    actors = request.form.get('actors') or None
    duration = request.form.get('duration') or None
    genre_id = request.form.get('genre_id') or None
    query = '''
        UPDATE exam_films SET name=%s, description=%s, production_year=%s, country=%s, director=%s, screenwriter=%s, actors=%s, duration=%s, genre_id=%s
        WHERE id=%s;
    '''
    cursor = mysql.connection.cursor(named_tuple=True)
    try:
        cursor.execute(query, (name, description, production_year, country, director, screenwriter, actors, duration, film_id, genre_id))
    except connector.errors.DatabaseError:
        flash('Введены некорректные данные, ошибка сохранения', 'danger')
        film = {
            'id': film_id,
            'name': name,
            'description': description,
            'country': country,
            'director': director,
            'screenwriter': screenwriter,
            'actors': actors,
            'duration': duration,
            'genre_id': genre_id
            
        }
        return render_template('film/edit.html', film=film, genres=load_genres())
    mysql.connection.commit()
    cursor.close()
    flash(f'Фильм {name} был успешно обновлён.', 'success')
    return redirect(url_for('films'))


@app.route('/films/new')
@check_rights('new')
@login_required
def new():
    return render_template('films/new.html', film={})

@app.route('/films/create', methods=['POST'])
@check_rights('new')
@login_required
def create():
    name = request.form.get('name') or None
    description = request.form.get('description') or None
    production_year = request.form.get('production_year') or None
    country = request.form.get('country') or None
    director = request.form.get('director') or None
    screenwriter = request.form.get('screenwriter') or None
    actors = request.form.get('actors') or None
    duration = request.form.get('duration') or None
    poster_id = request.form.get('poster_id') or None
    try:
        role_id = int(request.form.get('role_id'))
    except ValueError:
        role_id = None
    query = '''
        INSERT INTO users (name, description, production_year, country, director, screenwriter, actors, duration, poster_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    '''
    cursor = mysql.connection.cursor(named_tuple=True)
    try:
        cursor.execute(query, (name, description, production_year, country, director, screenwriter, actors, duration))
    except connector.errors.DatabaseError:
        flash('Введены некорректные данные, ошибка сохранения', 'danger')
        user = {
            'name': name,
            'description': description,
            'country': country,
            'director': director,
            'screenwriter': screenwriter,
            'actors': actors,
            'duration': duration
        }
        return render_template('users/new.html', user=user, roles=load_roles())
    mysql.connection.commit()
    cursor.close()
    flash(f'Фильм {name} был успешно добавлен.', 'success')
    return redirect(url_for('users'))