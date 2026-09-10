"""Read-only role discovery from protocol replies, never names or USB descriptors."""
import asyncio
import re
import time

LABELS = {'companion':'Companion','repeater':'Repeater','room':'Room Server','unknown':'Unknown firmware'}


def parse_cli_role(reply):
    roles=set()
    complete=reply if reply.endswith(('\r','\n')) else reply.rsplit('\n',1)[0] if '\n' in reply else ''
    for line in complete.splitlines():
        m=re.fullmatch(r'\s*(?:->\s*)?>\s*(repeater|room_server)\s*',line)
        if m:roles.add({'repeater':'repeater','room_server':'room'}[m[1]])
    return roles.pop() if len(roles)==1 else 'unknown'


def probe_cli(port):
    import serial
    with serial.Serial(port,115200,timeout=0.15,write_timeout=1) as connection:
        connection.reset_input_buffer()
        connection.write(b'get role\r')
        deadline=time.monotonic()+2
        reply=bytearray()
        while time.monotonic()<deadline and len(reply)<4096:
            reply.extend(connection.read(min(512,4096-len(reply))))
            role=parse_cli_role(reply.decode('ascii',errors='replace'))
            if role!='unknown':return role
    return 'unknown'


async def detect(port):
    from device import operate,basic
    if not port.startswith('ble:'):
        role=await asyncio.to_thread(probe_cli,port)
        if role!='unknown':return role
    try:
        await operate(port,lambda mc:basic(mc,port))
        return 'companion'
    except (RuntimeError,TimeoutError):
        return 'unknown'
