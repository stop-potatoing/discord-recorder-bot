import discord
import asyncio
import os

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
client = discord.Client(intents=intents)

RECORDINGS_DIR = "recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)

TARGET_CHANNEL_ID = 123456789012345678  # 👈 replace with your text channel ID

class AudioRecorder(discord.AudioSink):
    def __init__(self, user):
        self.user = user
        self.filename = f"{RECORDINGS_DIR}/{user.id}-{int(asyncio.get_event_loop().time())}.pcm"
        self.file = open(self.filename, "wb")

    def write(self, data):
        if data.user == self.user:
            self.file.write(data.pcm)

    def cleanup(self):
        self.file.close()
        return self.filename

async def finished_callback(sink, user):
    print(f"💾 Finished recording {user}")
    filename = sink.cleanup()

    # Convert to .wav with ffmpeg
    wav_filename = filename.replace(".pcm", ".wav")
    os.system(f"ffmpeg -f s16le -ar 48000 -ac 2 -i {filename} {wav_filename}")

    # Send file to target text channel
    channel = client.get_channel(TARGET_CHANNEL_ID)
    if channel:
        await channel.send(
            content=f"🎙 Recording for {user} finished:",
            file=discord.File(wav_filename)
        )

    # Clean up raw pcm
    os.remove(filename)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_voice_state_update(member, before, after):
    # User joins a channel
    if after.channel and not before.channel:
        channel = after.channel
        if member.bot:
            return  # ignore bots

        vc = await channel.connect()
        print(f"🎙️ Recording in {channel.name}")

        # Record all users (except bots)
        for user in channel.members:
            if not user.bot:
                recorder = AudioRecorder(user)
                vc.start_recording(recorder, finished_callback, user)

        # Optional: stop recording after 1 hour
        await asyncio.sleep(3600)
        if vc.is_connected():
            await vc.disconnect()

# Run bot with token from Railway Environment Variable
client.run(os.getenv("TOKEN"))
