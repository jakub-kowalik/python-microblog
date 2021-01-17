from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db
from app import login
from flask_login import UserMixin

followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )

upvotes = db.Table('upvotes',
                   db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                   db.Column('post_id', db.Integer, db.ForeignKey('post.id'))
                   )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    joined = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    upvoted = db.relationship(
        'Post', secondary=upvotes,
        primaryjoin=(upvotes.c.user_id == id),
        backref=db.backref('upvotes', lazy='dynamic'),
        lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        if self.email is not None:
            digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        else:
            digest = 'deleted'
        return 'https://www.gravatar.com/avatar/{}?d=monsterid&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
            followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(1000))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    upvoters = db.relationship(
        'User', secondary=upvotes,
        primaryjoin=(upvotes.c.post_id == id),
        backref=db.backref('upvotes', lazy='dynamic'),
        lazy='dynamic')

    def __repr__(self):
        return '<Post {}>'.format(self.body)

    def post_score(self, post):
        return self.upvoters.filter(
            upvotes.c.post_id == post.id).count() > 0

    def is_upvoting(self, user):
        return self.upvoters.filter(
            upvotes.c.user_id == user.id).count() > 0

    def upvote(self, user):
        if not self.is_upvoting(user):
            self.upvoters.append(user)

    def unupvote(self, user):
        if self.is_upvoting(user):
            self.upvoters.remove(user)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
