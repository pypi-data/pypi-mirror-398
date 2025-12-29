from ._classes import *




"""
RLAPI void InitAudioDevice(void);                                     // Initialize audio device and context
RLAPI void CloseAudioDevice(void);                                    // Close the audio device and context
RLAPI bool IsAudioDeviceReady(void);                                  // Check if audio device has been initialized successfully
RLAPI void SetMasterVolume(float volume);                             // Set master volume (listener)
RLAPI float GetMasterVolume(void);                                    // Get master volume (listener)
"""
init_audio_device = lib.InitAudioDevice
close_audio_device = lib.CloseAudioDevice

makeconnect("IsAudioDeviceReady", [], c_bool)
def is_audio_device_ready():
    return lib.IsAudioDeviceReady()

makeconnect("SetMasterVolume", [c_float])
def set_master_volume(volume: float):
    lib.SetMasterVolume(volume)

makeconnect("GetMasterVolume", [], c_float)
def get_master_volume():
    return lib.GetMasterVolume()

"""
RLAPI void PlaySound(Sound sound);                                    // Play a sound
RLAPI void StopSound(Sound sound);                                    // Stop playing a sound
RLAPI void PauseSound(Sound sound);                                   // Pause a sound
RLAPI void ResumeSound(Sound sound);                                  // Resume a paused sound

RLAPI bool IsSoundPlaying(Sound sound);                               // Check if a sound is currently playing
RLAPI void SetSoundVolume(Sound sound, float volume);                 // Set volume for a sound (1.0 is max level)
RLAPI void SetSoundPitch(Sound sound, float pitch);                   // Set pitch for a sound (1.0 is base level)
RLAPI void SetSoundPan(Sound sound, float pan);                       // Set pan for a sound (0.5 is center)

RLAPI Wave WaveCopy(Wave wave);                                       // Copy a wave to a new wave
RLAPI void WaveCrop(Wave *wave, int initFrame, int finalFrame);       // Crop a wave to defined frames range
RLAPI void WaveFormat(Wave *wave, int sampleRate, int sampleSize, int channels); // Convert wave data to desired format
RLAPI float *LoadWaveSamples(Wave wave);                              // Load samples data from wave as a 32bit float data array
RLAPI void UnloadWaveSamples(float *samples);   
"""

makeconnect("PlaySound", [Sound])
def play_sound(sound: Sound):
    lib.PlaySound(sound)

makeconnect("StopSound", [Sound])
def stop_sound(sound: Sound):
    lib.StopSound(sound)

makeconnect("PauseSound", [Sound])
def pause_sound(sound: Sound):
    lib.PauseSound(sound)

makeconnect("ResumeSound", [Sound])
def resume_sound(sound: Sound):
    lib.ResumeSound(sound)

makeconnect("IsSoundPlaying", [Sound], c_bool)
def is_sound_playing(sound: Sound):
    return lib.IsSoundPlaying(sound)

makeconnect("SetSoundVolume", [Sound])
def set_sound_volume(sound: Sound, volume: float):
    lib.SetSoundVolume(sound, volume)

makeconnect("SetSoundPitch", [Sound])
def set_sound_pitch(sound: Sound, pitch: float):
    lib.SetSoundPitch(sound, pitch)

makeconnect("SetSoundPan", [Sound])
def set_sound_pan(sound: Sound, pan: float):
    lib.SetSoundPan(sound, pan)

# WaveCopy
makeconnect("WaveCopy", [Wave], Wave)
def wave_copy(wave: Wave):
    """Copy a wave to a new wave."""
    return lib.WaveCopy(wave)


# WaveCrop
makeconnect("WaveCrop", [POINTER(Wave), c_int, c_int])
def wave_crop(wave: Wave, init_frame: int, final_frame: int):
    """Crop a wave to a defined frame range."""
    lib.WaveCrop(byref(wave), init_frame, final_frame)
    return wave


