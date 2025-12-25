from ._core._core import ncorpos_utilidades as nut

def energia_cinetica (massas, momentos):
  """
  Energia cinetica do sistema usando os momentos lineares.

  Parametros
  ----------
  massas : list | np.array
    Lista de massas das particulas.
  momentos : list | np.array
    Lista de momentos lineares das particulas.
  """
  return nut.py_energia_cinetica(massas, momentos)

def momento_angular_individual (posicao, momento):
  """
  Momento angular de um corpo.

  Parametros
  ----------
  posicao : list | np.array
    Posicao da particula
  momento : list | np.array
    Momento linear da particula
  """
  return nut.py_momento_angular_individual(posicao, momento)

def momento_angular_total (posicoes, momentos):
  """
  Momento angular total do sistema.
  
  Parametros
  ----------
  posicoes : list | np.array
    Posicoes das particulas
  momentos : list | np.array
    Momentos lineares das particulas
  """
  return nut.py_momento_angular_total(posicoes, momentos)

def energia_potencial (massas, posicoes, G:float=1.0, eps:float=0.0):
  """
  Energia potencial do sistema
  
  Parametros
  ----------
  massas : list | np.array
    Massas das particulas.
  posicoes : list | np.array
    Posicoes das particulas
  G : float = 1.0
    Constante de gravitacao universal
  eps : float = 0.0
    constante de amortecimento do potencial
  """
  return nut.py_energia_potencial(G, massas, posicoes, eps)

def energia_total (massas, posicoes, momentos, G:float=1.0, eps:float=0.0):
  """
  Energia total do sistema
  
  Parametros
  ----------
  massas : list | np.array
    Massas das particulas.
  posicoes : list | np.array
    Posicoes das particulas
  momentos : list | np.array
    Momentos lineares das particulas
  G : float = 1.0
    Constante de gravitacao universal
  eps : float = 0.0
    constante de amortecimento do potencial
  """
  return nut.py_energia_total(G, massas, posicoes, momentos, eps)

def momento_dilatacao (posicoes, momentos):
  """
  Momento de dilatacao do sistema, definido por
    D = \sum_{a=1}^N <q_a, p_a> = 2 I'(t),
  onde I(t) eh o momento de inercia do sistema.

  Parametros
  ----------
  posicoes : list | np.array
    Posicoes das particulas
  momentos : list | np.array
    Momentos lineares das particulas
  """
  return nut.py_momento_dilatacao(posicoes, momentos)

def momento_inercia (massas, posicoes):
  """
  Momento de inercia do sistema, definido por
    I = \sum_{a=1}^N m_a ||q_a||^2
  
  Parametros
  ----------
  massas : list | np.array
    Massas das particulas.
  posicoes : list | np.array
    Posicoes das particulas
  """
  return nut.py_momento_inercia(massas, posicoes)

def raio_meia_massa (massas, posicoes):
  """
  Raio de meia massa do sistema. Em um sistema com N particulas, eh definido pelo raio que compreende metade da massa total do sistema, considerando a margem de diferenca para cima.
  
  Parametros
  ----------
  massas : list | np.array
    Massas das particulas.
  posicoes : list | np.array
    Posicoes das particulas
  """
  return nut.py_raio_meia_massa(massas, posicoes)

def tempo_relaxacao_rh (massas, posicoes):
  """
  Calculo do tempo de relaxacao para o raio de meia massa do sistema. Sendo r_mh o raio de meia massa, eh definido por
    t_rh = c * sqrt(N * r_mh**3 / (G * M)),
  onde M eh a massa total do sistema e
    c = 0.138 * N / log(0.4 * N)
  
  Parametros
  ----------
  massas : list | np.array
    Massas das particulas.
  posicoes : list | np.array
    Posicoes das particulas

  Referencias
  -----------
  AARSETH, Sverre. Gravitational N-Body Simulations: Tools and Algorithms. Cambridge: Cambridge University Press, 2003.
  """
  return nut.py_tempo_relaxacao_rh(massas, posicoes)

def virial_potencial_amortecido (massas, posicoes, G:float=1.0, eps:float=0.0):
  """
  Termo \sum <F,q> que aparece ao se calcular a segunda derivada temporal do momento de inercia I(t):
    I''(t) = 2 * T(p) + \sum_{a=1}^N <F_a(q), q_a>,
  onde F_a(q) eh a forca aplicada sobre o corpo de indice `a`, considerando o amortecimento por `eps`.
  Se `eps=0.0`, o esse termo eh o proprio potencial newtoniano.
  
  Parametros
  ----------
  massas : list | np.array
    Massas das particulas.
  posicoes : list | np.array
    Posicoes das particulas
  G : float = 1.0
    Constante de gravitacao universal
  eps : float = 0.0
    Constante de amortecimento do potencial
  """
  return nut.py_virial_potencial_amortecido(G, massas, posicoes, eps)

def tensor_inercia_individual (massa, posicao):
  """
  Tensor de inercia de uma particula. Sendo v um vetor qualquer em R^3, o tensor de inercia I_a eh definido pelo operador
    I_a * v = m_a q_a x (q_a x v),
  onde x eh o produto vetorial no R^3.
  
  Parametros
  ----------
  massas : list | np.array
    Massas das particulas.
  posicoes : list | np.array
    Posicoes das particulas
  """
  return nut.py_tensor_inercia_individual(massa, posicao)

def tensor_inercia_geral (massas, posicoes):
  """
  Tensor de inercia geral do sistema. Eh dado pela soma dos tensores de inercia de todas as paticulas do sistema.
  
  Parametros
  ----------
  massas : list | np.array
    Massas das particulas.
  posicoes : list | np.array
    Posicoes das particulas
  """
  return nut.py_tensor_inercia_geral(massas, posicoes)

def centro_massas (massas, posicoes):
  """
  Centro de massas do sistema. Eh definido por
    r_cm = \sum_{a=1}^N m_a q_a / M,
  onde M eh a massa total do sistema.
  
  Parametros
  ----------
  massas : list | np.array
    Massas das particulas.
  posicoes : list | np.array
    Posicoes das particulas
  """
  return nut.py_centro_massas(massas, posicoes)

def momento_linear_total (momentos):
  """
  Momento linear total do sistema. Eh a soma de todos os momentos lineares do sistema.
  
  Parametros
  ----------
  momentos : list | np.array
    Momentosl ineares das particulas.
  """
  return nut.py_momento_linear_total(momentos)

def anisotropia_tensor_inercia (massas, posicoes):
  """
  Anisotropia do tensor de inercia geral do sistema. Sendo I o tensor de inercia geral e L1, L2, L3 seus autovalores (reais) em ordem decrescente, a anisotropia A eh definida por
    A = (L2 - L3)/L1
  
  Parametros
  ----------
  massas : list | np.array
    Massas das particulas.
  posicoes : list | np.array
    Posicoes das particulas
  """
  return nut.py_anisotropia_tensor_inercia(massas, posicoes)

def anisotropia_velocidades (massas, posicoes, momentos):
  """
  Anisotropia via velocidades radial e tangencial.
  
  Parametros
  ----------
  massas : list | np.array
    Massas das particulas.
  posicoes : list | np.array
    Posicoes das particulas
  momentos : list | np.array
    Momentos lineares das particulas
  """
  return nut.py_anisotropia_velocidades(massas, posicoes, momentos)