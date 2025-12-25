from sympy import Matrix, latex
from .utilitaires import tableau_en_array_latex, retrait_sauts_ligne, formattage_chaine, execute_dans_google_colab, envelopper_latex_dans_balises_align
from .pivotgauss import PivotGaussInverseMatrice

# tirade du nez (extrait)
MESSAGE_EXEMPLE_FR = """
AH ! NON ! C’EST UN PEU COURT, JEUNE HOMME !
ON POUVAIT DIRE… OH ! DIEU ! … BIEN DES CHOSES EN SOMME…
EN VARIANT LE TON, - PAR EXEMPLE, TENEZ :
AGRESSIF : " MOI, MONSIEUR, SI J'AVAIS UN TEL NEZ,
IL FAUDRAIT SUR-LE-CHAMP QUE JE ME L'AMPUTASSE ! "
AMICAL : " MAIS IL DOIT TREMPER DANS VOTRE TASSE
POUR BOIRE, FAITES-VOUS FABRIQUER UN HANAP ! "
DESCRIPTIF : " C'EST UN ROC ! … C’EST UN PIC ! … C'EST UN CAP !
QUE DIS-JE, C'EST UN CAP ? … C'EST UNE PENINSULE ! "
CURIEUX : " DE QUOI SERT CETTE OBLONGUE CAPSULE ?
D'ECRITOIRE, MONSIEUR, OU DE BOITE A CISEAUX ? "
GRACIEUX : " AIMEZ-VOUS A CE POINT LES OISEAUX
QUE PATERNELLEMENT VOUS VOUS PREOCCUPATES
DE TENDRE CE PERCHOIR A LEURS PETITES PATTES ? "
TRUCULENT : " CA, MONSIEUR, LORSQUE VOUS PETUNEZ,
LA VAPEUR DU TABAC VOUS SORT-ELLE DU NEZ
SANS QU'UN VOISIN NE CRIE AU FEU DE CHEMINEE ? "
PREVENANT : " GARDEZ-VOUS, VOTRE TETE ENTRAINEE
PAR CE POIDS, DE TOMBER EN AVANT SUR LE SOL ! "
TENDRE : " FAITES-LUI FAIRE UN PETIT PARASOL
DE PEUR QUE SA COULEUR AU SOLEIL NE SE FANE ! "
"""

# préambule de déclaration d'indépendance des États-Unis
MESSAGE_EXEMPLE_EN = """
WE THE PEOPLE OF THE UNITED STATES, IN ORDER TO FORM A MORE PERFECT UNION,
ESTABLISH JUSTICE, INSURE DOMESTIC TRANQUILITY, PROVIDE FOR THE COMMON DEFENCE,
PROMOTE THE GENERAL WELFARE, AND SECURE THE BLESSINGS OF LIBERTY TO OURSELVES
AND OUR POSTERITY, DO ORDAIN AND ESTABLISH THIS CONSTITUTION FOR THE UNITED
STATES OF AMERICA.
"""


class MessageAlphabet:

    def __init__(
            self,
            message: str,
            alphabet: list[str] = None,
            alphabet_auto: bool = False,
            ignorer_car_hors_alphabet: bool = True
        ):
        # vérification du message
        assert isinstance(message, str), "message doit être du type str !"
        message = retrait_sauts_ligne(message)
        # alphabets par défaut
        if alphabet == None and not alphabet_auto:
            # lettres majuscules non accentuées
            alphabet = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
        elif alphabet_auto:
            # l'alphabet est l'ensemble des caractères rencontrés dans le message
            alphabet = []
            for car in message:
                if car not in alphabet:
                    alphabet.append(car)
            alphabet.sort()
        else:
            assert isinstance(alphabet, list), "alphabet doit être du type list !"
            dico_car = {}
            for car in alphabet:
                assert isinstance(car, str), "chaque élément de alphabet doit être du type str !"
                assert len(car) == 1, "chaque élément de alphabet doit être un caractère (str de longueur 1) !"
                assert car not in dico_car, "l'alphabet contient un doublon !"
                dico_car[car] = 1
            if not ignorer_car_hors_alphabet:
                for car in message:
                    assert car in alphabet, f"Le caractère {car} du message n'est pas dans l'alphabet. Ajoutez-le ou passez ignorer_car_hors_alphabet ou alphabet_auto à True !"
        self.message = message
        self.alphabet = alphabet
        self.alphabet_auto = alphabet_auto
        self.ignorer_car_hors_alphabet = ignorer_car_hors_alphabet


