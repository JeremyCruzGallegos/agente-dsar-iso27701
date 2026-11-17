from dsar_api.extensions import db
from dsar_api.models import InstitutionalCaseGuide
from dsar_api.services.case_guide_service import buscar_casos_guia
from scripts.seed_unsa_case_guides import CASES


def test_defines_exactly_50_distinct_unsa_guides():
    assert len(CASES) == 50
    assert len({(area, title) for area, title, *_ in CASES}) == 50


def test_guide_search_prioritizes_similar_unsa_case(app):
    with app.app_context():
        for index, (area, title, scenario, focus, keywords) in enumerate(CASES, 1):
            db.session.add(InstitutionalCaseGuide(
                code=f'UNSA-CG-{index:03d}', title=title, area=area, scenario=scenario,
                reasoning_focus=focus, keywords=keywords, active=True))
        db.session.commit()
        result = buscar_casos_guia('se filtraron notas y correos de estudiantes', 2)
        assert result
        assert result[0]['title'] == 'Filtración de calificaciones'


def test_guides_are_not_legal_provisions(app):
    with app.app_context():
        db.session.add(InstitutionalCaseGuide(
            code='UNSA-CG-TEST', title='Ejemplo', area='Prueba', scenario='Caso de ejemplo',
            reasoning_focus='Solo orientar.', keywords='ejemplo', active=True))
        db.session.commit()
        assert InstitutionalCaseGuide.query.count() == 1
