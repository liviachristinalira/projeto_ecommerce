from django.db import models
from django.contrib.auth.models import User
# Create your models here.

# Cliente: nome, email, telefone, usuario, id_sessao

class Cliente(models.Model):
    #id automaticamente
    nome = models.CharField(max_length=200, null=True, blank=True)
    email = models.CharField(max_length=200, null=True, blank=True)
    telefone = models.CharField(max_length=200, null=True, blank=True)
        #idsessao = salvamento de página sem login
    id_sessao = models.CharField(max_length=200, null=True, blank=True)
        #referencia a tabela de usuarios existente do django 
    usuario = models.OneToOneField(User, null=True, blank=True, on_delete= models.CASCADE)
        # OneToOneField = cada cliente só pode ter um usuario e visse-versa 

    def __str__ (self):
        return str(self.email)

#Categorias: nome (maasculino, feminino, infantil )

class Categoria(models.Model):
    nome = models.CharField(max_length=200, null=True, blank=True)
    slug = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return str(self.nome)

#Tipo: nome (blusa, calça)

class Tipo(models.Model):
    nome = models.CharField(max_length=200, null=True, blank=True)
    slug = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return str(self.nome)

#Produtos: imagem, nome, preco, status (ativo ou inativo), categoria, tipo 

class Produto (models.Model):
    imagem = models.ImageField(null= True, blank= True)
    nome = models.CharField(max_length=200, null=True, blank=True)
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.BooleanField(default=True) #padrão=ativo
    categoria = models.ForeignKey(Categoria, null=True, blank=True, on_delete=models.SET_NULL)
    tipo =  models.ForeignKey(Tipo, null=True, blank=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return f"Nome: {self.nome}, Categoria: {self.categoria}, Tipo: {self.tipo}, Preço: {self.preco}"
    
    def total_vendas(self):
        itens = ItensPedido.objects.filter(pedido__status=True, itemestoque__produto=self.id)
        total = sum([item.quantidade for item in itens])
        return total

class Cor(models.Model):
    nome = models.CharField(max_length=200, null=True, blank=True)
    codigo = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return str(self.nome)

#Itemestoque: produto, cor, tamanho, quantidade 
class ItemEstoque(models.Model):
    produto =  models.ForeignKey(Produto, null=True, blank=True, on_delete=models.SET_NULL)
    cor =  models.ForeignKey(Cor, null=True, blank=True, on_delete=models.SET_NULL)
    tamanho =  models.CharField(max_length=200, null=True, blank=True)
    quantidade = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.produto.nome}, Tamanho: {self.tamanho}, Cor: {self.cor.nome}"
    

#Endereco: rua, numero, complemento, cep, cidade, estado, cliente 
class Endereco (models.Model):
    rua = models.CharField (max_length=200, null=True, blank=True)
    numero = models.IntegerField(default=0)
    complemento = models.CharField(max_length=200, null=True, blank=True)
    cep = models.CharField(max_length=200, null=True, blank=True)
    cidade = models.CharField(max_length=200, null=True, blank=True)
    estado = models.CharField(max_length=200, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, null=True, blank=True, on_delete = models.SET_NULL)

    def __str__(self) -> str:
        return f"{self.cliente} - {self.rua} - {self.cidade}-{self.estado} - {self.cep}"

#Pedidos:  cliente, data_finaalizacao, status, id_transacao, endereco, ItensPedido

class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, null=True, blank=True, on_delete= models.SET_NULL)
    status = models.BooleanField(default=0)
    codigo_transacao = models.CharField(max_length=200, null=True, blank=True)
    endereco = models.ForeignKey(Endereco, null=True, blank=True, on_delete= models.SET_NULL)
    data_finalizacao = models.DateTimeField(null=True, blank=True)

    @property
    def quantidade_total (self): #soma dos itens pedido
        itens_pedido = ItensPedido.objects.filter(pedido__id=self.id)
        quantidade = sum( [item.quantidade for item in itens_pedido]  )
        return quantidade
    @property
    def preco_total (self):
        itens_pedido = ItensPedido.objects.filter(pedido__id=self.id)
        preco = sum( [item.preco_total for item in itens_pedido]  )
        return preco
    
    @property
    def itens(self):
        itens_pedido = ItensPedido.objects.filter(pedido__id=self.id)
        return itens_pedido

    def __str__(self):
        return f"Cliente: {self.cliente.email} - Id_pedido: {self.id}, - Status: {self.status}"
    
#ItensPedido: itemestoque, quantidade 

class ItensPedido(models.Model):
    itemestoque = models.ForeignKey(ItemEstoque, null=True, blank=True, on_delete=models.SET)
    quantidade = models.IntegerField(default=0) #que o usuario está comprando
    pedido = models.ForeignKey(Pedido, null=True, blank=True, on_delete=models.SET_NULL)

    @property
    def preco_total(self):
        return self.quantidade * self.itemestoque.produto.preco

    def __str__(self):
        return f"Id_Pedido: {self.pedido.id} - Produto: {self.itemestoque.produto.nome},{self.itemestoque.tamanho},{self.itemestoque.cor.nome}"

class Banner (models.Model):
    imagem = models.ImageField(null=True, blank=True)
    link_destino = models.CharField(max_length= 400, null=True, blank= True)
    status = models.BooleanField(default=True)

    def __str__ (self):
        return f"{self.link_destino} - Ativo: {self.status}"


