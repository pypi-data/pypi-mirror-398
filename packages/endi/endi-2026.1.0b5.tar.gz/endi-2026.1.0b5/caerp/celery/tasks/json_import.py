import json
import os

import transaction
from celery.utils.log import get_task_logger
from pyramid_celery import celery_app

from caerp.celery.models import CsvImportJob
from caerp.celery.tasks import utils
from caerp.import_.sale_product import deserialize_catalog
from caerp.models.company import Company

IMPORT_ERROR_MESSAGE = (
    "Une erreur inconnue a été rencontrée à l'import de votre fichier, "
    "veuillez contacter votre administrateur en lui "
    "fournissant l'identifiant suivant : %s"
)


@celery_app.task(bind=True)
def import_json_company_sales_catalog(
    self,
    job_id,
    company_id,
    filepath,
):
    from caerp.models.base import DBSESSION

    logger = get_task_logger(__name__)

    logger.info(f" + Importing sales catalog for company : {company_id}")
    try:
        # Mark job started
        utils.start_job(self.request, CsvImportJob, job_id)
        transaction.begin()
        dbsession = DBSESSION()

        company = Company.get(company_id)

        with open(filepath) as f:
            objs, warnings = deserialize_catalog(company, json.load(f))

            dbsession.add_all(objs)
            dbsession.flush()
            msg = (
                f"{len(objs)} produits importés dans "
                f"le catalogue de l'enseigne f{company.name}"
            )
            transaction.commit()

    except Exception:
        transaction.abort()
        logger.exception(f"Error while importing catalog for Company {company_id}")
        errors = [IMPORT_ERROR_MESSAGE % job_id]
        utils.record_failure(CsvImportJob, job_id, errors)
    else:
        utils.record_completed(
            CsvImportJob,
            job_id,
            error_messages=warnings,
            messages=[msg],
        )

    finally:
        if filepath:
            try:
                logger.info(f"Deleting file {filepath}")
                os.remove(filepath)
            except Exception as e:
                logger.error(f"Unable to delete file")

    return ""
