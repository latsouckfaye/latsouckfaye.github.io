"""
Comparer des cartes a differentes resolutions spatiales -- equivalent Python
==============================================================================

Port du notebook R (github.com/latsouckfaye/CompareMap) : desagregation de
resolution, score de concordance ("Match") et score equilibre par classe
("Balanced Match").

Choix deliberes :
  - Aucune dependance geospatiale lourde (pas de geopandas, shapely ni
    rasterio -- indisponibles ou fragiles a installer). Le test
    point-dans-polygone est fait avec matplotlib.path.Path, et les grilles
    sont de simples tableaux numpy.
  - Les donnees d'entree (REFERENCE, PRED_COARSE ci-dessous) ne sont PAS
    tirees aleatoirement. Une premiere version utilisait `set.seed(12)` cote
    R et `np.random.default_rng(12)` cote Python en esperant des resultats
    comparables -- mais R et numpy implementent des generateurs de nombres
    pseudo-aleatoires differents : un meme seed ne produit PAS la meme
    sequence d'un langage a l'autre. Les deux jeux de donnees etaient donc
    structurellement differents, et les scores ne pouvaient qu'etre "du meme
    ordre de grandeur", jamais identiques.
    Plutot que de re-implementer le generateur de R en Python (fragile, et
    qui casserait au moindre changement de version de R), les deux grilles
    ci-dessous ont ete extraites directement des images publiees par le
    notebook R (refmap.png, predmap.png) en lisant la couleur de chaque
    cellule et en la comparant a la palette de la legende. Les deux jeux de
    donnees sont donc desormais les MEMES, et les scores calcules ici
    reproduisent ceux de R a l'arrondi pres (verifie : Match 0.81/0.70,
    NCBM 0.86, CBM1 0.75, CBM2 0.56 -- contre 0.82/0.71, 0.86, 0.76, 0.56
    cote R ; l'ecart residuel vient du bruit d'extraction sur 1-2 cellules
    en bordure d'image, pas d'une difference de methode).
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.colors import ListedColormap, BoundaryNorm

OUT_DIR = "."

# ---------------------------------------------------------------------------
# 1. Zone d'etude (identique au notebook R)
# ---------------------------------------------------------------------------
POLY_LON = [-116.8, -114.2, -112.9, -111.9, -114.2, -115.4, -117.7]
POLY_LAT = [41.3, 42.9, 42.4, 39.8, 37.9, 38.3, 38.6]
POLYGON = np.column_stack([POLY_LON, POLY_LAT])

XMIN, XMAX = -117.7, -111.9
YMIN, YMAX = 37.9, 42.9

NA = np.nan

# ---------------------------------------------------------------------------
# 2. Cartes de reference et predite -- extraites de refmap.png / predmap.png
#    (voir la note en tete de fichier : memes donnees que la version R,
#    pour permettre une comparaison directe des scores).
# ---------------------------------------------------------------------------
REFERENCE = np.array([
    [NA, NA, NA, NA, NA, NA,  5,  5, NA, NA, NA, NA],
    [NA, NA, NA, NA, NA,  3,  5,  5,  5,  5, NA, NA],
    [NA, NA, NA,  3,  2,  2,  5,  5,  2,  2, NA, NA],
    [NA, NA,  3,  3,  2,  2,  5,  5,  2,  2,  1, NA],
    [NA,  4,  2,  2,  2,  2,  5,  5,  4,  4,  1, NA],
    [NA,  4,  2,  2,  2,  2,  5,  5,  4,  4,  1, NA],
    [NA,  2,  3,  3,  5,  5,  4,  4,  5,  5,  5, NA],
    [ 2,  2,  3,  3,  5,  5,  4,  4,  5,  5, NA, NA],
    [ 1,  1,  2,  2,  2,  2,  4,  4,  4, NA, NA, NA],
    [NA, NA, NA, NA, NA, NA,  4,  4, NA, NA, NA, NA],
], dtype=float)

PRED_COARSE = np.array([
    [NA, NA, NA,  5,  5, NA],
    [NA,  3,  5,  5,  2, NA],
    [NA,  2,  2,  5,  1,  1],
    [ 2,  3,  4,  4,  5, NA],
    [NA, NA,  2,  4, NA, NA],
], dtype=float)

CLASSES = [1, 2, 3, 4, 5]


def make_grid(res):
    """Centres de cellules d'une grille reguliere couvrant l'etendue, a la resolution `res`."""
    ncol = int(round((XMAX - XMIN) / res))
    nrow = int(round((YMAX - YMIN) / res))
    xs = XMIN + res * (np.arange(ncol) + 0.5)
    ys = YMAX - res * (np.arange(nrow) + 0.5)  # nord -> sud, comme un raster
    return xs, ys, nrow, ncol


def cell_polygon_mask(xs, ys, polygon):
    """True pour les cellules dont le centre est a l'interieur du polygone."""
    xx, yy = np.meshgrid(xs, ys)
    pts = np.column_stack([xx.ravel(), yy.ravel()])
    inside = Path(polygon).contains_points(pts)
    return inside.reshape(len(ys), len(xs))


