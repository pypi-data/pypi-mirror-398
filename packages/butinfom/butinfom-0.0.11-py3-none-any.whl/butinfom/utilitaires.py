from sympy import Number, Rational, latex
from os import getenv

def preparer_coef(
        coef: int|float|Rational|Number,
        en_tete: bool = False,
        bold: bool = False
    ) -> str:
    r"""Renvoie dans une chaîne au format LaTeX un coefficient coef (type
    nombre) à écrire à gauche d'une variable dans une expression LaTeX. Si
    le coefficient est en tête de formule, choisir l'option en_tete=True.
    Exemples :
    >>> preparer_coef(-3)
    ' - 3'
    >>> preparer_coef(-3, en_tete=True)
    '-3'
    >>> preparer_coef(1)
    ' + '
    >>> preparer_coef(1, en_tete=True)
    ''
    >>> preparer_coef(Rational(-2, 3))
    r' - \frac{2}{3}'
    """
    if coef == 0:
        return ''
    elif coef == 1:
        if en_tete:
            return ''
        else:
            return ' + '
    elif coef == -1:
        if en_tete:
            return '-'
        else:
            return ' - '
    elif coef > 0:
        if en_tete:
            if bold:
                return r'\boldsymbol{' + latex(coef) + '}'
            else:
                return latex(coef)
        else:
            if bold:
                return ' + ' + r'\boldsymbol{' + latex(coef) + '}'
            else:
                return ' + ' + latex(coef)
    else: # coef < 0
        if en_tete:
            if bold:
                return r'\boldsymbol{' + '-' + latex(abs(coef)) + '}'
            else:
                return '-' + latex(abs(coef))
        else:
            if bold:
                return ' ' + r'\boldsymbol{-}' + ' ' + r'\boldsymbol{' + latex(abs(coef)) + '}'
            else:
                return ' - ' + latex(abs(coef))


def entier_en_indice_unicode(entier: int) -> str:
    """Renvoie une chaîne de caractère contenant le nombre entier positif passé
    en paramètre sous forme de petits chiffres de catalogue Unicode."""
    res = ''
    for chiffre in str(entier):
        res += chr(ord('₀') + ord(chiffre) - ord('0'))
    return res

def tableau_en_array_latex(tab: list[list[str]], format_col: str = '', hlines: list[int] = []) -> str:
    """Prend en paramètre un tableau 2D de chaîne de caractères et renvoie le
    code LaTeX de l'array correspondant. Attention, chaque cellule doit
    contenir une expression mathématique valide. Pour passer du texte écrire
    dans une case \text{<votre texte>}. Par défaut, les cellules sont centrées
    horizontalement et toutes les bordures des cellules sont tracées. On peut
    préciser le format des colonnes (ex: '|c|llll|r') et le numéro des lignes
    avant lesquelles tracer une hline."""
    assert isinstance(tab, list), "tab doit être du type list !"
    for ligne in tab:
        assert isinstance(ligne, list), "Chaque élément de tab doit être du type list !"
        for case in ligne:
            assert isinstance(case, str), "Chaque case de tab doit être du type str !"
    largeur = len(tab[0])
    for ligne in tab:
        assert len(ligne) == largeur, "Les lignes du tableau n'ont pas toutes le même nombre de cases !"
    assert isinstance(hlines, list), "hlines doit être du type list !"
    if format_col == '':
        format_col = largeur * '|c' + '|'
    for elt in hlines:
        assert isinstance(elt, int), "hlines ne doit contenir que des entiers !"
        assert elt in range(len(tab) + 1), "hlines ne doit contenir que des indices positifs valides !"
    res = r'\begin{array}{' + format_col + '}\n'
    for i in range(len(tab)):
        if i in hlines or hlines == []:
            res += r'    \hline' + '\n'
        res += '    ' + ' & '.join(tab[i]) + r' \\' + '\n'
    if i + 1 in hlines or hlines == []:
        res += r'    \hline' + '\n'
    res += r'\end{array}' + '\n'
    return res


def envelopper_latex_dans_balises_align(latex: str) -> str:
    r"""Enveloppe le code LaTeX passé en paramètre entre des des balises
    \begin{align} et \end{align}. Cela doit être fait uniquement si le
    Jupyter Notebook n'est pas exécuté dans Google Colab. Dans les
    environnements Jupyter Notebooks "classiques" le rendu est
    incorrect si les balises \begin{align} et \end{align} sont omises
    alors que c'est le contraire dans Google Colab.
    """
    return "\\begin{align*}\n" + latex + "\\end{align*}\n"


def execute_dans_google_colab() -> bool:
    return getenv("COLAB_RELEASE_TAG")

def retrait_sauts_ligne(chaine: str):
    assert isinstance(chaine, str), "chaine doit être du type str !"
    res = ''
    for car in chaine:
        if car == '\n':
            res += ' '
        else:
            res += car
    return res

def formattage_chaine(chaine: str, nbre_car_ligne: int = 79):
    assert isinstance(chaine, str), "chaine doit être du type str !"
    assert isinstance(nbre_car_ligne, int), "nbre_car_ligne doit être un entier !"
    assert nbre_car_ligne > 1, "nbre_car_ligne doit être strictement positif !"
    sans_sauts = retrait_sauts_ligne(chaine)
    res = ''
    for i in range(len(sans_sauts)):
        res += sans_sauts[i]
        if i > 0 and i % nbre_car_ligne == 0:
            res += '\n'
    return res


if __name__ == '__main__':
    assert preparer_coef(-3) == ' - 3'
    assert preparer_coef(-3, en_tete=True) == '-3'
    assert preparer_coef(1) == ' + '
    assert preparer_coef(1, en_tete=True) == ''
    assert preparer_coef(Rational(-2, 3)) == r' - \frac{2}{3}'
    print(entier_en_indice_unicode(16))