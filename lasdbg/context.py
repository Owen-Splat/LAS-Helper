import lasdbg.connector as connection
import struct


# def get_application_pid(device: pytwib.ITwibDeviceInterface) -> int:
#     for process in device.ListProcesses():
#         if process.process_name == "Application":
#             return process.process_id
#     raise RuntimeError("No application found")


_NUL_CHR = b'\x00'

class Context:
    def __init__(self) -> None:
        # self.client: pytwib.Client = pytwib.GetClient()
        # self.device: pytwib.ITwibDeviceInterface = pytwib.GetDeviceInterface(self.client)
        # pid = get_application_pid(self.device)
        # self.debug: pytwib.ITwibDebugger = self.device.OpenActiveDebugger(pid)
        # self.base = self.debug.GetTargetEntry()

        self.base = 0xC88 #0x710143109f
        self.debug = connection.Debug()
        # self.ingest_events()

    def addr(self, ea: int) -> int:
        return ea - 0x7100000000 - self.base

    def to_ida(self, addr: int) -> int:
        return addr + 0x7100000000 + self.base

    def read(self, addr: int, size: int) -> bytes:
        return self.debug.readMemory(addr, size)

    def write(self, addr: int, data=None):
        self.debug.writeMemory(addr, data)

    # def break_process(self) -> None:
    #     self.debug.breakProcess()
    #     # event = self.debug.GetDebugEvent()
    #     # if not event or event.event_type != pytwib.DebugEvent.EventType.Exception:
    #     #     print("warn: did not get Exception debug event after break?")

    # def continue_process(self) -> None:
    #     self.debug.continueProcess()

    # def ingest_events(self) -> None:
    #     return
    #     # while True:
    #     #     event = self.debug.GetDebugEvent()
    #     #     if not event:
    #     #         return
    #     #     print(f"got event type {event.event_type}")

    def read_bool(self, addr: int) -> bool:
        return self.read_u8(addr) != 0

    def read_u8(self, addr: int) -> int:
        return struct.unpack("B", self.read(addr, 1))[0]

    def read_u16(self, addr: int) -> int:
        return struct.unpack("H", self.read(addr, 2))[0]

    def read_u32(self, addr: int) -> int:
        return struct.unpack("I", self.read(addr, 4))[0]

    def read_s32(self, addr: int) -> int:
        return struct.unpack("i", self.read(addr, 4))[0]

    def read_u64(self, addr: int) -> int:
        return struct.unpack("Q", self.read(addr, 8))[0]

    def read_f32(self, addr: int) -> float:
        return struct.unpack("f", self.read(addr, 4))[0]

    # def read_string(self, addr: int) -> str:
    #     b = self.read(addr, 0x40)
    #     end = b.find(_NUL_CHR)
    #     return b[:end].decode()

    def read_string(self, addr: int) -> str:
        s = ""
        i = 0
        while True:
            c = self.read_u8(addr + i)
            if c == 0:
                break
            s += chr(c)
            i += 1
        return s

    def count_set_bits(self, num) -> int:
        count = 0
        while num:
            count += num & 1
            num >>= 1
        return count

instance = Context()