class ChiffreCesar:

    def __init__(
            self,
            mess_clair: str,
            cle: int,
            alphabet: list[str] = None,
            alphabet_auto: bool = False,
            ignorer_car_hors_alphabet: bool = True,
            car_par_ligne_max: int = 20,
            larg_formattage_message: int = 79,
            dechiffrer: bool = False
        ):
        mess_alpha = MessageAlphabet(
            message = mess_clair,
            alphabet = alphabet,
            alphabet_auto = alphabet_auto,
            ignorer_car_hors_alphabet = ignorer_car_hors_alphabet
        )
        assert isinstance(cle, int), "cle doit être du type int !"
        assert isinstance(larg_formattage_message, int), "larg_formattage_message doit être du type int !"
        assert larg_formattage_message > 1, "larg_formattage_message doit être strictement positif !"
        self.mess_clair = mess_alpha.message
        self.cle = cle
        self.alphabet = mess_alpha.alphabet
        self.alphabet_auto = mess_alpha.alphabet_auto
        self.ignorer_car_hors_alphabet = mess_alpha.ignorer_car_hors_alphabet
        self.car_par_ligne_max = car_par_ligne_max
        self.larg_formattage_message = larg_formattage_message
        self.dechiffrer = dechiffrer
        self.nbres_clair = self._creer_tab_nbres_clair()
        self.nbres_chiff = self._creer_tab_nbres_chiff()
        self.nbres_chiff_mod = self._creer_tab_nbres_chiff_mod()
        self.mess_chiff = self._creer_mess_chiff()
        self.tabs = self._creer_tabs()
        self.latex = self._creer_latex()
        self.mess_clair_format = formattage_chaine(self.mess_clair, self.larg_formattage_message)
        self.mess_chiff_format = formattage_chaine(self.mess_chiff, self.larg_formattage_message)

    def __str__(self) -> str:
        return self.latex

    def __repr__(self) -> str:
        return self.latex
    
    def _repr_latex_(self) -> str:
        return self.latex

    def _creer_tab_nbres_clair(self) -> list[int]:
        res = []
        for car in self.mess_clair:
            if car in self.alphabet:
                res.append(self.alphabet.index(car))
            else:
                res.append('')
        return res
    
    def _creer_tab_nbres_chiff(self) -> list[int]:
        res = []
        for nbre in self.nbres_clair:
            if nbre == '':
                res.append('')
            else:
                if self.dechiffrer:
                    res.append(nbre - self.cle)
                else:
                    res.append(nbre + self.cle)
        return res
    
    def _creer_tab_nbres_chiff_mod(self) -> list[int]:
        res = []
        for nbre in self.nbres_chiff:
            if nbre == '':
                res.append('')
            else:
                res.append(nbre % len(self.alphabet))
        return res
    
    def _creer_mess_chiff(self) -> str:
        res = []
        for i in range(len(self.mess_clair)):
            if self.nbres_chiff[i] == '':
                res.append(self.mess_clair[i])
            else:
                res.append(self.alphabet[self.nbres_chiff[i] % len(self.alphabet)])
        return ''.join(res)

    def _creer_tabs(self) -> list[list[list[str]]]:
        if self.dechiffrer:
            signe = '-'
        else:
            signe = '+'
        res = []
        i = 0
        nbre_car_ligne = 0
        while i < len(self.mess_clair):
            if nbre_car_ligne == 0:
                # initialisation d'un nouveau sous-tableau
                tab = [
                    [''],    # 0 : ligne du message clair
                    [''],    # 1 : ligne des nombres clairs
                    [signe], # 2 : ligne de l'ajout de la clé
                    [''],    # 3 : ligne des nombres chiffrés avant modulo longueur de l'alphabet
                    [''],    # 4 : ligne des nombres chiffrés après modulo longueur de l'alphabet
                    ['']     # 5 : ligne du message chiffré
                ]
            if nbre_car_ligne < self.car_par_ligne_max and i < len(self.mess_clair):
                # complétion du tableau courant colonne par colonne
                tab[0].append('\\text{' + self.mess_clair[i] + '}')
                tab[1].append(str(self.nbres_clair[i]))
                if self.nbres_chiff[i] == '':
                    tab[3].append('')
                    tab[4].append('')
                    tab[2].append('')
                elif self.nbres_chiff[i] == self.nbres_chiff[i] % len(self.alphabet):
                    tab[2].append(str(self.cle))
                    tab[3].append(str(self.nbres_chiff[i]))
                    tab[4].append('')
                else:
                    tab[2].append(str(self.cle))
                    tab[3].append('\\cancel{' + str(self.nbres_chiff[i]) + '}') # à barrer
                    tab[4].append(str(self.nbres_chiff_mod[i]))
                tab[5].append('\\text{' + self.mess_chiff[i] + '}')
                nbre_car_ligne += 1
                i += 1
            if nbre_car_ligne == self.car_par_ligne_max or i == len(self.mess_clair):
                # ajout du tableau courant fini au tableau de tableaux résultat
                res.append(tab)
                nbre_car_ligne = 0
        return res

    def _creer_latex(self) -> str:
        if not execute_dans_google_colab():
            debut_ligne = '&' # pour aligner à gauche le texte
        else:
            debut_ligne = '' # & est inutile et empêche l'affichage LaTeX dans Google Colab
        res = ''
        for tab in self.tabs:
            res += debut_ligne + "\\text{Taille de l'alphabet : }" + str(len(self.alphabet)) + r' \\' + '\n'
            res += debut_ligne + "\\text{Clé : }" + str(self.cle) + r' \\' + '\n'
            if self.dechiffrer:
                mode = 'Déchiffrement'
            else:
                mode = 'Chiffrement'
            res += debut_ligne + "\\text{Mode : " + mode + r"} \\" + '\n'
            format_col = 'c' * len(tab[0])
            res += debut_ligne + tableau_en_array_latex(tab, format_col, hlines=[3])
            res += r'\\' + '\n'
            res += r'\\' + '\n'
        if not execute_dans_google_colab():
            return envelopper_latex_dans_balises_align(res)
        else:
            return res


