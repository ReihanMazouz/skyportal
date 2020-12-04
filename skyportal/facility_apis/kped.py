import time
import json
import requests
from datetime import datetime, timedelta
from sshtunnel import SSHTunnelForwarder
import urllib
import jwt

from . import FollowUpAPI
from baselayer.app.env import load_env

from ..utils import http

env, cfg = load_env()

KPED_URL = 'http://localhost:8001'
"""URL for the KPED scheduler."""


server = SSHTunnelForwarder(
    ('140.252.53.120', 22221),
    ssh_username=cfg["app.kped_username"],
    ssh_password=cfg["app.kped_password"],
    remote_bind_address=('127.0.0.1', 5000),
    local_bind_address=('localhost', 8001),
)

secret_key = cfg["app.kped_secret_key"]

print(cfg["app.kped_username"], cfg["app.kped_password"], cfg["app.kped_secret_key"])

class KPEDRequest:

    """A JSON structure for KPED requests."""

    def _build_payload(self, request):
        """Payload json for KPED queue requests.

        Parameters
        ----------

        request: skyportal.models.FollowupRequest
            The request to add to the queue and the SkyPortal database.

        Returns
        ----------
        payload: json
            payload for requests.
        """

        # The target of the observation
        target = {
            'name': request.obj.id,
            'type': 'ICRS',
            'ra': request.obj.ra,
            'dec': request.obj.dec,
            'epoch': 2000
        }

        exp_time = request.payload["exposure_time"]
        exp_count = int(request.payload["exposure_counts"])

        # The configurations for this request. In this example we are taking 2 exposures with different filters.
        targets = []
        for filt in request.payload['observation_choices']:
            target = {'id': request.id,
                      'name': request.obj.id,
                      'ra': request.obj.ra,
                      'dec': request.obj.dec,
                      'epoch': 2000,
                      'exposure_time': exp_time,
                      'exposure_counts': exp_count,
                      'filter': '%s' % filt,
                      'priority': request.payload["priority"],
                      'program_pi': 'Kulkarni' + '/' + request.requester.username
                     }
            targets.append(target)

        return {'targets': targets}

class KPEDAPI(FollowUpAPI):

    """An interface to KPED operations."""

    @staticmethod
    def delete(request):

        """Delete a follow-up request from KPED queue.

        Parameters
        ----------
        request: skyportal.models.FollowupRequest
            The request to delete from the queue and the SkyPortal database.
        """

        from ..models import DBSession, FollowupRequest, FacilityTransaction

        req = (
            DBSession()
            .query(FollowupRequest)
            .filter(FollowupRequest.id == request.id)
            .one()
        )

        # this happens for failed submissions
        # just go ahead and delete
        if len(req.transactions) == 0:
            DBSession().query(FollowupRequest).filter(
                FollowupRequest.id == request.id
            ).delete()
            DBSession().commit()
            return

        req = KPEDRequest()
        requestgroup = req._build_payload(request)

        payload = {
            'targets': requestgroup["targets"],
            'user': request.requester.username,
        }
        encoded_jwt = jwt.encode(payload, secret_key, algorithm='HS256')

        server.start()
        r = requests.delete(
            urllib.parse.urljoin(KPED_URL, 'api/queues'), data=encoded_jwt
        )
        server.stop()

        r.raise_for_status()
        request.status = "deleted"

        transaction = FacilityTransaction(
            request=http.serialize_requests_request(r.request),
            response=http.serialize_requests_response(r),
            followup_request=request,
            initiator_id=request.last_modified_by_id,
        )
        DBSession().add(transaction)

    # subclasses *must* implement the method below
    @staticmethod
    def submit(request):

        """Submit a follow-up request to KPED.

        Parameters
        ----------
        request: skyportal.models.FollowupRequest
            The request to add to the queue and the SkyPortal database.
        """

        from ..models import FacilityTransaction, DBSession

        req = KPEDRequest()
        requestgroup = req._build_payload(request)

        payload = {
            'targets': requestgroup["targets"],
            'user': request.requester.username,
        }
        encoded_jwt = jwt.encode(payload, secret_key, algorithm='HS256')

        server.start()
        r = requests.put(urllib.parse.urljoin(KPED_URL, 'api/queues'), data=encoded_jwt)
        server.stop()

        r.raise_for_status()

        if r.status_code == 201:
            request.status = 'submitted'
        else:
            request.status = f'rejected: {r.content}'

        transaction = FacilityTransaction(
            request=http.serialize_requests_request(r.request),
            response=http.serialize_requests_response(r),
            followup_request=request,
            initiator_id=request.last_modified_by_id,
        )

        DBSession().add(transaction)

    form_json_schema = {
        "type": "object",
        "properties": {
            "observation_choices": {
                "type": "array",
                "title": "Desired Observations",
                "items": {"type": "string", "enum": ["gs", "rs", "uj", "bj", "vj", "rj", "ij"]},
                "uniqueItems": True,
                "minItems": 1,
            },
            "exposure_time": {
                "title": "Exposure Time [s]",
                "type": "number",
                "default": 300.0,
            },
            "priority": {
                "type": "string",
                "enum": ["1", "2", "3", "4", "5"],
                "default": "1",
                "title": "Priority",
            },
            "exposure_counts": {
                "title": "Exposure Counts",
                "type": "number",
                "default": 1,
            },
        },
        "required": [
            "observation_choices",
            "exposure_time",
            "exposure_counts",
            "priority"
        ],
    }

    ui_json_schema = {"observation_choices": {"ui:widget": "checkboxes"}}
