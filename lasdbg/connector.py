import socket

class Debug(socket.socket):
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(("192.168.1.93", 6000))

    # Make sure to append "\r\n" to the end of every command to ensure arg are parsed correctly
    def sendCommand(self, content):
        content += '\r\n'
        self.s.sendall(content.encode())

    def readMemory(self, addr: int, size: int):
        self.sendCommand(f"peekMain {hex(addr)} {size}")
        data = self.s.recv((size * 2) + 1)[:-1] # remove trailing \n
        data = str(data, 'utf-8')
        return bytes.fromhex(data)

    def writeMemory(self, addr: int, size: int, value):
        if isinstance(value, int):
            print(value)
            signed = True if value < 0 else False
            b_value: bytes = value.to_bytes(size, 'little', signed=signed)
            value = "0x" + b_value.hex()

        self.sendCommand(f"pokeMain {hex(addr)} {value}")
