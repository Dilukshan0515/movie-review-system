from flask import Flask, render_template, request, redirect, session, url_for, flash  # Added flash here
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from db_config import db_config
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL config
app.config['MYSQL_HOST'] = db_config['host']
app.config['MYSQL_USER'] = db_config['user']
app.config['MYSQL_PASSWORD'] = db_config['password']
app.config['MYSQL_DB'] = db_config['database']

mysql = MySQL(app)

# ROUTES
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movies")
    movies = cur.fetchall()
    return render_template('index.html', movies=movies)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user[2], password_input):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[3]
            return redirect('/')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/movie/<int:id>')
def movie_detail(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movies WHERE id = %s", (id,))
    movie = cur.fetchone()
    
    # Check if movie is in user's watchlist
    watchlist_ids = []
    if 'user_id' in session:
        cur.execute("SELECT movie_id FROM watchlists WHERE user_id = %s", (session['user_id'],))
        watchlist_ids = [item[0] for item in cur.fetchall()]
    
    cur.execute("""
        SELECT r.id, r.rating, r.review_text, u.username, r.created_at, r.user_id 
        FROM reviews r 
        JOIN users u ON r.user_id = u.id 
        WHERE r.movie_id = %s
        ORDER BY r.created_at DESC
    """, (id,))
    reviews = cur.fetchall()
    
    review_dicts = []
    for review in reviews:
        review_dicts.append({
            'id': review[0],
            'rating': review[1],
            'review_text': review[2],
            'username': review[3],
            'created_at': review[4],
            'user_id': review[5]
        })
    
    return render_template('movie_detail.html', 
                         movie=movie, 
                         reviews=review_dicts,
                         current_user_id=session.get('user_id'),
                         watchlist_ids=watchlist_ids)

    
    # Convert reviews to dictionaries for easier template access
    review_dicts = []
    for review in reviews:
        review_dicts.append({
            'id': review[0],
            'rating': review[1],
            'review_text': review[2],
            'username': review[3],
            'created_at': review[4],
            'user_id': review[5]
        })
    
    return render_template('movie_detail.html', 
                         movie=movie, 
                         reviews=review_dicts,
                         current_user_id=session.get('user_id'))
    
    return render_template('movie_detail.html', 
                         movie=movie, 
                         reviews=reviews,
                         current_user_id=session.get('user_id'))
@app.route('/add_review/<int:movie_id>', methods=['POST'])
def add_review(movie_id):
    if 'user_id' not in session:
        flash('Please login to add reviews', 'danger')
        return redirect(url_for('login'))
    
    try:
        rating = int(request.form['rating'])
        review_text = request.form['review']
        user_id = session['user_id']
        
        # Validate rating
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5', 'danger')
            return redirect(url_for('movie_detail', id=movie_id))
            
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO reviews (user_id, movie_id, rating, review_text) 
            VALUES (%s, %s, %s, %s)
        """, (user_id, movie_id, rating, review_text))
        mysql.connection.commit()
        flash('Review added successfully!', 'success')
    except ValueError:
        flash('Invalid rating value', 'danger')
    except Exception as e:
        flash('Error adding review: ' + str(e), 'danger')
        
    return redirect(url_for('movie_detail', id=movie_id))

@app.route('/admin/add_movie', methods=['GET', 'POST'])
def add_movie():
    if not session.get('is_admin'):
        return redirect('/')
    if request.method == 'POST':
        name = request.form['name']
        image_url = request.form['image_url']
        duration = request.form['duration']
        year = request.form['year']
        genre = request.form['genre']
        description = request.form['description']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO movies (name, image_url, duration, year, genre, description) VALUES (%s, %s, %s, %s, %s, %s)",
                    (name, image_url, duration, year, genre, description))
        mysql.connection.commit()
        return redirect('/')
    return 
# Add these new routes to your existing app.py

@app.route('/my_reviews')
def my_reviews():
    if 'user_id' not in session:
        flash('Please login to view your reviews', 'danger')
        return redirect('/login')
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT r.id, r.rating, r.review_text, r.created_at, r.updated_at, 
               m.name as movie_name, m.id as movie_id 
        FROM reviews r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.user_id = %s
        ORDER BY r.created_at DESC
    """, (session['user_id'],))
    reviews = cur.fetchall()
    return render_template('my_reviews.html', reviews=reviews)

