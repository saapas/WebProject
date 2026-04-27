import os
import json
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
API_BASE = os.getenv("WORDLE_API_BASE_URL", "http://127.0.0.1:5000")
STAT_API_BASE = os.getenv("STAT_API_BASE_URL", "http://127.0.0.1:5001")
MAP_FILE = "discord-bot/user_map.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

def load_map():
    """Load persisted Discord-to-API account mapping."""
    try:
        with open(MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        save_map({})
        return {}

def save_map(data):
    """Persist Discord-to-API account mapping to disk."""
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _normalize_account_state(raw_state):
    """Normalize legacy and current account-state formats."""
    if raw_state is None:
        return None
    if isinstance(raw_state, dict):
        user_id = raw_state.get("user_id")
        if user_id is None:
            return None
        return {
            "user_id": int(user_id),
            "active_game_id": raw_state.get("active_game_id"),
        }
    return {"user_id": int(raw_state), "active_game_id": None}


def get_account_state(discord_user_id: int):
    """Get normalized account state for a Discord user."""
    mapping = load_map()
    return _normalize_account_state(mapping.get(str(discord_user_id)))


def set_account_state(discord_user_id: int, account_state):
    """Save account state for a Discord user."""
    mapping = load_map()
    mapping[str(discord_user_id)] = account_state
    save_map(mapping)


def clear_active_game(discord_user_id: int):
    """Clear the tracked active game for a Discord user."""
    account_state = get_account_state(discord_user_id)
    if not account_state:
        return
    account_state["active_game_id"] = None
    set_account_state(discord_user_id, account_state)

async def api_request(method, path, payload=None, base_url=None):
    """Send an HTTP request to the configured API service."""
    base = base_url or API_BASE
    url = f"{base}{path}"
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, json=payload) as resp:
            text = await resp.text()
            if resp.status >= 400:
                return None, f"{resp.status}: {text}"
            if text:
                return await resp.json(), None
            return {}, None


def get_registered_user_id(discord_user_id: int):
    """Return mapped API user id for a Discord user."""
    account_state = get_account_state(discord_user_id)
    if not account_state:
        return None
    return account_state["user_id"]


def get_discord_id_for_api_user(api_user_id: int):
    """Resolve a Discord user id from an API user id mapping."""
    mapping = load_map()
    for discord_id, raw_state in mapping.items():
        account_state = _normalize_account_state(raw_state)
        if not account_state:
            continue
        if account_state["user_id"] == api_user_id:
            return int(discord_id)
    return None


def format_feedback(feedback: str):
    """Convert G/Y/X feedback letters into emoji squares."""
    mapping = {
        "G": ":green_square:",
        "Y": ":yellow_square:",
        "X": ":black_large_square:",
    }
    return "".join(mapping.get(char, char) for char in feedback)

@bot.event
async def on_ready():
    """Sync slash commands when the bot is ready."""
    await tree.sync()
    print(f"Logged in as {bot.user}")

@tree.command(name="register", description="Register your Wordle API user")
@app_commands.describe(username="Max 10 chars, letters/numbers recommended")
async def register(interaction: discord.Interaction, username: str):
    """Register the invoking Discord user with the Wordle API."""
    account_state = get_account_state(interaction.user.id)
    if account_state:
        await interaction.response.send_message("This Discord account is already registered.", ephemeral=True)
        return

    data, err = await api_request("POST", "/api/users", {"username": username})
    if err:
        await interaction.response.send_message(f"Register failed: {err}", ephemeral=True)
        return

    users, err2 = await api_request("GET", "/api/users")
    if err2:
        await interaction.response.send_message(f"Created user, but failed to fetch id: {err2}", ephemeral=True)
        return

    user = next((u for u in users if u.get("username") == username), None)
    if not user:
        await interaction.response.send_message("User created but not found in list.", ephemeral=True)
        return

    set_account_state(interaction.user.id, {"user_id": user["id"], "active_game_id": None})
    await interaction.response.send_message(f"Registered as {username} (api user id {user['id']})")

@tree.command(name="newgame", description="Create a new game")
@app_commands.describe(mode="day or inf")
async def newgame(interaction: discord.Interaction, mode: str):
    """Create a new game for the invoking user."""
    mode = mode.lower()
    if mode not in {"day", "inf"}:
        await interaction.response.send_message("Mode must be day or inf", ephemeral=True)
        return

    account_state = get_account_state(interaction.user.id)
    if not account_state:
        await interaction.response.send_message("You need /register first.", ephemeral=True)
        return

    api_user_id = account_state["user_id"]

    if mode == "day":
        games, games_err = await api_request("GET", "/api/games")
        if games_err:
            await interaction.response.send_message(f"Could not verify day-game limit: {games_err}", ephemeral=True)
            return
        if any(g.get("user_id") == api_user_id and g.get("mode") == "day" for g in games):
            await interaction.response.send_message(
                "You have already played the daily game and cannot start another day-mode game.",
                ephemeral=True,
            )
            return

    active_game_id = account_state.get("active_game_id")
    if active_game_id is not None:
        active_game, active_err = await api_request("GET", f"/api/games/{active_game_id}")
        if active_err:
            clear_active_game(interaction.user.id)
        else:
            if not (active_game.get("won") or active_game.get("attempts", 0) >= 6):
                await interaction.response.send_message(
                    f"You already have an active game (id {active_game_id}). Finish it before starting a new one.",
                    ephemeral=True,
                )
                return
            clear_active_game(interaction.user.id)

    _, err = await api_request("POST", "/api/games", {"user_id": api_user_id, "mode": mode})
    if err:
        await interaction.response.send_message(f"Create game failed: {err}", ephemeral=True)
        return

    games, err2 = await api_request("GET", "/api/games")
    if err2:
        await interaction.response.send_message(f"Game created, but listing failed: {err2}")
        return

    mine = [g for g in games if g["user_id"] == api_user_id]
    newest = max(mine, key=lambda g: g["id"]) if mine else None
    if not newest:
        await interaction.response.send_message("Game created, but could not determine id.")
        return

    account_state["active_game_id"] = newest["id"]
    set_account_state(interaction.user.id, account_state)
    await interaction.response.send_message(f"Game created: id {newest['id']} mode {newest['mode']}")

