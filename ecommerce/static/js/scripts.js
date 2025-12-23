var eleCabecalhoLogin = document.querySelector(".cabecalho__icone-login");
var eleInfosPerfil = document.querySelector(".cabecalho__informacoes-perfil");

if (eleCabecalhoLogin && eleInfosPerfil) {
  eleCabecalhoLogin.addEventListener("click", function (e) {
    e.stopPropagation();
    eleInfosPerfil.classList.toggle("cabecalho__informacoes-perfil--aberto");
  });

  document.addEventListener("click", function () {
    eleInfosPerfil.classList.remove("cabecalho__informacoes-perfil--aberto");
  });
}
