import pyxel
from functools import partial
from rogue.core import LevelItem, State, Player


def _add_key(player: Player) -> Player:
    player.keys += 1
    pyxel.play(3, 52)
    return player


def _add_flag(flag: str, player: Player) -> Player:
    player.flags.add(flag)
    pyxel.play(3, 52)
    return player


ADD_KEY = _add_key
TELEPORT_SPELL = partial(_add_flag, "teleport")
MAGIC_WAND = partial(_add_flag, "wand")


class Chest(LevelItem):
    def __init__(self, content_fn, *args, **kw):
        super().__init__(*args, **kw)
        self.content_fn = content_fn
        self.sprite_id = 'chest'

    def interact(self, state: State):
        state.player = self.content_fn(state.player)
        # I know...
        state.level.items.remove(self)
