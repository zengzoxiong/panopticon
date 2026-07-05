import { useContext } from "react";
import { useTranslation } from "react-i18next";
import { Typography } from "@mui/material";
import { GameStatusContext } from "@/gui/contextProviders/contexts/GameStatusContext";

const currentActionContextDisplayStyle = {
  textAlign: "left",
  padding: "2px",
  paddingLeft: "1.5em",
  color: "#4F4F4F",
  fontSize: "12px",
  fontStyle: "normal",
  fontWeight: 400,
};

export default function CurrentActionContextDisplay() {
  const { t } = useTranslation();
  const CurrentGameStatusFromContext = useContext(GameStatusContext);

  return (
    <Typography
      variant="body2"
      component="p"
      sx={currentActionContextDisplayStyle}
    >
      {t(CurrentGameStatusFromContext)}
    </Typography>
  );
}
