import uvicorn

from bigraph_schema import allocate_core

from rest_process.server import start_server
from rest_process.processes.grow import GrowProcess


def test_server():
    core = allocate_core()
    server = start_server(core)

    uvicorn.run(server, host='0.0.0.0', port=22222)


if __name__ == '__main__':
    test_server()
