from __future__ import annotations
import dataclasses
import sys
import struct
import time
import typing as tp

# from pyqtgraph import PlotWidget, plot
# import pyqtgraph as pg
import PySide6.QtCore as qt
import PySide6.QtWidgets as qtw

from lasdbg.context import instance as ctx
import lasdbg.game as game

GAME_TICK_CALC = 0x7100017E30


class Entry(tp.NamedTuple):
    name: str
    get_value: tp.Callable[[EntryContext], str]


class PlotEntry(tp.NamedTuple):
    name: str
    get_value: tp.Callable[[EntryContext], tp.Tuple[float, float]]
    pen: tp.Any


@dataclasses.dataclass
class EntryContext:
    save: game.GlobalSave = game.GlobalSave(ctx.addr(game.Addresses.GlobalSave))

    frm: game.Framework = game.getFramework()
    player: tp.Optional[game.Player] = None
    actsys: tp.Optional[game.ActorSystem] = None

    hinox: tp.Optional[game.Hinox] = None
    shouldFindHinox: bool = False

    _i = 0

    def findMapObject(self, id: str) -> tp.Optional[game.Actor]:
        if not self.actsys:
            return None
        for id_, actor in self.actsys.mapObjects.items():
            if str(id_).upper() == id:
                return actor.value
        return None

    def update(self) -> None:
        self.frm = game.getFramework()
        self.player = self.frm.player.value
        self.actsys = self.frm.actorSystem.value

        if self.shouldFindHinox:
            hinox_actor = self.findMapObject("1F07D9005CED2261")
            self.hinox = game.Hinox(hinox_actor.addr) if hinox_actor else None
            self.shouldFindHinox = False

        self._i += 1


