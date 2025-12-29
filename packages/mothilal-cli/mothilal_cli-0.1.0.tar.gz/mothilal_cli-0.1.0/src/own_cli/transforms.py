"""Text transformation functions for stylizing names."""


def to_leetspeak(text: str) -> str:
    """
    Convert text to leetspeak style.
    
    Example: 'Mothilal' -> 'M0th!l@l'
    """
    replacements = {
        'a': '@', 'A': '@',
        'e': '3', 'E': '3',
        'i': '!', 'I': '!',
        'o': '0', 'O': '0',
        's': '$', 'S': '$',
        't': '7', 'T': '7',
        'l': '1', 'L': '1',
    }
    return ''.join(replacements.get(c, c) for c in text)


def to_fancy(text: str) -> str:
    """
    Convert text to fancy unicode style.
    
    Example: 'Mothilal' -> '𝕄𝕠𝕥𝕙𝕚𝕝𝕒𝕝'
    """
    # Double-struck (blackboard bold) characters
    normal = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    fancy = '𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡'
    
    trans_table = str.maketrans(normal, fancy)
    return text.translate(trans_table)


def to_spaced(text: str) -> str:
    """
    Add spaces between characters for dramatic effect.
    
    Example: 'Mothilal' -> 'M o t h i l a l'
    """
    return ' '.join(text)


def to_reversed(text: str) -> str:
    """
    Reverse the text.
    
    Example: 'Mothilal' -> 'lalihtoM'
    """
    return text[::-1]
