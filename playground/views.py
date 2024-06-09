from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Article
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from . import forms

# Create your views here.
def article_list(request):
    articles = Article.objects.all().order_by('date')

    return render(request, 'articles.html', {'articles': articles})

def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)

    return render(request, 'article_detail.html', {'article': article})
    # return HttpResponse(f"Article Title: {article.title}")

@login_required(login_url="/account/login")
def article_create(request):
    if request.method == 'POST':
        form = forms.CreateArticle(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.author = request.user
            instance.save()
            return redirect('articles:article_list')
    else:
        form = forms.CreateArticle
    return render(request, 'article_create.html', {'form': form})