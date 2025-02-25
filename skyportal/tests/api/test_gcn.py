import os
import numpy as np

from skyportal.tests import api
from skyportal.utils.gcn import from_url

import time
import uuid
import pandas as pd
from regions import Regions
from astropy.table import Table

import pytest


def test_gcn_GW(super_admin_token, view_only_token):

    datafile = f'{os.path.dirname(__file__)}/../data/GW190425_initial.xml'
    with open(datafile, 'rb') as fid:
        payload = fid.read()
    event_data = {'xml': payload}

    dateobs = "2019-04-25 08:18:05"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)
    if status == 404:
        status, data = api(
            'POST', 'gcn_event', data=event_data, token=super_admin_token
        )
        assert status == 200
        assert data['status'] == 'success'

    dateobs = "2019-04-25 08:18:05"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)
    assert status == 200
    data = data["data"]
    assert data["dateobs"] == "2019-04-25T08:18:05"
    assert 'GW' in data["tags"]
    property_dict = {
        'BBH': 0.0,
        'BNS': 0.999402567114,
        'FAR': 4.53764787126e-13,
        'NSBH': 0.0,
        'HasNS': 1.0,
        'MassGap': 0.0,
        'HasRemnant': 1.0,
        'Terrestrial': 0.00059743288626,
    }
    assert data["properties"][0]["data"] == property_dict

    params = {
        'startDate': "2019-04-25T00:00:00",
        'endDate': "2019-04-26T00:00:00",
        'gcnTagKeep': 'GW',
    }

    status, data = api('GET', 'gcn_event', token=super_admin_token, params=params)
    assert status == 200
    data = data["data"]
    assert len(data['events']) > 0
    data = data['events'][0]
    assert data["dateobs"] == "2019-04-25T08:18:05"
    assert 'GW' in data["tags"]

    params = {
        'startDate': "2019-04-25T00:00:00",
        'endDate': "2019-04-26T00:00:00",
        'gcnTagKeep': 'Fermi',
    }

    status, data = api('GET', 'gcn_event', token=super_admin_token, params=params)
    assert status == 200
    data = data["data"]
    assert len(data['events']) == 0

    params = {"include2DMap": True}
    skymap = "bayestar.fits.gz"
    status, data = api(
        'GET',
        f'localization/{dateobs}/name/{skymap}',
        token=super_admin_token,
        params=params,
    )

    data = data["data"]
    assert data["dateobs"] == "2019-04-25T08:18:05"
    assert data["localization_name"] == "bayestar.fits.gz"
    assert np.isclose(np.sum(data["flat_2d"]), 1)

    status, data = api(
        'DELETE',
        f'localization/{dateobs}/name/{skymap}',
        token=view_only_token,
    )
    assert status == 404

    status, data = api(
        'DELETE',
        f'localization/{dateobs}/name/{skymap}',
        token=super_admin_token,
    )
    assert status == 200


def test_gcn_Fermi(super_admin_token, view_only_token):

    datafile = f'{os.path.dirname(__file__)}/../data/GRB180116A_Fermi_GBM_Gnd_Pos.xml'
    with open(datafile, 'rb') as fid:
        payload = fid.read()
    event_data = {'xml': payload}

    dateobs = "2018-01-16 00:36:53"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)

    if status == 404:
        status, data = api(
            'POST', 'gcn_event', data=event_data, token=super_admin_token
        )
        assert status == 200
        assert data['status'] == 'success'

    params = {"include2DMap": True}
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)
    assert status == 200
    data = data["data"]
    assert data["dateobs"] == "2018-01-16T00:36:53"
    assert 'GRB' in data["tags"]

    skymap = "214.74000_28.14000_11.19000"
    status, data = api(
        'GET',
        f'localization/{dateobs}/name/{skymap}',
        token=super_admin_token,
        params=params,
    )

    data = data["data"]
    assert data["dateobs"] == "2018-01-16T00:36:53"
    assert data["localization_name"] == "214.74000_28.14000_11.19000"
    assert np.isclose(np.sum(data["flat_2d"]), 1)

    status, data = api(
        'DELETE',
        f'localization/{dateobs}/name/{skymap}',
        token=view_only_token,
    )
    assert status == 404

    status, data = api(
        'DELETE',
        f'localization/{dateobs}/name/{skymap}',
        token=super_admin_token,
    )
    assert status == 200