class ChiffreVigenere:

    def __init__(
            self,
            mess_clair: str,
            cle: str,
            alphabet: list[str] = None,
            alphabet_auto: bool = False,
            ignorer_car_hors_alphabet: bool = True,
            car_par_ligne_max: int = 20,
            larg_formattage_message: int = 79,
            dechiffrer: bool = False
        ):
        mess_alpha = MessageAlphabet(
            message = mess_clair,
            alphabet = alphabet,
            alphabet_auto = alphabet_auto,
            ignorer_car_hors_alphabet = ignorer_car_hors_alphabet
        )
        assert isinstance(larg_formattage_message, int), "larg_formattage_message doit être du type int !"
        assert larg_formattage_message > 1, "larg_formattage_message doit être strictement positif !"
        self.mess_clair = mess_alpha.message
        self.alphabet = mess_alpha.alphabet
        assert isinstance(cle, str), "cle doit être du type str !"
        for car in cle:
            assert car in self.alphabet, "Le caractère {car} de la clé n'est pas dans l'alphabet !"
        self.cle = cle
        self.alphabet_auto = mess_alpha.alphabet_auto
        self.ignorer_car_hors_alphabet = mess_alpha.ignorer_car_hors_alphabet
        self.car_par_ligne_max = car_par_ligne_max
        self.larg_formattage_message = larg_formattage_message
        self.dechiffrer = dechiffrer
        self.nbres_clair = self._creer_tab_nbres_clair()
        self.cle_sur_mess = self._creer_tab_cle_sur_mess()
        self.nbres_cle_sur_mess = self._creer_tab_nbres_cle_sur_mess()
        self.nbres_chiff = self._creer_tab_nbres_chiff()
        self.nbres_chiff_mod = self._creer_tab_nbres_chiff_mod()
        self.mess_chiff = self._creer_mess_chiff()
        self.tabs = self._creer_tabs()
        self.latex = self._creer_latex()
        self.mess_clair_format = formattage_chaine(self.mess_clair, self.larg_formattage_message)
        self.mess_chiff_format = formattage_chaine(self.mess_chiff, self.larg_formattage_message)

    def __str__(self) -> str:
        return self.latex

    def __repr__(self) -> str:
        return self.latex
    
    def _repr_latex_(self) -> str:
        return self.latex

    def _creer_tab_nbres_clair(self) -> list[int]:
        res = []
        for car in self.mess_clair:
            if car in self.alphabet:
                res.append(self.alphabet.index(car))
            else:
                res.append('')
        return res
    
    def _creer_tab_cle_sur_mess(self):
        res = []
        i = 0
        for car in self.mess_clair:
            if i == len(self.cle):
                i = 0
            if car in self.alphabet:
                res.append(self.cle[i])
                i += 1
            else:
                res.append('')
        return res

    def _creer_tab_nbres_cle_sur_mess(self):
        res = []
        for car in self.cle_sur_mess:
            if car == '':
                res.append('')
            else:
                res.append(self.alphabet.index(car))
        return res
    
    def _creer_tab_nbres_chiff(self) -> list[int]:
        res = []
        for i in range(len(self.nbres_clair)):
            if self.nbres_clair[i] == '':
                res.append('')
            else:
                if self.dechiffrer:
                    res.append(self.nbres_clair[i] - self.nbres_cle_sur_mess[i])
                else:
                    res.append(self.nbres_clair[i] + self.nbres_cle_sur_mess[i])
        return res
    
    def _creer_tab_nbres_chiff_mod(self) -> list[int]:
        res = []
        for nbre in self.nbres_chiff:
            if nbre == '':
                res.append('')
            else:
                res.append(nbre % len(self.alphabet))
        return res
    
    def _creer_mess_chiff(self) -> str:
        res = []
        for i in range(len(self.mess_clair)):
            if self.nbres_chiff[i] == '':
                res.append(self.mess_clair[i])
            else:
                res.append(self.alphabet[self.nbres_chiff[i] % len(self.alphabet)])
        return ''.join(res)

    def _creer_tabs(self) -> list[list[list[str]]]:
        if self.dechiffrer:
            signe = '-'
        else:
            signe = '+'
        res = []
        i = 0
        nbre_car_ligne = 0
        while i < len(self.mess_clair):
            if nbre_car_ligne == 0:
                # initialisation d'un nouveau sous-tableau
                tab = [
                    [''],    # 0 : ligne du message clair
                    [''],    # 1 : ligne des nombres clairs
                    [''],    # 2 : ligne de de la clé sur le message
                    [signe], # 3 : ligne des nombres de la clé sur le message
                    [''],    # 4 : ligne des nombres chiffrés avant modulo longueur de l'alphabet
                    [''],    # 5 : ligne des nombres chiffrés après modulo longueur de l'alphabet
                    ['']     # 6 : ligne du message chiffré
                ]
            if nbre_car_ligne < self.car_par_ligne_max and i < len(self.mess_clair):
                # complétion du tableau courant colonne par colonne
                tab[0].append('\\text{' + self.mess_clair[i] + '}')
                tab[1].append(str(self.nbres_clair[i]))
                if self.nbres_chiff[i] == '':
                    tab[2].append('')
                    tab[3].append('')
                    tab[4].append('')
                    tab[5].append('')
                elif self.nbres_chiff[i] == self.nbres_chiff[i] % len(self.alphabet):
                    tab[2].append('\\text{' + self.cle_sur_mess[i] + '}')
                    tab[3].append(str(self.nbres_cle_sur_mess[i]))
                    tab[4].append(str(self.nbres_chiff[i]))
                    tab[5].append('')
                else:
                    tab[2].append('\\text{' + self.cle_sur_mess[i] + '}')
                    tab[3].append(str(self.nbres_cle_sur_mess[i]))
                    tab[4].append('\\cancel{' + str(self.nbres_chiff[i]) + '}') # à barrer
                    tab[5].append(str(self.nbres_chiff_mod[i]))
                tab[6].append('\\text{' + self.mess_chiff[i] + '}')
                nbre_car_ligne += 1
                i += 1
            if nbre_car_ligne == self.car_par_ligne_max or i == len(self.mess_clair):
                # ajout du tableau courant fini au tableau de tableaux résultat
                res.append(tab)
                nbre_car_ligne = 0
        return res

    def _creer_latex(self) -> str:
        if not execute_dans_google_colab():
            debut_ligne = '&' # pour aligner à gauche le texte
        else:
            debut_ligne = '' # & est inutile et empêche l'affichage LaTeX dans Google Colab
        res = ''
        for tab in self.tabs:
            res += debut_ligne + "\\text{Taille de l'alphabet : }" + str(len(self.alphabet)) + r' \\' + '\n'
            res += debut_ligne + "\\text{Clé : " + self.cle + '}' + r' \\' + '\n'
            if self.dechiffrer:
                mode = 'Déchiffrement'
            else:
                mode = 'Chiffrement'
            res += debut_ligne + "\\text{Mode : " + mode + r"} \\" + '\n'
            format_col = 'c' * len(tab[0])
            res += debut_ligne + tableau_en_array_latex(tab, format_col, hlines=[4])
            res += r'\\' + '\n'
            res += r'\\' + '\n'
        if not execute_dans_google_colab():
            return envelopper_latex_dans_balises_align(res)
        else:
            return res
        

