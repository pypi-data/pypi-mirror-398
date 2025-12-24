from enum import Enum


class Instrument(Enum):
    Sitar = 'Sitar'
    Vocal_M = 'Vocal (M)'
    Vocal_F = 'Vocal (F)'
    Sarangi = 'Sarangi'


class TalaName(Enum):
    """Predefined tala names for Hindustani classical music meters."""
    Tintal = 'Tintal'
    Tilwada = 'Tilwada'
    Jhoomra = 'Jhoomra'
    AdaChautal = 'Ada Chautal'
    Dhamar = 'Dhamar'
    DeepchandiThumri = 'Deepchandi (Thumri)'
    DeepchandiDhrupad = 'Deepchandi (Dhrupad)'
    Ektal = 'Ektal'
    Jhaptal = 'Jhaptal'
    SoolTaal = 'Sool Taal'
    Keherwa = 'Keherwa'
    Rupak = 'Rupak'
    Tivra = 'Tivra'
    Dadra = 'Dadra'