def test_gcn_from_moc(super_admin_token, view_only_token):

    name = str(uuid.uuid4())
    post_data = {
        'name': name,
        'nickname': name,
        'type': 'gravitational-wave',
        'fixed_location': True,
        'lat': 0.0,
        'lon': 0.0,
    }

    status, data = api('POST', 'mmadetector', data=post_data, token=super_admin_token)
    assert status == 200
    assert data['status'] == 'success'
    mmadetector_id = data['data']['id']

    skymap = f'{os.path.dirname(__file__)}/../data/GRB220617A_IPN_map_hpx.fits.gz'
    dateobs = '2022-06-18T18:31:12'
    tags = ['IPN', 'GRB', name]
    skymap = from_url(skymap)
    properties = {'BNS': 0.9, 'NSBH': 0.1}

    event_data = {
        'dateobs': dateobs,
        'skymap': skymap,
        'tags': tags,
        'properties': properties,
    }

    dateobs = "2022-06-18 18:31:12"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)

    if status == 404:
        status, data = api(
            'POST', 'gcn_event', data=event_data, token=super_admin_token
        )
        assert status == 200
        assert data['status'] == 'success'

    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)
    assert status == 200
    data = data["data"]
    assert data["dateobs"] == "2022-06-18T18:31:12"
    assert 'IPN' in data["tags"]
    assert name in [detector["name"] for detector in data["detectors"]]
    properties_dict = data["properties"][0]
    assert properties_dict["data"] == properties

    status, data = api('GET', f'mmadetector/{mmadetector_id}', token=super_admin_token)
    assert status == 200
    assert data['status'] == 'success'
    data = data["data"]
    assert "2022-06-18T18:31:12" in [event["dateobs"] for event in data["events"]]

    params = {'gcnPropertiesFilter': 'BNS: 0.5: gt, NSBH: 0.5: lt'}
    status, data = api('GET', 'gcn_event', token=super_admin_token, params=params)
    assert status == 200
    data = data["data"]
    assert "2022-06-18T18:31:12" in [event["dateobs"] for event in data['events']]

    params = {'gcnPropertiesFilter': 'BNS: 0.5: lt, NSBH: 0.5: lt'}
    status, data = api('GET', 'gcn_event', token=super_admin_token, params=params)
    assert status == 200
    data = data["data"]
    assert "2022-06-18T18:31:12" not in [event["dateobs"] for event in data['events']]


@pytest.mark.flaky(reruns=3)
def test_gcn_summary_sources(
    super_admin_user,
    super_admin_token,
    view_only_token,
    public_group,
    ztf_camera,
    upload_data_token,
):

    datafile = f'{os.path.dirname(__file__)}/../../../data/GW190814.xml'
    with open(datafile, 'rb') as fid:
        payload = fid.read()
    event_data = {'xml': payload}

    dateobs = "2019-08-14T21:10:39"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)

    if status == 404:
        status, data = api(
            'POST', 'gcn_event', data=event_data, token=super_admin_token
        )
        assert status == 200
        assert data['status'] == 'success'

    # wait for event to load
    for n_times in range(26):
        status, data = api('GET', f"gcn_event/{dateobs}", token=super_admin_token)
        if data['status'] == 'success':
            break
        time.sleep(2)
    assert n_times < 25

    # wait for the localization to load
    params = {"include2DMap": True}
    for n_times_2 in range(26):
        status, data = api(
            'GET',
            'localization/2019-08-14T21:10:39/name/LALInference.v1.fits.gz',
            token=super_admin_token,
            params=params,
        )

        if data['status'] == 'success':
            data = data["data"]
            assert data["dateobs"] == "2019-08-14T21:10:39"
            assert data["localization_name"] == "LALInference.v1.fits.gz"
            assert np.isclose(np.sum(data["flat_2d"]), 1)
            break
        else:
            time.sleep(2)
    assert n_times_2 < 25

    obj_id = str(uuid.uuid4())
    status, data = api(
        "POST",
        "sources",
        data={
            "id": obj_id,
            "ra": 24.6258,
            "dec": -32.9024,
            "redshift": 3,
        },
        token=upload_data_token,
    )
    assert status == 200

    status, data = api("GET", f"sources/{obj_id}", token=view_only_token)
    assert status == 200

    status, data = api(
        'POST',
        'photometry',
        data={
            'obj_id': obj_id,
            'mjd': 58709 + 1,
            'instrument_id': ztf_camera.id,
            'flux': 12.24,
            'fluxerr': 0.031,
            'zp': 25.0,
            'magsys': 'ab',
            'filter': 'ztfg',
            "ra": 24.6258,
            "dec": -32.9024,
            "ra_unc": 0.01,
            "dec_unc": 0.01,
        },
        token=upload_data_token,
    )
    assert status == 200
    assert data['status'] == 'success'

    # get the gcn event summary
    data = {
        "title": "gcn summary",
        "subject": "follow-up",
        "userIds": super_admin_user.id,
        "groupId": public_group.id,
        "startDate": "2019-08-13 08:18:05",
        "endDate": "2019-08-19 08:18:05",
        "localizationCumprob": 0.99,
        "numberDetections": 1,
        "showSources": True,
        "showGalaxies": False,
        "showObservations": False,
        "noText": False,
    }

    status, data = api(
        'POST',
        'gcn_event/2019-08-14T21:10:39/summary',
        data=data,
        token=super_admin_token,
    )
    assert status == 200
    summary_id = data["data"]["id"]

    nretries = 0
    summaries_loaded = False
    while nretries < 40:
        status, data = api(
            'GET',
            f'gcn_event/2019-08-14T21:10:39/summary/{summary_id}',
            token=view_only_token,
            params=params,
        )
        if status == 404:
            nretries = nretries + 1
            time.sleep(5)
        if status == 200:
            data = data["data"]
            if data["text"] == "pending":
                nretries = nretries + 1
                time.sleep(5)
            else:
                summaries_loaded = True
                break

    assert nretries < 40
    assert summaries_loaded
    data = list(filter(None, data["text"].split("\n")))

    assert "TITLE: GCN SUMMARY" in data[0]
    assert "SUBJECT: Follow-up" in data[1]
    assert "DATE" in data[2]
    assert (
        f"FROM:  {super_admin_user.first_name} {super_admin_user.last_name} at ... <{super_admin_user.contact_email}>"
        in data[3]
    )
    assert (
        f"{super_admin_user.first_name.upper()[0]}. {super_admin_user.last_name} (...)"
        in data[4]
    )
    assert f"on behalf of the {public_group.name}, report:" in data[5]

    # sources
    assert (
        "Found" in data[6]
        and "in the event's localization, given the specified date range:" in data[6]
    )
    table = data[7:]
    idx = ["Photometry for source" in line for line in table].index(True)
    sources_table = table[: idx - 1]
    photometry_table = table[idx + 1 :]

    assert (
        len(sources_table) >= 6
    )  # other sources have probably been added in previous tests
    assert "id" in sources_table[1]
    assert "alias" in sources_table[1]
    assert "ra" in sources_table[1]
    assert "dec" in sources_table[1]
    assert "redshift" in sources_table[1]

    # source phot
    assert "Photometry for source" in table[idx]

    assert (
        len(photometry_table) >= 5
    )  # other photometry have probably been added in previous tests
    assert "mjd" in photometry_table[1]
    assert "mag±err (ab)" in photometry_table[1]
    assert "filter" in photometry_table[1]
    assert "origin" in photometry_table[1]
    assert "instrument" in photometry_table[1]


