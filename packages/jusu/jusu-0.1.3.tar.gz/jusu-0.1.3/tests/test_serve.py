import time
import threading

from JUSU import cli


def test_start_and_stop_static_server(tmp_path):
    # start server on an ephemeral port (0 lets OS pick)
    server, thread, stop = cli.start_static_server(tmp_path, port=0)
    try:
        port = server.server_address[1]
        # server should be listening
        assert cli._is_port_open(port)
    finally:
        stop()
    # after stopping, port should not be open (may take a moment)
    time.sleep(0.1)
    assert not cli._is_port_open(port)


def test_watch_module_file_detects_change(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text("# initial\n")

    called = {"flag": False}

    def on_change():
        called["flag"] = True

    # schedule a file modification after a short delay
    def modify_file():
        time.sleep(0.3)
        f.write_text("# modified\n")

    t = threading.Thread(target=modify_file, daemon=True)
    t.start()

    changed = cli.watch_module_file(str(f), on_change, interval=0.1, timeout=5.0)
    assert changed is True
    assert called["flag"] is True
