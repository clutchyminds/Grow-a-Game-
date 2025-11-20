import pygame
import pytmx
import sys
import time

pygame.init()

# ===================== PARAMETRES GENERAUX =====================
SCALE = 2
TILE_ORIG_W, TILE_ORIG_H = 16, 16
MAP_WIDTH, MAP_HEIGHT = 200, 200
MAP_TILE_W, MAP_TILE_H = TILE_ORIG_W * SCALE, TILE_ORIG_H * SCALE
SCREEN_W, SCREEN_H = 960, 640
fenetre = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Grow a Game")

map_file = "ma_map.tmx"
tmx_data = pytmx.util_pygame.load_pygame(map_file)

# --- AFFICHAGE COORDONNÉES ---
font_coords = pygame.font.SysFont("arial", 24)


# ===================== CHARGEMENT ANIMATIONS JOUEUR =====================
def load_animation_images(prefix, nb_frames):
    # Charge une liste d'images d'animation pour une direction
    images = []
    for i in range(nb_frames):
        img = pygame.image.load(f"{prefix}_{i}.png")
        img = pygame.transform.scale(img, (MAP_TILE_W, MAP_TILE_H))
        images.append(img)
    return images

# Charge 4 frames pour chaque direction (modifie nb_versions si besoin)
NB_FRAMES = 4
anim_right = load_animation_images("player_right", NB_FRAMES)
anim_left = load_animation_images("player_left", NB_FRAMES)
anim_up = load_animation_images("player_up", NB_FRAMES)
anim_down = load_animation_images("player_down", NB_FRAMES)