def test_gcn_summary_galaxies(
    super_admin_user,
    super_admin_token,
    view_only_token,
    public_group,
):

    catalog_name = 'test_galaxy_catalog'

    # in case the catalog already exists, delete it.
    status, data = api(
        'DELETE', f'galaxy_catalog/{catalog_name}', token=super_admin_token
    )

    datafile = f'{os.path.dirname(__file__)}/../../../data/GW190814.xml'
    with open(datafile, 'rb') as fid:
        payload = fid.read()
    event_data = {'xml': payload}

    dateobs = "2019-08-14T21:10:39"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)

    if status == 404:
        status, data = api(
            'POST', 'gcn_event', data=event_data, token=super_admin_token
        )
        assert status == 200
        assert data['status'] == 'success'

    # wait for event to load
    for n_times in range(26):
        status, data = api('GET', f"gcn_event/{dateobs}", token=super_admin_token)
        if data['status'] == 'success':
            break
        time.sleep(2)
    assert n_times < 25

    # wait for the localization to load
    params = {"include2DMap": True}
    for n_times_2 in range(26):
        status, data = api(
            'GET',
            'localization/2019-08-14T21:10:39/name/LALInference.v1.fits.gz',
            token=super_admin_token,
            params=params,
        )

        if data['status'] == 'success':
            data = data["data"]
            assert data["dateobs"] == "2019-08-14T21:10:39"
            assert data["localization_name"] == "LALInference.v1.fits.gz"
            assert np.isclose(np.sum(data["flat_2d"]), 1)
            break
        else:
            time.sleep(2)
    assert n_times_2 < 25

    datafile = f'{os.path.dirname(__file__)}/../../../data/CLU_mini.hdf5'
    data = {
        'catalog_name': catalog_name,
        'catalog_data': Table.read(datafile).to_pandas().to_dict(orient='list'),
    }

    status, data = api('POST', 'galaxy_catalog', data=data, token=super_admin_token)
    assert status == 200
    assert data['status'] == 'success'

    params = {'catalog_name': catalog_name}

    nretries = 0
    galaxies_loaded = False
    while nretries < 40:
        status, data = api(
            'GET', 'galaxy_catalog', token=view_only_token, params=params
        )
        assert status == 200
        data = data["data"]["galaxies"]
        if len(data) == 92 and any(
            [
                d['name'] == '6dFgs gJ0001313-055904'
                and d['mstar'] == 336.60756522868667
                for d in data
            ]
        ):
            galaxies_loaded = True
            break
        nretries = nretries + 1
        time.sleep(2)

    assert nretries < 40
    assert galaxies_loaded

    # get the gcn event summary
    data = {
        "title": "gcn summary",
        "subject": "follow-up",
        "userIds": super_admin_user.id,
        "groupId": public_group.id,
        "startDate": "2019-08-13 08:18:05",
        "endDate": "2019-08-19 08:18:05",
        "localizationCumprob": 0.99,
        "showSources": False,
        "showGalaxies": True,
        "showObservations": False,
        "noText": False,
    }

    status, data = api(
        'POST',
        'gcn_event/2019-08-14T21:10:39/summary',
        data=data,
        token=super_admin_token,
    )
    assert status == 200
    summary_id = data["data"]["id"]

    nretries = 0
    summaries_loaded = False
    while nretries < 40:
        status, data = api(
            'GET',
            f'gcn_event/2019-08-14T21:10:39/summary/{summary_id}',
            token=view_only_token,
            params=params,
        )
        if status == 404:
            nretries = nretries + 1
            time.sleep(5)
        if status == 200:
            data = data["data"]
            if data["text"] == "pending":
                nretries = nretries + 1
                time.sleep(5)
            else:
                summaries_loaded = True
                break

    assert nretries < 40
    assert summaries_loaded
    data = list(filter(None, data["text"].split("\n")))

    assert "TITLE: GCN SUMMARY" in data[0]
    assert "SUBJECT: Follow-up" in data[1]
    assert "DATE" in data[2]
    assert (
        f"FROM:  {super_admin_user.first_name} {super_admin_user.last_name} at ... <{super_admin_user.contact_email}>"
        in data[3]
    )
    assert (
        f"{super_admin_user.first_name.upper()[0]}. {super_admin_user.last_name} (...)"
        in data[4]
    )
    assert f"on behalf of the {public_group.name}, report:" in data[5]

    # galaxies
    assert "Found 82 galaxies in the event's localization:" in data[6]

    galaxy_table = data[7:]
    assert len(galaxy_table) == 86
    assert "catalog" in galaxy_table[1]
    assert "name" in galaxy_table[1]
    assert "ra" in galaxy_table[1]
    assert "dec" in galaxy_table[1]
    assert "distmpc" in galaxy_table[1]
    assert "redshift" in galaxy_table[1]

    status, data = api(
        'DELETE', f'galaxy_catalog/{catalog_name}', token=super_admin_token
    )


