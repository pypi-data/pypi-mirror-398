import mimetypes
import re
import signal
import subprocess
import time
from distutils.spawn import find_executable
from time import sleep

from ovos_bus_client import Message
from ovos_plugin_manager.templates.audio import AudioBackend
from ovos_utils.log import LOG
from requests import Session

try:
    from ovos_utils.ocp import MediaState
except ImportError:
    LOG.warning("Please update to ovos-utils~=0.1.")
    from enum import IntEnum


    class MediaState(IntEnum):
        # https://doc.qt.io/qt-5/qmediaplayer.html#MediaStatus-enum
        # The status of the media cannot be determined.
        UNKNOWN = 0
        # There is no current media. PlayerState == STOPPED
        NO_MEDIA = 1
        # The current media is being loaded. The player may be in any state.
        LOADING_MEDIA = 2
        # The current media has been loaded. PlayerState== STOPPED
        LOADED_MEDIA = 3
        # Playback of the current media has stalled due to
        # insufficient buffering or some other temporary interruption.
        # PlayerState != STOPPED
        STALLED_MEDIA = 4
        # The player is buffering data but has enough data buffered
        # for playback to continue for the immediate future.
        # PlayerState != STOPPED
        BUFFERING_MEDIA = 5
        # The player has fully buffered the current media. PlayerState != STOPPED
        BUFFERED_MEDIA = 6
        # Playback has reached the end of the current media. PlayerState == STOPPED
        END_OF_MEDIA = 7
        # The current media cannot be played. PlayerState == STOPPED
        INVALID_MEDIA = 8


def find_mime(path):
    mime = None
    if path.startswith('http'):
        response = Session().head(path, allow_redirects=True)
        if 200 <= response.status_code < 300:
            mime = response.headers['content-type']
    if not mime:
        mime = mimetypes.guess_type(path)[0]
    # Remove any http address arguments
    if not mime:
        mime = mimetypes.guess_type(re.sub(r'\?.*$', '', path))[0]

    if mime:
        return mime.split('/')
    else:
        return (None, None)


def play_audio(uri, play_cmd="play"):
    """ Play a audio file.

        Returns: subprocess.Popen object
    """
    play_wav_cmd = play_cmd.split() + [uri]

    try:
        return subprocess.Popen(play_wav_cmd)
    except Exception as e:
        LOG.error(f"Failed to play: {play_wav_cmd}")
        LOG.debug(f"Error: {e}")
        return None