def getEntries() -> tp.List[Entry]:
    entries = []

    entries.append(Entry("Health", lambda ectx: str(ectx.save.inventory.health)))
    entries.append(Entry("Rupees", lambda ectx: str(ectx.save.inventory.rupees)))
    entries.append(Entry("Pop Counter", lambda ectx: str(ectx.save.inventory.popCounter)))
    entries.append(Entry("Acorn Counter", lambda ectx: str(ectx.save.inventory.acornCounter)))
    entries.append(Entry("Trade Item", lambda ectx: str(ectx.save.inventory.tradeItem)))
    entries.append(Entry("Companion", lambda ectx: str(ectx.save.inventory.companion)))

    # entries.append(Entry("Frame", lambda ectx: str(str(ectx.frm.frameCount))))
    # entries.append(Entry("Number of actors", lambda ectx: str(len(ectx.actsys.actors))))
    # entries.append(Entry("Number of map objects", lambda ectx: str(len(ectx.actsys.mapObjects))))

    # entries.append(Entry("Player - Actor spawn pos",
    #                      lambda ectx: str(ectx.player.spawnCoords.pos)))

    # # entries.append(Entry("Player - Actor spawn rotate",
    # #                      lambda ectx: str(ectx.player.spawnCoords.rotate)))

    # entries.append(Entry("Player - Respawn pos",
    #                      lambda ectx: str(ectx.player.respawnCoords.pos)))
    # # entries.append(Entry("Player - Player rotate",
    # #                      lambda ectx: str(ectx.player.playerCoords.rotate)))

    # entries.append(Entry("Player - SklMdlComp posNew",
    #                      lambda ectx: str(ectx.player.skeletalModelComp.value.coordsNew.pos)))
    # entries.append(Entry("Player - SklMdlComp pos",
    #                      lambda ectx: str(ectx.player.skeletalModelComp.value.coords.pos)))
    # # entries.append(Entry("Player - SklMdlComp rotate",
    # #                      lambda ectx: str(ectx.player.skeletalModelComp.value.coords.rotate)))

    # entries.append(Entry("Player - Collision posNew",
    #                      lambda ectx: str(ectx.player.playerCollision.value.coordsNew.pos)))
    # entries.append(Entry("Player - Collision pos",
    #                      lambda ectx: str(ectx.player.playerCollision.value.coords.pos)))
    # # entries.append(Entry("Player - Collision rotate",
    # #                      lambda ectx: str(ectx.player.playerCollision.value.coords.rotate)))

    # # entries.append(Entry("Player - Collision vecA",
    # #                      lambda ectx: str(ectx.player.playerCollision.value.vecA)))
    # entries.append(Entry("Player - Collision vel",
    #                      lambda ectx: str(ectx.player.playerCollision.value.vel)))
    # # entries.append(Entry("Player - Collision gravity",
    # #                      lambda ectx: str(ectx.player.playerCollision.value.gravity)))
    # # entries.append(Entry("Player - Collision vecC",
    # #                      lambda ectx: str(ectx.player.playerCollision.value.vecC)))

    # entries.append(Entry("Hinox.state", lambda ectx: str(ectx.hinox.state)))
    # entries.append(Entry("Hinox.walkSpeed", lambda ectx: str(ectx.hinox.walkSpeed)))
    # entries.append(Entry("Hinox.angleToPlayer", lambda ectx: str(ectx.hinox.angleToPlayer)))
    # entries.append(Entry("Hinox.attachedPlayer", lambda ectx: str(ectx.hinox.attachedPlayer)))
    # entries.append(Entry("Hinox.SklMdlComp.pos", lambda ectx: str(
    #     ectx.hinox.sklModelComp.value.coords.pos)))
    # entries.append(Entry("Hinox.SklMdlComp.posNew", lambda ectx: str(
    #     ectx.hinox.sklModelComp.value.coordsNew.pos)))
    # entries.append(Entry("Hinox.attachR.coords", lambda ectx: str(
    #     ectx.hinox.attachR.value.coords.pos)))
    # entries.append(Entry("Hinox.attachL.coords", lambda ectx: str(
    #     ectx.hinox.attachL.value.coords.pos)))

    # # entries.append(Entry("RootComp.a.tRC.name", lambda ectx: str(
    # #     ectx.player.rootComp.value.attachInfo.targetRootComp.value.name)))
    # entries.append(Entry("RootComp.a.atc.name", lambda ectx: str(
    #     ectx.player.rootComp.value.attachInfo.attacher.value.name)))
    # # entries.append(Entry("RootComp.a.atc.skl.name", lambda ectx: str(
    # #     ectx.player.rootComp.value.attachInfo.attacher.value.sklModelComp.value.name)))
    # entries.append(Entry("RootComp.a.types", lambda ectx: str(
    #     ectx.player.rootComp.value.attachInfo.enabledTypes)))
    # entries.append(Entry("RootComp.a.tgCoords.pos", lambda ectx: str(
    #     ectx.player.rootComp.value.attachInfo.targetCoords.pos)))
    # entries.append(Entry("RootComp.needsCoordUpdate", lambda ectx: str(
    #     ectx.player.rootComp.value.needsCoordUpdate)))
    # entries.append(Entry("Player(Entity).flags", lambda ectx: f"{ectx.player.flags:08X}"))
    # entries.append(Entry("Player state", lambda ectx: f"{ectx.player.state:08X}"))
    # entries.append(Entry("Player damage state", lambda ectx: f"{ctx.read_u8(ectx.player.getStateHandler(0xB).addr + 0xF0 + 0x18):08X}"))

    # # entries.append(Entry("Save.x240.levelName", lambda ectx: str(ectx.save.eventFlags.x248.levelName)))
    # # entries.append(Entry("Save.x240.setup", lambda ectx: str(ectx.save.eventFlags.x248.setup)))
    # # entries.append(Entry("Save.x240.zoneId", lambda ectx: str(ectx.save.eventFlags.x248.zoneId)))
    # # entries.append(Entry("Save.x240.pos1", lambda ectx: str(ectx.save.eventFlags.x248.pos1)))
    # # entries.append(Entry("Save.x240.pos2", lambda ectx: str(ectx.save.eventFlags.x248.pos2)))
    # # entries.append(Entry("Save.x240.pos3", lambda ectx: str(ectx.save.eventFlags.x248.pos3)))

    return entries


# def getPlotEntries() -> tp.List[PlotEntry]:
#     entries = []

#     def vec3_to_vec2(vec3):
#         v = vec3.data
#         return (v[0], v[2])

#     entries.append(PlotEntry("Player - Respawn pos",
#                              lambda ectx: vec3_to_vec2(
#                                  ectx.player.respawnCoords.pos),
#                              pen=pg.mkPen(color=(255, 0, 0), width=3)))

