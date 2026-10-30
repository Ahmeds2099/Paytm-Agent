export type AssistantSegment = {
    responseId: string;
    segmentId: string;
    text?: string;
};

export type VoiceError = {
    code: string;
    message: string;
    recoverable: boolean;
};

export type EmotionUpdate = {
    provider: string;
    status: string;
    label?: string;
    displayLabel?: string;
    rawLabel?: string;
    confidence?: number;
    smoothedConfidence?: number;
    reliable?: boolean;
    clarificationMode?: boolean;
    message?: string;
};

export class VoiceSocket {
    private socket: WebSocket | null = null;

    onOpen?: () => void;
    onClose?: () => void;
    onError?: (event: Event) => void;
    onMessage?: (data: unknown) => void;
    onTranscript?: (text: string) => void;
    onInterimTranscript?: (text: string) => void;
    onAssistantStreamStart?: (responseId?: string) => void;
    onAssistantStream?: (token: string, responseId?: string) => void;
    onAssistantStreamEnd?: (responseId?: string) => void;
    onAssistantAudio?: (audio: ArrayBuffer) => void;
    onInterrupted?: (responseId?: string) => void;
    onSegmentStart?: (segment: AssistantSegment) => void;
    onSegmentEnd?: (segment: AssistantSegment) => void;
    onSTTReady?: (provider: string) => void;
    onFallbackRequired?: (message: string) => void;
    onProviderChanged?: (provider: string) => void;
    onVoiceError?: (error: VoiceError) => void;
    onEmotionUpdate?: (emotion: EmotionUpdate) => void;
    onSessionRestored?: (messageCount: number, memoryCount: number) => void;
    onLanguageChanged?: (language: string, locked: boolean, display: string) => void;
    onConnected?: (sessionId: string) => void;
    onVoiceState?: (state: VoiceState) => void;
    onPipelineStage?: (stage: PipelineStage) => void;
    onToolAction?: (action: { status: string; summary: string; action?: string; durationMs?: number }) => void;
    onTurnContext?: (context: TurnContext) => void;

    onTurnMetrics?: (metrics: TurnMetrics) => void;
    onDocumentContextUpdated?: (documentIds: string[]) => void;
    // Phase 4
    onToolCall?: (data: { tool: string; args: Record<string, unknown>; status: string; latency_ms: number }) => void;
    onEscalation?: (reason: string) => void;
    onCallClosed?: (outcome: string) => void;
    onCallBlocked?: (message: string) => void;

