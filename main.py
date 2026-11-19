import math
import random
import sys
import pygame
import confi
from inimigos import HordaInimigos
from jogador import Barricada, Jogador


class Particula:
    def __init__(self, x, y, cor):
        angulo = random.uniform(0, math.pi * 2)
        velocidade = random.uniform(50, 210)
        self.x = float(x)
        self.y = float(y)
        self.vx = math.cos(angulo) * velocidade
        self.vy = math.sin(angulo) * velocidade
        self.tamanho = random.choice([3, 4, 5])
        self.vida = random.uniform(0.30, 0.60)
        self.cor = cor

    def atualizar(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vida -= dt

    def desenhar(self, tela):
        pygame.draw.rect(
            tela, self.cor, (int(self.x), int(self.y), self.tamanho, self.tamanho)
        )


class Jogo:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        self.tela = pygame.display.set_mode((confi.LARGURA, confi.ALTURA))
        pygame.display.set_caption(confi.TITULO)
        self.relogio = pygame.time.Clock()

        # Fontes estilo terminal/arcade
        self.fonte_titulo = pygame.font.SysFont("consolas", 40, bold=True)
        self.fonte_media = pygame.font.SysFont("consolas", 20, bold=True)
        self.fonte_hud = pygame.font.SysFont("consolas", 16, bold=True)
        self.fonte_pequena = pygame.font.SysFont("consolas", 13, bold=True)

        self.som = confi.SintetizadorRetro()
        self.scanlines = self._criar_scanlines()
        self.icone_vida = confi.criar_surface_pixel(
            confi.SPRITE_JOGADOR, escala=2, cor=confi.MAGENTA
        )

        # Estrelas do fundo
        self.estrelas = [
            {
                "x": random.randint(0, confi.LARGURA),
                "y": random.randint(0, confi.ALTURA),
                "tam": random.choice([2, 2, 3]),
                "vel": random.uniform(20, 65),
                "cor": random.choice([confi.BRANCO, confi.CIANO, confi.AMARELO]),
            }
            for _ in range(65)
        ]

        # Estado da partida
        self.estado = "INICIO"  # INICIO | JOGANDO | PAUSADO | GAMEOVER
        self.pontos = 0
        self.recorde = confi.carregar_recorde()
        self.novo_recorde = False
        self.vidas = confi.VIDAS_INICIAIS
        self.fase = 1
        self.tremor_tela = 0.0

        self.jogador = Jogador()
        self.barricada = Barricada()
        self.horda = HordaInimigos()
        self.projeteis_jogador = []
        self.projeteis_inimigos = []
        self.particulas = []

    def _criar_scanlines(self):
        surface = pygame.Surface((confi.LARGURA, confi.ALTURA), pygame.SRCALPHA)
        for y in range(48, confi.ALTURA, 4):
            pygame.draw.line(surface, (0, 0, 0, 75), (0, y), (confi.LARGURA, y))
        return surface

    def iniciar_partida(self):
        self.estado = "JOGANDO"
        self.pontos = 0
        self.novo_recorde = False
        self.vidas = confi.VIDAS_INICIAIS
        self.fase = 1
        self.tremor_tela = 0.0

        self.jogador.resetar()
        self.barricada.criar()
        self.horda = HordaInimigos()
        self.horda.criar_onda(self.fase)
        self.projeteis_jogador.clear()
        self.projeteis_inimigos.clear()
        self.particulas.clear()

    def adicionar_pontos(self, valor):
        self.pontos += valor
        if self.pontos > self.recorde:
            self.recorde = self.pontos
            self.novo_recorde = True
            confi.salvar_recorde(self.recorde)

    def gerar_explosao(self, x, y, cor, quantidade=14):
        for _ in range(quantidade):
            self.particulas.append(Particula(x, y, cor))

    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_m:
                    self.som.ativo = not self.som.ativo

                if self.estado in ("INICIO", "GAMEOVER"):
                    if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.iniciar_partida()

                elif self.estado == "JOGANDO":
                    if evento.key == pygame.K_p:
                        self.estado = "PAUSADO"

                elif self.estado == "PAUSADO":
                    if evento.key in (pygame.K_p, pygame.K_RETURN):
                        self.estado = "JOGANDO"

    def atualizar(self, dt):
        # Fundo estrelado contínuo
        for estrela in self.estrelas:
            estrela["y"] += estrela["vel"] * dt
            if estrela["y"] > confi.ALTURA:
                estrela["y"] = 48
                estrela["x"] = random.randint(0, confi.LARGURA)

        if self.estado != "JOGANDO":
            return

        if self.tremor_tela > 0:
            self.tremor_tela -= dt

        teclas = pygame.key.get_pressed()
        self.jogador.atualizar(dt, teclas, self.projeteis_jogador, self.som)
        self.horda.atualizar(dt, self.fase, self.projeteis_inimigos)

        # Atualiza projéteis
        for tiro in self.projeteis_jogador:
            tiro.atualizar(dt)
        self.projeteis_jogador = [
            t for t in self.projeteis_jogador if not t.fora_da_tela()
        ]

        for tiro in self.projeteis_inimigos:
            tiro.atualizar(dt)
        self.projeteis_inimigos = [
            t for t in self.projeteis_inimigos if not t.fora_da_tela()
        ]

        # Colisões dos tiros do jogador
        for i in range(len(self.projeteis_jogador) - 1, -1, -1):
            tiro = self.projeteis_jogador[i]
            acertou = False

            if self.barricada.verificar_colisao(tiro.rect):
                acertou = True

            if not acertou and self.horda.ovni is not None:
                if tiro.rect.colliderect(self.horda.ovni.rect):
                    self.adicionar_pontos(self.horda.ovni.pontos)
                    self.som.tocar("ovni")
                    self.gerar_explosao(
                        self.horda.ovni.rect.centerx,
                        self.horda.ovni.rect.centery,
                        confi.ROSA,
                        22,
                    )
                    self.horda.ovni = None
                    acertou = True

            if not acertou:
                for j in range(len(self.horda.lista) - 1, -1, -1):
                    inimigo = self.horda.lista[j]
                    if tiro.rect.colliderect(inimigo.rect):
                        self.adicionar_pontos(inimigo.pontos)
                        self.som.tocar("explosao")
                        self.gerar_explosao(
                            inimigo.rect.centerx, inimigo.rect.centery, inimigo.cor, 12
                        )
                        self.horda.lista.pop(j)
                        acertou = True
                        break

            if acertou:
                self.projeteis_jogador.pop(i)

        # Colisões dos tiros inimigos
        for i in range(len(self.projeteis_inimigos) - 1, -1, -1):
            tiro = self.projeteis_inimigos[i]
            acertou = False

            if self.barricada.verificar_colisao(tiro.rect):
                acertou = True

            if not acertou and tiro.rect.colliderect(self.jogador.rect):
                acertou = True
                if self.jogador.sofrer_dano():
                    self.vidas -= 1
                    self.tremor_tela = 0.35
                    self.som.tocar("dano")
                    self.gerar_explosao(
                        self.jogador.rect.centerx,
                        self.jogador.rect.centery,
                        confi.AMARELO,
                        24,
                    )
                    if self.vidas <= 0:
                        self.estado = "GAMEOVER"
                        self.som.tocar("gameover")
                        return

            if acertou:
                self.projeteis_inimigos.pop(i)

        # Verifica se os inimigos alcançaram o jogador
        if self.horda.invadiu_base(self.jogador.rect.top):
            self.vidas = 0
            self.estado = "GAMEOVER"
            self.som.tocar("gameover")
            return

        # Atualiza partículas
        for p in self.particulas:
            p.atualizar(dt)
        self.particulas = [p for p in self.particulas if p.vida > 0]

        # Avança de fase ao eliminar toda a horda
        if not self.horda.lista:
            self.fase += 1
            self.som.tocar("fase")
            self.projeteis_jogador.clear()
            self.projeteis_inimigos.clear()
            self.horda.criar_onda(self.fase)

    def _desenhar_texto_centralizado(self, texto, fonte, cor, y):
        surf = fonte.render(texto, True, cor)
        rect = surf.get_rect(center=(confi.LARGURA // 2, y))
        self.tela.blit(surf, rect)

    def _desenhar_hud(self):
        pygame.draw.rect(self.tela, confi.FUNDO_HUD, (0, 0, confi.LARGURA, 48))
        pygame.draw.line(
            self.tela, confi.BORDA_NEON, (0, 48), (confi.LARGURA, 48), 2
        )

        txt_pontos = self.fonte_hud.render(
            f"PONTOS:{self.pontos:06d}", True, confi.CIANO
        )
        txt_recorde = self.fonte_hud.render(
            f"RECORDE:{self.recorde:06d}", True, confi.AMARELO
        )
        txt_fase = self.fonte_hud.render(f"FASE:{self.fase:02d}", True, confi.VERDE)

        self.tela.blit(txt_pontos, (12, 15))
        self.tela.blit(txt_recorde, (175, 15))
        self.tela.blit(txt_fase, (355, 15))

        # Ícones de vidas no canto superior direito
        for i in range(self.vidas):
            pos_x = confi.LARGURA - 28 - (i * 26)
            self.tela.blit(self.icone_vida, (pos_x, 16))

    def _desenhar_overlay(self):
        escuro = pygame.Surface((confi.LARGURA, confi.ALTURA - 48), pygame.SRCALPHA)
        escuro.fill((5, 6, 16, 215))
        self.tela.blit(escuro, (0, 48))

        if self.estado == "INICIO":
            self._desenhar_texto_centralizado(
                "INSERT COIN • 1 PLAYER", self.fonte_pequena, confi.AMARELO, 145
            )
            self._desenhar_texto_centralizado(
                "DEFENSOR RETRÔ", self.fonte_titulo, confi.CIANO, 205
            )
            self._desenhar_texto_centralizado(
                "OVNI BÔNUS = +300 PTS", self.fonte_hud, confi.ROSA, 285
            )
            self._desenhar_texto_centralizado(
                "INVASOR ELITE = 40 PTS", self.fonte_hud, confi.MAGENTA, 318
            )
            self._desenhar_texto_centralizado(
                "INVASOR MÉDIO = 20 PTS", self.fonte_hud, confi.CIANO, 351
            )
            self._desenhar_texto_centralizado(
                "INVASOR BASE  = 10 PTS", self.fonte_hud, confi.VERDE, 384
            )
            self._desenhar_texto_centralizado(
                "PRESSIONE [ENTER] OU [ESPAÇO]", self.fonte_media, confi.BRANCO, 465
            )
            self._desenhar_texto_centralizado(
                "SETAS/A-D: MOVER • ESPAÇO: ATIRAR • P: PAUSAR • M: SOM",
                self.fonte_pequena,
                confi.CINZA_TEXTO,
                535,
            )

        elif self.estado == "PAUSADO":
            self._desenhar_texto_centralizado(
                "JOGO PAUSADO", self.fonte_titulo, confi.AMARELO, 300
            )
            self._desenhar_texto_centralizado(
                "PRESSIONE [P] PARA CONTINUAR", self.fonte_hud, confi.BRANCO, 365
            )

        elif self.estado == "GAMEOVER":
            self._desenhar_texto_centralizado(
                "GAME OVER", self.fonte_titulo, confi.MAGENTA, 250
            )
            self._desenhar_texto_centralizado(
                f"PONTUAÇÃO FINAL: {self.pontos}", self.fonte_media, confi.CIANO, 320
            )
            if self.novo_recorde and self.pontos > 0:
                self._desenhar_texto_centralizado(
                    "★ NOVO RECORDE! ★", self.fonte_hud, confi.AMARELO, 365
                )
            self._desenhar_texto_centralizado(
                "PRESSIONE [ENTER] PARA REINICIAR",
                self.fonte_hud,
                confi.BRANCO,
                435,
            )

    def desenhar(self):
        offset_x = 0
        offset_y = 0
        if self.tremor_tela > 0:
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)

        self.tela.fill(confi.PRETO)

        # Estrelas
        for estrela in self.estrelas:
            pygame.draw.rect(
                self.tela,
                estrela["cor"],
                (
                    int(estrela["x"]) + offset_x,
                    int(estrela["y"]) + offset_y,
                    estrela["tam"],
                    estrela["tam"],
                ),
            )

        # Linha do solo retrô
        pygame.draw.line(
            self.tela,
            confi.BORDA_NEON,
            (14, confi.ALTURA - 16),
            (confi.LARGURA - 14, confi.ALTURA - 16),
            2,
        )

        # Elementos da arena
        self.barricada.desenhar(self.tela)
        if self.estado != "GAMEOVER":
            self.jogador.desenhar(self.tela)
        self.horda.desenhar(self.tela)

        for tiro in self.projeteis_jogador:
            tiro.desenhar(self.tela)
        for tiro in self.projeteis_inimigos:
            tiro.desenhar(self.tela)
        for particula in self.particulas:
            particula.desenhar(self.tela)

        self._desenhar_hud()

        if self.estado != "JOGANDO":
            self._desenhar_overlay()

        # Efeito visual de monitor CRT
        self.tela.blit(self.scanlines, (0, 0))
        pygame.display.flip()

    def executar(self):
        while True:
            dt = min(0.05, self.relogio.tick(confi.FPS) / 1000.0)
            self.processar_eventos()
            self.atualizar(dt)
            self.desenhar()


if __name__ == "__main__":
    Jogo().executar()