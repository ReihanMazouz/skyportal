# inspired by https://github.com/growth-astro/growth-too-marshal/blob/main/growth/too/gcn.py

import os
import gcn
import lxml
import xmlschema
from urllib.parse import urlparse
import healpix_alchemy as ha
import numpy as np
from tornado.ioloop import IOLoop

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import sessionmaker, scoped_session

from baselayer.app.access import auth_or_token
from baselayer.log import make_log
from ..base import BaseHandler
from ...models import (
    DBSession,
    GcnEvent,
    GcnNotice,
    GcnTag,
    Localization,
    LocalizationTile,
)
from ...utils.gcn import get_dateobs, get_tags, get_skymap, get_contour

log = make_log('api/gcn_event')


Session = scoped_session(sessionmaker(bind=DBSession.session_factory.kw["bind"]))


class GcnEventHandler(BaseHandler):
    @auth_or_token
    def post(self):
        """
        ---
        description: Ingest GCN xml file
        tags:
          - gcnevents
          - gcntags
          - gcnnotices
          - localizations
        requestBody:
          content:
            application/json:
              schema: GcnHandlerPut
        responses:
          200:
            content:
              application/json:
                schema: Success
          400:
            content:
              application/json:
                schema: Error
        """
        data = self.get_json()
        payload = data['xml']

        schema = f'{os.path.dirname(__file__)}/../../utils/schema/VOEvent-v2.0.xsd'
        voevent_schema = xmlschema.XMLSchema(schema)
        if voevent_schema.is_valid(payload):
            root = lxml.etree.fromstring(payload.encode('ascii'))
        else:
            raise Exception("xml file is not valid VOEvent")

        dateobs = get_dateobs(root)

        try:
            event = GcnEvent.query.filter_by(dateobs=dateobs).one()

            if not event.is_accessible_by(self.current_user, mode="update"):
                return self.error(
                    "Insufficient permissions: GCN event can only be updated by original poster"
                )

        except NoResultFound:
            event = GcnEvent(dateobs=dateobs, sent_by_id=self.associated_user_object.id)
            DBSession().add(event)

        tags = [
            GcnTag(
                dateobs=event.dateobs,
                text=text,
                sent_by_id=self.associated_user_object.id,
            )
            for text in get_tags(root)
        ]

        gcn_notice = GcnNotice(
            content=payload.encode('ascii'),
            ivorn=root.attrib['ivorn'],
            notice_type=gcn.get_notice_type(root),
            stream=urlparse(root.attrib['ivorn']).path.lstrip('/'),
            date=root.find('./Who/Date').text,
            dateobs=event.dateobs,
            sent_by_id=self.associated_user_object.id,
        )

        for tag in tags:
            DBSession().add(tag)
        DBSession().add(gcn_notice)

        skymap = get_skymap(root, gcn_notice)
        skymap["dateobs"] = event.dateobs
        skymap["sent_by_id"] = self.associated_user_object.id

        try:
            localization = (
                Localization.query_records_accessible_by(
                    self.current_user,
                )
                .filter(
                    Localization.dateobs == dateobs,
                    Localization.localization_name == skymap["localization_name"],
                )
                .one()
            )
        except NoResultFound:
            localization = Localization(**skymap)
            DBSession().add(localization)
            DBSession().commit()

            IOLoop.current().run_in_executor(
                None, lambda: add_tiles(localization.id, self.current_user.id)
            )
            IOLoop.current().run_in_executor(
                None, lambda: add_contour(localization.id, self.current_user.id)
            )

        return self.success()

    @auth_or_token
    def get(self, dateobs=None):
        """
        ---
        description: Retrieve GCN events
        tags:
          - gcnevents
        responses:
          200:
            content:
              application/json:
                schema: GcnEventHandlerGet
          400:
            content:
              application/json:
                schema: Error
        """
        if dateobs is not None:
            event = (
                GcnEvent.query_records_accessible_by(
                    self.current_user,
                    options=[
                        joinedload(GcnEvent.localizations),
                        joinedload(GcnEvent.gcn_notices),
                    ],
                )
                .filter(GcnEvent.dateobs == dateobs)
                .first()
            )
            if event is None:
                return self.error("GCN event not found", status=404)

            data = {
                **event.to_dict(),
                "tags": event.tags,
                "lightcurve": event.lightcurve,
            }

            return self.success(data=data)

        q = GcnEvent.query_records_accessible_by(
            self.current_user,
            options=[
                joinedload(GcnEvent.localizations),
                joinedload(GcnEvent.gcn_notices),
            ],
        )

        events = []
        for event in q.all():
            events.append({**event.to_dict(), "tags": event.tags})

        return self.success(data=events)

    @auth_or_token
    def delete(self, dateobs):
        """
        ---
        description: Delete a GCN event
        tags:
          - gcnevents
        parameters:
          - in: path
            name: dateobs
            required: true
            schema:
              type: dateobs
        responses:
          200:
            content:
              application/json:
                schema: Success
          400:
            content:
              application/json:
                schema: Error
        """
        event = GcnEvent.query.filter_by(dateobs=dateobs).first()
        if event is None:
            return self.error("GCN event not found", status=404)

        if not event.is_accessible_by(self.current_user, mode="delete"):
            return self.error(
                "Insufficient permissions: GCN event can only be deleted by original poster"
            )

        DBSession().delete(event)
        self.verify_and_commit()

        return self.success()


