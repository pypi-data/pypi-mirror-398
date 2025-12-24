__all__ = [
    "DshellTokenizer",
    "table_regex",
    "MASK_CHARACTER"
]

from re import DOTALL, IGNORECASE, ASCII
from re import compile, Pattern, finditer, escape, sub, findall

from .dshell_keywords import *
from .dshell_token_type import DshellTokenType as DTT
from .dshell_token_type import Token

MASK_CHARACTER = '§'

table_regex: dict[DTT, Pattern] = {
    DTT.PARAMETERS: compile(rf"--\*\s*(\w+)\s*", flags=ASCII),
    DTT.STR_PARAMETER: compile(rf"--\'\s*(\w+)\s*", flags=ASCII),
    DTT.PARAMETER: compile(rf"--\s*(\w+)\s*", flags=ASCII),
    DTT.STR: compile(r'"((?:[^\\"]|\\.)*)"', flags=DOTALL),
    DTT.COMMENT: compile(r"::(.*?)$"),
    DTT.EVAL_GROUP: compile(r"`(.*?)`"),
    DTT.LIST: compile(r"\[(.*?)\]"),
    DTT.MENTION: compile(r'<(?:@!?|@&|#)([0-9]+)>'),
    DTT.SUB_SEPARATOR: compile(rf"(~~)"),
    DTT.KEYWORD: compile(rf"(?<!\w)(#?{'|'.join(dshell_keyword)})(?!\w)"),
    DTT.DISCORD_KEYWORD: compile(rf"(?<!\w|-)(#?{'|'.join(dshell_discord_keyword)})(?!\w|-)"),
    DTT.COMMAND: compile(rf"\b({'|'.join(dshell_commands.keys())})\b"),
    DTT.MATHS_OPERATOR: compile(rf"({'|'.join([escape(i) for i in dshell_mathematical_operators.keys()])})"),
    DTT.LOGIC_OPERATOR: compile(rf"({'|'.join([escape(i) for i in dshell_logical_operators.keys()])})"),
    DTT.LOGIC_WORD_OPERATOR: compile(rf"(?:^|\s)({'|'.join([escape(i) for i in dshell_logical_word_operators.keys()])})(?:$|\s)"),
    DTT.FLOAT: compile(r"(\d+\.\d+)"),
    DTT.INT: compile(r"(\d+)"),
    DTT.BOOL: compile(r"(True|False)", flags=IGNORECASE),
    DTT.NONE: compile(r"(None)", flags=IGNORECASE),
    DTT.IDENT: compile(rf"([A-Za-z0-9_]+)")
}


class DshellTokenizer:

    def __init__(self, code: str):
        """
        Init le tokenizer.
        :param code: Le code à tokenizer
        """
        self.code: str = code

    def start(self):
        """
        Démarre le tokenizer pour qu'il traîte le code actuel.
        Renvoie un tableau de tokens par ligne (séparé normalement pas des \n)
        """
        splited_commandes = self.split(self.code)
        return self.tokenizer(splited_commandes)

    def tokenizer(self, commandes_lines: list[str]) -> list[list[Token]]:
        """
        Tokenize chaque ligne de code
        :param commandes_lines: Le code séparé en plusieurs lignes par la méthode split
        """
        tokens: list[list[Token]] = []

        line_number = 1
        for ligne in commandes_lines:  # iter chaque ligne du code
            tokens_par_ligne: list[Token] = []

            for token_type, pattern in table_regex.items():  # iter la table de régex pour tous les tester sur la ligne

                for match in finditer(pattern, ligne):  # iter les résultat du match pour avoir leur position

                    start_match = match.start()  # position de début du match

                    if token_type != DTT.COMMENT:  # si ce n'est pas un commentaire
                        token = Token(token_type, match.group(1), (line_number, start_match))  # on enregistre son token
                        tokens_par_ligne.append(token)

                        if token_type == DTT.STR:
                            token.value = token.value.replace(r'\"', '"')

                        if token_type in (
                                DTT.LIST,
                                DTT.EVAL_GROUP):  # si c'est un regroupement de donnée, on tokenize ce qu'il contient
                            result = self.tokenizer([token.value])
                            token.value = result[0] if len(
                                result) > 0 else result  # gère si la structure de donnée est vide ou non

                            for token_in_list in token.value:
                                token_in_list.position = (line_number, token_in_list.position[1])

                            for token_in_line in range(len(tokens_par_ligne)-1):
                                if tokens_par_ligne[token_in_line].position[1] > start_match:
                                    str_tokens_in_list = tokens_par_ligne[token_in_line:-1]
                                    tokens_par_ligne = tokens_par_ligne[:token_in_line] + [tokens_par_ligne[-1]]
                                    token.value.extend(str_tokens_in_list)
                                    token.value.sort(key=lambda t: t.position[1])  # trie les tokens par rapport à leur position
                                    break

                    len_match = len(match.group(0))  # longueur du match trouvé
                    ligne = ligne[:start_match] + (MASK_CHARACTER * len_match) + ligne[
                                                                                   match.end():]  # remplace la match qui vient d'avoir lieu pour ne pas le rematch une seconde fois

            tokens_par_ligne.sort(key=lambda
                token: token.position[1])  # trie la position par rapport aux positions de match des tokens pour les avoir dans l'ordre du code
            if tokens_par_ligne:
                tokens.append(tokens_par_ligne)

            line_number += 1  # incrémente le numéro de ligne pour la prochaine ligne

        return tokens

    @staticmethod
    def split(commande: str, global_split='\n', garder_carractere_regroupant=True, carractere_regroupant='"') -> list[
        str]:
        """
        Sépare les commandes en une liste en respectant les chaînes entre guillemets.
        Echapper les caractères regroupants avec un antislash (\) pour les inclure dans la chaîne.
        :param commande: La chaîne de caractères à découper.
        :param global_split: Le séparateur utilisé (par défaut '\n').
        :param garder_carractere_regroupant: Si False, enlève les guillemets autour des chaînes.
        :param caractere_regroupant: Le caractère utilisé pour regrouper une chaîne (par défaut '"').
        :return: Une liste des commandes découpées avec les chaînes restaurées.
        """

        commandes: str = commande.strip()
        remplacement_temporaire = '[REMPLACER]'
        pattern_find_regrouped_part = compile(fr'({carractere_regroupant}(?:[^\\{carractere_regroupant}]|\\.)*{carractere_regroupant})', flags=DOTALL)
        entre_caractere_regroupant = findall(pattern_find_regrouped_part, commandes)  # repère les parties entre guillemets et les save

        res = sub(pattern_find_regrouped_part,
                  remplacement_temporaire,
                  commandes,
                  )  # remplace les parties entre guillemets

        res = res.split(global_split)  # split les commandes sans les guillemets

        # remet les guillemets à leurs place
        result = []
        for i in res:
            while remplacement_temporaire in i:
                i = i.replace(remplacement_temporaire,
                              entre_caractere_regroupant[0][1: -1] if not garder_carractere_regroupant else
                              entre_caractere_regroupant[0], 1)
                entre_caractere_regroupant.pop(0)
            result.append(i)
        return result
