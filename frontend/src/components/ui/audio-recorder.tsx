import { useAudioRecorder } from '@/hooks/useAudioRecorder';
import { cn } from '@/lib/utils';
import { Loader2, Mic } from 'lucide-react';
import React, { createContext, useContext, useEffect } from 'react';
import { Button } from '../ui/button';

interface AudioRecorderProps {
  onTranscriptionReceived: (transcription: string) => void;
  disabled?: boolean;
  className?: string;
}

// Context to share audio recorder state
interface AudioRecorderContextType {
  containerRef: React.RefObject<HTMLDivElement | null>;
  isRecording: boolean;
  isProcessing: boolean;
  isInitialized: boolean;
  toggleRecording: () => void;
  error: string | null;
}

const AudioRecorderContext = createContext<AudioRecorderContextType | null>(null);

// Provider component
export const AudioRecorderProvider: React.FC<{
  children: React.ReactNode;
  onTranscriptionReceived: (transcription: string) => void;
}> = ({ children, onTranscriptionReceived }) => {
  const audioRecorder = useAudioRecorder({ onTranscriptionReceived });

  // Cleanup on unmount only
  useEffect(() => {
    return () => {
      audioRecorder.cleanup();
    };
  }, [audioRecorder.cleanup]);

  return (
    <AudioRecorderContext.Provider value={audioRecorder}>
      {children}
    </AudioRecorderContext.Provider>
  );
};

// Hook to use the context
const useAudioRecorderContext = () => {
  const context = useContext(AudioRecorderContext);
  if (!context) {
    throw new Error('useAudioRecorderContext must be used within AudioRecorderProvider');
  }
  return context;
};

// Component that renders only the waveform
export const AudioWaveform: React.FC = () => {
  const { containerRef, isRecording } = useAudioRecorderContext();
  
  return (
    <div className={cn(
      "transition-all duration-300 overflow-hidden",
      isRecording ? "max-h-24 opacity-100" : "max-h-0 opacity-0"
    )}>
      <div className="bg-muted border border-border rounded-lg p-3 mb-3">
        <div ref={containerRef} className="w-full" style={{ height: '40px' }} />
      </div>
    </div>
  );
};

// Component that renders only the microphone button
export const AudioButton: React.FC<{
  disabled?: boolean;
  className?: string;
}> = ({ disabled, className }) => {
  const { toggleRecording, isRecording, isProcessing, error } = useAudioRecorderContext();
  
  return (
    <div className="relative">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={toggleRecording}
        disabled={disabled || isProcessing}
        className={cn(
          "transition-all duration-200",
          className
        )}
      >
        {isProcessing ? (
          <Loader2 className="size-6 animate-spin" />
        ) : (
          <Mic className={cn(
            "size-6 transition-colors",
            isRecording ? "text-red-500" : "text-muted-foreground hover:text-foreground"
          )} />
        )}
      </Button>
      
      {/* Error message (if any) */}
      {error && (
        <div className="absolute top-full left-0 mt-1 text-xs text-red-500 whitespace-nowrap">
          {error}
        </div>
      )}
    </div>
  );
};

// Legacy component for backward compatibility
export const AudioRecorder: React.FC<AudioRecorderProps> = ({
  onTranscriptionReceived,
  disabled = false,
  className,
}) => {
  return (
    <AudioRecorderProvider onTranscriptionReceived={onTranscriptionReceived}>
      <AudioButton disabled={disabled} className={className} />
    </AudioRecorderProvider>
  );
};
