import tempfile,unittest
from pathlib import Path
import app
class GraphTests(unittest.TestCase):
 def test_cycle(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/"a.py").write_text("import b\n");(p/"b.py").write_text("import a\n")
   r=app.scan(p)
   self.assertTrue(r["cycles"])
   self.assertIn("b",r["edges"]["a"])
if __name__=="__main__":unittest.main()
