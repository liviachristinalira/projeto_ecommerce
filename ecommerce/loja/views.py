from django.shortcuts import render, redirect
from .models import *
import uuid
from  .utils import filtro_produtos, preco_min_max, ordenar_produtos
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required

from django.core.validators import validate_email
from django.core.exceptions import ValidationError


# Create your views here.
def homepage(request):
    banners = Banner.objects.filter(status=True)
    context = {"banners": banners}
    return render(request, 'homepage.html', context)

def loja(request, filtro=None):
    produtos = Produto.objects.filter(status=True) #queryset = resultado da busca do BD
    produtos = filtro_produtos(produtos,filtro)
    
    # aplicar os filtros do formulario 
    if request.method == "POST":
        dados = request.POST.dict()
        produtos = produtos.filter(preco__gte=dados.get("preco_minimo"), preco__lte=dados.get("preco_maximo"))
        if "tamanho" in dados:
            itens = ItemEstoque.objects.filter(produto__in=produtos, tamanho=dados.get("tamanho"))
            ids_produtos = itens.values_list("produto", flat=True).distinct()
            produtos = produtos.filter(id__in=ids_produtos)

        if "tipo" in dados:
            produtos = produtos.filter(tipo__slug=dados.get("tipo"))

        if "categoria" in dados:
            produtos = produtos.filter(categoria__slug=dados.get("categoria"))

    itens = ItemEstoque.objects.filter(quantidade__gt=0, produto__in=produtos)
    tamanhos = itens.values_list("tamanho", flat=True).distinct()
    ids_categorias = produtos.values_list("categoria", flat=True).distinct()
    categorias = Categoria.objects.filter(id__in=ids_categorias)
    minimo, maximo = preco_min_max(produtos)

    ordem = request.GET.get("ordem", "menor-preco")
    produtos = ordenar_produtos(produtos, ordem)



    context = {"produtos": produtos, "minimo":minimo, "maximo":maximo, "tamanhos":tamanhos, "categorias": categorias}
    return render(request, 'loja.html', context)

def ver_produto(request, id_produto, id_cor= None):

    tem_estoque = False
    cores = {}
    tamanhos = {}
    cor_selecionada = None
    if id_cor:
        cor_selecionada = Cor.objects.get(id=id_cor)

    produto = Produto.objects.get(id=id_produto)
    itens_estoque = ItemEstoque.objects.filter(produto=produto, quantidade__gt=0)
    
    if len(itens_estoque) > 0:
        tem_estoque = True
        cores = {item.cor for item in itens_estoque}
        if id_cor:
            itens_estoque = ItemEstoque.objects.filter(produto=produto, quantidade__gt=0, cor__id=id_cor)
            tamanhos = {item.tamanho for item in itens_estoque}
    similares = Produto.objects.filter(categoria__id=produto.categoria.id, tipo__id=produto.tipo.id).exclude(id=produto.id)[:4]
    context = {"produto": produto, "tem_estoque": tem_estoque, "cores": cores, "tamanhos": tamanhos, 
               "cor_selecionada": cor_selecionada, "similares": similares}
    return render(request, "ver_produto.html", context)


def adicionar_carrinho(request, id_produto): 
    if request.method == "POST" and id_produto:

        dados = request.POST.dict()
        tamanho = dados.get("tamanho")
        id_cor = dados.get("cor")

        if not tamanho:
            return redirect('loja')
        # pegar o cliente 
        resposta = redirect('carrinho')

        if request.user.is_authenticated:
             cliente = request.user.cliente
        else:
            if request.COOKIES.get("id_sessao"):
                id_sessao = request.COOKIES.get("id_sessao")
                id_sessao = str(uuid.uuid4())
                resposta.set_cookie(key = "id_sessao", value= id_sessao, max_age= 60*60*24*30) 
            cliente, cliente_criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
            
            
        # criar o pedido ou pegar o pedido que está em aberto 
        pedido, pedido_criado = Pedido.objects.get_or_create(cliente=cliente, status=False)
        item_estoque = ItemEstoque.objects.get(produto__id=id_produto, tamanho=tamanho, cor__id=id_cor)
        item_pedido, item_criado = ItensPedido.objects.get_or_create(itemestoque=item_estoque, pedido=pedido)
        item_pedido.quantidade += 1
        item_pedido.save()
        return resposta    
    else: 
        return redirect ('loja')