def test_gcn_instrument_field(
    super_admin_user,
    super_admin_token,
    view_only_token,
    public_group,
):

    datafile = f'{os.path.dirname(__file__)}/../../../data/GW190814.xml'
    with open(datafile, 'rb') as fid:
        payload = fid.read()
    event_data = {'xml': payload}

    dateobs = "2019-08-14T21:10:39"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)

    if status == 404:
        status, data = api(
            'POST', 'gcn_event', data=event_data, token=super_admin_token
        )
        assert status == 200
        assert data['status'] == 'success'

    # wait for event to load
    for n_times in range(26):
        status, data = api('GET', f"gcn_event/{dateobs}", token=super_admin_token)
        if data['status'] == 'success':
            break
        time.sleep(2)
    assert n_times < 25

    # wait for the localization to load
    params = {"include2DMap": True}
    for n_times_2 in range(26):
        status, data = api(
            'GET',
            'localization/2019-08-14T21:10:39/name/LALInference.v1.fits.gz',
            token=super_admin_token,
            params=params,
        )

        if data['status'] == 'success':
            data = data["data"]
            assert data["dateobs"] == "2019-08-14T21:10:39"
            assert data["localization_name"] == "LALInference.v1.fits.gz"
            assert np.isclose(np.sum(data["flat_2d"]), 1)
            break
        else:
            time.sleep(2)
    assert n_times_2 < 25

    name = str(uuid.uuid4())
    status, data = api(
        'POST',
        'telescope',
        data={
            'name': name,
            'nickname': name,
            'lat': 0.0,
            'lon': 0.0,
            'elevation': 0.0,
            'diameter': 10.0,
        },
        token=super_admin_token,
    )
    assert status == 200
    assert data['status'] == 'success'
    telescope_id = data['data']['id']

    fielddatafile = f'{os.path.dirname(__file__)}/../../../data/ZTF_Fields.csv'
    regionsdatafile = f'{os.path.dirname(__file__)}/../../../data/ZTF_Region.reg'

    instrument_name = str(uuid.uuid4())
    status, data = api(
        'POST',
        'instrument',
        data={
            'name': instrument_name,
            'type': 'imager',
            'band': 'Optical',
            'filters': ['ztfr'],
            'telescope_id': telescope_id,
            'api_classname': 'ZTFAPI',
            'api_classname_obsplan': 'ZTFMMAAPI',
            'field_data': pd.read_csv(fielddatafile)[199:204].to_dict(orient='list'),
            'field_region': Regions.read(regionsdatafile).serialize(format='ds9'),
        },
        token=super_admin_token,
    )
    assert status == 200
    assert data['status'] == 'success'
    instrument_id = data['data']['id']

    # wait for the fields to populate
    nretries = 0
    fields_loaded = False
    while not fields_loaded and nretries < 5:
        try:
            status, data = api(
                'GET',
                f'instrument/{instrument_id}',
                token=super_admin_token,
            )
            assert status == 200
            assert data['status'] == 'success'
            assert data['data']['band'] == 'NIR'

            assert len(data['data']['fields']) == 5
            fields_loaded = True
        except AssertionError:
            nretries = nretries + 1
            time.sleep(3)

    status, data = api(
        'GET',
        f'gcn_event/{dateobs}/instrument/{instrument_id}',
        token=super_admin_token,
    )
    assert status == 200
    assert data['status'] == 'success'

    assert 'field_ids' in data['data']
    assert 'probabilities' in data['data']

    assert set(data['data']['field_ids']) == {200, 201, 202}