    connect(url: string) {
        if (this.socket) {
            return;
        }

        this.socket = new WebSocket(url);
        this.socket.binaryType = "arraybuffer";

        this.socket.onopen = () => {
            this.onOpen?.();
        };

        this.socket.onmessage = (event) => {
            if (event.data instanceof ArrayBuffer) {
                this.onAssistantAudio?.(event.data);
                return;
            }

            const message = JSON.parse(event.data);

            switch (message.type) {
                case "connected":
                    this.onConnected?.(message.session_id ?? "");
                    break;
                case "transcript":
                    this.onTranscript?.(message.text);
                    break;
                case "transcript_interim":
                    this.onInterimTranscript?.(message.text);
                    break;
                case "assistant_stream_start":
                    this.onAssistantStreamStart?.(
                        message.response_id,
                    );
                    break;
                case "assistant_stream":
                    this.onAssistantStream?.(
                        message.token,
                        message.response_id,
                    );
                    break;
                case "assistant_stream_end":
                    this.onAssistantStreamEnd?.(
                        message.response_id,
                    );
                    break;
                case "assistant_segment_start":
                    this.onSegmentStart?.({
                        responseId: message.response_id,
                        segmentId: message.segment_id,
                        text: message.text,
                    });
                    break;
                case "assistant_segment_end":
                    this.onSegmentEnd?.({
                        responseId: message.response_id,
                        segmentId: message.segment_id,
                    });
                    break;
                case "interrupted":
                    this.onInterrupted?.(message.response_id);
                    break;
                case "stt_ready":
                    this.onSTTReady?.(message.provider);
                    break;
                case "stt_fallback_required":
                    this.onFallbackRequired?.(message.message);
                    break;
                case "stt_provider_changed":
                    this.onProviderChanged?.(message.provider);
                    break;
                case "emotion_status":
                case "emotion_update":
                    this.onEmotionUpdate?.({
                        provider: message.provider ?? "emotion2vec+",
                        status: message.status ?? "unknown",
                        label: message.label,
                        displayLabel: message.display_label,
                        rawLabel: message.raw_label,
                        confidence: message.confidence,
                        smoothedConfidence: message.smoothed_confidence,
                        reliable: Boolean(message.reliable),
                        clarificationMode: Boolean(
                            message.clarification_mode,
                        ),
                        message: message.message,
                    });
                    break;
                case "session_restored":
                    this.onSessionRestored?.(
                        Number(message.message_count ?? 0),
                        Number(message.memory_count ?? 0),
                    );
                    break;
                case "language_changed":
                    this.onLanguageChanged?.(
                        String(message.language ?? "auto"),
                        Boolean(message.locked),
                        String(message.display ?? message.language ?? "Auto"),
                    );
                    break;
                case "voice_state":
                    this.onVoiceState?.(message.state as VoiceState);
                    break;
                case "pipeline_stage":
                    this.onPipelineStage?.({
                        responseId: message.response_id,
                        stage: message.stage,
                        status: message.status ?? "unknown",
                        durationMs: message.duration_ms,
                        elapsedMs: message.elapsed_ms,
                        clientElapsedMs: message.client_elapsed_ms,
                        updatedAt: Date.now(),
                    });
                    break;
                case "tool_action":
                    this.onToolAction?.({
                        status: message.data?.status ?? "executed",
                        summary: message.data?.summary ?? "",
                        action: message.data?.action,
                        durationMs: message.data?.duration_ms,
                    });
                    break;

                case "turn_context":
                    this.onTurnContext?.({
                        responseId: message.response_id,
                        provenance: message.provenance ?? "general",
                        memoryCount: Number(message.memory_count ?? 0),
                        documentCount: Number(message.document_count ?? 0),
                        sources: Array.isArray(message.sources) ? message.sources : [],
                    });
                    break;
                case "turn_metrics":
                    this.onTurnMetrics?.({
                        responseId: message.response_id,
                        serverResponseMs: message.server_response_ms,
                        estimatedOutputTokens: message.estimated_output_tokens,
                        interrupted: Boolean(message.interrupted),
                    });
                    break;
                case "document_context_updated":
                    this.onDocumentContextUpdated?.(
                        Array.isArray(message.document_ids) ? message.document_ids : [],
                    );
                    break;
                case "tool_call":
                    // Phase 4: Paytm tool call result
                    this.onToolCall?.({
                        tool: message.data?.tool ?? "",
                        args: message.data?.args ?? {},
                        status: message.data?.status ?? "error",
                        latency_ms: message.data?.latency_ms ?? 0,
                    });
                    break;
                case "escalation":
                    // Phase 4: escalation event
                    this.onEscalation?.(String(message.reason ?? "unknown"));
                    break;
                case "call_closed":
                    this.onCallClosed?.(String(message.outcome ?? "closed"));
                    break;
                case "call_blocked":
                    this.onCallBlocked?.(String(message.message ?? "This demo call is not available."));
                    break;
                case "error":
                    this.onVoiceError?.({
                        code: message.code ?? "voice_error",
                        message: message.message ?? "Voice error",
                        recoverable: Boolean(message.recoverable),
                    });
                    break;
                default:
                    this.onMessage?.(message);
            }
        };

        this.socket.onerror = (event) => {
            this.onError?.(event);
        };

        this.socket.onclose = () => {
            this.socket = null;
            this.onClose?.();
        };
    }

    sendJSON(data: unknown) {
        if (this.connected) {
            this.socket?.send(JSON.stringify(data));
        }
    }

    sendPCM(buffer: ArrayBuffer) {
        if (this.connected) {
            this.socket?.send(buffer);
        }
    }

    acknowledgePlayback(responseId: string, segmentId: string) {
        this.sendJSON({
            type: "playback_ack",
            response_id: responseId,
            segment_id: segmentId,
        });
    }

    playbackStarted(
        responseId: string,
        segmentId: string,
        clientElapsedMs?: number,
    ) {
        this.sendJSON({
            type: "playback_started",
            response_id: responseId,
            segment_id: segmentId,
            client_elapsed_ms: clientElapsedMs,
        });
    }

    chooseFallback(choice: "continue" | "stop") {
        this.sendJSON({
            type: "stt_fallback_choice",
            choice,
        });
    }

    initializeSession(
        clientId: string,
        documentIds: string[],
        merchantProfile?: Record<string, unknown>,
    ) {
        const payload: Record<string, unknown> = {
            type: "session_init",
            client_id: clientId,
        };

        if (documentIds.length > 0 || !merchantProfile) {
            payload.document_ids = documentIds;
        }

        if (merchantProfile) {
            payload.merchant_profile = merchantProfile;
        }

        this.sendJSON(payload);
    }

    requestEscalation() {
        this.sendJSON({ type: "manual_escalation" });
    }

    setDocumentContext(documentIds: string[]) {
        this.sendJSON({
            type: "set_document_context",
            document_ids: documentIds,
        });
    }

    disconnect() {
        this.socket?.close();
    }

    get connected() {
        return this.socket?.readyState === WebSocket.OPEN;
    }
}
import type {
    PipelineStage,
    TurnContext,
    TurnMetrics,
    VoiceState,
} from "@/lib/voice/types";