def add_contour(localization_id, user_id):
    session = Session()
    try:
        localization = (
            Localization.query_records_accessible_by(session.query(User).get(user_id))
            .filter(
                Localization.id == localization_id,
            )
            .first()
        )
        localization = get_contour(localization)
        session.add(localization)
        session.commit()
    except Exception as e:
        return log(
            f"Unable to generate contour for localization {localization_id}: {e}"
        )
    finally:
        session.remove()


def add_tiles(localization_id, user_id):
    session = Session()
    try:
        localization = (
            Localization.query_records_accessible_by(session.query(User).get(user_id))
            .filter(
                Localization.id == localization_id,
            )
            .first()
        )

        # Loop over the skymap MOC indices and probabilities
        # and compute the integrated probability in the entire tile
        tiles, probs = [], []
        for uniq, probdensity in zip(localization.uniq, localization.probdensity):
            tile = LocalizationTile(
                localization_id=localization.id, uniq=int(uniq), probdensity=probdensity
            )
            area = (tile.nested_hi - tile.nested_lo + 1) * ha.healpix.PIXEL_AREA
            prob = probdensity * area
            tiles.append(tile)
            probs.append(prob)

        # Compute cumulative probabilities for the MOC (for ease of
        # computing the percentiles for sources contained)
        idx = np.argsort(probs)[::-1].astype(int)
        tiles, probs = [tiles[ii] for ii in idx], [probs[ii] for ii in idx]
        cumprobs = np.cumsum(probs)

        for tile, cumprob in zip(tiles, cumprobs):
            tile.cumprob = cumprob
        session.add_all(tiles)
        session.commit()
    except Exception as e:
        return log(f"Unable to generate tiles for localization {localization_id}: {e}")
    finally:
        session.remove()


class LocalizationHandler(BaseHandler):
    @auth_or_token
    def get(self, dateobs, localization_name):
        """
        ---
        description: Retrieve a GCN localization
        tags:
          - localizations
        parameters:
          - in: path
            name: dateobs
            required: true
            schema:
              type: dateobs
          - in: path
            name: localization_name
            required: true
            schema:
              type: localization_name
        responses:
          200:
            content:
              application/json:
                schema: LocalizationHandlerGet
          400:
            content:
              application/json:
                schema: Error
        """
        localization = (
            Localization.query_records_accessible_by(self.current_user)
            .filter(
                Localization.dateobs == dateobs,
                Localization.localization_name == localization_name,
            )
            .first()
        )
        if localization is None:
            return self.error("Localization not found", status=404)

        data = {
            **localization.to_dict(),
            "flat_2d": localization.flat_2d,
            "contour": localization.contour,
        }
        return self.success(data=data)

    @auth_or_token
    def delete(self, dateobs, localization_name):
        """
        ---
        description: Delete a GCN localization
        tags:
          - localizations
        parameters:
          - in: path
            name: dateobs
            required: true
            schema:
              type: dateobs
          - in: path
            name: localization_name
            required: true
            schema:
              type: localization_name
        responses:
          200:
            content:
              application/json:
                schema: LocalizationHandlerGet
          400:
            content:
              application/json:
                schema: Error
        """

        localization = Localization.query.filter_by(
            dateobs=dateobs, localization_name=localization_name
        ).first()

        if localization is None:
            return self.error("Localization not found", status=404)

        if not localization.is_accessible_by(self.current_user, mode="delete"):
            return self.error(
                "Insufficient permissions: Localization can only be deleted by original poster"
            )

        DBSession().delete(localization)
        self.verify_and_commit()

        return self.success()
