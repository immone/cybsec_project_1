from django.shortcuts import render, redirect
from .models import Account, Resource
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm as RegForm

def registerView(request):
    return render(request, 'pages/register.html', { "form": RegForm })

def validateView(request):
    if request.method == 'POST':
        form = RegForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            pw = form.cleaned_data["password"]
            if not Account.objects.filter(owner__username='name').exists():
                user_obj = User.objects.create_user(username=name, password=pw)
                Account.objects.create(owner=user_obj)
                return redirect('/')
    return redirect('/')

@login_required
def homePageView(request):
    if request.user.is_superuser:
        return render(request, 'pages/index_admin.html', {"accounts": Account.objects.all() })
    res = Account.objects.get(owner=request.user).resources.all()
    return render(request, 'pages/index.html', { "resources": res} )

@login_required
def addView(request):
    if request.method == 'POST':
        receiver = request.POST.get('to')
        name= request.POST.get('name')
        amount = int(request.POST.get('amount'))
        user = Account.objects.get(owner__username=receiver)
        res = Resource(name=name, available=amount)
        res.save()
        user.resources.add(res)
    return redirect('/')

@login_required
def listView(request):
    if request.method == 'GET':
        return render(request, 'pages/list.html', {"resource": Resource.objects.get(name=request.GET.get('list_field')) })

@login_required
def spendView(request):
    if request.method == 'POST':
        res_name = request.POST.get('spend_field_name')
        res_amount = request.POST.get('spend_field_amount')
        msg = ""
        try:
            list = Resource.objects.get(name=res_name)
            n = list.available
            list.available = n - int(res_amount)
            list.save()
            msg = "Spent " + str(res_amount) + " resources. " + str(list.available) + " " + res_name + " resources remains."
        except:
            msg = msg + "Failed to find or spend the resources"
        return render(request, 'pages/spend.html', {"msg": msg})