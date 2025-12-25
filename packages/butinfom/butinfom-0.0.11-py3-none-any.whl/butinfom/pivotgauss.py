from sympy import Matrix, Symbol, Number, eye, latex, zeros
from os import getenv
from .utilitaires import preparer_coef, envelopper_latex_dans_balises_align
from .calculmod import ClasseCongruence


class PivotGaussSysteme:

    """Classe permettant de représenter dans un cahier Jupyter les étapes de
    l'algorithme du pivot de Gauss pour la résolution d'un système d'équations.
    - Le système est passé en paramètre du constructeur sous forme d'un tableau
    2D.
    - Le code LaTeX est produit.
    - On peut ensuite réaliser l'affichage en dernière ligne de cellule de
    cahier Jupyter.

    Exemple :

    piv1 = PivotGaussSysteme([
        [2, 0,  6,  0], # equation 1 : 2x + 6z = 0
        [3, 5, 10, -2], # equation 2 : 3x + 5y + 10z = -2
        [1, 4,  0,  1]  # equation 3 : x + 4y = 1
    ])

    piv1 # à mettre en fin de cellule pour obtenir l'affichage naturel

    On peut ensuite obtenir le code LaTeX associé dans une nouvelle cellule
    avec :

    print(piv1)
    """

    def __init__(
            self,
            tab: list[list[Number]],
            affichage_lignes_zeros: bool = True
        ) -> None:
        """Prend en paramètres:

            tab: list[list[Number]]
                tableau 2D de nombres représentant le système à résoudre par le
                pivot de Gauss. Les types de nombres possibles sont :
                    int
                    float
                    Rational (du module sympy)
                    Number (tout type de nombre du module sympy)

            affichage_lignes_zeros: bool
                permet d'afficher ou masquer les équations 0 = 0 dans le
                système résultat. Par défaut, les équations 0 = 0 sont
                affichées. Passer ce paramètre à False pour les masquer.
        """
        self._affichage_ligne_zeros = affichage_lignes_zeros
        # tableau de départ converti en instance de la classe Matrix de sympy
        self._mat = Matrix(tab)
        # vérification de la validité du tableau
        n, m = self._mat.shape
        assert n > 0, "Le tableau doit posséder au moins une ligne !"
        assert m > 1, "Le tableau doit posséder au moins deux colonnes !"
        self._nb_equ = self._nbre_equations()
        self._nb_var = self._nbre_variables()
        self._noms_lignes = self._creer_noms_lignes()
        # liste des matrices à chaque étape de l'algorithme
        self._matrices = [self._mat.copy()]
        # liste des opérations sur les lignes à chaque étape de l'algorithme
        self._operations = [self._noms_lignes]
        # nom des variables au format LaTeX
        self._noms_variables = self._creer_noms_variables()
        # variables : instances de la classe Symbol de sympy
        self._variables = self._creer_variables()
        # Initialisation de la chaîne LaTeX contenant la présentation de
        # l'algorithme du pivot de Gauss. Au départ cette chaîne contient le
        # système d'équations associé au tableau de départ.
        self._latex = self._latex_systeme()
        # exécution de l'algorithme du pivot
        self._pivot()
        # Calcul du nombre d'étapes de l'algorithme du pivot
        self._nb_etapes = len(self._matrices)
        # complétion du rendu en LaTeX
        self._latex += self._creer_latex()
        # Si le Jupyter Notebook n'est pas exécuté dans Google Colab
        if not getenv("COLAB_RELEASE_TAG"):
            self._envelopper_latex_dans_balises_align()

    def _nbre_equations(self) -> int:
        """Renvoie le nombre d'équations correspondant au tableau passé en
        paramètre du constructeur.
        Exemple :
        >>> piv1 = PivotGaussSysteme([
        ...     [2, 4,  6,  4,  5], # equation 1
        ...     [3, 5, 10,  3, -2], # equation 2
        ...     [1, 4, -5, 14,  1]  # equation 3
        ... ])
        ...
        >>> piv1._nbre_equations()
        3
        """
        n, _ = self._mat.shape
        return n

    def _nbre_variables(self) -> int:
        """Renvoie le nombre de variables correspondant au tableau passé en
        paramètre du constructeur.
        Exemple :
        >>> piv1 = PivotGaussSysteme([
        ... #    v  v   v   v   c
        ... #    a  a   a   a   s
        ... #    r  r   r   r   t
        ... #    1  2   3   4   e
        ... #
        ...     [2, 4,  6,  4,  5],
        ...     [3, 5, 10,  3, -2],
        ...     [1, 4, -5, 14,  1]
        ... ])
        ...
        >>> piv1._nbre_variables()
        4
        """
        _, m = self._mat.shape
        return m - 1 # le -1 correspond à la dernière colonne des constantes

    def _creer_noms_lignes(self) -> list[str]:
        """Renvoie la liste des noms de ligne au format LaTeX.
        Exemple pour 3 lignes :
        >>> piv1 = PivotGaussSysteme([
        ...     [2, 4,  6,  4], # L1
        ...     [3, 5, 10,  3], # L2
        ...     [1, 4, -5, 14]  # L3
        ... ])
        ...
        >>> piv1._nb_equ
        3
        >>> piv1._creer_noms_lignes()
        ['L_{1}', 'L_{2}', 'L_{3}']
        """
        res = []
        for i in range(self._nb_equ):
            res.append('L_{' + str(i + 1) + '}')
        return res

    def _creer_noms_variables(self) -> list[str]:
        """Renvoie la liste des noms de variables au format LateX.
        Exemple pour 3 variables :
        >>> piv1 = PivotGaussSysteme([
        ... #    x  y   z   cste    
        ...     [2, 4,  6,  4],
        ...     [3, 5, 10,  3],
        ...     [1, 4, -5, 14]
        ... ])
        ...
        >>> piv1._nb_var
        3
        >>> piv1._creer_nom_variables()
        ['x', 'y', 'z']
        Exemple pour 4 variables :
        >>> piv2 = PivotGaussSysteme([
        ... #    x1 x2  x3  x4  cste  
        ...     [2, 4,  6,  4,  5],
        ...     [3, 5, 10,  3, -2],
        ...     [1, 4, -5, 14,  1]
        ... ])
        ...
        >>> piv2._nb_var
        4
        >>> piv2._creer_nom_variables()
        ['x_{1}', 'x_{2}', 'x_{3}', 'x_{4}']
        """
        if self._nb_var < 4:
            return ['x', 'y', 'z'][:self._nb_var]
        else:
            return ['x_{' + str(i + 1) + '}' for i in range(self._nb_var)]

    def _creer_variables(self) -> list[Symbol]:
        """Renvoie la liste des variables (instances de la classe Symbol de
        sympy). Ces variables peuvent être utilisées dans des expressions
        algébriques et des équations avec sympy.
        Exemple pour 3 variables :
        >>> piv1 = PivotGaussSysteme([
        ...     [2, 4,  6,  4],
        ...     [3, 5, 10,  3],
        ...     [1, 4, -5, 14]
        ... ])
        ...
        >>> piv1._nb_var
        3
        >>> piv1._creer_variables()
        [Symbol('x'), Symbol('y'), Symbol('z')]
        """
        return [Symbol(nom) for nom in self._noms_variables]

    def _tab_latex_balise_ouvrante(self) -> str:
        """Renvoie la balise ouvrante LaTeX du tableau résultat.
        Exemple pour 3 variables :
        >>> piv1 = PivotGaussSysteme([
        ...     [2, 4,  6,  4],
        ...     [3, 5, 10,  3],
        ...     [1, 4, -5, 14]
        ... ])
        ...
        >>> piv1._nb_var
        3
        >>> print(self._tab_latex_balise_ouvrante())
        \begin{array}{l|ccc|c|}

        """
        return r'\begin{array}{l|' + 'c' * self._nb_var + '|c|}\n'

    def _tab_latex_balise_fermante(self) -> str:
        r"""Renvoie la balise ouvrante LaTeX du tableau résultat.
        Exemple :
        >>> print(self._tab_latex_balise_ouvrante())
        \end{array} \\

        """
        return r'\end{array}' + r' \\' + '\n'

    def _latex_tableau(self, num_etape) -> str:
        r"""Renvoie le code LateX de l'étape num_etape du tableau résultat
        (sans les balises ouvrante et fermante).
        Exemple :
        >>> piv1 = PivotGaussSysteme([
        ...     [2, 4,  6,  4],
        ...     [3, 5, 10,  3],
        ...     [1, 4, -5, 14]
        ... ])
        ...
        >>> print(piv1._latex_tableau(2))
            \hline
            L_{1} \leftarrow L_{1} & 1 & 2 & 3 & 2 \\
            L_{2} \leftarrow L_{2} - 3L_{1} & 0 & -1 & 1 & -3 \\
            L_{3} \leftarrow L_{3} - L_{1} & 0 & 2 & -8 & 12 \\
            \hline
        """
        res = r'    \hline' + '\n'
        for i in range(self._nb_equ):
            # formule en debut de ligne
            res += '    ' + self._operations[num_etape][i] + ' & '
            # ensuite les coefficients des variables
            for j in range(self._nb_var):
                res += latex(self._matrices[num_etape][i, j]) + ' & '
            # finalement la constante en fin de ligne
            res += latex(self._matrices[num_etape][i, self._nb_var]) + r' \\'
            res += '\n'
        res += r'    \hline' + '\n'
        return res

    def _est_ligne_zeros(self, i) -> bool:
        """Renvoie True si la ligne i de la matrice de l'étape courante (au
        cours de l'algorithme du pivot) est une ligne de zéros. Renvoie False
        dans le cas contraire.
        """
        return self._matrices[-1].row(i) == zeros(1, self._nb_var + 1)

    def _nbre_lignes_zeros(self) -> int:
        """Renvoie le nombre de lignes de zéros de la matrice de l'étape
        courante (au cours de l'algorithme du pivot)."""
        res = 0
        for i in range(self._nb_equ):
            if self._est_ligne_zeros(i):
                res += 1
        return res

    def _membre_gauche_equation(self, i):
        """Renvoie dans une chaîne au format LaTeX le membre de 
        gauchel'équation en ligne i de la matrice de l'étape courante (au cours 
        de l'algorithme du pivot).
        """
        res = ''
        for j in range(self._nb_var):
            coef = self._matrices[-1][i, j]
            if coef != 0:
                if res == '':
                    en_tete = True
                else:
                    en_tete = False
                coef = preparer_coef(coef, en_tete)
                var = self._noms_variables[j]
                res += coef + var
        if res == '':
            return '0'
        else:
            return res

    def _latex_systeme(self):
        r"""Renvoie dans une chaîne au format LaTeX, le système associé à la
        matrice de l'étape courante au cours de l'algorithme.
        Exemple :
        >>> piv1 = PivotGaussSysteme([
        ...    [2, 4,  6,  4],
        ...    [3, 5, 10,  3],
        ...    [1, 4, -5, 14]
        ... ])
        ...
        >>> print(piv1._latex_systeme())
        \begin{cases}
            x = 1 \\
            y = 2 \\
            z = -1 \\
        \end{cases} \\

        """
        res = ''
        if self._affichage_ligne_zeros:
            nbre_equations_conservees = self._nb_equ
        else:
            nbre_equations_conservees = self._nb_equ \
                                        - self._nbre_lignes_zeros(-1)
        #res += r' \\' + '\n'
        if nbre_equations_conservees > 1:
            res = r'\begin{cases}' + '\n'
        for i in range(self._nb_equ):
            if not self._est_ligne_zeros(i) or self._affichage_ligne_zeros:
                cste = latex(self._matrices[-1][i, -1])
                membre_gauche = self._membre_gauche_equation(i)
                res += '    ' + membre_gauche + " = " + cste + r' \\' + '\n'
        if nbre_equations_conservees > 1:
            res += r'\end{cases}' + r' \\' + '\n'
        return res #+ r' \\' + '\n'

    def _pivot_existe(self, j: int) -> bool:
        """Renvoie True si un pivot existe dans la colonne j de la matrice de
        l'étape courante (au cours de l'algorithme du pivot) et False sinon.
        """
        for i in range(j, self._nb_equ):
            if self._matrices[-1][i, j] != 0:
                return True
        return False

    def _indice_ligne_pivot(self, j: int):
        """Renvoie la ligne du pivot dans la colonne j de la matrice de
        l'étape courante (au cours de l'algorithme du pivot).
        """
        assert self._pivot_existe(j), "Pas de pivot dans cette colonne !"
        for i in range(j, self._nb_equ):
            if self._matrices[-1][i, j] != 0:
                return i

    def _pivot_deja_positionne(self, j: int) -> bool:
        """Renvoie True si le pivot de la colonne j de la matrice courante (au
        cours de l'algorithme du pivot) est déjà positionné sur la diagonale.
        Renvoie False dans le cas contraire.
        """
        return self._indice_ligne_pivot(j) == j

    def _ligne_pivot_deja_normalisee(self, i: int) -> bool:
        """Renvoie True si la ligne i de la matrice courante (au cours de
        l'algorithme du pivot) est déjà normalisée. Renvoie False dans le cas
        contraire.
        """
        return self._matrices[-1][i, i] == 1

    def _colonne_deja_echelonnee(self, j) -> bool:
        """Renvoie True si la colonne j de la matrice courante (au cours de
        l'algorithme du pivot) est déjà entièrement échelonnée. Renvoie False
        dans le cas contraire.
        """
        for i in range(self._nb_equ):
            if i != j and self._matrices[-1][i, j] != 0:
                return False
        return True

    def _echanger_lignes(self, i1, i2) -> None:
        """Échange les lignes i1 et i2 de la matrice courante (au cours de
        l'algorithme du pivot). Ajoute les opérations associées à la liste des
        opérations. Ne renvoie rien.
        """
        # Échange des lignes de la matrice courante
        self._matrices[-1] = self._matrices[-1].elementary_row_op(
            op="n<->m",
            row1=i1,
            row2=i2
        )
        # Modification des opérations dans la liste des opérations.
        self._operations[-1][i1] = self._noms_lignes[i1] + r' \leftarrow ' \
                                  + self._noms_lignes[i2]
        self._operations[-1][i2] = self._noms_lignes[i2] + r' \leftarrow ' \
                                  + self._noms_lignes[i1]

    def _initialiser_operations(self) -> list[str]:
        r"""Renvoie une liste d'opérations pour chaque ligne du tableau. Les
        opérations sont des chaînes au format LaTeX qui représente chacune
        l'absence d'opération pour la ligne désignée. Lors d'une étape de
        l'algorithme, si une ligne est modifiée, l'opération sera modifiée dans
        cette liste.
        Exemple :
        >>> piv1 = PivotGaussSysteme([
        ...    [2, 4,  6,  4],
        ...    [3, 5, 10,  3],
        ...    [1, 4, -5, 14]
        ... ])
        ...
        >>> piv1._initialiser_operations()
        [L_{1} \leftarrow L_{1}, L_{2} \leftarrow L_{2}, L_{3} \leftarrow L_{3}]
        """
        return [self._noms_lignes[i] + r' \leftarrow '
                + self._noms_lignes[i]
                for i in range(self._nb_equ)]

    def _ajouter_etape(self) -> None:
        """Ajoute une case pour l'étape courante de l'algorithme du pivot dans
        la liste des matrices et dans la liste des opérations. Ne renvoie rien.
        """
        # La nouvelle matrice est une copie de la matrice de l'étape précédente
        self._matrices.append(self._matrices[-1].copy())
        # Les nouvelles opérations sont initialisées et pourront être modifiées
        # par la suite.
        operations = self._initialiser_operations()
        self._operations.append(operations)

    def _positionner_pivot(self, j) -> None:
        """Identifie le pivot et le positionne sur la diagonale dans la
        matrice de l'étape courante de l'algorithme du pivot. Ne renvoie rien.
        """
        assert self._pivot_existe(j), "Pas de pivot dans cette colonne !"
        self._ajouter_etape()
        i_pivot = self._indice_ligne_pivot(j)
        self._echanger_lignes(i_pivot, j)

    def _normaliser_pivot(self, j) -> None:
        """Normalise la ligne du pivot dans la matrice de l'étape courante de
        l'algorithme du pivot. Ne renvoie rien.
        """
        assert self._pivot_deja_positionne(j), "Pivot à positionner d'abord !"
        self._ajouter_etape()
        inv_pivot = self._matrices[-1][j, j] ** -1
        self._matrices[-1] = self._matrices[-1].elementary_row_op(
            op="n->kn",
            row=j,
            k=inv_pivot
        )
        self._operations[-1][j] = self._noms_lignes[j] + r' \leftarrow ' \
                                + preparer_coef(inv_pivot, en_tete=True) \
                                + self._noms_lignes[j]

    def _echelonner_colonne(self, j) -> None:
        """Échelonne la colonne j de la matrice de l'étape courante de
        l'algorithme du pivot. Ne renvoie rien.
        """
        message = "Ligne du pivot à normaliser d'abord !"
        assert self._ligne_pivot_deja_normalisee(j), message
        self._ajouter_etape()
        for i in range(self._nb_equ):
            if i != j and self._matrices[-1][i, j] != 0:
                self._echelonner_case(i, j)


    def _echelonner_case(self, i, j) -> None:
        """Échelonne la case (i, j) de la matrice de l'étape courante de
        l'algorithme du pivot. Ne renvoie rien.
        """
        val_case = self._matrices[-1][i, j]
        self._matrices[-1] = self._matrices[-1].elementary_row_op(
            op="n->n+km",
            row=i,
            k=-val_case,
            row2=j
        )
        self._operations[-1][i] = self._noms_lignes[i] + r' \leftarrow ' \
                                 + self._noms_lignes[i] \
                                 + preparer_coef(-val_case) \
                                 + self._noms_lignes[j]

    def _traitement_colonne(self, j) -> None:
        """Réalise les étapes de traitement de la colonne j dans la matrice
        courante au cours de l'algorithme du pivot. Ne renvoie rien."""
        if not self._pivot_deja_positionne(j):
            self._positionner_pivot(j)
        if not self._ligne_pivot_deja_normalisee(j):
            self._normaliser_pivot(j)
        if not self._colonne_deja_echelonnee(j):
            self._echelonner_colonne(j)

    def _pivot(self) -> None:
        """Réalise l'algorithme du pivot de Gauss sur le tableau passé en
        paramètre du constructeur. Ne renvoie rien.
        Au cours de l'algorithme, les résultats intermédiaires sont stockés
        dans deux attributs :
            self.matrices: list[Matrix]
                liste des matrices de chaque étape
            self.operations: list[list[str]]
                liste des opérations appliquées à chaque étape au format
                LaTeX.
        """
        for j in range(self._nb_var):
            if self._pivot_existe(j):
                self._traitement_colonne(j)

    def _creer_latex(self) -> str:
        r"""Renvoie dans une chaîne l'ensemble des étapes de l'agorithme au
        format LaTeX (sauf le système de départ dèja ajouté précédemment).
            - pour chaque étape le tableau avec les opérations appliquées
            - puis le système dans sa version finale simplifiée.
        Exemple :
        >>> piv1 = PivotGaussSysteme([
        ...    [2, 4,  6,  4],
        ...    [3, 5, 10,  3],
        ...    [1, 4, -5, 14]
        ... ])
        ...
        >>> print(piv1._creer_latex())
        \begin{array}{l|ccc|c|}
            \hline
            L_{1} & 2 & 4 & 6 & 4 \\
            L_{2} & 3 & 5 & 10 & 3 \\
            L_{3} & 1 & 4 & -5 & 14 \\
            \hline
            \hline
            L_{1} \leftarrow \frac{1}{2}L_{1} & 1 & 2 & 3 & 2 \\
            L_{2} \leftarrow L_{2} & 3 & 5 & 10 & 3 \\
            L_{3} \leftarrow L_{3} & 1 & 4 & -5 & 14 \\
            \hline
            \hline
            L_{1} \leftarrow L_{1} & 1 & 2 & 3 & 2 \\
            L_{2} \leftarrow L_{2} - 3L_{1} & 0 & -1 & 1 & -3 \\
            L_{3} \leftarrow L_{3} - L_{1} & 0 & 2 & -8 & 12 \\
            \hline
            \hline
            L_{1} \leftarrow L_{1} & 1 & 2 & 3 & 2 \\
            L_{2} \leftarrow -L_{2} & 0 & 1 & -1 & 3 \\
            L_{3} \leftarrow L_{3} & 0 & 2 & -8 & 12 \\
            \hline
            \hline
            L_{1} \leftarrow L_{1} - 2L_{2} & 1 & 0 & 5 & -4 \\
            L_{2} \leftarrow L_{2} & 0 & 1 & -1 & 3 \\
            L_{3} \leftarrow L_{3} - 2L_{2} & 0 & 0 & -6 & 6 \\
            \hline
            \hline
            L_{1} \leftarrow L_{1} & 1 & 0 & 5 & -4 \\
            L_{2} \leftarrow L_{2} & 0 & 1 & -1 & 3 \\
            L_{3} \leftarrow -\frac{1}{6}L_{3} & 0 & 0 & 1 & -1 \\
            \hline
            \hline
            L_{1} \leftarrow L_{1} - 5L_{3} & 1 & 0 & 0 & 1 \\
            L_{2} \leftarrow L_{2} + L_{3} & 0 & 1 & 0 & 2 \\
            L_{3} \leftarrow L_{3} & 0 & 0 & 1 & -1 \\
            \hline
        \end{array} \\
        \begin{cases}
            x = 1 \\
            y = 2 \\
            z = -1 \\
        \end{cases} \\
        """
        res = self._tab_latex_balise_ouvrante()
        for i in range(self._nb_etapes):
            res += self._latex_tableau(i)
        res += self._tab_latex_balise_fermante()
        res += self._latex_systeme()
        return res
    
    def _envelopper_latex_dans_balises_align(self) -> None:
        r"""Enveloppe le code LaTeX contenu dans l'attribut self.latex entre
        des balises \begin{align} et \end{align}. Cela doit être fait
        uniquement si le Jupyter Notebook n'est pas exécuté dans Google Colab.
        Dans les environnements Jupyter Notebooks "classiques" le rendu est
        incorrect si les balises \begin{align} et \end{align} sont omises
        alors que c'est le contraire dans Google Colab.
        """
        self._latex = "\\begin{align*}\n" + self._latex + "\\end{align*}\n"

    def _repr_latex_(self) -> str:
        """Méthode spéciale spécifique à sympy qui permet de personnaliser
        l'affichage obtenu en dernière ligne de cellule dans un cahier Jupyter.
        Ici le code LaTeX est utilisé affichant élégamment :
        - le sytème d'équation correspondant au tableau passé en paramètre du
        constructeur ;
        - les tableaux décrivant chaque étape de l'algorithme ;
        - le système d'équation dans son état final simplifié.
        """
        return self._latex
    
    def __repr__(self) -> str:
        return self._latex
    
    def __str__(self) -> str:
        """Méthode spéciale définissant l'affichage obtenu avec la fonction
        print.
        """
        return self._latex


