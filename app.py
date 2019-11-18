from flask import Flask, request, flash, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, redirect, url_for , jsonify, flash,Response
from flask_sqlalchemy import SQLAlchemy
from flask import request, session
import datetime
import json
import hashlib 
from sqlalchemy import func, create_engine
import time
from flask_mail import Mail, Message
import math



all_cities = {"Bengaluru":{"park":0.2,"lake":0.15,"historic":0.15,"holy":0.05,"amusement":0.2,"trek":0.1,"market":0.05,"waterfalls":0.1}, "Hyderabad":{"park":0.2,"historic":0.3,"holy":0.25,"lake":0.1,"amusement":0.2}, "Mumbai":{"historic":0.15,"holy":0.1,"beach":0.3,"park":0.1,"lake":0.1,"amusement":0.2,"trek":0.05},"Goa":{"beach":0.5,"holy":0.1,"historic":0.05,"party":0.2,"market":0.05,"park":0.025,"trek":0.025,"waterfalls":0.05}}

#Bengaluru = {"park":0.2,"lake":0.15,"historic":0.15,"holy":0.05,"amusement":0.2,"trek":0.1,"market":0.05,"waterfalls":0.1}
#Hyderabad = {"park":0.2,"historic":0.3,"holy":0.25,"lake":0.1,"amusement":0.2}
#Mumbai = {"historic":0.15,"holy":0.1,"beach":0.3,"park":0.1,"lake":0.1,"amusement":0.2,"trek":0.05}
#Goa = {"beach":0.5,"holy":0.1,"historic":0.05,"party":0.2,"market":0.05,"park":0.025,"trek":0.025,"waterfalls":0.05}

