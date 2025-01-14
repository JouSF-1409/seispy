import logging
from os.path import expanduser, join


class setuplog(object):
    default_logs={
        "RF2depthlog":("RF2depth","INFO","stream_handler"),
        "RFlog":("RF","INFO","stream_handler"),
        "Batlog":("Bat","INFO","stream_handler","file_handler"),
        "CCPlog":("CCP","INFO","stream_handler"),
        "ModCreatorlog":("ModCreator","INFO","stream_handler"),
        "PickDepthlog": ("PickDepth", "INFO","stream_handler")
    }
    def __init__(self, filename=join(expanduser('~'), '.RF.log')):
        """
        use default_logs to gen loggers
        change default_logs for future changes if needed,
        check logger level with logger.getEffectiveLevel

        """
        self.filename = filename
        fh = logging.FileHandler(filename)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        for loger_branch, config in self.default_logs.items():
            # init, setlevel
            log = logging.getLogger(config[0])
            log.setLevel(config[1])
            next if log.hasHandlers else None

            # add handler
            if "file_handler" in config:
                log.addHandler(fh)
            if "stream_handler" in config:
                log.addHandler(ch)

            # attach to class
            setattr(self,loger_branch,log)


if __name__ == '__main__':
    logger = setuplog()
    logger.RFlog.info('print')