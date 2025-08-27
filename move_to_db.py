# Pokemon GO availability data - Pokemon that are actually released in Pokemon GO
# This is a simplified list - in production you'd want to maintain this more dynamically
POKEMON_GO_AVAILABLE = set(range(1, 152))  # Gen 1
POKEMON_GO_AVAILABLE.update(range(152, 252))  # Gen 2
POKEMON_GO_AVAILABLE.update(range(252, 387))  # Gen 3
POKEMON_GO_AVAILABLE.update(range(387, 494))  # Gen 4
POKEMON_GO_AVAILABLE.update(range(494, 650))  # Gen 5
POKEMON_GO_AVAILABLE.update(range(650, 722))  # Gen 6
POKEMON_GO_AVAILABLE.update(range(722, 810))  # Gen 7
POKEMON_GO_AVAILABLE.update(range(810, 899))  # Gen 8 (partial)
# Note: This is simplified - real Pokemon GO has selective releases

# Legendary Pokemon (including Ultra Beasts and Mythicals)
LEGENDARY_POKEMON = {
    144, 145, 146, 150, 151,  # Gen 1: Articuno, Zapdos, Moltres, Mewtwo, Mew
    243, 244, 245, 249, 250, 251,  # Gen 2: Raikou, Entei, Suicune, Lugia, Ho-Oh, Celebi
    377, 378, 379, 380, 381, 382, 383, 384, 385, 386,  # Gen 3: Regirock, Regice, Registeel, Latias, Latios, Kyogre, Groudon, Rayquaza, Jirachi, Deoxys
    480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493,  # Gen 4
    494, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649,  # Gen 5
    716, 717, 718, 719, 720, 721,  # Gen 6: Xerneas, Yveltal, Zygarde, Volcanion, Hoopa, Diancie
    772, 773, 785, 786, 787, 788, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809,  # Gen 7
    888, 889, 890, 891, 892, 893, 894, 895, 896, 897, 898  # Gen 8 (partial)
}

# Pokemon that have Mega Evolution in Pokemon GO
MEGA_POKEMON = {
    3, 6, 9, 65, 80, 94, 115, 127, 130, 142, 150, 181, 208, 212, 214, 229, 248, 254, 257, 260, 282, 302, 303, 306, 308, 310, 319, 323, 334, 354, 359, 362, 373, 376, 380, 381, 384, 428, 445, 448, 460
}

# Pokemon that have Shadow forms (this is a subset - many more exist)
SHADOW_POKEMON = {
    1,2,3,4,5,6,7,8,9,10,
    11,12,13,14,15,16,17,18,19,20,
    23,24,27,28,29,30,
    31,32,33,34,37,38,
    41,42,43,44,45,48,49,50,
    51,52,53,54,55,56,57,58,59,60,
    61,62,63,64,65,66,67,68,69,70,
    71,72,73,74,75,76,79,80,
    81,82,88,89,90,
    91,92,93,94,95,96,97,100,
    101,102,103,104,105,106,107,109,110,
    111,112,114,116,117,
    121,123,125,126,127,129,130,
    131,137,138,139,
    142,143,144,145,146,147,148,149,150,
}

# Pokemon that have Dynamax forms
DMAX_POKEMON = {
    1,2,3,4,5,6,7,8,9,10,11,12,
    66,67,68,92,93,94,98,99,131,138,139,140,141,143,
    144,145,146,213,241,242,243,244,245,
    302,320,321,374,375,376,380,381,
    519,520,521,529,530,554,555,568,569,615,766,
    810,811,812,813,814,815,816,817,818,819,820,
    821,822,823,831,832,849,856,857,858,
    870,891,892,893
}
# Pokemon that have Gigantanamax forms
GMAX_POKEMON = {
    3,6,9,12,68,94,99,131,143,812,815,818,849
}

# Type effectiveness chart for Pokemon Go
TYPE_CHART = {
    'normal': {'rock': 0.625, 'ghost': 0.390625, 'steel': 0.625},
    'fire': {'fire': 0.625, 'water': 0.625, 'grass': 1.6, 'ice': 1.6, 'bug': 1.6, 'rock': 0.625, 'dragon': 0.625, 'steel': 1.6, 'ground': 1.6},
    'water': {'fire': 1.6, 'water': 0.625, 'grass': 0.625, 'ground': 1.6, 'rock': 1.6, 'dragon': 0.625},
    'electric': {'water': 1.6, 'electric': 0.625, 'grass': 0.625, 'ground': 0.390625, 'flying': 1.6, 'dragon': 0.625},
    'grass': {'fire': 0.625, 'water': 1.6, 'electric': 1.6, 'grass': 0.625, 'poison': 0.625, 'flying': 0.625, 'bug': 0.625, 'rock': 1.6, 'dragon': 0.625, 'steel': 0.625, 'ground': 1.6},
    'ice': {'fire': 0.625, 'water': 0.625, 'grass': 1.6, 'ice': 0.625, 'ground': 1.6, 'flying': 1.6, 'dragon': 1.6, 'steel': 0.625},
    'fighting': {'normal': 1.6, 'ice': 1.6, 'poison': 0.625, 'flying': 0.625, 'psychic': 0.625, 'bug': 0.625, 'rock': 1.6, 'ghost': 0.390625, 'dark': 1.6, 'steel': 1.6, 'fairy': 0.625},
    'poison': {'grass': 1.6, 'poison': 0.625, 'ground': 0.625, 'rock': 0.625, 'ghost': 0.625, 'steel': 0.390625, 'fairy': 1.6},
    'ground': {'fire': 1.6, 'electric': 1.6, 'grass': 0.625, 'poison': 1.6, 'flying': 0.390625, 'bug': 0.625, 'rock': 1.6, 'steel': 1.6},
    'flying': {'electric': 0.625, 'grass': 1.6, 'ice': 0.625, 'fighting': 1.6, 'bug': 1.6, 'rock': 0.625, 'steel': 0.625},
    'psychic': {'fighting': 1.6, 'poison': 1.6, 'psychic': 0.625, 'dark': 0.390625, 'steel': 0.625},
    'bug': {'fire': 0.625, 'grass': 1.6, 'fighting': 0.625, 'poison': 0.625, 'flying': 0.625, 'psychic': 1.6, 'ghost': 0.625, 'dark': 1.6, 'steel': 0.625, 'fairy': 0.625},
    'rock': {'fire': 1.6, 'ice': 1.6, 'fighting': 0.625, 'ground': 0.625, 'flying': 1.6, 'bug': 1.6, 'steel': 0.625},
    'ghost': {'normal': 0.390625, 'psychic': 1.6, 'ghost': 1.6, 'dark': 0.625},
    'dragon': {'dragon': 1.6, 'steel': 0.625, 'fairy': 0.390625},
    'dark': {'fighting': 0.625, 'psychic': 1.6, 'ghost': 1.6, 'dark': 0.625, 'fairy': 0.625},
    'steel': {'fire': 0.625, 'water': 0.625, 'electric': 0.625, 'ice': 1.6, 'rock': 1.6, 'steel': 0.625, 'fairy': 1.6},
    'fairy': {'fire': 0.625, 'fighting': 1.6, 'poison': 0.625, 'dragon': 1.6, 'dark': 1.6, 'steel': 0.625}
}