def test_gcn_summary_observations(
    super_admin_user,
    super_admin_token,
    view_only_token,
    public_group,
):

    datafile = f'{os.path.dirname(__file__)}/../../../data/GW190814.xml'
    with open(datafile, 'rb') as fid:
        payload = fid.read()
    event_data = {'xml': payload}

    dateobs = "2019-08-14T21:10:39"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)

    if status == 404:
        status, data = api(
            'POST', 'gcn_event', data=event_data, token=super_admin_token
        )
        assert status == 200
        assert data['status'] == 'success'

        gcnevent_id = data['data']['gcnevent_id']
    else:
        gcnevent_id = data['data']['id']

    # wait for event to load
    for n_times in range(26):
        status, data = api('GET', f"gcn_event/{dateobs}", token=super_admin_token)
        if data['status'] == 'success':
            break
        time.sleep(2)
    assert n_times < 25

    # wait for the localization to load
    params = {"include2DMap": True}
    for n_times_2 in range(26):
        status, data = api(
            'GET',
            'localization/2019-08-14T21:10:39/name/LALInference.v1.fits.gz',
            token=super_admin_token,
            params=params,
        )

        if data['status'] == 'success':
            data = data["data"]
            assert data["dateobs"] == "2019-08-14T21:10:39"
            assert data["localization_name"] == "LALInference.v1.fits.gz"
            assert np.isclose(np.sum(data["flat_2d"]), 1)
            break
        else:
            time.sleep(2)
    assert n_times_2 < 25
    localization_id = data['id']

    name = str(uuid.uuid4())
    status, data = api(
        'POST',
        'telescope',
        data={
            'name': name,
            'nickname': name,
            'lat': 0.0,
            'lon': 0.0,
            'elevation': 0.0,
            'diameter': 10.0,
        },
        token=super_admin_token,
    )
    assert status == 200
    assert data['status'] == 'success'
    telescope_id = data['data']['id']

    fielddatafile = f'{os.path.dirname(__file__)}/../../../data/ZTF_Fields.csv'
    regionsdatafile = f'{os.path.dirname(__file__)}/../../../data/ZTF_Region.reg'

    instrument_name = str(uuid.uuid4())
    status, data = api(
        'POST',
        'instrument',
        data={
            'name': instrument_name,
            'type': 'imager',
            'band': 'Optical',
            'filters': ['ztfr'],
            'telescope_id': telescope_id,
            'api_classname': 'ZTFAPI',
            'api_classname_obsplan': 'ZTFMMAAPI',
            'field_data': pd.read_csv(fielddatafile)[199:204].to_dict(orient='list'),
            'field_region': Regions.read(regionsdatafile).serialize(format='ds9'),
        },
        token=super_admin_token,
    )
    assert status == 200
    assert data['status'] == 'success'
    instrument_id = data['data']['id']

    # wait for the fields to populate
    nretries = 0
    fields_loaded = False
    while not fields_loaded and nretries < 5:
        try:
            status, data = api(
                'GET',
                f'instrument/{instrument_id}',
                token=super_admin_token,
            )
            assert status == 200
            assert data['status'] == 'success'
            assert data['data']['band'] == 'NIR'

            assert len(data['data']['fields']) == 5
            fields_loaded = True
        except AssertionError:
            nretries = nretries + 1
            time.sleep(3)

    request_data = {
        'group_id': public_group.id,
        'instrument_id': instrument_id,
        'pi': 'Shri Kulkarni',
        'hours_allocated': 200,
        'start_date': '3021-02-27T00:00:00',
        'end_date': '3021-07-20T00:00:00',
        'proposal_id': 'COO-2020A-P01',
    }

    status, data = api('POST', 'allocation', data=request_data, token=super_admin_token)
    assert status == 200
    assert data['status'] == 'success'
    allocation_id = data['data']['id']

    queue_name = str(uuid.uuid4())
    request_data = {
        'allocation_id': allocation_id,
        'gcnevent_id': gcnevent_id,
        'localization_id': localization_id,
        'payload': {
            'start_date': '2019-08-15 08:18:05',
            'end_date': '2019-08-20 08:18:05',
            'filter_strategy': 'block',
            'schedule_strategy': 'tiling',
            'schedule_type': 'greedy_slew',
            'exposure_time': 300,
            "field_ids": [200, 201, 202],
            'filters': 'ztfr',
            'maximum_airmass': 2.0,
            'integrated_probability': 100,
            'minimum_time_difference': 30,
            'queue_name': queue_name,
            'program_id': 'Partnership',
            'subprogram_name': 'GRB',
        },
    }

    status, data = api(
        'POST', 'observation_plan', data=request_data, token=super_admin_token
    )
    assert status == 200
    assert data['status'] == 'success'
    id = data['data']['ids'][0]

    # wait for the observation plan to finish loading
    time.sleep(15)

    status, data = api(
        'GET',
        f'observation_plan/{id}',
        params={"includePlannedObservations": "true"},
        token=super_admin_token,
    )
    assert status == 200
    assert data['status'] == 'success'

    assert data["data"]["gcnevent_id"] == gcnevent_id
    assert data["data"]["allocation_id"] == allocation_id
    assert data["data"]["payload"] == request_data["payload"]

    assert len(data["data"]["observation_plans"]) == 1

    datafile = f'{os.path.dirname(__file__)}/../../../data/sample_observation_gw.csv'
    data = {
        'telescopeName': name,
        'instrumentName': instrument_name,
        'observationData': pd.read_csv(datafile).to_dict(orient='list'),
    }

    status, data = api('POST', 'observation', data=data, token=super_admin_token)

    assert status == 200
    assert data['status'] == 'success'

    # wait for the executed observations to populate

    params = {
        'telescopeName': name,
        'instrumentName': instrument_name,
        'startDate': '2019-08-13 08:18:05',
        'endDate': '2019-08-19 08:18:05',
    }
    nretries = 0
    observations_loaded = False
    while not observations_loaded and nretries < 25:
        try:
            status, data = api(
                'GET', 'observation', params=params, token=super_admin_token
            )
            assert status == 200
            data = data["data"]
            assert len(data['observations']) >= 9
            observations_loaded = True
        except AssertionError:
            nretries = nretries + 1
            time.sleep(2)

    assert nretries < 25
    assert status == 200
    assert observations_loaded is True

    # get the gcn event summary
    data = {
        "title": "gcn summary",
        "subject": "follow-up",
        "userIds": super_admin_user.id,
        "groupId": public_group.id,
        "startDate": "2019-08-13 08:18:05",
        "endDate": "2019-08-19 08:18:05",
        "localizationCumprob": 0.99,
        "showSources": False,
        "showGalaxies": False,
        "showObservations": True,
        "noText": False,
    }

    status, data = api(
        'POST',
        'gcn_event/2019-08-14T21:10:39/summary',
        data=data,
        token=super_admin_token,
    )
    assert status == 200
    summary_id = data["data"]["id"]

    nretries = 0
    summaries_loaded = False
    while nretries < 40:
        status, data = api(
            'GET',
            f'gcn_event/2019-08-14T21:10:39/summary/{summary_id}',
            token=view_only_token,
            params=params,
        )
        if status == 404:
            nretries = nretries + 1
            time.sleep(5)
        if status == 200:
            data = data["data"]
            if data["text"] == "pending":
                nretries = nretries + 1
                time.sleep(5)
            else:
                summaries_loaded = True
                break

    assert nretries < 40
    assert summaries_loaded
    data = list(filter(None, data["text"].split("\n")))

    assert "TITLE: GCN SUMMARY" in data[0]
    assert "SUBJECT: Follow-up" in data[1]
    assert "DATE" in data[2]
    assert (
        f"FROM:  {super_admin_user.first_name} {super_admin_user.last_name} at ... <{super_admin_user.contact_email}>"
        in data[3]
    )
    assert (
        f"{super_admin_user.first_name.upper()[0]}. {super_admin_user.last_name} (...)"
        in data[4]
    )
    assert f"on behalf of the {public_group.name}, report:" in data[5]

    # obs
    assert "Observations:" in data[6]

    obs_summary_text = (
        'We observed the localization region of LVC trigger 2019-08-14T21:10:39.000 UTC.  '
        'We obtained a total of 9 images covering ztfr bands for a total of 270 seconds. '
        'The observations covered 26.5 square degrees beginning at 2019-08-17T01:00:00.288 '
        '(2 days after the burst trigger time) corresponding to ~9% '
        'of the probability enclosed in the localization region.'
    )

    assert obs_summary_text in data[8]

    obs_table = data[10:]
    assert len(obs_table) >= 13  # other obs have probably been added in previous tests
    assert "T-T0 (hr)" in obs_table[1]
    assert "mjd" in obs_table[1]
    assert "ra" in obs_table[1]
    assert "dec" in obs_table[1]
    assert "filter" in obs_table[1]
    assert "exposure" in obs_table[1]
    assert "limmag (ab)" in obs_table[1]


