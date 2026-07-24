import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { IconButton, Tooltip, Chip, TextField, Stack, Typography } from "@mui/material";
import { Pause, PlayArrow, Stop, Wifi, WifiOff } from "@mui/icons-material";

interface RealtimeTelemetryPlayerProps {
  onConnect: (url: string) => void;
  onDisconnect: () => void;
  connected: boolean;
  frameCount: number;
}

export default function RealtimeTelemetryPlayer(
  props: Readonly<RealtimeTelemetryPlayerProps>
) {
  const { t } = useTranslation();
  const [wsUrl, setWsUrl] = useState<string>("ws://127.0.0.1:8765");
  const [isConnecting, setIsConnecting] = useState<boolean>(false);

  const handleConnect = () => {
    if (props.connected) {
      props.onDisconnect();
    } else {
      setIsConnecting(true);
      props.onConnect(wsUrl);
    }
  };

  useEffect(() => {
    if (props.connected) {
      setIsConnecting(false);
    }
  }, [props.connected]);

  return (
    <Stack direction="column" spacing={1} sx={{ padding: "0 1em" }}>
      <Stack direction="row" spacing={1} alignItems="center">
        <TextField
          size="small"
          label={t("toolbar.telemetry.websocketUrl", "WebSocket URL")}
          value={wsUrl}
          onChange={(e) => setWsUrl(e.target.value)}
          disabled={props.connected}
          sx={{ flex: 1 }}
          placeholder="ws://127.0.0.1:8765"
        />
        <Tooltip
          title={
            props.connected
              ? t("toolbar.telemetry.disconnect", "断开连接")
              : t("toolbar.telemetry.connect", "连接")
          }
        >
          <IconButton onClick={handleConnect} color={props.connected ? "error" : "primary"}>
            {props.connected ? <WifiOff /> : <Wifi />}
          </IconButton>
        </Tooltip>
      </Stack>
      <Stack direction="row" spacing={1} alignItems="center" justifyContent="center">
        <Chip
          icon={props.connected ? <Wifi /> : <WifiOff />}
          label={
            props.connected
              ? t("toolbar.telemetry.connected", "已连接")
              : isConnecting
              ? t("toolbar.telemetry.connecting", "连接中...")
              : t("toolbar.telemetry.disconnected", "未连接")
          }
          color={props.connected ? "success" : "default"}
          size="small"
        />
        {props.connected && (
          <Typography variant="caption" color="text.secondary">
            {t("toolbar.telemetry.frames", "帧数")}: {props.frameCount}
          </Typography>
        )}
      </Stack>
    </Stack>
  );
}
