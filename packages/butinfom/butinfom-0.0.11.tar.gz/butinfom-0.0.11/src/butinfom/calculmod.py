from .utilitaires import entier_en_indice_unicode, tableau_en_array_latex
from .divisibilite import pgcd
from typing_extensions import Self


class ClasseCongruence:

    def __init__(self, nombre: int, module: int) -> None:
        assert isinstance(nombre, int), "nombre doit être un entier !"
        assert isinstance(module, int), "module doit être un entier !"
        assert module >= 2, "module doit être supérieur ou égal à 2 !"
        self.reste = nombre % module
        self.restes = [nbre for nbre in range(module)]
        self.module = module
        self.latex = self._creer_latex()

    def __eq__(self, autre) -> bool:
        return self.module == autre.module and self.reste == autre.reste

    def __add__(self, autre: Self) -> Self:
        assert self.module == autre.module, "Addition impossible : les classes de congruence n'ont pas le même module !"
        return ClasseCongruence(self.reste + autre.reste, self.module)

    def __mul__(self, autre: Self) -> Self:
        assert self.module == autre.module, "Multiplication impossible : les classes de congruence n'ont pas le même module !"
        return ClasseCongruence(self.reste * autre.reste, self.module)
    
    def __rtruediv__(self, autre: Self) -> Self:
        return ClasseCongruence(autre, self.module) * self.inv()
    
    def __pow__(self, puissance: int) -> Self:
        assert isinstance(puissance, int), "puissance doit être un entier !"
        if puissance < 0:
            facteur = self.inv()
            puissance = abs(puissance)
        else:
            facteur = self
        res = ClasseCongruence(1, self.module)
        for _ in range(puissance):
            res *= facteur
        return res

    def __str__(self) -> str:
        return '[' + str(self.reste) + ']' + entier_en_indice_unicode(self.module)
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def _repr_latex_(self) -> str:
        return self.latex

    def _creer_latex(self):
        return '[' + str(self.reste) + ']_{' + str(self.module) + '}'

    def est_inversible(self) -> bool:
        return pgcd(self.reste, self.module) == 1
    
    def inv(self, erreur=True) -> Self|None:
        assert self.est_inversible(), f"Pas d'inverse pour {self.__str__()} !"
        for reste in self.restes:
            if reste * self.reste % self.module == 1:
                return ClasseCongruence(reste, self.module)
           

class TabOperationMod:

    def __init__(self, module: int, multiplication: bool = False) -> None:
        assert isinstance(module, int), "module doit être un entier !"
        assert module >= 2, "module doit être supérieur ou égal à 2 !"
        self.module = module
        self.restes = ClasseCongruence(0, module).restes
        self.classes = [ClasseCongruence(nbre, self.module) for nbre in self.restes]
        self.multiplication = multiplication
        self.tab = self._creer_tab()
        self.latex = self._creer_latex()

    def __str__(self) -> str:
        return self.latex
    
    def __repr__(self) -> str:
        return self.latex
    
    def _repr_latex_(self) -> str:
        return self.latex

    def _creer_latex(self) -> str:
        format_col = 'c|' * len(self.tab[0])
        hlines = list(range(1, len(self.tab) + 1))
        return tableau_en_array_latex(self.tab, format_col, hlines)

    def _creer_tab(self) -> list[str]:
        if self.multiplication:
            coin = r'\times'
        else: # addition
            coin = '+'
        res = [[coin] + [classe.latex for classe in self.classes]]
        for classe1 in self.classes:
            ligne = [classe1.latex]
            for classe2 in self.classes:
                if self.multiplication:
                    resultat = classe1 * classe2
                else: # addition
                    resultat = classe1 + classe2
                ligne.append(resultat.latex)
            res.append(ligne)
        return res


if __name__ == "__main__":
    cong1 = ClasseCongruence(7, 10)
    cong2 = ClasseCongruence(2, 10)
    print(cong1.est_inversible())
    print(cong2.est_inversible())
    print(cong1.inv())
    print(cong1**-1)
    print(1/cong1)