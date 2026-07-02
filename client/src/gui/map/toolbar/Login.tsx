import { useAuth0 } from "@auth0/auth0-react";
import { Chip } from "@mui/material";
import React from "react";
import { useTranslation } from 'react-i18next';

const LoginButton = () => {
  const { loginWithRedirect } = useAuth0();
  const { t } = useTranslation();

  return (
    <Chip
      variant="outlined"
      onClick={() => loginWithRedirect()}
      label={t('toolbar.auth.login')}
      sx={{
        marginRight: "1em",
      }}
    />
  );
};

export default LoginButton;
