import pytest

from flask import url_for
from pytest_flask import fixtures

from mdt_app.models import *

@pytest.mark.usefixtures('client_class')
class TestIndex:

    def test_page_load(self):
        assert self.client.get(url_for('main.index')).status_code == 200

@pytest.mark.usefixtures('client_class')
class TestCaseCreate:

    def setup(self):
        self.patient1 = Patient(id=1, hospital_number=12345678,
                                first_name='test1', last_name='patient',
                                date_of_birth='1988-10-09', sex='F')

    def test_page_load(self, db_session):
        db_session.add(self.patient1)
        db_session.commit()
        req_pass = self.client.get(url_for('main.case_create', patient_id=1))
        req_no_id = self.client.get(url_for('main.case_create', patient_id=''))

        assert req_pass.status_code == 200

        assert req_no_id.status_code == 404, 'no id, page not found'
