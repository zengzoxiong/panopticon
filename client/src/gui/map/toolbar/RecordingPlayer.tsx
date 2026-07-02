import { useContext, useState } from "react";
import { useTranslation } from 'react-i18next';
import { IconButton, Slider, Tooltip } from "@mui/material";
import Stack from "@mui/material/Stack";
import { Pause, PlayArrow, SkipNext, SkipPrevious } from "@mui/icons-material";
import { RecordingStepContext } from "@/gui/contextProviders/contexts/RecordingStepContext";

interface RecordingPlayerProps {
  recordingPaused: boolean;
  timelineStart: number;
  timelineEnd: number;
  handlePlayRecordingClick: () => void;
  handlePauseRecordingClick: () => void;
  handleStepRecordingToStep: (step: number) => void;
  handleStepRecordingBackwards: () => void;
  handleStepRecordingForwards: () => void;
  formatTimelineMark: (step: number) => string;
}

export default function RecordingPlayer(props: Readonly<RecordingPlayerProps>) {
  const { t } = useTranslation();
  const [recordingPaused, setRecordingPaused] = useState<boolean>(
    props.recordingPaused
  );
  const recordingStep = useContext(RecordingStepContext);

  const handlePlayRecordingClick = () => {
    if (recordingPaused) {
      setRecordingPaused(false);
      props.handlePlayRecordingClick();
    } else {
      setRecordingPaused(true);
      props.handlePauseRecordingClick();
    }
  };

  const handleChangeRecordingStep = (event: Event, newValue: number) => {
    setRecordingPaused(true);
    props.handlePauseRecordingClick();
    props.handleStepRecordingToStep(newValue);
  };

  const stepRecordingBackwards = () => {
    setRecordingPaused(true);
    props.handlePauseRecordingClick();
    props.handleStepRecordingBackwards();
  };

  const stepRecordingForwards = () => {
    setRecordingPaused(true);
    props.handlePauseRecordingClick();
    props.handleStepRecordingForwards();
  };

  const recordingTimelineMark = (recordingStep: number) => {
    return <>{props.formatTimelineMark(recordingStep)}</>;
  };

  return (
    <>
      <Stack
        direction="row"
        spacing={1}
        sx={{
          padding: "0 2em",
        }}
      >
        <Slider
          aria-label="Recording Player Timeline"
          value={recordingStep}
          onChange={handleChangeRecordingStep}
          min={props.timelineStart}
          max={props.timelineEnd}
          shiftStep={1}
          step={1}
          size="small"
          valueLabelDisplay="auto"
          valueLabelFormat={(recordingStep) =>
            recordingTimelineMark(recordingStep)
          }
        />
      </Stack>
      <Stack
        direction="row"
        spacing={1}
        sx={{
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <Tooltip title={t('toolbar.recording.seekBackwards')}>
          <IconButton onClick={stepRecordingBackwards}>
            {<SkipPrevious />}
          </IconButton>
        </Tooltip>
        <Tooltip
          title={!recordingPaused ? t('toolbar.recording.pauseRecording') : t('toolbar.recording.playRecording')}
        >
          <IconButton onClick={handlePlayRecordingClick}>
            {!recordingPaused ? <Pause /> : <PlayArrow />}
          </IconButton>
        </Tooltip>
        <Tooltip title={t('toolbar.recording.seekForwards')}>
          <IconButton onClick={stepRecordingForwards}>
            {<SkipNext />}
          </IconButton>
        </Tooltip>
      </Stack>
    </>
  );
}
