def create_client(host="localhost", port=18861):
    # try to get memory error from machine68k - otherwise use own
    try:
        import machine68k

        mem_error = machine68k.MemoryError
    except ImportError:

        class MemoryError(Exception):
            def __init__(self, addr, op, size=None):
                self.addr = addr
                self.op = op
                self.size = size

            def __repr__(self):
                return "MemoryError(%06x, %s, %s)" % (self.addr, self.op, self.size)

        mem_error = MemoryError
    # get rpyc
    try:
        import rpyc

        # map remote exceptions
        rpyc.core.vinegar._generic_exceptions_cache["machine68k.MemoryError"] = (
            mem_error
        )
    except ImportError:
        return None

    class RMachine68kClient:
        def __init__(self, host="localhost", port=18861):
            self.client = rpyc.connect(host, port)
            self.open = True

        def create_machine(self, cpu_name, ram_size_kib):
            return self.client.root.create_machine(cpu_name, ram_size_kib)

        def release_machine(self):
            return self.client.root.release_machine()

        def test_param(self, param):
            return self.client.root.test_param(param)

        def close(self):
            if not self.open:
                raise RuntimeError("RMachine68kClient already closed!")
            self.open = False
            return self.client.close()

    return RMachine68kClient(host=host, port=port)


def create_machine(client, cpu_name="68000", ram_size_kib=1024, auto_close=True):

    own_methods = (
        "client",
        "cpu_name",
        "ram_size_kib",
        "auto_close",
        "rmachine",
    )

    class RMachine68k:
        def __init__(self, client, cpu_name, ram_size_kib, auto_close=True):
            self.client = client
            self.cpu_name = cpu_name
            self.ram_size_kib = ram_size_kib
            self.auto_close = auto_close
            # setup machine
            self.rmachine = client.create_machine(cpu_name, ram_size_kib)

        def cleanup(self):
            self.client.release_machine()
            if self.auto_close:
                self.client.close()

        def __getattr__(self, name):
            if name in own_methods:
                # my own methods
                return object.__get_attr__(self, name)
            else:
                # forward to machine
                return getattr(self.rmachine, name)

    return RMachine68k(client, cpu_name, ram_size_kib, auto_close)