def remover_carrinho(request, id_produto):
    if request.method == "POST" and id_produto:

        dados = request.POST.dict()
        tamanho = dados.get("tamanho")
        id_cor = dados.get("cor")

        if not tamanho:
            return redirect('loja')
        
        # pegar o cliente 
        if request.user.is_authenticated:
             cliente = request.user.cliente
        else:
            if request.COOKIES.get("id_sessao"):
                id_sessao = request.COOKIES.get("id_sessao") 
                cliente, cliente_criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
            else:
                return redirect('loja')
        
        # criar o pedido ou pegar o pedido que está em aberto 
        pedido, pedido_criado = Pedido.objects.get_or_create(cliente=cliente, status=False)
        item_estoque = ItemEstoque.objects.get(produto__id=id_produto, tamanho=tamanho, cor__id=id_cor)
        item_pedido, item_criado = ItensPedido.objects.get_or_create(itemestoque=item_estoque, pedido=pedido)
        item_pedido.quantidade -= 1
        item_pedido.save()

        if item_pedido.quantidade <=0:
            item_pedido.delete()
        return redirect('carrinho')
        
    else: 
        return redirect ('loja')


def carrinho(request):
    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        
        if request.COOKIES.get("id_sessao"):
           id_sessao = request.COOKIES.get("id_sessao") 
           cliente, cliente_criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
        else:
            context = {"cliente_existe": False, "itens_pedido": None, "pedido": None}
            return render(request, 'carrinho.html', context)

    pedido, pedido_criado = Pedido.objects.get_or_create(cliente=cliente, status=False)
    itens_pedido = ItensPedido.objects.filter(pedido=pedido)

    context = {"itens_pedido": itens_pedido, "pedido":pedido, "cliente_existe":True}
    return render(request, 'carrinho.html', context)

def checkout(request):
    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        
        if request.COOKIES.get("id_sessao"):
           id_sessao = request.COOKIES.get("id_sessao") 
           cliente, cliente_criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
        else:
            
            return redirect('loja')

    pedido, pedido_criado = Pedido.objects.get_or_create(cliente=cliente, status=False)
    enderecos = Endereco.objects.filter(cliente=cliente)

    context = {"pedido":pedido, "enderecos":enderecos}
    return render(request, 'checkout.html', context)

def adicionar_endereco(request):
    if request.method == "POST":
        #tratar o envio do formulario 
        if request.user.is_authenticated:
            cliente = request.user.cliente
        else:
            if request.COOKIES.get("id_sessao"):
                id_sessao = request.COOKIES.get("id_sessao") 
                cliente, cliente_criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
            else:
                return redirect('loja')
        dados = request.POST.dict()
        endereco = Endereco.objects.create(cliente=cliente, rua=dados.get("rua"), 
                                           numero= int(dados.get("numero")), estado= dados.get("estado"), 
                                           cidade = dados.get("cidade"), cep = dados.get("cep"), 
                                           complemento = dados.get("complemento"))
        endereco.save()
        return redirect("checkout")
    
    else: 
        context = {}
    return render(request, 'adicionar_endereco.html', context)

@login_required
def minha_conta(request):
    return render(request, 'usuario/minha_conta.html')

