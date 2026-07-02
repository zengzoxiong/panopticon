import { useAuth0 } from "@auth0/auth0-react";
import { Chip, Tooltip } from "@mui/material";
import React from "react";
import { useTranslation } from 'react-i18next';

const LogoutButton = () => {
  const { user, logout } = useAuth0();
  const { t } = useTranslation();

  return (
    <Tooltip title={t('toolbar.auth.loggedInAs') + (user ? user.name : "Unknown User")}>
      <Chip
        variant="outlined"
        onClick={() =>
          logout({ logoutParams: { returnTo: window.location.origin } })
        }
        label={t('toolbar.auth.logout')}
        sx={{
          marginRight: "1em",
        }}
      />
    </Tooltip>
  );
};

export default LogoutButton;
