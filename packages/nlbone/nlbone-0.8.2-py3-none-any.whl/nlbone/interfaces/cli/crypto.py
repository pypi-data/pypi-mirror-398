import typer

from nlbone.utils.crypto import decrypt_text, encrypt_text

crypto_command = typer.Typer(help="Encryption / Decryption utilities")


@crypto_command.command("encrypt")
def encrypt_cmd(value: str):
    """Encrypt a plain text string."""
    encrypted = encrypt_text(value)
    typer.secho(f"🔐 Encrypted:\n{encrypted}", fg=typer.colors.GREEN)


@crypto_command.command("decrypt")
def decrypt_cmd(value: str):
    """Decrypt an encrypted token string."""
    try:
        decrypted = decrypt_text(value)
        typer.secho(f"🔓 Decrypted:\n{decrypted}", fg=typer.colors.CYAN)
    except Exception as e:
        typer.secho(f"❌ Failed to decrypt: {e}", fg=typer.colors.RED)