def test_confirm_reject_source_in_gcn(
    super_admin_token,
    view_only_token,
    ztf_camera,
    upload_data_token,
):

    datafile = f'{os.path.dirname(__file__)}/../../../data/GW190814.xml'
    with open(datafile, 'rb') as fid:
        payload = fid.read()
    event_data = {'xml': payload}

    dateobs = "2019-08-14T21:10:39"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)

    if status == 404:
        status, data = api(
            'POST', 'gcn_event', data=event_data, token=super_admin_token
        )
        assert status == 200
        assert data['status'] == 'success'

    # wait for event to load
    for n_times in range(26):
        status, data = api('GET', f"gcn_event/{dateobs}", token=super_admin_token)
        if data['status'] == 'success':
            break
        time.sleep(2)
    assert n_times < 25

    # wait for the localization to load
    params = {"include2DMap": True}
    for n_times_2 in range(26):
        status, data = api(
            'GET',
            'localization/2019-08-14T21:10:39/name/LALInference.v1.fits.gz',
            token=super_admin_token,
            params=params,
        )

        if data['status'] == 'success':
            data = data["data"]
            assert data["dateobs"] == "2019-08-14T21:10:39"
            assert data["localization_name"] == "LALInference.v1.fits.gz"
            assert np.isclose(np.sum(data["flat_2d"]), 1)
            break
        else:
            time.sleep(2)
    assert n_times_2 < 25

    obj_id = str(uuid.uuid4())
    status, data = api(
        "POST",
        "sources",
        data={
            "id": obj_id,
            "ra": 24.6258,
            "dec": -32.9024,
            "redshift": 3,
        },
        token=upload_data_token,
    )
    assert status == 200

    status, data = api("GET", f"sources/{obj_id}", token=view_only_token)
    assert status == 200

    status, data = api(
        'POST',
        'photometry',
        data={
            'obj_id': obj_id,
            'mjd': 58709 + 1,
            'instrument_id': ztf_camera.id,
            'flux': 12.24,
            'fluxerr': 0.031,
            'zp': 25.0,
            'magsys': 'ab',
            'filter': 'ztfg',
            "ra": 24.6258,
            "dec": -32.9024,
            "ra_unc": 0.01,
            "dec_unc": 0.01,
        },
        token=upload_data_token,
    )
    assert status == 200
    assert data['status'] == 'success'

    params = {
        "sourcesIdList": obj_id,
    }
    status, data = api(
        'GET',
        'sources_in_gcn/2019-08-14T21:10:39',
        params=params,
        token=upload_data_token,
    )
    assert status == 200
    assert len(data["data"]) == 0

    # confirm source
    params = {
        "source_id": obj_id,
        "localization_name": "LALInference.v1.fits.gz",
        "localization_cumprob": 0.95,
        "confirmed": True,
        "start_date": "2019-08-13 08:18:05",
        "end_date": "2019-08-19 08:18:05",
    }

    # verify that you can't confirm a source without the Manage GCNs permission
    status, data = api(
        'POST',
        'sources_in_gcn/2019-08-14T21:10:39',
        data=params,
        token=upload_data_token,
    )
    assert status == 401

    status, data = api(
        'POST',
        'sources_in_gcn/2019-08-14T21:10:39',
        data=params,
        token=super_admin_token,
    )
    assert status == 200

    params = {
        "sourcesIdList": obj_id,
    }
    status, data = api(
        'GET',
        'sources_in_gcn/2019-08-14T21:10:39',
        params=params,
        token=upload_data_token,
    )
    assert status == 200
    data = data["data"]
    assert len(data) == 1
    assert data[0]["obj_id"] == obj_id
    assert data[0]["dateobs"] == "2019-08-14T21:10:39"
    assert data[0]["confirmed"] is True

    # find gcns associated to source
    status, data = api(
        'GET',
        f"associated_gcns/{obj_id}",
        token=upload_data_token,
    )
    assert status == 200
    data = data["data"]
    assert '2019-08-14T21:10:39' in data['gcns']

    # reject source
    params = {
        "confirmed": False,
    }

    status, data = api(
        'PATCH',
        f'sources_in_gcn/2019-08-14T21:10:39/{obj_id}',
        data=params,
        token=upload_data_token,
    )
    assert status == 401

    status, data = api(
        'PATCH',
        f'sources_in_gcn/2019-08-14T21:10:39/{obj_id}',
        data=params,
        token=super_admin_token,
    )
    assert status == 200

    params = {
        "sourcesIdList": obj_id,
    }
    status, data = api(
        'GET',
        'sources_in_gcn/2019-08-14T21:10:39',
        params=params,
        token=upload_data_token,
    )
    assert status == 200
    data = data["data"]
    assert len(data) == 1
    assert data[0]["obj_id"] == obj_id
    assert data[0]["dateobs"] == "2019-08-14T21:10:39"
    assert data[0]["confirmed"] is False

    # verify that no gcns are associated to source

    # find no gcns associated to source
    status, data = api(
        'GET',
        f"associated_gcns/{obj_id}",
        token=upload_data_token,
    )
    assert status == 200
    data = data["data"]
    assert len(data['gcns']) == 0

    # mark source as unknow (delete it from the table)
    status, data = api(
        'DELETE',
        f'sources_in_gcn/2019-08-14T21:10:39/{obj_id}',
        token=upload_data_token,
    )
    assert status == 401

    status, data = api(
        'DELETE',
        f'sources_in_gcn/2019-08-14T21:10:39/{obj_id}',
        token=super_admin_token,
    )
    assert status == 200

    params = {
        "sourcesIdList": obj_id,
    }
    status, data = api(
        'GET',
        'sources_in_gcn/2019-08-14T21:10:39',
        params=params,
        token=upload_data_token,
    )
    assert status == 200
    data = data["data"]
    assert len(data) == 0


