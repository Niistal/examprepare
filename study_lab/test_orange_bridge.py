"""Launch the real installed Orange GUI through the authorized local bridge (offscreen).
No installation and no personal desktop/profile interaction. Requires an existing Orange launcher.
"""
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import urllib.request
from unittest.mock import patch
from local_server import create_server,orange_command

assert orange_command(),'Orange is not installed; no installation is performed by this test'
with tempfile.TemporaryDirectory(prefix='niis-orange-profile-') as profile:
    # Only profile paths and Qt rendering mode are replaced; launching is NOT mocked.
    environment={'QT_QPA_PLATFORM':'offscreen','XDG_CONFIG_HOME':profile+'/config','XDG_CACHE_HOME':profile+'/cache','XDG_DATA_HOME':profile+'/data'}
    with patch.dict(os.environ,environment):
        server=create_server(0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        process=None
        try:
            base=f'http://127.0.0.1:{server.server_port}'
            request=urllib.request.Request(base+'/api/tools/launch',data=json.dumps({'tool':'orange','practice':'M09'}).encode(),headers={'Content-Type':'application/json','Origin':base,'X-Study-Token':server.token})
            with urllib.request.urlopen(request,timeout=10) as response:
                assert response.status==200
                result=json.load(response);assert 'iniciado' in result['message']
            process=server.orange_process
            assert process is not None and process.poll() is None
            time.sleep(3)
            assert process.poll() is None,'Orange GUI exited after bridge startup'
            assert process.args[-1]==str(Path(__file__).resolve().parent/'resources/orange-M09.ows')
            print('PASS real Orange GUI process launched by authorized bridge with M09, alive after startup')
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:process.wait(timeout=10)
                except Exception:process.kill();process.wait(timeout=5)
            server.shutdown();server.server_close();thread.join(timeout=5)
print('PASS temporary Orange process and profile cleaned up')
