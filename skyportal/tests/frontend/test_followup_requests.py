import uuid
import pytest
import requests
from selenium.webdriver.common.action_chains import ActionChains
from baselayer.app.env import load_env
from skyportal.tests import api
import glob
import os


env, cfg = load_env()
endpoint = cfg['app.sedm_endpoint']

sedm_isonline = False
try:
    requests.get(endpoint, timeout=5)
except requests.exceptions.ConnectTimeout:
    pass
else:
    sedm_isonline = True


def add_telescope_and_instrument(instrument_name, token):
    status, data = api("GET", f"instrument?name={instrument_name}", token=token)
    if len(data["data"]) == 1:
        return data["data"][0]

    telescope_name = str(uuid.uuid4())
    status, data = api(
        "POST",
        "telescope",
        data={
            "name": telescope_name,
            "nickname": telescope_name,
            "lat": 0.0,
            "lon": 0.0,
            "elevation": 0.0,
            "diameter": 10.0,
            "robotic": True,
        },
        token=token,
    )
    assert status == 200
    assert data["status"] == "success"
    telescope_id = data["data"]["id"]

    status, data = api(
        "POST",
        "instrument",
        data={
            "name": instrument_name,
            "type": "imager",
            "band": "Optical",
            "telescope_id": telescope_id,
            "filters": ["ztfg"],
            "api_classname": f"{instrument_name.upper()}API",
        },
        token=token,
    )
    assert status == 200
    assert data["status"] == "success"
    return data["data"]


def add_allocation_sedm(instrument_id, group_id, token):
    status, data = api(
        "POST",
        "allocation",
        data={
            "group_id": group_id,
            "instrument_id": instrument_id,
            "hours_allocated": 100,
            "pi": "Ed Hubble",
        },
        token=token,
    )
    assert status == 200
    assert data["status"] == "success"
    return data["data"]


def add_allocation_lt(instrument_id, group_id, token):
    status, data = api(
        "POST",
        "allocation",
        data={
            "group_id": group_id,
            "instrument_id": instrument_id,
            "hours_allocated": 100,
            "pi": "Ed Hubble",
            "altdata": '{"username": "fritz_bot", "password": "fX5uxZTDy3", "LT_proposalID": "GrowthTest"}',
        },
        token=token,
    )
    assert status == 200
    assert data["status"] == "success"
    return data["data"]


def add_allocation_lco(instrument_id, group_id, token):
    status, data = api(
        "POST",
        "allocation",
        data={
            "group_id": group_id,
            "instrument_id": instrument_id,
            "hours_allocated": 100,
            "pi": "Ed Hubble",
            "altdata": '{"API_TOKEN": "854c32f01d6afba87446fd86f0d95c5c6c8de0a9", "PROPOSAL_ID": "NOAO2020B-005"}',
        },
        token=token,
    )
    assert status == 200
    assert data["status"] == "success"
    return data["data"]


def add_allocation_ztf(instrument_id, group_id, token):
    status, data = api(
        "POST",
        "allocation",
        data={
            "group_id": group_id,
            "instrument_id": instrument_id,
            "hours_allocated": 100,
            "pi": "Ed Hubble",
        },
        token=token,
    )
    assert status == 200
    assert data["status"] == "success"
    return data["data"]


