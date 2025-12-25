import time
import threading

import grpc


class CancellableStreamThread:
    def __init__(
        self, callback, create_stream, logger, attribute=None, ignore_unavailable=False
    ):
        """
        Feeds data from the gRPC stream into the callback
        until the cancel method is called.
        """
        self.stream = None
        self._canceled = False

        def target():
            while True:
                try:
                    self.stream = create_stream()
                    if self._canceled:
                        return
                    for _ in self.stream:
                        if attribute is not None:
                            callback(getattr(_, attribute))
                        else:
                            callback(_)
                except grpc.RpcError as e:
                    if e.code() == grpc.StatusCode.CANCELLED:
                        return
                    if logger and not (
                        ignore_unavailable and e.code() == grpc.StatusCode.UNAVAILABLE
                    ):
                        logger.warn("Error creating stream %s" % str(e))
                    if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                        return
                    # wait a short duration before re-registering when
                    # agent unavailable or other rpc error
                    time.sleep(0.1)

        t = threading.Thread(target=target,name="CancellableStreamThread")
        t.daemon = True
        t.start()

    def cancel(self):
        self._canceled = True
        if self.stream is not None:
            self.stream.cancel()
