import React, { useState } from "react";
import {
  GameStatusContext,
  SetGameStatusContext,
} from "@/gui/contextProviders/contexts/GameStatusContext";

export const GameStatusProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [currentGameStatus, setCurrentGameStatus] =
    useState<string>("status.scenarioPaused"); // 存储翻译键而非翻译后的字符串

  return (
    <GameStatusContext.Provider value={currentGameStatus}>
      <SetGameStatusContext.Provider value={setCurrentGameStatus}>
        {children}
      </SetGameStatusContext.Provider>
    </GameStatusContext.Provider>
  );
};
