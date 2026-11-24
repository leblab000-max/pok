"""Launch a private Chromium profile against the local-only application."""
import argparse
from pathlib import Path
import sys
import signal
from time import monotonic
import threading
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from poker_sandbox.server import SandboxServer

class InstanceLock:
    """OS lock, automatically released after a crash; no PID-file stale locks."""
    def __init__(self,path): self.path=path;self.stream=None
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.stream=self.path.open('a+b');self.stream.write(b'0');self.stream.flush();self.stream.seek(0)
        try:
            if sys.platform=='win32':
                import msvcrt
                msvcrt.locking(self.stream.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            self.stream.close();raise RuntimeError('Poker sandbox is already open. Close its browser before restarting.')
        return self
    def __exit__(self,*args): self.stream.close()

def local_route(route, origin):
    # Dedicated sandbox profile must never navigate to / contact a poker room.
    if route.request.url.startswith(('data:','about:','blob:')) or urlsplit(route.request.url).scheme in ('http','https') and route.request.url.split('/',3)[:3]==origin.split('/',3)[:3]:
        route.continue_()
    else: route.abort('blockedbyclient')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--serve-only',action='store_true',help='HTTP only; browser integration testing / Linux')
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--seconds',type=float,help='Optional finite runtime after browser startup')
    parser.add_argument('--directory',type=Path,default=ROOT/'runs/sandbox')
    args=parser.parse_args()
    if args.seconds is not None and not 0 < args.seconds < float('inf'): parser.error('--seconds must be finite and positive')
    stopping=threading.Event()
    # Avoid raising KeyboardInterrupt inside Playwright's greenlet dispatcher.
    for name in ('SIGINT','SIGTERM'):
        signal.signal(getattr(signal,name),lambda *_:stopping.set())
    with InstanceLock(args.directory/'instance.lock'):
        server=SandboxServer(args.directory,args.port)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        print(f'Poker sandbox: {server.url}\nVirtual chips only. Data: {args.directory.resolve()}',flush=True)
        try:
            if args.serve_only:
                deadline=monotonic()+args.seconds if args.seconds else float('inf')
                while thread.is_alive() and not stopping.wait(.25) and monotonic()<deadline: pass
            else:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as pw:
                    context=pw.chromium.launch_persistent_context(str(args.directory/'browser-profile'),
                        headless=args.headless,viewport=dict(width=1440,height=1000),
                        handle_sigint=False,handle_sigterm=False,handle_sighup=False,
                        service_workers='block',args=['--disable-background-networking'])
                    context.route('**/*',lambda route:local_route(route,server.url))
                    page=context.pages[0] if context.pages else context.new_page()
                    context.on('close',lambda:stopping.set())
                    page.goto(server.url)
                    deadline=monotonic()+args.seconds if args.seconds else float('inf')
                    try:
                        while context.pages and not stopping.is_set() and monotonic()<deadline:
                            page.wait_for_timeout(100)
                    except Exception as exc:
                        if not stopping.is_set() and not page.is_closed(): raise exc
                    finally: context.close()
        except KeyboardInterrupt: pass
        finally:
            server.shutdown();thread.join(timeout=5);server.server_close()

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(f'Cannot start Poker AI: {exc}',file=sys.stderr);sys.exit(1)
