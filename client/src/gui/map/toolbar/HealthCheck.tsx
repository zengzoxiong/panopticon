import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import Chip from "@mui/material/Chip";
import Tooltip from "@mui/material/Tooltip";
import { Wifi, WifiOff, Computer } from "@mui/icons-material";

const TIMEOUT_MS = 30000;

interface HealthCheckProps {
  realtimeMode?: boolean;
  onToggleMode?: (realtimeMode: boolean) => void;
}

export default function HealthCheck(props: HealthCheckProps) {
  const { t } = useTranslation();
  const env = import.meta.env.VITE_ENV;
  const apiUrl = import.meta.env.VITE_API_SERVER_URL;

  const [status, setStatus] = useState("checking");

  useEffect(() => {
    if (!env || env === "standalone") return;
    let active = true;
    setStatus("checking");

    const timer = setTimeout(() => {
      if (active) setStatus("down");
    }, TIMEOUT_MS);

    fetch(`${apiUrl}/health`)
      .then((res) => {
        if (!active) return;
        clearTimeout(timer);
        setStatus(res.ok ? "connected" : "down");
      })
      .catch(() => {
        if (!active) return;
        clearTimeout(timer);
        setStatus("down");
      });

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [apiUrl]);

  const handleClick = () => {
    if (props.onToggleMode) {
      props.onToggleMode(!props.realtimeMode);
    }
  };

  // 实时遥测模式下的显示
  if (props.realtimeMode !== undefined) {
    return (
      <Tooltip
        title={
          props.realtimeMode
            ? t("health.realtimeMode", "实时遥测模式 - 点击切换到独立模式")
            : t("health.standaloneMode", "独立模式 - 点击切换到实时遥测模式")
        }
      >
        <Chip
          icon={props.realtimeMode ? <Wifi /> : <Computer />}
          label={
            props.realtimeMode
              ? t("health.realtimeMode", "实时遥测")
              : t("health.standaloneMode", "独立模式")
          }
          onClick={handleClick}
          color={props.realtimeMode ? "primary" : "default"}
          variant={props.realtimeMode ? "filled" : "outlined"}
          size="small"
          sx={{ cursor: "pointer" }}
        />
      </Tooltip>
    );
  }

  // 原有的 HealthCheck 逻辑
  let content;
  if (!env || env === "standalone") {
    content = <Typography>{t("health.standalone")}</Typography>;
  } else if (status === "checking") {
    content = (
      <Box display="flex" alignItems="center" gap={1}>
        <CircularProgress size={24} />
        <Typography>{t("health.connecting")}</Typography>
      </Box>
    );
  } else if (status === "connected") {
    content = <Typography>{t("health.connected")}</Typography>;
  } else {
    content = <Typography>{t("health.down")}</Typography>;
  }

  return (
    <Box
      sx={{
        color: "#000",
        padding: "0 1em",
      }}
    >
      {content}
    </Box>
  );
}
