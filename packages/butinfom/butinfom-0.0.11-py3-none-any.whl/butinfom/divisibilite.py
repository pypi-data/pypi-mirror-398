from .utilitaires import preparer_coef, tableau_en_array_latex, envelopper_latex_dans_balises_align, execute_dans_google_colab

def pgcd(a: int, b: int) -> int:
    assert isinstance(a, int), "a doit être un entier !"
    assert isinstance(b, int), "b doit être un entier !"
    assert a != 0 or b != 0, "0 et 0 n'ont pas de PGCD !"
    a = abs(a)
    b = abs(b)
    if a < b:
        a, b = b, a
    if b == 0:
        return a
    while a % b != 0:
        tmp = b
        b = a % b
        a = tmp
    return b


class EuclideEtendu:

    def __init__(self, nbre1: int, nbre2: int) -> None:
        assert isinstance(nbre1, int), "nbre1 doit être du type int !"
        assert isinstance(nbre2, int), "nbre2 doit être du type int !"
        assert nbre1 != 0, "nbre1 doit être non-nul !"
        assert nbre2 != 0, "nbre2 doit être non-nul !"
        if abs(nbre2) > abs(nbre1):
            tmp = nbre1
            nbre1 = nbre2
            nbre2 = tmp
        self.nbre1 = nbre1
        self.nbre2 = nbre2
        self.tab = self._creer_tab()
        self.equation = self._creer_equation()
        self.latex = self._creer_latex()
        
    def _creer_tab(self) -> list[str]:
        reste = abs(self.nbre1) % abs(self.nbre2)
        tab = [
            [r'\text{ligne}', 'x', 'y', 'ax + by \\text{ (reste)}', r'\text{quotient}'],
            [        'L_{1}',   1,   0,            abs(self.nbre1),                 ''],
            [        'L_{2}',   0,   1,            abs(self.nbre2),                 '']
        ]
        i = 3
        while reste != 0:
            quotient = tab[-2][3] // tab[-1][3]
            tab[-1][4] = quotient
            reste = tab[-2][3] % tab[-1][3]
            tab.append([''] * 5)
            tab[-1][3] = reste
            if reste != 0:
                tab[-1][0] = 'L_{' + str(i) + '} = L_{' + str(i - 2) + '}' + preparer_coef(-quotient) + 'L_{' + str(i - 1) + '}'
                tab[-1][1] = tab[-3][1] - quotient * tab[-2][1]
                tab[-1][2] = tab[-3][2] - quotient * tab[-2][2]
            i += 1
        for i in range(len(tab)):
            for j in range(len(tab[0])):
                if not isinstance(tab[i][j], str):
                    tab[i][j] = str(tab[i][j]) 
        return tab
    
    def _creer_equation(self):
        x = int(self.tab[-2][1])
        y = int(self.tab[-2][2])
        dernier_reste = str(self.tab[-2][3])
        if self.nbre1 < 0:
            x = -x
        if self.nbre2 < 0:
            y = -y
        xbold = r'\boldsymbol{' + str(x) + '}'
        if y < 0:
            ybold = r'\boldsymbol{(' + str(y) + ')}'
        else:
            ybold = r'\boldsymbol{' + str(y) + '}'
        nbre1 = str(self.nbre1)
        nbre2 = str(self.nbre2)
        if self.nbre1 < 0:
            nbre1 = '(' + nbre1 + ')'
        if self.nbre2 < 0:
            nbre2 = '(' + nbre2 + ')'
        membre_gauche_normal = nbre1 + r' \wedge ' + nbre2
        membre_gauche_positif = str(abs(self.nbre1)) + r' \wedge ' + str(abs(self.nbre2))
        membre_droite = xbold + r' \times ' + nbre1 + ' + ' + ybold + r' \times ' + nbre2
        if self.nbre1 > 0 and self.nbre2 > 0:
            return membre_gauche_normal + ' = ' + dernier_reste + ' = ' + membre_droite + '\n'
        else:
            return membre_gauche_normal + ' = ' + membre_gauche_positif + ' = ' + dernier_reste + ' = ' + membre_droite + '\n'
    
    def _creer_latex(self) -> str:
        format_col = 'l|ccccc'
        hlines = [1]
        res = tableau_en_array_latex(self.tab, format_col, hlines)
        res += r'\\' + '\n' + self.equation
        if not execute_dans_google_colab():
            return envelopper_latex_dans_balises_align(res)
        else:
            return res
    
    def __str__(self) -> str:
        return self.latex
    
    def __repr__(self) -> str:
        return self.latex
    
    def _repr_latex_(self) -> str:
        return self.latex


if __name__ == '__main__':
    print(pgcd(0, 0))