def add_followup_request_using_frontend_and_verify_ZTF(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    """Adds a new followup request and makes sure it renders properly."""
    idata = add_telescope_and_instrument("ZTF", super_admin_token)
    add_allocation_sedm(idata['id'], public_group.id, super_admin_token)

    driver.get(f"/become_user/{super_admin_user.id}")

    driver.get(f"/source/{public_source.id}")
    # wait for the plots to load
    driver.wait_for_xpath('//div[@class="bk-root"]//span[text()="Flux"]', timeout=20)
    # this waits for the spectroscopy plot by looking for the element Mg
    driver.wait_for_xpath('//div[@class="bk-root"]//label[text()="Mg"]', timeout=20)

    submit_button_xpath = '//form[@class="rjsf"]//button[@type="submit"]'
    driver.wait_for_xpath(submit_button_xpath)

    select_box = driver.find_element_by_id(
        "mui-component-select-followupRequestAllocationSelect"
    )
    select_box.click()

    driver.wait_for_xpath('//li[@data-value="1"]')
    for ii in range(1, 100):
        allocation = driver.wait_for_xpath('//li[@data-value="%d"]' % ii)
        if "ZTF" in allocation.text:
            allocation.click()
            break

    driver.click_xpath(submit_button_xpath)

    driver.wait_for_xpath(
        f'//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "GRB")]'
    )
    driver.wait_for_xpath(
        f'''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'''
    )
    driver.wait_for_xpath(
        f'''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "g,r,i")]'''
    )
    driver.wait_for_xpath(
        f'''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


def add_followup_request_using_frontend_and_verify_SEDM(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    """Adds a new followup request and makes sure it renders properly."""
    idata = add_telescope_and_instrument("SEDM", super_admin_token)
    add_allocation_sedm(idata['id'], public_group.id, super_admin_token)

    driver.get(f"/become_user/{super_admin_user.id}")

    driver.get(f"/source/{public_source.id}")
    # wait for the plots to load
    driver.wait_for_xpath('//div[@class="bk-root"]//span[text()="Flux"]', timeout=20)
    # this waits for the spectroscopy plot by looking for the element Mg
    driver.wait_for_xpath('//div[@class="bk-root"]//label[text()="Mg"]', timeout=20)

    submit_button_xpath = '//form[@class="rjsf"]//button[@type="submit"]'
    driver.wait_for_xpath(submit_button_xpath)

    select_box = driver.find_element_by_id(
        "mui-component-select-followupRequestAllocationSelect"
    )
    select_box.click()

    driver.wait_for_xpath('//li[@data-value="1"]')
    for ii in range(1, 100):
        allocation = driver.wait_for_xpath('//li[@data-value="%d"]' % ii)
        if "SEDM" in allocation.text:
            allocation.click()
            break

    # mode select
    driver.click_xpath('//*[@id="root_observation_type"]')

    # mix n match option
    driver.click_xpath('''//li[@data-value="Mix 'n Match"]''')

    # u band option
    driver.click_xpath(
        '//input[@id="root_observation_choices_0"]', wait_clickable=False
    )

    # ifu option
    driver.click_xpath(
        '//input[@id="root_observation_choices_4"]', wait_clickable=False
    )
    driver.click_xpath(submit_button_xpath)

    driver.wait_for_xpath(
        f'//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "Mix \'n Match")]'
    )
    driver.wait_for_xpath(
        f'''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "u,IFU")]'''
    )
    driver.wait_for_xpath(
        f'''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "1")]'''
    )
    driver.wait_for_xpath(
        f'''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


def add_followup_request_using_frontend_and_verify_Floyds(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    """Adds a new followup request and makes sure it renders properly."""

    idata = add_telescope_and_instrument("Floyds", super_admin_token)
    add_allocation_lco(idata['id'], public_group.id, super_admin_token)

    driver.get(f"/become_user/{super_admin_user.id}")

    driver.get(f"/source/{public_source.id}")
    # wait for the plots to load
    driver.wait_for_xpath('//div[@class="bk-root"]//span[text()="Flux"]', timeout=20)
    # this waits for the spectroscopy plot by looking for the element Mg
    driver.wait_for_xpath('//div[@class="bk-root"]//label[text()="Mg"]', timeout=20)

    submit_button_xpath = '//form[@class="rjsf"]//button[@type="submit"]'
    driver.wait_for_xpath(submit_button_xpath)

    select_box = driver.find_element_by_id(
        "mui-component-select-followupRequestAllocationSelect"
    )
    select_box.click()

    driver.wait_for_xpath('//li[@data-value="1"]')
    for ii in range(1, 100):
        allocation = driver.wait_for_xpath('//li[@data-value="%d"]' % ii)
        if "Floyds" in allocation.text:
            allocation.click()
            break

    driver.click_xpath(submit_button_xpath)

    driver.wait_for_xpath(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "30")]'''
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


def add_followup_request_using_frontend_and_verify_MUSCAT(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    """Adds a new followup request and makes sure it renders properly."""

    idata = add_telescope_and_instrument("MUSCAT", super_admin_token)
    add_allocation_lco(idata['id'], public_group.id, super_admin_token)

    driver.get(f"/become_user/{super_admin_user.id}")

    driver.get(f"/source/{public_source.id}")
    # wait for the plots to load
    driver.wait_for_xpath('//div[@class="bk-root"]//span[text()="Flux"]', timeout=20)
    # this waits for the spectroscopy plot by looking for the element Mg
    driver.wait_for_xpath('//div[@class="bk-root"]//label[text()="Mg"]', timeout=20)

    submit_button_xpath = '//form[@class="rjsf"]//button[@type="submit"]'
    driver.wait_for_xpath(submit_button_xpath)

    select_box = driver.find_element_by_id(
        "mui-component-select-followupRequestAllocationSelect"
    )
    select_box.click()

    driver.wait_for_xpath('//li[@data-value="1"]')
    for ii in range(1, 100):
        allocation = driver.wait_for_xpath('//li[@data-value="%d"]' % ii)
        if "MUSCAT" in allocation.text:
            allocation.click()
            break

    driver.click_xpath(submit_button_xpath)

    driver.wait_for_xpath(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "30")]'''
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


def add_followup_request_using_frontend_and_verify_Spectral(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    """Adds a new followup request and makes sure it renders properly."""

    idata = add_telescope_and_instrument("Spectral", super_admin_token)
    add_allocation_lco(idata['id'], public_group.id, super_admin_token)

    driver.get(f"/become_user/{super_admin_user.id}")

    driver.get(f"/source/{public_source.id}")
    # wait for the plots to load
    driver.wait_for_xpath('//div[@class="bk-root"]//span[text()="Flux"]', timeout=20)
    # this waits for the spectroscopy plot by looking for the element Mg
    driver.wait_for_xpath('//div[@class="bk-root"]//label[text()="Mg"]', timeout=20)

    submit_button_xpath = '//form[@class="rjsf"]//button[@type="submit"]'
    driver.wait_for_xpath(submit_button_xpath)

    select_box = driver.find_element_by_id(
        "mui-component-select-followupRequestAllocationSelect"
    )
    select_box.click()

    driver.wait_for_xpath('//li[@data-value="1"]')
    for ii in range(1, 100):
        allocation = driver.wait_for_xpath('//li[@data-value="%d"]' % ii)
        if "Spectral" in allocation.text:
            allocation.click()
            break

    # gp band option
    driver.click_xpath(
        '//input[@id="root_observation_choices_0"]', wait_clickable=False
    )

    # Y option
    driver.click_xpath(
        '//input[@id="root_observation_choices_4"]', wait_clickable=False
    )

    driver.click_xpath(submit_button_xpath)

    driver.wait_for_xpath(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "gp,Y")]'''
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


def add_followup_request_using_frontend_and_verify_Sinistro(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    """Adds a new followup request and makes sure it renders properly."""

    idata = add_telescope_and_instrument("Sinistro", super_admin_token)
    add_allocation_lco(idata['id'], public_group.id, super_admin_token)

    driver.get(f"/become_user/{super_admin_user.id}")

    driver.get(f"/source/{public_source.id}")
    # wait for the plots to load
    driver.wait_for_xpath('//div[@class="bk-root"]//span[text()="Flux"]', timeout=20)
    # this waits for the spectroscopy plot by looking for the element Mg
    driver.wait_for_xpath('//div[@class="bk-root"]//label[text()="Mg"]', timeout=20)

    submit_button_xpath = '//form[@class="rjsf"]//button[@type="submit"]'
    driver.wait_for_xpath(submit_button_xpath)

    select_box = driver.find_element_by_id(
        "mui-component-select-followupRequestAllocationSelect"
    )
    select_box.click()

    driver.wait_for_xpath('//li[@data-value="1"]')
    for ii in range(1, 100):
        allocation = driver.wait_for_xpath('//li[@data-value="%d"]' % ii)
        if "Sinistro" in allocation.text:
            allocation.click()
            break

    # gp band option
    driver.click_xpath(
        '//input[@id="root_observation_choices_0"]', wait_clickable=False
    )

    # Y option
    driver.click_xpath(
        '//input[@id="root_observation_choices_4"]', wait_clickable=False
    )

    driver.click_xpath(submit_button_xpath)

    driver.wait_for_xpath(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "gp,Y")]'''
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


def add_followup_request_using_frontend_and_verify_SPRAT(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    """Adds a new followup request and makes sure it renders properly."""

    idata = add_telescope_and_instrument("SPRAT", super_admin_token)
    add_allocation_lt(idata['id'], public_group.id, super_admin_token)

    driver.get(f"/become_user/{super_admin_user.id}")

    driver.get(f"/source/{public_source.id}")
    # wait for the plots to load
    driver.wait_for_xpath('//div[@class="bk-root"]//span[text()="Flux"]', timeout=20)
    # this waits for the spectroscopy plot by looking for the element Mg
    driver.wait_for_xpath('//div[@class="bk-root"]//label[text()="Mg"]', timeout=20)

    submit_button_xpath = '//form[@class="rjsf"]//button[@type="submit"]'
    driver.wait_for_xpath(submit_button_xpath)

    select_box = driver.find_element_by_id(
        "mui-component-select-followupRequestAllocationSelect"
    )
    select_box.click()

    driver.wait_for_xpath('//li[@data-value="1"]')
    for ii in range(1, 100):
        allocation = driver.wait_for_xpath('//li[@data-value="%d"]' % ii)
        if "SPRAT" in allocation.text:
            allocation.click()
            break

    photometric_option = driver.wait_for_xpath('//input[@id="root_photometric"]')
    driver.scroll_to_element_and_click(photometric_option)

    driver.click_xpath(submit_button_xpath)

    driver.wait_for_xpath(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "blue")]'''
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


def add_followup_request_using_frontend_and_verify_IOI(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    """Adds a new followup request and makes sure it renders properly."""

    idata = add_telescope_and_instrument("IOI", super_admin_token)
    add_allocation_lt(idata['id'], public_group.id, super_admin_token)

    driver.get(f"/become_user/{super_admin_user.id}")

    driver.get(f"/source/{public_source.id}")
    # wait for the plots to load
    driver.wait_for_xpath('//div[@class="bk-root"]//span[text()="Flux"]', timeout=20)
    # this waits for the spectroscopy plot by looking for the element Mg
    driver.wait_for_xpath('//div[@class="bk-root"]//label[text()="Mg"]', timeout=20)

    submit_button_xpath = '//form[@class="rjsf"]//button[@type="submit"]'
    driver.wait_for_xpath(submit_button_xpath)

    select_box = driver.find_element_by_id(
        "mui-component-select-followupRequestAllocationSelect"
    )
    select_box.click()

    driver.wait_for_xpath('//li[@data-value="1"]')
    for ii in range(1, 100):
        allocation = driver.wait_for_xpath('//li[@data-value="%d"]' % ii)
        if "IOI" in allocation.text:
            allocation.click()
            break

    # H band option
    driver.click_xpath(
        '//input[@id="root_observation_choices_0"]', wait_clickable=False
    )

    photometric_option = driver.wait_for_xpath('//input[@id="root_photometric"]')
    driver.scroll_to_element_and_click(photometric_option)

    driver.click_xpath(submit_button_xpath)

    driver.wait_for_xpath(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "H")]'''
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


def add_followup_request_using_frontend_and_verify_IOO(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    """Adds a new followup request and makes sure it renders properly."""

    idata = add_telescope_and_instrument("IOO", super_admin_token)
    add_allocation_lt(idata['id'], public_group.id, super_admin_token)

    driver.get(f"/become_user/{super_admin_user.id}")

    driver.get(f"/source/{public_source.id}")
    # wait for the plots to load
    driver.wait_for_xpath('//div[@class="bk-root"]//span[text()="Flux"]', timeout=20)
    # this waits for the spectroscopy plot by looking for the element Mg
    driver.wait_for_xpath('//div[@class="bk-root"]//label[text()="Mg"]', timeout=20)

    submit_button_xpath = '//form[@class="rjsf"]//button[@type="submit"]'
    driver.wait_for_xpath(submit_button_xpath)

    select_box = driver.find_element_by_id(
        "mui-component-select-followupRequestAllocationSelect"
    )
    select_box.click()

    driver.wait_for_xpath('//li[@data-value="1"]')
    for ii in range(1, 100):
        allocation = driver.wait_for_xpath('//li[@data-value="%d"]' % ii)
        if "IOO" in allocation.text:
            allocation.click()
            break

    # u band option
    driver.click_xpath(
        '//input[@id="root_observation_choices_0"]', wait_clickable=False
    )

    # z option
    driver.click_xpath(
        '//input[@id="root_observation_choices_4"]', wait_clickable=False
    )

    photometric_option = driver.wait_for_xpath('//input[@id="root_photometric"]')
    driver.scroll_to_element_and_click(photometric_option)

    driver.click_xpath(submit_button_xpath)

    driver.wait_for_xpath(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "u,z")]'''
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


@pytest.mark.flaky(reruns=2)
@pytest.mark.skipif(not sedm_isonline, reason="SEDM server down")
def test_submit_new_followup_request_SEDM(
    driver, super_admin_user, public_source, super_admin_token, public_group
):

    add_followup_request_using_frontend_and_verify_SEDM(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )


@pytest.mark.flaky(reruns=2)
# @pytest.mark.skipif(not sedm_isonline, reason="SEDM server down")
def test_submit_new_followup_request_ZTF(
    driver, super_admin_user, public_source, super_admin_token, public_group
):

    add_followup_request_using_frontend_and_verify_ZTF(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )


@pytest.mark.flaky(reruns=2)
def test_submit_new_followup_request_IOO(
    driver, super_admin_user, public_source, super_admin_token, public_group
):

    add_followup_request_using_frontend_and_verify_IOO(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )


@pytest.mark.flaky(reruns=2)
def test_submit_new_followup_request_IOI(
    driver, super_admin_user, public_source, super_admin_token, public_group
):

    add_followup_request_using_frontend_and_verify_IOO(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )


@pytest.mark.flaky(reruns=2)
def test_submit_new_followup_request_SPRAT(
    driver, super_admin_user, public_source, super_admin_token, public_group
):

    add_followup_request_using_frontend_and_verify_SPRAT(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )


@pytest.mark.flaky(reruns=2)
def test_submit_new_followup_request_Sinistro(
    driver, super_admin_user, public_source, super_admin_token, public_group
):

    add_followup_request_using_frontend_and_verify_Sinistro(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )


@pytest.mark.flaky(reruns=2)
def test_submit_new_followup_request_Spectral(
    driver, super_admin_user, public_source, super_admin_token, public_group
):

    add_followup_request_using_frontend_and_verify_Spectral(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )


@pytest.mark.flaky(reruns=2)
def test_submit_new_followup_request_MUSCAT(
    driver, super_admin_user, public_source, super_admin_token, public_group
):

    add_followup_request_using_frontend_and_verify_MUSCAT(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )


@pytest.mark.flaky(reruns=2)
def test_submit_new_followup_request_Floyds(
    driver, super_admin_user, public_source, super_admin_token, public_group
):

    add_followup_request_using_frontend_and_verify_Floyds(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )


@pytest.mark.flaky(reruns=2)
@pytest.mark.skipif(not sedm_isonline, reason="SEDM server down")
def test_edit_existing_followup_request(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    add_followup_request_using_frontend_and_verify_SEDM(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )
    edit_button = driver.wait_for_xpath(f'//button[contains(@name, "editRequest")]')
    driver.scroll_to_element_and_click(edit_button)
    mode_select = driver.wait_for_xpath(
        '//div[@role="dialog"]//div[@id="root_observation_type"]'
    )
    ActionChains(driver).move_to_element(mode_select).pause(1).click().perform()

    mix_n_match_option = driver.wait_for_xpath('''//li[@data-value="IFU"]''')
    driver.scroll_to_element_and_click(mix_n_match_option)

    submit_button = driver.wait_for_xpath(
        '//form[@class="rjsf"]//button[@type="submit"]'
    )

    driver.scroll_to_element_and_click(submit_button)

    driver.wait_for_xpath(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "IFU")]'
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "1")]'''
    )
    driver.wait_for_xpath(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


# @pytest.mark.flaky(reruns=2)
def test_delete_followup_request_ZTF(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    add_followup_request_using_frontend_and_verify_ZTF(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )
    delete_button = driver.wait_for_xpath(f'//button[contains(@name, "deleteRequest")]')
    driver.scroll_to_element_and_click(delete_button)

    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "GRB")]'''
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'''
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


@pytest.mark.flaky(reruns=2)
@pytest.mark.skipif(not sedm_isonline, reason='SEDM server down')
def test_delete_followup_request_SEDM(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    add_followup_request_using_frontend_and_verify_SEDM(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )
    delete_button = driver.wait_for_xpath(f'//button[contains(@name, "deleteRequest")]')
    driver.scroll_to_element_and_click(delete_button)

    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "u,IFU")]'''
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "1")]'''
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


@pytest.mark.flaky(reruns=2)
def test_delete_followup_request_IOO(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    add_followup_request_using_frontend_and_verify_IOO(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )

    delete_button = driver.wait_for_xpath(f'//button[contains(@name, "deleteRequest")]')
    driver.scroll_to_element(delete_button)
    driver.execute_script("window.scrollTo(200, document.body.scrollHeight);")
    ActionChains(driver).pause(1).click().perform()
    driver.refresh()

    driver.wait_for_xpath_to_disappear(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "u,z")]'''
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


