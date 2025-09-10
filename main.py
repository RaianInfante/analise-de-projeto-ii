import discord
from discord.ext import commands
import os
import subprocess
import asyncio
import time
import datetime
import re
from dotenv import load_dotenv

# Importar biblioteca para detectar dispositivo de áudio padrão
try:
    from pycaw.pycaw import AudioUtilities
    PYCAW_AVAILABLE = True
except ImportError:
    print("Biblioteca pycaw não encontrada. Usando método alternativo para detecção de dispositivos de áudio.")
    PYCAW_AVAILABLE = False

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Pasta de áudio
if not os.path.exists("audios"):
    os.makedirs("audios")

# Dicionário para armazenar informações de gravação por servidor
recording_data = {}


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")


@bot.command()
async def entrar(ctx):
    """Entra no canal de voz do usuário"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"Conectado ao canal {channel.name}")
    else:
        await ctx.send("Você não está em um canal de voz!")


def get_default_audio_device():
    """Obtém o dispositivo de áudio padrão do sistema usando pycaw"""
    # Usar o microfone Fifine como dispositivo preferencial
    try:
        # Verifica se o microfone Fifine está disponível
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-list_devices",
                "true", "-f", "dshow", "-i", "dummy"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Verifica pelo nome do dispositivo ou pelo nome alternativo
        if "Microfone (2- Fifine Microphone)" in result.stderr:
            print("Usando Microfone (2- Fifine Microphone) como dispositivo de gravação")
            return "Microfone (2- Fifine Microphone)"
        elif "@device_cm_{33D9A762-90C8-11D0-BD43-00A0C911CE86}\\wave_{A19A230B-EE1D-48B0-BB7F-D7F94E1AE7CA}" in result.stderr:
            print(
                "Usando nome alternativo do Fifine Microphone como dispositivo de gravação")
            return "@device_cm_{33D9A762-90C8-11D0-BD43-00A0C911CE86}\\wave_{A19A230B-EE1D-48B0-BB7F-D7F94E1AE7CA}"
    except Exception as e:
        print(f"Erro ao verificar microfone Fifine: {e}")

    # Se não encontrar o Fifine, tenta usar o dispositivo padrão do sistema
    try:
        if PYCAW_AVAILABLE:
            # Obtém o dispositivo de áudio padrão usando pycaw
            speakers = AudioUtilities.GetSpeakers()
            if speakers:
                # Obtém o nome amigável do dispositivo
                device_name = speakers.FriendlyName
                print(f"Dispositivo de áudio padrão detectado: {device_name}")
                return device_name
    except Exception as e:
        print(f"Erro ao obter dispositivo de áudio padrão com pycaw: {e}")

    return None


# Função para obter o dispositivo de áudio para gravação
def get_first_audio_device():
    """Obtém o dispositivo de áudio para gravação, priorizando o dispositivo padrão do sistema"""
    try:
        # Primeiro tenta obter o dispositivo padrão do sistema (que o Discord provavelmente está usando)
        default_device = get_default_audio_device()
        if default_device:
            return default_device

        # Se não conseguir, usa o método anterior para encontrar dispositivos
        # Executa o comando ffmpeg para listar dispositivos
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-list_devices",
                "true", "-f", "dshow", "-i", "dummy"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Extrai a saída de erro (onde o ffmpeg lista os dispositivos)
        output = result.stderr

        # Procura por dispositivos de áudio
        audio_devices = []
        audio_section = False

        for line in output.split('\n'):
            if "DirectShow audio devices" in line:
                audio_section = True
                continue

            if audio_section and "DirectShow video devices" in line:
                audio_section = False
                break

            if audio_section:
                # Procura pelo padrão "Nome do dispositivo" entre aspas
                match = re.search(r'"([^"]+)"', line)
                if match:
                    audio_devices.append(match.group(1))

        # Método alternativo: usar o comando PowerShell para listar dispositivos de áudio
        if not audio_devices:
            ps_cmd = "Get-WmiObject Win32_SoundDevice | Select-Object -ExpandProperty Name"
            ps_result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                text=True
            )

            if ps_result.returncode == 0:
                audio_devices = [device.strip() for device in ps_result.stdout.split(
                    '\n') if device.strip()]

        # Retorna o primeiro dispositivo encontrado ou None se não encontrar nenhum
        return audio_devices[0] if audio_devices else None

    except Exception as e:
        print(f"Erro ao listar dispositivos: {e}")
        return None


@bot.command()
async def gravar(ctx):
    """Inicia a gravação de áudio no canal de voz"""
    if not ctx.voice_client:
        await ctx.send("O bot não está conectado a nenhum canal de voz. Use !entrar primeiro.")
        return

    guild_id = ctx.guild.id

    # Verifica se já está gravando neste servidor
    if guild_id in recording_data:
        await ctx.send("Já existe uma gravação em andamento neste servidor.")
        return

    # Cria um nome de arquivo único com timestamp
    timestamp = int(time.time())
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"audios/gravacao_{guild_id}_{date_str}.wav"

    # Obtém o dispositivo de áudio preferencial (Fifine ou dispositivo padrão)
    audio_device = get_default_audio_device()

    # Se não conseguir obter o dispositivo preferencial, tenta o método antigo
    if not audio_device:
        audio_device = get_first_audio_device()

    if not audio_device:
        await ctx.send("Não foi possível encontrar nenhum dispositivo de áudio. Verifique se há dispositivos de áudio disponíveis.")
        return

    # Inicia a gravação usando ffmpeg
    try:
        # Comando para iniciar a gravação do áudio do sistema
        # Se o dispositivo contém caracteres especiais, usa o nome alternativo
        if "@device_cm_" in audio_device:
            # Usando o nome alternativo do dispositivo
            process = subprocess.Popen([
                "ffmpeg",
                "-f", "dshow",  # Para Windows
                # Usando o nome alternativo do dispositivo
                "-i", f"audio={audio_device}",
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                filename
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            # Usando o nome normal do dispositivo
            process = subprocess.Popen([
                "ffmpeg",
                "-f", "dshow",  # Para Windows
                # Usando o dispositivo disponível
                "-i", f"audio={audio_device}",
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                filename
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        recording_data[guild_id] = {
            "process": process,
            "filename": filename,
            "start_time": timestamp,
            "audio_device": audio_device
        }

        await ctx.send(f"Gravação iniciada! Use !parar para finalizar e salvar o arquivo.\n\nNota: Usando o dispositivo '{audio_device}' para capturar o áudio.")
    except Exception as e:
        await ctx.send(f"Erro ao iniciar gravação: {str(e)}\n\nVerifique se o dispositivo de áudio '{audio_device}' está disponível.")


@bot.command()
async def parar(ctx):
    """Para a gravação de áudio e salva o arquivo .wav"""
    guild_id = ctx.guild.id

    if guild_id not in recording_data:
        await ctx.send("Não há gravação em andamento neste servidor.")
        return

    try:
        # Obtém os dados da gravação
        rec_data = recording_data[guild_id]
        process = rec_data["process"]
        filename = rec_data["filename"]

        # Encerra o processo do ffmpeg (envia q para sair)
        process.communicate(input=b'q')
        process.terminate()

        # Calcula a duração da gravação
        duration = time.time() - rec_data["start_time"]
        duration_str = f"{int(duration // 60)}m {int(duration % 60)}s"

        # Verifica se o arquivo de áudio foi criado com sucesso
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            # Cria também um arquivo de texto com informações sobre a gravação
            txt_filename = filename.replace(".wav", ".txt")
            try:
                with open(txt_filename, "w") as f:
                    f.write(
                        f"Áudio gravado\nDuração: {duration_str}\nDispositivo: {rec_data.get('audio_device', 'Desconhecido')}\nData: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
            except Exception as write_error:
                print(
                    f"Erro ao salvar arquivo de informações: {str(write_error)}")

            await ctx.send(f"Gravação finalizada! Duração: {duration_str}\nArquivo salvo como: {filename}")
        else:
            await ctx.send(
                f"Aviso: O arquivo de áudio parece estar vazio ou não foi criado corretamente.\nVerifique se o dispositivo '{rec_data.get('audio_device', 'Desconhecido')}' está capturando áudio."
            )

        # Remove do dicionário de gravações
        del recording_data[guild_id]
    except Exception as e:
        await ctx.send(f"Erro ao parar gravação: {str(e)}")


@bot.command()
async def sair(ctx):
    """Sai do canal de voz"""
    guild_id = ctx.guild.id

    # Se estiver gravando, para a gravação primeiro
    if guild_id in recording_data:
        try:
            rec_data = recording_data[guild_id]
            process = rec_data["process"]
            process.communicate(input=b'q')
            process.terminate()
            del recording_data[guild_id]
        except Exception as e:
            await ctx.send(f"Erro ao finalizar gravação: {str(e)}")

    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Desconectado do canal de voz.")
    else:
        await ctx.send("O bot não está conectado a nenhum canal de voz.")


@bot.command()
async def listar(ctx):
    """Lista todos os arquivos de gravação disponíveis"""
    files = os.listdir("audios")
    if files:
        file_list = "\n".join(files)
        await ctx.send(f"Arquivos de gravação disponíveis:\n```{file_list}```")
    else:
        await ctx.send("Não há arquivos de gravação disponíveis.")


# Iniciar o bot usando o token do arquivo .env
bot.run(os.getenv("DISCORD_TOKEN"))
