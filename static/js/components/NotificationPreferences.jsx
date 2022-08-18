import React, { useEffect, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useForm } from "react-hook-form";
import { makeStyles } from "@mui/styles";
import Button from "@mui/material/Button";
import { showNotification } from "baselayer/components/Notifications";

import FormGroup from "@mui/material/FormGroup";
import FormControlLabel from "@mui/material/FormControlLabel";
import Switch from "@mui/material/Switch";
import Tooltip from "@mui/material/Tooltip";
import HelpOutlineOutlinedIcon from "@mui/icons-material/HelpOutlineOutlined";

import UserPreferencesHeader from "./UserPreferencesHeader";
import ClassificationSelect from "./ClassificationSelect";
import GcnNoticeTypesSelect from "./GcnNoticeTypesSelect";
import GcnTagsSelect from "./GcnTagsSelect";
import NotificationSettingsSelect from "./NotificationSettingsSelect";
import * as profileActions from "../ducks/profile";

const useStyles = makeStyles((theme) => ({
  typography: {
    padding: theme.spacing(2),
  },
  pref: {
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    marginBottom: theme.spacing(2),
  },
  form: {
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
  },
  button: {
    height: "3rem",
    marginRight: theme.spacing(1),
  },
  form_group: {
    display: "flex",
    flexDirection: "row",
    justifyContent: "left",
    alignItems: "center",
    marginRight: theme.spacing(2),
  },
  tooltip: {
    fontSize: "1rem",
    maxWidth: "30rem",
  },
}));

