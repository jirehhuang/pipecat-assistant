'use client';

import {
  ConsoleTemplate,
  FullScreenContainer,
  ThemeProvider,
} from '@pipecat-ai/voice-ui-kit';

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
          collapseMediaPanel={true}
          collapseInfoPanel={true}
          collapseEventsPanel={true}
        />
      </FullScreenContainer>
    </ThemeProvider>
  );
}