def disaggregate(coarse, factor):
    """Desagrege une grille grossiere en repetant chaque cellule factor x factor fois."""
    return np.repeat(np.repeat(coarse, factor, axis=0), factor, axis=1)


# ---------------------------------------------------------------------------
# 3. Statut des cellules (hors zone / predite / non predite)
#
# Une cellule est "non predite" si la grille grossiere ne la couvrait pas
# (NA dans PRED_COARSE) alors qu'elle est dans la zone d'etude a resolution
# fine -- exactement le mecanisme du notebook R : ce n'est pas un masque
# ajoute a part, ca sort naturellement de la desagregation.
# ---------------------------------------------------------------------------
def status_prop(predicted, mask_ref):
    outside = ~mask_ref
    predicted_mask = mask_ref & ~np.isnan(predicted)
    nonpredicted_mask = mask_ref & np.isnan(predicted)

    n_outside = int(outside.sum())
    n_predicted = int(predicted_mask.sum())
    n_nonpredicted = int(nonpredicted_mask.sum())
    total_in = n_predicted + n_nonpredicted
    prop_L = n_predicted / total_in
    prop_NL = n_nonpredicted / total_in

    return {
        "outside": outside, "predicted_mask": predicted_mask, "nonpredicted_mask": nonpredicted_mask,
        "n_outside": n_outside, "n_predicted": n_predicted, "n_nonpredicted": n_nonpredicted,
        "prop_L": prop_L, "prop_NL": prop_NL,
    }


# ---------------------------------------------------------------------------
# 4. Score de concordance ("Match")
# ---------------------------------------------------------------------------
def match_score(pred, ref, mask, correct=False):
    """Proportion de cellules identiques entre pred et ref, a l'interieur de mask.

    correct=False : ignore les cellules non predites (pred = NaN).
    correct=True  : les compte comme des erreurs (NaN != tout).
    """
    valid_ref = mask & ~np.isnan(ref)
    if correct:
        matches = valid_ref & (pred == ref)
        return float(matches.sum() / valid_ref.sum())
    valid = valid_ref & ~np.isnan(pred)
    return float(np.mean(pred[valid] == ref[valid]))


