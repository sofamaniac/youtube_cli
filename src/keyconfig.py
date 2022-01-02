import curses
class KeyConfiguration:

    def __init__(self):

        self.quit   = ord('q')
        
        self.down   = ord('j')
        self.up     = ord('k')
        self.left   = ord('h')
        self.right  = ord('l')

        self.pause      = ord(' ')
        self.next       = ord('>')
        self.prev       = ord('<')

        self.forward    = curses.KEY_RIGHT
        self.backward   = curses.KEY_LEFT

        self.mute       = ord('m')
        self.incVolume  = ord('f')
        self.decVolume  = ord('d')

        self.nextPage   = ord('n')
        self.prevPage   = ord('p')

        self.validate   = ord('\n')
        self.autoplay   = ord('a')
        self.repeat     = ord('r')
        self.shuffle    = ord('y')
        self.addPlaylist= ord('t')
        self.search     = ord('s')
        self.reload     = ord('c')
        self.video      = ord('v')

configuration = KeyConfiguration()