#gen = {"park":0.156,"lake":0.09,"historic":0.16,"holy":0.125,"amusement":0.15,"trek":0.043,"market":0.025,"waterfalls":0.037,"beach":0.164,"party":0.05}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tourism.sqlite3'
app.config['SECRET_KEY'] = "randomstring"
mail=Mail(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'tourismprp@gmail.com'
app.config['MAIL_PASSWORD'] = 'prpt1234'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
db = SQLAlchemy(app)

class User(db.Model):
   uid = db.Column(db.Integer, primary_key = True)
   username = db.Column(db.String(20), unique = True, nullable = False)
   password = db.Column(db.String(256), nullable = False) 
   phoneNumber = db.Column(db.Integer)
   email = db.Column(db.String(20))
   keywords = db.Column(db.String(100))

def __init__(self, uid, username, password, phoneNumber, email,keywords):
   self.uid = uid
   self.username = username
   self.password = password
   self.phoneNumber = phoneNumber
   self.email = email
   self.keywords = keywords


class PackageDetails(db.Model):
   pid = db.Column(db.Integer,primary_key=True)
   pname = db.Column(db.String(25))
   places = db.Column(db.String(200))
   days = db.Column(db.Integer)
   price = db.Column(db.Integer)
   seatsLeft=db.Column(db.Integer)
   imgs=db.Column(db.String(200))
   bookedSeats=db.Column(db.String(35))
   keywords = db.Column(db.String(150))
   def __init__(self, pid, pname, places, days, price,seatsLeft, bookedSeats,keywords):
      self.pid = pid
      self.pname = pname
      self.places = places
      self.days = days
      self.price = price
      self.seatsLeft=seatsLeft
      self.imgs=imgs
      self.bookedSeats=bookedSeats
      self.keywords=keywords

class seats(db.Model):
   snum=db.Column(db.Integer,primary_key=True)
   status=db.Column(db.Integer)
   def __init__(self,snum,status):
        self.snum=snum
        self.status=status

class ratingsAndReviews(db.Model):
  uid = db.Column(db.Integer,primary_key=True)
  packageId = db.Column(db.Integer,primary_key=True)
  review = db.Column(db.String(1000))
  rating = db.Column(db.Float)
  def __init__(self,uid,packageId,review,rating):
    self.uid = uid
    self.packageId = packageId
    self.review = review
    self.rating = rating

@app.route('/')
def show_all():
  return render_template('index.html')
  
@app.route("/bestoffers")
def bestoffers():
   toppicks= db.session.query(func.sum(ratingsAndReviews.rating), ratingsAndReviews.packageId ).group_by(ratingsAndReviews.packageId).all()
   print(toppicksss)
   sort1=sorted(toppicks, key = lambda x: float(x[0]), reverse = True)
   print(sort1)
   d={}
   packages=[]
   for x in range(0,3):
        packages.append(db.session.query(PackageDetails.places,PackageDetails.pid).filter(PackageDetails.pid==sort1[x][1]).first())
   print(packages)
   for i in range(len(packages)):
          d["package"+str(packages[i][1])]=(packages[i],packages[i][1])
   return render_template("displayPackages.html",result=d)
   
@app.route('/register', methods=['POST'])
def register():
    email=request.form['email']
    pwd=request.form['password']
    username=request.form['username']
    phonenumber=request.form['phonenumber']
    keyword=request.form['Interest']
    user=User(username=username, password=pwd, phoneNumber=phonenumber, email=email ,keywords=keyword)
    db.session.add(user)
    #ResultProxy = connection.execute(query)
    db.session.commit()
    app.logger.info(user.uid)
    session['logged_in'] = True
    return show_all()


@app.route('/suggest/<cityname>', methods=['POST','GET'])
def suggest(cityname):

    user=session['current_user']
    userkeywords = db.session.query(User.keywords).filter(User.uid==user).first()
    userkeywords=userkeywords[0].split(";")
    print(userkeywords)
    citykeywords = db.session.query(PackageDetails.keywords, PackageDetails.pid ).filter(PackageDetails.pname==cityname).all()
    print(citykeywords)
    scores=[[0,citykeywords[i][1]] for i in range(len(citykeywords))]
    matrix = [ [0] * len(citykeywords) for _ in range(len(userkeywords))]
    print(scores)
    for i in range(len(userkeywords)):
        for j in range(len(citykeywords)):
            if(citykeywords[j][0].find(userkeywords[i].lower())!=-1):
                matrix[i][j]=all_cities[cityname][userkeywords[i].lower()]
    print(matrix)
    print(scores)
    for j in range(len(citykeywords)):
        for i in range(len(userkeywords)):
            scores[j][0]+=round(matrix[i][j],2)
        scores[j][0]=round(scores[j][0],2)
    print(scores)
    tuples = []

    #for i in range(len(scores)):
    #    tuples.append((i,scores[i]))

    sort1=sorted(scores, key = lambda x: float(x[0]), reverse = True)
    print(sort1)
    d={}
    packages=[]
    for x in range(0,3):
        packages.append(db.session.query(PackageDetails.places,PackageDetails.pid).filter(PackageDetails.pid==sort1[x][1]).first())
    print(packages)
    
    for i in range(len(packages)):
          d["package"+str(packages[i][1])]=(packages[i],packages[i][1])
       
    return render_template("displayPackages.html",result=d)



@app.route('/login', methods=['POST'])
def login():
    if session.get('logged_in'):
        return render_template('index.html')
    email=request.form['email']
    pwd=request.form['password']
    p=User.query.filter_by(email=email).first()
    print("###################",p.uid)
    session['current_user']=p.uid
    
    if(p==None):
        flash("Invalid, please register")
        return render_template("login.html")
    else:
        print(p.password)
        if(pwd==p.password):
          session['logged_in'] = True
          results=suggest("Bengaluru")
          return render_template("index.html", data=results)
        else:
          flash("Wrong password")
          return render_template("login.html")

@app.route("/logout")
def logout():
    session['logged_in'] = False
    session['current_user']=0
    return show_all()
   
@app.route('/tourism/searchPackages/', methods=['POST'])
def searchPackages():
  if request.method == 'POST':
          d={}
          city=request.form['city']
          city=city.lower()
          city=city.capitalize()
          days=request.form['days']
          price=request.form['rangeInput']
          print("--------------",city,days,price)
          packages = db.session.query(PackageDetails.places,PackageDetails.pid).filter(PackageDetails.pname==city,PackageDetails.days==days).all()
          print(packages)
          
          

          l2=[]
         
          for i in range(len(packages)):
              d["package"+str(packages[i][1])]=(packages[i],packages[i][1])
          p=json.dumps(d)
          return render_template('displayPackages.html',result=d,cityname=city),200  # render p to some page


@app.route('/tourism/booked/',methods=['POST','GET'])
def booked():
    if not session.get('logged_in'):
        return render_template('login.html')
    packageId=request.form["id1"]
    l=packageId.split(";")
    session['packid']=int(l[1])
    print("^^^^^^^^^^^^^^^^^^",session['packid'])
    #l=packageId.encode('ascii','ignore').split(";")
    print("l", l)
    print(type(l[0]))
    p=PackageDetails.query.filter_by(pid=int(l[1])).first() 
    print(p)
    print(p.seatsLeft,type(l[0]))
    for i in range(2,len(l)):
        print(l[i])
        p.seatsLeft=p.seatsLeft-1
        if(p.bookedSeats=='0'):
            p.bookedSeats=str(l[i])
        else:
            p.bookedSeats=p.bookedSeats+';'+str(l[i])
    print(p.bookedSeats, p.seatsLeft)
    db.session.commit()
    return redirect(url_for('result'))
    
@app.route('/subscribe', methods=['POST', 'GET'])
def subscribe():
    email=request.form["mail"]
    msg = Message('Thanks For Subscribing', sender = 'tourismprp@gmail.com', recipients = [email])
    msg.body = "Dear User, Thank you for subscribing to our newsletter! We will keep you posted for any new packages!!"
    mail.send(msg)
    return "Sent"

@app.route('/pagelog', methods=['GET'])
def pagelog():
    return render_template('login.html')
    
@app.route('/result',methods=['POST','GET']) 
def result():
    return render_template('confirmed.html',uid=session['current_user'],pid=session['packid'])   
    
@app.route('/bus/<packId>',methods=['POST','GET'])
def bus(packId):
    p=PackageDetails.query.filter_by(pid=int(packId)).first()
    s=p.bookedSeats
    return render_template('bus.html',data=packId,booked=s)  
    
@app.route('/log' ,methods=['POST','GET'])
def log():
   return render_template('log.html') 



@app.route('/booknow/<packId>',methods=['POST','GET'])
def booknow(packId):
    if not session.get('logged_in'):
        return render_template('login.html')
    d={}
    p=PackageDetails.query.filter_by(pid=packId).first() 
    #print(p)
    d['packId']=packId
    d['price']=p.price
    d['seatsLeft']=p.seatsLeft
    d['places']=p.places
    d['days']=p.days
   
    packId=int(packId)
    print(type(packId))
    rev=ratingsAndReviews.query.filter_by(packageId=int(packId)).all()
    rat=[]
    reviews=[]
    for review in rev:
      reviews.append(review.review)
      rat.append(review.rating)
    if(len(rat)!=0):
      avgrat=math.ceil(sum(rat)/len(rat))
    else:
        avgrat=0
    #rating = 4  #get avg rating query and make it int
    #reviews = ["hello this is my bad review","hello this is my good review","1","3423434","fggdfgdfg","asdasdasdasdas","qweweqweqweq"] #get reviews for packid
    images = [str(i)+".jpeg" for i in list(p.imgs.split(";"))]
    return render_template("moredetails.html",data=d,img=images,len=len(images),rating=avgrat,reviews=reviews)

@app.route('/tourism/availability',methods=['POST','GET'])
def availableSeats():
    def eventstream():
             
                old=db.session.query(PackageDetails.seatsLeft).all()
            
                old=[val for val, in old]
                print(old)
                while True:
                    new=db.session.query(PackageDetails.seatsLeft).all()
                    new=[val1 for val1, in new]
                    if(new!=old):
                       for i in range(len(old)):
                            if(new[i]!=old[i]):
                                  old[i]=new[i]
                                  
                                  yield 'data:%s\n\n' % (str(new[i])+";"+str(i+1))
                                  
                    time.sleep(2)
    return Response(eventstream(),mimetype="text/event-stream")



@app.route('/writeReview',methods=['POST','GET'])
def writeReview():
    pid=session['packid']
    session['packid']=0
    review=request.form["Message"]
    print("$$$$$$$$$$$$$$$$$$$",pid,review)
    p=ratingsAndReviews(uid=session['current_user'],packageId=pid,rating=4,review=review) 
    db.session.add(p)
    db.session.commit()
    return show_all()

    
    
if __name__ == '__main__':
   db.create_all()
   app.run(debug = True)