class OVOSSimpleService(AudioBackend):
    sox_play = find_executable("play")
    pulse_play = find_executable("paplay")
    alsa_play = find_executable("aplay")
    mpg123_play = find_executable("mpg123")

    def __init__(self, config, bus=None, name='ovos_simple'):
        super(OVOSSimpleService, self).__init__(config, bus)
        self.name = name

        self.process = None
        self._stop_signal = False
        self._is_playing = False
        self._time_accumulator = 0
        self._start = 0
        self._paused = False

        self.supports_mime_hints = True
        mimetypes.init()

        self.bus.on('ovos.common_play.simple.play', self._play)

    ###################
    # simple player internals
    def _get_track(self, track_data):
        if isinstance(track_data, list):
            track = track_data[0]
            mime = track_data[1]
            mime = mime.split('/')
        else:  # Assume string
            track = track_data
            mime = find_mime(track)
        return track, mime

    def _is_process_running(self):
        return self.process and self.process.poll() is None

    def _stop_running_process(self):
        if self._is_process_running():
            if self._paused:
                # The child process must be "unpaused" in order to be stopped
                self.process.send_signal(signal.SIGCONT)
            self.process.terminate()
            countdown = 10
            while self._is_process_running() and countdown > 0:
                sleep(0.1)
                countdown -= 1

            if self._is_process_running():
                # Failed to shutdown when asked nicely.  Force the issue.
                LOG.debug("Killing currently playing audio...")
                self.process.kill()
        self.process = None

    def _play(self, message):
        """Implementation specific async method to handle playback.

        This allows mpg123 service to use the next method as well
        as basic play/stop.
        """
        LOG.info('SimpleAudioService._play')

        # Stop any existing audio playback
        self._stop_running_process()

        repeat = message.data.get('repeat', False)
        self._is_playing = True
        self._paused = False

        # sox should handle almost every format, but fails in some urls
        if self.sox_play:
            track = self._now_playing
            # NOTE: some urls like youtube streams will cause extension detection to fail
            # let's handle it explicitly
            ext = track.split("?")[0].split(".")[-1]
            player = self.sox_play + f" --type {ext}"

        # determine best available player
        else:
            track, mime = self._get_track(self._now_playing)
            LOG.debug(f'Mime info: {mime}')

            # wav file
            player = None
            if 'wav' in mime[1]:
                player = self.pulse_play
            # guess mp3
            elif self.mpg123_play:
                player = self.mpg123_play

            # fallback to alsa, only wav files will play correctly
            player = player or self.alsa_play

        # Indicate to audio service which track is being played
        self._track_start_callback(track)

        # Replace file:// uri's with normal paths
        uri = track.replace('file://', '')

        try:
            self.process = play_audio(uri, player)
        except FileNotFoundError as e:
            LOG.error(f'Couldn\'t play audio, {e}')
            self.process = None
        except Exception as e:
            LOG.exception(repr(e))
            self.process = None

        if self.process:
            # Wait for completion or stop request
            while (self._is_process_running() and not self._stop_signal):
                sleep(0.25)

            if self._stop_signal:
                self._stop_running_process()
                self._is_playing = False
                self._paused = False
                return
            else:
                self.process = None
        else:
            try:
                self.ocp_error()
            except:  # too old OPM version
                self.bus.emit(Message("ovos.common_play.media.state",
                                      {"state": MediaState.INVALID_MEDIA}))

        self._track_start_callback(None)
        self._is_playing = False
        self._paused = False

    ############
    # mandatory abstract methods

    @property
    def playback_time(self):
        """ in milliseconds """
        return max(self._start - time.time(), 0) + self._time_accumulator

    def supported_uris(self):
        uris = ['file', 'http']
        if self.sox_play:
            uris.append("https")
        return uris

    def play(self, repeat=False):
        """ Play playlist using simple. """
        self._start = time.time()
        self._time_accumulator = 0
        self.bus.emit(Message('ovos.common_play.simple.play',
                              {'repeat': repeat}))

    def stop(self):
        """ Stop simple playback. """
        LOG.info('SimpleService Stop')
        self._start = self._time_accumulator = 0
        if self._is_playing:
            self._stop_signal = True
            while self._is_playing:
                sleep(0.1)
            self._stop_signal = False
            return True
        return False

    def pause(self):
        """ Pause simple playback. """
        if self.process and not self._paused:
            if self._start:
                self._time_accumulator += time.time() - self._start
                self._start = 0
            # Suspend the playback process
            self.process.send_signal(signal.SIGSTOP)
            self._paused = True

    def resume(self):
        """ Resume paused playback. """
        if self.process and self._paused:
            self._start = time.time()
            # Resume the playback process
            self.process.send_signal(signal.SIGCONT)
            self._paused = False

    def get_track_position(self):
        """
        get current position in milliseconds
        """
        return self.playback_time

    ################
    # missing features in simple audio plugin
    def lower_volume(self):
        LOG.error("simple audio player does not support lower_volume")

    def restore_volume(self):
        LOG.error("simple audio player does not support restore_volume")

    def get_track_length(self):
        """
        getting the duration of the audio in milliseconds
        """
        LOG.error("simple audio player does not support get_track_length")
        return self.playback_time

    def set_track_position(self, milliseconds):
        """
        go to position in milliseconds

          Args:
                milliseconds (int): number of milliseconds of final position
        """
        LOG.error("simple audio player does not support set_track_position")

    def seek_forward(self, seconds=1):
        """
        skip X seconds

          Args:
                seconds (int): number of seconds to seek, if negative rewind
        """
        LOG.error("simple audio player does not support seek_forward")

    def seek_backward(self, seconds=1):
        """
        rewind X seconds

          Args:
                seconds (int): number of seconds to seek, if negative rewind
        """
        LOG.error("simple audio player does not support seek_backward")


def load_service(base_config, bus):
    backends = base_config.get('backends', [])
    services = [(b, backends[b]) for b in backends
                if backends[b]['type'] in ["simple",
                                           'ovos_simple',
                                           'ovos_audio_simple'] and
                backends[b].get('active', False)]

    if not any([OVOSSimpleService.sox_play,
                OVOSSimpleService.pulse_play,
                OVOSSimpleService.alsa_play,
                OVOSSimpleService.mpg123_play]):
        LOG.error("No basic playback functionality detected!!")
        return []

    instances = [OVOSSimpleService(s[1], bus, s[0]) for s in services]
    return instances


SimpleAudioPluginConfig = {
    "simple": {
        "type": "ovos_simple",
        "active": True
    }
}
