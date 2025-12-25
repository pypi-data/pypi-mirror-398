from ._core._core import ncorpos_vi
import ncorpos_utilidades as nut

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
    ncorpos_vi.parametros(N, G, eps, modo, energia, angular, linear)
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
    ncorpos_vi.parametros_massas(distribuicao, regiao, intervalo, normalizadas)

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
    ncorpos_vi.parametros_posicoes(distribuicao, regiao, intervalo)

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
    ncorpos_vi.parametros_momentos(distribuicao, regiao, intervalo)

  def gerar (self, exibir=True):
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
    print()

    # Gera
    ncorpos_vi.gerar()

    # Salva
    self.massas = ncorpos_vi.massas_c
    self.posicoes = ncorpos_vi.posicoes_c
    self.momentos = ncorpos_vi.momentos_c

    # Calcula o estado do sistema  
    self.atualizar_estado()

    # se quiser exibir o estado
    if exibir: self.exibir_estado()

  def atualizar_estado (self):
    """
    Calcula os observaveis do sistema conforme o estado atual.
    """
    self.V = nut.energia_potencial(self.massas, self.posicoes, self.G, self.eps)
    self.T = nut.energia_cinetica(self.massas, self.momentos)
    self.E = self.V + self.T
    
    self.J = nut.momento_angular_total(self.posicoes, self.momentos)
    self.P = nut.momento_linear_total(self.momentos)

    self.I = nut.momento_inercia(self.massas, self.posicoes)
    self.D = nut.momento_dilatacao(self.posicoes, self.momentos)
    
    self.virial_Fq = nut.virial_potencial_amortecido(self.massas, self.posicoes, self.G, self.eps)
    self.virial = 2*self.T + self.virial_Fq

  def exibir_estado (self):
    print(f"\n> ESTADO ATUAL DO SISTEMA:\n")
    print(f"- Energia cinetica (T): \t {self.T}")
    print(f"- Energia potencial (V):\t {self.V} ")
    print(f"- Energia total (E):    \t {self.E}")
    print()
    print(f"- Momento angular total (J):\t {self.J}")
    print(f"- Momento linear total (P): \t {self.P}")
    print()
    print(f"- Momento de inercia (I):  \t {self.I}")
    print(f"- Momento de dilatacao (D):\t {self.D}")
    print()
    print(f"- Termo de virial (<F,q>):\t {self.virial_Fq}")
    print(f"- Virial (2*T + <F,q>):   \t {self.virial}")