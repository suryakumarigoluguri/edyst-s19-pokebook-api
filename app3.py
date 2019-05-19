from flask import Flask,request,json,render_template,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_simple import (
    JWTManager, jwt_required, create_jwt, get_jwt_identity
)
import os
import jwt
import datetime
from sqlalchemy import DateTime,Column

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app3.sqlite')
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this!
jwt = JWTManager(app)

db = SQLAlchemy(app)
ma = Marshmallow(app)

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

#user schema
class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String,unique=True)
    email = db.Column(db.String,unique=True)
    password = db.Column(db.String)
    bio = db.Column(db.String,default="null")
    image = db.Column(db.String,default="null")
    following = db.Column(db.Boolean,default=False)

    #followed = db.relationship(
        #'User', secondary=followers,
        #primaryjoin=(followers.c.follower_id == id),
        #secondaryjoin=(followers.c.followed_id == id),
        #backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __init__(self,username,email,password):
        self.username=username
        self.email=email
        self.password=password

class UserSchema(ma.Schema):
    class Meta:
        fields=('id','username','email','password','bio','image','following')

user_schema=UserSchema()
users_schema=UserSchema(many=True)

#followers schema
class Followers(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    follower_id=db.Column(db.Integer)
    followed_id=db.Column(db.Integer)

    def __init__(self,follower_id,followed_id):
        self.follower_id=follower_id
        self.followed_id=followed_id

class FollowersSchema(ma.Schema):
    class Meta:
        fields=('id','follower_id','followed_id')

flr_schema=FollowersSchema()
flrs_schema=FollowersSchema(many=True)

#pokemon schema
class Pokemon(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String, unique=True)
    sprite = db.Column(db.String, unique=True)
    description = db.Column(db.String)
    #createdAt = db.Column(db.String,default="null")
    #updatedAt = db.Column(db.String,default="null")
    createdAt=Column(DateTime,default=datetime.datetime.utcnow)
    updatedAt=Column(DateTime,default=datetime.datetime.utcnow)
    favourited = db.Column(db.Boolean,default=False)
    favouritesCount = db.Column(db.Integer,default=0)
    user_id=db.Column(db.Integer)
    #username = db.Column(db.String)
    #bio = db.Column(db.String)
    #image = db.Column(db.String)
    #following = db.Column(db.Boolean)

    def __init__(self, name, sprite, description,user_id):
        self.name = name
        self.sprite = sprite
        self.description = description
        self.user_id=user_id
        #self.username = username   #add user id as foreign
        #self.bio = bio
        #self.image = image
        #self.following = following

class PokemonSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('id','name', 'sprite', 'description','createdAt','updatedAt','favourited','favouritesCount','user_id')
    
pokemon_schema=PokemonSchema()
pokemons_schema=PokemonSchema(many=True)

#tag list schema
class Tag(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    flying=db.Column(db.Boolean,default=False)
    fire=db.Column(db.Boolean,default=False)
    water=db.Column(db.Boolean,default=False)
    grass=db.Column(db.Boolean,default=False)

    def __init__(self,id):
        self.id=id

class TagSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('id','flying','fire','water','grass')
    
tag_schema=TagSchema()
tags_schema=TagSchema(many=True)

#comment schema
class Comments(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    body=db.Column(db.String)
    pk_name=db.Column(db.String)
    user_id=db.Column(db.Integer)
    createdAt=Column(DateTime,default=datetime.datetime.utcnow)
    updatedAt=Column(DateTime,default=datetime.datetime.utcnow)
    
    def __init__(self,body,pk_name,user_id):
        self.body=body
        self.pk_name=pk_name
        self.user_id=user_id


class CommentsSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('id','body','pk_name','user_id')
    
comment_schema=CommentsSchema()
comments_schema=CommentsSchema(many=True)

#user registration
@app.route("/api/users", methods=["POST"])
def add_user():
    u=request.get_json()
    if len(u["user"]["username"])>50 or len(u["user"]["username"])==0:
        return render_template("422.html"), 422
    if len(u["user"]["email"])>50 or len(u["user"]["email"])==0:
        return render_template("422.html"), 422
    if len(u["user"]["password"]) not in range(8,15):
        return render_template("422.html"), 422
    username = u["user"]["username"]
    email = u["user"]["email"]
    password = u["user"]["password"]
    new_user = User(username, email, password)
    db.session.add(new_user)
    db.session.commit()
    urdata = User.query.filter(User.username==username).first()
    ur = {"user":{"id":urdata.id,"username":urdata.username,"email":urdata.email,"password":urdata.password,"bio":urdata.bio,"image":urdata.image,"following":urdata.following}}
    return json.dumps(ur)

#user login
@app.route("/api/users/login", methods=["POST"])
def user_login():
    u=request.get_json()
    email = u["user"]["email"]
    password = u["user"]["password"]
    if not email:
        return jsonify({"msg": "Missing email parameter"}), 400
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400
    urdata = User.query.filter(User.email==email).first()
    if urdata is None:
        return jsonify({"msg": "Invalid email"}), 401
    if (urdata.password!=password):
        return jsonify({"msg": "Invalid password"}), 401

    # Identity can be any data that is json serializable
    ret = {'jwt': create_jwt(identity=email)}
    return jsonify(ret), 200

#getting the current user details
@app.route("/api/user", methods=["GET"])
@jwt_required
def get_user():
    email=get_jwt_identity()
    #return(email)
    urdata=User.query.filter(User.email==email).first()
    ur={"user":{"id":urdata.id,"email":urdata.email,"username":urdata.username,"bio":urdata.bio,"image":urdata.image,"following":urdata.following}}
    return json.dumps(ur)

#updating the user details
@app.route("/api/user", methods=["PATCH"])
@jwt_required
def update_user():
    u=request.get_json()
    email=get_jwt_identity()
    if u["user"]["email"]!=email:
        return render_template("403.html"), 403
    urdata=User.query.filter(User.email==email).first()
    if "username" in u["user"]:
        urdata.username=u["user"]["username"]
    if "password" in u["user"]:
        urdata.password=u["user"]["password"]
    if "bio" in u["user"]:
        urdata.bio=u["user"]["bio"]
    if "image" in u["user"]:
        urdata.image=u["user"]["image"]        
    db.session.commit()
    urdata=User.query.filter(User.email==email).first()
    ur={"user":{"id":urdata.id,"email":urdata.email,"username":urdata.username,"password":urdata.password,"bio":urdata.bio,"image":urdata.image,"following":urdata.following}}
    return json.dumps(ur)

#to get the profile of any user by using the username
@app.route("/api/profiles/<username>", methods=["GET"])
@jwt_required
def user_profile(username):
    prdata=User.query.filter(User.username==username).first()
    if prdata is None:
        return render_template("404.html"), 404
    email=get_jwt_identity()
    curdata=User.query.filter(User.email==email).first()  
    all=Followers.query.filter(Followers.follower_id==curdata.id)
    a=flrs_schema.dump(all)
    flr=False
    if all is None:
        flr=False
    else:
        for i in a.data:
            if i["followed_id"]==prdata.id:
                flr=True
                break
            else:
                flr=False
    pr={"user":{"id":prdata.id,"email":prdata.email,"username":prdata.username,"bio":prdata.bio,"image":prdata.image,"following":flr}}
    return json.dumps(pr)


#to follow any user
@app.route("/api/profiles/<username>/follow", methods=["POST"])
@jwt_required
def follow_user(username):
    email=get_jwt_identity()
    flrdata=User.query.filter(User.email==email).first()  #get follower details using email
    flddata=User.query.filter(User.username==username).first()   #get followed details using username
    #to check whether the follower is previously following or not
    all=Followers.query.filter(Followers.follower_id==flrdata.id)
    a=flrs_schema.dump(all)
    for i in a.data:
        if flddata.id==i["followed_id"]:
            pr=user_profile(flddata.username)
            return(pr)

    follower_id=flrdata.id
    followed_id=flddata.id
    new_flr=Followers(follower_id,followed_id)
    db.session.add(new_flr)
    db.session.commit()
    pr=user_profile(flddata.username)
    return(pr)

#to unfollow the user
@app.route("/api/profiles/<username>/follow",methods=["DELETE"])
@jwt_required
def unfollow_user(username):
    email=get_jwt_identity()
    flrdata=User.query.filter(User.email==email).first()  #get follower details using email
    flddata=User.query.filter(User.username==username).first()   #get followed details using username
    all=Followers.query.filter(Followers.follower_id==flrdata.id)
    a=flrs_schema.dump(all)
    for i in a.data:
        if flddata.id==i["followed_id"]:
            id=i["id"]
            fdata = Followers.query.get(id)
            db.session.delete(fdata)
            db.session.commit()
    pr=user_profile(flddata.username)
    return(pr)

#to fill tags table
def update_tag(tag,id):
    t=Tag.query.filter(Tag.id==id).first()
    if "flying" in tag:
        t.flying=True
    if "fire" in tag:
        t.fire=True   
    if "water" in tag:
        t.water=True
    if "grass" in tag:
        t.grass=True
    db.session.commit()
    t=Tag.query.filter(Tag.id==id).first()
    data=[]
    if t.flying==True:
        data.append("flying")
    if t.fire==True:
        data.append("fire")
    if t.water==True:
        data.append("water")
    if t.grass==True:
        data.append("grass")
    return(data)

#adding(or)creating pokemon
@app.route("/api/pokemon", methods=["POST"])
@jwt_required
def add_pokemon():
    pk=request.get_json()
    email=get_jwt_identity()
    urdata=User.query.filter(User.email==email).first()
    if urdata is None:
        return render_template("404.html"), 404    
    if len(pk["pokemon"]["name"])>50:
        return("Name value has exceeded the limit...")
    name = pk["pokemon"]["name"]
    if len(pk["pokemon"]["sprite"])>300:
        return("sprite value has exeeded the limit...")
    sprite = pk["pokemon"]["sprite"]
    description=pk["pokemon"]["sprite"]
    new_pk = Pokemon(name, sprite, description,urdata.id)
    db.session.add(new_pk)
    db.session.commit()
    pkdata = Pokemon.query.filter(Pokemon.name==name).first()
    id=pkdata.id
    new_tag=Tag(id)
    db.session.add(new_tag)
    db.session.commit()
    if "tagList" in pk["pokemon"]:
        tag=update_tag(pk["pokemon"]["tagList"],id)
    else:
        tag=[]
    pk = {"pokemon":{"id":pkdata.id,"name":pkdata.name,"tagList":tag,"sprite":pkdata.sprite,"descripion":pkdata.description,"userid":pkdata.user_id}}
    return json.dumps(pk)

#to update pokemon using name
@app.route("/api/pokemon/<name>", methods=["PATCH"])
@jwt_required
def update_pokemon(name):
    pkdata = Pokemon.query.filter(Pokemon.name==name).first()
    if (pkdata is None):
        return render_template("404.html"), 404
    else:
        email=get_jwt_identity()
        urdata=User.query.filter(User.email==email).first()
        if urdata is None:
            return render_template("404.html"), 404
        if urdata.id!=pkdata.user_id:
            return render_template("403.html"), 403
        pk=request.get_json()
        if "sprite" in pk["pokemon"]:
            pkdata.sprite = pk["pokemon"]["sprite"]
        if "description" in pk["pokemon"]:
            pkdata.description = pk["pokemon"]["description"]
        db.session.commit()
        pkdata = Pokemon.query.get(pkdata.id)
        if "tagList" in pk["pokemon"]:
            tag=pk["pokemon"]["tagList"]
        else:
            tag=[]
        tag=update_tag(tag,pkdata.id)
        pk = {"pokemon":{"id":pkdata.id,"name":pkdata.name,"tagList":tag,"sprite":pkdata.sprite,"descripion":pkdata.description,"user_id":pkdata.user_id}}
        return json.dumps(pk)

#to delete pokemon using name
@app.route("/api/pokemon/<name>", methods=["DELETE"])
@jwt_required
def delete_pokemon(name):
    pkdata = Pokemon.query.filter(Pokemon.name==name).first()
    if (pkdata==None):
        return render_template("404.html"), 404
    else:
        email=get_jwt_identity()
        urdata=User.query.filter(User.email==email).first()
        if urdata is None:
            return render_template("404.html"), 404
        if urdata.id!=pkdata.user_id:
            return render_template("403.html"), 403
        tag=update_tag([],pkdata.id)
        pk = {"pokemon":{"id":pkdata.id,"name":pkdata.name,"tagList":tag,"sprite":pkdata.sprite,"descripion":pkdata.description,"user_id":pkdata.user_id}}
        db.session.delete(pkdata)
        db.session.commit()
        return json.dumps(pk)

#to get the trainer details
def trainer_profile(cuser_id,pk_name):
    pk=Pokemon.query.filter(Pokemon.name==pk_name).first()
    prdata=User.query.filter(User.user_id==pk.user_id).first()
    if prdata is None:
        return render_template("404.html"), 404
    curdata=User.query.get(cuser_id)  
    all=Followers.query.filter(Followers.follower_id==curdata.id)
    a=flrs_schema.dump(all)
    flr=False
    if all is None:
        flr=False
    else:
        for i in a.data:
            if i["followed_id"]==prdata.id:
                flr=True
                break
            else:
                flr=False
    tr={"trainer":{"username":prdata.username,"bio":prdata.bio,"image":prdata.image,"following":flr}}
    return(tr)

#to get comment from a comment table using id
def get_comment(id):
    cmdata=Comments.query.get(id)
    #curdata=User.query.get(cmdata.user_id)  
    tr=trainer_profile(cmdata.user_id,cmdata.pk_name)
    cm={"comment":{"id":cmdata.id,"createdAt":cmdata.createdAt,"updatedAt":cmdata.updatedAt,"body":cmdata.boby,"trainer":tr["trainer"]}}
    return(cm)

#to comment for a particular pokemon using name
@app.route("/api/pokemon/<name>/comments", methods=["POST"])
@jwt_required
def comment(name):
    pkdata = Pokemon.query.filter(Pokemon.name==name).first()
    if (pkdata==None):
        return render_template("404.html"), 404
    else:
        email=get_jwt_identity()
        urdata=User.query.filter(User.email==email).first()
        if urdata is None:
            return render_template("404.html"), 404
        cd=request.get_json()
        body=cd["comment"]["body"]
        pk_name=pkdata.name 
        user_id=urdata.id       
        new_cm=Comments(body,pk_name,user_id)
        db.session.add(new_cm)
        db.session.commit()
        cmdata = Comments.query.filter(Comments.body==body).first()
        cm = get_comment(cmdata.id)
        return json.dumps(cm)


#to get the comments on a particular pokemon using name
@app.route("/api/pokemon/<name>/comments", methods=["GET"])
def get_comment(name):
    all=Comments.query.filter(Comments.pk_name==name).filter()
    if all is None:
        return render_template("404.html"), 404
    a=comments_schema.dump(all)
    cm=[]
    for i in a.data:
        cmt=get_comment(i["id"])
        cm.append(cmt["comment"])
    return json.dumps(cm)

if __name__ == '__main__':
    db.create_all()
    app.run(host='localhost', port=8006, debug=True)