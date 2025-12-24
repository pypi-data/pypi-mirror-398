"""
Python Declarative Programming (DecPy) version 2.0.0

The BSD 3-Clause Copyright (c) 2025 Paul Dobryak (Pavel Vadimovich Dobryak)

A library for lazy evaluation and 4 types of declarative programming in Python:
1. An analogue of SQL (tuple calculus).
2. An analogue of QBE (domain calculus).
3. An analogue of Prolog (first-order predicate calculus, logic programming)
with recursive queries.
4. Declarative language for working with graphs.
and instruments for functional programming:
functors, applicative functors, monads and currying

Verified on Python 3.13.0

For the latest version and documentation, see
https://github.com/pauldobriak/DecPy

Author and programmer: Pavel Vadimovich Dobryak,
e-mail: goodsoul@mail.ru
https://vk.com/pauldobriak
tel, whatsapp: +79022726154
"""

from itertools import product
from functools import reduce
from inspect import signature
from copy import deepcopy

#Множественный конструктор
def multiconstr(cls):
    def wrapper(*n):
        if len(n)==0:
            return cls()
        elif len(n)==1 and type(n[0])==int:
            return (cls() for i in range(n[0]))
        else:
            return cls(*n)
    return wrapper

#ленивое выражение
class expr:
    def __init__(self,arg1,op,arg2):
        self.arg1=arg1
        self.op=op
        self.arg2=arg2
        self.recstart=False
    def __call__(self,*args):
        #вычисления с рекурсиями
        if self.recstart:
            n=0
            buf=self.recparam[0].value
            self.recparam[0].value=lazyset()
            #reclim=10
            #while reclim>0:
            while True:
                R=self.callmain(*args)
                if len(R)==n:
                    break
                n=len(R)
                self.recparam[0].value=lazyset(R)    
                #reclim=reclim-1
            self.recparam[0].value=buf
            return lazyset(R)
        else:
            return self.callmain(*args)
    def __iter__(self):
        return self().__iter__()
    def __next__(self):
        return self().__next__()
    #вычисления или выполнение запросов без рекурсий
    def callmain(self,*args):
            if len(args)>0:
                sign = self.createsign()
                for i in range(len(sign)):
                    sign[i](args[i])
            arg1 = self.arg1
            #проверка на цепочку умножений
            manymult=False
            if type(arg1)==expr and arg1.op=="*" and self.op=="*":
                manymult=True
            elif type(arg1)==lazyindex and type(arg1.obj)==expr and arg1.obj.op=="*" and self.op=="*":
                manymult=True
            # получение выборок, вычислений; прерывание вызовов, если аргумент - класс.
            while callable(arg1):
                if hasattr(arg1,"__dict__") and ("qrcls" in arg1.__dict__) and (arg1.__dict__["qrcls"]==True):
                    break
                arg1=arg1()
            arg2 = self.arg2
            while callable(arg2):
                if hasattr(arg2,"__dict__") and ("qrcls" in arg2.__dict__) and (arg2.__dict__["qrcls"]==True):
                    break
                arg2=arg2()
            if self.op=="+":
                return arg1+arg2
            elif self.op=="*":
                if manymult and type(arg1) is multset and type(arg2) is multset:
                    return arg1.specialmult(arg2)
                if type(arg1)==set or type(arg2)==set:
                    return multset(arg1)*multset(arg2)
                return arg1*arg2
            elif self.op=="**":
                #заплатка - дополнительные проверки
                if type(arg1)==set or type(arg2)==set:
                    return multset(arg1)**multset(arg2)
                return arg1**arg2
            elif self.op=="<":
                return arg1<arg2
            elif self.op=="<=":
                return arg1<=arg2
            elif self.op=="==":
                return arg1==arg2
            elif self.op==">=":
                return arg1>=arg2
            elif self.op==">":
                return arg1>arg2
            elif self.op=="!=":
                return arg1!=arg2
            elif self.op=="&":
                return arg1 & arg2
            elif self.op=="|":
                return arg1 | arg2
            elif self.op=="|=":
                return arg2
            elif self.op=="/":
                return arg1 / arg2
            elif self.op=="//":
                return arg1 // arg2
            elif self.op=="%":
                return arg1 % arg2
            elif self.op=="-":
                return arg1 - arg2
            elif self.op=="^":
                return arg1 ^ arg2
            elif self.op=="neg":
                return -arg1
                          
    def __str__(self):
        return str(self())
    def __repr__(self):
        return str(self)
    def __add__(self,other):
        return expr(self,"+",other)
    def __mul__(self,other):
        return expr(self,"*",other)
    def __pow__(self,other):
        return expr(self,"**",other)
    def __or__(self,other):
        return expr(self,"|",other)
    def __sub__(self,other):
        return expr(self,"-",other)
    def __xor__(self,other):
        return expr(self,"^",other)
    def __lt__(self,other):
        return expr(self,"<",other)
    def __le__(self,other):
        return expr(self,"<=",other)
    def __eq__(self,other):
        return expr(self,"==",other)
    def __ge__(self,other):
        return expr(self,">=",other)
    def __gt__(self,other):
        return expr(self,">",other)
    def __ne__(self,other):
        return expr(self,"!=",other)
    def __and__(self,other):
        return expr(self,"&",other)
    def __truediv__(self,other):
        return expr(self,"/",other)
    def __floordiv__(self,other):
        return expr(self,"//",other)
    def __neg__(self):
        return expr(self,"neg",None)
    def __mod__(self,other):
        return expr(self,"%",other)

    def __radd__(self,other):
        return expr(other,"+",self)
    def __rmul__(self,other):
        return expr(other,"*",self)
    def __rpow__(self,other):
        return expr(other,"**",self)
    def __rsub__(self, other):
        return expr(other,"-",self)
    def __rtruediv__(self, other):
        return expr(other,"/",self)
    def __rfloordiv__(self, other):
        return expr(other,"//",self)
    def __rmod__(self, other):
        return expr(other,"%",self)

    # определение новых понятий в стиле пролога
    def __ior__(self,other):
        L=reccheck(self,other)
        if len(L)>0:
            #проталкивание индекса внутрь выражения:
            if type(other)==lazyindex:
                A=var()[other.arg]
                other = other.obj
                R = indpropagation(A,other)
                other.recstart=True
                other.recparam=L
                return R
            else:
                other.recstart=True
                other.recparam=L
                return other
        return other
    # создание сигнатуры для превращения ленивого выражения в функцию
    def createsign(self,L=None):
        if L==None:
            L=[]
        if callable(self.arg1):
            self.arg1.createsign(L)
        if callable(self.arg2):
            self.arg2.createsign(L)
        return L
    def __getattr__(self,attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return lazyattr(self,attr)
    def __getitem__(self,ind):
        return lazyindex(self,ind)
    def __deepcopy__(self,memo):
        arg1 = deepcopy(self.arg1, memo)
        op = deepcopy(self.op, memo)
        arg2 = deepcopy(self.arg2, memo)
        my_copy = type(self)(arg1,op,arg2)
        my_copy.recstart = self.recstart
        memo[id(self)] = my_copy
        return my_copy
    
#ленивая функция (в том числе - метод) для внутреннего использования    
def lazyfunc(f):           
    class wrapper(expr):
        def __init__(self,*args):
            self.args=args
        def __call__(self,*args):
            if len(args)>0:
                sign = self.createsign()
                for i in range(len(sign)):
                    sign[i](args[i])
            return f(*self.args)
        def createsign(self,L=None):
            if L==None:
                L=[]
            for arg in self.args:
                if callable(arg):
                    arg.createsign(L)
            return L
    def res(*args):
        return wrapper(*args)
    def __repr__(self):
        return str(self())
    res.lzfnc=True
    return res

#ленивая функция, например, для встраивания в формулу функций библиотеки math
def lazyfun(f):
    @lazyfunc
    def wrapper(*args):
        return f(*[a() for a in args])
    return wrapper

#универсальный способ добавления элемента в коллекцию
def app(coll,el):
    if type(coll)==tuple:
        R=coll+(el,)
        return R
    elif hasattr(coll,"append"):
        coll.append(el)
        return coll
    elif hasattr(coll,"add"):
        coll.add(el)
        return coll
    
#универсальный способ соединения коллекций:
def merge(coll1,coll2):
    if hasattr(coll1,"__add__") and hasattr(coll2,"__add__"):
        #print("случай 1")
        if type(coll1)==type(coll2):
            return coll1+coll2
        else:
            return coll1+type(coll1)(coll2)
    elif hasattr(coll1,"__or__") and hasattr(coll2,"__or__"):
        #print("случай 2")
        if type(coll1)==type(coll2):
            return coll1 | coll2
        else:
            return coll1 | type(coll1)(coll2)
    elif hasattr(coll1,"__add__") and hasattr(coll2,"__or__"):
        #print("случай 3")
        return coll1 + type(coll1)(coll2)
    elif hasattr(coll1,"__or__") and hasattr(coll2,"__add__"):
        #print("случай 4")
        return coll1 | type(coll1)(coll2)
    elif hasattr(coll1,"merge"):
        #print("случай 5")
        return coll1.merge(coll2)
    

#Линеаризация - превращение коллекции со множеством уровней вложенности в одномерную коллекцию
#Или уменьшение количества уровней
def flat(coll,n=0):
    #функция обычной линеаризации:
    def flat(coll):
        if type(coll) in [list,set,tuple]:
            L=type(coll)()
        else:
            L=()
        for el in coll:
            if type(el)==str or not(hasattr(el,"__iter__")):
                L=app(L,el)
            else:
                L=merge(L,flat(el))
        return L
    def depth(coll,r=0):
        D=[]
        r=r+1
        for el in coll:
            if type(el)==str or not(hasattr(el,"__iter__")):
                D.append(r)
            else:
                D.append(depth(el,r))
        return max(D)
    if n==0:
        return flat(coll)
    elif n>0:
        if type(coll) in [list,set,tuple]:
            L=type(coll)()
        else:
            L=()
        for el in coll:
            if type(el)==str or not(hasattr(el,"__iter__")):
                L=app(L,el)
            else:
                L=merge(L,[var(el).flat(n-1)])
        return L
    else:
        n=depth(coll)+n-1
        return var(coll).flat(n)

#Монадическое удаление дубликатов
def monaddistinct(coll,D=None):
    R=type(coll)()
    if D==None:
        D=[]
    for el in coll:
        if not(hasattr(el,"__iter__")):
            if el not in D:
                if hasattr(R,"append"):
                    R.append(el)
                else:
                    R.add(el)
                D.append(el)
        else:
            n=monaddistinct(el,D)
            if len(n)==1:
                if hasattr(R,"append"):
                    R.append(*n)
                else:
                    R.add(*n)
            elif len(n)>1:
                if hasattr(R,"append"):
                    R.append(n)
                else:
                    R.add(n)
    return R

#монадическое стягивание:
def monadreduce(f,coll):
    L=[]
    for el in coll:
        if not(hasattr(el,"__iter__")):
            L.append(el)
        else:
            L.append(monadreduce(f,el))
    return reduce(f,L)

#Замена элементов коллекции на элементы из списка
def monadreplace(coll,L,st=0):
    j=st
    for i in range(len(coll)):
        if not(hasattr(coll[i],"__iter__")):
            coll[i]=L[j]
            j=j+1
        else:
            j=monadreplace(coll[i],L,j)
    return j

#абстрактный класс c ленивыми вычислительными методами
class calculus:
    def __len__(self):
        return len(self())
    @lazyfunc
    def flat(self,n=0):
        return flat(self(),n)
    @lazyfunc
    def len(self):
        return len(self())
        #return len(flat(self()))
    @lazyfunc
    def monadlen(self):
        #return len(self())
        return len(flat(self()))
    @lazyfunc
    def sum(self):
        return sum(self())
        #return sum(flat(self()))
    @lazyfunc
    def monadsum(self):
        #sum(self())
        return sum(flat(self()))
    @lazyfunc
    def min(self,arg=lambda x:x):
        return min(self(),key=arg)
        #return min(flat(self()),key=arg)
    @lazyfunc
    def monadmin(self,arg=lambda x:x):
        #return min(self(),key=arg)
        return min(flat(self()),key=arg)
    @lazyfunc
    def max(self,arg=lambda x:x):
        return max(self(),key=arg)
        #return max(flat(self()),key=arg)
    @lazyfunc
    def monadmax(self,arg=lambda x:x):
        #return max(self(),key=arg)
        return max(flat(self()),key=arg)
    @lazyfunc
    def avg(self):
        return sum(self())/len(self())
        #return sum(flat(self()))/len(flat(self()))
    @lazyfunc
    def monadavg(self):
        #return sum(self())/len(self())
        return sum(flat(self()))/len(flat(self()))
    @lazyfunc
    def sorted(self,arg=lambda x:x):
        return sorted(self(),key=arg)
        #return sorted(flat(self()),key=arg)
    @lazyfunc
    def monadsorted(self,arg=lambda x:x):
        #return sorted(self(),key=arg)
        #return sorted(flat(self()),key=arg)
        L=sorted(flat(self()),key=arg)
        R=deepcopy(self())
        monadreplace(R,L)
        return R
    @lazyfunc
    def group(self):
        return self()
    @lazyfunc
    def distinct(self):
        S=self()
        R=type(S)()
        if hasattr(R,"append"):
            for el in S:
                if el not in R:
                    R.append(el)
            return R
        elif hasattr(R,"add"):
            for el in S:
                if el not in R:
                    R.add(el)
            return R
        elif type(R)==tuple:
            for el in S:
                if el not in R:
                    R=R+(el,)
            return R
        else:
            return type(self())(set(self()))
    @lazyfunc
    def monaddistinct(self):
        return monaddistinct(self())
    @lazyfunc
    def reduce(self,arg):
        return reduce(arg,self())
        #return sorted(flat(self()),key=arg)
    @lazyfunc
    def monadreduce(self,arg):
        return monadreduce(arg,self())
        #return sorted(flat(self()),key=arg)
    def All(self,arg):
        if type(arg) in [int,float,str]:
            a=var()
            arg = (a==arg)
        @lazyfunc
        def f(self):
            return all(arg(el) for el in self)
            #return all(arg(el) for el in flat(self))
        return f(self)
    def Any(self,arg):
        if type(arg) in [int,float,str]:
            a=var()
            arg = (a==arg)
        @lazyfunc
        def f(self):
            return any(arg(el) for el in self)
            #return any(arg(el) for el in flat(self))
        return f(self)
    def monadall(self,arg):
        if type(arg) in [int,float,str]:
            a=var()
            arg = (a==arg)
        @lazyfunc
        def f(self):
            return all(arg(el) for el in flat(self))
        return f(self)
    def monadany(self,arg):
        if type(arg) in [int,float,str]:
            a=var()
            arg = (a==arg)
        @lazyfunc
        def f(self):
            return any(arg(el) for el in flat(self))
        return f(self)
        
#calcfunclist=[calculus.len,calculus.max,calculus.min,calculus.sum]
calcfunclist=[calculus.len,calculus.max,calculus.min,calculus.sum,calculus.avg,calculus.monadlen,calculus.monadmax,calculus.monadmin,calculus.monadsum,calculus.monadavg]

#абстрактный класс-предок для ленивого индекса и атрибута
class lazyabc(expr,calculus):
    def __init__(self,obj,arg):
        self.obj = obj
        self.arg = arg
    def __call__(self,*args):
        obj = self.obj
        if callable(obj):
            if not(hasattr(obj,"__dict__") and ("qrcls" in obj.__dict__) and (obj.__dict__["qrcls"]==True)):
                obj = obj(*args)
            else:
                obj = obj.value
        else:
            obj = obj.value
        return obj
    def createsign(self,L=None):
        return self.obj.createsign(L)
    def __deepcopy__(self,memo):
        obj = deepcopy(self.obj, memo)
        arg = deepcopy(self.arg, memo)
        my_copy = type(self)(obj,arg)
        memo[id(self)] = my_copy
        return my_copy
    
#Ленивый атрибут    
class lazyattr(lazyabc):    
    def __call__(self,*args):
        obj = super().__call__(*args)
        if self.arg in obj.__dict__:
            return obj.__dict__[self.arg]
        #Потенциально опасно, но устраняет необходимость писать код типа F=flight.L
        elif self.arg == "L":
            return set(obj.__dict__.values())

#вспомогательная функция для заполнения пользовательской коллекции результатом - сохранения её типа и настроек. Несколько стратегий:
def createcoll(obj,coll):
    coll=list(coll)
    #создается копия исходной коллекции и из нее удаляются элементы, не входящие в ответ
    if type(obj)not in [multset, set, list] and hasattr(obj,"remove") and all(el in obj for el in coll):
        R=deepcopy(obj)
        for el in zip(obj,R):
            if el[0] not in coll:
                R.remove(el[1])
        return R
    #создание копии коллекции, её очистка и повторное заполнение отобранными значениями (попытка сохранить все настройки):
    elif type(obj)not in [multset, set, list] and (hasattr(obj,"clear") or hasattr(obj,"remove")) and (hasattr(obj,"append") or hasattr(obj,"add")):
        R=deepcopy(obj)
        if hasattr(obj,"clear"):
            R.clear()
        else:
            for el in R:
                R.remove(el)
        if hasattr(obj,"append"):
            f=True
        else:
            f=False
        for el in coll:
            if f:
                R.append(el)
            else:
                R.add(el)
        return R
    #создаем коллекцию с ключом, добавляем элементы
    elif type(obj)not in [multset, set, list] and hasattr(obj,"key"):
        return type(obj)([el for el in coll],obj.key)
    #заполнение коллекции отобранными значениями - свойства-установки коллекции теряются.
    else:
        return type(obj)([el for el in coll])

#вспомогательная функция - определяет, состоит ли коллекция только из истин и лжи
def isbool(arg):
    if not(hasattr(arg,"__iter__")):
        if arg in [True,False]:
            return True
        else:
            return False
    else:
        for a in arg:
            if not(isbool(a)):
                return False
    return True

#Формирование выборки на основе истин и лжи
def selection(obj, arg):
    R=[]
    for el in zip(obj,arg):
        if hasattr(el[1],"__iter__"):
            r=selection(el[0],el[1])
            if len(r)==1:
                R.append(*r)
            elif len(r)>0:
                R.append(r)
        elif el[1]:
            R.append(el[0])
    return type(obj)(R)
    #return type(obj)(el[0] for el in zip(obj,arg) if el[1])


#Запросы к графам
def patternmatch(obj,arg):
    if type(arg)!=tuple:
        return False
    if type(arg[0])!=tuple:
        return False
    f=True
    for a in arg[0]:
        if type(a)!=vartype and a!=Ellipsis:
               f=False
               break
    if f:
        #Шаблон (A,A,...) Пути в дереве
        if len(arg[0])==3 and type(arg[0][0])==vartype and type(arg[0][1])==vartype and arg[0][2]==Ellipsis:
            #print("(A,A,...)")
            R=packelements(var(obj))
            M=var(obj)
            n=len(obj)
            while True:
                P=lazyset()
                for m in M*R:
                    S=lazyset({(m[0],m[1])})[arg[0][:-1]+arg[1:]]()
                    if len(S)>0:
                        P.append(m)
                R = R | P
                k=len(R())
                if k==n:
                    break
                else:
                    n=k
            return R()
        #Шаблон (A,A,...,A) Пути в графе без циклов
        elif len(arg[0])==4 and type(arg[0][0])==vartype and type(arg[0][1])==vartype and arg[0][2]==Ellipsis and type(arg[0][3])==vartype:
            R=packelements(var(obj))
            M=var(obj)
            n=len(obj)
            #print("(A,A,...,A)")
            while True:
                P=lazyset()
                for m in M*R:
                    S=lazyset({(m[0],m[1],m[-1])})[arg[0][:2]+(arg[0][3],)+arg[1:]]()
                    if len(S)>0:
                        P.append(m)
                R = R | P
                k=len(R())
                if k==n:
                    break
                else:
                    n=k
            return R()
        #Шаблон (A,A,...,A,...) Пути в  графе
        elif len(arg[0])==5 and type(arg[0][0])==vartype and type(arg[0][1])==vartype and arg[0][2] is Ellipsis and type(arg[0][3])==vartype and arg[0][4] is Ellipsis:
            R=packelements(var(obj))
            M=var(obj)
            n=len(obj)
            #print("(A,A,...,A,...)")
            while True:
                P=lazyset()
                for m in M*R:
                    fl=True
                    for i in range(1,len(m)):
                        S=lazyset({(m[0],m[1],m[i])})[arg[0][:2]+(arg[0][3],)+arg[1:]]()
                        if len(S)==0:
                            fl=False
                            break
                    if fl:
                        P.append(m)
                R = R | P
                k=len(R())
                if k==n:
                    break
                else:
                    n=k
            return R()
        #Шаблон (A,...,A,...,A) циклы, воcьмерки тоже выводятся
        elif len(arg[0])==5 and type(arg[0][0])==vartype and arg[0][1] is Ellipsis and type(arg[0][2])==vartype and arg[0][3] is Ellipsis and type(arg[0][4])==vartype:
            M=var(obj)
            C=set()
            P=var(obj)
            #print("(A,...,A,...,A)")
            while True:
                newP=lazyset()
                for m in M*P:
                    S=lazyset({(m[0],m[1])})[(arg[0][0],arg[0][2])+arg[1:]]()
                    if len(S)>0:
                        if m[0]==m[-1]:
                            C.add(m[:-1])
                        elif m[0] not in m[1:]:
                            newP.append(m)
                if len(newP())==0:
                    break
                else:
                    P=newP
            #Убираем одинаковые циклы
            D=set()
            for c in C:
                f=True
                d=c
                for i in range(len(c)):
                    d=d[1:]+(d[0],)
                    if d in D:
                        f=False
                        break
                if f:
                    D.add(d)
            return D
        #Шаблон (A,...,A) циклы, удаление восьмерок
        elif len(arg[0])==3 and type(arg[0][0])==vartype and arg[0][1] is Ellipsis and type(arg[0][2])==vartype:
            M=var(obj)
            C=set()
            P=var(obj)
            #print("(A,...,A)")
            while True:
                newP=lazyset()
                for m in M*P:
                    S=lazyset({(m[0],m[1])})[(arg[0][0],arg[0][2])+arg[1:]]()
                    if len(S)>0:
                        if m[0]==m[-1]:
                            C.add(m[:-1])
                        elif m[0] not in m[1:]:
                            newP.append(m)
                if len(newP())==0:
                    break
                else:
                    P=newP
            #Убираем одинаковые циклы
            D=set()
            for c in C:
                f=True
                d=c
                for i in range(len(c)):
                    d=d[1:]+(d[0],)
                    if d in D:
                        f=False
                        break
                if f:
                    D.add(d)
            #Убираем "восьмерки" - рекурсивно ищем циклы в уже найденном цикле
            E=set()
            for d in D:
                dc=lazyset(d)[(arg[0][0],...,arg[0][2],...,arg[0][2]),*arg[1:]]()
                if len(dc)==1:
                   E.add(d) 
            return E
        #декартово произведение множества само на себя несколько раз
        #Шаблон (A,B,C,D,E)
        else:
            M=lazyset(obj)
            for i in range(len(arg[0])-1):
                M=M*lazyset(obj)
            if len(arg)>1:
                R=M[arg[0]+arg[1:]]
            else:
                R=M()
            return R
    return f

#Ленивый индекс
class lazyindex(lazyabc):

    # проверка и расчет декларативных цепочек
    def chainmatch(self,*args):
        # шаблон A*A*...*A*...
        if type(self.obj)==expr and hasattr(self.obj,"op") and self.obj.arg2 is Ellipsis and type(self.obj.arg1.arg1)==expr and hasattr(self.obj.arg1.arg1,"op") and self.obj.arg1.arg1.arg2 is Ellipsis:
            return var(self.obj.arg1.arg2())[((self.arg[0],self.arg[1],...,self.arg[2],...),)+self.arg[3:]](*args)
        # шаблон A*A*...
        elif type(self.obj)==expr and hasattr(self.obj,"op") and self.obj.arg2 is Ellipsis:
            return var(self.obj.arg1.arg2())[((self.arg[0],self.arg[1],...),)+self.arg[2:]](*args)
        # шаблон A*...*A*...*A - цикл с сохранением восьмерок
        elif type(self.obj)==expr and hasattr(self.obj,"op") and type(self.obj.arg1)==expr and hasattr(self.obj.arg1,"op") and self.obj.arg1.arg2 is Ellipsis and type(self.obj.arg1.arg1)==expr and hasattr(self.obj.arg1.arg1,"op") and type(self.obj.arg1.arg1.arg1)==expr and hasattr(self.obj.arg1.arg1.arg1,"op") and self.obj.arg1.arg1.arg1.arg2 is Ellipsis:
            return var(self.obj.arg2())[((self.arg[0],...,self.arg[1],...,self.arg[1]),self.arg[1])+self.arg[2:]](*args)
        # шаблон A*A*...*A
        elif type(self.obj)==expr and hasattr(self.obj,"op") and type(self.obj.arg1)==expr and hasattr(self.obj.arg1,"op") and self.obj.arg1.arg2 is Ellipsis and type(self.obj.arg1.arg1)==expr and hasattr(self.obj.arg1.arg1,"op"):
            return var(self.obj.arg2())[((self.arg[0],self.arg[1],...,self.arg[2]),)+self.arg[3:]](*args)    
        # шаблон A*...*A - цикл c удалением восьмерок
        elif type(self.obj)==expr and hasattr(self.obj,"op") and type(self.obj.arg1)==expr and hasattr(self.obj.arg1,"op") and self.obj.arg1.arg2 is Ellipsis:
            return var(self.obj.arg2())[((self.arg[0],...,self.arg[1]),)+self.arg[2:]](*args)
        return False
    
    def __call__(self,*args):
        #проверка декларативной цепочки, возвращение результата поиска
        P=self.chainmatch(*args)
        if P:
            return P
        obj = super().__call__(*args)
        while callable(obj):
            if hasattr(obj,"__dict__") and ("qrcls" in obj.__dict__) and (obj.__dict__["qrcls"]==True):
                break
            obj=obj()
        #проверка соответствия шаблону, возвращение результата поиска
        P = patternmatch(obj,self.arg)
        if P:
            return P
        #монадическая выборка
        if type(self.arg)==monad:
            R=self.arg(obj)()()
            if isbool(R):
                return var(obj)[R]()
            else:
                return R
            #return var(obj)[self.arg(obj)()()]()
        # Одно условие - исчисление на кортежах
        if callable(self.arg):
            if type(self.arg) is expr and self.arg.op not in ["<","<=","==",">=",">","!=","&","|","^"]:                
                return createcoll(obj,(self.arg(el) for el in obj))
                #return type(obj)(self.arg(el) for el in obj)
                #return type(obj)(*(self.arg(el) for el in obj))
            elif type(self.arg)in [expr,var]:#вероятно, ошибка - вместо var - vartype
                return createcoll(obj,(el for el in obj if self.arg(el)))
                #return type(obj)(el for el in obj if self.arg(el))
            else:
                if type(self.arg) is expr and self.arg.op in ["<","<=","==",">=",">","!=","&","|","^"]:
                    return createcoll(obj,(self.arg(el) for el in obj if self.arg(el)))
                    #return type(obj)(self.arg(el) for el in obj if self.arg(el))
                else:
                    return createcoll(obj,(self.arg(el) for el in obj))
                    return type(obj)(self.arg(el) for el in obj)
        
        # Несколько условий - исчисление на доменах или проекция
        elif type(self.arg)==tuple:
            sign = []
            func = []
            example=None
            for el in obj:
                example = el
                break #для множеств с переменной длинной кортежей может понадобиться перебор всего множества
            if example==None:
                return multset()
            if type(example) in simpletypes:
                lenexample=1
            else:
                lenexample=len(example)
            # Проекция и исчисление на кортежах
            if lenexample>len(self.arg): 
                A = set()
                for el in obj:
                    f = True
                    for i in range(len(self.arg)):
                        if type(self.arg[i]) is expr:
                            if not(self.arg[i](el)):
                                f=False
                                break
                    if f:
                        a=[]
                        for i in range(len(self.arg)):
                            if type(self.arg[i]) in [lazyindex,lazyattr,expr]:
                                xx=self.arg[i](el)
                                if type(xx)!=bool:
                                    a.append(xx)
                                else:
                                    a.append(el)
                        if len(a)==1:
                            A.add(a[0])
                        else:
                            A.add(tuple(a))
                return multset(A)
            # Исчисление на доменах
            else:
                #группировка
                g=False
                lg=0
                arggroup=[None]*min(len(self.arg),lenexample)
                for i in range(min(len(self.arg),lenexample)):
                    if type(self.arg[i])==vargrouptype:
                        g=True
                        lg=lg+1
                        arggroup[i]=var()
                if g:
                    grp = lazyset(obj)[*arggroup]
                    res = lazyset()
                    for el in grp:
                        k=0
                        arggroup1=[var() for a in range(len(arggroup))]
                        for i in range(len(arggroup)):
                            if type(arggroup[i])==vartype:
                                if lg>1:
                                    arggroup1[i]=el[k]
                                else:
                                    arggroup1[i]=el
                                k=k+1
                        grp1=lazyset(obj)[*arggroup1]
                        b=[]
                        for i in range(len(arggroup1)):
                            if type(arggroup1[i])==vartype:
                                b.append([])
                            else:
                                b.append(arggroup1[i])
                        for a in grp1:
                            for i in range(len(a)):
                                if type(arggroup[i])!=vartype:
                                    b[i].append(a[i])
                        for i in range(len(b)):
                            if type(b[i])==list:
                                b[i]=tuple(b[i])
                        b=tuple(b)
                        res.add(b)
                    obj=res
                # Формирование сигнатуры условий без учета None
                for i in range(min(len(self.arg),lenexample)):
                    if self.arg[i]!=None:
                        sign.append(i)
                # Формирование списка условий
                for i in range(len(self.arg)):
                    if self.arg[i]!=None:
                        if callable(self.arg[i]):
                            func.append(self.arg[i])
                        # Создание функций - условий по заданным образцам
                        else:
                            if i<lenexample:
                                v=var()
                                func.append(v==self.arg[i])
                if lenexample==1:
                    A = {(el,) for el in obj}
                else:
                    A = {tuple(el[i] for i in sign) for el in obj}
                B=multset()
                # Проверки выборок
                for el in A:
                    f=True
                    # Проверки основных условий
                    for i in range(min(len(func),len(sign))):
                        if type(func[i])==funcanytype or type(func[i])==funcalltype:
                            if not(func[i](el[i])()):
                                f=False
                                break
                        elif type(func[i]) not in [vartype,lazyindex,lazyattr] and type(func[i]) not in agrfunctypes and not(func[i](el[i])): 
                            f=False
                            break
                    # Одинаковым переменным в выборках соответствуют одинаковые значения:
                    if f:
                        argname=[]
                        for i in range(lenexample):
                            if self.arg[i]!=None:
                                argname.append(self.arg[i])
                        mask=[True]*len(argname)
                        for i in range(len(argname)):
                            for j in range(i+1,len(argname)):
                                if argname[i] is argname[j]:
                                    mask[j]=False
                                    if el[i]!=el[j]:
                                        f=False
                                        break
                            if not(f):
                                break
                    # проверки дополнительных условий
                    if f:
                        
                        for i in range(len(sign),len(func)):            
                            S=func[i].createsign()
                            for j in range(len(S)):
                                for k in range(len(sign)):
                                    if S[j] is self.arg[sign[k]]:
                                        S[j](el[k])
                            if not(func[i]()):
                                f=False
                                break
                    # проекция - если выбирается индекс или атрибут, подменить элемент его составляющей
                    if f:
                        el=list(el)
                        for i in range(len(sign)):
                            if type(self.arg[sign[i]]) in [lazyindex,lazyattr] or self.arg[sign[i]] in calcfunclist: # calcfunclist вероятно не работает
                                #el[i]=self.arg[sign[i]](el[i])
                                xx=self.arg[sign[i]](el[i])
                                if type(xx)!=bool:
                                    el[i]=xx
                        el=tuple(el)
                    # Удаление дублирующих атрибутов
                    if f:
                        ex = tuple(el[i] for i in range(len(el)) if mask[i])
                    # добавление конструируемых атрибутов
                    if f:
                        ex = list(ex)
                        for i in range(lenexample,len(self.arg)):
                            if type(self.arg[i]) not in [expr,lazyindex,lazyattr,vartype] and self.arg[i] not in calcfunclist: # calcfunclist вероятно не работает
                                ex.append(self.arg[i])
                            elif type(self.arg[i])==vartype:
                                for j in range(len(sign)):
                                    if self.arg[i] is self.arg[sign[j]]:
                                        ex.append(el[j])
                            elif type(self.arg[i])==expr and self.arg[i].op not in ["<","<=","==",">=",">","!="] or type(self.arg[i]) in [lazyindex,lazyattr] or self.arg[i] in calcfunclist:
                                S=self.arg[i].createsign()
                                for j in range(len(S)):
                                    for k in range(len(sign)):
                                        if S[j] is self.arg[sign[k]]:
                                            S[j](el[k])
                                aa = self.arg[i]() #последнее условие с calculus очевидно не работает, поэтому проверка:
                                if type(aa) is not bool:
                                    ex.append(aa)
                        ex=tuple(ex)
                    # помещение кортежа в результат:
                    if f:
                        if len(ex)==1:
                            ex=ex[0]
                        B.add(ex)
                
                #пробуем преобразовать результат в тип исходной коллекции:
                f=False
                if len(B)>0 and not(g):    
                    for b in B:
                        exampleres=b
                        break
                    if exampleres in obj:
                        f=True
                    elif hasattr(exampleres,"__iter__") and hasattr(example,"__iter__") and hasattr(exampleres,"__len__") and hasattr(example,"__len__") and len(exampleres)==len(example) and not(hasattr(example,"qrcls")):
                        f=all(type(el[0])==type(el[1]) for el in zip(exampleres,example))
                        if type(example)(exampleres) in obj:
                            f=True
                            B=(type(example)(b) for b in B)
                if f and not(g):
                    return createcoll(obj,B)
                else:
                    return multset(B)
                
                return multset(B)
        # Числовой индекс или срез
        else:
            # индекс из истин и лжи
            if type(self.arg)!=int and isbool(self.arg):
                return selection(obj,self.arg)
            # Числовой индекс или срез
            else:
                if hasattr(obj,"__getitem__"):
                    return obj.__getitem__(self.arg)
                elif hasattr(obj,"__dict__"):
                    return list(obj.__dict__.values())[self.arg]
                return obj.__getitem__(self.arg)
    
    #общий индекс из индексов аргументов при декартовом произведении
    def __pow__(self,other):
        if type(other)==lazyindex:
            return (self.obj ** other.obj)[self.arg + other.arg]
        else:
            return super().__pow__(other)
    def __ior__(self,other):
        L=reccheck(self.obj,other)
        if len(L)>0:
            other.recstart=True
            other.recparam=L
        R = indpropagation(self,other)
        return R

    

#проверка на наличие рекурсии
def reccheck(A,B,L=None):
    if L==None:
        L=[]
    if type(B)==expr:
        L = reccheck(A,B.__dict__["arg1"],L)
        L = reccheck(A,B.__dict__["arg2"],L)
    elif type(B)==lazyindex or type(B)==lazyattr:
        L = reccheck(A,B.__dict__["obj"],L)
    elif type(B)==vartype:
        if A is B:
            L.append(B)
    return L

#перестановка местами элементов кортежа
@lazyfunc
def subst(R,P):
    return ({tuple(el[i] for i in P) for el in R()})

#проталкивание левого индекса внутрь правого выражения
def indpropagation(self,other):
        if type(other)==lazyindex and (type(other.arg) is tuple) and (type(self.arg) is tuple):
            ind=[]
            for i in range(len(other.arg)):
                f=True
                for j in range(i):
                    if other.arg[i] is other.arg[j]:
                        f=False
                        break
                if f:
                    ind.append(other.arg[i])
            for i in range(len(ind)):
                f=True
                for j in range(len(self.arg)):    
                    if ind[i] is self.arg[j]:
                        f=False
                        break
                if f:
                    ind[i]=None
            R=other[*ind]
            # формирование подстановки
            ind1 = []
            for i in range(len(ind)):
                if ind[i]!=None:
                    ind1.append(ind[i])
            P=[]
            for i in range(len(self.arg)):
                for j in range(len(ind1)):
                    if self.arg[i] is ind1[j]:
                        P.append(j)
                        break
            #return R
            return subst(R,P)
        elif type(other)==expr and other.op=="|":
            other.arg1=indpropagation(self,other.arg1)
            other.arg2=indpropagation(self,other.arg2)
            return other
        elif type(other)==vartype:
            return other[self.arg]
        else:
            return other[self.arg]  



        
#Ленивая переменная    
@multiconstr
class var(expr,calculus):
    def __init__(self,value=None):
        self.value=value
        #self.addgetitem()
    def __call__(self,*args):
        if len(args)==0:
            return self.value
        else:
            self.value=args[0]
            #self.addgetitem()
            return self.value
    # Функция - попытка добавить итератор к обычной коллекции - перебор её атрибутов.
    def addgetitem(self):
        if not(hasattr(self.value,"__iter__")) and not(hasattr(self.value,"__getitem__")) and hasattr(self.value,"__dict__"):
            K=list(self.value.__dict__.keys())
            setattr(type(self.value),"__iter__", lambda self : iter(list(self.__dict__[k] for k in K)))
            setattr(type(self.value),"__next__", lambda self : next(list(self.__dict__[k] for k in K)))
            
    #добавление переменной в сигнатуру функции из ленивого выражения
    def createsign(self,L=None):
        if L==None:
            L=[]
        f = True
        for el in L:
            if self is el:
                f = False
        if f:
            L.append(self)
        return L
    def add(self,value):
        if hasattr(self.value,"add"):
            self.value.add(value)
        else:
            self.value.append(value)
    def append(self,value):
        if hasattr(self.value,"append"):
            self.value.append(value)
        else:
            self.value.add(value)
    def __setitem__(self,ind,value):
        self(value)
    def __deepcopy__(self,memo):
        my_copy = type(self)()
        memo[id(self)] = my_copy
        my_copy.value = deepcopy(self.value, memo)
        return my_copy
    def __iter__(self):
        if hasattr(self.value,"__iter__"):
            return iter(self.value)
        elif hasattr(self.value,"__dict__"):
            return iter(list(self.value.__dict__[k] for k in self.value.__dict__))
    

#используемые для сравнения типы данных  
funcanytype = type(calculus.Any(var(),var()==5))
funcalltype = type(calculus.All(var(),var()==5))
vartype = type(var())
vargrouptype = type(var().group())
simpletypes = [int,float,str]
#agrfunctypes = [type(var().sum()),type(var().len()),type(var().min()),type(var().max())]
agrfunctypes = [type(var().sum()),type(var().len()),type(var().min()),type(var().max()),type(var().avg()),type(var().monadsum()),type(var().monadlen()),type(var().monadmin()),type(var().monadmax()),type(var().monadavg())]

#множество с операциями декартова произведения      
class multset(set):
    def __mul__(self,other):
        R=set()
        # попытка присоединения кортежей справа
        for el in self:
            exL=el
            if type(exL)==tuple:
                exa=exL[0]
                for el in other:
                    exb=el
                    break
                if type(exa)==type(exb):
                    return self.specialmult(other)
                else:
                    break
        # попытка присоединения кортежей слева
        for el in other:
            exL=el
            if type(exL)==tuple:
                exb=exL[0]
                for el in self:
                    exa=el
                    break
                if type(exa)==type(exb):
                    return self.specialmultleft(other)
                else:
                    break
        # декартово произведение
        for a in self:
            for b in other:
                R.add((a,b))
        return multset(R)
    def specialmult(self,other):
        R=set()
        for a in self:
            for b in other:
                R.add((a+(b,)))
        return multset(R)
    def specialmultleft(self,other):
        R=set()
        for a in self:
            for b in other:
                R.add(((a,)+b))
        return multset(R)

    def __pow__(self,other):
        R=set()
        for a in self:
            for b in other:
                if type(a) in simpletypes:
                    a1=(a,)
                elif type(a) in [tuple,list]:
                    a1=a
                else:
                    a1=tuple(el for el in a)
                    #a1=tuple(a.__dict__.values())
                if type(b) in simpletypes:
                    b1=(b,)
                elif type(b) in [tuple,list]:
                    b1=b
                else:
                    b1=tuple(el for el in b)
                    #b1=tuple(b.__dict__.values())
                R.add(a1+b1)
        return multset(R)
    def __str__(self):
        f=True
        for el in self:
            if not(type(el)==tuple and len(el)==1):
                f=False
                break
        if f:
            return str({el[0] for el in self}) #вывод кортежа из одного элемента
        else:
            return str({el for el in self})

#создание ленивого множества с умножением (упаковка множества с умножением в ленивую переменную)
def lazyset(L=None):
    if L==None:
        L=set()
    M=multset(L)
    v=var()
    v(M)
    return v

#декоратор, добавляющий к классу экстент - ленивое множество
#(экземпляры автоматически помещаются в ленивое множество)
def queryclass(cls):
    class metaset(type):
        def __init__(self,*args):
            self.L=lazyset()
            self.qrcls=True
        def __repr__(self):
            return self.L.__repr__
        def __getitem__(self,i):
            return self.L[i]
        def __str__(self):
            return self.L.__str__()
        def __or__(self,other):
            if type(other)==vartype:
                return self.L | other()
            else:
                return self.L | other.L
        def __and__(self,other):
            return self.L & other.L
        def __mul__(self,other):
            return self.L * other.L
        def __sub__(self,other):
            return self.L - other.L
        def __xor__(self,other):
            return self.L ^ other.L
        def __pow__(self,other):
            if type(other)==expr:
                return self.L ** other
            else:
                return self.L ** other.L
        def __iter__(self):
            return self.L().__iter__()
        def __next__(self):
            return self.L().__next__()
    class newclass(cls,metaclass=metaset):
        def __init__(self,*args):
            super().__init__(*args)
            self.__class__.L.add(self)
            self.__class__.L.L.name=cls.__name__

        def __getattr__(self,attr):
            if attr in self.__dict__:
                return self.__dict__[attr]
            elif attr=="L":
                return tuple(self.__dict__.values())

        def __getitem__(self,ind):
            return list(self.__dict__.values())[ind]
        def __len__(self):
            return len(list(self.__dict__.values()))
    return newclass

#декоратор, добавляющий к классу экстент - любую коллекцию
def querycoll(coll=None,key=None):
    def queryclass(cls):
        class metaset(type):
            def __init__(self,*args):
                if coll==None:
                    self.L=lazyset()
                elif key==None:
                    self.L=var(coll())
                else:
                    self.L=var(coll([],key))
                self.qrcls=True
            def __repr__(self):
                return self.L.__repr__
            def __getitem__(self,i):
                return self.L[i]
            def __str__(self):
                return self.L.__str__()
            def __or__(self,other):
                if type(other)==vartype:
                    return self.L | other()
                else:
                    return self.L | other.L
            def __and__(self,other):
                return self.L & other.L
            def __mul__(self,other):
                return self.L * other.L
            def __sub__(self,other):
                return self.L - other.L
            def __xor__(self,other):
                return self.L ^ other.L
            def __pow__(self,other):
                if type(other)==expr:
                    return self.L ** other
                else:
                    return self.L ** other.L
            def __iter__(self):
                return self.L().__iter__()
            def __next__(self):
                return self.L().__next__()
        class newclass(cls,metaclass=metaset):
            def __init__(self,*args):
                super().__init__(*args)
                self.__class__.L.add(self)
                self.__class__.L.L.name=cls.__name__

            def __getattr__(self,attr):
                if attr in self.__dict__:
                    return self.__dict__[attr]
                elif attr=="L":
                    return tuple(self.__dict__.values())
            def __getitem__(self,ind):
                return list(self.__dict__.values())[ind]
            def __len__(self):
                return len(list(self.__dict__.values()))
        return newclass
    return queryclass


#превращение функции в предикат
class queryfun:
    def __init__(self,f):
        self.f=f
        self.L=lazyset()
    def __call__(self,*args):
        r=self.f(*args)
        self.L.add((*args,r))
        return r
    def __str__(self):
        return str(self.L)
    def __getitem__(self,ind):
        F=True
        for i in range(len(ind)-1):
            if type(ind[i]) in [expr,lazyindex,lazyset,vartype]:
                F=False
                break
        if F:
            r=(self(*ind[:-1]))
            if ind[-1] not in [expr,lazyindex,lazyset,vartype]:
                return r==ind[-1]
            else:
                return lazyset({*(list(ind)[:-1]),r})
        else:
            return self.L.__getitem__(ind)
    def init(self,*args):
        for arg in product(*args):
            self(*arg)

# строка таблицы - предиката
def tablerow(header):
    class newclass:
        def __init__(self,lst):
            self.header=header
            self.L=lst
            self.qrcls=True
            # потенциально опасно, если будут изменяться значения атрибутов
            for i in range(len(header)):
                self.__dict__[header[i]]=self.L[i]
        def __getitem__(self,ind):
            return self.L[ind]
        def __getattr__(self,attr):
            if attr in self.__dict__:
                return self.__dict__[attr]
            elif attr in self.header:
                i=self.header.index(attr)
                return self.L[i]
        def __str__(self):
            return str(self.L)
        def __repr__(self):
            return str(self.L)
        def __len__(self):
            return len(list(self.L))
    return newclass


# таблица - предикат
@multiconstr
class table:
    def __init__(self,*args):
        self.L=lazyset()
        self.header = (args)
        self.rowclass =tablerow(self.header)
        self.allowfact = True
        self.terms=[]
        self.recstart=False
    def __call__(self,*args):
        if self.allowfact:
            if len(self.header)==0:
                if len(args)==0:
                    return self.L
                if len(args)==1:
                    self.L.add(args[0])
                else:
                    self.L.add(args)
                return args
            else:
                if len(args)!=0:
                    #el = tablerow(self.header,args)
                    el = self.rowclass(args)
                    self.L.add(el)
                    return el
                else:
                    return self.L
        else:
            n=len(self.L)
            while True:
                for el in self.realobj()():
                    self.L.add(el)
                if len(self.L)>n:
                    n=len(self.L)
                else:
                    break
            return self.L
    #подмена исходного множества на все добавленные и вычисленные
    def realobj(self):
        if self.allowfact:
            return self.L
        else:
            res = self.L
            for t in self.terms:
                res = res | t
            return res
    def __str__(self):
        if self.allowfact:
            return str(self.L)
        else:
            return str(self())
    def __getitem__(self,ind):
        return self.realobj()[ind]
    def __mul__(self,other):
        #if type(other)!=table:
        if type(other)!=type(table()):
            return self.realobj() * other
        else:
            return self.realobj() * other.realobj()
    def __pow__(self,other):
        #if type(other)!=table:
        if type(other)!=type(table()):
            return self.realobj() ** other
        else:
            return self.realobj() ** other.realobj()
    def __or__(self,other):
        #if type(other)!=table:
        if type(other)!=type(table()):
            return self.realobj() | other
        else:
            return self.realobj() | other.realobj()
    def __sub__(self,other):
        return self.realobj() - other
    def __xor__(self,other):
        return self.realobj() ^ other
    def __setitem__(self,ind,value):
        self.allowfact = False
        self.terms.append(value[ind])
        return self
    def __ior__(self,other):
        self.allowfact = False
        self.terms.append(other)
        return self
    def __iter__(self):
        return self.realobj()().__iter__()
    def __next__(self):
        return self.realobj()().__next__()

@lazyfunc
def packelements(L):
    return lazyset({(el,) for el in L})

@lazyfunc
def lazyrange(*args):
    fin=0
    if len(args)==1:
        start=0
        fin = args[0]
        cond=lambda x : x<fin
        func=lambda x : x+1
    elif len(args)==2:
        start = args[0]
        fin = args[1]
        if start < fin:
            cond=lambda x : x<fin
            func=lambda x : x+1
        else:
            cond=lambda x : x>fin
            func=lambda x : x-1
    elif len(args)==3 and type(args[2]) in [int,float]:
        start = args[0]
        fin = args[1]
        if start < fin:
            cond=lambda x : x<fin
        else:
            cond=lambda x : x>fin
        func=lambda x : x+args[2]
    elif len(args)==3:
        start = args[0]
        fin = args[1]
        if start < fin:
            cond=lambda x : x<fin
        else:
            cond=lambda x : x>fin
        func=args[2]
    else:
        #Для последовательностей типа чисел Фибоначчи
        L = list(args[:-2])
        fin = args[-2]
        if L[0] < fin:
            cond=lambda x : x<fin
        else:
            cond=lambda x : x>fin
        func=args[-1]
        n=len(args)-2
        while cond(L[-1]):
            r=func(*L[-n:])
            if cond(r):
                L.append(r)
            else:
                break
        return L
    #для обычных прогрессий
    n=start
    L=[]
    while cond(n):
        L.append(n)
        #yield n
        n=func(n)
    return L

#ИНСТРУМЕНТЫ ФУНКЦИОНАЛЬНОГО ПРОГРАММИРОВАНИЯ

# Карринг
def curry(f):
    def curry(f):
        return lambda *y: functor(lambda x: f(*y,x))
    if type(f)==expr:
        length=len(f.createsign())
    else:
        length = len(signature(f).parameters)
    for i in range(length-1):
        f=curry(f)
    return f

# Аппликативный функтор
class applicative:
    def __init__(self,coll):
        self.coll=coll
    def __call__(self,arg):
        #R=type(self.coll)(f(arg) for f in self.coll)
        if type(self.coll)!=set:
            R=type(self.coll)(f(arg) for f in self.coll)
        else:
            R=tuple(f(arg) for f in self.coll)
        app=False
        for el in R:
            if callable(el):
                app=True
                break
        if app:
            return applicative(R)
        else:
            return R
        #return type(self.coll)(f(arg) for f in self.coll)
    def __iter__(self):
        return iter(self.coll)


# Функтор, также работает как монада
class functor:
    def __init__(self,f):
        self.f=curry(f)
    def __call__(self,arg):
        while callable(arg):
            arg=arg()
        if not(hasattr(arg,"__iter__")):
            return self.f(arg)
        else:
            #R=(type(arg)(self(el) for el in arg))
            if type(arg)!=set:
                R=(type(arg)(self(el) for el in arg))
            else:
                R=(tuple(self(el) for el in arg))
            app=False
            for el in R:
                if callable(el):
                    app=True
                    break
            if app:
                return applicative(R)
            else:
                return R
    def __matmul__(self,other):
        return functor(lambda *args: self(other(*args)))

# Монада. Работает как f(x,y) -> f([...],[...])                
class monad:
    def __init__(self,f):
        self.f=functor(f)
    @lazyfunc
    def __call__(self,*args):
        R=self.f(args[0])
        for i in range(1,len(args)):
            R=R(args[i])
        res=var()
        res(R)
        return res
