from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from datetime import datetime
from .models import PostNew, Ingredient
from .forms import PostForm, IngredientForm
from django.utils import timezone
from django.shortcuts import redirect
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
import time

#Adding by Yi
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.contrib.auth.views import login, logout
from django.contrib.auth.forms import AuthenticationForm

def home(request):
    post_list = Post.objects.all()
    return render(request, 'home.html', {
        'post_list': post_list,
    })

def login_form(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request,user)
            return redirect('post_list')
    else:
        form = AuthenticationForm()
    return render(request,'login_form.html',{'form':form})


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            cluster = Cluster(['18.219.216.0'])
            session = cluster.connect()
            sql = "INSERT INTO ezcook17.user (id, username, password) VALUES (1, '{}', '{}');".format(str(username), str(raw_password))
            print(sql)
            session.execute(sql)
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('post_list_without_edit')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def logout_form(request):
    logout(request)
    # posts = PostNew.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return redirect('post_list_without_edit')

# def post_list(request):
#     posts = PostNew.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
#     return render(request, 'post_list.html', {'posts': posts})

def post_list_without_edit(request):
    # posts = PostNew.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    cluster = Cluster(['18.219.216.0'])
    session = cluster.connect()
    sql = "SELECT * FROM ezcook17.recipe ALLOW FILTERING;"
    print(sql)
    posts = session.execute(sql)
    return render(request, 'post_list_without_edit.html', {'posts': posts})

def post_detail_without_edit(request, pk):
    # post = get_object_or_404(PostNew, pk=pk)
    cluster = Cluster(['18.219.216.0'])
    session = cluster.connect()
    sql = "SELECT * FROM ezcook17.recipe WHERE pk = {} ALLOW FILTERING;".format(str(pk))
    print(sql)
    post = session.execute(sql)
    return render(request, 'post_detail_without_edit.html', {'post': post[0]})

def post_detail(request, pk):
    # post = get_object_or_404(PostNew, pk=pk)
    cluster = Cluster(['18.219.216.0'])
    session = cluster.connect()
    sql = "SELECT * FROM ezcook17.recipe WHERE pk = {} ALLOW FILTERING;".format(str(pk))
    print(sql)
    post = session.execute(sql)
    return render(request, 'post_detail.html', {'post': post[0]})

# def post_detail(request, pk):
#     post = get_object_or_404(PostNew, pk=pk)
#     return render(request, 'post_detail.html', {'post': post})

def post_list(request):
    # posts = PostNew.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    cluster = Cluster(['18.219.216.0'])
    session = cluster.connect()
    sql = "SELECT * FROM ezcook17.recipe  WHERE owner = '"+str(request.user)+"' ALLOW FILTERING;"
    print(sql)
    posts = session.execute(sql)
    return render(request, 'post_list.html', {'posts': posts})

def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            # post.author = request.user
            # post.published_date = timezone.now()
            post.save()
            cluster = Cluster(['18.219.216.0'])
            session = cluster.connect()
            sql = "INSERT INTO ezcook17.recipe (id, pk,  content, owner, post_time, title) VALUES (1, "+str(post.pk)+", '"+str(post.text)+"', '"+str(request.user)+"', toTimestamp(now()), '"+str(post.title)+"');"
            print(sql)
            session.execute(sql)
            # session.execute("INSERT INTO ezcook17.recipe (id, content, owner, title) VALUES (now(),"+str(post.text)+", "+str(request.user)+", "+str(post.title)+");")
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'post_new.html', {'form': form})

def post_edit(request, pk):
    print("here")
    print(pk)
    post = get_object_or_404(PostNew, pk=pk)
    cluster = Cluster(['18.219.216.0'])
    session = cluster.connect()
    sql = "SELECT id FROM ezcook17.recipe  WHERE pk = "+str(pk)+" ALLOW FILTERING;"
    print(sql)
    Cpost = session.execute(sql)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            # post.author = request.user
            # post.published_date = timezone.now()
            post.save()
            cluster = Cluster(['18.219.216.0'])
            session = cluster.connect()
            sql = "update ezcook17.recipe set content = '{}', title = '{}' where pk = {} and id = {}".format(post.text, post.title, post.pk, Cpost[0].id)
            print(sql)
            Cpost = session.execute(sql)
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'post_edit.html', {'form': form})

def my_stock(request):
    cluster = Cluster(['18.219.216.0'])
    session = cluster.connect()
    sql = "SELECT ingredients FROM ezcook17.user WHERE username = '"+str(request.user)+"' ALLOW FILTERING;"
    print(sql)
    ingredients = session.execute(sql)
    print("my ingredients: {}".format(ingredients[0]))
    ingred = {}
    for idx_value, value in enumerate(ingredients[0]):
        print(idx_value,value)
        ingred = value
    print(ingred)
    return render(request, 'my_stock.html', {'ingredients': ingred})

def add_ingredient(request):
    if request.method == "POST":
        form = IngredientForm(request.POST)
        if form.is_valid():
            ingredient = form.save(commit=False)
            ingredient.save()
            print(type("{now():{}}"))
            cluster = Cluster(['18.219.216.0'])
            session = cluster.connect()
            ingred_map = "{'"+str(ingredient.name)+"':"+str(ingredient.amount)+"}"
            sql = "update ezcook17.user set ingredients = ingredients + {} where id = 1 and username = '{}'".format(ingred_map, str(request.user))
            print(sql)
            session.execute(sql)
            return redirect('my_stock')
    else:
        form = IngredientForm()
    return render(request, 'add_ingredient.html', {'form': form})

def edit_ingredient(request, name):
    ingred = get_object_or_404(Ingredient, name=name)
    print(ingred.name)
    if request.method == "POST":
        # form = PostForm(request.POST, instance=post)
        form = IngredientForm(request.POST, instance=ingred)
        print(form)
        form.name = name
        if form.is_valid():
            ingredient = form.save(commit=False)
            ingredient.save()
            print(type("{now():{}}"))
            cluster = Cluster(['18.219.216.0'])
            session = cluster.connect()
            ingred_map = "{'"+str(ingredient.name)+"':"+str(ingredient.amount)+"}"
            sql = "update ezcook17.user set ingredients = ingredients + {} where id = 1 and username = '{}'".format(ingred_map, str(request.user))
            print(sql)
            session.execute(sql)
            return redirect('my_stock')
    else:
        form = IngredientForm()
    return render(request, 'edit_ingredient.html', {'form': form})