@pytest.mark.flaky(reruns=2)
def test_delete_followup_request_IOI(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    add_followup_request_using_frontend_and_verify_IOI(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )

    delete_button = driver.wait_for_xpath(f'//button[contains(@name, "deleteRequest")]')
    driver.scroll_to_element(delete_button)
    driver.execute_script("window.scrollTo(200, document.body.scrollHeight);")
    ActionChains(driver).pause(1).click().perform()
    driver.refresh()

    driver.wait_for_xpath_to_disappear(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "H")]'''
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


# @pytest.mark.flaky(reruns=2)
def test_delete_followup_request_SPRAT(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    add_followup_request_using_frontend_and_verify_SPRAT(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )

    delete_button = driver.wait_for_xpath(f'//button[contains(@name, "deleteRequest")]')
    driver.scroll_to_element(delete_button)
    driver.execute_script("window.scrollTo(200, document.body.scrollHeight);")
    ActionChains(driver).pause(1).click().perform()
    driver.refresh()

    driver.wait_for_xpath_to_disappear(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "blue")]'''
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


@pytest.mark.flaky(reruns=2)
def test_delete_followup_request_Sinistro(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    add_followup_request_using_frontend_and_verify_Sinistro(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )

    delete_button = driver.wait_for_xpath(f'//button[contains(@name, "deleteRequest")]')
    driver.scroll_to_element(delete_button)
    driver.execute_script("window.scrollTo(200, document.body.scrollHeight);")
    ActionChains(driver).pause(1).click().perform()
    driver.refresh()

    driver.wait_for_xpath_to_disappear(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "gp,Y")]'''
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


@pytest.mark.flaky(reruns=2)
def test_delete_followup_request_Spectral(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    add_followup_request_using_frontend_and_verify_Spectral(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )

    delete_button = driver.wait_for_xpath(f'//button[contains(@name, "deleteRequest")]')
    driver.scroll_to_element(delete_button)
    driver.execute_script("window.scrollTo(200, document.body.scrollHeight);")
    ActionChains(driver).pause(1).click().perform()
    driver.refresh()

    driver.wait_for_xpath_to_disappear(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "gp,Y")]'''
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


