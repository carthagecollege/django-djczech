from django.conf import settings
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required

from djczech.reconciliation.data.models import Cheque
from djczech.reconciliation.forms import ChequeDataForm

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import desc
from datatables import DataTable
from datetime import date, datetime

import csv
import logging
logger = logging.getLogger(__name__)

EARL = settings.INFORMIX_EARL
STATUS="I"
if settings.DEBUG:
    STATUS="EYE"

@staff_member_required
def cheque_data(request):
    """
    Form that allows the user to upload bank data in CSV format
    and then inserts the data into the database
    """
    if request.method=='POST':
        form = ChequeDataForm(request.POST, request.FILES)
        if form.is_valid():
            # database connection
            engine = create_engine(EARL)
            Session = sessionmaker(bind=engine)
            session = Session()
            # munge the data from CSV file
            bank_data = form.cleaned_data['bank_data']
            # convert date to datetime
            import_date = datetime.combine(
                form.cleaned_data['import_date'], datetime.min.time()
            )
            # for some reason we set jbpayee equal to the import date
            # plus user info
            jbpayee = "{}_{}".format(
                form.cleaned_data['import_date'], request.user.username
            )
            # CSV headers
            fieldnames = (
                "jbstatus_date", "jbstatus", "jbamount",
                "jbaccount", "jbchkno", "jbpayee"
            )
            # read the CSV file
            reader = csv.DictReader(bank_data, fieldnames)
            for r in reader:
                # convert amount from string to float and strip dollar sign
                try:
                    jbamount = float(r["jbamount"][1:])
                except:
                    jbamount = 0
                # status date
                try:
                    jbstatus_date = datetime.strptime(
                        r["jbstatus_date"], "%m/%d/%Y"
                    )
                except:
                    jbstatus_date = None

                cheque = Cheque(
                    jbimprt_date=import_date,
                    jbstatus_date=jbstatus_date,
                    jbchkno=int(r["jbchkno"]), jbchknolnk=int(r["jbchkno"]),
                    jbstatus=STATUS, jbaction="", jbaccount=r["jbaccount"],
                    jbamount=jbamount, jbamountlnk=jbamount,
                    jbpayee=jbpayee
                )

                # insert the data
                session.add(cheque)

            session.commit()
            session.close()

            return HttpResponseRedirect(
                reverse("cheque_data_success")
            )
    else:
        form = ChequeDataForm()
    return render_to_response(
        "reconciliation/cheque/data_form.html",
        {"form": form,"earl":EARL},
        context_instance=RequestContext(request)
    )

@staff_member_required
def cheque_search(request):
    # database connection
    engine = create_engine(EARL)
    Session = sessionmaker(bind=engine)
    session = Session()

@staff_member_required
def cheque_ajax(request):
    # database connection
    engine = create_engine(EARL)
    Session = sessionmaker(bind=engine)
    session = Session()
    # query
    #cheques = session.query(Cheque).order_by(desc(jbissue_date)).limit(length)
    #cheques = session.query(Cheque).order_by(desc(Cheque.jbissue_date))
    cheques = session.query(Cheque)
    # datatable
    table = DataTable(request.GET, Cheque, cheques, [
        "jbchkno",
        "jbimprt_date",
        "jbstatus",
        "jbstatus_date",
        "jbaction",
        "jbaccount",
        "jbamount",
        "jbissue_date",
        "jbpostd_dat",
        "jbpayee",
        "jbseqno"
    ])

    table.add_data(link=lambda o: reverse("cheque_detail", args=[o.jbchkno]))
    table.add_data(pk=lambda o: o.jbchkno)
    #table.searchable(lambda queryset, user_input: cheque_search(queryset, user_input))

    session.close()
    return JsonResponse(table.json())

@staff_member_required
def cheque_list(request):
    '''
    # database connection
    engine = create_engine(EARL)
    Session = sessionmaker(bind=engine)
    session = Session()
    # query
    cheques = session.query(Cheque).order_by(desc(jbissue_date)).limit(100)
    session.close()
    '''

    #{"cheques": cheques,},
    return render_to_response(
        "dashboard/cheque/list.html",
        context_instance=RequestContext(request)
    )


@staff_member_required
def cheque_detail(request, cid=None):
    if not cid:
        # search POST
        try:
            cid = request.POST["cid"]
        except:
            return HttpResponseRedirect(
                reverse("cheque_list")
            )

    # database connection
    engine = create_engine(EARL)
    Session = sessionmaker(bind=engine)
    session = Session()
    cheque = session.query(Cheque).get(cid)
    session.close()

    return render_to_response(
        "dashboard/cheque/search.html",
        {"cheque":cheque,},
        context_instance=RequestContext(request)
    )

