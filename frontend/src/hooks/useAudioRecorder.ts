import { useTheme } from 'next-themes';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import RecordPlugin from 'wavesurfer.js/dist/plugins/record.esm.js';

interface UseAudioRecorderProps {
  onTranscriptionReceived: (transcription: string) => void;
}

export const useAudioRecorder = ({ onTranscriptionReceived }: UseAudioRecorderProps) => {
  const { resolvedTheme } = useTheme();
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const recordPluginRef = useRef<RecordPlugin | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const operationInProgress = useRef(false);

  // Theme-based waveform colors
  const waveformOptions = useMemo(() => {
    const dark = resolvedTheme === 'dark';
    return {
      waveColor: dark ? 'rgb(115, 115, 115)' : 'rgb(163, 163, 163)',
      progressColor: dark ? 'rgb(96, 165, 250)' : 'rgb(59, 130, 246)',
    };
  }, [resolvedTheme]);

  // Register plugin event handlers
  const attachEvents = useCallback((plugin: RecordPlugin) => {
    plugin.on('record-start', () => {
      setIsRecording(true);
      setError(null);
    });

    plugin.on('record-end', async (blob: Blob) => {
      setIsRecording(false);
      operationInProgress.current = false;

      if (blob.size < 1000) return;

      setIsProcessing(true);
      try {
        const formData = new FormData();
        formData.append('audio', blob, 'recording.wav');
        const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:2024';
        const res = await fetch(`${url}/api/transcribe`, { method: 'POST', body: formData });
        if (!res.ok) throw new Error('Transcription failed');
        const { transcription } = await res.json();
        onTranscriptionReceived(transcription);
      } catch {
        setError('Failed to transcribe audio. Please try again.');
      } finally {
        setIsProcessing(false);
      }
    });
  }, [onTranscriptionReceived]);

  // Initialize or reinitialize WaveSurfer and plugin
  const initializeWaveSurfer = useCallback(async () => {
    if (!containerRef.current) return;
    setError(null);

    // Destroy existing
    wavesurferRef.current?.destroy();
    wavesurferRef.current = null;
    recordPluginRef.current = null;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      height: 40,
      barWidth: 2,
      barGap: 3,
      barRadius: 3,
      ...waveformOptions,
    });

    const plugin = ws.registerPlugin(RecordPlugin.create({
      renderRecordedAudio: false,
      scrollingWaveform: true,
      scrollingWaveformWindow: 15,
    }));

    wavesurferRef.current = ws;
    recordPluginRef.current = plugin;
    setIsInitialized(true);

    // Check mic permissions
    try {
      await RecordPlugin.getAvailableAudioDevices();
    } catch {
      setError('Could not access microphone. Please grant permission.');
    }

    attachEvents(plugin);
  }, [waveformOptions, attachEvents]);

  const startRecording = useCallback(async () => {
    if (operationInProgress.current) return;
    operationInProgress.current = true;
    setError(null);

    if (!isInitialized) {
      await initializeWaveSurfer();
      await new Promise(r => setTimeout(r, 100));
    }

    const plugin = recordPluginRef.current;
    if (!plugin) {
      setError('Audio recorder not initialized');
      operationInProgress.current = false;
      return;
    }

    try {
      await plugin.startRecording();
    } catch {
      setError('Failed to start recording. Please check microphone permissions.');
      operationInProgress.current = false;
    }
  }, [isInitialized, initializeWaveSurfer]);

  const stopRecording = useCallback(() => {
    recordPluginRef.current?.stopRecording();
    operationInProgress.current = false;
  }, []);

  const toggleRecording = useCallback(() => {
    if (isRecording) stopRecording();
    else if (!operationInProgress.current && !isProcessing) startRecording();
  }, [isRecording, isProcessing, startRecording, stopRecording]);

  // Reinitialize on theme change when idle
  useEffect(() => {
    if (isInitialized && !isRecording) {
      setIsInitialized(false);
      setTimeout(initializeWaveSurfer, 100);
    }
  }, [resolvedTheme]);

  // Cleanup function to destroy WaveSurfer and reset state
  const cleanup = useCallback(() => {
    wavesurferRef.current?.destroy();
    wavesurferRef.current = null;
    recordPluginRef.current = null;
    setIsInitialized(false);
    operationInProgress.current = false;
  }, []);

  return {
    containerRef,
    isRecording,
    isProcessing,
    isInitialized,
    toggleRecording,
    error,
    cleanup,
  };
};