def test_gcn_from_polygon(super_admin_token, view_only_token):

    localization_name = str(uuid.uuid4())
    dateobs = '2022-09-03T14:44:12'
    polygon = [(30.0, 60.0), (40.0, 60.0), (40.0, 70.0), (30.0, 70.0)]
    tags = ['IPN', 'GRB']
    skymap = {'polygon': polygon, 'localization_name': localization_name}

    event_data = {'dateobs': dateobs, 'skymap': skymap, 'tags': tags}

    status, data = api('POST', 'gcn_event', data=event_data, token=super_admin_token)
    assert status == 200
    assert data['status'] == 'success'

    dateobs = "2022-09-03 14:44:12"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)
    assert status == 200
    data = data["data"]
    assert data["dateobs"] == "2022-09-03T14:44:12"
    assert 'IPN' in data["tags"]


def test_gcn_Swift(super_admin_token, view_only_token):

    datafile = f'{os.path.dirname(__file__)}/../data/SWIFT_1125809-092.xml'
    with open(datafile, 'rb') as fid:
        payload = fid.read()
    event_data_1 = {'xml': payload}

    datafile = f'{os.path.dirname(__file__)}/../data/SWIFT_1125809-104.xml'
    with open(datafile, 'rb') as fid:
        payload = fid.read()
    event_data_2 = {'xml': payload}

    dateobs = "2022-09-30 11:11:52"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)

    if status == 404:
        status, data = api(
            'POST', 'gcn_event', data=event_data_1, token=super_admin_token
        )
        assert status in [200, 400]
        assert data['status'] == 'success'

        status, data = api(
            'POST', 'gcn_event', data=event_data_2, token=super_admin_token
        )
        assert status == 200
        assert data['status'] == 'success'

    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)
    assert status == 200
    data = data["data"]
    assert data["dateobs"] == "2022-09-30T11:11:52"
    assert any(
        [
            loc['localization_name'] == '64.71490_13.35000_0.00130'
            for loc in data["localizations"]
        ]
    )
    assert any(
        [
            loc['localization_name'] == '64.73730_13.35170_0.05000'
            for loc in data["localizations"]
        ]
    )


