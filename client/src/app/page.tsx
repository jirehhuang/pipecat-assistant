'use client';

import {
  ConsoleTemplate,
  FullScreenContainer,
  ThemeProvider,
  PipecatAppBase,
  SpinLoader,
  type PipecatBaseChildProps,
} from '@pipecat-ai/voice-ui-kit';
import { App } from './components/App';

export default function Home() {
  return (
    <ThemeProvider>
      <FullScreenContainer>
        <ConsoleTemplate
          transportType="daily"
          connectParams={{
            endpoint: "/api/connect",
          }}
          noUserVideo
        />
      </FullScreenContainer>
    </ThemeProvider>
  );
}
