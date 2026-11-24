"""Safe synchronization tested with real local Git repositories (no network)."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from scripts import bootstrap_sandbox as setup
from scripts.run_sandbox import InstanceLock

class SafeSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.remote=self.base/'remote';self.remote.mkdir()
        self.git(self.remote,'init','-b',setup.BRANCH)
        self.git(self.remote,'config','user.name','Sandbox Test');self.git(self.remote,'config','user.email','test@example.invalid')
        (self.remote/'sample.txt').write_text('first\n');self.git(self.remote,'add','.');self.git(self.remote,'commit','-m','initial')
        self.checkout=self.base/'checkout'
        subprocess.check_call(['git','clone','--quiet',str(self.remote),str(self.checkout)])
    def tearDown(self):self.temp.cleanup()
    @staticmethod
    def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.DEVNULL,text=True).strip()
    def test_clean_working_branch_fast_forwards(self):
        (self.remote/'sample.txt').write_text('second\n');self.git(self.remote,'commit','-am','next')
        with patch.object(setup,'REMOTE',str(self.remote)):
            result=setup.sync_repository(self.checkout,self.base/'isolated')
        self.assertEqual(result,self.checkout)
        self.assertEqual(self.git(result,'rev-parse','HEAD'),self.git(self.remote,'rev-parse','HEAD'))
    def test_dirty_files_index_and_head_are_preserved_in_original_checkout(self):
        (self.checkout/'sample.txt').write_text('staged work\n');self.git(self.checkout,'add','sample.txt')
        (self.checkout/'sample.txt').write_text('unstaged work\n');(self.checkout/'untracked.txt').write_text('keep me')
        before=(self.git(self.checkout,'rev-parse','HEAD'),self.git(self.checkout,'diff'),self.git(self.checkout,'diff','--cached'),self.git(self.checkout,'status','--porcelain'))
        with patch.object(setup,'REMOTE',str(self.remote)):
            result=setup.sync_repository(self.checkout,self.base/'isolated')
        self.assertNotEqual(result,self.checkout)
        after=(self.git(self.checkout,'rev-parse','HEAD'),self.git(self.checkout,'diff'),self.git(self.checkout,'diff','--cached'),self.git(self.checkout,'status','--porcelain'))
        self.assertEqual(after,before);self.assertEqual((self.checkout/'untracked.txt').read_text(),'keep me')
    def test_main_is_never_checked_out_over_or_modified(self):
        self.git(self.checkout,'checkout','-b','main');head=self.git(self.checkout,'rev-parse','HEAD')
        with patch.object(setup,'REMOTE',str(self.remote)):
            result=setup.sync_repository(self.checkout,self.base/'isolated')
        self.assertNotEqual(result,self.checkout)
        self.assertEqual(self.git(self.checkout,'branch','--show-current'),'main')
        self.assertEqual(self.git(self.checkout,'rev-parse','HEAD'),head)
    def test_duplicate_launcher_lock_and_crash_safe_release(self):
        path=self.base/'instance.lock'
        with InstanceLock(path):
            with self.assertRaises(RuntimeError):
                with InstanceLock(path):pass
        with InstanceLock(path):pass

if __name__=='__main__':unittest.main()