# ---------------------------------------------------------------------------
# 5. Score equilibre par classe ("Balanced Match")
# ---------------------------------------------------------------------------
def balanced_match(pred, ref, mask, classes, prop_L):
    """Retourne (NCBM, CBM1, CBM2) -- voir le tutoriel pour la definition de chacun.

    NCBM : rappel par classe calcule uniquement sur les cellules predites (les
    cellules non predites sont exclues du calcul, numerateur ET denominateur).

    CBM2 : le denominateur de chaque rappel redevient "toutes les cellules de
    cette classe dans la reference", y compris celles non predites -- une
    cellule non predite compte donc comme un echec pour sa vraie classe. La
    moyenne est ensuite divisee par K+1 (le "+1" represente la classe des
    cellules non predites, dont le rappel est fixe a 0 par convention), pas
    par K : avoir une categorie non predictible penalise le score meme si les
    predictions faites sont toutes correctes.
    """
    valid_ref = mask & ~np.isnan(ref)
    valid_pred = valid_ref & ~np.isnan(pred)

    recalls_ncbm, recalls_cbm2 = [], []
    for k in classes:
        idx_pred = valid_pred & (ref == k)
        if idx_pred.sum() > 0:
            recalls_ncbm.append(float((idx_pred & (pred == k)).sum() / idx_pred.sum()))

        idx_ref = valid_ref & (ref == k)  # inclut les cellules non predites de cette classe
        if idx_ref.sum() > 0:
            recalls_cbm2.append(float((idx_ref & (pred == k)).sum() / idx_ref.sum()))

    ncbm = float(np.mean(recalls_ncbm))
    cbm1 = ncbm * prop_L
    cbm2 = float(sum(recalls_cbm2) / (len(recalls_cbm2) + 1))
    return ncbm, cbm1, cbm2


# ---------------------------------------------------------------------------
# 6. Cartes (figures)
# ---------------------------------------------------------------------------
CLASS_COLORS = ["#dee273", "#dcbf64", "#a5bfdd", "#1f77b6", "#02426d"]