class ChiffreHill:

    def __init__(
            self,
            mess_clair: str,
            cle: list[list[int]]|Matrix,
            alphabet: list[str] = None,
            alphabet_auto: bool = False,
            ignorer_car_hors_alphabet: bool = True,
            car_par_ligne_max: int = 20,
            larg_formattage_message: int = 79,
            dechiffrer: bool = False
        ):
        mess_alpha = MessageAlphabet(
            message = mess_clair,
            alphabet = alphabet,
            alphabet_auto = alphabet_auto,
            ignorer_car_hors_alphabet = ignorer_car_hors_alphabet
        )
        assert isinstance(cle, (list, Matrix)), "cle doit être du type list ou sympy.Matrix !"
        self.cle = Matrix(cle)
        assert isinstance(larg_formattage_message, int), "larg_formattage_message doit être du type int !"
        assert larg_formattage_message > 1, "larg_formattage_message doit être strictement positif !"
        self.mess_clair = mess_alpha.message
        self.alphabet = mess_alpha.alphabet
        self.nbre_car_de_alphabet = self._calculer_nbre_car_alphabet()
        self.nbre_car_manquant = self._calculer_nbre_car_manquant()
        n, m = self.cle.shape
        message = f"Taille du message en nombre de caractère(s) de l'alphabet ({self.nbre_car_de_alphabet}) incompatible avec la dimension de la clé ({n})!"
        message += f"\nEn effet, {self.nbre_car_de_alphabet} % {n} vaut {(n - self.nbre_car_manquant) % n} !"
        message += f"\nAjouter {self.nbre_car_manquant} caractère(s) ou retirer {(n - self.nbre_car_manquant) % n} caractère(s) au message !"
        assert self.nbre_car_manquant == 0, message
        piv = PivotGaussInverseMatrice(self.cle, module=len(self.alphabet))
        self.inv_cle = piv.inv
        self.alphabet_auto = mess_alpha.alphabet_auto
        self.ignorer_car_hors_alphabet = mess_alpha.ignorer_car_hors_alphabet
        self.car_par_ligne_max = car_par_ligne_max
        self.larg_formattage_message = larg_formattage_message
        self.dechiffrer = dechiffrer
        self.nbres_clair = self._creer_tab_nbres_clair()
        self.tab_groupes_coord = self._creer_tab_groupes_coord()
        self.nbres_chiff = self._creer_tab_nbres_chiff()
        self.nbres_chiff_mod = self._creer_tab_nbres_chiff_mod()
        self.mess_chiff = self._creer_mess_chiff()
        self.tabs = self._creer_tabs()
        self.latex = self._creer_latex()
        self.mess_clair_format = formattage_chaine(self.mess_clair, self.larg_formattage_message)
        self.mess_chiff_format = formattage_chaine(self.mess_chiff, self.larg_formattage_message)

    def __str__(self) -> str:
        return self.latex

    def __repr__(self) -> str:
        return self.latex
    
    def _repr_latex_(self) -> str:
        return self.latex

    def _creer_tab_nbres_clair(self) -> list[int]:
        res = []
        for car in self.mess_clair:
            if car in self.alphabet:
                res.append(self.alphabet.index(car))
            else:
                res.append('')
        return res
    
    def _calculer_nbre_car_alphabet(self):
        res = 0
        for car in self.mess_clair:
            if car in self.alphabet:
                res += 1
        return res
    
    def _calculer_nbre_car_manquant(self):
        n, m = self.cle.shape
        reste = self.nbre_car_de_alphabet % n
        return (n - reste) % n 
    
    def _creer_tab_groupes_coord(self) -> list[int]:
        res = []
        groupe = []
        n, m = self.cle.shape
        for i in range(len(self.nbres_clair)):
            if self.nbres_clair[i] != '':
                if len(groupe) < n:
                    groupe.append(i)
            if len(groupe) == n:
                res.append(groupe)
                groupe = []
        return res
    
    def _creer_tab_nbres_chiff(self) -> list[int]:
        res = [0] * len(self.mess_clair)
        for i in range(len(self.nbres_clair)):
            if self.nbres_clair[i] == '':
                res[i] = ''
        for coords in self.tab_groupes_coord:
            groupe_clair = []
            for pos in coords:
                groupe_clair.append([self.nbres_clair[pos]])
            groupe_clair = Matrix(groupe_clair) # matrice colonne
            if self.dechiffrer:
                groupe_chiff = self.inv_cle * groupe_clair
            else:
                groupe_chiff = self.cle * groupe_clair
            for i in range(len(coords)):
                res[coords[i]] = groupe_chiff[i]
        return res
    
    def _creer_tab_nbres_chiff_mod(self) -> list[int]:
        res = []
        for nbre in self.nbres_chiff:
            if nbre == '':
                res.append('')
            else:
                res.append(nbre % len(self.alphabet))
        return res
    
    def _creer_mess_chiff(self) -> str:
        res = []
        for i in range(len(self.mess_clair)):
            if self.nbres_chiff[i] == '':
                res.append(self.mess_clair[i])
            else:
                res.append(self.alphabet[self.nbres_chiff[i] % len(self.alphabet)])
        return ''.join(res)

    def _creer_tabs(self) -> list[list[list[str]]]:
        if self.dechiffrer:
            signe = '-'
        else:
            signe = '+'
        res = []
        i = 0
        nbre_car_ligne = 0
        while i < len(self.mess_clair):
            if nbre_car_ligne == 0:
                # initialisation d'un nouveau sous-tableau
                tab = [
                    [],    # 0 : ligne du message clair
                    [],    # 1 : ligne des nombres clairs
                    [],    # 2 : ligne des nombres chiffrés avant modulo longueur de l'alphabet
                    [],    # 3 : ligne des nombres chiffrés après modulo longueur de l'alphabet
                    []     # 4 : ligne du message chiffré
                ]
            if nbre_car_ligne < self.car_par_ligne_max and i < len(self.mess_clair):
                # complétion du tableau courant colonne par colonne
                tab[0].append('\\text{' + self.mess_clair[i] + '}')
                tab[1].append(str(self.nbres_clair[i]))
                if self.nbres_chiff[i] == '':
                    tab[2].append('')
                    tab[3].append('')
                elif self.nbres_chiff[i] == self.nbres_chiff[i] % len(self.alphabet):
                    tab[2].append(str(self.nbres_chiff[i]))
                    tab[3].append('')
                else:
                    tab[2].append('\\cancel{' + str(self.nbres_chiff[i]) + '}') # à barrer
                    tab[3].append(str(self.nbres_chiff_mod[i]))
                tab[4].append('\\text{' + self.mess_chiff[i] + '}')
                nbre_car_ligne += 1
                i += 1
            if nbre_car_ligne == self.car_par_ligne_max or i == len(self.mess_clair):
                # ajout du tableau courant fini au tableau de tableaux résultat
                res.append(tab)
                nbre_car_ligne = 0
        return res

    def _creer_latex(self) -> str:
        if not execute_dans_google_colab():
            debut_ligne = '&' # pour aligner à gauche le texte
        else:
            debut_ligne = '' # & est inutile et empêche l'affichage LaTeX dans Google Colab
        res = ''
        i_mess = 0
        for tab in self.tabs:
            res += debut_ligne + "\\text{Taille de l'alphabet : }" + str(len(self.alphabet)) + r' \\' + '\n'
            res += debut_ligne + "\\text{Clé : }" + latex(self.cle) + r' \\' + '\n'
            if self.dechiffrer:
                res += debut_ligne + "\\text{Clé inverse: }" + latex(self.inv_cle) + r' \\' + '\n'
                mode = 'Déchiffrement'
            else:
                mode = 'Chiffrement'
            res += debut_ligne + "\\text{Mode : " + mode + r"} \\" + '\n'
            #format_col = '|' + 'c' * len(tab[0])
            pos_debut_groupes = [groupe[0] for groupe in self.tab_groupes_coord]
            format_col = ''
            for i in range(len(tab[0])):
                if i_mess in pos_debut_groupes:
                    format_col += '|'
                format_col += 'c'
                i_mess += 1
            #format_col += '|'
            res += debut_ligne + tableau_en_array_latex(tab, format_col, hlines=[2])
            res += r'\\' + '\n'
            res += r'\\' + '\n'
        if not execute_dans_google_colab():
            return envelopper_latex_dans_balises_align(res)
        else:
            return res

    
if __name__ == '__main__':
    #chi1 = ChiffreCesar("BRUTUS M'A TUE", 15)
    #print(chi1) 
    #chi2 = ChiffreCesar("QGJIJH B'P IJT", -15)
    #print(chi2)
    chi3 = ChiffreCesar(MESSAGE_EXEMPLE_FR, cle=5)
    print(chi3)