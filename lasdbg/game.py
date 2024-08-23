from __future__ import annotations
import enum
import typing as tp
import struct

from lasdbg.context import instance as ctx

# Specific to v1.0.0.


class Addresses:
    FrameworkPtr = 0x7101C97188
    ActorByIdMapPtr = 0x7101CB2D00
    GlobalSave = 0x7101CBB200
    # RamEnd = 0x710143109f


def getFramework() -> Framework:
    return Framework(ctx.read_u64(ctx.addr(Addresses.FrameworkPtr)))


class Structure:
    def __init__(self, addr: int) -> None:
        self.addr = addr


class VirtualStructure(Structure):
    @property
    def vtable(self) -> int:
        return ctx.read_u64(self.addr)


class Vec3(Structure):
    size = 0x10

    def __repr__(self) -> str:
        x, y, z = self.data
        return f"({x:.3f}, {y:.3f}, {z:.3f})"

    @property
    def data(self) -> tp.Tuple[float, float, float]:
        return struct.unpack("<fff", ctx.read(self.addr, 0xC))  # type: ignore


class Vec4(Structure):
    size = 0x10

    def __repr__(self) -> str:
        x, y, z, t = self.data
        return f"({x:.3f}, {y:.3f}, {z:.3f}, {t:.3f})"

    @property
    def data(self) -> tp.Tuple[float, float, float, float]:
        return struct.unpack("<ffff", ctx.read(self.addr, 0x10))  # type: ignore


class Coords(Structure):
    size = 0x30

    def __repr__(self) -> str:
        return (self.pos, self.rotate, self.scale).__repr__()

    @property
    def pos(self) -> Vec3:
        return Vec3(self.addr)

    @property
    def rotate(self) -> Vec4:
        return Vec4(self.addr + 0x10)

    @property
    def scale(self) -> Vec3:
        return Vec3(self.addr + 0x20)


class StringView(Structure):
    size = 0x10

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return ctx.read_string(ctx.read_u64(self.addr))


T = tp.TypeVar("T")
T2 = tp.TypeVar("T2")


class SharedPtr(Structure, tp.Generic[T]):
    size = 0x10

    def __init__(self, addr: int, c1: tp.Type[T]):
        super().__init__(addr)
        self.c1 = c1

    @property
    def value(self) -> tp.Optional[T]:
        ptr = ctx.read_u64(self.addr)
        return self.c1(ptr) if ptr else None  # type: ignore


def makeTypeSharedPtr(c1: tp.Type[T]) -> tp.Type[SharedPtr[T]]:
    class Type(SharedPtr):
        def __init__(self, addr: int):
            super().__init__(addr, c1)
    Type.__name__ = f"SharedPtr[{c1.__name__}]"
    return Type


class Pair(Structure, tp.Generic[T, T2]):
    def __init__(self, addr: int, c1: tp.Type[T], c2: tp.Type[T2]):
        super().__init__(addr)
        self.c1 = c1
        self.c2 = c2

    def __iter__(self):
        yield self.first
        yield self.second

    @property
    def first(self) -> T:
        return self.c1(self.addr)  # type: ignore

    @property
    def second(self) -> T2:
        return self.c2(self.addr + self.c1.size)  # type: ignore


class HashTableNode(Structure, tp.Generic[T]):
    """libc++ std::unordered_map node (hash table node)"""

    @property
    def next(self) -> tp.Optional[HashTableNode]:
        ptr = ctx.read_u64(self.addr)
        return HashTableNode(ptr) if ptr else None

    @property
    def hash(self) -> int:
        return ctx.read_u64(self.addr + 8)

    def value(self, class_: tp.Type[T]) -> T:
        return class_(self.addr + 0x10)  # type: ignore