def test_gcn_tach(
    super_admin_token,
    view_only_token,
):

    datafile = f'{os.path.dirname(__file__)}/../data/GRB180116A_Fermi_GBM_Gnd_Pos.xml'
    with open(datafile, 'rb') as fid:
        payload = fid.read()
    event_data = {'xml': payload}

    dateobs = "2018-01-16T00:36:53"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)

    if status == 404:
        status, data = api(
            'POST', 'gcn_event', data=event_data, token=super_admin_token
        )
        assert status == 200
        assert data['status'] == 'success'

    for n_times in range(26):
        status, data = api('GET', f"gcn_event/{dateobs}", token=super_admin_token)
        if data['status'] == 'success':
            break
        time.sleep(2)
    assert n_times < 25

    data = data['data']
    assert len(data['aliases']) == 0

    status, data = api('POST', f'gcn_event/{dateobs}/tach', token=view_only_token)
    assert status == 401

    status, data = api('POST', f'gcn_event/{dateobs}/tach', token=super_admin_token)
    assert status == 200
    assert data['status'] == 'success'

    for n_times in range(30):
        status, data = api('GET', f"gcn_event/{dateobs}", token=super_admin_token)
        if data['status'] == 'success':
            if len(data['data']['aliases']) > 0:
                aliases = data['data']['aliases']
                break
            time.sleep(1)

    assert n_times < 29
    assert len(aliases) == 1
    assert 'GRB180116A' in aliases

    status, data = api('GET', f"gcn_event/{dateobs}/tach", token=super_admin_token)

    assert status == 200
    assert data['status'] == 'success'
    data = data['data']
    assert len(data['aliases']) == 1
    assert len(data['circulars']) == 3
    assert data['tach_id'] is not None


def test_download_localization(super_admin_token, view_only_token):

    datafile = f'{os.path.dirname(__file__)}/../../../data/GW190814.xml'
    with open(datafile, 'rb') as fid:
        payload = fid.read()
    event_data = {'xml': payload}

    dateobs = "2019-08-14T21:10:39"
    status, data = api('GET', f'gcn_event/{dateobs}', token=super_admin_token)

    if status == 404:
        status, data = api(
            'POST', 'gcn_event', data=event_data, token=super_admin_token
        )
        assert status == 200
        assert data['status'] == 'success'

    # wait for event to load
    for n_times in range(26):
        status, data = api('GET', f"gcn_event/{dateobs}", token=super_admin_token)
        if data['status'] == 'success':
            break
        time.sleep(2)
    assert n_times < 25

    skymap = 'LALInference.v1.fits.gz'
    assert data["data"]["dateobs"] == dateobs
    assert any(
        [loc['localization_name'] == skymap for loc in data["data"]["localizations"]]
    )

    status, data = api(
        'GET',
        f'localization/{dateobs}/name/{skymap}/download',
        token=super_admin_token,
    )
    assert status == 200
