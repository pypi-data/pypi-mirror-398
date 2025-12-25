"""
Valores iniciais

Este pacote fornece rotinas para a geracao de valores iniciais para
problemas de N-corpos, e o seu condicionamento para obter sistemas
com integrais primeiras desejadas e/ou estado de equilibrio inicial.
"""
from ._core import valores_iniciais

class Gerador:
  """
  Gerador de valores iniciais.

  Parâmetros
  ----------
  N : int
    Quantidade de corpos
  G : float = 1.0
    Constante de gravitacao universal
  eps : float = 0.0
    Amortecedor do potencial  
  modo : str = "sorteio_ip_iterativo"
    Modo de sorteio. Disponiveis: sorteio, sorteio_ip_iterativo, sorteio_ip_direto, sorteio_aarseth, sorteio_aarseth_modificado.
  energia : float = 0.0
    Energia total do sistema desejada.
  angular : list = [0.0, 0.0, 0.0]
    Momento angular total do sistema desejado.
  linear : list = [0.0, 0.0, 0.0]
    Momento linear total do sistema desejado.
  """
  def __init__ (self, N:int, G:float=1.0, eps:float=0.0, modo:str="sorteio_ip_iterativo", energia:float=0.0, angular:list=[0.0,0.0,0.0], linear:list=[0.0,0.0,0.0]):
    self.configurar(N, G, eps, modo, energia, angular, linear)

  def configurar (self, N:int, G:float=1.0, eps:float=0.0, 
  modo:str="sorteio_ip_iterativo", energia:float=0.0, angular:list=[0.0,0.0,0.0], linear:list=[0.0,0.0,0.0]):
    """
    Gerador de valores iniciais.

    Parametros
    ----------
    N : int
      Quantidade de corpos
    G : float = 1.0
      Constante de gravitacao universal
    eps : float = 0.0
      Amortecedor do potencial  
    modo : str = "sorteio_ip_iterativo"
      Modo de sorteio. Disponiveis: sorteio, sorteio_ip_iterativo, sorteio_ip_direto, sorteio_aarseth, sorteio_aarseth_modificado.
    energia : float = 0.0
      Energia total do sistema desejada.
    angular : list = [0.0, 0.0, 0.0]
      Momento angular total do sistema desejado.
    linear : list = [0.0, 0.0, 0.0]
      Momento linear total do sistema desejado.
    """
    # Salva os valores
    self.N = N
    self.G = G
    self.eps = eps
    self.modo = modo
    self.energia = energia
    self.angular = angular
    self.linear = linear
    # Agora instancia tambem no fortran
    valores_iniciais.parametros(N, G, eps, modo, energia, angular, linear)
    self.configurar_massas()
    self.configurar_posicoes()
    self.configurar_momentos()

  def configurar_massas (self, intervalo:list=[1.0,1.0], normalizadas:bool=False):
    """
    Configuracao do gerador de massas.

    Parametros
    ----------
    intervalo : list = [1.0, 1.0]
      Intervalo para a geracao de massas com distribuicao uniforme.
      Se tiver medida zero (i.e. `intervalo=[x,x]`), entao todas as massas serao iguais a x. 
      Eh ignorado se `normalizadas=True`.
    
    normalizadas : bool = False
      Se esta opcao estiver ativada, todas as massas serao `1/N`.
    """
    # Parametros padrao
    distribuicao = "uniforme"
    regiao = "cubo"
    self.massas_parametros = {"intervalo": intervalo, "normalizadas": normalizadas}
    # Configurando no fortran
    valores_iniciais.parametros_massas(distribuicao, regiao, intervalo, normalizadas)

  def configurar_posicoes (self, distribuicao:str="uniforme", regiao:str="cubo", intervalo:list=[-10.0,10.0]):
    """
    Configuracao do gerador de posicoes.

    Parametros
    ----------
    distribuicao : str = "uniforme"
      Distribuicao para geracao de posicoes.
      Disponiveis: `uniforme`, `normal`, `cauchy`.

    regiao : str = "cubo"
      Regiao para geracao de posicoes.
      Disponiveis: `cubo`, `esfera`, `cobrinha`.

    intervalo : list = [-10.0, 10.0]
      Intervalo para a geracao de posicoes com a distribuicao desejada.
      Se o intervalo nao for centrado em zero e for feito o condicionamento,
      o centro de massas ainda assim sera passado para a origem.
    """
    if intervalo[0] == intervalo[1]:
      exit("O intervalo de posicoes precisa ter medida maior que zero!")

    self.posicoes_parametros = {
      "distribuicao": distribuicao,
      "regiao": regiao,
      "intervalo": intervalo
    }
    # Configurando no fortran
    valores_iniciais.parametros_posicoes(distribuicao, regiao, intervalo)

  def configurar_momentos (self, distribuicao:str="uniforme", regiao:str="cubo", intervalo:list=[-1.0,1.0]):
    """
    Configuracao do gerador de momentos lineares.

    Parametros
    ----------
    distribuicao : str = "uniforme"
      Distribuicao para geracao de momentos.
      Disponiveis: `uniforme`, `normal`, `cauchy`.

    regiao : str = "cubo"
      Regiao para geracao de momentos.
      Disponiveis: `cubo`, `esfera`, `cobrinha`.

    intervalo : list = [-1.0, 1.0]
      Intervalo para a geracao de momentos lineares com a distribuicao desejada.
      O condicionamento pode extrapolar o intervalo passado.
    """
    self.momentos_parametros = {
      "distribuicao": distribuicao,
      "regiao": regiao,
      "intervalo": intervalo
    }
    # Configurando no fortran
    valores_iniciais.parametros_momentos(distribuicao, regiao, intervalo)

  def gerar (self):
    """
    Geracao de valores iniciais.
    """
    print("Gerando valores iniciais com as seguintes configuracoes: ")
    print(f"N = {self.N} / G = {self.G} / eps = {self.eps} / modo = {self.modo}")
    print(f"Constantes de movimento: E = {self.energia} / J = {self.angular} / P = {self.linear}")
    
    print("\nMassas:")
    print(f" - intervalo = {self.massas_parametros['intervalo']}")
    print(f" - normalizadas = {self.massas_parametros['normalizadas']}")
    
    print("\nPosicoes:")
    print(f" - distribuicao = {self.posicoes_parametros['distribuicao']}")
    print(f" - regiao = {self.posicoes_parametros['regiao']}")
    print(f" - intervalo = {self.posicoes_parametros['intervalo']}")
    
    print("\nMomentos lineares:")
    print(f" - distribuicao = {self.momentos_parametros['distribuicao']}")
    print(f" - regiao = {self.momentos_parametros['regiao']}")
    print(f" - intervalo = {self.momentos_parametros['intervalo']}")

    # Gera
    valores_iniciais.gerar()

    # Salva
    self.massas = valores_iniciais.massas_c
    self.posicoes = valores_iniciais.posicoes_c
    self.momentos = valores_iniciais.momentos_c