const NotificationPreferences = () => {
  const classes = useStyles();
  const profile = useSelector((state) => state.profile.preferences);
  const dispatch = useDispatch();
  const { handleSubmit } = useForm();
  const [selectedClassifications, setSelectedClassifications] = useState(
    profile?.notifications?.sources?.classifications || []
  );

  const [selectedGcnNoticeTypes, setSelectedGcnNoticeTypes] = useState(
    profile?.notications?.gcn_events?.gcn_notice_types || []
  );

  const [selectedGcnTags, setSelectedGcnTags] = useState(
    profile?.notications?.gcn_events?.gcn_tags || []
  );

  useEffect(() => {
    setSelectedClassifications(
      profile?.notifications?.sources?.classifications || []
    );
    setSelectedGcnNoticeTypes(
      profile?.notifications?.gcn_events?.gcn_notice_types || []
    );
    setSelectedGcnTags(profile?.notifications?.gcn_events?.gcn_tags || []);
  }, [profile]);

  const prefToggled = (event) => {
    const prefs = {
      notifications: {},
    };
    if (
      event.target.name === "sources" ||
      event.target.name === "gcn_events" ||
      event.target.name === "mention" ||
      event.target.name === "favorite_sources" ||
      event.target.name === "facility_transactions"
    ) {
      prefs.notifications[event.target.name] = {
        active: event.target.checked,
      };
    } else if (event.target.name === "favorite_sources_new_comments") {
      prefs.notifications.favorite_sources = {
        new_comments: event.target.checked,
      };
    } else if (event.target.name === "favorite_sources_new_classifications") {
      prefs.notifications.favorite_sources = {
        new_classifications: event.target.checked,
      };
    } else if (event.target.name === "favorite_sources_new_spectra") {
      prefs.notifications.favorite_sources = {
        new_spectra: event.target.checked,
      };
    }

    dispatch(profileActions.updateUserPreferences(prefs));
  };

  const onSubmitSources = () => {
    const prefs = {
      notifications: {
        sources: {
          classifications: [...new Set(selectedClassifications)],
        },
      },
    };
    dispatch(profileActions.updateUserPreferences(prefs));
    setSelectedClassifications([...new Set(selectedClassifications)]);
    dispatch(showNotification("Sources classifications updated"));
  };

  const onSubmitGcns = () => {
    const prefs = {
      notifications: {
        gcn_events: {
          gcn_notice_types: [...new Set(selectedGcnNoticeTypes)],
          gcn_tags: [...new Set(selectedGcnTags)],
        },
      },
    };
    dispatch(profileActions.updateUserPreferences(prefs));
    setSelectedGcnNoticeTypes([...new Set(selectedGcnNoticeTypes)]);
    setSelectedGcnTags([...new Set(selectedGcnTags)]);
    dispatch(showNotification("Gcn notice types updated"));
  };

  return (
    <div>
      <UserPreferencesHeader
        title="Notifications Preferences"
        popupText="Enable these to receive notifications on: all sources, favorite sources, gcn events, facility transactions. For each of them, click on the bell to configure the notification settings: email, sms and/or slack"
      />
      <div className={classes.pref}>
        <FormGroup row className={classes.form_group}>
          <FormControlLabel
            control={
              <Switch
                checked={profile?.notifications?.sources?.active === true}
                name="sources"
                onChange={prefToggled}
              />
            }
            label="Sources"
          />
          <Tooltip
            title="This allows you to be notified for all sources, based on a certain criteria. For now, you can select classification(s) to be notified for, when added to any source."
            placement="right"
            classes={{ tooltip: classes.tooltip }}
          >
            <HelpOutlineOutlinedIcon />
          </Tooltip>
        </FormGroup>
        {profile?.notifications?.sources?.active === true && (
          <>
            <form onSubmit={handleSubmit(onSubmitSources)}>
              <div className={classes.form}>
                <ClassificationSelect
                  selectedClassifications={selectedClassifications}
                  setSelectedClassifications={setSelectedClassifications}
                />
                <Button
                  variant="contained"
                  type="submit"
                  data-testid="addShortcutButton"
                  className={classes.button}
                >
                  Update
                </Button>
              </div>
            </form>
            <NotificationSettingsSelect notificationResourceType="sources" />
          </>
        )}
      </div>
      <div className={classes.pref}>
        <FormGroup row className={classes.form_group}>
          <FormControlLabel
            control={
              <Switch
                checked={profile?.notifications?.gcn_events?.active === true}
                name="gcn_events"
                onChange={prefToggled}
              />
            }
            label="GCN Events"
          />
          <Tooltip
            title="This allows you to be notified for GCN events. You can select the notice types you want to be notified for."
            placement="right"
            classes={{ tooltip: classes.tooltip }}
          >
            <HelpOutlineOutlinedIcon />
          </Tooltip>
        </FormGroup>
        {profile?.notifications?.gcn_events?.active === true && (
          <>
            <form onSubmit={handleSubmit(onSubmitGcns)}>
              <div className={classes.form}>
                <GcnNoticeTypesSelect
                  selectedGcnNoticeTypes={selectedGcnNoticeTypes}
                  setSelectedGcnNoticeTypes={setSelectedGcnNoticeTypes}
                />
                <GcnTagsSelect
                  selectedGcnTags={selectedGcnTags}
                  setSelectedGcnTags={setSelectedGcnTags}
                />
                <Button
                  variant="contained"
                  type="submit"
                  data-testid="addShortcutButton"
                  className={classes.button}
                >
                  Update
                </Button>
              </div>
            </form>
            <NotificationSettingsSelect notificationResourceType="gcn_events" />
          </>
        )}
      </div>
      <div className={classes.pref}>
        <FormGroup row className={classes.form_group}>
          <FormControlLabel
            control={
              <Switch
                checked={
                  profile?.notifications?.facility_transactions?.active === true
                }
                name="facility_transactions"
                onChange={prefToggled}
              />
            }
            label="Facility Transactions"
          />
          <Tooltip
            title="This allows you to be notified for all facility transactions (followup requests, observation plans)."
            placement="right"
            classes={{ tooltip: classes.tooltip }}
          >
            <HelpOutlineOutlinedIcon />
          </Tooltip>
        </FormGroup>
        {profile?.notifications?.facility_transactions?.active === true && (
          <NotificationSettingsSelect notificationResourceType="facility_transactions" />
        )}
      </div>
      <div className={classes.pref}>
        <FormGroup row className={classes.form_group}>
          <FormControlLabel
            control={
              <Switch
                checked={
                  profile?.notifications?.favorite_sources?.active === true
                }
                name="favorite_sources"
                onChange={prefToggled}
              />
            }
            label="Favorite Sources"
          />
          <Tooltip
            title="This allows you to be notified when certain actions are performed by users on your favorite sources. You can select to be notified about new comments, new classifications and new spectra added to a favorite source."
            placement="right"
            classes={{ tooltip: classes.tooltip }}
          >
            <HelpOutlineOutlinedIcon />
          </Tooltip>
        </FormGroup>
        {profile?.notifications?.favorite_sources?.active === true && (
          <div className={classes.form}>
            <FormGroup row className={classes.form_group}>
              <FormControlLabel
                control={
                  <Switch
                    checked={
                      profile?.notifications?.favorite_sources?.new_comments ===
                      true
                    }
                    name="favorite_sources_new_comments"
                    onChange={prefToggled}
                  />
                }
                label="New Comments"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={
                      profile?.notifications?.favorite_sources?.new_spectra ===
                      true
                    }
                    name="favorite_sources_new_spectra"
                    onChange={prefToggled}
                  />
                }
                label="New Spectra"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={
                      profile?.notifications?.favorite_sources
                        ?.new_classifications === true
                    }
                    name="favorite_sources_new_classifications"
                    onChange={prefToggled}
                  />
                }
                label="New Classifications"
              />
            </FormGroup>
          </div>
        )}
        {profile?.notifications?.favorite_sources?.active === true && (
          <NotificationSettingsSelect notificationResourceType="favorite_sources" />
        )}
      </div>
      <div className={classes.pref}>
        <FormGroup row className={classes.form_group}>
          <FormControlLabel
            control={
              <Switch
                checked={profile?.notifications?.mention?.active === true}
                name="mention"
                onChange={prefToggled}
              />
            }
            label="@ Mentions"
          />
          <Tooltip
            title="On SkyPortal, you will always be notified when a user mentions you. If you activate this, it will simply allow you to specify in the settings if you want to also be notified by email, sms and/or slack."
            placement="right"
            classes={{ tooltip: classes.tooltip }}
          >
            <HelpOutlineOutlinedIcon />
          </Tooltip>
        </FormGroup>
        {profile?.notifications?.mention?.active === true && (
          <NotificationSettingsSelect notificationResourceType="mention" />
        )}
      </div>
    </div>
  );
};

export default NotificationPreferences;
