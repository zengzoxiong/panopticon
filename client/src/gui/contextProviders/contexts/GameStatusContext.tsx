import { createContext } from "react";

type GameStatusContextType = string;
type SetGameStatusContextType = (status: string) => void;

const GameStatusContext =
  createContext<GameStatusContextType>("status.scenarioPaused");
const SetGameStatusContext = createContext<SetGameStatusContextType>(
  (_status: string) => {}
);

export { GameStatusContext, SetGameStatusContext };
