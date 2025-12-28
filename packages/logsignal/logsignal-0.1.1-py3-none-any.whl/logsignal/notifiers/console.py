from logsignal.signal import Signal


class ConsoleNotifier:
    def notify(self, signal: Signal) -> None:
        print(
            f"[{signal.severity.upper()}] "
            f"{signal.name}: {signal.message} | {signal.meta}"
        )