@app.route('/edit_review/<int:review_id>', methods=['GET', 'POST'])
def edit_review(review_id):
    if 'user_id' not in session:
        flash('Please login to edit reviews', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    
    try:
        # Get review with movie info in one query
        cur.execute("""
            SELECT r.id, r.rating, r.review_text, r.movie_id, m.name 
            FROM reviews r
            JOIN movies m ON r.movie_id = m.id
            WHERE r.id = %s AND r.user_id = %s
        """, (review_id, session['user_id']))
        review_data = cur.fetchone()

        if not review_data:
            flash('Review not found or no permission', 'danger')
            return redirect(url_for('my_reviews'))

        if request.method == 'POST':
            rating = int(request.form.get('rating', 0))
            review_text = request.form.get('review', '').strip()

            if not (1 <= rating <= 5):
                flash('Rating must be between 1 and 5', 'danger')
                return redirect(url_for('edit_review', review_id=review_id))

            if not review_text:
                flash('Review text cannot be empty', 'danger')
                return redirect(url_for('edit_review', review_id=review_id))

            cur.execute("""
                UPDATE reviews 
                SET rating = %s, 
                    review_text = %s, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (rating, review_text, review_id))
            mysql.connection.commit()
            
            flash('Review updated successfully!', 'success')
            return redirect(url_for('movie_detail', id=review_data[3]))

        # Prepare data for template
        review = {
            'id': review_data[0],
            'rating': review_data[1],
            'review_text': review_data[2],
            'movie_id': review_data[3]
        }
        movie_name = review_data[4]

        return render_template('edit_review.html', 
                            review=review,
                            movie_name=movie_name)

    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('my_reviews'))
@app.route('/delete_review/<int:review_id>')
def delete_review(review_id):
    if 'user_id' not in session:
        flash('Please login to delete reviews', 'danger')
        return redirect('/login')

    cur = mysql.connection.cursor()
    
    # First get movie_id before deleting
    cur.execute("SELECT movie_id FROM reviews WHERE id = %s AND user_id = %s", 
               (review_id, session['user_id']))
    result = cur.fetchone()
    
    if not result:
        flash('Review not found or you dont have permission', 'danger')
        return redirect('/')
    
    movie_id = result[0]
    
    # Delete review
    cur.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
    mysql.connection.commit()
    
    flash('Review deleted successfully!', 'success')
    return redirect(url_for('movie_detail', id=movie_id))




@app.route('/add_to_watchlist/<int:movie_id>', methods=['POST'])
def add_to_watchlist(movie_id):
    if 'user_id' not in session:
        flash('Login required to add to watchlist.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    
    # Check if already added
    cur.execute("SELECT * FROM watchlists WHERE user_id=%s AND movie_id=%s", (user_id, movie_id))
    existing = cur.fetchone()
    
    if existing:
        # Remove from watchlist
        cur.execute("DELETE FROM watchlists WHERE user_id=%s AND movie_id=%s", (user_id, movie_id))
        flash('Removed from watchlist!', 'success')
    else:
        # Add to watchlist
        cur.execute("INSERT INTO watchlists (user_id, movie_id) VALUES (%s, %s)", (user_id, movie_id))
        flash('Added to watchlist!', 'success')
    
    mysql.connection.commit()
    return redirect(url_for('movie_detail', id=movie_id))

@app.route('/my_watchlist')
def my_watchlist():
    if 'user_id' not in session:
        flash('Please login to view watchlist.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT m.* FROM movies m
        JOIN watchlists w ON w.movie_id = m.id
        WHERE w.user_id = %s
        ORDER BY w.created_at DESC
    """, (user_id,))
    watchlist_movies = cur.fetchall()
    return render_template('watchlist.html', movies=watchlist_movies)
    
'''
    <form method="post">
      Name: <input name="name"><br>
      Image URL: <input name="image_url"><br>
      Duration: <input name="duration"><br>
      Year: <input name="year"><br>
      Genre: <input name="genre"><br>
      Description: <textarea name="description"></textarea><br>
      <button type="submit">Add</button>
    </form>
    '''

if __name__ == '__main__':
    app.run(debug=True)