# WaveFormat
makeconnect("WaveFormat", [POINTER(Wave), c_int, c_int, c_int])
def wave_format(wave: Wave, sample_rate: int, sample_size: int, channels: int):
    """Convert wave data to desired format (sample rate, bit depth, channels)."""
    lib.WaveFormat(byref(wave), sample_rate, sample_size, channels)
    return wave


# LoadWaveSamples
makeconnect("LoadWaveSamples", [Wave], POINTER(c_float))
def load_wave_samples(wave: Wave):
    """Load 32-bit float samples from a wave and return a pointer."""
    return lib.LoadWaveSamples(wave)


# UnloadWaveSamples
makeconnect("UnloadWaveSamples", [POINTER(c_float)])
def unload_wave_samples(samples):
    """Unload 32-bit float samples previously loaded from a wave."""
    lib.UnloadWaveSamples(samples)

"""
RLAPI bool IsMusicValid(Music music);                                 // Checks if a music stream is valid (context and buffers initialized)
RLAPI void UnloadMusicStream(Music music);                            // Unload music stream
RLAPI void PlayMusicStream(Music music);                              // Start music playing
RLAPI bool IsMusicStreamPlaying(Music music);                         // Check if music is playing

RLAPI void UpdateMusicStream(Music music);                            // Updates buffers for music streaming
RLAPI void StopMusicStream(Music music);                              // Stop music playing
RLAPI void PauseMusicStream(Music music);                             // Pause music playing
RLAPI void ResumeMusicStream(Music music);                            // Resume playing paused music

RLAPI void SeekMusicStream(Music music, float position);              // Seek music to a position (in seconds)
RLAPI void SetMusicVolume(Music music, float volume);                 // Set volume for music (1.0 is max level)
RLAPI void SetMusicPitch(Music music, float pitch);                   // Set pitch for a music (1.0 is base level)
RLAPI void SetMusicPan(Music music, float pan);                       // Set pan for a music (0.5 is center)

RLAPI float GetMusicTimeLength(Music music);                          // Get music time length (in seconds)
RLAPI float GetMusicTimePlayed(Music music);                          // Get current music time played (in seconds)
"""

makeconnect("IsMusicValid", [Music], c_bool)
def is_music_valid(music: Music):
    return lib.IsMusicValid(music)

makeconnect("UnloadMusicStream", [Music])
def unload_music_stream(music: Music):
    lib.UnloadMusicStream(music)

makeconnect("PlayMusicStream", [Music])
def play_music_stream(music: Music):
    lib.PlayMusicStream(music)

makeconnect("IsMusicStreamPlaying", [Music], c_bool)
def is_music_stream_playing(music: Music):
    return lib.IsMusicStreamPlaying(music)

# music_stream
makeconnect("UpdateMusicStream", [Music])
def update_music_stream(music: Music):
    lib.UpdateMusicStream(music)

makeconnect("StopMusicStream", [Music])
def stop_music_stream(music: Music):
    lib.StopMusicStream(music)

makeconnect("PauseMusicStream", [Music])
def pause_music_stream(music: Music):
    lib.PauseMusicStream(music)

makeconnect("ResumeMusicStream", [Music])
def resume_music_stream(music: Music):
    lib.ResumeMusicStream(music)

makeconnect("SeekMusicStream", [Music, c_float])
def seek_music_stream(music: Music, position: float):
    lib.SeekMusicStream(music, position)

makeconnect("SetMusicVolume", [Music, c_float])
def set_music_volume(music: Music, volume: float):
    lib.SetMusicVolume(music, volume)

makeconnect("SetMusicPitch", [Music, c_float])
def set_music_pitch(music: Music, pitch: float):
    lib.SetMusicPitch(music, pitch)

makeconnect("SetMusicPan", [Music, c_float])
def pan(music: Music, pan: float):
    lib.SetMusicPan(music, pan)


makeconnect("GetMusicTimeLength", [Music], c_float)
def get_music_time_length(music: Music):
    "Get music time length (in seconds)"
    return lib.GetMusicTimeLength(music)

makeconnect("GetMusicTimePlayed", [Music], c_float)
def get_music_time_played(music: Music):
    "Get current music time played (in seconds)"
    return lib.GetMusicTimePlayed(music)

