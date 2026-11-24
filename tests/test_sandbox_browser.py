"""Real Chromium tests, opt in with POKER_BROWSER_TESTS=1 (also run in CI)."""
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest

from poker_sandbox.server import SandboxServer
from scripts.run_sandbox import local_route

@unittest.skipUnless(os.environ.get('POKER_BROWSER_TESTS')=='1','Optional Chromium suite; set POKER_BROWSER_TESTS=1')
class ChromiumTests(unittest.TestCase):
    def setUp(self):
        from playwright.sync_api import sync_playwright
        self.temp=tempfile.TemporaryDirectory();self.server=SandboxServer(self.temp.name,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.pw=sync_playwright().start()
        self.context=self.pw.chromium.launch_persistent_context(str(Path(self.temp.name)/'browser-profile'),
            headless=True,viewport=dict(width=1440,height=1000),service_workers='block')
        self.context.route('**/*',lambda route:local_route(route,self.server.url))
        self.page=self.context.pages[0];self.errors=[]
        self.page.on('pageerror',lambda error:self.errors.append(str(error)))
        self.page.goto(self.server.url);self.page.wait_for_function("document.querySelector('#status').textContent==='Готов к запуску'")
    def tearDown(self):
        self.context.close();self.pw.stop();self.server.shutdown();self.thread.join();self.server.server_close();self.temp.cleanup()
    def state(self):return self.server.session.snapshot()
    def wait(self,predicate,timeout=20):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            self.page.wait_for_timeout(30)
            if predicate():return
        self.fail('Browser scenario timed out: '+str(self.state().get('error')))
    def test_dashboard_start_pause_step_manual_stop_reset_and_responsive_layout(self):
        p=self.page;p.select_option('#players','2');p.select_option('#strategy','portfolio');p.select_option('#delay','1');p.fill('#samples','8')
        p.click('#start');self.wait(lambda:self.state()['pending'] is not None)
        p.click('#pause');count=self.state()['stats']['actions'];p.wait_for_timeout(300)
        self.assertEqual(self.state()['stats']['actions'],count)
        self.assertEqual(self.state()['pending']['seat'],0)
        p.locator('[data-action="call"]').click()
        self.wait(lambda:self.state()['stats']['actions']==count+1)
        self.assertEqual(self.state()['last_decision']['source'],'manual')
        self.wait(lambda:'CALL' in p.locator('#chosen').inner_text())
        p.click('#step');self.wait(lambda:self.state()['stats']['actions']==count+2)
        p.wait_for_timeout(250);self.assertEqual(self.state()['stats']['actions'],count+2)
        # Screenshots show actual game data from a paused real hand.
        output=Path(__file__).resolve().parents[1]/'runs/sandbox-test';output.mkdir(parents=True,exist_ok=True)
        p.screenshot(path=str(output/'desktop.png'),full_page=True)
        p.set_viewport_size(dict(width=390,height=844));p.wait_for_timeout(100)
        self.assertTrue(p.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        p.screenshot(path=str(output/'mobile.png'),full_page=True)
        p.click('#stop');self.wait(lambda:self.state()['status']=='stopped');count=self.state()['stats']['actions']
        p.wait_for_timeout(300);self.assertEqual(self.state()['stats']['actions'],count)
        self.assertTrue(p.locator('#start').is_disabled())
        p.click('#reset');self.wait(lambda:self.state()['status']=='ready')
        self.assertEqual(self.state()['stats']['actions'],0)
        self.assertEqual(self.errors,[])
    def test_nine_ai_tournament_and_only_loopback_network(self):
        p=self.page;p.select_option('#delay','0');p.fill('#samples','4');p.click('#start')
        self.wait(lambda:self.state()['status'] in ('completed','error'),30)
        state=self.state();self.assertEqual(state['status'],'completed',state['error'])
        self.assertEqual(sum(state['stacks'].values())+state['pot'],9000)
        p.set_viewport_size(dict(width=390,height=844));p.wait_for_timeout(300)
        self.assertTrue(p.evaluate("[...document.querySelectorAll('.seat')].every(el=>{const r=el.getBoundingClientRect();const t=document.querySelector('.table-wrap').getBoundingClientRect();return r.left>=t.left&&r.right<=t.right})"))
        self.assertEqual(state['stats']['tournaments'],1)
        self.assertTrue((Path(self.temp.name)/'browser-profile').exists())
        # Route rejects external origins without making a connection.
        result=p.evaluate("async()=>{try{await fetch('https://example.com/');return 'allowed'}catch(e){return 'blocked'}}")
        self.assertEqual(result,'blocked');self.assertEqual(self.errors,[])
    def test_all_six_manual_buttons_reach_the_actual_engine(self):
        # A check/call policy on all seats makes unopened postflop streets deterministic.
        from poker_ai.strategy import CallingBaseline
        with self.server.session.condition:
            self.server.session.factory=lambda *args:CallingBaseline()
        p=self.page;p.select_option('#players','2');p.select_option('#delay','1');p.fill('#samples','4')
        seen=set()
        for requested in ('fold','call','raise','all-in','check','bet'):
            p.click('#reset');p.click('#start');self.wait(lambda:self.state()['pending'] is not None);p.click('#pause')
            # Fold/call/raise/all-in available preflop; reach an unopened street for check/bet.
            for _ in range(80):
                state=self.state();pending=state['pending']
                if state['status'] in ('completed','error'):break
                if not pending:
                    p.click('#step')
                    self.wait(lambda:self.state()['pending'] is not None or self.state()['status'] in ('completed','error'))
                    continue
                button=p.locator(f'[data-action="{requested}"]')
                key={'raise':'raise_','all-in':'all_in'}.get(requested,requested)
                if pending['seat']==0 and pending['controls'][key]:
                    count=state['stats']['actions']
                    if requested in ('raise','bet'):p.fill('#amount',str(pending['controls']['minimum']))
                    button.click();self.wait(lambda:self.state()['stats']['actions']>count)
                    detail=self.state()['last_decision'];self.assertEqual(detail['source'],'manual')
                    self.assertEqual(detail['decision']['action'],'raise' if requested in ('bet','raise','all-in') else requested)
                    seen.add(requested);break
                # Keep hero alive while traversing; opponents use existing profile strategies.
                count=state['stats']['actions']
                if pending['seat']==0:
                    fallback='call' if pending['controls']['call'] else 'check'
                    p.locator(f'[data-action="{fallback}"]').click()
                else:p.click('#step')
                self.wait(lambda:self.state()['stats']['actions']>count)
            else:self.fail('Could not reach '+requested)
            self.assertIn(requested,seen)
        self.assertEqual(len(seen),6);self.assertEqual(self.errors,[])

if __name__=='__main__':unittest.main()
