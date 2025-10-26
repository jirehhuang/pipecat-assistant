import {
  Button,
  ConnectButton,
  ControlBar,
  ErrorCard,
  PipecatLogo,
  TranscriptOverlay,
  UserAudioControl,
  usePipecatConnectionState,
} from '@pipecat-ai/voice-ui-kit';
import { PlasmaVisualizer } from '@pipecat-ai/voice-ui-kit/webgl';
import { LogOutIcon, XIcon, MicIcon } from 'lucide-react';
import { usePipecatClient } from '@pipecat-ai/client-react';
import { useCallback, useState } from 'react';

export interface AppProps {
  handleConnect?: () => void | Promise<void>;
  handleDisconnect?: () => void | Promise<void>;
  error?: string | null;
}

export const App = ({ handleConnect, handleDisconnect, error }: AppProps) => {
  const { isConnected } = usePipecatConnectionState();

  if (error) {
    return (
      <ErrorCard error={error} title="An error occurred connecting to agent." />
    );
  }

  return (
    <div className="w-full h-screen">
      <div className="flex flex-col h-full">
        <div className="relative bg-background overflow-hidden flex-1 shadow-long/[0.02]">
          <main className="flex flex-col gap-0 h-full relative justify-end items-center">
            <PlasmaVisualizer />
            <div className="absolute w-full h-full flex items-center justify-center">
              <ConnectButton
                size="xl"
                onConnect={handleConnect}
                onDisconnect={handleDisconnect}
              />
            </div>
            <div className="absolute w-full h-full flex items-center justify-center pointer-events-none">
              <TranscriptOverlay participant="remote" className="max-w-md" />
            </div>
            {isConnected && (
              <>
                <ControlBar>
                  <UserAudioControl />
                  <Button
                    size="xl"
                    isIcon={true}
                    variant="outline"
                    onClick={handleDisconnect}>
                    <LogOutIcon />
                  </Button>
                </ControlBar>
              </>
            )}
          </main>
        </div>
        <footer className="p-5 md:p-7 text-center flex flex-row gap-4 items-center justify-center">
          <PipecatLogo className="h-[24px] w-auto text-gray-500" />
          <div className="flex flex-row gap-2 items-center justify-center opacity-60">
            <p className="text-sm text-muted-foreground font-medium">
              Pipecat AI
            </p>
            <XIcon size={16} className="text-gray-400" />
            <p className="text-sm text-muted-foreground font-medium">
              Voice UI Kit
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default App;