# ================== POSITION & ETATS DU JOUEUR ===================
joueur_px = (MAP_WIDTH // 2) * MAP_TILE_W
joueur_py = (MAP_HEIGHT // 2) * MAP_TILE_H
vitesse = 2

direction = "down"    # Direction par défaut
anim_index = 0        # Frame actuelle de l’animation
anim_timer = 0        # Pour timing animation
anim_speed = 0.12     # Durée (sec) avant de passer à la frame suivante

# ====================== NOMS DES CALQUES ========================
calque_bas = "Calque 1"
calques_haut = ["Calque 2", "Calque 3", "Calque 4", "Calque 41", "Calque 5"]
calque_collision = "Calque 2"
calque_tp4 = "Calque 4"
calque_tp41 = "Calque 41" #41 car on ne peux pas mettre 4.1 ou 4-1

def pos_to_grid(px, py):
    return int(px // MAP_TILE_W), int(py // MAP_TILE_H)

def tile_blocking(px, py):
    grid_x, grid_y = pos_to_grid(px, py)
    if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == calque_collision:
                gid = layer.data[grid_y][grid_x]
                return gid != 0
    return False

def tile_tp4(px, py):
    grid_x, grid_y = pos_to_grid(px, py)
    if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == calque_tp4:
                gid = layer.data[grid_y][grid_x]
                return gid != 0
    return False

def tile_tp41(px, py):
    grid_x, grid_y = pos_to_grid(px, py)
    if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == calque_tp41:
                gid = layer.data[grid_y][grid_x]
                return gid != 0
    return False

# ================== FONCTION AFFICHAGE DES REGLES ==================
def afficher_regles(fenetre):
    font = pygame.font.SysFont("arial", 32)
    petit = pygame.font.SysFont("arial", 25)
    en_regles = True
    while en_regles:
        fenetre.fill((25, 30, 50))
        # Affiche les règles du jeu
        titre = font.render("Règles du jeu", True, (250, 230, 80))
        ligne1 = petit.render("Déplace-toi avec les flèches. Evite les obstacles.", True, (230, 230, 250))
        ligne2 = petit.render("Tu peux te téléporter sur les tuiles spéciales.", True, (230, 230, 250))
        ligne3 = petit.render("Appuie sur ESC ou Retour pour revenir au menu.", True, (220, 220, 220))
        fenetre.blit(titre, (SCREEN_W // 2 - titre.get_width() // 2, 130))
        fenetre.blit(ligne1, (SCREEN_W // 2 - ligne1.get_width() // 2, 220))
        fenetre.blit(ligne2, (SCREEN_W // 2 - ligne2.get_width() // 2, 260))
        fenetre.blit(ligne3, (SCREEN_W // 2 - ligne3.get_width() // 2, 340))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN):
                en_regles = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                en_regles = False

# ======= FONCTION POUR LE MENU PRINCIPAL AVEC 2 BOUTONS =======
def afficher_menu(fenetre):
    font = pygame.font.SysFont("arial", 52)
    font_btn = pygame.font.SysFont("arial", 36)
    btn_jouer = pygame.Rect(SCREEN_W//2 - 105, 300, 210, 60)
    btn_regles = pygame.Rect(SCREEN_W//2 - 105, 380, 210, 60)
    selected = 0
    while True:
        fenetre.fill((30, 30, 50))
        titre = font.render("Grow a Game", True, (255, 255, 255))
        fenetre.blit(titre, (SCREEN_W // 2 - titre.get_width() // 2, 130))
        mouse_pos = pygame.mouse.get_pos()
        # Affichage visuel des boutons du menu principal, effet surbrillance
        for i, (rect, txt) in enumerate([(btn_jouer, "Jouer"), (btn_regles, "Règles")]):
            color = (90, 180, 220) if rect.collidepoint(mouse_pos) or selected == i else (120, 120, 180)
            pygame.draw.rect(fenetre, color, rect, border_radius=8)
            label = font_btn.render(txt, True, (255, 255, 255))
            fenetre.blit(label, (rect.x + rect.width // 2 - label.get_width() // 2, rect.y + rect.height // 2 - label.get_height() // 2))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = max(0, selected - 1)
                if event.key == pygame.K_DOWN:
                    selected = min(1, selected + 1)
                if event.key == pygame.K_RETURN:
                    if selected == 0:
                        return      # Démarre le jeu
                    elif selected == 1:
                        afficher_regles(fenetre)  # Affiche les règles
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_jouer.collidepoint(event.pos):
                    return
                elif btn_regles.collidepoint(event.pos):
                    afficher_regles(fenetre)

# ===================== DEMARRAGE DU JEU =====================
clock = pygame.time.Clock()
afficher_menu(fenetre)    # Lance le menu au démarrage

# --- Initialisation du timer pour l’animation ---
last_time = time.time()


# ===================== BOUCLE PRINCIPALE DU JEU =====================
en_cours = True
while en_cours:
    # Calcule delta temps
    now = time.time()
    dt = now - last_time
    last_time = now

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            en_cours = False

    touches = pygame.key.get_pressed()
    nx, ny = joueur_px, joueur_py

    # --- GESTION DU DEPLACEMENT + DETECTION DIRECTION ---
    moved = False
    # Ordre if...elif pour priorité à 1 direction à la fois
    if touches[pygame.K_LEFT]:
        direction = "left"
        if not tile_blocking(nx - vitesse, ny):
            nx -= vitesse
            moved = True
    elif touches[pygame.K_RIGHT]:
        direction = "right"
        if not tile_blocking(nx + vitesse + MAP_TILE_W - 1, ny):
            nx += vitesse
            moved = True
    elif touches[pygame.K_UP]:
        direction = "up"
        if not tile_blocking(nx, ny - vitesse):
            ny -= vitesse
            moved = True
    elif touches[pygame.K_DOWN]:
        direction = "down"
        if not tile_blocking(nx, ny + vitesse + MAP_TILE_H - 1):
            ny += vitesse
            moved = True

    # --- Applique les coordonnées ---
    nx = max(0, min(nx, MAP_WIDTH * MAP_TILE_W - MAP_TILE_W))
    ny = max(0, min(ny, MAP_HEIGHT * MAP_TILE_H - MAP_TILE_H))
    joueur_px, joueur_py = nx, ny

    # --- Animation : avance la frame si on bouge ---
    if moved:
        anim_timer += dt
        if anim_timer >= anim_speed:
            anim_index = (anim_index + 1) % NB_FRAMES   # Passe à la frame suivante
            anim_timer = 0
    else:
        anim_index = 0         # Immobile = première frame

    # --- Choix de l’image à dessiner ---
    if direction == "left":
        image_affiche = anim_left[anim_index]
    elif direction == "right":
        image_affiche = anim_right[anim_index]
    elif direction == "up":
        image_affiche = anim_up[anim_index]
    else:
        image_affiche = anim_down[anim_index]

    # --- TELEPORTATION ---
    if tile_tp4(joueur_px, joueur_py):
        dest_x, dest_y = 107, 73
        joueur_px = dest_x * MAP_TILE_W
        joueur_py = dest_y * MAP_TILE_H
        print("Téléportation !")

    if tile_tp41(joueur_px, joueur_py):
        dest_x, dest_y = 109, 97
        joueur_px = dest_x * MAP_TILE_W
        joueur_py = dest_y * MAP_TILE_H
        print("Téléportation !")

    # --- CAMERA CENTREE ---
    camera_x = joueur_px - SCREEN_W // 2 + MAP_TILE_W // 2
    camera_y = joueur_py - SCREEN_H // 2 + MAP_TILE_H // 2
    camera_x = max(0, min(camera_x, MAP_WIDTH * MAP_TILE_W - SCREEN_W))
    camera_y = max(0, min(camera_y, MAP_HEIGHT * MAP_TILE_H - SCREEN_H))

    # --- AFFICHAGE DE LA CARTE + JOUEUR ANIME ---
    fenetre.fill((0, 0, 0))
    visible_tile_x = SCREEN_W // MAP_TILE_W + 2
    visible_tile_y = SCREEN_H // MAP_TILE_H + 2
    first_tile_x = camera_x // MAP_TILE_W
    first_tile_y = camera_y // MAP_TILE_H

    for y in range(first_tile_y, first_tile_y + visible_tile_y):
        for x in range(first_tile_x, first_tile_x + visible_tile_x):
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                # Calque bas
                for layer in tmx_data.visible_layers:
                    if isinstance(layer, pytmx.TiledTileLayer) and layer.name == calque_bas:
                        gid = layer.data[y][x]
                        if gid != 0:
                            image = tmx_data.get_tile_image_by_gid(gid)
                            if image:
                                image = pygame.transform.scale(image, (MAP_TILE_W, MAP_TILE_H))
                                fenetre.blit(image, (x * MAP_TILE_W - camera_x, y * MAP_TILE_H - camera_y))
                # Calques au-dessus
                for layer in tmx_data.visible_layers:
                    if isinstance(layer, pytmx.TiledTileLayer) and layer.name in calques_haut:
                        gid = layer.data[y][x]
                        if gid != 0:
                            image = tmx_data.get_tile_image_by_gid(gid)
                            if image:
                                image = pygame.transform.scale(image, (MAP_TILE_W, MAP_TILE_H))
                                fenetre.blit(image, (x * MAP_TILE_W - camera_x, y * MAP_TILE_H - camera_y))

    # --- AFFICHAGE DU JOUEUR ANIME TOUJOURS AU CENTRE ---
    fenetre.blit(image_affiche, (SCREEN_W // 2 - MAP_TILE_W // 2, SCREEN_H // 2 - MAP_TILE_H // 2))

    # --- AFFICHAGE COORDONNÉES ---
    coord_text = font_coords.render(f"X: {joueur_px // MAP_TILE_W}  Y: {joueur_py // MAP_TILE_H}", True, (255,255,0))
    fenetre.blit(coord_text, (SCREEN_W - coord_text.get_width() - 20, 20))  # 20 px depuis le bord droit, 20px depuis le haut

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
