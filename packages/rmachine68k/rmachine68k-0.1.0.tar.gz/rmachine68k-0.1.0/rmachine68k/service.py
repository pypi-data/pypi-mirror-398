import logging
import machine68k


def create_service(host="localhost", port=18861, type="threaded"):
    try:
        import rpyc
    except ImportError:
        return None

    class Machine68kService(rpyc.Service):
        def on_connect(self, conn):
            logging.info("on connect: %s", conn)
            self.machine_in_use = False

        def on_disconnect(self, conn):
            logging.info("on disconnect: %s", conn)

        def exposed_create_machine(self, cpu_str, mem_size):
            if self.machine_in_use:
                logging.error("create_machine: machine already in use!")
                return None
            logging.info(f"create_machine(cpu_str={cpu_str}, mem_size={mem_size})")
            cpu_id = machine68k.cpu_type_from_str(cpu_str)
            mach = machine68k.Machine(cpu_id, mem_size)
            logging.info("-> %s", mach)
            self.machine_in_use = True
            self.machine = mach
            return mach

        def exposed_release_machine(self):
            if not self.machine_in_use:
                logging.error("release_machine: no machine in use!")
                return False
            logging.info("release_machine: %s", self.machine)
            self.machine_in_use = False
            self.machine.cleanup()
            self.machine = None
            return True

    cfg = {"allow_public_attrs": True, "import_custom_exceptions": True}

    if type == "forking":
        logging.info("create forking server: host=%s, port=%d", host, port)
        return rpyc.utils.server.ForkingServer(
            Machine68kService, port=port, hostname=host, protocol_config=cfg
        )
    elif type == "threaded":
        logging.info("create threaded server: host=%s, port=%d", host, port)
        return rpyc.utils.server.ThreadedServer(
            Machine68kService, port=port, hostname=host, protocol_config=cfg
        )
    else:
        raise RuntimeError("Invalid type ('threaded' or 'forking')")
