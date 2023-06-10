from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import current_user, LoginManager
import mysql.connector
import random
import sys

app = Flask(__name__)
app.secret_key = '12345'


db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Calleja_0221",
    database="quested"
)

cursor = db.cursor()

#user fetcher
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    cursor.execute("SELECT * FROM login_database WHERE idlogin_database=%s", (user_id,))
    return cursor.fetchone()
#user fetcher

#login
@app.route('/')
def root():
    audio_url = url_for('static', filename='audio/arcade.mp3')
    return render_template('login.html', audio_url=audio_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM login_database WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user is not None:
            session['username'] = user[1]
            return redirect('/home')
        else:
            return redirect('/login')
    audio_url = url_for('static', filename='audio/arcade.mp3')
    return render_template('login1.html',audio_url=audio_url )
#login 

#register
@app.route('/register1')
def register1():
    return render_template('register.html')   

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        cursor.execute("SELECT * FROM login_database WHERE username=%s", (username,))
        if cursor.fetchone() is not None:
            return "Username already exists!"

        cursor.execute("INSERT INTO login_database (username, password, email) VALUES (%s, %s, %s)", (username, password, email))
        db.commit()
        return redirect('/login')
    audio_url = url_for('static', filename='audio/arcade.mp3')
    return render_template('register.html',audio_url=audio_url)
#register

#homepage      
@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        cursor.execute("SELECT * FROM login_database WHERE username=%s", (username,))
        user_data = cursor.fetchone()
        if user_data:
            username = user_data[1]
            email = user_data[2]
            audio_url = url_for('static', filename='audio/arcade.mp3')
            return render_template('homepage.html', username=username, email=email,audio_url=audio_url)
        else:
            return "User not found in the database."
    else:
        audio_url = url_for('static', filename='audio/arcade.mp3')
        return redirect(url_for('login',audio_url=audio_url))
 #homepage 
      
#play pagge
@app.route('/playpage')
def play():
    audio_url = url_for('static', filename='audio/arcade.mp3')
    return render_template('play.html',audio_url=audio_url) 
#play pagge

#leaderboards page
@app.route('/leaderboards/<category>')
def leaderboard(category):
    audio_url = url_for('static', filename='audio/arcade.mp3')

    if category == 'english':
        cursor.execute("SELECT * FROM eleaderboards_database ORDER BY score DESC")
    elif category == 'science':
        cursor.execute("SELECT * FROM sleaderboards_database  ORDER BY score DESC")
    elif category == 'math':
        cursor.execute("SELECT * FROM mleaderboards_database  ORDER BY score DESC")
    else:
        return "Invalid category"

    scores = cursor.fetchall()
    return render_template('leaderboards.html', scores=scores, category=category.capitalize(),audio_url=audio_url)
#leaderboards page

#Single player page
@app.route('/single')
def single():
    audio_url = url_for('static', filename='audio/arcade.mp3')
    return render_template('singleplayer.html',audio_url=audio_url)
#Single player page

#game
@app.route('/game', methods=['GET', 'POST'])
def game():
    if request.method == 'POST':
        counter = int(request.form['counter'])
        user_answer = request.form['answers']
        score = int(request.form['score'])
        category = session.get('category')

        if not category:
            return redirect(url_for('play'))

        table_name = f"{category[0]}questions_database"
        cursor.execute("SELECT * FROM {} WHERE TRIM(LOWER(answers)) = TRIM(LOWER(%s))".format(table_name), (user_answer,),)
        result = cursor.fetchone()

        if result:
            score += 1

        counter += 1
        session['counter'] = counter
        session['score'] = score

        if counter < 10:
            questions = get_shuffled_questions(table_name)
            if not questions:
                return "No more questions available."
            question = questions[counter - 1]
            question_text = question[1]


            return render_template('game.html', question=question_text, counter=counter, score=score, category=category,)

        session.pop('counter', None)
        session.pop('score', None)
        session.pop('category', None)
       
        insert_score(category, score)

        return redirect(url_for('result', score=score))

    else:
        category = request.args.get('category')

        if not category:
            return redirect(url_for('play'))

        session['category'] = category
        counter = 1
        score = 0
        table_name = f"{category[0]}questions_database"
        questions = get_shuffled_questions(table_name)

        if questions:
            question = questions[counter - 1]
            question_text = question[1]
            
            return render_template('game.html', question=question_text, counter=counter, score=score, category=category)
        else:
            return "No questions found in the database."
#game

def get_shuffled_questions(table_name):
    cursor.execute("SELECT * FROM {}".format(table_name))
    questions = cursor.fetchall()
    random.shuffle(questions)
    return questions
        
#score inserter
def insert_score(category, score):
    if 'username' in session:
        username = session['username']

        if category == 'english':
            leaderboard_table = 'eleaderboards_database'
        elif category == 'science':
            leaderboard_table = 'sleaderboards_database'
        elif category == 'math':
            leaderboard_table = 'mleaderboards_database'
        else:
            return "Invalid category"

        try:
            cursor.execute(f"INSERT INTO {leaderboard_table} (username, score) VALUES (%s, %s)", (username, score))
            db.commit()
            return True
        except mysql.connector.Error as error:
            return str(error)

    return "User not logged in"
#score inserter

#result
@app.route('/result')
def result():
    score = request.args.get('score')
    audio_url = url_for('static', filename='audio/arcade.mp3')
    return render_template('result.html', score=score,audio_url=audio_url)
#result

#editorial
@app.route('/user_game', methods=['GET', 'POST'])
def user_game():
    if request.method == 'POST':
        username = request.form['username']
        cursor.execute("SELECT * FROM user_questions WHERE username=%s", (username,))
        questions = cursor.fetchall()

        if questions:
            game_questions = [(question[1], question[2]) for question in questions]

            session['game_questions'] = game_questions
            session['counter'] = 1
            session['score'] = 0

            return redirect(url_for('play_user_game'))
        else:
            return "No questions found for the selected username."
    audio_url = url_for('static', filename='audio/arcade.mp3')
    return render_template('user_game.html',audio_url=audio_url)

#editorial
@app.route('/play_user_game', methods=['GET', 'POST'])
def play_user_game():
    if 'game_questions' in session:
        game_questions = session['game_questions']
        counter = session.get('counter', 1)
        score = session.get('score', 0)

        if request.method == 'POST':
            counter = int(request.form['counter'])
            user_answer = request.form['answers']
            score = int(request.form['score'])
            game_questions = session.get('game_questions')

            if game_questions:
                if counter <= len(game_questions):
                    correct_answer = game_questions[counter - 1][1]

                    if user_answer.strip().lower() == correct_answer.strip().lower():
                        score += 1

                    counter += 1
                    session['counter'] = counter
                    session['score'] = score

                    if counter <= len(game_questions):
                        return redirect(url_for('play_user_game'))

                    session.pop('counter', None)
                    session.pop('score', None)
                    session.pop('game_questions', None)

                    final_score = session['score']
                    print("Final Score:", final_score)
                    return redirect(url_for('game_completed'))

                    # Here you can perform any actions or render any templates for the game completion

        current_question = game_questions[counter - 1][0]
        return render_template('play_user_game.html', question=current_question, counter=counter, score=score)

    return redirect(url_for('user_game'))

@app.route('/editorial', methods=['GET', 'POST'])
def editorial():
    if request.method == 'POST':
        option = request.form['option']

        if option == 'create':
            return redirect(url_for('create_questionnaire'))
        elif option == 'play':
            return redirect(url_for('select_questionnaire'))

    return render_template('editorial.html')

@app.route('/create', methods=['GET', 'POST'])
def create_questionnaire():
    if request.method == 'POST':
        username = session.get('username')  
        question = request.form['question']
        answer = request.form['answer']

        cursor.execute("INSERT INTO editorial_database (username, question, answer) VALUES (%s, %s, %s)", (username, question, answer))
        db.commit()

        return redirect(url_for('create_questionnaire'))

    return render_template('create_questionnaire.html')

@app.route('/select', methods=['GET', 'POST'])
def select_questionnaire():
    if request.method == 'POST':
        username = request.form['username']
        cursor.execute("SELECT * FROM editorial_database WHERE username=%s", (username,))
        questions = cursor.fetchall()

        if questions:
            game_questions = [(question[1], question[2]) for question in questions]

            session['game_questions'] = game_questions
            session['counter'] = 1
            session['score'] = 0
            return redirect(url_for('play_user_game'))
        else:
            return "No questions found for the selected username."

    return render_template('select_questionnaire.html')
#editorial

#settings
@app.route('/settings')
def settings():
    audio_url = url_for('static', filename='audio/arcade.mp3')
    return render_template('settings.html',audio_url=audio_url)
#settings

#exit app
@app.route('/exit')
def exit_app():
    sys.exit(0) 
#exit app

if __name__ == '__main__':
    app.run()