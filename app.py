import pymysql as pymysql,phonenumbers 
from flask import Flask, render_template, request, redirect, url_for,session

import pickle

import nltk
import re
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

nltk.download("stopwords")
ps = PorterStemmer()
conn = pymysql.connect(host="localhost",user="root",password="major",db="project")
cursor = conn.cursor()

def load_pkl(fname):
    with open(fname, 'rb') as f:
        obj = pickle.load(f)
    return obj

model =load_pkl("xgb_fake_review_predictor.pkl")



def preprocess_review(review):
    p_review = re.sub('[^a-zA-Z]', ' ', review)
    p_review = p_review.lower().split()
    p_review = [ps.stem(word) for word in p_review if word not in stopwords.words('english')]
    p_review = ' '.join(p_review)
    return p_review




def register_user_to_db(username, password,email,number):
    result = cursor.execute("select username,number,email from user where username='"+username+"'or number='"+number+"'or email='"+email+"'")
    conn.commit()
    if result>0:
        return False
    else:
        cursor.execute("insert into user(username,password,number,email)values('" + username + "','"+ password + "','" + number + "','" + email + "')")
    return True




def check_user(username, password):
    result=cursor.execute("select username,password from user where username='"+username+"' and password='"+password+"'")
    if result:
        return True
    else:
        return False




app = Flask(__name__)
app.secret_key = "r@nd0mSk_1"



@app.route("/",methods=["POST","GET"])
def index():
    return render_template('login.html') 




@app.route('/register', methods=["GET","POST"])
def register():
    wrong=False
    message=""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email= request.form['email']
        number=request.form['number']
       # ph=phonenumbers.parse("+447986123456", number)
        mailc= r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if (re.fullmatch(mailc,email))==False:
            return render_template("register.html",wrong=True,message="Mail Invalid")
        if register_user_to_db(username, password,email,number):
            return render_template('login.html',Right=True,message="Registration Success")
        return render_template("register.html",wrong=True,message="User Already Exists ")
    return render_template('register.html')  


           
@app.route('/home', methods = ['GET','POST'])
def home():
    wrong=False
    try:
        if session['username'] is None:
            return render_template("login.html",wrong=True,message="Please Login")
        fake_flag = False
        non_fake_flag = False
        danger=False
        message = ""
        if request.method == 'POST':
            dic = request.form.to_dict()
            review = dic['review']
            if len(review) == 0:
                danger = True
                message = "PLEASE ENTER SOME TEXT"
                return render_template("home.html",danger=True,message=message)
            review = preprocess_review(review)
            if len(review) == 0:
                danger = True
                message = "PLEASE ENTER SOME VALID TEXT"
                return render_template("home.html",danger=True,message=message)
            prediction = model.predict([review])
            probability = model.predict_proba([review])
            if prediction[0] == 1:
                fake_flag = True
                message = f"This Review is predicted as FAKE Review with {round(max(probability[0])*100, 2)}% accuracy"
                return render_template("home.html",fake_flag=True,message=message)
            else:
                non_fake_flag = True
                message = f"This Review is predicted as REAL Review with {round(max(probability[0])*100, 2)}% accuracy"
                return render_template("home.html",non_fake_flag=True,message=message)
        return render_template("login.html",wrong=True,message="please login")
    except Exception as e:
        return render_template("login.html",wrong=True,message="please login")
    return render_template("login.html",wrong=True,message="please login")
   
    
    
@app.route('/login', methods=['GET','POST'])
def login():
    wrong=False
    message=""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        #print(check_user(username, password))
        if check_user(username, password):
            session['username']=username
            return render_template("home.html")

        return render_template("login.html",wrong=True,message="Invalid username or password")
    else:
        return redirect(url_for('index'))


@app.route('/logout', methods=['GET','POST'])
def logout():
    session['username']=None
    return render_template("login.html",message="")

if __name__ == '__main__':
    app.run(debug = True)