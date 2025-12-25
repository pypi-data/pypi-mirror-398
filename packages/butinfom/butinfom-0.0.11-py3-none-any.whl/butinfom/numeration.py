from .utilitaires import entier_en_indice_unicode, tableau_en_array_latex
from typing_extensions import Self

def chiffres_base(base: int) -> list[str]:
    """Renvoie la liste des chiffres de la base (entier >= 2)."""
    assert isinstance(base, int), "base doit être du type int !"
    assert base >= 2, "base doit être supérieur ou égal à 2 !"
    res = []
    i = 0
    while i < base:
        if i < 10:
            res.append(str(i))
        else:
            res.append(chr(ord('A') + i - 10))
        i += 1
    return res

def zero(base: int):
    return EntierNat('0', base)

class EntierNat:

    def __init__(self, chaine: str, base: int = 10) -> None:
        assert isinstance(chaine, str), "chaine doit être du type str !"
        assert isinstance(base, int), "base doit être du type int !"
        assert base >= 2, "base doit être supérieur ou égal à 2 !"
        self.chaine = chaine
        self.base = base
        self.chiffres_base = chiffres_base(self.base)
        assert self._est_valide(), "Nombre invalide : chiffres et base incompatibles !"
        self.decimal = self._decimal()
        self.latex = self._latex()

    def _est_valide(self) -> bool:
        """Vérifie que les caractères utilisés dans la chaîne sont compatibles
        avec la base choisie."""
        for car in self.chaine:
            if car not in self.chiffres_base:
                return False
        return True
    
    def _decimal(self) -> int:
        """Renvoie la valeur décimale du nombre."""
        res = 0
        puissance = len(self.chaine) - 1
        for chiffre in self.chaine:
            val_chiffre = self.chiffres_base.index(chiffre)
            res += val_chiffre * self.base ** puissance
            puissance -= 1
        return res
    
    def changer_base(self, nouvelle_base: int, nb_chiffres_min: int = 1) -> None:
        """Change la base du nombre. Complète éventuellement le nombre par des
        zéros par la gauche si la chaîne du nombre après le changement de base
        est plus petit que nb_chiffres_min."""
        # Changement de la base
        self.base = nouvelle_base
        # Chiffres de la nouvelle base
        self.chiffres_base = chiffres_base(self.base)
        # Divisions successives
        chaine = ''
        quotient = self.decimal
        while quotient > 0:
            reste = quotient % self.base
            chaine = self.chiffres_base[reste] + chaine
            quotient = quotient // self.base
        if nb_chiffres_min > len(chaine):
            nb_zeros_a_ajouter = nb_chiffres_min - len(chaine)
            chaine = nb_zeros_a_ajouter * '0' + chaine
        self.chaine = chaine
        self.latex = self._latex()

    def _latex(self) -> str:
        """Renvoie une chaîne contenant le code LaTeX du nombre."""
        return r'(\text{' + self.chaine + '})_{' + str(self.base) + '}'

    def _repr_latex_(self) -> str:
        """Méthode spéciale spécifique à sympy qui permet de personnaliser
        l'affichage obtenu en dernière ligne de cellule dans un cahier Jupyter.
        """
        return self.latex
        
    def __str__(self):
        return '(' + self.chaine + ')' + entier_en_indice_unicode(self.base)
    
    def __repr__(self):
        return self.__str__()
    
    def __add__(self, autre: Self) -> Self:
        somme = self.decimal + autre.decimal
        res = EntierNat(str(somme), 10)
        res.changer_base(self.base)
        return res
    
    def __mul__(self, autre: Self) -> Self:
        somme = self.decimal * autre.decimal
        res = EntierNat(str(somme), 10)
        res.changer_base(self.base)
        return res
    
    def __eq__(self, autre: Self) -> bool:
        return self.decimal == autre.decimal
    
    def chiffres(self) -> list[Self]:
        """Renvoie le tableau des chiffres du nombre."""
        return [EntierNat(self.chaine[i], self.base) for i in range(len(self.chaine))]
    
    def nbre_chiffres(self) -> int:
        return len(self.chaine)


