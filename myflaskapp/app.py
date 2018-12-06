from flask import Flask, render_template, flash, redirect, url_for, session,request, logging
from data import Articles
from flaskext.mysql import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
from functools import wraps
import pymysql


app = Flask(__name__)


# Config MySQL
mysql = MySQL()
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'myflaskapp'
app.config['MYSQL_DATABASE_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql.init_app(app)


#Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')







@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        conn = mysql.connect()
        cur =conn.cursor(pymysql.cursors.DictCursor)

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        conn.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        conn = mysql.connect()
        cur =conn.cursor(pymysql.cursors.DictCursor)

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return render_template('home.html')
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# Articles
@app.route('/articles')
@is_logged_in
def articles():
    # Create cursor
    conn = mysql.connect()
    cur =conn.cursor(pymysql.cursors.DictCursor)

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


# Categories
@app.route('/categories')
@is_logged_in
def categories():
    # Create cursor
    conn = mysql.connect()
    cur =conn.cursor(pymysql.cursors.DictCursor)

    # Get articles
    result = cur.execute("SELECT * FROM categories")

    categories = cur.fetchall()

    if result > 0:
        return render_template('categories.html', categories=categories)
    else:
        msg = 'No Categories Found'
        return render_template('categories.html', msg=msg)
    # Close connection
    cur.close()
    

#Single Article
@app.route('/article/<string:id>/')
@is_logged_in
def article(id):
    # Create cursor
    conn = mysql.connect()
    cur =conn.cursor(pymysql.cursors.DictCursor)

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)




#Single Categorie
@app.route('/categorie/<string:id>/')
@is_logged_in
def categorie(id):
    # Create cursor
    conn = mysql.connect()
    cur =conn.cursor(pymysql.cursors.DictCursor)

    # Get article
    result = cur.execute("SELECT * FROM categories WHERE id = %s", [id])

    categorie = cur.fetchone()

    return render_template('categorie.html', categorie=categorie)


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.DataRequired(),validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')
    


# Dashboard of Categories
@app.route('/dashboard_categories')
@is_logged_in
def dashboard_categories():
    # Create cursor
    conn = mysql.connect()
    cur =conn.cursor(pymysql.cursors.DictCursor)

    # Get articles
    # Show articles only from the user logged in 
    result = cur.execute("SELECT * FROM categories")

    categories = cur.fetchall()

    if result > 0:
        return render_template('dashboard_categories.html', categories=categories)
    else:
        msg = 'No Categories Found'
        return render_template('dashboard_categories.html', msg=msg)
    # Close connection
    cur.close()

# Dashboard of Arcticles
@app.route('/dashboard_articles')
@is_logged_in
def dashboard_articles():
    # Create cursor
    conn = mysql.connect()
    cur =conn.cursor(pymysql.cursors.DictCursor)

    # Get articles
    # Show articles only from the user logged in 
    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['username']])

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard_articles.html', articles=articles)
    else:
        msg = 'No rticles Found'
        return render_template('dashboard_articles.html', msg=msg)
    # Close connection
    cur.close()

    



# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Categorie Form Class
class CategorieForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=200)])
    description = TextAreaField('Description', [validators.Length(min=30)])
    

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        conn = mysql.connect()
        cur =conn.cursor(pymysql.cursors.DictCursor)

        # Execute
        cur.execute("INSERT INTO articles( title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        conn.commit()

        #Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard_articles'))

    return render_template('add_article.html', form=form)



# Add Categorie
@app.route('/add_categorie', methods=['GET', 'POST'])
@is_logged_in
def add_categorie():
    form = CategorieForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        description = form.description.data

        # Create Cursor
        conn = mysql.connect()
        cur =conn.cursor(pymysql.cursors.DictCursor)


        # Execute
        cur.execute("INSERT INTO categories(name, description) VALUES(%s, %s)",(name, description))

        # Commit to DB
        conn.commit()

        #Close connection
        cur.close()

        flash('Categorie Created', 'success')

        return redirect(url_for('dashboard_categories'))

    return render_template('add_categorie.html', form=form)



# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    conn = mysql.connect()
    cur =conn.cursor(pymysql.cursors.DictCursor)

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        conn = mysql.connect()
        cur =conn.cursor(pymysql.cursors.DictCursor)
        
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        conn.commit()
        
        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard_articles'))

    return render_template('edit_article.html', form=form)



# Edit Categorie
@app.route('/edit_categorie/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_categorie(id):
    # Create cursor
    conn = mysql.connect()
    cur =conn.cursor(pymysql.cursors.DictCursor)

    # Get article by id
    result = cur.execute("SELECT * FROM categories WHERE id = %s", [id])

    categorie = cur.fetchone()
    cur.close()
    # Get form
    form = CategorieForm(request.form)

    # Populate article form fields
    form.name.data = categorie['name']
    form.description.data = categorie['description']

    if request.method == 'POST' and form.validate():
        name = request.form['name']
        description = request.form['description']

        # Create Cursor
        conn = mysql.connect()
        cur =conn.cursor(pymysql.cursors.DictCursor)
        
        app.logger.info(name)
        # Execute
        cur.execute ("UPDATE categories SET name=%s, description=%s WHERE id=%s",(name, description, id))
        # Commit to DB
        conn.commit()
        
        #Close connection
        cur.close()

        flash('Categorie Updated', 'success')

        return redirect(url_for('dashboard_categories'))

    return render_template('edit_categorie.html', form=form)


# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    conn = mysql.connect()
    cur =conn.cursor(pymysql.cursors.DictCursor)

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    conn.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard_articles'))

# Delete Categorie
@app.route('/delete_categorie/<string:id>', methods=['POST'])
@is_logged_in
def delete_categorie(id):
    # Create cursor
    conn = mysql.connect()
    cur =conn.cursor(pymysql.cursors.DictCursor)

    # Execute
    cur.execute("DELETE FROM categories WHERE id = %s", [id])

    # Commit to DB
    conn.commit()

    #Close connection
    cur.close()

    flash('Categorie Deleted', 'success')

    return redirect(url_for('dashboard_categories'))

@app.route('/perfil')
@is_logged_in
def perfil():
    # Create cursor
    conn = mysql.connect()
    cur =conn.cursor(pymysql.cursors.DictCursor)
    username = session['username']

    # Get article
    result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

    user = cur.fetchone()
    return render_template('perfil.html', user=user)



if __name__ == '__main__':    
    app.secret_key='secret123'
    app.run(debug=True)
    
    
