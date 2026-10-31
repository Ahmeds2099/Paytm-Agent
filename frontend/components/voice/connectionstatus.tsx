"use client";

type Props = {

    connected: boolean;

    connecting: boolean;

};

export default function ConnectionStatus({

    connected,

    connecting,

}: Props) {

    if (connecting) {
        return (
            <p className="text-yellow-500" data-status="connecting">
                <span aria-hidden="true" className="status-dot" data-status="connecting" /> Connecting...
            </p>
        );
    }

    if (connected) {
        return (
            <p className="text-green-500" data-status="ready">
                <span aria-hidden="true" className="status-dot" data-status="ready" /> Connected
            </p>
        );
    }

    return (
        <p className="text-red-500" data-status="idle">
            <span aria-hidden="true" className="status-dot" data-status="idle" /> Disconnected
        </p>
    );
}