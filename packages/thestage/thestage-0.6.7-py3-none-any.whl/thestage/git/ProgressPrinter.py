from git import RemoteProgress


class ProgressPrinter(RemoteProgress):
    def __init__( self ):
        super().__init__()

        self.__all_dropped_lines = []

    def update( self, op_code, cur_count, max_count=None, message='' ):
        pass

    def line_dropped( self, line ):
        if line.startswith( 'POST git-upload-pack' ):
            return

        self.__all_dropped_lines.append( line )

    def allErrorLines( self ):
        return self.error_lines + self.__all_dropped_lines

    def allDroppedLines( self ):
        return self.__all_dropped_lines