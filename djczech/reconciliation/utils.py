from django.conf import settings

from djczech.reconciliation.sql import *
from djtools.fields import NOW

import logging
logger = logging.getLogger(__name__)

# move this to djtools
def handle_uploaded_file(f):
    ts = NOW.strftime("%Y%m%d%H%M%S%f")
    phile = "{}{}.csv".format(settings.CHEQUE_DATA_DIR, ts)
    destination = open(phile, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    return phile

def recce_cheques(request, session, import_date):
    # Drop the temporary tables, just in case
    try:
        session.execute("DROP TABLE tmp_voida")
        logger.debug("DROP TABLE tmp_voida")
    except:
        logger.debug("tmp_voida does not exist")

    try:
        session.execute("DROP TABLE tmp_voidb")
        logger.debug("DROP TABLE tmp_voidb")
    except:
        logger.debug("tmp_voidb does not exist")

    # Populate void temp table A
    session.execute(TMP_VOID_A)
    logger.debug("Populate void temp table A")
    logger.debug("TMP_VOID_A sql:")
    logger.debug(TMP_VOID_A)
    # Populate void temp table B
    session.execute(TMP_VOID_B)
    logger.debug("Populate void temp table B")
    logger.debug("TMP_VOID_B sql:")
    logger.debug(TMP_VOID_B)

    # Display temp table B data
    select_voidb = session.execute(SELECT_VOID_B).fetchall()
    logger.debug("Display temp table B data")
    logger.debug("SELECT_VOID_B sql:")
    logger.debug(SELECT_VOID_B)

    # set reconciliation status to 'v'
    session.execute(UPDATE_RECONCILIATION_STATUS)
    logger.debug("set reconciliation status to 'v'")
    logger.debug("UPDATE_RECONCILIATION_STATUS sql:")
    logger.debug(SELECT_VOID_B)

    # Find the duplicate check numbers and update those as 's'uspicious

    # Drop the temporary tables, just in case
    try:
        session.execute("DROP TABLE tmp_maxbtchdate")
        logger.debug("DROP TABLE tmp_maxbtchdate")
    except:
        logger.debug("tmp_maxbtchdate does not exist")

    try:
        session.execute("DROP TABLE tmp_DupCkNos")
        logger.debug("DROP TABLE tmp_DupCkNos")
    except:
        logger.debug("tmp_DupCkNos does not exist")

    try:
        session.execute("DROP TABLE tmp_4updtstatus")
        logger.debug("DROP TABLE tmp_4updtstatus")
    except:
        logger.debug("tmp_4updtstatus does not exist")

    # select import_date and stick it in a temp table, for some reason
    sql = SELECT_CURRENT_BATCH_DATE(import_date=import_date)
    session.execute(sql)
    logger.debug("select import_date and stick it in a temp table")
    logger.debug("SELECT_CURRENT_BATCH_DATE sql:")
    logger.debug(sql)

    # Select the duplicates
    sql = SELECT_DUPLICATES_1(import_date=import_date)
    duplicate_check_numbers = session.execute(sql)
    logger.debug("select the duplicates")
    logger.debug("SELECT_DUPLICATES_1 sql:")
    logger.debug(sql)

    # Selected for updating
    sql = SELECT_FOR_UPDATING(
        import_date=import_date,
        status=settings.IMPORT_STATUS
    )
    for_update_status = session.execute(sql)
    logger.debug("Selected for updating")
    logger.debug("SELECT_FOR_UPDATING sql:")
    logger.debug(sql)

    # Display the records selected to be updated
    select_records_for_update = session.execute(
        SELECT_RECORDS_FOR_UPDATE
    ).fetchall()
    logger.debug("Display the records selected to be updated")
    logger.debug("SELECT_RECORDS_FOR_UPDATE sql:")
    logger.debug(SELECT_RECORDS_FOR_UPDATE)

    # Update cheque status to 's'uspictious
    session.execute(UPDATE_STATUS_SUSPICIOUS)
    logger.debug("Update cheque status to 's'uspictious")
    logger.debug("UPDATE_STATUS_SUSPICIOUS sql:")
    logger.debug(UPDATE_STATUS_SUSPICIOUS)

    # Display duplicate records
    sql = SELECT_DUPLICATES_2(import_date=import_date)
    select_duplicates_2 = session.execute(sql).fetchall()
    logger.debug("Display duplicate records")
    logger.debug("SELECT_DUPLICATES_2 sql:")
    logger.debug(sql)

    # Find the cleared CheckNos and update gltr_rec as 'r'econciled
    # and ccreconjb_rec as 'ar' (auto-reconciled)

    # Drop the temporary table, just in case
    try:
        session.execute("DROP TABLE tmp_reconupdta")
        logger.debug("DROP TABLE tmp_reconupdta")
    except:
        logger.debug("tmp_reconupdta does not exist")

    # Find the cleared Check Numbers
    sql = SELECT_CLEARED_CHEQUES(
        import_date=import_date,
        suspicious=settings.SUSPICIOUS,
        auto_rec=settings.AUTO_REC,
        requi_rich=settings.REQUI_RICH,
        requi_vich=settings.REQUI_VICH
    )
    session.execute(sql)
    logger.debug("Find the cleared Check Numbers")
    logger.debug("SELECT_CLEARED_CHEQUES sql:")
    logger.debug(sql)

    # Set gltr_rec as 'r'econciled
    update_reconciled = session.execute(UPDATE_RECONCILED)
    logger.debug("Set gltr_rec as 'r'econciled")
    logger.debug("UPDATE_RECONCILED sql:")
    logger.debug(UPDATE_RECONCILED)

    # Set ccreconjb_rec as 'ar' (auto-reconciled)
    update_status = session.execute(UPDATE_STATUS_AUTO_REC)
    logger.debug("Set ccreconjb_rec as 'ar' (auto-reconciled)")
    logger.debug("UPDATE_STATUS_AUTO_REC sql:")
    logger.debug(UPDATE_STATUS_AUTO_REC)

    # Display the checks that have been reconciled
    select_reconciled = session.execute(SELECT_RECONCILIATED).fetchall()
    logger.debug("Display the checks that have been reconciled")
    logger.debug("SELECT_RECONCILIATED sql:")
    logger.debug(SELECT_RECONCILIATED)

    # Display any left over imported checks whose status has not changed
    select_remaining_eye = session.execute(SELECT_REMAINING_EYE).fetchall()
    logger.debug("Display any left over imported checks whose status has not changed")
    logger.debug("SELECT_REMAINING_EYE sql:")
    logger.debug(SELECT_REMAINING_EYE)

    return {
        "select_voidb":select_voidb,
        "select_records_for_update":select_records_for_update,
        "select_duplicates_2": select_duplicates_2,
        "select_reconciled":select_reconciled,
        "select_remaining_eye":select_remaining_eye
    }