#     entries.append(PlotEntry("Player - SklMdlComp pos",
#                              lambda ectx: vec3_to_vec2(ectx.player.skeletalModelComp.value.coords.pos), pen=pg.mkPen(color=(0, 0, 255), width=3)))

#     entries.append(PlotEntry("Player - Collision posNew",
#                              lambda ectx: vec3_to_vec2(
#                                  ectx.player.playerCollision.value.coords.pos),
#                              pen=pg.mkPen(color=(255, 255, 0), width=3)))

#     entries.append(PlotEntry("Player - Collision pos",
#                              lambda ectx: vec3_to_vec2(
#                                  ectx.player.playerCollision.value.coords.pos),
#                              pen=pg.mkPen(color=(255, 255, 255), width=3)))

#     entries.append(PlotEntry("RootComp.a.tgCoords.pos", lambda ectx: vec3_to_vec2(
#         ectx.player.rootComp.value.attachInfo.targetCoords.pos), pen=pg.mkPen(color=(0, 255, 255), width=3)))

#     return entries


class MainWindow(qtw.QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("LAS")
        self.initLayout()

        self.running = False

        self.entryCtx = EntryContext()
        self.entries: tp.List[Entry] = getEntries()
        # self.plotEntries: tp.List[PlotEntry] = getPlotEntries()
        # self.plots: tp.List[tp.Tuple[list, list]] = []
        # for i in range(len(self.plotEntries)):
        #     self.plots.append(([], []))

        self.updateTimer = qt.QTimer(self)
        self.updateTimer.timeout.connect(self.onUpdateTimer)
        self.updateTimer.setTimerType(qt.Qt.TimerType.PreciseTimer)
        self.updateTimer.setInterval(3000)
        self.updateTimer.start()

        # self.plotTimer = qt.QTimer(self)
        # self.plotTimer.timeout.connect(self.onPlotTimer)
        # self.plotTimer.start(100)

    @qt.Slot()
    def onUpdateTimer(self) -> None:
        if not self.running:
            return

        # ctx.break_process()

        self.entryCtx.update()
        self.table.setRowCount(len(self.entries))
        for i, entry in enumerate(self.entries):
            item = qtw.QTableWidgetItem(entry.name)
            self.table.setItem(i, 0, item)

            try:
                val = entry.get_value(self.entryCtx)
            except Exception as e:
                val = "???"
                # print(e)
            item = qtw.QTableWidgetItem(val)
            self.table.setItem(i, 1, item)

        # for i, pentry in enumerate(self.plotEntries):
        #     try:
        #         x, y = pentry.get_value(self.entryCtx)
        #         self.plots[i][0].append(x)
        #         self.plots[i][1].append(-y)
        #     except:
        #         pass

        # ctx.continue_process()

    # @qt.Slot()
    # def onPlotTimer(self) -> None:
    #     self.graph.clear()
    #     for i, pentry in enumerate(self.plotEntries):
    #         self.graph.plot(self.plots[i][0], self.plots[i][1], pen=pentry.pen)

    @qt.Slot()
    def onRunBtnPressed(self) -> None:
        if self.running:
            self.runBtn.setText("Continue")
            # ctx.break_process()
        else:
            self.runBtn.setText("Break")
            # ctx.ingest_events()
            # ctx.continue_process()
        self.running = not self.running

    # @qt.Slot()
    # def onClearGraphPressed(self) -> None:
    #     for lx, ly in self.plots:
    #         lx.clear()
    #         ly.clear()
    #     self.graph.clear()

    # @qt.Slot()
    # def onFindHinoxPressed(self) -> None:
    #     self.entryCtx.shouldFindHinox = True

    @qt.Slot()
    def onHealPressed(self) -> None:
        inventory = self.entryCtx.save.inventory
        inventory.fullHeal()
        # player = self.entryCtx.player
        # if not player:
        #     return
        # rootComp = player.rootComp.value
        # print(ctx.read(rootComp.coords.addr, 0x30))
        # if not rootComp:
        #     return
        # ctx.write(rootComp.coordsNew.addr, ctx.read(rootComp.coords.addr, 0x30))
        # # ctx.write(rootComp.coordsNew.pos.addr, struct.pack('<f', 500))
        # # ctx.write(rootComp.coordsNew.pos.addr + 4, struct.pack('<f', 500))
        # # ctx.write(rootComp.coordsNew.pos.addr + 8, struct.pack('<f', 500))

    @qt.Slot()
    def onForcePopPressed(self) -> None:
        inventory = self.entryCtx.save.inventory
        inventory.forcePop()
        # player = self.entryCtx.player
        # if not player:
        #     return
        # rootComp = player.rootComp.value
        # if not rootComp:
        #     return
        # ctx.write(rootComp.coordsNew.pos.addr, struct.pack('<f', 38))
        # ctx.write(rootComp.coordsNew.pos.addr + 4, struct.pack('<f', 0))
        # ctx.write(rootComp.coordsNew.pos.addr + 8, struct.pack('<f', 72))

        # ctx.write(rootComp.coordsNew.pos.addr, struct.pack('<f', 17))
        # ctx.write(rootComp.coordsNew.pos.addr + 4, struct.pack('<f', 0.5))
        # ctx.write(rootComp.coordsNew.pos.addr + 8, struct.pack('<f', 43))

        # ctx.write(rootComp.coordsNew.pos.addr, struct.pack('<f', 130))
        # ctx.write(rootComp.coordsNew.pos.addr + 4, struct.pack('<f', 5))
        # ctx.write(rootComp.coordsNew.pos.addr + 8, struct.pack('<f', 20))

    @qt.Slot()
    def onRefillPressed(self) -> None:
        inventory = self.entryCtx.save.inventory
        inventory.resourceRefill()

    def initLayout(self) -> None:
        buttonsLayout = qtw.QHBoxLayout()
        self.runBtn = qtw.QPushButton("Monitor Stats")
        self.runBtn.pressed.connect(self.onRunBtnPressed)
        buttonsLayout.addWidget(self.runBtn)
        # clearGraphBtn = qtw.QPushButton("Clear graph")
        # clearGraphBtn.pressed.connect(self.onClearGraphPressed)
        # buttonsLayout.addWidget(clearGraphBtn)
        # findHinoxBtn = qtw.QPushButton("Find Hinox")
        # findHinoxBtn.pressed.connect(self.onFindHinoxPressed)
        # buttonsLayout.addWidget(findHinoxBtn)
        testBtn = qtw.QPushButton("Full Heal")
        testBtn.pressed.connect(self.onHealPressed)
        buttonsLayout.addWidget(testBtn)
        testBtn = qtw.QPushButton("Force PoP")
        testBtn.pressed.connect(self.onForcePopPressed)
        buttonsLayout.addWidget(testBtn)
        testBtn = qtw.QPushButton("Refill Bombs/Arrows/Powder")
        testBtn.pressed.connect(self.onRefillPressed)
        buttonsLayout.addWidget(testBtn)

        left = qtw.QVBoxLayout()
        self.table = qtw.QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, qtw.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, qtw.QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        left.addLayout(buttonsLayout)
        left.addWidget(self.table)

        # self.graph = pg.PlotWidget(self)
        # self.graph.showGrid(x=True, y=True)
        # self.graph.setLabel("left", "y")
        # self.graph.setLabel("bottom", "x")

        hbox = qtw.QHBoxLayout()
        hbox.addLayout(left, stretch=3)
        # hbox.addWidget(self.graph, stretch=7)

        widget = qtw.QWidget(self)
        widget.setLayout(hbox)
        self.setCentralWidget(widget)


# def fg() -> None:
#     ctx.ingest_events()
#     ctx.continue_process()


# def br() -> None:
#     ctx.break_process()


def main() -> None:
    # print(f"base: {ctx.base:016x}")

    app = qtw.QApplication([])
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


main()

frm = game.Framework(ctx.read_u64(ctx.addr(game.Addresses.FrameworkPtr)))
gameState = frm.gameState.value
assert gameState
print(f"{ctx.to_ida(ctx.read_u64(gameState.addr)):016x}")
player = frm.player.value

print(len(player.components))
for name, comp in player.components.items():
    print(name)

actorSystem = frm.actorSystem.value
assert actorSystem


def print_actors() -> None:
    assert actorSystem
    print("============ map1 ============")
    for name, actor in actorSystem.actors.items():
        print(name)
    print("============ map objects ============")
    for objid, actor in actorSystem.mapObjects.items():
        name = actor.value.name
        print(objid, name)
