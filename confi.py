import array
import math
import os
import pygame

# Configurações de Tela e Desempenho
LARGURA = 600
ALTURA = 660
FPS = 60
TITULO = "Defensor Retrô - Arcade 8-Bit"
ARQUIVO_RECORDE = "recorde.txt"

# Paleta de Cores Retrô Neon
PRETO = (3, 3, 8)
FUNDO_HUD = (16, 17, 34)
BORDA_NEON = (42, 45, 90)
CIANO = (0, 245, 212)
MAGENTA = (255, 42, 133)
AMARELO = (255, 230, 0)
VERDE = (57, 255, 20)
ROSA = (255, 119, 255)
BRANCO = (244, 244, 248)
CINZA_TEXTO = (140, 146, 198)

# Parâmetros do Jogador e Partida
VIDAS_INICIAIS = 3
VELOCIDADE_JOGADOR = 330
VELOCIDADE_TIRO_JOGADOR = 540
COOLDOWN_TIRO = 0.28
TEMPO_INVULNERAVEL = 2.0

# Pontuação
PONTOS_ELITE = 40
PONTOS_MEDIO = 20
PONTOS_BASE = 10
PONTOS_OVNI = 300

# Matrizes Pixel Art (Sprites 8-Bit)
SPRITE_JOGADOR = [
    "00000100000",
    "00001110000",
    "00001110000",
    "01011111010",
    "01111111110",
    "11111111111",
    "11101110111",
    "10000000001",
]

SPRITES_INIMIGOS = {
    "elite": [
        [
            "00011000",
            "00111100",
            "01111110",
            "11011011",
            "11111111",
            "00100100",
            "01011010",
            "10100101",
        ],
        [
            "00011000",
            "00111100",
            "01111110",
            "11011011",
            "11111111",
            "01011010",
            "10000001",
            "01000010",
        ],
    ],
    "medio": [
        [
            "00100000100",
            "00010001000",
            "00111111100",
            "01101110110",
            "11111111111",
            "10111111101",
            "10100000101",
            "00011011000",
        ],
        [
            "00100000100",
            "10010001001",
            "10111111101",
            "11101110111",
            "11111111111",
            "01111111110",
            "00100000100",
            "01000000010",
        ],
    ],
    "base": [
        [
            "000011110000",
            "011111111110",
            "111111111111",
            "111001100111",
            "111111111111",
            "000110011000",
            "001101101100",
            "110000000011",
        ],
        [
            "000011110000",
            "011111111110",
            "111111111111",
            "111001100111",
            "111111111111",
            "001110011100",
            "011001100110",
            "001100001100",
        ],
    ],
}

SPRITE_OVNI = [
    "0000011111100000",
    "0001111111111000",
    "0011111111111100",
    "0110110110110110",
    "1111111111111111",
    "0011100110011100",
    "0001000000001000",
]


def criar_surface_pixel(matriz, escala, cor):
    """Converte uma matriz de 0s e 1s em uma Surface transparente com pixel art."""
    altura = len(matriz)
    largura = len(matriz[0])
    surface = pygame.Surface((largura * escala, altura * escala), pygame.SRCALPHA)

    for linha_idx, linha in enumerate(matriz):
        for col_idx, pixel in enumerate(linha):
            if pixel == "1":
                rect = pygame.Rect(
                    col_idx * escala, linha_idx * escala, escala, escala
                )
                pygame.draw.rect(surface, cor, rect)

    return surface


def carregar_recorde():
    if not os.path.exists(ARQUIVO_RECORDE):
        return 0
    try:
        with open(ARQUIVO_RECORDE, "r", encoding="utf-8") as arquivo:
            return int(arquivo.read().strip() or 0)
    except (ValueError, OSError):
        return 0


def salvar_recorde(valor):
    try:
        with open(ARQUIVO_RECORDE, "w", encoding="utf-8") as arquivo:
            arquivo.write(str(valor))
    except OSError:
        pass


class SintetizadorRetro:
    """Gera efeitos sonoros 8-bit proceduralmente sem depender de arquivos externos."""

    def __init__(self):
        self.ativo = True
        self.sons = {}
        try:
            self.sons["tiro"] = self._gerar_tom(880, 220, 0.10, "square", 0.18)
            self.sons["explosao"] = self._gerar_tom(180, 42, 0.20, "sawtooth", 0.22)
            self.sons["dano"] = self._gerar_tom(150, 35, 0.42, "sawtooth", 0.28)
            self.sons["ovni"] = self._gerar_tom(520, 1180, 0.18, "triangle", 0.20)
            self.sons["fase"] = self._gerar_tom(440, 880, 0.28, "square", 0.20)
            self.sons["gameover"] = self._gerar_tom(320, 95, 0.55, "sawtooth", 0.25)
        except Exception:
            self.sons = {}

    def _gerar_tom(self, freq_ini, freq_fim, duracao, onda="square", volume=0.2):
        taxa = 44100
        total_amostras = int(taxa * duracao)
        amostras = array.array("h")
        fase = 0.0

        for i in range(total_amostras):
            progresso = i / total_amostras
            freq = freq_ini + (freq_fim - freq_ini) * progresso
            envelope = (1.0 - progresso) * volume
            fase += (2.0 * math.pi * freq) / taxa

            if onda == "square":
                valor = 1.0 if math.sin(fase) >= 0 else -1.0
            elif onda == "sawtooth":
                valor = 2.0 * ((fase / (2.0 * math.pi)) % 1.0) - 1.0
            else:
                valor = math.sin(fase)

            amostras.append(int(valor * envelope * 32767))

        return pygame.mixer.Sound(buffer=amostras)

    def tocar(self, nome):
        if self.ativo and nome in self.sons:
            self.sons[nome].play()