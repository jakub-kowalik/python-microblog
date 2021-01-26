from app import app
from app.forms import LoginForm
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user
from app.models import User, upvotes
from flask_login import logout_user
from flask_login import login_required
from app import db
from app.forms import RegistrationForm
from datetime import datetime
from app.forms import EditProfileForm
from app.forms import EmptyForm
from app.forms import PostForm
from app.forms import CheckboxForm
from app.models import Post


@app.before_request
def before_request():
    if not current_user.is_anonymous:
        if current_user.is_authenticated:
            current_user.last_seen = datetime.utcnow()
            db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if not current_user.is_anonymous:
        form = PostForm()
        if form.validate_on_submit():
            post = Post(body=form.post.data, author=current_user)
            db.session.add(post)
            db.session.commit()
            flash('Dodano wpis!')
            return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    if current_user.is_anonymous:
        return render_template("index.html", title='Home', posts=posts.items,
                               next_url=next_url, prev_url=prev_url)
    else:
        return render_template('index.html', title='Home', form=form,
                               posts=posts.items, next_url=next_url,
                               prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Niewlasciwe dane')
            return redirect(url_for('login'))
        if user.is_deleted:
            flash('Uzytkownik usunal swoje konto')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(request.referrer)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Witamy na mikroblogu!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    form2 = CheckboxForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form, delete_form=form2)


@app.route('/user/<username>/upvoted')
def user_upvoted(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.upvoted.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    form2 = CheckboxForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form, delete_form=form2)


@app.route('/post/<post_id>')
def post(post_id):
    form = EmptyForm()
    posts = Post.query.filter_by(id=post_id).first_or_404()
    return render_template('post.html', post=posts, form=form)


@app.route('/delete/post/<post_id>', methods=['POST'])
def delete_post(post_id):
    form = EmptyForm()
    if form.validate_on_submit():
        posts = Post.query.filter_by(id=post_id).first_or_404()
        if current_user == posts.author or current_user.is_admin:
            posts.upvoters = []
            db.session.commit()
            db.session.delete(posts)
            db.session.commit()
            flash('Usunieto wpis!')
            return redirect(request.referrer)


@app.route('/delete/user/<username>', methods=['POST'])
def delete_user(username):
    form = CheckboxForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first_or_404()
        if current_user == user or current_user.is_admin:
            user.is_deleted = True
            user.email = None
            user.about_me = None
            user.password_hash = None
            db.session.commit()
            flash('Usunieto konto! '.format(username))
            if current_user.is_admin:
                return redirect(request.referrer)
            else:
                return redirect(url_for('logout'))


@app.route('/edit_profile/<username>', methods=['GET', 'POST'])
@login_required
def edit_profile(username):
    if current_user.username == username or current_user.is_admin:
        form = EditProfileForm(username)
        user = User.query.filter_by(username=username).first_or_404()
        if form.validate_on_submit():
            user.about_me = form.about_me.data
            db.session.commit()
            flash('Zmiany zostaly zapisane.')
            return redirect(url_for('edit_profile', username=user.username))
        elif request.method == 'GET':
            form.about_me.data = user.about_me
        return render_template('edit_profile.html', title='Edit Profile',
                               form=form)
    return render_template('404.html', title='error')


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('Nie ma uzytkownika {}.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('Nie mozesz obserwowac sam siebie!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('Zaobserwowano {}!'.format(username))
        return redirect(request.referrer)
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('Nie ma uzytkownika {}.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('Nie mozesz odobserwowac siebie')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('Nie obserwujesz juz {}.'.format(username))
        return redirect(request.referrer)
    else:
        return redirect(url_for('index'))


@app.route('/my', methods=['GET', 'POST'])
@login_required
def my_microblog():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Dodano wpis!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('my_microblog', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('my_microblog', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/upvote/<post_id>', methods=['POST'])
@login_required
def upvote(post_id):
    if not current_user.is_anonymous:
        form = EmptyForm()
        if form.validate_on_submit():
            post = Post.query.filter_by(id=post_id).first()
            if post is None:
                flash('Nie ma uzytkownika {}.'.format(username))
                return redirect(url_for('index'))
            if post.author == current_user:
                return redirect(url_for('index'))
            post.upvote(current_user)
            db.session.commit()
            flash('Zaplusowales wpis o id {}!'.format(post_id))
            return redirect(request.referrer)
        else:
            return redirect(url_for('index'))


@app.route('/unupvote/<post_id>', methods=['POST'])
@login_required
def unupvote(post_id):
    if not current_user.is_anonymous:
        form = EmptyForm()
        if form.validate_on_submit():
            post = Post.query.filter_by(id=post_id).first()
            if post is None:
                flash('Nie ma uzytkownika {}.'.format(username))
                return redirect(url_for('index'))
            post.unupvote(current_user)
            db.session.commit()
            flash('Odplusowales wpis o id {}!'.format(post_id))
            return redirect(request.referrer)
        else:
            return redirect(url_for('index'))
