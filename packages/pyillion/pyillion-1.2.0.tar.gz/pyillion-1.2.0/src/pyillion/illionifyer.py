def e(number:int)->int:
    """e(number)
    Return ``1000 ** number``."""
    return 1000**number
    
def d(a:int, b:int, r=3): 
    """d(a, b, r=3)
    Divide ``a`` by ``b`` and keep ``r`` decimal digits."""
    return round(a/b, r)


def il(n: int, bl: bool = False):
    
    if n < 0:
        return -1

    base = {
        0: "one",
        1: "thousand",
        2: "million",
        3: "billion",
        4: "trillion",
        5: "quadrillion",
        6: "quintillion",
        7: "sextillion",
        8: "septillion",
        9: "octillion",
        10: "nonillion",
        11: "decillion",
    }

    if n in base:
        name = base[n]

    elif 12 <= n <= 19:
        special = {
            12: "undecillion",
            13: "duodecillion",
            14: "tredecillion",
            15: "quattuordecillion",
            16: "quindecillion",
            17: "sexdecillion",
            18: "septendecillion",
            19: "octodecillion",
        }
        name = special[n]

    else:
        units = ["", "un", "duo", "tre", "quattuor",
                 "quin", "sex", "septen", "octo", "novem"]

        tens = ["", "", "vigint", "trigint", "quadragint",
                "quinquagint", "sexagint", "septuagint",
                "octogint", "nonagint"]

        hundreds = ["", "cent", "ducent", "trecent",
                    "quadringent", "quingent", "sescent",
                    "septingent", "octingent", "nongent"]

        if n >= 1000:
            name = f"{illionify(n,r=9)}-illion"
        else:
            u = n % 10
            t = (n // 10) % 10
            h = (n // 100) % 10
            name = units[u] + tens[t] + hundreds[h] + "illion"

    return 1000**n if bl else name

def il_short(n: int,bl=False):
    if n < 0:
        return -1
    
    base = {
        0: "one",
        1: "thousand",
        2: "M",
        3: "B",
        4: "T",
        5: "Qa",
        6: "Qn",
        7: "Sx",
        8: "Sp",
        9: "Oct",
        10: "Non",
        11: "Dec",
    }
    if n in base:
        name = base[n]
    elif 12 <= n <= 19:
        special = {
            12: "UDec",
            13: "DDec",
            14: "TDec",
            15: "QaDec",
            16: "QnDec",
            17: "SxDec",
            18: "SpDec",
            19: "OctDec",
        }
        name = special[n]    
    else:
        units = ["", "U", "D", "T", "Qa",
                 "Qn", "Sx", "Sp", "Oct", "Non"]

        tens = ["", "", "Vg", "Tg", "Qag",
                "Qng", "Sxg", "Spg",
                "Octg", "Nong"]

        hundreds = ["", "C", "Dc", "Tc",
                    "Qac", "Qnc", "Sxc",
                    "Spc", "Octc", "Nonc"]

        u = n % 10
        t = (n // 10) % 10
        h = (n // 100) % 10
        name = units[u] + tens[t] + hundreds[h]
    
    return 1000**n if bl else name
def illionify(n,r=3,short=False):
    """illionify(n, r=3, short=False)\n
    Convert a large integer into *-illion* long form or short form.
    """
    if n < 1000:
        return n
    elif short:
        k = (len(str(n)) - 1) // 3
        a = il_short(k,True)
        return f"{d(n,a,r)} {il_short(k)}"
    k = (len(str(n)) - 1) // 3
    a = il(k,True)
    return f"{d(n,a,r)} {il(k)}"