class PivotGaussInverseMatrice:

    """Classe permettant de représenter dans un cahier Jupyter les étapes de
    l'algorithme du pivot de Gauss pour l'inversion d'une matrice carrée.
    - La matrice de départ est passée en paramètre du constructeur sous forme
    d'un tableau 2D (ou d'une instance de la classe Matrix de sympy).
    - Le code LaTeX est produit.
    - On peut ensuite réaliser l'affichage en dernière ligne de cellule de
    cahier Jupyter.
    Si la matrice de départ n'est pas inversible, l'algorithme se déroule
    jusqu'à arriver à un blocage. Les étapes de l'algorithme sont affichées
    comme pour une matrice inversible.

    Exemple :
    piv1 = PivotGaussInverseMatrice([
        [ 1,  2, 3],
        [ 2,  5, 4],
        [-1, -3, 0]
    ])

    piv1 # à mettre en fin de cellule pour obtenir l'affichage naturel

    On peut ensuite obtenir le code LaTeX associé dans une nouvelle cellule
    avec :

    print(piv1)
    """

    def __init__(
            self,
            tab: list[list[int|float|Number]]|Matrix,
            module: int = None
        ) -> None:
        """Prend en paramètres:
            tab: list[list[int|float|Fraction|Number]]|Matrix
                tableau 2D de nombres représentant la matrice inversible à
                inverser par le pivot de Gauss. Les types de nombres possibles
                sont :
                    int
                    float
                    Fraction (du module fractions)
                    Number (tout type de nombre du module sympy)
                tab peut aussi être une instance de la classe Matrix de sympy
            module: int
                entier supérieur ou égal à 2. Par défaut à None. Si précisé,
                permet d'obtenir le pivot de Gauss pour inverser la matrice
                dans Z/moduleZ.
        """
        if module != None:
            assert isinstance(module, int), "module doit être du type int !"
            assert module >= 2, "module doit être supérieur ou égal à 2 !"
        self.module = module
        # tableau de départ convertit en instance de la classe Matrix de sympy
        # n'a aucun effet si tab est déjà une instance de la classe Matrix
        self._mat = Matrix(tab)
        # vérification de la validité de la matrice
        n, m = self._mat.shape
        assert n > 0, "La matrice doit posséder au moins une ligne !"
        assert m > 0, "La matrice doit posséder au moins une colonne !"
        assert n == m , "La matrice doit être carré !"
        #assert self.mat.det() != 0, "La matrice doit être inversible !"
        # dimensions de la matrice
        self._n = n
        self._noms_lignes = self._creer_noms_lignes()
        # la première matrice de gauche est la matrice de départ
        matrice_gauche = self._mat
        # la première matrice de droite est la matrice identité
        matrice_droite = eye(self._n)
        # liste des matrices fusion entre la matrice de gauche et de droite au
        # cours de l'algorithme
        self._matrices = [matrice_gauche.row_join(matrice_droite)]
        # liste des opérations sur les lignes à chaque étape de l'algorithme
        self._operations = [self._noms_lignes]
        # exécution de l'algorithme du pivot
        self._pivot()
        # Calcul du nombre d'étapes de l'algorithme du pivot
        self._nb_etapes = len(self._matrices)
        # Création du rendu en LaTeX
        self._latex = self._creer_latex()
        self.mat = self._mat
        self.inv = self._matrices[-1][:,m:2*m]

    def _creer_noms_lignes(self) -> list[str]:
        """Renvoie la liste des noms de ligne au format LaTeX.
        Exemple pour 3 lignes :
        >>> piv1 = PivotGaussInverseMatrice([
        ...     [ 1,  2, 3],
        ...     [ 2,  5, 4],
        ...     [-1, -3, 0]
        ... ])
        ...
        >>> piv1._creer_noms_lignes()
        ['L_{1}', 'L_{2}', 'L_{3}']
        """
        res = []
        for i in range(self._n):
            res.append('L_{' + str(i + 1) + '}')
        return res

    def _tab_latex_balise_ouvrante(self) -> str:
        """Renvoie la balise ouvrante LaTeX du tableau résultat.
        Exemple pour une matrice (3, 3) :
        >>> piv1 = PivotGaussInverseMatrice([
        ...     [ 1,  2, 3],
        ...     [ 2,  5, 4],
        ...     [-1, -3, 0]
        ... ])
        ...
        >>> print(self._tab_latex_balise_ouvrante())
        \begin{array}{l|ccc|ccc|}

        """
        return r'\begin{array}{l|' + 2*('c' * self._n + '|') + '}\n'

    def _tab_latex_balise_fermante(self) -> str:
        r"""Renvoie la balise ouvrante LaTeX du tableau résultat.
        Exemple :
        >>> piv1 = PivotGaussInverseMatrice([
        ...     [ 1,  2, 3],
        ...     [ 2,  5, 4],
        ...     [-1, -3, 0]
        ... ])
        ...
        >>> print(piv1._tab_latex_balise_ouvrante())
        \end{array} \\

        """
        return r'\end{array}' + r' \\' + '\n'

    def _latex_tableau(self, num_etape) -> str:
        r"""Renvoie le code LateX de l'étape num_etape du tableau résultat
        (sans les balises ouvrante et fermante).
        Exemple :
        >>> piv1 = PivotGaussInverseMatrice([
        ...     [ 1,  2, 3],
        ...     [ 2,  5, 4],
        ...     [-1, -3, 0]
        ... ])
        ...
        >>> print(piv1._latex_tableau(2))
            \hline
            L_{1} \leftarrow L_{1} - 2L_{2} & 1 & 0 & 7 & 5 & -2 & 0 \\
            L_{2} \leftarrow L_{2} & 0 & 1 & -2 & -2 & 1 & 0 \\
            L_{3} \leftarrow L_{3} + L_{2} & 0 & 0 & 1 & -1 & 1 & 1 \\
            \hline

        """
        res = r'    \hline' + '\n'
        for i in range(self._n):
            # opération en debut de ligne
            res += '    ' + self._operations[num_etape][i] + ' & '
            # ensuite les coefficients des deux matrices côte à côte
            ligne = [latex(self._matrices[num_etape][i, j]) \
                     for j in range(self._n*2)]
            res += ' & '.join(ligne)
            # Fin de ligne
            res += r' \\' + '\n'
        res += r'    \hline' + '\n'
        return res

    def _pivot_existe(self, j: int) -> bool:
        """Renvoie True si un pivot existe dans la colonne j de la matrice
        gauche de l'étape courante (au cours de l'algorithme du pivot) et False
        sinon.
        """
        for i in range(j, self._n):
            if self.module == None:
                if self._matrices[-1][i, j] != 0:
                    return True
            else:
                cong = ClasseCongruence(int(self._matrices[-1][i, j]), self.module)
                if cong.est_inversible():
                    return True
        return False

    def _indice_ligne_pivot(self, j: int):
        """Renvoie la ligne du pivot dans la colonne j de la matrice gauche de
        l'étape courante (au cours de l'algorithme du pivot).
        """
        assert self._pivot_existe(j), "Pas de pivot dans cette colonne !"
        for i in range(j, self._n):
            if self.module == None:
                if self._matrices[-1][i, j] != 0:
                    return i
            else:
                cong = ClasseCongruence(int(self._matrices[-1][i, j]), self.module)
                if cong.est_inversible():
                    return i


    def _pivot_deja_positionne(self, j: int) -> bool:
        """Renvoie True si le pivot de la colonne j de la matrice de gauche
        courante (au cours de l'algorithme du pivot) est déjà positionné sur la
        diagonale de la matrice de gauche. Renvoie False dans le cas contraire.
        """
        return self._indice_ligne_pivot(j) == j

    def _ligne_pivot_deja_normalisee(self, i: int) -> bool:
        """Renvoie True si la ligne i de la matrice de gauche courante (au
        cours de l'algorithme du pivot) est déjà normalisée. Renvoie False dans
        le cas contraire.
        """
        return self._matrices[-1][i, i] == 1

    def _colonne_deja_echelonnee(self, j) -> bool:
        """Renvoie True si la colonne j de la matrice de gauche courante (au
        cours de l'algorithme du pivot) est déjà entièrement échelonnée.
        Renvoie False dans le cas contraire.
        """
        for i in range(self._n):
            if i != j and self._matrices[-1][i, j] != 0:
                return False
        return True

    def _echanger_lignes(self, i1, i2) -> None:
        """Échange les lignes i1 et i2 des matrices courantes de gauche et de
        droite (au cours de l'algorithme du pivot). Ajoute les opérations
        associées à la liste des opérations. Ne renvoie rien.
        """
        # Échange des lignes de la matrice courante
        self._matrices[-1] = self._matrices[-1].elementary_row_op(
            op="n<->m",
            row1=i1,
            row2=i2
        )
        # Modification des opérations dans la liste des opérations.
        self._operations[-1][i1] = self._noms_lignes[i1] + r' \leftarrow ' \
                                  + self._noms_lignes[i2]
        self._operations[-1][i2] = self._noms_lignes[i2] + r' \leftarrow ' \
                                  + self._noms_lignes[i1]

    def _initialiser_operations(self) -> list[str]:
        r"""Renvoie une liste d'opérations pour chaque ligne du tableau. Les
        opérations sont des chaînes au format LaTeX qui représente chacune
        l'absence d'opération pour la ligne désignée. Lors d'une étape de
        l'algorithme, si une ligne est modifiée, l'opération sera modifiée dans
        cette liste.
        Exemple :
        >>> piv1 = PivotGaussInverseMatrice([
        ...     [ 1,  2, 3],
        ...     [ 2,  5, 4],
        ...     [-1, -3, 0]
        ... ])
        ...
        >>> piv1._initialiser_operations()
        [L_{1} \leftarrow L_{1}, L_{2} \leftarrow L_{2}, L_{3} \leftarrow L_{3}]
        """
        return [self._noms_lignes[i] + r' \leftarrow '
                + self._noms_lignes[i]
                for i in range(self._n)]

    def _ajouter_etape(self) -> None:
        """Ajoute une case pour l'étape courante de l'algorithme du pivot dans
        la liste des matrices et dans la liste des opérations. Ne renvoie rien.
        """
        # La nouvelle matrice est une copie de la matrice de l'étape précédente
        self._matrices.append(self._matrices[-1].copy())
        # Les nouvelles opérations sont initialisées et pourront être modifiées
        # par la suite.
        operations = self._initialiser_operations()
        self._operations.append(operations)

    def _positionner_pivot(self, j) -> None:
        """Identifie le pivot et le positionne sur la diagonale dans la
        matrice de gauche de l'étape courante de l'algorithme du pivot. Ne
        renvoie rien.
        """
        assert self._pivot_existe(j), "Pas de pivot dans cette colonne !"
        self._ajouter_etape()
        i_pivot = self._indice_ligne_pivot(j)
        self._echanger_lignes(i_pivot, j)

    def _normaliser_pivot(self, j) -> None:
        """Normalise la ligne du pivot dans la matrice de gauche de l'étape
        courante de l'algorithme du pivot. Ne renvoie rien.
        """
        assert self._pivot_deja_positionne(j), "Pivot à positionner d'abord !"
        self._ajouter_etape()
        if self.module == None:
            inv_pivot = self._matrices[-1][j, j] ** -1
        else:
            cong = ClasseCongruence(int(self._matrices[-1][j, j]), self.module)
            inv_cong = cong ** -1
            inv_pivot = inv_cong.reste
        self._matrices[-1] = self._matrices[-1].elementary_row_op(
            op="n->kn",
            row=j,
            k=inv_pivot
        )
        # calcul des restes modulaires
        if self.module != None:
            nlig, ncol = self._matrices[-1].shape
            for c in range(ncol):
                self._matrices[-1][j,c] = self._matrices[-1][j,c] % self.module
        self._operations[-1][j] = self._noms_lignes[j] + r' \leftarrow ' \
                                + preparer_coef(inv_pivot, en_tete=True) \
                                + self._noms_lignes[j]

    def _echelonner_colonne(self, j) -> None:
        """Échelonne la colonne j de la matrice de gauche de l'étape courante
        de l'algorithme du pivot. Ne renvoie rien.
        """
        message = "Ligne du pivot à normaliser d'abord !"
        assert self._ligne_pivot_deja_normalisee(j), message
        self._ajouter_etape()
        for i in range(self._n):
            if i != j and self._matrices[-1][i, j] != 0:
                self._echelonner_case(i, j)


    def _echelonner_case(self, i, j) -> None:
        """Échelonne la case (i, j) de la matrice de gauche l'étape courante de
        l'algorithme du pivot. Ne renvoie rien.
        """
        val_case = self._matrices[-1][i, j]
        self._matrices[-1] = self._matrices[-1].elementary_row_op(
            op="n->n+km",
            row=i,
            k=-val_case,
            row2=j
        )
        # calcul des restes modulaires
        if self.module != None:
            nlig, ncol = self._matrices[-1].shape
            for c in range(ncol):
                self._matrices[-1][i,c] = self._matrices[-1][i,c] % self.module
        self._operations[-1][i] = self._noms_lignes[i] + r' \leftarrow ' \
                                 + self._noms_lignes[i] \
                                 + preparer_coef(-val_case) \
                                 + self._noms_lignes[j]

    def _traitement_colonne(self, j) -> None:
        """Réalise les étapes de traitement de la colonne j dans la matrice
        courante de gauche au cours de l'algorithme du pivot. Ne renvoie rien.
        """
        if not self._pivot_deja_positionne(j):
            self._positionner_pivot(j)
        if not self._ligne_pivot_deja_normalisee(j):
            self._normaliser_pivot(j)
        if not self._colonne_deja_echelonnee(j):
            self._echelonner_colonne(j)

    def _pivot(self) -> None:
        """Réalise l'algorithme du pivot de Gauss sur le tableau passé en
        paramètre du constructeur. Ne renvoie rien.
        Au cours de l'algorithme, les résultats intermédiaires sont stockés
        dans deux attributs :
            self.matrices: list[Matrix]
                liste des matrices de chaque étape (fusion des matricess de
                gauche et de droite)
            self.operations: list[list[str]]
                liste des opérations appliquées à chaque étape au format
                LaTeX.
        """
        for j in range(self._n):
            if self._pivot_existe(j):
                self._traitement_colonne(j)

    def _creer_latex(self) -> str:
        r"""Renvoie dans une chaîne l'ensemble des étapes de l'agorithme au
        format LaTeX. À chaque étape on présente un tableau avec :
            - les opérations appliquées
            - la matrice de gauche
            - la matrice de droite
        Exemple :
        >>> piv1 = PivotGaussInverseMatrice([
        ...     [ 1,  2, 3],
        ...     [ 2,  5, 4],
        ...     [-1, -3, 0]
        ... ])
        ...
        >>> print(piv1._creer_latex())
        \begin{array}{l|ccc|ccc|}
            \hline
            L_{1} & 1 & 2 & 3 & 1 & 0 & 0 \\
            L_{2} & 2 & 5 & 4 & 0 & 1 & 0 \\
            L_{3} & -1 & -3 & 0 & 0 & 0 & 1 \\
            \hline
            \hline
            L_{1} \leftarrow L_{1} & 1 & 2 & 3 & 1 & 0 & 0 \\
            L_{2} \leftarrow L_{2} - 2L_{1} & 0 & 1 & -2 & -2 & 1 & 0 \\
            L_{3} \leftarrow L_{3} + L_{1} & 0 & -1 & 3 & 1 & 0 & 1 \\
            \hline
            \hline
            L_{1} \leftarrow L_{1} - 2L_{2} & 1 & 0 & 7 & 5 & -2 & 0 \\
            L_{2} \leftarrow L_{2} & 0 & 1 & -2 & -2 & 1 & 0 \\
            L_{3} \leftarrow L_{3} + L_{2} & 0 & 0 & 1 & -1 & 1 & 1 \\
            \hline
            \hline
            L_{1} \leftarrow L_{1} - 7L_{3} & 1 & 0 & 0 & 12 & -9 & -7 \\
            L_{2} \leftarrow L_{2} + 2L_{3} & 0 & 1 & 0 & -4 & 3 & 2 \\
            L_{3} \leftarrow L_{3} & 0 & 0 & 1 & -1 & 1 & 1 \\
            \hline
        \end{array} \\
        """
        res = self._tab_latex_balise_ouvrante()
        for i in range(self._nb_etapes):
            res += self._latex_tableau(i)
        res += self._tab_latex_balise_fermante()
        return res

    def _repr_latex_(self) -> str:
        """Méthode spéciale spécifique à sympy qui permet de personnaliser
        l'affichage obtenu en dernière ligne de cellule dans un cahier Jupyter.
        Ici le code LaTeX est utilisé affichant élégamment les tableaux
        décrivant chaque étape de l'algorithme.
        """
        return self._latex
    
    def __repr__(self) -> str:
        return self._latex
    
    def __str__(self):
        """Méthode spéciale définissant l'affichage obtenu avec la fonction
        print.
        """
        return self._latex
    

if __name__ == '__main__':
    piv1 = PivotGaussSysteme([
        [2, 4,  6,  4],
        [3, 5, 10,  3],
        [1, 4, -5, 14]
    ])
    print(piv1)
    piv2 = PivotGaussInverseMatrice([
        [ 1,  2, 3],
        [ 2,  5, 4],
        [-1, -3, 0]
    ])
    print(piv2)