import random
import pygame
import confi
from jogador import Projetil


class Inimigo:
    def __init__(self, x, y, tipo, cor, pontos):
        matrizes = confi.SPRITES_INIMIGOS[tipo]
        self.frames = [
            confi.criar_surface_pixel(matrizes[0], escala=3, cor=cor),
            confi.criar_surface_pixel(matrizes[1], escala=3, cor=cor),
        ]
        self.rect = self.frames[0].get_rect(topleft=(int(x), int(y)))
        self.x_exato = float(x)
        self.y_exato = float(y)
        self.cor = cor
        self.pontos = pontos

    def mover(self, dx, dy):
        self.x_exato += dx
        self.y_exato += dy
        self.rect.x = int(self.x_exato)
        self.rect.y = int(self.y_exato)

    def desenhar(self, tela, frame_atual):
        tela.blit(self.frames[frame_atual], self.rect)


class OvniBonus:
    def __init__(self):
        self.sprite = confi.criar_surface_pixel(
            confi.SPRITE_OVNI, escala=3, cor=confi.ROSA
        )
        vem_da_esquerda = random.choice([True, False])
        x_inicial = -self.sprite.get_width() if vem_da_esquerda else confi.LARGURA + 4
        self.rect = self.sprite.get_rect(topleft=(x_inicial, 62))
        self.x_exato = float(x_inicial)
        self.velocidade_x = 135.0 if vem_da_esquerda else -135.0
        self.pontos = confi.PONTOS_OVNI

    def atualizar(self, dt):
        self.x_exato += self.velocidade_x * dt
        self.rect.x = int(self.x_exato)

    def fora_da_tela(self):
        return self.rect.right < -20 or self.rect.left > confi.LARGURA + 20

    def desenhar(self, tela):
        tela.blit(self.sprite, self.rect)


class HordaInimigos:
    def __init__(self):
        self.lista = []
        self.ovni = None
        self.direcao = 1
        self.velocidade_base = 44.0
        self.timer_animacao = 0.0
        self.frame_atual = 0
        self.timer_tiro = 1.2
        self.timer_ovni = 9.0

    def criar_onda(self, fase):
        self.lista.clear()
        self.direcao = 1
        self.velocidade_base = 44.0 + (fase - 1) * 14.0
        self.timer_tiro = max(0.4, 1.25 - fase * 0.1)

        linhas = 5
        colunas = 10
        espaco_x = 48
        espaco_y = 40
        offset_x = (confi.LARGURA - colunas * espaco_x) / 2 + 6
        offset_y = 102

        for r in range(linhas):
            for c in range(colunas):
                if r == 0:
                    tipo = "elite"
                    cor = confi.MAGENTA
                    pontos = confi.PONTOS_ELITE
                    largura = 24
                elif r in (1, 2):
                    tipo = "medio"
                    cor = confi.CIANO
                    pontos = confi.PONTOS_MEDIO
                    largura = 33
                else:
                    tipo = "base"
                    cor = confi.VERDE
                    pontos = confi.PONTOS_BASE
                    largura = 36

                pos_x = offset_x + c * espaco_x + (36 - largura) / 2
                pos_y = offset_y + r * espaco_y
                self.lista.append(Inimigo(pos_x, pos_y, tipo, cor, pontos))

    def atualizar(self, dt, fase, projeteis_inimigos):
        # Alternância de quadros da animação 8-bit
        self.timer_animacao += dt
        if self.timer_animacao >= 0.42:
            self.timer_animacao = 0.0
            self.frame_atual = 1 - self.frame_atual

        # Controle do OVNI bônus
        self.timer_ovni -= dt
        if self.ovni is None and self.timer_ovni <= 0:
            self.ovni = OvniBonus()
            self.timer_ovni = random.uniform(14.0, 22.0)

        if self.ovni is not None:
            self.ovni.atualizar(dt)
            if self.ovni.fora_da_tela():
                self.ovni = None

        # Aceleração progressiva conforme restam menos inimigos
        fator_velocidade = 1.0 + (50 - len(self.lista)) * 0.032
        velocidade_atual = self.velocidade_base * fator_velocidade

        bateu_borda = False
        for inimigo in self.lista:
            inimigo.mover(self.direcao * velocidade_atual * dt, 0)
            if (self.direcao == 1 and inimigo.rect.right >= confi.LARGURA - 16) or (
                self.direcao == -1 and inimigo.rect.left <= 16
            ):
                bateu_borda = True

        if bateu_borda:
            self.direcao *= -1
            for inimigo in self.lista:
                inimigo.mover(0, 18)

        # Disparos dos inimigos
        self.timer_tiro -= dt
        if self.timer_tiro <= 0 and self.lista:
            atirador = random.choice(self.lista)
            tiro = Projetil(
                atirador.rect.centerx,
                atirador.rect.bottom,
                250.0 + fase * 22.0,
                confi.MAGENTA,
                largura=4,
                altura=12,
            )
            projeteis_inimigos.append(tiro)
            self.timer_tiro = max(0.35, 1.25 - fase * 0.12)

    def invadiu_base(self, y_jogador):
        return any(inimigo.rect.bottom >= y_jogador for inimigo in self.lista)

    def desenhar(self, tela):
        if self.ovni is not None:
            self.ovni.desenhar(tela)
        for inimigo in self.lista:
            inimigo.desenhar(tela, self.frame_atual)