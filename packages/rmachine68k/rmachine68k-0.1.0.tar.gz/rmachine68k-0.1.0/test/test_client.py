def rmachine68k_client_connect_test(remote_client):
    pass


def rmachine68k_client_machine_test(remote_machine):
    assert remote_machine.cpu is not None
    assert remote_machine.mem is not None
    assert remote_machine.traps is not None
    # proxy method
    assert remote_machine.execute is not None


def rmachine68k_client_machine_cfg_test(remote_machine):
    assert remote_machine.cpu.get_cpu_name() == "68000"
    assert remote_machine.mem.get_ram_size_kib() == 1024