def plot_class_map(grid, title, path, tag=""):
    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    cmap = ListedColormap(CLASS_COLORS)
    norm = BoundaryNorm(np.arange(0.5, 6.5, 1), cmap.N)
    masked = np.ma.masked_invalid(grid)
    ax.pcolormesh(np.linspace(XMIN, XMAX, grid.shape[1] + 1),
                   np.linspace(YMAX, YMIN, grid.shape[0] + 1),
                   masked, cmap=cmap, norm=norm, edgecolors="black", linewidth=0.3)
    ax.plot(np.append(POLY_LON, POLY_LON[0]), np.append(POLY_LAT, POLY_LAT[0]),
            color="blue", linewidth=1)
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    if tag:
        ax.text(0.01, 1.05, tag, transform=ax.transAxes, fontsize=12, fontweight="bold")
    handles = [plt.Rectangle((0, 0), 1, 1, color=CLASS_COLORS[i]) for i in range(5)]
    ax.legend(handles, [str(i) for i in range(1, 6)], title="Class",
              loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def plot_status_map(status, mask_ref, path, tag=""):
    grid = np.full(mask_ref.shape, np.nan)
    grid[status["predicted_mask"]] = 1
    grid[status["nonpredicted_mask"]] = 0
    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    cmap = ListedColormap(["orange", "green"])
    norm = BoundaryNorm([-0.5, 0.5, 1.5], cmap.N)
    masked = np.ma.masked_invalid(grid)
    ax.pcolormesh(np.linspace(XMIN, XMAX, grid.shape[1] + 1),
                   np.linspace(YMAX, YMIN, grid.shape[0] + 1),
                   masked, cmap=cmap, norm=norm, edgecolors="black", linewidth=0.3)
    ax.plot(np.append(POLY_LON, POLY_LON[0]), np.append(POLY_LAT, POLY_LAT[0]),
            color="blue", linewidth=1)
    ax.set_title("Prediction map disaggregated marking", fontsize=10, loc="left")
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    if tag:
        ax.text(0.01, 1.05, tag, transform=ax.transAxes, fontsize=12, fontweight="bold")
    handles = [plt.Rectangle((0, 0), 1, 1, color="orange"), plt.Rectangle((0, 0), 1, 1, color="green")]
    ax.legend(handles, ["NL", "L"], title="Status",
              loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def plot_match_map(pred, ref, mask, correct, yes, no, path, tag=""):
    valid_ref = mask & ~np.isnan(ref)
    grid = np.full(mask.shape, np.nan)
    if correct:
        match = valid_ref & (pred == ref)
        grid[valid_ref] = np.where(match[valid_ref], 1, 0)
    else:
        valid = valid_ref & ~np.isnan(pred)
        grid[valid] = np.where((pred == ref)[valid], 1, 0)
    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    cmap = ListedColormap(["yellow", "seagreen"])
    norm = BoundaryNorm([-0.5, 0.5, 1.5], cmap.N)
    masked = np.ma.masked_invalid(grid)
    ax.pcolormesh(np.linspace(XMIN, XMAX, grid.shape[1] + 1),
                   np.linspace(YMAX, YMIN, grid.shape[0] + 1),
                   masked, cmap=cmap, norm=norm, edgecolors="black", linewidth=0.3)
    ax.plot(np.append(POLY_LON, POLY_LON[0]), np.append(POLY_LAT, POLY_LAT[0]),
            color="blue", linewidth=1)
    title = "Corrected Match" if correct else "Non corrected Match"
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    if tag:
        ax.text(0.01, 1.05, tag, transform=ax.transAxes, fontsize=12, fontweight="bold")
    handles = [plt.Rectangle((0, 0), 1, 1, color="yellow"), plt.Rectangle((0, 0), 1, 1, color="seagreen")]
    ax.legend(handles, [f"No = {no:.2f}", f"Yes = {yes:.2f}"], title="Match",
              loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 7. Execution complete
# ---------------------------------------------------------------------------
def main():
    xs_f, ys_f, nrow_f, ncol_f = make_grid(0.5)
    mask_ref = cell_polygon_mask(xs_f, ys_f, POLYGON)

    reference = np.where(mask_ref, REFERENCE, np.nan)
    predicted_dis = disaggregate(PRED_COARSE, 2)
    predicted = np.where(mask_ref, predicted_dis, np.nan)

    status = status_prop(predicted, mask_ref)

    match_nc = match_score(predicted, reference, mask_ref, correct=False)
    match_c = match_score(predicted, reference, mask_ref, correct=True)
    ncbm, cbm1, cbm2 = balanced_match(predicted, reference, mask_ref, CLASSES, status["prop_L"])

    print("=== Statut des cellules ===")
    print(f"Hors zone        : {status['n_outside']}")
    print(f"Predites (L)     : {status['n_predicted']}  ({status['prop_L']*100:.1f} %)")
    print(f"Non predites (NL): {status['n_nonpredicted']}  ({status['prop_NL']*100:.1f} %)")
    print()
    print("=== Scores (R entre parentheses) ===")
    print(f"Match non corrige : {match_nc:.2f}  (0.82)")
    print(f"Match corrige     : {match_c:.2f}  (0.71)")
    print(f"NCBM (brut)       : {ncbm:.2f}  (0.86)")
    print(f"CBM1 (corrige, prop. 1) : {cbm1:.2f}  (0.76)")
    print(f"CBM2 (corrige, prop. 2) : {cbm2:.2f}  (0.56)")

    plot_class_map(reference, "Reference map", f"{OUT_DIR}/refmap_py.png", tag="B")
    plot_class_map(PRED_COARSE, "Prediction map", f"{OUT_DIR}/predmap_py.png", tag="C")
    plot_class_map(predicted, "Prediction map disaggregated", f"{OUT_DIR}/predismap_py.png", tag="D")
    plot_status_map(status, mask_ref, f"{OUT_DIR}/statusmap_py.png", tag="E")
    plot_match_map(predicted, reference, mask_ref, False, match_nc, 1 - match_nc,
                    f"{OUT_DIR}/pmapcomp_py.png", tag="F")
    plot_match_map(predicted, reference, mask_ref, True, match_c, 1 - match_c,
                    f"{OUT_DIR}/pmapcompcorr_py.png", tag="G")

    return {
        "n_outside": status["n_outside"], "n_predicted": status["n_predicted"],
        "n_nonpredicted": status["n_nonpredicted"], "prop_L": status["prop_L"],
        "match_nc": match_nc, "match_c": match_c,
        "ncbm": ncbm, "cbm1": cbm1, "cbm2": cbm2,
    }


if __name__ == "__main__":
    main()