class TabConvChiffres:

    def __init__(self, base_depart: int, base_arrivee: int) -> None:
        assert isinstance(base_depart, int), "base_depart doit être un entier !"
        assert isinstance(base_arrivee, int), "base_arrivee doit être un entier !"
        assert base_depart >= base_arrivee, "base_depart doit être strictement superieur à base_arrivee !"
        self.base_depart = base_depart
        self.base_arrivee = base_arrivee
        self.tab = self._creer_tab()
        self.latex = tableau_en_array_latex(self.tab)   

    def _creer_tab(self) -> list[list[str]]:
        """Renvoie le tableau de conversion."""
        res = [
            [r'\text{écriture en base ' + str(self.base_depart) + '}'],
            [r'\text{écriture en base ' + str(self.base_arrivee) + '}']
        ]
        chiffres_base_depart = chiffres_base(self.base_depart)
        chiffre_max = chiffres_base_depart[-1]
        nbre_max = EntierNat(chiffre_max, self.base_depart)
        nbre_max.changer_base(self.base_arrivee)
        nb_chiffres_arrivee = len(nbre_max.chaine)
        for chiffre in chiffres_base_depart:
            nbre = EntierNat(chiffre, self.base_depart)
            res[0].append(nbre.latex)
            nbre.changer_base(self.base_arrivee, nb_chiffres_arrivee)
            res[1].append(nbre.latex)
        return res
    
    def __str__(self) -> str:
        return self.latex
    
    def __repr__(self) -> str:
        return self.latex
    
    def _repr_latex_(self) -> str:
        return self.latex
    

class TabOperation:

    def __init__(self, base: int, facteurs: list[str] = [], multiplication: bool = True) -> None:
        self.multiplication = multiplication
        assert isinstance(base, int), "base doit être un entier !"
        assert base >= 2, "base doit être supérieure ou égale à 2 !"
        self.base = base
        self.chiffres_base = chiffres_base(base)
        assert isinstance(facteurs, list), "facteurs doit être du type list !"
        for car in facteurs:
            assert isinstance(car, str), "facteurs ne doit contenir que des str !"
            assert car in self.chiffres_base, "facteurs ne doit contenir que des chiffres de la base !"
        self.facteurs = facteurs
        self.tab = self._creer_tab()
        self.latex = self._creer_latex()

    def _creer_tab(self):
        if self.multiplication:
            coin = r'\times'
        else: # addition
            coin = '+'
        res = [[coin] + [EntierNat(chiff, self.base).latex for chiff in self.chiffres_base]]
        if self.facteurs == []:
            self.facteurs = self.chiffres_base
        for fact in self.facteurs:
            facteur = EntierNat(fact, self.base)
            ligne = [facteur.latex]
            for chiff in self.chiffres_base:
                chiffre = EntierNat(chiff, self.base)
                if self.multiplication:
                    nbre = facteur * chiffre
                else: # addition
                    nbre = facteur + chiffre
                ligne.append(nbre.latex)
            res.append(ligne)
        return res
    
    def _creer_latex(self) -> str:
        format_col = 'c|' * len(self.tab[0])
        hlines = list(range(1, len(self.tab) + 1))
        return tableau_en_array_latex(self.tab, format_col, hlines)
    
    def __str__(self) -> str:
        return self.latex
    
    def __repr__(self) -> str:
        return self.latex
    
    def _repr_latex_(self) -> str:
        return self.latex


class AdditionPosee:

    def __init__(self, nbre1: str, nbre2: str, base: int) -> None:
        assert isinstance(base, int), "base doit être du type int !"
        assert base >= 2, "base doit être supérieur ou égal à 2 !"
        self.base = base
        self.n1 = EntierNat(nbre1, self.base)
        self.n2 = EntierNat(nbre2, self.base)
        if self.n1.decimal < self.n2.decimal:
            tmp = self.n1
            self.n1 = self.n2
            self.n2 = tmp
        self.tab = self._creer_tab()
        self.latex = self._creer_latex()

    def _creer_tab(self) -> list[EntierNat]:
        chiffres1 = [zero(self.base)] + self.n1.chiffres()
        retenues = [zero(self.base)] * len(chiffres1)
        chiffres2 = [zero(self.base)] * (len(chiffres1) - self.n2.nbre_chiffres()) + self.n2.chiffres()
        sommes = [zero(self.base)] * len(chiffres1)
        for i in range(len(chiffres2) + 1):
            res = retenues[-i] + chiffres1[-i] + chiffres2[-i]
            res.changer_base(self.base, nb_chiffres_min=2)
            sommes[-i] = EntierNat(res.chaine[1], self.base)
            if i < len(chiffres2):
                retenues[-i-1] = EntierNat(res.chaine[0], self.base)
        if sommes[0] == zero(self.base):
            retenues = retenues[1:]
            chiffres1 = chiffres1[1:]
            chiffres2 = chiffres2[1:]
            sommes = sommes[1:]
        # retrait des zéros inutiles
        for j in range(len(chiffres1) - self.n1.nbre_chiffres()):
            if chiffres1[j] == zero(self.base):
                chiffres1[j] = ''
        for j in range(len(chiffres2) - self.n2.nbre_chiffres()):
            if chiffres2[j] == zero(self.base):
                chiffres2[j] = ''
        for j in range(len(retenues)):
            if retenues[j] == zero(self.base):
                retenues[j] = ''
        tab = [
            ['', ''] + retenues + [''],
            ['', '('] + chiffres1 + [')_{' + str(self.base) + '}'],
            ['+', '('] + chiffres2 + [')_{' + str(self.base) + '}'],
            ['', '('] + sommes + [')_{' + str(self.base) + '}'],
        ]
        for i in range(len(tab)):
            for j in range(len(tab[0])):
                if isinstance(tab[i][j], EntierNat):
                    tab[i][j] = r'\text{' + tab[i][j].chaine + '}'
        for j in range(len(tab[0])):
            # retenues
            if tab[0][j] == '0' or tab[0][j] == '':
                tab[0][j] = ''
            else:
                tab[0][j] = '_' + tab[0][j]
            # chiffres1
            if j < len(tab[0]) - self.n1.nbre_chiffres() - 1 and tab[1][j] == '0':
                 tab[1][j] = ''
            # chiffres2
            if j < len(tab[0]) - self.n2.nbre_chiffres() - 1 and tab[2][j] == '0':
                 tab[2][j] = ''
        # sommes
        if tab[3][2] == '0' and len(tab[0]) > 4:
            tab[3][2] = ''
        return tab
    
    def _creer_latex(self) -> str:
        format_col = 'c' * len(self.tab[0])
        hlines = [len(self.tab) - 1]
        return tableau_en_array_latex(self.tab, format_col, hlines)
    
    def __str__(self) -> str:
        return self.latex
    
    def __repr__(self) -> str:
        return self.latex
    
    def _repr_latex_(self) -> str:
        return self.latex