@login_required
def minha_conta(request):
    erro = None
    alterado = False
    if request.method == "POST":
        dados = request.POST.dict()
        if "senha_atual" in dados:
            # esta modificando senha
            senha_atual = dados.get("senha_atual")
            nova_senha = dados.get("nova_senha")
            nova_senha_confirmacao = dados.get("nova_senha_confirmacao")
            if nova_senha == nova_senha_confirmacao:
                # verificar se a senha atual ta certa
                usuario = authenticate(request, username=request.user.email, password=senha_atual)
                if usuario:
                    usuario.set_password(nova_senha)
                    usuario.save()
                    alterado = True
                else:
                    erro = "senha_incorreta"
            else:
                erro = "senhas_diferentes"
        elif "email" in dados:
            email = dados.get("email")
            telefone = dados.get("telefone")
            nome = dados.get("nome")
            if email != request.user.email:
                usuarios = User.objects.filter(email=email)
                if len(usuarios) > 0:
                    erro = "email_existente"
            if not erro:
                cliente = request.user.cliente
                cliente.email = email
                request.user.email = email
                request.user.username = email
                cliente.nome = nome
                cliente.telefone = telefone
                cliente.save()
                request.user.save()
                alterado = True
        else:
            erro = "formulario_invalido"
    context = {"erro": erro, "alterado": alterado}
    return render(request, 'usuario/minha_conta.html', context)

@login_required
def meus_pedidos(request):

    cliente = request.user.cliente 
    pedidos = Pedido.objects.filter(status = True, cliente=cliente).order_by("data_finalizacao")
    context = {"pedidos":pedidos}
    return render(request, "usuario/meus_pedidos.html", context)

def fazer_login(request):
    erro = False

    if request.user.is_authenticated:
        return redirect('loja')
    
    if request.method == "POST":
        dados = request.POST.dict()
        if "email" in dados and "senha" in dados:
            # fazer o login e autenticação
            email = dados.get("email")
            senha = dados.get("senha")
            usuario = authenticate(request, username=email, password=senha)
            
            if usuario:
                login(request, usuario)
                return redirect('loja')
            else:
                erro = True
        else:
            erro = True

    context = {"erro":erro}
    return render(request, 'usuario/login.html', context)

def criar_conta(request):
    erro = None
    if request.user.is_authenticated:
        return redirect("loja")
    if request.method == "POST":
        dados = request.POST.dict()
        if "email" in dados and "senha" in dados and "confirmacao_senha" in dados:
            #criar conta
            email = dados.get("email")
            senha = dados.get("senha")
            confirmacao_senha = dados.get("confirmacao_senha")

            try:
                validate_email(email)
            except ValidationError:
                erro = "email_invalido"
            if senha == confirmacao_senha:
                #criar conta
                usuario, usuario_criado = User.objects.get_or_create(username=email, email=email)
                if not usuario_criado:
                    erro = "usuario_existente"
                else:
                    usuario.set_password(senha)
                    usuario.save()

                    #fazer o login 
                    usuario = authenticate(request, username=email, password=senha)
                    login(request, usuario)

                    #criar o cliente
                    #verificar o id_sessão com cookies 
                    if request.COOKIES.get("id_sessao"):
                        id_sessao = request.COOKIES.get("id_sessao") 
                        cliente, cliente_criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
                    else:
                        cliente, cliente_criado = Cliente.objects.get_or_create(email=email)
                    cliente.usuario = usuario
                    cliente.email = email 
                    cliente.save()
                    return redirect("loja") 
                
            else:
                erro = "senhas_diferentes"
        else:
            erro = "preenchimento"
    context = {"erro":erro}
    return render(request, "usuario/criar_conta.html", context)

@login_required
def fazer_logout(request):
    logout(request)
    return redirect("fazer_login")

# TODO sempre que o usuario criar uma conta no site, ele será atrelado a um cliente (concluído)
# TODO criar uma conta do usuario colocar o username dele igual ao email (concluído!)

def finalizar_pedido(request):
    if request.method != "POST":
        return redirect('checkout')

    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        if request.COOKIES.get("id_sessao"):
            id_sessao = request.COOKIES.get("id_sessao")
            cliente = Cliente.objects.filter(id_sessao=id_sessao).first()
        else:
            return redirect('loja')

    pedido = Pedido.objects.filter(cliente=cliente, status=False).first()

    if not pedido:
        return redirect('carrinho')

    # FINALIZA O PEDIDO
    pedido.status = True
    pedido.save()

    return redirect('meus_pedidos')