class HashTable(Structure, tp.Generic[T]):
    """libc++ std::unordered_map (hash table)"""

    def __init__(self, addr: int, class_: tp.Type[T]):
        super().__init__(addr)
        self.class_ = class_

    def items(self) -> tp.Iterable[T]:
        node = self.firstNode
        while node:
            yield node.value(self.class_)
            node = node.next

    @property
    def firstNode(self) -> tp.Optional[HashTableNode[T]]:
        ptr = ctx.read_u64(self.addr + 0x10)
        return HashTableNode(ptr) if ptr else None

    def __len__(self) -> int:
        return ctx.read_u64(self.addr + 0x18)


class Framework(Structure):
    @property
    def actorSystem(self) -> SharedPtr[ActorSystem]:
        return SharedPtr(self.addr + 0x498, ActorSystem)

    @property
    def gameState(self) -> SharedPtr[GameState]:
        return SharedPtr(self.addr + 0x4A8, GameState)

    @property
    def player(self) -> SharedPtr[Player]:
        return SharedPtr(self.addr + 0x4B8, Player)

    @property
    def frameCount(self) -> int:
        return ctx.read_u32(self.addr + 0x4D4)

# forward declaration


class Actor:
    pass


class DeferredInitComp:
    pass


class ActorId(Structure):
    size = 8

    def __repr__(self) -> str:
        return "%016x" % self.id

    @property
    def id(self) -> int:
        return ctx.read_u64(self.addr)


class ActorSystem(Structure):
    class ActorMapValue(Pair[StringView, SharedPtr[Actor]]):
        def __init__(self, addr: int):
            super().__init__(addr, StringView, makeTypeSharedPtr(Actor))

    class ActorByIdMapValue(Pair[ActorId, SharedPtr[Actor]]):
        def __init__(self, addr: int):
            super().__init__(addr, ActorId, makeTypeSharedPtr(Actor))

    @property
    def mapObjects(self) -> HashTable[ActorByIdMapValue]:
        return HashTable(ctx.read_u64(ctx.addr(Addresses.ActorByIdMapPtr)), self.ActorByIdMapValue)

    @property
    def actors(self) -> HashTable[ActorMapValue]:
        return HashTable(self.addr + 0x10, self.ActorMapValue)

    @property
    def actors2(self) -> HashTable[ActorMapValue]:
        return HashTable(self.addr + 0x38, self.ActorMapValue)

    @property
    def actors3(self) -> HashTable[ActorMapValue]:
        return HashTable(self.addr + 0x60, self.ActorMapValue)


class GameState(VirtualStructure):
    @property
    def type(self) -> str:
        tables = {
            0x7101BC4300: "Root",
        }
        return tables.get(ctx.to_ida(self.vtable), "???")


class Entity(VirtualStructure):
    @property
    def name(self) -> str:
        return ctx.read_string(self.addr + 0x18)

    @property
    def flags(self) -> int:
        return ctx.read_u32(self.addr + 0x40)


class Actor(Entity):  # type: ignore
    class ComponentMapValue(Pair[StringView, SharedPtr[DeferredInitComp]]):
        def __init__(self, addr: int):
            super().__init__(addr, StringView, makeTypeSharedPtr(DeferredInitComp))

    @property
    def components(self) -> HashTable[ComponentMapValue]:
        return HashTable(self.addr + 0x58, self.ComponentMapValue)

    @property
    def rootComp(self) -> SharedPtr[RootComp]:
        return SharedPtr(self.addr + 0x80, RootComp)

    @property
    def id(self) -> int:
        return ctx.read_u64(self.addr + 0x98)

    @property
    def actorIdx(self) -> int:
        return ctx.read_u16(self.addr + 0xA0)

    @property
    def spawnCoords(self) -> Coords:
        return Coords(self.addr + 0x260)


class Player(Actor):
    @property
    def skeletalModelComp(self) -> SharedPtr[RootComp]:
        return SharedPtr(self.addr + 0x2A8, RootComp)

    @property
    def playerCollision(self) -> SharedPtr[CharMovementComp]:
        return SharedPtr(self.addr + 0x2D8, CharMovementComp)

    @property
    def respawnCoords(self) -> Coords:
        return Coords(self.addr + 0x1B40)

    @property
    def state(self) -> int:
        return ctx.read_u8(self.addr + 0x4ED)

    def getStateHandler(self, idx: int) -> Structure:
        return Structure(ctx.read_u64(self.addr + 0x1340 + 8*idx))


