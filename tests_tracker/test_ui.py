import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from tracker.storage import LocalStore

ROOT=Path(__file__).resolve().parents[1]


class InterfaceTests(unittest.TestCase):
    def test_local_interface_parse_edit_save_and_export(self):
        with tempfile.TemporaryDirectory() as d, patch('tracker.storage.GitHubStore', side_effect=lambda **kw:LocalStore(d)), patch.dict(os.environ, {'GITHUB_TOKEN':'','APP_PASSWORD':''}):
            at=AppTest.from_file(str(ROOT/'app.py'), default_timeout=15).run()
            self.assertFalse(at.exception)
            self.assertEqual(len(at.tabs), 4)
            at.text_input[0].input('test-only').run()
            at.text_area[0].input((ROOT/'examples/predictions.txt').read_text()).run()
            next(b for b in at.button if b.label=='Распознать').click().run()
            self.assertFalse(at.exception)
            self.assertEqual(at.session_state['preview'][0]['event'], 'Брест — Ницца')
            # Simulate the editor's checkbox interaction through widget state.
            at.session_state['prediction_editor'] = {'edited_rows': {0: {'Сохранить': True}}, 'added_rows': [], 'deleted_rows': []}
            at.checkbox(key='ack').check().run()
            next(b for b in at.button if b.label=='Подтвердить и сохранить').click().run()
            self.assertFalse(at.exception)
            self.assertIn('Последний импорт: 1', at.session_state['saved_message'])
            self.assertTrue((Path(d)/'data/imported_predictions.csv').exists())
            self.assertEqual(len(at.get('download_button')), 2)
    def test_shared_credential_fails_closed_without_password(self):
        with patch.dict(os.environ, {'GITHUB_TOKEN':'test-only','APP_PASSWORD':''}):
            at=AppTest.from_file(str(ROOT/'app.py')).run()
            self.assertFalse(at.exception)
            self.assertIn('APP_PASSWORD', at.error[0].value)
            self.assertEqual(len(at.tabs), 0)
