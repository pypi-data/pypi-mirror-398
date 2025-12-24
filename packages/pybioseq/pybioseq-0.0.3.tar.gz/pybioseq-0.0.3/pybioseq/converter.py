aa_one_word_list = [
    'G', 'A', 'V', 'L', 'I', 'P', 'F', 'Y', 'W', 'S',
    'T', 'C', 'M', 'N', 'Q', 'D', 'E', 'K', 'R', 'H'
]

aa_three_word_list = [
    'GLY', 'ALA', 'VAL', 'LEU', 'ILE',
    'PRO', 'PHE', 'TYR', 'TRP', 'SER',
    'THR', 'CYS', 'MET', 'ASN', 'GLN',
    'ASP', 'GLU', 'LYS', 'ARG', 'HIS'
]

condon_table = {
    'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
    'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
    'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
    'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
    'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
    'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    'TAT': 'Y', 'TAC': 'Y', 'TAA': None, 'TAG': None,
    'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
    'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
    'TGT': 'C', 'TGC': 'C', 'TGA': None, 'TGG': 'W',
    'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
    'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
    'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G'
}

def to3(aa, style='AAA'):
    idx = aa_one_word_list.index(aa.upper())
    aa_3_word = aa_three_word_list[idx]
    if style == 'AAA':
        return aa_3_word.upper()
    elif style == 'Aaa':
        return aa_3_word.capitalize()

    raise ValueError("style must be 'AAA' or 'Aaa'")

def to1(aa):
    idx = aa_three_word_list.index(aa.upper())
    aa_1_word = aa_one_word_list[idx]
    return aa_1_word.upper()

def standard_aa(aa):
    aa = aa.upper()
    return aa in aa_one_word_list or aa in aa_three_word_list

def standard_nmp(nmp):
    nmp = nmp.upper()
    return nmp in ['A', 'C', 'G', 'U']

def standard_dnmp(dnmp):
    dnmp = dnmp.upper()
    return dnmp in ['A', 'C', 'G', 'T']

def translate(condon):
    return condon_table[condon.upper()]