class DeferredInitComp(Entity):  # type: ignore
    pass


class RootComp(DeferredInitComp):
    @property
    def otherComp(self) -> SharedPtr[RootComp]:
        return SharedPtr(self.addr + 0x58, RootComp)

    @property
    def coordsNew(self) -> Coords:
        return Coords(self.addr + 0x80)

    @property
    def coords(self) -> Coords:
        return Coords(self.addr + 0xB0)

    @property
    def needsCoordUpdate(self) -> bool:
        return ctx.read_bool(self.addr + 0xE0)

    @property
    def attachInfo(self) -> tp.Optional[AttachInfo]:
        ptr = ctx.read_u64(self.addr + 0x140)
        return AttachInfo(ptr) if ptr else None


class CharCtrlComp(RootComp):
    @property
    def vecA(self) -> Vec3:
        return Vec3(self.addr + 0x180)

    @property
    def vel(self) -> Vec3:
        return Vec3(self.addr + 0x190)

    @property
    def gravity(self) -> Vec3:
        return Vec3(self.addr + 0x1A0)

    @property
    def vecC(self) -> Vec3:
        return Vec3(self.addr + 0x1B0)


class CharMovementComp(CharCtrlComp):
    pass


class SklModelComp(RootComp):
    pass


class Attacher(Structure):
    @property
    def sklModelComp(self) -> SharedPtr[SklModelComp]:
        return SharedPtr(self.addr + 0x8, SklModelComp)

    @property
    def name(self) -> str:
        return ctx.read_string(self.addr + 0x78)

    @property
    def coordsB0(self) -> Coords:
        return Coords(self.addr + 0xB0)

    @property
    def coords(self) -> Coords:
        return Coords(self.addr + 0xF0)

    @property
    def initialCoords(self) -> Coords:
        return Coords(self.addr + 0x120)


class AttachInfo(Structure):
    class EnabledTypes(enum.IntFlag):
        Pos = 1 << 0
        Rot = 1 << 1
        Scale = 1 << 2

    @property
    def targetRootComp(self) -> SharedPtr[RootComp]:
        return SharedPtr(self.addr, RootComp)

    @property
    def attacher(self) -> SharedPtr[Attacher]:
        return SharedPtr(self.addr + 0x10, Attacher)

    @property
    def enabledTypes(self) -> AttachInfo.EnabledTypes:
        return AttachInfo.EnabledTypes(ctx.read_u8(self.addr + 0x20))

    @property
    def needsInit(self) -> bool:
        return ctx.read_bool(self.addr + 0x60)

    @property
    def targetCoords(self) -> Coords:
        return Coords(self.addr + 0x30)


class Hinox(Actor):
    class State(enum.IntEnum):
        Appear = 0
        Wait = 1
        Walk = 2
        CatchBegin = 3
        CatchDash = 4
        CatchStart = 5
        Catch = 6
        CatchThrow = 7
        CatchFailed = 8
        ThrowBomb = 9
        EnterEvent = 10
        mDeadEventReactionState = 11
        Turn = 12
        Laugh = 13
        mBraceReactionState = 14
        mBurnReactionState = 15
        mDamageReactionState = 16
        mDefenseReactionState = 17

    @property
    def state(self) -> Hinox.State:
        return Hinox.State(ctx.read_u8(self.addr + 0xFF0 + 0xD))

    @property
    def walkSpeed(self) -> float:
        return ctx.read_f32(self.addr + 0x15E0)

    @property
    def angleToPlayer(self) -> int:
        return ctx.read_u32(self.addr + 0x15F0)

    @property
    def sklModelComp(self) -> SharedPtr[SklModelComp]:
        return SharedPtr(self.addr + 0x1608, SklModelComp)

    @property
    def attachR(self) -> SharedPtr[Attacher]:
        return SharedPtr(self.addr + 0x1688, Attacher)

    @property
    def attachL(self) -> SharedPtr[Attacher]:
        return SharedPtr(self.addr + 0x1698, Attacher)

    @property
    def attachedPlayer(self) -> bool:
        return ctx.read_bool(self.addr + 0x16D8)


