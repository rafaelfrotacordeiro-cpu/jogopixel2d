import pygame
import confi


class Projetil:
    def __init__(self, x, y, velocidade_y, cor, largura=4, altura=14):
        self.rect = pygame.Rect(int(x - largura // 2), int(y), largura, altura)
        self.y_exato = float(y)
        self.velocidade_y = velocidade_y
        self.cor = cor

    def atualizar(self, dt):
        self.y_exato += self.velocidade_y * dt
        self.rect.y = int(self.y_exato)

    def fora_da_tela(self):
        return self.rect.bottom < 0 or self.rect.top > confi.ALTURA

    def desenhar(self, tela):
        pygame.draw.rect(tela, self.cor, self.rect)


class Barricada:
    """Escudos destrutíveis em blocos retrô."""

    def __init__(self):
        self.blocos = []
        self.criar()

    def criar(self):
        self.blocos.clear()
        quantidade = 4
        espacamento = confi.LARGURA / (quantidade + 1)
        bloco_w = 11
        bloco_h = 9

        for i in range(quantidade):
            inicio_x = espacamento * (i + 1) - (5 * bloco_w) / 2
            inicio_y = confi.ALTURA - 135

            for linha in range(4):
                for coluna in range(5):
                    # Recorte inferior estilo arco clássico
                    if linha == 3 and coluna in (1, 2, 3):
                        continue
                    rect = pygame.Rect(
                        int(inicio_x + coluna * bloco_w),
                        int(inicio_y + linha * bloco_h),
                        bloco_w - 1,
                        bloco_h - 1,
                    )
                    self.blocos.append(rect)

    def verificar_colisao(self, rect_alvo):
        for i in range(len(self.blocos) - 1, -1, -1):
            if self.blocos[i].colliderect(rect_alvo):
                self.blocos.pop(i)
                return True
        return False

    def desenhar(self, tela):
        for bloco in self.blocos:
            pygame.draw.rect(tela, confi.VERDE, bloco)


class Jogador:
    def __init__(self):
        self.sprite = confi.criar_surface_pixel(
            confi.SPRITE_JOGADOR, escala=4, cor=confi.AMARELO
        )
        self.rect = self.sprite.get_rect()
        self.x_exato = 0.0
        self.cooldown = 0.0
        self.invulneravel = 0.0
        self.resetar()

    def resetar(self):
        self.x_exato = (confi.LARGURA - self.rect.width) / 2
        self.rect.x = int(self.x_exato)
        self.rect.y = confi.ALTURA - 56
        self.cooldown = 0.0
        self.invulneravel = 1.2

    def atualizar(self, dt, teclas, projeteis_jogador, som):
        if self.cooldown > 0:
            self.cooldown -= dt
        if self.invulneravel > 0:
            self.invulneravel -= dt

        direcao = 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            direcao -= 1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            direcao += 1

        self.x_exato += direcao * confi.VELOCIDADE_JOGADOR * dt
        limite_esq = 14
        limite_dir = confi.LARGURA - self.rect.width - 14
        self.x_exato = max(limite_esq, min(limite_dir, self.x_exato))
        self.rect.x = int(self.x_exato)

        if teclas[pygame.K_SPACE] and self.cooldown <= 0:
            novo_tiro = Projetil(
                self.rect.centerx,
                self.rect.top - 10,
                -confi.VELOCIDADE_TIRO_JOGADOR,
                confi.CIANO,
            )
            projeteis_jogador.append(novo_tiro)
            self.cooldown = confi.COOLDOWN_TIRO
            som.tocar("tiro")

    def sofrer_dano(self):
        if self.invulneravel > 0:
            return False
        self.invulneravel = confi.TEMPO_INVULNERAVEL
        return True

    def desenhar(self, tela):
        # Pisca enquanto estiver com escudo de invulnerabilidade
        if self.invulneravel > 0 and int(self.invulneravel * 14) % 2 == 1:
            return
        tela.blit(self.sprite, self.rect)