@tree.command(name="guess", description="Submit a 5-letter guess")
async def guess(interaction: discord.Interaction, word: str):
    """Submit a guess to the invoking user's active game."""
    account_state = get_account_state(interaction.user.id)
    if not account_state:
        await interaction.response.send_message("You need /register first.", ephemeral=True)
        return

    api_user_id = account_state["user_id"]
    active_game_id = account_state.get("active_game_id")
    if active_game_id is None:
        await interaction.response.send_message("You do not have an active game. Use /newgame first.", ephemeral=True)
        return

    game, game_err = await api_request("GET", f"/api/games/{active_game_id}")
    if game_err:
        clear_active_game(interaction.user.id)
        await interaction.response.send_message("Your active game is no longer available. Start a new one with /newgame.", ephemeral=True)
        return

    if game.get("user_id") != api_user_id:
        await interaction.response.send_message("That active game does not belong to you.", ephemeral=True)
        return

    previous_guesses, history_err = await api_request("GET", f"/api/games/{active_game_id}/guesses")
    if history_err:
        await interaction.response.send_message(f"Could not load guess history: {history_err}", ephemeral=True)
        return

    word = word.lower().strip()
    data, err = await api_request("POST", f"/api/games/{active_game_id}/guesses", {"guessed_word": word})
    if err:
        await interaction.response.send_message(f"Guess failed: {err}", ephemeral=True)
        return

    updated_game, updated_err = await api_request("GET", f"/api/games/{active_game_id}")
    if updated_err:
        updated_game = game

    if updated_game.get("won") or updated_game.get("attempts", 0) >= 6:
        clear_active_game(interaction.user.id)

    response_lines = ["Guesses:"]
    for guess_item in previous_guesses:
        response_lines.append(
            f"{guess_item['guessed_word']} -> {format_feedback(guess_item['feedback'])}"
        )
    response_lines.append(f"{data['guessed_word']} -> {format_feedback(data['feedback'])}")
    if data.get("feedback") == "GGGGG":
        response_lines.append(f"You won! {data['guessed_word']} was correct!")

    await interaction.response.send_message("\n".join(response_lines))

@tree.command(name="leaderboard", description="Top players")
async def leaderboard(interaction: discord.Interaction):
    """Show top leaderboard entries from the stats service."""
    data, err = await api_request("GET", "/stats/leaderboard", base_url=STAT_API_BASE)
    if err:
        await interaction.response.send_message(f"Leaderboard failed: {err}", ephemeral=True)
        return

    if not data:
        await interaction.response.send_message("No leaderboard data yet.")
        return

    lines = []
    for i, row in enumerate(data[:10]):
        api_user_id = row.get("wordle_user_id")
        discord_id = get_discord_id_for_api_user(api_user_id)
        player_label = f"user {api_user_id}"

        if discord_id is not None:
            member = interaction.guild.get_member(discord_id) if interaction.guild else None
            if member is not None:
                player_label = member.display_name
            else:
                cached_user = bot.get_user(discord_id)
                if cached_user is not None:
                    player_label = cached_user.name
                else:
                    try:
                        fetched_user = await bot.fetch_user(discord_id)
                        player_label = fetched_user.name
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                        pass
        else:
            user_data, user_err = await api_request("GET", f"/api/users/{api_user_id}")
            if not user_err and user_data:
                player_label = user_data.get("username", f"user {api_user_id}")

        lines.append(f"{i+1}. {player_label} score {row.get('score')}")
    await interaction.response.send_message("\n".join(lines))


@tree.command(name="stats", description="Show player stats")
@app_commands.describe(member="Optional Discord member to view stats for")
async def stats(interaction: discord.Interaction, member: discord.Member | None = None):
    """Show stats for the invoking user or an optional member."""
    target_member = member or interaction.user
    account_state = get_account_state(target_member.id)
    if not account_state:
        if member is None:
            await interaction.response.send_message("You need /register first.", ephemeral=True)
        else:
            await interaction.response.send_message("That member is not registered with the bot yet.", ephemeral=True)
        return

    api_user_id = account_state["user_id"]
    data, err = await api_request("GET", f"/stats/{api_user_id}/", base_url=STAT_API_BASE)
    if err:
        await interaction.response.send_message(f"Stats failed: {err}", ephemeral=True)
        return

    lines = [
        f"Stats for {target_member.display_name} (user {data.get('wordle_user_id', api_user_id)})",
        f"Total games: {data.get('total_games', 0)}",
        f"Total wins: {data.get('total_wins', 0)}",
        f"Average guesses: {data.get('avg_guesses', 0.0)}",
    ]
    await interaction.response.send_message("\n".join(lines))

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is missing")
    bot.run(DISCORD_TOKEN)
