from django.shortcuts import render, redirect
from .models import Account, Resource
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm as RegForm
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

"""
    PROBLEM: CSRF validation is not enforced
        Description:
            Django, by default, enforces CSRF validation (see https://docs.djangoproject.com/en/5.0/howto/csrf/).
            Currently, it is disabled in ../project/settings.py on line 47, which allows the application
            to send POST requests without CSRF validation, exposing a CSRF vulnerability in the register form.
            
        FIX:
            Turn Django's default CSRF validation back on by doing the following:
                1) Go to ../project/settings.py and uncomment line 47
                2) Remove the @csrf_exempt tag below before the register view
                3) Go to ./pages/register.html and add `{% csrf_token %}` inside the form element.
"""

@csrf_exempt
def registerView(request):
    return render(request, 'pages/register.html',{ "form": RegForm })

def validateView(request):
    if request.method == 'POST':
        form = RegForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            if User.objects.filter(username=name).first():
                return HttpResponse("The username is taken")
            pw = form.cleaned_data["password"]
            """
                PROBLEM: OWASP A07:2021 - Identification and Authentication Failures
                    Description: 
                        The application allows both brute-forcing, as well as permits weak and known passwords without
                        any extra complexity requirements. Note that Django implements password salting + hashing as a 
                        default, so that is not an issue (see https://docs.djangoproject.com/en/5.0/topics/auth/passwords/).
                        The is_valid-call above only checks that the form elements types and maximum lengths
                        agree with how they are declared in .forms.py.
                            
                    FIX:
                        Implement (at least some level of) control system to force complexity. According to OWASP, the 
                        passwords should not be from a "list of well-known passwords" (as also discussed on the course),
                        but for the sake of simplicity we shall not do this.
                        
                        We could, for example, require the password to be at least of length 8 and consist of at least 1 number
                        and at least 1 special character as follows:
                        
                        import re
                        re_sc = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
                        re_n = re.compile('\d')
                        if not re_sc.search(pw):
                            return HttpResponse("The password must contain a special character")
                        elif not re_n.search(pw):
                            return HttpResponse("The password must contain a number")
                        elif len(pw) < 8:
                            return HttpResponse("The password must be at least of length 8")
                        else:                 
            """

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
        name = request.GET.get("list_field")
        """
               PROBLEM: OWASP A01:2021 – Broken Access Control
                   Description:
                       The user's should only have access to view the availability of the resources that they own. However,
                       sending a GET-request via localhost:8000/list?=list_field=<resource> gives an access to a resource even if
                       the user does not possess the particular resource.
                   FIX:
                       Enforce an access control system that checks that the requesting user owns the particular resource. 
                       For example, the following control structure should work:
                   
                       if name not in [x.name for x in Account.objects.get(owner=request.user).resources.all()]:
                          return HttpResponse("You do not own the resource")
                       else:
                    
           """
        try:
            row = Resource.objects.raw(f"SELECT * FROM resources WHERE name = '{name}'")[0]
            """
                PROBLEM: OWASP AO3:2021 - Injection
                    Description:
                        Django allows raw SQL queries, where SQL injections are a vulnerability in the system
                        when the parameters are being passed directly to the query as above.
                    FIX:
                        If the programmer wants to use Django's raw queries, then the string should be passed
                        as a `params` to the raw-call (see: https://docs.djangoproject.com/en/5.0/topics/db/sql/) as follows:
                        
                        row = Resource.objects.raw("SELECT * FROM resources WHERE name = %s", [name])[0]
                        
                        Alternatively, a more straightforward fix is to use Django's Object-Relational Mapping and query
                        the corresponding row directly using ORM as commented below in the return statement.
                    
            """
        except Exception as e:
            return redirect('/')
        return render(request, 'pages/list.html', {"resource": row })
        # return render(request, 'pages/list.html', {"resource": Resource.objects.get(name=request.GET.get('list_field')) })

@login_required
def spendView(request):
    if request.method == 'POST':
        res_name = request.POST.get('spend_field_name')
        res_amount = request.POST.get('spend_field_amount')
        msg = ""
        try:
            list = Resource.objects.get(name=res_name)
            n = list.available
            """
                PROBLEM: OWASP A04:2021 - Insecure Design
                    Description:
                        The application allows user to "spend" arbitrary amounts as well as negative amounts, which, as an
                        architectural flaw, causes issues in the resource allocation and database consistency.
                    FIX:
                        Employ control systems to make sure that the "spent" amounts don't exceed the
                        resource's availability. Also make sure that the input is a non-negative number. 
                        This is fixed as follows:

                    if n < int(res_amount):
                        msg = msg + "Not enough resources"
                    elif int(res_amount) < 0:
                        msg = msg + "Spent resources has to be a positive number"
                    else:
            """
            list.available = n - int(res_amount)
            list.save()
            msg = "Spent " + str(res_amount) + " resources. " + str(list.available) + " " + res_name + " resources remains."

        except:
            msg = msg + "Failed to find or spend the resources"
        return render(request, 'pages/spend.html', {"msg": msg})