@pytest.mark.flaky(reruns=2)
def test_delete_followup_request_MUSCAT(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    add_followup_request_using_frontend_and_verify_MUSCAT(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )

    delete_button = driver.wait_for_xpath(f'//button[contains(@name, "deleteRequest")]')
    driver.scroll_to_element(delete_button)
    driver.execute_script("window.scrollTo(200, document.body.scrollHeight);")
    ActionChains(driver).pause(1).click().perform()
    driver.refresh()

    driver.wait_for_xpath_to_disappear(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "30")]'''
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


@pytest.mark.flaky(reruns=2)
def test_delete_followup_request_Floyds(
    driver, super_admin_user, public_source, super_admin_token, public_group
):
    add_followup_request_using_frontend_and_verify_Floyds(
        driver, super_admin_user, public_source, super_admin_token, public_group
    )

    delete_button = driver.wait_for_xpath(f'//button[contains(@name, "deleteRequest")]')
    driver.scroll_to_element(delete_button)
    driver.execute_script("window.scrollTo(200, document.body.scrollHeight);")
    ActionChains(driver).pause(1).click().perform()
    driver.refresh()

    driver.wait_for_xpath_to_disappear(
        '//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "300")]'
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "30")]'''
    )
    driver.wait_for_xpath_to_disappear(
        '''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )


@pytest.mark.flaky(reruns=2)
@pytest.mark.skipif(not sedm_isonline, reason="SEDM server down")
def test_submit_new_followup_request_two_groups(
    driver,
    super_admin_user,
    public_source_two_groups,
    super_admin_token,
    public_group,
    public_group2,
    view_only_token_group2,
    user_group2,
):

    idata = add_telescope_and_instrument("SEDM", super_admin_token)
    add_allocation_sedm(idata['id'], public_group.id, super_admin_token)

    driver.get(f"/become_user/{super_admin_user.id}")

    driver.get(f"/source/{public_source_two_groups.id}")
    # wait for the plots to load
    driver.wait_for_xpath('//div[@class="bk-root"]//span[text()="Flux"]', timeout=20)
    # this waits for the spectroscopy plot by looking for the element Mg
    driver.wait_for_xpath('//div[@class="bk-root"]//label[text()="Mg"]', timeout=20)

    submit_button_xpath = '//form[@class="rjsf"]//button[@type="submit"]'
    driver.wait_for_xpath(submit_button_xpath)

    select_box = driver.find_element_by_id(
        "mui-component-select-followupRequestAllocationSelect"
    )
    select_box.click()

    driver.wait_for_xpath('//li[@data-value="1"]')
    for ii in range(1, 100):
        allocation = driver.wait_for_xpath('//li[@data-value="%d"]' % ii)
        if "SEDM" in allocation.text:
            allocation.click()
            break

    group_select = driver.wait_for_xpath('//*[@id="selectGroups"]')
    driver.scroll_to_element_and_click(group_select)

    group1 = f'//*[@data-testid="group_{public_group.id}"]'
    driver.click_xpath(group1, scroll_parent=True)

    group2 = f'//*[@data-testid="group_{public_group2.id}"]'
    driver.click_xpath(group2, scroll_parent=True)

    # Click somewhere definitely outside the select list to remove focus from select
    header = driver.wait_for_xpath("//header")
    ActionChains(driver).move_to_element(header).click().pause(0.1).perform()

    # mode select
    driver.click_xpath('//*[@id="root_observation_type"]')

    # mix n match option
    driver.click_xpath('''//li[@data-value="Mix 'n Match"]''')

    # u band option
    driver.click_xpath(
        '//input[@id="root_observation_choices_0"]', wait_clickable=False
    )

    # ifu option
    driver.click_xpath(
        '//input[@id="root_observation_choices_4"]', wait_clickable=False
    )
    driver.click_xpath(submit_button_xpath)

    driver.wait_for_xpath(
        f'//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "Mix \'n Match")]'
    )
    driver.wait_for_xpath(
        f'''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "u,IFU")]'''
    )
    driver.wait_for_xpath(
        f'''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "1")]'''
    )
    driver.wait_for_xpath(
        f'''//table[contains(@data-testid, "followupRequestTable")]//td[contains(., "submitted")]'''
    )

    filename = glob.glob(
        f'{os.path.dirname(__file__)}/../data/ZTF20abwdwoa_20200902_P60_v1.ascii'
    )[0]
    with open(filename, 'r') as f:
        ascii = f.read()

    status, data = api(
        'GET', f'sources/{public_source_two_groups.id}', token=super_admin_token
    )

    assert status == 200
    assert data['status'] == 'success'

    status, data = api(
        "POST",
        'spectrum/ascii',
        data={
            'obj_id': str(public_source_two_groups.id),
            'observed_at': '2020-01-01T00:00:00',
            'instrument_id': idata['id'],
            'fluxerr_column': 2,
            'followup_request_id': data['data']['followup_requests'][0]['id'],
            'ascii': ascii,
            'filename': os.path.basename(filename),
        },
        token=super_admin_token,
    )

    assert status == 200
    assert data['status'] == 'success'

    sid = data['data']['id']
    status, data = api('GET', f'spectrum/{sid}', token=view_only_token_group2)

    assert status == 200
    assert data['status'] == 'success'
