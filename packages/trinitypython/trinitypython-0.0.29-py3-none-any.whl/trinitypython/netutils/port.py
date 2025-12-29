import psutil
import socket
import ollama


def get_open_ports_and_programs():
    connections = psutil.net_connections(kind='inet')
    open_ports = {}

    for conn in connections:
        if conn.status == psutil.CONN_LISTEN:
            laddr = conn.laddr
            port = laddr.port
            pid = conn.pid

            try:
                proc = psutil.Process(pid)
                program_name = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                program_name = "Unknown"

            open_ports[port] = program_name

    return sorted([(k, v) for k, v in open_ports.items()], key=lambda x: x[0])


def show_open_ports_and_programs(desc_model=None):
    open_ports = get_open_ports_and_programs()
    cached_desc = {}

    if not open_ports:
        print("No open ports found.")
    else:
        print("Open Ports and Listening Programs:")
        for port, program in open_ports:
            if desc_model is not None:
                if program in cached_desc:
                    desc = f"- {cached_desc[program]}"
                else:
                    print(
                        f"Getting description for {program} service from "
                        f"OLLAMA")
                    response = ollama.chat(model=desc_model, messages=[
                        {
                            'role': 'user',
                            'content': f'summarize in 1 sentence what is '
                                       f'{program} service'
                        },
                    ])
                    cached_desc[program] = response['message']['content']
                    desc = f"- {response['message']['content']}"
            else:
                desc = ""
            print(f"Port {port}: {program} {desc}")


def get_port_details(port_list):
    # Get all network connections
    connections = psutil.net_connections(kind='inet')
    port_details = {}

    for port in port_list:
        port_info = []
        for conn in connections:
            if conn.laddr and conn.laddr.port == port:
                try:
                    proc = psutil.Process(conn.pid) if conn.pid else None
                    proc_name = proc.name() if proc else "Unknown"
                    proc_cmdline = " ".join(
                        proc.cmdline()) if proc else "Unknown"
                    proc_username = proc.username() if proc else "Unknown"
                except (psutil.NoSuchProcess, psutil.AccessDenied,
                        psutil.ZombieProcess):
                    proc_name = proc_cmdline = proc_username = "Unknown"

                info = {
                    "status": conn.status,
                    "pid": conn.pid,
                    "process_name": proc_name,
                    "process_cmdline": proc_cmdline,
                    "process_user": proc_username,
                    "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if
                    conn.laddr else None,
                    "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if
                    conn.raddr else None,
                    "family": socket.AddressFamily(conn.family).name,
                    "type": socket.SocketKind(conn.type).name
                }

                port_info.append(info)

        if port_info:
            port_details[port] = port_info
        else:
            port_details[port] = [{"error": "Port not found or not in use"}]

    return port_details
