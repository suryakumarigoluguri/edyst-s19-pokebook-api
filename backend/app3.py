from flask import Flask,request,json,render_template,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_simple import (
    JWTManager, jwt_required, create_jwt, get_jwt_identity
)
import os
import jwt
import datetime
from sqlalchemy import DateTime,Column,desc

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
    createdAt=Column(DateTime,default=datetime.datetime.utcnow)
    updatedAt=Column(DateTime,default=datetime.datetime.utcnow)
    favourited = db.Column(db.Boolean,default=False)
    favouritesCount = db.Column(db.Integer,default=0)
    user_id=db.Column(db.Integer)
    
    def __init__(self, name, sprite, description,user_id):
        self.name = name
        self.sprite = sprite
        self.description = description
        self.user_id=user_id
        
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

#favourite schema
class Favourites(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    pk_name=db.Column(db.String)
    user_id=db.Column(db.Integer)
    
    def __init__(self,pk_name,user_id):
        self.pk_name=pk_name
        self.user_id=user_id


class FavouritesSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('id','pk_name','user_id')
    
fav_schema=FavouritesSchema()
favs_schema=FavouritesSchema(many=True)

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

#getting the current user details
@app.route("/api/user", methods=["GET"])
@jwt_required
def get_user():
    email=get_jwt_identity()
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

#to get the list of pokemons using tags
def tag_pk(tag):
    if tag=="flying":
        tags=Tag.query.filter(Tag.flying==True).order_by(desc(Tag.id)).all()
    elif tag=="fire":
        tags=Tag.query.filter(Tag.fire==True).all()
    elif tag=="water":
        tags=Tag.query.filter(Tag.water==True).all()
    elif tag=="grass":
        tags=Tag.query.filter(Tag.grass==True).all()
    if tags is None:
        return ("The data is not present"),404
    all_tags=tags_schema.dump(tags)
    l=[]
    for i in all_tags.data:
            pkdata=Pokemon.query.get(i["id"])
            tag=update_tag([],pkdata.id)
            tr=trainer_profile(pkdata.user_id,pkdata.name)
            pk = {"id":pkdata.id,"name":pkdata.name,"tagList":tag,"sprite":pkdata.sprite,"descripion":pkdata.description,"createdAt":pkdata.createdAt,"updatedAt":pkdata.updatedAt,"favouritesCount":pkdata.favouritesCount,"trainer":tr["trainer"]}
            l.append(pk)
    lp={"pokemon":l,"pokemonCount":len(l)}
    return(lp)

#to list the pokemon details using pokemon filter by tag (or)
#filter by favourited(user) (or)filter by trainer
@app.route("/api/pokemon",methods=["GET"])
def getmul_pokemon():
    tag=request.args.get('tag')
    trainer=request.args.get('trainer')
    favourited=request.args.get('favourited')
    limit=request.args.get('limit')
    offset=request.args.get('offset')
    if limit is None:
        limit=20
    elif offset is None:
        offset=0
    if tag is not None:
        return json.dumps(tag_pk(tag))   #call to tag_pk() method
    elif trainer is not None:
        urdata=User.query.filter(User.username==trainer).first()
        if urdata is None:
            return ("The data is not present"),404
        pkdata=Pokemon.query.filter(Pokemon.user_id==urdata.id).order_by(desc(Pokemon.id)).all()
        if pkdata is None:
            return ("The data is not present"),404
        pks=pokemons_schema.dump(pkdata)
        l=[]
        for i in pks.data:
            pkdata=Pokemon.query.filter(Pokemon.name==i["name"]).first()
            tag=update_tag([],pkdata.id)
            tr=trainer_profile(pkdata.user_id,pkdata.name)
            pk = {"id":pkdata.id,"name":pkdata.name,"tagList":tag,"sprite":pkdata.sprite,"descripion":pkdata.description,"createdAt":pkdata.createdAt,"updatedAt":pkdata.updatedAt,"favouritesCount":pkdata.favouritesCount,"trainer":tr["trainer"]}
            l.append(pk)
        lp={"pokemon":l,"pokemonCount":len(l)}
        return json.dumps(lp)
    elif favourited is not None:
        urdata=User.query.filter(User.username==favourited).first()
        if urdata is None:
            return ("The data is not present"),404
        favdata=Favourites.query.filter(Favourites.user_id==urdata.id).order_by(desc(Favourites.id)).all()
        if favdata is None:
            return ("The data is not present"),404
        fav=favs_schema.dump(favdata)
        l=[]
        for i in fav.data:
            pkdata=Pokemon.query.filter(Pokemon.name==i["pk_name"]).first()
            tag=update_tag([],pkdata.id)
            tr=trainer_profile(pkdata.user_id,pkdata.name)
            pk = {"id":pkdata.id,"name":pkdata.name,"tagList":tag,"sprite":pkdata.sprite,"descripion":pkdata.description,"createdAt":pkdata.createdAt,"updatedAt":pkdata.updatedAt,"favouritesCount":pkdata.favouritesCount,"trainer":tr["trainer"]}
            l.append(pk)
        lp={"pokemon":l,"pokemonCount":len(l)}
        return json.dumps(lp)
    else:
        pkdata=Pokemon.query.order_by(desc(Pokemon.id)).limit(limit).offset(offset).all()
        if pkdata is None:
            return ("The data is not present"),404
        pks=pokemons_schema.dump(pkdata)
        l=[]
        for i in pks.data:
            pkdata=Pokemon.query.get(i["id"])
            tag=update_tag([],pkdata.id)
            tr=trainer_profile(pkdata.user_id,pkdata.name)
            pk = {"id":pkdata.id,"name":pkdata.name,"tagList":tag,"sprite":pkdata.sprite,"descripion":pkdata.description,"createdAt":pkdata.createdAt,"updatedAt":pkdata.updatedAt,"favouritesCount":pkdata.favouritesCount,"trainer":tr["trainer"]}
            l.append(pk)
        lp={"pokemon":l,"pokemonCount":len(l)}
        return json.dumps(lp)

#to feed the pokemons followed by user
@app.route("/api/pokemon/feed",methods=["GET"])
@jwt_required
def pk_feed():
    limit=request.args.get('limit')
    offset=request.args.get('offset')
    if limit is None:
        limit=20
    if offset is None:
        offset=0
    email=get_jwt_identity()
    urdata=User.query.filter(User.email==email).first()
    flr=Followers.query.filter(Followers.follower_id==urdata.id).order_by(desc(Followers.id)).limit(limit).offset(offset).all()
    if flr is None:
        return ("There are no followers to feed"),404
    flr=flrs_schema.dump(flr)
    l=[]
    for j in flr.data:
        pkdata=Pokemon.query.filter(Pokemon.user_id==j["followed_id"]).all()
        if pkdata is None:
            return ("There are no pokemons under followers to feed"),404
        pk=pokemons_schema.dump(pkdata)
        for i in pk.data:
            pkdata=Pokemon.query.get(i["id"])
            tag=update_tag([],pkdata.id)
            tr=trainer_profile(pkdata.user_id,pkdata.name)
            pk = {"id":pkdata.id,"name":pkdata.name,"tagList":tag,"sprite":pkdata.sprite,"descripion":pkdata.description,"createdAt":pkdata.createdAt,"updatedAt":pkdata.updatedAt,"favouritesCount":pkdata.favouritesCount,"trainer":tr["trainer"]}
            l.append(pk)
    lp={"pokemon":l,"pokemonCount":len(l)}
    return json.dumps(lp)

#to get pokemon details using pokemon name
@app.route("/api/pokemon/<name>",methods=["GET"])
def get_pokemon(name):
    pkdata=Pokemon.query.filter(Pokemon.name==name).first()
    if pkdata is None:
        return render_template("404.html"),404
    tag=update_tag([],pkdata.id)
    tr=trainer_profile(pkdata.user_id,pkdata.name)
    pk = {"pokemon":{"id":pkdata.id,"name":pkdata.name,"tagList":tag,"sprite":pkdata.sprite,"descripion":pkdata.description,"createdAt":pkdata.createdAt,"updatedAt":pkdata.updatedAt,"favouritesCount":pkdata.favouritesCount,"trainer":tr["trainer"]}}
    return json.dumps(pk)

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
    return get_pokemon(pkdata.name)
        
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
        return (get_pokemon(pkdata.name))
        

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
        pk=get_pokemon(pkdata.name)
        tag=update_tag([],pkdata.id)
        db.session.delete(pkdata)
        db.session.commit()
        return (pk)

#to get the trainer details
def trainer_profile(cuser_id,pk_name):
    pk=Pokemon.query.filter(Pokemon.name==pk_name).first()
    prdata=User.query.filter(User.id==pk.user_id).first()
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
    tr=trainer_profile(cmdata.user_id,cmdata.pk_name)
    cm={"comment":{"id":cmdata.id,"createdAt":cmdata.createdAt,"updatedAt":cmdata.updatedAt,"body":cmdata.body,"trainer":tr["trainer"]}}
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
def get_comments(name):
    all=Comments.query.filter(Comments.pk_name==name)
    if all is None:
        return render_template("404.html"), 404
    a=comments_schema.dump(all)
    cm=[]
    for i in a.data:
        cmt=get_comment(i["id"])
        cm.append(cmt["comment"])
    return json.dumps(cm)

#to delete comment on pokemon using pokemon name and comment id
#comments can be deleted by both we posted and on whom posted
@app.route("/api/pokemon/<name>/comments/<id>", methods=["DELETE"])
@jwt_required
def delete_comment(name,id):
    email=get_jwt_identity()
    urdata=User.query.filter(User.email==email).first()
    cmdata=Comments.query.get(id)
    if(cmdata.pk_name!=name):
        return ("the pokemon name and id is not matching")
    if(urdata.id!=cmdata.user_id):
        return render_template("403.html"),403
    cmt=get_comment(cmdata.id)
    db.session.delete(cmdata)
    db.session.commit()
    return json.dumps(cmt)

#to get the favourite in the pokemon using pokemon name and user_id
def favget_pokemon(name):
    pkdata=Pokemon.query.filter(Pokemon.name==name).first()
    if pkdata is None:
        return render_template("404.html"),404
    tag=update_tag([],pkdata.id)
    tr=trainer_profile(pkdata.user_id,pkdata.name)
    fav=Favourites.query.filter(Favourites.pk_name==name).first()
    if fav is None:
        f=False
    else:
        f=True
    pk = {"pokemon":{"id":pkdata.id,"name":pkdata.name,"tagList":tag,"sprite":pkdata.sprite,"descripion":pkdata.description,"createdAt":pkdata.createdAt,"updatedAt":pkdata.updatedAt,"favourited":f,"favouritesCount":pkdata.favouritesCount,"trainer":tr["trainer"]}}
    return json.dumps(pk)

#to favourite a pokemon using name
@app.route("/api/pokemon/<name>/favourite", methods=["POST"])
@jwt_required
def fav_pokemon(name):
    email=get_jwt_identity()
    urdata=User.query.filter(User.email==email).first()
    pkdata = Pokemon.query.filter(Pokemon.name==name).first()
    if (pkdata==None):
        return render_template("404.html"), 404
    #to check whether the follower is previously favorited or not
    all=Favourites.query.filter(Favourites.pk_name==name)
    a=favs_schema.dump(all)
    for i in a.data:
        if urdata.id==i["user_id"]:
            return(favget_pokemon(name))

    fav=Favourites(pkdata.name,urdata.id)
    db.session.add(fav)
    db.session.commit()
    pkdata.favouritesCount+=1
    db.session.commit()
    return (favget_pokemon(name))
    
#to unfavourite a pokemon using name
@app.route("/api/pokemon/<name>/favourite", methods=["DELETE"])
@jwt_required
def unfav_pokemon(name):
    email=get_jwt_identity()
    urdata=User.query.filter(User.email==email).first()
    pkdata = Pokemon.query.filter(Pokemon.name==name).first()
    if (pkdata==None):
        return render_template("404.html"), 404
    #to check whether the follower is previously unfavorited or not
    a=Favourites.query.filter(Favourites.pk_name==name).first()
    if a is None:
        return (favget_pokemon(name))
    if urdata.id!=a.user_id:
        return render_template("403.html"),403

    db.session.delete(a)
    db.session.commit()
    pkdata.favouritesCount-=1
    db.session.commit()
    return (favget_pokemon(name))

#to get the list of unique tags which have used
@app.route("/api/tags",methods=["GET"])
def get_tags():
    all_tags = Tag.query.all()
    tag=[]
    if(all_tags==None):
        return json.dumps(tag)
    result = tags_schema.dump(all_tags)
    for i in result.data:
        if i["flying"]==True:
            if "flying" not in tag:
                tag.append("flying")
        if i["fire"]==True:
            if "fire" not in tag:
                tag.append("fire")
        if i["water"]==True:
            if "water" not in tag:
                tag.append("water")
        if i["grass"]==True:
            if "grass" not in tag:
                tag.append("grass")
    return json.dumps(tag)


if __name__ == '__main__':
    db.create_all()
    app.run(host='localhost', port=8006, debug=True)