class Save240(Structure):
    pass


class Save248(Structure):
    @property
    def levelName(self) -> str:
        return ctx.read_string(self.addr)

    @property
    def setup(self) -> str:
        return ctx.read_string(self.addr + 0x40)

    @property
    def pos1(self) -> Vec3:
        return Vec3(self.addr + 0xC4)

    @property
    def pos2(self) -> Vec3:
        return Vec3(self.addr + 0xD0)

    @property
    def pos3(self) -> Vec3:
        return Vec3(self.addr + 0xDC)

    @property
    def zoneId(self) -> int:
        return ctx.read_u32(self.addr + 0xEC)


class EventFlags(Structure):
    @property
    def x240(self) -> Save240:
        return Save240(ctx.read_u64(self.addr + 0x240))

    @property
    def x248(self) -> Save248:
        return Save248(ctx.read_u64(self.addr + 0x248))


class GlobalSave(Structure):
    @property
    def eventFlags(self) -> EventFlags:
        return EventFlags(self.addr + 0x5F20) # 0x7101CC1120
    
    @property
    def inventory(self) -> Inventory:
        return Inventory(self.addr + 0x6168) # 0x7101CC1368


class Inventory(Structure):
    TRADE_ITEMS = {
        0: "None",
        1: "YoshiDoll",
        2: "Ribbon",
        3: "DogFood",
        4: "Bananas",
        5: "Stick",
        6: "Honeycomb",
        7: "Pineapple",
        8: "Hibiscus",
        9: "Letter",
        10: "Broom",
        11: "FishingHook",
        12: "Necklace",
        13: "MermaidsScale",
        14: "MagnifyingLens"
    }

    COMPANIONS = {
        0: "None",
        1: "BowWow",
        2: "Marin",
        3: "Ghost",
        4: "Rooster"
    }

    @property
    def acornCounter(self) -> int:
        return ctx.read_u8(self.addr + 0xA5)

    @property
    def popCounter(self) -> int:
        return ctx.read_u8(self.addr + 0xA4)

    @property
    def health(self) -> int:
        return ctx.read_u8(self.addr + 0x84)

    @property
    def rupees(self) -> int:
        return ctx.read_u16(self.addr + 0x80)

    @property
    def tradeItem(self) -> str:
        return Inventory.TRADE_ITEMS[ctx.read_u8(self.addr + 0x9A)]

    @property
    def companion(self) -> str:
        return Inventory.COMPANIONS[ctx.read_u8(self.addr + 0x9D)]

    def fullHeal(self) -> None:
        hearts = 3
        hearts += ctx.count_set_bits(ctx.read_u16(self.addr + 0x98))
        hearts += ctx.count_set_bits(ctx.read_u64(self.addr + 0x90)) // 4
        ctx.write(self.addr + 0x84, size=1, data=(4 * hearts))

    def forceAcorn(self) -> None:
        ctx.write(self.addr + 0xA5, size=1, data=14)

    def forcePop(self) -> None:
        ctx.write(self.addr + 0xA4, size=1, data=52)

    def maxRupees(self) -> None:
        ctx.write(self.addr + 0x80, size=2, data=9999)

    def testTrade(self) -> None:
        ctx.write(self.addr + 0x9A, size=1, data=13)

    def resourceRefill(self) -> None:
        ctx.write(self.addr + 0x9E, size=1, data=60) # Bombs
        ctx.write(self.addr + 0x9F, size=1, data=60) # Arrows
        ctx.write(self.addr + 0xA0, size=1, data=40) # MagicPowder
