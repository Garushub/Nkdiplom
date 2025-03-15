from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '2021260401gg',
    'database': 'car_rental'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cars")
    cars = cursor.fetchall()
    for car in cars:
        cursor.execute("SELECT * FROM rental_prices WHERE car_id = %s", (car['id'],))
        car['prices'] = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', cars=cars)

@app.route('/car/<int:car_id>')
def car_detail(car_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cars WHERE id = %s", (car_id,))
    car = cursor.fetchone()
    cursor.execute("SELECT * FROM rental_prices WHERE car_id = %s", (car_id,))
    prices = cursor.fetchall()
    cursor.execute("SELECT * FROM car_features WHERE car_id = %s", (car_id,))
    features = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('car_detail.html', car=car, prices=prices, features=features)

@app.route('/upload', methods=['GET', 'POST'])
def upload_car():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему, чтобы добавить автомобиль.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        license_plate = request.form['license_plate']
        photo = request.files['photo']
        photo_filename = photo.filename
        photo.save(f'static/uploads/{photo_filename}')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO cars (название, категория, гос_номер, фото) VALUES (%s, %s, %s, %s)",
                       (name, category, license_plate, photo_filename))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/rent', methods=['POST'])
def rent_car():
    car_id = request.form['car_id']
    rent_period = request.form['rent_period']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT цена FROM rental_prices WHERE car_id = %s AND срок = %s", (car_id, rent_period))
    price = cursor.fetchone()
    cursor.close()
    conn.close()
    if price:
        total_cost = price['цена']
    else:
        total_cost = "Цена не найдена"

    return render_template('rent_result.html', total_cost=total_cost)

@app.route('/category/<string:category>')
def show_category(category):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cars WHERE категория = %s", (category,))
    cars = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('category.html', cars=cars, category=category)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему, чтобы просмотреть профиль.')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/favorites')
def favorites():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему, чтобы просмотреть избранные автомобили.')
        return redirect(url_for('login'))

    favorite_car_ids = session.get('favorites', [])
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if favorite_car_ids:
        format_strings = ','.join(['%s'] * len(favorite_car_ids))
        cursor.execute(f"SELECT * FROM cars WHERE id IN ({format_strings})", tuple(favorite_car_ids))
        favorite_cars = cursor.fetchall()
    else:
        favorite_cars = []
    cursor.close()
    conn.close()
    return render_template('favorites.html', cars=favorite_cars)

@app.route('/add_to_favorites/<int:car_id>', methods=['POST'])
def add_to_favorites(car_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему, чтобы добавить автомобиль в избранное.')
        return redirect(url_for('login'))

    favorites = session.get('favorites', [])
    if car_id not in favorites:
        favorites.append(car_id)
        session['favorites'] = favorites
    return redirect(url_for('index'))

@app.route('/remove_from_favorites/<int:car_id>', methods=['POST'])
def remove_from_favorites(car_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему, чтобы удалить автомобиль из избранного.')
        return redirect(url_for('login'))

    favorites = session.get('favorites', [])
    if car_id in favorites:
        favorites.remove(car_id)
        session['favorites'] = favorites
    return redirect(url_for('favorites'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'user')",
                       (name, email, password))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Регистрация прошла успешно! Теперь вы можете войти в систему.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            flash('Вы успешно вошли в систему.')
            return redirect(url_for('index'))
        else:
            flash('Неправильный email или пароль.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы успешно вышли из системы.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)