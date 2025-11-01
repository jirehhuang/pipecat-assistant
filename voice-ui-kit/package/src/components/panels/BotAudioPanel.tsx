import {
  Panel,
  PanelContent,
  PanelHeader,
  PanelTitle,
} from "@/components/ui/panel";
import { cn } from "@/lib/utils";
import { VoiceVisualizer } from "@/visualizers/VoiceVisualizer";
import { usePipecatClientMediaTrack } from "@pipecat-ai/client-react";
import { MicOffIcon, Volume2Icon, VolumeXIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";

interface BotAudioPanelProps {
  audioTracks?: MediaStreamTrack[];
  className?: string;
  collapsed?: boolean;
  visualization?: "bar" | "circle";
  isMuted?: boolean;
  onMuteToggle?: () => void;
}

const barCount = 10;

export const BotAudioPanel: React.FC<BotAudioPanelProps> = ({
  className,
  collapsed = false,
  isMuted = false,
  onMuteToggle,
}) => {
  const track = usePipecatClientMediaTrack("audio", "bot");

  const [maxHeight, setMaxHeight] = useState(48);
  const [width, setWidth] = useState(4);

  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;

        const maxWidth = 240;
        const maxBarWidth = maxWidth / (2 * barCount - 1);
        const maxMaxHeight = 240 / (16 / 9);

        const barWidth = Math.max(
          Math.min(width / (barCount * 2), maxBarWidth),
          2,
        );
        const maxHeight = Math.max(Math.min(height, maxMaxHeight), 20);

        setMaxHeight(maxHeight);
        setWidth(barWidth);
      }
    });
    observer.observe(containerRef.current);
    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <Panel
      className={cn(
        "flex-1 mt-auto",
        {
          "flex-0 border-none": collapsed,
        },
        className,
      )}
    >
      {!collapsed && (
        <PanelHeader>
          <PanelTitle>Bot Audio</PanelTitle>
          {onMuteToggle && (
            <Button
              variant="ghost"
              size="sm"
              isIcon
              onClick={onMuteToggle}
              disabled={!track}
              className="ml-auto"
              aria-label={isMuted ? "Unmute bot" : "Mute bot"}
            >
              {isMuted ? <VolumeXIcon size={16} /> : <Volume2Icon size={16} />}
            </Button>
          )}
        </PanelHeader>
      )}
      <PanelContent
        className={cn("overflow-hidden flex-1", {
          "aspect-video": collapsed && !onMuteToggle,
          "min-h-32": collapsed && onMuteToggle,
        })}
      >
        <div
          ref={containerRef}
          className={cn("flex h-full overflow-hidden", {
            "flex-col": collapsed,
            "relative": !collapsed,
          })}
        >
          {/* Mute button for collapsed state */}
          {collapsed && onMuteToggle && (
            <>
              <div className="flex justify-end p-2">
                <Button
                  variant="ghost"
                  size="sm"
                  isIcon
                  onClick={onMuteToggle}
                  disabled={!track}
                  aria-label={isMuted ? "Unmute bot" : "Mute bot"}
                >
                  {isMuted ? <VolumeXIcon size={16} /> : <Volume2Icon size={16} />}
                </Button>
              </div>
              <div className="border-t border-border" />
            </>
          )}
          {track ? (
            <div className={cn({ "m-auto": !collapsed, "flex-1 flex items-center justify-center": collapsed })}>
              <VoiceVisualizer
                participantType="bot"
                backgroundColor="transparent"
                barColor="--color-agent"
                barCount={barCount}
                barGap={width}
                barLineCap="square"
                barMaxHeight={maxHeight}
                barOrigin="bottom"
                barWidth={width}
              />
            </div>
          ) : (
            <div className={cn("text-subtle flex w-full gap-2 items-center justify-center", {
              "flex-1": collapsed,
            })}>
              <MicOffIcon size={16} />
              {!collapsed && (
                <span className="font-semibold text-sm">No audio</span>
              )}
            </div>
          )}
        </div>
      </PanelContent>
    </Panel>
  );
};

export default BotAudioPanel;