class MultiplicationPosee:

    def __init__(self, nbre1: str, nbre2: str, base: int) -> None:
        assert isinstance(base, int), "base doit être du type int !"
        assert base >= 2, "base doit être supérieur ou égal à 2 !"
        self.base = base
        self.n1 = EntierNat(nbre1, self.base)
        self.n2 = EntierNat(nbre2, self.base)
        if self.n1.decimal < self.n2.decimal:
            tmp = self.n1
            self.n1 = self.n2
            self.n2 = tmp
        self.tab = self._creer_tab()
        self.latex = self._creer_latex()

    def _creer_tab(self) -> list[EntierNat]:
        nchiffres1 = self.n1.nbre_chiffres()
        nchiffres2 = self.n2.nbre_chiffres()
        produit = self.n1 * self.n2
        if nchiffres2 == 1:
            nlig = 3
        else:
            nlig = 3 + nchiffres2
        ncol = max(nchiffres1 + 2, produit.nbre_chiffres()) + 1
        tab = [['' for _ in range(ncol)] for _ in range(nlig)]
        # Nombre avant le trait d'opération
        for i in range(nchiffres1):
            tab[0][-i-1] = self.n1.chiffres()[-i-1]
        for i in range(nchiffres2):
            tab[1][-i-1] = self.n2.chiffres()[-i-1]
        # Ajout du symbole fois
        tab[1][-nchiffres1-2] = r'\times'
        # Calculs intermédiaires
        if self.n2.nbre_chiffres() > 1:
            for i in range(nchiffres2):
                prod = tab[1][-i-1] * self.n1
                nchiffres = prod.nbre_chiffres()
                for j in range(nchiffres + i):
                    if j < i:
                        # ajout des points
                        tab[i + 2][-j-1] = r'\cdot'
                    else:
                        # ajout du produit
                        tab[i + 2][-j-1] = prod.chiffres()[-j-1+i]
        # ajout du résultat
        res = self.n1 * self.n2
        for i in range(res.nbre_chiffres()):
            tab[-1][-i-1] = res.chiffres()[-i-1]
        # Conversion des EntierNat en chaînes de caractères
        for i in range(nlig):
            for j in range(ncol):
                if isinstance(tab[i][j], EntierNat):
                    tab[i][j] = r'\text{' + tab[i][j].chaine + '}'
        # Ajout des parenthèses et indices
        tab[0][-nchiffres1-1] = '('
        tab[1][-nchiffres1-1] = '('
        for i in range(2, nlig):
            tab[i][0] = '('
        for i in range(nlig):
            tab[i].append(')_{' + str(self.base) + '}')
        return tab
    
    def _creer_latex(self) -> str:
        format_col = 'c' * len(self.tab[0])
        if self.n2.nbre_chiffres() == 1:
            hlines = [2]
        else:
            hlines = [2, len(self.tab) - 1]
        return tableau_en_array_latex(self.tab, format_col, hlines)

    def __str__(self) -> str:
        return self.latex
    
    def __repr__(self) -> str:
        return self.latex
    
    def _repr_latex_(self) -> str:
        return self.latex


if __name__ == '__main__':
    mul1 = MultiplicationPosee('1456', '467', 10)
    print(mul1)