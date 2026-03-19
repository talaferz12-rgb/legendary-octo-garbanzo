import discord
from discord.ext import commands
import random
import asyncio
import json
import os
from datetime import datetime, date

# 
#   🔥 بوت أكاديمية Lucifer العسكرية
#    ضع TOKEN بوتك هنا 
#    ضع ID قناة الترحيب هنا 
#    ضع رابط صورة Lucifer هنا 
# 

TOKEN          = "ضع_توكن_بوتك_هنا"
WELCOME_CH_ID  = 0          #  ID قناة الترحيب (رقم فقط)
LUCIFER_IMG    = "https://i.imgur.com/ضع_رابط_الصورة_هنا.png"  #  رابط صورة Lucifer

# ألوان Lucifer الذهبية
C_GOLD   = 0xF5A623   # ذهبي برتقالي
C_DARK   = 0x1A1208   # أسود داكن
C_FIRE   = 0xFF6B00   # برتقالي ناري
C_WHITE  = 0xFFFFFF

# 
#   قاعدة البيانات
# 

DATA_FILE    = "players_data.json"
CONFIG_FILE  = "config.json"
HISTORY_FILE = "match_history.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "disabled_games": [],
        "vip_roles": [],
        "vip_games": ["ريبلكا_vip", "مافيا_vip"],
        "tournament_active": False,
    }

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(h):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(h[-500:], f, ensure_ascii=False, indent=2)  # آخر 500 مباراة

def add_match(game_type, winner_name, players_names, guild_id):
    h = load_history()
    h.append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "game": game_type,
        "winner": winner_name,
        "players": players_names,
        "guild": str(guild_id)
    })
    save_history(h)

def get_player(uid):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = {
            "coins": 200, "points": 0, "wins": 0,
            "games": 0, "level": 1, "vip": False,
            "last_daily": "", "tournament_wins": 0,
            "xp": 0
        }
        save_data(data)
    return data[uid]

def update_player(uid, **kw):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = {
            "coins": 200, "points": 0, "wins": 0,
            "games": 0, "level": 1, "vip": False,
            "last_daily": "", "tournament_wins": 0,
            "xp": 0
        }
    for k, v in kw.items():
        if k == "vip":
            data[uid][k] = v
        else:
            data[uid][k] = data[uid].get(k, 0) + v
    # حساب المستوى من XP
    xp = data[uid].get("xp", 0)
    data[uid]["level"] = max(1, xp // 200 + 1)
    save_data(data)

def is_vip(uid):
    p = get_player(uid)
    return p.get("vip", False)

def is_game_enabled(game_name):
    cfg = load_config()
    return game_name not in cfg.get("disabled_games", [])

active_games   = {}
tournaments    = {}   # guild_id  tournament state
challenges     = {}   # "{uid1}_{uid2}"  challenge state

def pl_text(players: dict) -> str:
    if not players:
        return "لا يوجد لاعبون بعد"
    return "\n".join(f"• {u.display_name}" for u in players.values())

# 
#   إعداد البوت
# 

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", help_command=None, intents=intents)

# 
#   Embed مخصص بتصميم Lucifer
# 

def lucifer_embed(title="", desc="", color=C_GOLD, footer=True):
    """Embed بتصميم Lucifer الذهبي"""
    e = discord.Embed(title=title, description=desc, color=color)
    if footer:
        e.set_footer(
            text="⚔️ أكاديمية Lucifer العسكرية • discord.gg/lf1",
            icon_url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else None
        )
    return e

def game_embed(title, desc, game_emoji="🎮"):
    """Embed للعبة بتصميم موحّد"""
    e = discord.Embed(
        title=f"{game_emoji}  {title}",
        description=desc,
        color=C_GOLD
    )
    e.set_thumbnail(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
    e.set_footer(text="⚔️ Lucifer Gaming • discord.gg/lf1")
    return e

# 
#   🎉 ترحيب بالأعضاء الجدد — تصميم Lucifer
# 

@bot.event
async def on_member_join(member):
    if not WELCOME_CH_ID:
        return
    ch = member.guild.get_channel(WELCOME_CH_ID)
    if not ch:
        return

    embed = discord.Embed(
        title=f"🔥  مرحباً بك في Lucifer!",
        description=(
            f"### {member.mention} انضم إلى الأكاديمية!\n\n"
            f"\n"
            f"⚔️ **السيرفر:** {member.guild.name}\n"
            f"👥 **عدد الأعضاء:** {member.guild.member_count}\n"
            f"🪙 **رصيدك الابتدائي:** 200 عملة\n"
            f"\n\n"
            f"استخدم `!مساعدة` لمعرفة الأوامر\n"
            f"العب الألعاب واكسب عملات ونقاط! 🎮"
        ),
        color=C_GOLD
    )
    embed.set_image(url=LUCIFER_IMG)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="⚔️ Lucifer Gaming • discord.gg/lf1")
    await ch.send(embed=embed)

# 
#   أحداث البوت
# 

@bot.event
async def on_ready():
    print(f"✅ البوت يعمل: {bot.user.name} ({bot.user.id})")
    active_games.clear()
    print("تم مسح الالعاب العالقة")
    await bot.change_presence(activity=discord.Game(name="🔥 Lucifer Gaming | !مساعدة"))

# 
#   🛡️ أوامر الإدارة
# 

def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

@bot.command(name="تفعيل")
async def enable_game(ctx, game: str = None):
    if not is_admin(ctx):
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "هذا الأمر للأدمن فقط!", C_FIRE))
    if not game:
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "استخدم: `!تفعيل اسم_اللعبة`", C_FIRE))
    cfg = load_config()
    if game in cfg["disabled_games"]:
        cfg["disabled_games"].remove(game)
        save_config(cfg)
        await ctx.send(embed=lucifer_embed("✅ تم التفعيل", f"تم تفعيل لعبة **{game}**!", C_GOLD))
    else:
        await ctx.send(embed=lucifer_embed("⚠️ تنبيه", f"لعبة **{game}** مفعّلة أصلاً.", C_FIRE))

@bot.command(name="تعطيل")
async def disable_game(ctx, game: str = None):
    if not is_admin(ctx):
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "هذا الأمر للأدمن فقط!", C_FIRE))
    if not game:
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "استخدم: `!تعطيل اسم_اللعبة`", C_FIRE))
    cfg = load_config()
    if game not in cfg["disabled_games"]:
        cfg["disabled_games"].append(game)
        save_config(cfg)
        await ctx.send(embed=lucifer_embed("🔒 تم التعطيل", f"تم تعطيل لعبة **{game}**!", C_FIRE))
    else:
        await ctx.send(embed=lucifer_embed("⚠️ تنبيه", f"لعبة **{game}** معطّلة أصلاً.", C_FIRE))

@bot.command(name="الألعاب_المعطلة")
async def show_disabled(ctx):
    cfg = load_config()
    disabled = cfg.get("disabled_games", [])
    if not disabled:
        await ctx.send(embed=lucifer_embed("✅ الحالة", "جميع الألعاب مفعّلة!", C_GOLD))
    else:
        await ctx.send(embed=lucifer_embed("🔒 ألعاب معطّلة", "\n".join(f"• {g}" for g in disabled), C_FIRE))

@bot.command(name="منح_vip")
async def grant_vip(ctx, member: discord.Member = None):
    if not is_admin(ctx):
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "للأدمن فقط!", C_FIRE))
    if not member:
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "استخدم: `!منح_vip @عضو`", C_FIRE))
    update_player(member.id, vip=True)
    embed = lucifer_embed("👑 VIP", f"تم منح **{member.display_name}** صلاحية VIP! 👑", C_GOLD)
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="سحب_vip")
async def revoke_vip(ctx, member: discord.Member = None):
    if not is_admin(ctx):
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "للأدمن فقط!", C_FIRE))
    if not member:
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "استخدم: `!سحب_vip @عضو`", C_FIRE))
    update_player(member.id, vip=False)
    await ctx.send(embed=lucifer_embed("🔒 VIP", f"تم سحب VIP من **{member.display_name}**", C_FIRE))

@bot.command(name="منح_عملات")
async def give_coins(ctx, member: discord.Member = None, amount: int = 0):
    if not is_admin(ctx):
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "للأدمن فقط!", C_FIRE))
    if not member or amount <= 0:
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "استخدم: `!منح_عملات @عضو الكمية`", C_FIRE))
    update_player(member.id, coins=amount)
    await ctx.send(embed=lucifer_embed("🪙 عملات", f"تم منح **{member.display_name}** {amount} 🪙", C_GOLD))

# 
#   📅 تذكّر يومي
# 

@bot.command(name="يومي", aliases=["daily"])
async def daily_cmd(ctx):
    uid = str(ctx.author.id)
    p = get_player(uid)
    today = str(date.today())
    if p.get("last_daily") == today:
        embed = lucifer_embed(
            "⏳ انتظر!", 
            f"{ctx.author.mention} استلمت مكافأتك اليومية بالفعل!\nعود غداً 🌙",
            C_FIRE
        )
        return await ctx.send(embed=embed)
    reward = random.randint(50, 200)
    data = load_data()
    data[uid]["last_daily"] = today
    data[uid]["coins"] = data[uid].get("coins", 0) + reward
    save_data(data)
    embed = lucifer_embed(
        "🎁 المكافأة اليومية!",
        f"{ctx.author.mention} حصلت على **{reward} 🪙** اليوم!\n\nرصيدك الكلي: **{data[uid]['coins']} 🪙**",
        C_GOLD
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# 
#   📊 الملف الشخصي
# 

@bot.command(name="ملفي")
async def profile_cmd(ctx, member: discord.Member = None):
    target = member or ctx.author
    p = get_player(target.id)
    lvl  = p.get("level", 1)
    xp   = p.get("xp", 0)
    next_xp = lvl * 200
    filled = min(int((xp % 200) / 200 * 10), 10)
    bar  = "█" * filled + "░" * (10 - filled)
    vip_badge = " 👑 VIP" if p.get("vip") else ""
    embed = discord.Embed(
        title=f"⚔️  ملف {target.display_name}{vip_badge}",
        color=C_GOLD
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.set_image(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
    embed.add_field(name="🪙 عملات",       value=f"**{p.get('coins',0)}**",          inline=True)
    embed.add_field(name="⭐ نقاط",        value=f"**{p.get('points',0)}**",          inline=True)
    embed.add_field(name="🏆 انتصارات",    value=f"**{p.get('wins',0)}**",            inline=True)
    embed.add_field(name="🎮 ألعاب",       value=f"**{p.get('games',0)}**",           inline=True)
    embed.add_field(name="🥇 بطولات",      value=f"**{p.get('tournament_wins',0)}**", inline=True)
    embed.add_field(name=f"📊 المستوى {lvl}", value=f"`{bar}` {xp%200}/{next_xp} XP", inline=False)
    embed.set_footer(text="⚔️ Lucifer Gaming • discord.gg/lf1")
    await ctx.send(embed=embed)

# 
#   🏆 الترتيب
# 

@bot.command(name="ترتيب")
async def leaderboard_cmd(ctx):
    data = load_data()
    if not data:
        return await ctx.send(embed=lucifer_embed("❌", "لا يوجد لاعبون بعد!"))
    top = sorted(data.items(), key=lambda x: x[1].get("points", 0), reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"] + ["🔸"] * 7
    desc = ""
    for i, (uid, stats) in enumerate(top):
        try:
            user = await bot.fetch_user(int(uid))
            name = user.display_name
        except Exception:
            name = f"لاعب#{uid[-4:]}"
        vip = " 👑" if stats.get("vip") else ""
        desc += f"{medals[i]} **{name}**{vip} — {stats.get('points',0)} نقطة\n"
    embed = lucifer_embed("🏆  أفضل اللاعبين", desc, C_GOLD)
    embed.set_image(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
    await ctx.send(embed=embed)

# 
#   📜 سجل المباريات
# 

@bot.command(name="سجل", aliases=["مباريات"])
async def history_cmd(ctx):
    h = load_history()
    guild_h = [m for m in h if m.get("guild") == str(ctx.guild.id)][-10:]
    if not guild_h:
        return await ctx.send(embed=lucifer_embed("📜 السجل", "لا توجد مباريات مسجّلة بعد!", C_FIRE))
    desc = ""
    for m in reversed(guild_h):
        players_str = ", ".join(m.get("players", [])[:4])
        desc += f"**{m['game']}** — 🏆 {m['winner']} | {m['date']}\n {players_str}\n\n"
    embed = lucifer_embed("📜  آخر 10 مباريات", desc, C_GOLD)
    await ctx.send(embed=embed)

# 
#   🛒 المتجر
# 

SHOP_ITEMS = {
    "1": {"name": "🛡️ درع الحماية", "desc": "حماية جولة واحدة",      "price": 100},
    "2": {"name": "⚡ وقت إضافي",   "desc": "30 ثانية إضافية",        "price": 150},
    "3": {"name": "🎭 دور مخفي",    "desc": "دور سري في المافيا",      "price": 200},
    "4": {"name": "🎯 تغيير الحرف", "desc": "إعادة سحب حرف عشوائي",  "price": 80},
    "5": {"name": "🔥 XP مضاعف",   "desc": "XP مضاعف للعبة القادمة", "price": 300},
}

class ShopView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user
        for num, item in SHOP_ITEMS.items():
            btn = discord.ui.Button(
                label=f"{item['name']} — {item['price']}🪙",
                style=discord.ButtonStyle.secondary
            )
            btn.callback = self._make_buy(num)
            self.add_item(btn)

    def _make_buy(self, num):
        async def cb(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                return await interaction.response.send_message("❌ هذا المتجر ليس لك!", ephemeral=True)
            item = SHOP_ITEMS[num]
            p = get_player(interaction.user.id)
            if p["coins"] < item["price"]:
                return await interaction.response.send_message(
                    f"❌ رصيدك {p['coins']}🪙 وتحتاج {item['price']}🪙", ephemeral=True)
            update_player(interaction.user.id, coins=-item["price"])
            await interaction.response.send_message(
                f"✅ اشتريت **{item['name']}**! رصيدك: {p['coins']-item['price']}🪙", ephemeral=True)
        return cb

@bot.command(name="متجر")
async def shop_cmd(ctx):
    p = get_player(ctx.author.id)
    embed = lucifer_embed("🛒  متجر Lucifer", f"🪙 رصيدك: **{p['coins']} عملة**\n\nاضغط على العنصر لشرائه مباشرة!")
    embed.set_image(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
    await ctx.send(embed=embed, view=ShopView(ctx.author))

# 
#   ⚔️ تحدي 1v1
# 

CHALLENGE_GAMES = ["سرعة", "سؤال", "عد_للعشرة"]

class ChallengeAcceptView(discord.ui.View):
    def __init__(self, challenger, challenged, game, bet):
        super().__init__(timeout=30)
        self.challenger = challenger
        self.challenged = challenged
        self.game = game
        self.bet = bet
        self.accepted = False

    @discord.ui.button(label="✅ قبول التحدي", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.challenged.id:
            return await interaction.response.send_message("❌ هذا التحدي ليس لك!", ephemeral=True)
        self.accepted = True
        for c in self.children:
            c.disabled = True
        await interaction.response.edit_message(
            embed=lucifer_embed("⚔️ قُبل التحدي!", f"**{self.challenged.display_name}** قبل! تبدأ اللعبة...", C_GOLD),
            view=self
        )
        self.stop()

    @discord.ui.button(label="❌ رفض", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.challenged.id:
            return await interaction.response.send_message("❌ هذا التحدي ليس لك!", ephemeral=True)
        for c in self.children:
            c.disabled = True
        await interaction.response.edit_message(
            embed=lucifer_embed("❌ رُفض التحدي", f"**{self.challenged.display_name}** رفض التحدي.", C_FIRE),
            view=self
        )
        self.stop()

async def run_1v1_speed(channel, p1, p2, bet):
    """تحدي سرعة 1v1"""
    SPEED_WORDS = ["أكاديمية","ديسكورد","لوسيفر","عسكرية","بطولة","مسابقة","انتصار","لاعبون"]
    word = random.choice(SPEED_WORDS)
    embed = lucifer_embed(
        "⚔️ تحدي السرعة 1v1",
        f"{p1.mention} **VS** {p2.mention}\n\nأول من يكتب:\n## `{word}`\n\n⏱️ **30 ثانية!**",
        C_GOLD
    )
    await channel.send(embed=embed)

    winner = None
    def check(m):
        return m.channel == channel and m.author.id in [p1.id, p2.id] and m.content.strip() == word

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)
        winner = msg.author
    except asyncio.TimeoutError:
        pass

    if winner:
        loser = p2 if winner.id == p1.id else p1
        update_player(winner.id, wins=1, points=30, coins=bet*2, xp=50, games=1)
        update_player(loser.id, coins=-bet, games=1)
        embed2 = lucifer_embed(
            "🏆 نتيجة التحدي",
            f"🥇 **{winner.display_name}** فاز في تحدي السرعة!\n💰 ربح **{bet*2} 🪙**",
            C_GOLD
        )
        add_match("تحدي_سرعة", winner.display_name, [p1.display_name, p2.display_name], channel.guild.id)
        await channel.send(embed=embed2)
    else:
        embed2 = lucifer_embed("⏰ انتهى الوقت!", "تعادل! لم يكتب أحد الكلمة.", C_FIRE)
        await channel.send(embed=embed2)

async def run_1v1_trivia(channel, p1, p2, bet):
    """تحدي أسئلة 1v1"""
    TRIVIA = [
        {"q": "ما عاصمة فرنسا؟",             "a": "باريس"},
        {"q": "كم عدد أضلاع المثلث؟",         "a": "3"},
        {"q": "ما أسرع حيوان بري؟",           "a": "الفهد"},
        {"q": "كم كوكب في المجموعة الشمسية؟", "a": "8"},
        {"q": "ما عاصمة اليابان؟",            "a": "طوكيو"},
        {"q": "ما أطول نهر في العالم؟",        "a": "النيل"},
        {"q": "كم ساعة في اليوم؟",            "a": "24"},
        {"q": "ما أكبر كوكب في المجموعة؟",    "a": "المشتري"},
    ]
    scores = {p1.id: 0, p2.id: 0}

    for i in range(5):
        q = random.choice(TRIVIA)
        embed = lucifer_embed(
            f"🧠 سؤال {i+1}/5 — تحدي",
            f"{p1.mention} **VS** {p2.mention}\n\n**{q['q']}**\n\n⏱️ 15 ثانية",
            C_GOLD
        )
        await channel.send(embed=embed)

        def check(m):
            return m.channel == channel and m.author.id in [p1.id, p2.id] and q["a"] in m.content

        try:
            msg = await bot.wait_for("message", check=check, timeout=15)
            scores[msg.author.id] += 1
            await channel.send(f"✅ **{msg.author.display_name}** أجاب صح! (+1 نقطة)")
        except asyncio.TimeoutError:
            await channel.send(f"⏰ الجواب: **{q['a']}**")
        await asyncio.sleep(2)

    if scores[p1.id] > scores[p2.id]:
        winner, loser = p1, p2
    elif scores[p2.id] > scores[p1.id]:
        winner, loser = p2, p1
    else:
        embed = lucifer_embed("🤝 تعادل!", f"النتيجة: {p1.display_name} {scores[p1.id]} — {scores[p2.id]} {p2.display_name}", C_FIRE)
        return await channel.send(embed=embed)

    update_player(winner.id, wins=1, points=30, coins=bet*2, xp=50, games=1)
    update_player(loser.id, coins=-bet, games=1)
    w_score = scores[winner.id]
    l_score = scores[loser.id]
    embed = lucifer_embed(
        "🏆 نتيجة التحدي",
        f"🥇 **{winner.display_name}** فاز بالتحدي!\n📊 النتيجة: {w_score} — {l_score}\n💰 ربح **{bet*2} 🪙**",
        C_GOLD
    )
    add_match("تحدي_أسئلة", winner.display_name, [p1.display_name, p2.display_name], channel.guild.id)
    await channel.send(embed=embed)

@bot.command(name="تحدي", aliases=["1v1"])
async def challenge_cmd(ctx, opponent: discord.Member = None, game: str = "سرعة", bet: int = 50):
    if not opponent:
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "استخدم: `!تحدي @لاعب [سرعة/سؤال] [الرهان]`", C_FIRE))
    if opponent.id == ctx.author.id:
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "لا تتحدى نفسك!", C_FIRE))
    if opponent.bot:
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "لا تتحدى البوت!", C_FIRE))

    p1 = get_player(ctx.author.id)
    p2 = get_player(opponent.id)
    if p1["coins"] < bet:
        return await ctx.send(embed=lucifer_embed("❌ رصيد", f"رصيدك {p1['coins']}🪙 وتحتاج {bet}🪙", C_FIRE))
    if p2["coins"] < bet:
        return await ctx.send(embed=lucifer_embed("❌ رصيد", f"رصيد {opponent.display_name} غير كافٍ!", C_FIRE))

    view = ChallengeAcceptView(ctx.author, opponent, game, bet)
    embed = lucifer_embed(
        "⚔️ تحدي جديد!",
        f"**{ctx.author.mention}** يتحدى **{opponent.mention}**!\n\n"
        f"🎮 اللعبة: **{game}**\n💰 الرهان: **{bet} 🪙** لكل طرف\n\n"
        f"عندك **30 ثانية** للرد!",
        C_GOLD
    )
    msg = await ctx.send(embed=embed, view=view)
    await view.wait()

    if view.accepted:
        if game == "سرعة":
            await run_1v1_speed(ctx.channel, ctx.author, opponent, bet)
        elif game == "سؤال":
            await run_1v1_trivia(ctx.channel, ctx.author, opponent, bet)
        else:
            await ctx.send(embed=lucifer_embed("❌ خطأ", f"اللعبة **{game}** غير متوفرة للتحدي. استخدم: سرعة أو سؤال", C_FIRE))

# 
#   🏆 نظام البطولات
# 

class TournamentLobbyView(discord.ui.View):
    def __init__(self, gs):
        super().__init__(timeout=600)
        self.gs = gs

    def make_embed(self):
        gs = self.gs
        n = len(gs["players"])
        prize = gs["prize"]
        embed = discord.Embed(
            title="🏆  بطولة Lucifer",
            description=(
                f"**🎮 نوع البطولة:** {gs['game_type']}\n"
                f"**💰 الجائزة:** {prize} 🪙 للفائز\n"
                f"**👥 اللاعبون:** {n}\n\n"
                f"{pl_text(gs['players'])}"
            ),
            color=C_GOLD
        )
        embed.set_image(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
        embed.set_footer(text=f"👑 المضيف: {gs['host'].display_name} • ⚔️ Lucifer Gaming")
        return embed

    @discord.ui.button(label="دخول البطولة", style=discord.ButtonStyle.success, emoji="🏆", row=0)
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        if gs.get("started"):
            return await interaction.response.send_message("❌ البطولة بدأت!", ephemeral=True)
        if interaction.user.id in gs["players"]:
            return await interaction.response.send_message("⚠️ أنت مسجل!", ephemeral=True)
        gs["players"][interaction.user.id] = interaction.user
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="خروج من البطولة", style=discord.ButtonStyle.danger, emoji="🚪", row=0)
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        uid = interaction.user.id
        if gs.get("started"):
            return await interaction.response.send_message("❌ البطولة بدأت!", ephemeral=True)
        if uid not in gs["players"]:
            return await interaction.response.send_message("⚠️ لست مسجلاً!", ephemeral=True)
        if uid == gs["host"].id:
            return await interaction.response.send_message("❌ المضيف لا يخرج!", ephemeral=True)
        del gs["players"][uid]
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="▶️ ابدأ البطولة", style=discord.ButtonStyle.primary, row=1)
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        if interaction.user.id != gs["host"].id:
            return await interaction.response.send_message("❌ فقط المضيف!", ephemeral=True)
        if gs.get("started"):
            return await interaction.response.send_message("❌ بدأت!", ephemeral=True)
        if len(gs["players"]) < 2:
            return await interaction.response.send_message("❌ تحتاج لاعبَين على الأقل!", ephemeral=True)
        gs["started"] = True
        for c in self.children:
            c.disabled = True
        embed = self.make_embed()
        embed.set_footer(text="🚀 انطلقت البطولة!")
        await interaction.response.edit_message(embed=embed, view=self)
        await run_tournament(interaction.channel, gs)

async def run_tournament(channel, gs):
    """بطولة نوك-أوت — الخاسر يُحذف"""
    players = list(gs["players"].values())
    random.shuffle(players)
    round_num = 1

    embed = lucifer_embed(
        "🏆 انطلقت البطولة!",
        f"**{len(players)} لاعبين** يتنافسون!\n\nتبدأ جولة المواجهات...",
        C_GOLD
    )
    await channel.send(embed=embed)
    await asyncio.sleep(2)

    while len(players) > 1:
        embed = lucifer_embed(
            f"🔥 الجولة {round_num}",
            f"المتبقون: {len(players)} لاعبين\n" + "\n".join(f"• {p.display_name}" for p in players),
            C_FIRE
        )
        await channel.send(embed=embed)
        await asyncio.sleep(2)

        next_round = []
        random.shuffle(players)

        # مباريات زوجية
        for i in range(0, len(players) - 1, 2):
            p1, p2 = players[i], players[i+1]
            # تحدي سرعة سريع
            WORDS = ["نار","ماء","هواء","أرض","سيف","درع","قوة","نصر","مجد","بطل"]
            word = random.choice(WORDS)
            embed = lucifer_embed(
                f"⚔️ مواجهة!",
                f"{p1.mention} **VS** {p2.mention}\n\nاكتب: **`{word}`**\n⏱️ 20 ثانية",
                C_GOLD
            )
            await channel.send(embed=embed)

            winner_match = None
            def check(m):
                return m.channel == channel and m.author.id in [p1.id, p2.id] and m.content.strip() == word
            try:
                msg = await bot.wait_for("message", check=check, timeout=20)
                winner_match = msg.author
            except asyncio.TimeoutError:
                winner_match = random.choice([p1, p2])  # عشوائي عند التعادل

            loser_match = p2 if winner_match.id == p1.id else p1
            next_round.append(winner_match)
            await channel.send(
                embed=lucifer_embed("✅ المتقدم", f"🥊 **{winner_match.display_name}** تقدم!\n💀 {loser_match.display_name} حُذف", C_FIRE)
            )
            await asyncio.sleep(2)

        # لاعب فردي يتأهل مباشرة
        if len(players) % 2 == 1:
            bye_player = players[-1]
            next_round.append(bye_player)
            await channel.send(embed=lucifer_embed("✅ تأهل مباشر", f"**{bye_player.display_name}** تأهل مباشرة!", C_GOLD))

        players = next_round
        round_num += 1
        await asyncio.sleep(3)

    # الفائز
    winner = players[0]
    prize = gs["prize"]
    update_player(winner.id, wins=1, points=100, coins=prize, tournament_wins=1, xp=200, games=1)
    add_match("بطولة", winner.display_name, [u.display_name for u in gs["players"].values()], channel.guild.id)

    embed = discord.Embed(
        title="🏆  بطل البطولة!",
        description=(
            f"## 🥇 {winner.mention}\n\n"
            f"**{winner.display_name}** فاز بالبطولة!\n\n"
            f"💰 جائزة: **{prize} 🪙**\n"
            f"⭐ +100 نقطة\n"
            f"🏆 +1 بطولة في سجله"
        ),
        color=C_GOLD
    )
    embed.set_thumbnail(url=winner.display_avatar.url)
    embed.set_image(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
    embed.set_footer(text="⚔️ Lucifer Gaming • discord.gg/lf1")
    active_games.pop(channel.id, None)
    await channel.send(embed=embed)

@bot.command(name="بطولة")
async def tournament_cmd(ctx, game_type: str = "سرعة", prize: int = 500):
    cid = ctx.channel.id
    if cid in active_games:
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "يوجد لعبة جارية!", C_FIRE))
    gs = {
        "type": "tournament", "host": ctx.author,
        "players": {ctx.author.id: ctx.author},
        "game_type": game_type, "prize": max(100, prize),
        "started": False
    }
    active_games[cid] = gs
    view = TournamentLobbyView(gs)
    await ctx.send(embed=view.make_embed(), view=view)

# 
#   🎭 ريبلكا — 10 فئات + تصميم Lucifer
# 

ARABIC_LETTERS = list("أبتثجحخدذرزسشصضطظعغفقكلمنهوي")
RIPLKA_CATS = ["اسم","حيوان","نبات","دولة","جماد","طعام","مهنة","فيلم","رياضة","مدينة"]

class RiplkaLobbyView(discord.ui.View):
    def __init__(self, gs):
        super().__init__(timeout=600)
        self.gs = gs

    def make_embed(self):
        gs = self.gs
        n = len(gs["players"])
        embed = discord.Embed(title="🎭  ريبلكا", color=C_GOLD)
        embed.set_thumbnail(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
        embed.add_field(name="طريقة اللعب", value=(
            "**1-** اضغط الزر أدناه للدخول إلى اللعبة\n"
            "**2-** يتم اختيار حرف عشوائي كل جولة\n"
            "**3-** لكل فئة من الـ 10 فئات يتم اختيار لاعب عشوائي ليرسل كلمة تبدأ بالحرف\n"
            "**4-** آخر لاعب يفوز فاللعبة"
        ), inline=False)
        embed.add_field(name=f"اللاعبين المشاركين: ({n})", value=pl_text(gs["players"]), inline=False)
        embed.add_field(name="الفئات العشر", value=" | ".join(RIPLKA_CATS), inline=False)
        embed.set_footer(text=f"👑 المضيف: {gs['host'].display_name} • ⚔️ Lucifer Gaming")
        return embed

    @discord.ui.button(label="دخول إلى اللعبة", style=discord.ButtonStyle.success, emoji="🎮", row=0)
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        if gs.get("started"):
            return await interaction.response.send_message("❌ اللعبة بدأت!", ephemeral=True)
        if len(gs["players"]) >= 100:
            return await interaction.response.send_message("❌ اللعبة ممتلئة!", ephemeral=True)
        if interaction.user.id in gs["players"]:
            return await interaction.response.send_message("⚠️ أنت مسجل بالفعل!", ephemeral=True)
        gs["players"][interaction.user.id] = interaction.user
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="اخرج من اللعبة", style=discord.ButtonStyle.danger, emoji="🚪", row=0)
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        if gs.get("started"):
            return await interaction.response.send_message("❌ اللعبة بدأت!", ephemeral=True)
        uid = interaction.user.id
        if uid not in gs["players"]:
            return await interaction.response.send_message("⚠️ لست في اللعبة!", ephemeral=True)
        if uid == gs["host"].id:
            return await interaction.response.send_message("❌ المضيف لا يخرج! استخدم !انهي", ephemeral=True)
        del gs["players"][uid]
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="متجر اللعبة ⚡", style=discord.ButtonStyle.secondary, row=1)
    async def shop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = get_player(interaction.user.id)
        await interaction.response.send_message(
            f"🛒 **متجر Lucifer**\n🪙 رصيدك: **{p['coins']}**\n\n"
            "`1` 🛡️ درع الحماية — 100🪙\n`2` ⚡ وقت إضافي — 150🪙\n"
            "`3` 🎯 تغيير الحرف — 80🪙\n\nاستخدم `!شراء <رقم>`", ephemeral=True)

    @discord.ui.button(label="▶️ ابدأ اللعبة", style=discord.ButtonStyle.primary, row=1)
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        if interaction.user.id != gs["host"].id:
            return await interaction.response.send_message("❌ فقط المضيف!", ephemeral=True)
        if gs.get("started"):
            return await interaction.response.send_message("❌ بدأت بالفعل!", ephemeral=True)
        if len(gs["players"]) < 1:
            return await interaction.response.send_message("❌ لا يوجد لاعبون!", ephemeral=True)
        gs["started"] = True
        for c in self.children: c.disabled = True
        embed = self.make_embed()
        embed.set_footer(text="🚀 انطلقت ريبلكا! • ⚔️ Lucifer Gaming")
        await interaction.response.edit_message(embed=embed, view=self)
        await run_riplka(interaction.channel, gs)

async def run_riplka(channel, gs):
    if not is_game_enabled("ريبلكا"):
        return await channel.send(embed=lucifer_embed("🔒 معطّل", "لعبة ريبلكا معطّلة حالياً!", C_FIRE))
    gs["scores"] = {uid: 0 for uid in gs["players"]}
    max_rounds = gs.get("max_rounds", 5)

    for rnd in range(1, max_rounds + 1):
        if not active_games.get(channel.id): return
        letter = random.choice(ARABIC_LETTERS)
        gs["current_letter"] = letter
        gs["round_answers"] = {}
        gs["round_active"] = True
        pids = list(gs["players"].keys())
        assign = {cat: gs["players"][random.choice(pids)] for cat in RIPLKA_CATS}
        gs["assigned"] = assign
        assign_text = "\n".join(f"**{cat}:** {u.mention}" for cat, u in assign.items())
        embed = discord.Embed(
            title=f"🔤  الجولة {rnd}/{max_rounds}  —  الحرف: **{letter}**",
            description=f"{assign_text}\n\n📝 أرسل إجاباتك:\n`اسم:X حيوان:X نبات:X دولة:X جماد:X طعام:X مهنة:X فيلم:X رياضة:X مدينة:X`\n\n⏱️ **60 ثانية!**",
            color=C_GOLD
        )
        embed.set_footer(text="⚔️ Lucifer Gaming • discord.gg/lf1")
        await channel.send(embed=embed)
        await asyncio.sleep(60)
        if not active_games.get(channel.id): return
        gs["round_active"] = False
        embed2 = discord.Embed(title=f"📊  نتائج الجولة {rnd}", color=C_FIRE)
        if gs["round_answers"]:
            for uid, ans in gs["round_answers"].items():
                u = gs["players"].get(uid)
                embed2.add_field(name=u.display_name if u else "؟", value=ans[:300], inline=False)
                gs["scores"][uid] = gs["scores"].get(uid, 0) + 10
        else:
            embed2.description = "لم يجب أحد! 😅"
        embed2.set_footer(text="⚔️ Lucifer Gaming")
        await channel.send(embed=embed2)
        await asyncio.sleep(3)

    active_games.pop(channel.id, None)
    sorted_s = sorted(gs["scores"].items(), key=lambda x: x[1], reverse=True)
    medals = ["🥇","🥈","🥉"]
    desc = ""
    winner_name = "—"
    for i, (uid, sc) in enumerate(sorted_s[:5]):
        u = gs["players"].get(uid)
        name = u.display_name if u else "؟"
        if i == 0: winner_name = name
        desc += f"{medals[i] if i<3 else str(i+1)+'.'} **{name}** — {sc} نقطة\n"
        update_player(uid, points=sc, xp=sc, games=1, wins=1 if i == 0 else 0, coins=sc*2)
    add_match("ريبلكا", winner_name, [u.display_name for u in gs["players"].values()], channel.guild.id)
    embed = discord.Embed(title="🏁  انتهت ريبلكا!", description=desc or "—", color=C_GOLD)
    embed.set_image(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
    embed.set_footer(text="⚔️ Lucifer Gaming • discord.gg/lf1")
    await channel.send(embed=embed)

@bot.command(name="ريبلكا")
async def riplka_cmd(ctx):
    cid = ctx.channel.id
    if not is_game_enabled("ريبلكا"):
        return await ctx.send(embed=lucifer_embed("🔒 معطّل", "لعبة ريبلكا معطّلة حالياً!", C_FIRE))
    if cid in active_games:
        return await ctx.send(embed=lucifer_embed("❌ خطأ", "يوجد لعبة جارية في هذه القناة!", C_FIRE))
    gs = {"type":"riplka","host":ctx.author,"players":{ctx.author.id:ctx.author},"started":False,"max_rounds":5,"round_answers":{},"round_active":False,"scores":{}}
    active_games[cid] = gs
    view = RiplkaLobbyView(gs)
    await ctx.send(embed=view.make_embed(), view=view)

# 
#   🔫 مافيا
# 

MAFIA_ROLES_INFO = {
    "مافيا": {"emoji":"🔫","team":"mafia","desc":"تقتل مدنياً كل ليلة"},
    "مدني":  {"emoji":"👤","team":"civil","desc":"صوّت لطرد المافيا"},
    "محقق":  {"emoji":"🕵️","team":"civil","desc":"تكشف هوية لاعب كل ليلة"},
    "طبيب":  {"emoji":"💊","team":"civil","desc":"تحمي لاعباً من القتل"},
}

def assign_mafia_roles(pids):
    n = len(pids)
    mafia_count = max(1, n // 4)
    shuffled = list(pids); random.shuffle(shuffled)
    roles = {}
    for i, uid in enumerate(shuffled):
        if i < mafia_count:                    roles[uid] = "مافيا"
        elif i == mafia_count and n >= 5:      roles[uid] = "محقق"
        elif i == mafia_count+1 and n >= 6:    roles[uid] = "طبيب"
        else:                                   roles[uid] = "مدني"
    return roles

class MafiaLobbyView(discord.ui.View):
    def __init__(self, gs):
        super().__init__(timeout=600)
        self.gs = gs

    def make_embed(self):
        gs = self.gs
        n = len(gs["players"])
        embed = discord.Embed(title="🔫  لعبة المافيا", color=C_FIRE)
        embed.set_thumbnail(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
        embed.add_field(name="الأدوار", value="🔫 **مافيا**\n🕵️ **محقق**\n💊 **طبيب**\n👤 **مدني**", inline=True)
        embed.add_field(name=f"اللاعبين ({n})", value=pl_text(gs["players"]), inline=True)
        embed.set_footer(text=f"👑 {gs['host'].display_name} • ⚔️ Lucifer Gaming")
        return embed

    @discord.ui.button(label="دخول إلى اللعبة", style=discord.ButtonStyle.success, emoji="🎮", row=0)
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        if gs.get("started"): return await interaction.response.send_message("❌ بدأت!", ephemeral=True)
        if interaction.user.id in gs["players"]: return await interaction.response.send_message("⚠️ مسجل!", ephemeral=True)
        gs["players"][interaction.user.id] = interaction.user
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="اخرج من اللعبة", style=discord.ButtonStyle.danger, emoji="🚪", row=0)
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        uid = interaction.user.id
        if gs.get("started"): return await interaction.response.send_message("❌ بدأت!", ephemeral=True)
        if uid not in gs["players"]: return await interaction.response.send_message("⚠️ لست فيها!", ephemeral=True)
        if uid == gs["host"].id: return await interaction.response.send_message("❌ المضيف لا يخرج!", ephemeral=True)
        del gs["players"][uid]
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="▶️ ابدأ", style=discord.ButtonStyle.primary, row=1)
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        if interaction.user.id != gs["host"].id: return await interaction.response.send_message("❌ فقط المضيف!", ephemeral=True)
        if gs.get("started"): return await interaction.response.send_message("❌ بدأت!", ephemeral=True)
        if len(gs["players"]) < 2: return await interaction.response.send_message("❌ تحتاج لاعبَين!", ephemeral=True)
        gs["started"] = True
        for c in self.children: c.disabled = True
        embed = self.make_embed(); embed.set_footer(text="🚀 انطلقت المافيا!")
        await interaction.response.edit_message(embed=embed, view=self)
        await start_mafia_game(interaction.channel, gs)

async def start_mafia_game(channel, gs):
    gs["alive"] = dict(gs["players"])
    gs["roles"] = assign_mafia_roles(list(gs["players"].keys()))
    gs["round"] = 0; gs["actions"] = {}; gs["votes"] = {}
    await channel.send(embed=lucifer_embed("📨 الأدوار", "تم إرسال الأدوار سراً لكل لاعب!", C_GOLD))
    for uid, role in gs["roles"].items():
        user = gs["players"][uid]; ri = MAFIA_ROLES_INFO[role]
        try:
            e = lucifer_embed("🎭 دورك في المافيا", f"{ri['emoji']} أنت: **{role}**\n📋 {ri['desc']}\n**الفريق:** {'🔴 المافيا' if ri['team']=='mafia' else '🔵 المدنيون'}", C_GOLD)
            await user.send(embed=e)
        except Exception: pass
    await run_mafia_night(channel, gs)

class VoteView(discord.ui.View):
    def __init__(self, gs, alive_users):
        super().__init__(timeout=60)
        self.gs = gs
        for user in alive_users[:25]:
            btn = discord.ui.Button(label=user.display_name, style=discord.ButtonStyle.secondary)
            btn.callback = self._make_cb(user.id, user.display_name)
            self.add_item(btn)

    def _make_cb(self, tid, tname):
        async def cb(interaction: discord.Interaction):
            if interaction.user.id not in self.gs["alive"]:
                return await interaction.response.send_message("❌ لست حياً!", ephemeral=True)
            self.gs["votes"][interaction.user.id] = tid
            await interaction.response.send_message(f"✅ صوّتت على **{tname}**", ephemeral=True)
        return cb

async def run_mafia_night(channel, gs):
    if not active_games.get(channel.id): return
    gs["round"] += 1; gs["actions"] = {}; gs["phase"] = "night"
    embed = discord.Embed(title=f"🌙  الليلة {gs['round']}",description=f"**الأحياء:**\n{pl_text(gs['alive'])}\n\n📩 DM البوت أمرك:\n• مافيا: `اقتل اسم`\n• طبيب: `احمي اسم`\n• محقق: `تحقق اسم`\n\n⏱️ **45 ثانية**",color=C_DARK)
    embed.set_footer(text="⚔️ Lucifer Gaming")
    await channel.send(embed=embed)
    await asyncio.sleep(45)
    if not active_games.get(channel.id): return
    await run_mafia_day(channel, gs)

async def run_mafia_day(channel, gs):
    if not active_games.get(channel.id): return
    gs["phase"] = "day"
    killed = gs["actions"].get("kill"); protected = gs["actions"].get("protect")
    night_msg = ""
    if killed and killed in gs["alive"]:
        if killed == protected: night_msg = "💊 الطبيب أنقذ لاعباً!"
        else:
            victim = gs["alive"].pop(killed)
            night_msg = f"💀 **{victim.display_name}** قُتل! دوره: **{gs['roles'].get(killed,'؟')}**"
            update_player(killed, games=1)
    else: night_msg = "🌅 مرت الليلة بسلام!"
    gs["votes"] = {}
    alive_users = list(gs["alive"].values())
    vote_view = VoteView(gs, alive_users)
    embed = discord.Embed(title=f"☀️  النهار {gs['round']}",description=f"**نتيجة الليل:** {night_msg}\n\n**الأحياء:**\n{pl_text(gs['alive'])}\n\n🗳️ **صوّتوا — 60 ثانية!**",color=C_GOLD)
    embed.set_footer(text="⚔️ Lucifer Gaming")
    await channel.send(embed=embed, view=vote_view)
    await asyncio.sleep(60)
    if not active_games.get(channel.id): return
    vote_count = {}
    for _, tid in gs["votes"].items(): vote_count[tid] = vote_count.get(tid,0)+1
    if vote_count:
        expelled_id = max(vote_count, key=vote_count.get)
        if expelled_id in gs["alive"]:
            expelled = gs["alive"].pop(expelled_id)
            await channel.send(embed=lucifer_embed("🗳️ طُرد!", f"**{expelled.display_name}** طُرد! دوره: **{gs['roles'].get(expelled_id,'؟')}**", C_FIRE))
            update_player(expelled_id, games=1)
    else: await channel.send(embed=lucifer_embed("⚠️", "لم يصوت أحد!", C_FIRE))
    mafia_alive = [u for u,r in gs["roles"].items() if r=="مافيا" and u in gs["alive"]]
    civil_alive = [u for u,r in gs["roles"].items() if r!="مافيا" and u in gs["alive"]]
    if not mafia_alive:
        add_match("مافيا","المدنيون",[u.display_name for u in gs["players"].values()],channel.guild.id)
        for u in civil_alive: update_player(u, wins=1, points=50, coins=100, xp=80, games=1)
        active_games.pop(channel.id, None)
        await channel.send(embed=lucifer_embed("🎉 فاز المدنيون!", "تم القضاء على المافيا! 🏆", C_GOLD))
    elif len(mafia_alive) >= len(civil_alive):
        add_match("مافيا","المافيا",[u.display_name for u in gs["players"].values()],channel.guild.id)
        for u in mafia_alive: update_player(u, wins=1, points=50, coins=100, xp=80, games=1)
        active_games.pop(channel.id, None)
        await channel.send(embed=lucifer_embed("💀 فازت المافيا!", "سيطروا على المدينة!", C_FIRE))
    else: await run_mafia_night(channel, gs)

@bot.command(name="مافيا")
async def mafia_cmd(ctx):
    cid = ctx.channel.id
    if not is_game_enabled("مافيا"): return await ctx.send(embed=lucifer_embed("🔒","مافيا معطّلة!",C_FIRE))
    if cid in active_games: return await ctx.send(embed=lucifer_embed("❌","يوجد لعبة جارية!",C_FIRE))
    gs = {"type":"mafia","host":ctx.author,"players":{ctx.author.id:ctx.author},"started":False,"alive":{},"roles":{},"round":0,"actions":{},"votes":{},"phase":"lobby"}
    active_games[cid] = gs
    view = MafiaLobbyView(gs)
    await ctx.send(embed=view.make_embed(), view=view)

# 
#   🎡 روليت — عجلة طرد بتصميم Lucifer
# 

class RouletteWheelLobby(discord.ui.View):
    def __init__(self, gs):
        super().__init__(timeout=600)
        self.gs = gs

    def make_embed(self):
        gs = self.gs
        n = len(gs["players"])
        embed = discord.Embed(title="🎡  روليت الطرد", color=C_GOLD)
        embed.set_thumbnail(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
        embed.add_field(name="طريقة اللعب", value="**1-** الجميع يدخلون\n**2-** المضيف يدور العجلة\n**3-** العجلة تطرد لاعب\n**4-** آخر لاعب يفوز!", inline=False)
        embed.add_field(name=f"اللاعبون ({n})", value=pl_text(gs["players"]), inline=False)
        embed.set_footer(text=f"👑 {gs['host'].display_name} • ⚔️ Lucifer Gaming")
        return embed

    @discord.ui.button(label="دخول إلى اللعبة", style=discord.ButtonStyle.success, emoji="🎮", row=0)
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        if gs.get("started"): return await interaction.response.send_message("❌ بدأت!", ephemeral=True)
        if interaction.user.id in gs["players"]: return await interaction.response.send_message("⚠️ مسجل!", ephemeral=True)
        gs["players"][interaction.user.id] = interaction.user
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="اخرج من اللعبة", style=discord.ButtonStyle.danger, emoji="🚪", row=0)
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        uid = interaction.user.id
        if gs.get("started"): return await interaction.response.send_message("❌ بدأت!", ephemeral=True)
        if uid not in gs["players"]: return await interaction.response.send_message("⚠️ لست فيها!", ephemeral=True)
        if uid == gs["host"].id: return await interaction.response.send_message("❌ المضيف لا يخرج!", ephemeral=True)
        del gs["players"][uid]
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="🎡 دوّر العجلة!", style=discord.ButtonStyle.primary, row=1)
    async def spin_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        if interaction.user.id != gs["host"].id: return await interaction.response.send_message("❌ فقط المضيف!", ephemeral=True)
        if len(gs["players"]) < 2: return await interaction.response.send_message("❌ تحتاج لاعبَين!", ephemeral=True)
        gs["started"] = True
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(embed=self.make_embed(), view=self)
        await run_roulette_wheel(interaction.channel, gs)

async def run_roulette_wheel(channel, gs):
    cid = channel.id
    while len(gs["players"]) > 1:
        if not active_games.get(cid): return
        spin_msg = await channel.send("🎡 العجلة تدور...")
        names = list(gs["players"].values())
        for frame in ["🎡 ●○○○○○","🎡 ○●○○○○","🎡 ○○●○○○","🎡 ○○○●○○","🎡 ○○○○●○","🎡 ○○○○○●"]:
            await asyncio.sleep(0.5)
            try: await spin_msg.edit(content=frame)
            except: pass
        await asyncio.sleep(0.5)
        eliminated_id = random.choice(list(gs["players"].keys()))
        eliminated = gs["players"].pop(eliminated_id)
        update_player(eliminated_id, games=1)
        remaining = len(gs["players"])
        names_left = " | ".join(u.display_name for u in gs["players"].values())
        embed = discord.Embed(
            description=f"🎡 **العجلة توقفت على... {eliminated.mention}!**\n💥 **{eliminated.display_name}** طُرد!\n\n**المتبقون ({remaining}):** {names_left or '—'}",
            color=C_FIRE
        )
        embed.set_footer(text="⚔️ Lucifer Gaming")
        await spin_msg.edit(content=None, embed=embed)
        if remaining <= 1: break
        await asyncio.sleep(3)
    active_games.pop(cid, None)
    if gs["players"]:
        winner = list(gs["players"].values())[0]
        update_player(winner.id, wins=1, points=50, coins=150, xp=80, games=1)
        add_match("روليت", winner.display_name, [u.display_name for u in gs["players"].values()], channel.guild.id)
        embed = discord.Embed(title="🏆  فاز في الروليت!", description=f"🎉 **{winner.mention}** نجا من العجلة!\n💰 +150🪙 | +50 نقطة", color=C_GOLD)
        embed.set_thumbnail(url=winner.display_avatar.url)
        embed.set_footer(text="⚔️ Lucifer Gaming")
        await channel.send(embed=embed)
    else: await channel.send(embed=lucifer_embed("🏁","انتهت اللعبة!",C_FIRE))

@bot.command(name="روليت")
async def roulette_cmd(ctx):
    cid = ctx.channel.id
    if not is_game_enabled("روليت"): return await ctx.send(embed=lucifer_embed("🔒","روليت معطّل!",C_FIRE))
    if cid in active_games: return await ctx.send(embed=lucifer_embed("❌","يوجد لعبة جارية!",C_FIRE))
    gs = {"type":"roulette","host":ctx.author,"players":{ctx.author.id:ctx.author},"started":False}
    active_games[cid] = gs
    view = RouletteWheelLobby(gs)
    await ctx.send(embed=view.make_embed(), view=view)

# 
#   ⚡ سرعة — بدون تسجيل
# 

SPEED_WORDS = ["أكاديمية","ديسكورد","لوسيفر","عسكرية","بطولة","مسابقة","انتصار","لاعبون","مجتمع","قوانين","تحديات","فعاليات","مكافآت","إنجازات","مستويات","ريبلكا","فائز","خاسر","نقاط","عملات"]

@bot.command(name="سرعة")
async def speed_cmd(ctx):
    cid = ctx.channel.id
    if not is_game_enabled("سرعة"): return await ctx.send(embed=lucifer_embed("🔒","سرعة معطّلة!",C_FIRE))
    if cid in active_games: return await ctx.send(embed=lucifer_embed("❌","يوجد لعبة جارية!",C_FIRE))
    word = random.choice(SPEED_WORDS)
    active_games[cid] = {"type":"speed","word":word,"winner":None,"host":ctx.author}
    embed = discord.Embed(title="⚡  لعبة السرعة — بدون تسجيل!",description=f"أول شخص يكتب الكلمة بالضبط يفوز!\n\n## `{word}`\n\n⏱️ **30 ثانية!**",color=C_GOLD)
    embed.set_footer(text="⚔️ Lucifer Gaming • discord.gg/lf1")
    await ctx.send(embed=embed)
    await asyncio.sleep(30)
    state = active_games.pop(cid, None)
    if state and not state.get("winner"):
        await ctx.send(embed=lucifer_embed("⏰ انتهى الوقت!", "لم يفز أحد.", C_FIRE))

# 
#   🧠 سؤال — بدون تسجيل
# 

TRIVIA_QUESTIONS = [
    {"q":"ما عاصمة فرنسا؟","a":"باريس"},{"q":"كم عدد أضلاع المثلث؟","a":"3"},
    {"q":"ما أسرع حيوان بري؟","a":"الفهد"},{"q":"كم كوكب في المجموعة الشمسية؟","a":"8"},
    {"q":"ما عاصمة اليابان؟","a":"طوكيو"},{"q":"في أي قارة تقع مصر؟","a":"أفريقيا"},
    {"q":"كم يوم في السنة العادية؟","a":"365"},{"q":"ما عاصمة السعودية؟","a":"الرياض"},
    {"q":"كم ساعة في اليوم؟","a":"24"},{"q":"ما أطول نهر في العالم؟","a":"النيل"},
    {"q":"كم ضلع للمربع؟","a":"4"},{"q":"ما عاصمة ألمانيا؟","a":"برلين"},
    {"q":"ما أكبر محيط في العالم؟","a":"الهادي"},{"q":"كم دقيقة في الساعة؟","a":"60"},
    {"q":"ما أكبر كوكب في المجموعة؟","a":"المشتري"},{"q":"كم لون في قوس قزح؟","a":"7"},
]

@bot.command(name="سؤال", aliases=["ألغاز","تريفيا"])
async def trivia_cmd(ctx):
    cid = ctx.channel.id
    if not is_game_enabled("سؤال"): return await ctx.send(embed=lucifer_embed("🔒","سؤال معطّل!",C_FIRE))
    if cid in active_games: return await ctx.send(embed=lucifer_embed("❌","يوجد لعبة جارية!",C_FIRE))
    q = random.choice(TRIVIA_QUESTIONS)
    active_games[cid] = {"type":"trivia","answer":q["a"],"winner":None}
    embed = discord.Embed(title="🧠  سؤال — من يعرف الجواب؟",description=f"## {q['q']}\n\n⏱️ **30 ثانية!** — أرسل الجواب مباشرة",color=C_GOLD)
    embed.set_footer(text="⚔️ Lucifer Gaming • discord.gg/lf1")
    await ctx.send(embed=embed)
    await asyncio.sleep(30)
    state = active_games.pop(cid, None)
    if state and not state.get("winner"):
        await ctx.send(embed=lucifer_embed("⏰ انتهى الوقت!", f"الجواب الصحيح: **{q['a']}**", C_FIRE))

# 
#   🎭 كذب أو صدق
# 

class LieOrTruthLobby(discord.ui.View):
    def __init__(self, gs):
        super().__init__(timeout=600)
        self.gs = gs

    def make_embed(self):
        gs = self.gs
        n = len(gs["players"])
        embed = discord.Embed(title="🎭  كذب أو صدق", color=C_GOLD)
        embed.set_thumbnail(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
        embed.add_field(name="طريقة اللعب", value="**1-** الجميع يدخلون\n**2-** كل جولة لاعب عشوائي يقول جملة\n**3-** البقية يصوتون: كذب 🔴 أم صدق 🟢\n**4-** من يخدع أكثر يفوز!", inline=False)
        embed.add_field(name=f"اللاعبون ({n})", value=pl_text(gs["players"]), inline=False)
        embed.set_footer(text=f"👑 {gs['host'].display_name} • ⚔️ Lucifer Gaming")
        return embed

    @discord.ui.button(label="دخول إلى اللعبة", style=discord.ButtonStyle.success, emoji="🎮", row=0)
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        if gs.get("started"): return await interaction.response.send_message("❌ بدأت!", ephemeral=True)
        if interaction.user.id in gs["players"]: return await interaction.response.send_message("⚠️ مسجل!", ephemeral=True)
        gs["players"][interaction.user.id] = interaction.user
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="اخرج من اللعبة", style=discord.ButtonStyle.danger, emoji="🚪", row=0)
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        uid = interaction.user.id
        if gs.get("started"): return await interaction.response.send_message("❌ بدأت!", ephemeral=True)
        if uid not in gs["players"]: return await interaction.response.send_message("⚠️ لست فيها!", ephemeral=True)
        if uid == gs["host"].id: return await interaction.response.send_message("❌ المضيف لا يخرج!", ephemeral=True)
        del gs["players"][uid]
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="▶️ ابدأ", style=discord.ButtonStyle.primary, row=1)
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        if interaction.user.id != gs["host"].id: return await interaction.response.send_message("❌ فقط المضيف!", ephemeral=True)
        if gs.get("started"): return await interaction.response.send_message("❌ بدأت!", ephemeral=True)
        if len(gs["players"]) < 2: return await interaction.response.send_message("❌ تحتاج لاعبَين!", ephemeral=True)
        gs["started"] = True
        for c in self.children: c.disabled = True
        embed = self.make_embed(); embed.set_footer(text="🎭 انطلق كذب أو صدق!")
        await interaction.response.edit_message(embed=embed, view=self)
        await run_lie_truth(interaction.channel, gs)

class LieTruthVoteView(discord.ui.View):
    def __init__(self, gs, speaker_id):
        super().__init__(timeout=20)
        self.gs = gs; self.speaker_id = speaker_id
        self.votes = {"lie":0,"truth":0}

    @discord.ui.button(label="🔴 كذب", style=discord.ButtonStyle.danger)
    async def lie_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.speaker_id: return await interaction.response.send_message("❌ لا تصوت على نفسك!", ephemeral=True)
        voted = self.gs.setdefault("voted_round",{})
        if str(interaction.user.id) in voted: return await interaction.response.send_message("⚠️ صوّتت!", ephemeral=True)
        voted[str(interaction.user.id)] = "lie"; self.votes["lie"] += 1
        await interaction.response.send_message("✅ صوّتت: **كذب**", ephemeral=True)

    @discord.ui.button(label="🟢 صدق", style=discord.ButtonStyle.success)
    async def truth_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.speaker_id: return await interaction.response.send_message("❌ لا تصوت على نفسك!", ephemeral=True)
        voted = self.gs.setdefault("voted_round",{})
        if str(interaction.user.id) in voted: return await interaction.response.send_message("⚠️ صوّتت!", ephemeral=True)
        voted[str(interaction.user.id)] = "truth"; self.votes["truth"] += 1
        await interaction.response.send_message("✅ صوّتت: **صدق**", ephemeral=True)

async def run_lie_truth(channel, gs):
    gs["lt_scores"] = {uid:0 for uid in gs["players"]}
    rounds = min(len(gs["players"])*2, 10)
    for rnd in range(1, rounds+1):
        if not active_games.get(channel.id): return
        speaker_id = random.choice(list(gs["players"].keys()))
        speaker = gs["players"][speaker_id]; gs["voted_round"] = {}
        embed = discord.Embed(title=f"🎭  الجولة {rnd}/{rounds}",description=f"**{speaker.mention}** دورك!\n\n📝 أرسل جملة عنك\n\n⏱️ **20 ثانية**",color=C_GOLD)
        embed.set_footer(text="⚔️ Lucifer Gaming")
        await channel.send(embed=embed)
        def check(m): return m.author.id == speaker_id and m.channel.id == channel.id
        statement = None; is_lie = None
        try:
            msg = await bot.wait_for("message", check=check, timeout=20)
            statement = msg.content[:200]
        except asyncio.TimeoutError:
            await channel.send(embed=lucifer_embed("⏰","لم يرسل جملة! نتخطى.",C_FIRE)); continue
        try:
            e = lucifer_embed("🎭 دورك", f"جملتك: **{statement}**\n\nأرسل: `كذب` أو `صدق`", C_GOLD)
            await speaker.send(embed=e)
            def dm_check(m): return m.author.id == speaker_id and isinstance(m.channel, discord.DMChannel)
            reply = await bot.wait_for("message", check=dm_check, timeout=15)
            is_lie = "كذب" in reply.content
        except Exception: is_lie = random.choice([True, False])
        vote_view = LieTruthVoteView(gs, speaker_id)
        embed2 = discord.Embed(title="🗳️  صوّتوا الآن!",description=f"**{speaker.display_name}** قال:\n> {statement}\n\n**كذب أم صدق؟ — 20 ثانية!**",color=C_FIRE)
        embed2.set_footer(text="⚔️ Lucifer Gaming")
        await channel.send(embed=embed2, view=vote_view)
        await asyncio.sleep(20)
        lie_v = vote_view.votes["lie"]; truth_v = vote_view.votes["truth"]
        majority_said_lie = lie_v > truth_v
        speaker_fooled = (is_lie and not majority_said_lie) or (not is_lie and majority_said_lie)
        result_text = "كذب 🔴" if is_lie else "صدق 🟢"
        if speaker_fooled:
            gs["lt_scores"][speaker_id] = gs["lt_scores"].get(speaker_id,0)+10
            outcome = f"✅ **{speaker.display_name}** خدع الجميع! +10 نقطة"
        else: outcome = f"❌ **{speaker.display_name}** اكتُشف!"
        await channel.send(embed=lucifer_embed("النتيجة", f"الحقيقة: **{result_text}**\n🔴 كذب={lie_v} | 🟢 صدق={truth_v}\n{outcome}", C_GOLD))
        await asyncio.sleep(3)
    active_games.pop(channel.id, None)
    sorted_s = sorted(gs["lt_scores"].items(), key=lambda x: x[1], reverse=True)
    medals = ["🥇","🥈","🥉"]; desc = ""; winner_name = "—"
    for i,(uid,sc) in enumerate(sorted_s[:5]):
        u = gs["players"].get(uid); name = u.display_name if u else "؟"
        if i==0: winner_name = name
        desc += f"{medals[i] if i<3 else str(i+1)+'.'} **{name}** — {sc} نقطة\n"
        update_player(uid, points=sc, xp=sc, games=1, wins=1 if i==0 else 0, coins=sc*2)
    add_match("كذب_أو_صدق", winner_name, [u.display_name for u in gs["players"].values()], channel.guild.id)
    embed = discord.Embed(title="🏁  انتهى كذب أو صدق!", description=desc or "—", color=C_GOLD)
    embed.set_image(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
    embed.set_footer(text="⚔️ Lucifer Gaming • discord.gg/lf1")
    await channel.send(embed=embed)

@bot.command(name="كذب", aliases=["كذب_صدق"])
async def lie_truth_cmd(ctx):
    cid = ctx.channel.id
    if not is_game_enabled("كذب"): return await ctx.send(embed=lucifer_embed("🔒","كذب أو صدق معطّل!",C_FIRE))
    if cid in active_games: return await ctx.send(embed=lucifer_embed("❌","يوجد لعبة جارية!",C_FIRE))
    gs = {"type":"lie_truth","host":ctx.author,"players":{ctx.author.id:ctx.author},"started":False,"lt_scores":{}}
    active_games[cid] = gs
    await ctx.send(embed=LieOrTruthLobby(gs).make_embed(), view=LieOrTruthLobby(gs))

# 
#   🔐 الكلمة السرية
# 

SECRET_WORDS = ["تفاحة","سيارة","كتاب","شمس","قمر","بحر","جبل","نار","ماء","هاتف","طائرة","قطة","كلب","شجرة","باب","نافذة","مطبخ","حديقة","مدرسة","مستشفى","ملعب","سيف","قلم","ساعة"]

@bot.command(name="كلمة_سرية", aliases=["سرية","20سؤال"])
async def secret_word_cmd(ctx):
    cid = ctx.channel.id
    if not is_game_enabled("كلمة_سرية"): return await ctx.send(embed=lucifer_embed("🔒","كلمة سرية معطّلة!",C_FIRE))
    if cid in active_games: return await ctx.send(embed=lucifer_embed("❌","يوجد لعبة جارية!",C_FIRE))
    word = random.choice(SECRET_WORDS)
    active_games[cid] = {"type":"secret_word","word":word,"questions":0,"max_q":20,"host":ctx.author,"winner":None}
    try:
        e = lucifer_embed("🔐 الكلمة السرية", f"الكلمة: `{word}`\n\nأجب بـ **نعم** أو **لا** فقط!", C_GOLD)
        await ctx.author.send(embed=e)
    except: pass
    embed = discord.Embed(title="🔐  الكلمة السرية — 20 سؤال",description=f"**{ctx.author.mention}** يعرف كلمة سرية!\n\n📋 اسألوه أسئلة بـ نعم/لا فقط\n✅ للتخمين: `الجواب: كلمتك`\n\n🔍 ابدأوا بالأسئلة بدون تسجيل!",color=C_GOLD)
    embed.set_footer(text=f"الأسئلة المتبقية: 20/20 • ⚔️ Lucifer Gaming")
    await ctx.send(embed=embed)

# 
#   💣 بومبة
# 

class BombView(discord.ui.View):
    def __init__(self, gs):
        super().__init__(timeout=180)
        self.gs = gs; self.pressed_count = 0

    @discord.ui.button(label="💣 اضغط!", style=discord.ButtonStyle.danger, emoji="💣", row=0)
    async def bomb_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs; uid = interaction.user.id
        exploded = gs.setdefault("exploded", set())
        if uid in exploded: return await interaction.response.send_message("💀 أنت انفجرت!", ephemeral=True)
        self.pressed_count += 1
        explode_chance = min(0.10 + self.pressed_count*0.04, 0.85)
        if random.random() < explode_chance:
            exploded.add(uid); gs["players"][uid] = interaction.user
            update_player(uid, games=1)
            await interaction.response.send_message(f"💥 **{interaction.user.mention} انفجر!** 💀", ephemeral=False)
            survivors = [u for uid2,u in gs["players"].items() if uid2 not in exploded]
            if len(survivors) == 1 and len(gs["players"]) > 1:
                s = survivors[0]; update_player(s.id, wins=1, points=30, coins=100, xp=50, games=1)
                button.disabled = True; active_games.pop(interaction.channel.id, None)
                try: await interaction.message.edit(view=self)
                except: pass
                embed = lucifer_embed("🏆 الفائز!", f"**{s.mention}** نجا من الانفجار! +100🪙", C_GOLD)
                await interaction.channel.send(embed=embed)
        else:
            gs["players"][uid] = interaction.user
            await interaction.response.send_message(f"😅 **{interaction.user.display_name}** ضغط وسلم! (الضغطة {self.pressed_count} 🔺)", ephemeral=False)

    @discord.ui.button(label="👀 الإحصاء", style=discord.ButtonStyle.secondary, row=0)
    async def status_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gs = self.gs
        total = len(gs["players"]); exploded = len(gs.get("exploded", set()))
        pct = min(10 + self.pressed_count*4, 85)
        await interaction.response.send_message(f"💣 الضغطات: **{self.pressed_count}**\n💀 انفجروا: **{exploded}**\n👥 لاعبون: **{total}**\n🔺 احتمال الانفجار: **{pct}%**", ephemeral=True)

@bot.command(name="بومبة", aliases=["boom","قنبلة"])
async def bomb_cmd(ctx):
    cid = ctx.channel.id
    if not is_game_enabled("بومبة"): return await ctx.send(embed=lucifer_embed("🔒","بومبة معطّلة!",C_FIRE))
    if cid in active_games: return await ctx.send(embed=lucifer_embed("❌","يوجد لعبة جارية!",C_FIRE))
    gs = {"type":"bomb","host":ctx.author,"players":{},"exploded":set()}
    active_games[cid] = gs
    embed = discord.Embed(title="💣  لعبة البومبة!", description="**اضغط الزر قبل ما تنفجر!**\n\n• احتمال الانفجار يرتفع مع كل ضغطة 🔺\n• من ينفجر يخرج 💀\n• آخر شخص يفوز 🏆\n\n💡 **الجميع يضغط بدون تسجيل!**", color=C_GOLD)
    embed.set_footer(text="⚔️ Lucifer Gaming • discord.gg/lf1")
    await ctx.send(embed=embed, view=BombView(gs))

# 
#   🎲 عشوائي
# 

GAMES_LIST = [("🎭 ريبلكا","!ريبلكا"),("🔫 مافيا","!مافيا"),("🎡 روليت","!روليت"),("⚡ سرعة","!سرعة"),("🧠 سؤال","!سؤال"),("🎭 كذب","!كذب"),("🔐 كلمة سرية","!كلمة_سرية"),("💣 بومبة","!بومبة"),("🏆 بطولة","!بطولة")]

class RandomView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        for name, cmd in GAMES_LIST:
            btn = discord.ui.Button(label=name, style=discord.ButtonStyle.secondary)
            btn.callback = self._make_cb(name, cmd)
            self.add_item(btn)
    def _make_cb(self, name, cmd):
        async def cb(interaction: discord.Interaction):
            for c in self.children: c.disabled = True
            await interaction.response.edit_message(content=f"🚀 اخترت **{name}**! اكتب `{cmd}` لبدئها.", view=self)
        return cb

@bot.command(name="عشوائي")
async def random_cmd(ctx):
    chosen = random.choice(GAMES_LIST)
    await ctx.send(f"🎲 اقتراح: **{chosen[0]}** — `{chosen[1]}`\n\nأو اختر:", view=RandomView())

# 
#   !انهي + !مساعدة
# 

@bot.command(name="انهي")
async def end_cmd(ctx):
    cid = ctx.channel.id
    gs = active_games.get(cid)
    if not gs:
        return await ctx.send(embed=lucifer_embed("❌","لا توجد لعبة جارية!",C_FIRE))
    host = gs.get("host")
    if ctx.author.id != (host.id if host else 0) and not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=lucifer_embed("❌","فقط المضيف أو الأدمن!",C_FIRE))
    active_games.pop(cid, None)
    await ctx.send(embed=lucifer_embed("🛑 انتهت","تم إنهاء اللعبة.",C_FIRE))

@bot.command(name="مسح", aliases=["reset","كلير"])
async def force_clear(ctx):
    """امسح اللعبة العالقة — للأدمن فقط"""
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=lucifer_embed("❌","للأدمن فقط!",C_FIRE))
    cid = ctx.channel.id
    if cid in active_games:
        active_games.pop(cid, None)
        await ctx.send(embed=lucifer_embed("🧹 تم المسح","تم مسح اللعبة العالقة! الآن يمكنك بدء لعبة جديدة.",C_GOLD))
    else:
        await ctx.send(embed=lucifer_embed("✅ نظيف","لا توجد لعبة عالقة في هذه القناة.",C_GOLD))

@bot.command(name="حالة")
async def status_cmd(ctx):
    """اعرض حالة الألعاب الجارية"""
    if not active_games:
        return await ctx.send(embed=lucifer_embed("✅ الحالة","لا توجد ألعاب جارية حالياً.",C_GOLD))
    desc = ""
    for ch_id, gs in active_games.items():
        ch = ctx.guild.get_channel(ch_id)
        ch_name = ch.name if ch else str(ch_id)
        game_type = gs.get("type","؟")
        host = gs.get("host")
        host_name = host.display_name if host else "؟"
        players = len(gs.get("players",{}))
        desc += f"**#{ch_name}** — {game_type} | المضيف: {host_name} | {players} لاعبين\n"
    await ctx.send(embed=lucifer_embed("🎮 الألعاب الجارية", desc, C_GOLD))

@bot.command(name="مساعدة", aliases=["help"])
async def help_cmd(ctx):
    embed = discord.Embed(title="⚔️  أكاديمية Lucifer — الأوامر", color=C_GOLD)
    embed.set_image(url=LUCIFER_IMG if LUCIFER_IMG and "imgur" not in LUCIFER_IMG else discord.Embed.Empty)
    embed.add_field(name=" ألعاب بدخول ", value=(
        "`!ريبلكا` — 10 فئات 🎭\n`!مافيا` — أدوار سرية 🔫\n"
        "`!روليت` — عجلة طرد 🎡\n`!كذب` — كذب أو صدق 🎭\n"
        "`!بطولة` — بطولة نوك-أوت 🏆"
    ), inline=False)
    embed.add_field(name=" ألعاب فورية ", value=(
        "`!سرعة` — أسرع كاتب ⚡\n`!سؤال` — سؤال عام 🧠\n"
        "`!كلمة_سرية` — 20 سؤال 🔐\n`!بومبة` — اضغط الزر 💣"
    ), inline=False)
    embed.add_field(name=" تحدي ", value=(
        "`!تحدي @لاعب [سرعة/سؤال] [رهان]` — تحدي 1v1 ⚔️"
    ), inline=False)
    embed.add_field(name=" الملف ", value=(
        "`!ملفي` — ملفك الشخصي 👤\n`!ملفي @عضو` — ملف عضو آخر\n"
        "`!ترتيب` — أفضل 10 🏆\n`!متجر` — المتجر 🛒\n`!يومي` — مكافأة يومية 🎁\n`!سجل` — آخر المباريات 📜"
    ), inline=False)
    embed.add_field(name=" الأدمن ", value=(
        "`!تفعيل اسم` / `!تعطيل اسم`\n`!منح_vip @عضو` / `!سحب_vip @عضو`\n`!منح_عملات @عضو الكمية`"
    ), inline=False)
    embed.set_footer(text="⚔️ Lucifer Gaming • discord.gg/lf1 | !انهي لإنهاء اللعبة")
    await ctx.send(embed=embed)

# 
#   on_message
# 

@bot.event
async def on_message(message):
    if message.author.bot: return
    cid = message.channel.id
    state = active_games.get(cid)

    if state:
        t = state.get("type")

        if t == "speed" and not state.get("winner"):
            if message.content.strip() == state["word"]:
                state["winner"] = message.author
                active_games.pop(cid, None)
                update_player(message.author.id, wins=1, points=20, coins=50, xp=30, games=1)
                add_match("سرعة", message.author.display_name, [], message.guild.id)
                embed = lucifer_embed("⚡ فاز!", f"{message.author.mention} كتب الكلمة أولاً! +50🪙", C_GOLD)
                await message.channel.send(embed=embed)

        elif t == "trivia" and not state.get("winner"):
            if state["answer"].lower() in message.content.lower():
                state["winner"] = message.author
                active_games.pop(cid, None)
                update_player(message.author.id, wins=1, points=15, coins=30, xp=20, games=1)
                add_match("سؤال", message.author.display_name, [], message.guild.id)
                embed = lucifer_embed("🧠 أجاب صح!", f"{message.author.mention} الجواب: **{state['answer']}** +30🪙", C_GOLD)
                await message.channel.send(embed=embed)

        elif t == "secret_word":
            content = message.content.strip()
            if content.startswith("الجواب:") or content.startswith("الجواب :"):
                guess = content.replace("الجواب :","").replace("الجواب:","").strip()
                if guess == state["word"]:
                    state["winner"] = message.author
                    active_games.pop(cid, None)
                    update_player(message.author.id, wins=1, points=30, coins=80, xp=50, games=1)
                    add_match("كلمة_سرية", message.author.display_name, [], message.guild.id)
                    embed = lucifer_embed("🎉 خمّن!", f"{message.author.mention} الكلمة: **{state['word']}** في {state['questions']} سؤال! +80🪙", C_GOLD)
                    await message.channel.send(embed=embed)
                else:
                    rem = state["max_q"] - state["questions"]
                    await message.channel.send(embed=lucifer_embed("❌ خطأ!", f"تبقى **{rem}** سؤال.", C_FIRE))
            elif message.author.id != state["host"].id:
                state["questions"] += 1
                rem = state["max_q"] - state["questions"]
                if rem <= 0:
                    word = state["word"]; active_games.pop(cid, None)
                    await message.channel.send(embed=lucifer_embed("💀 انتهت!", f"الكلمة كانت: **{word}**", C_FIRE))
                else:
                    await message.channel.send(embed=lucifer_embed(f"❓ سؤال {state['questions']}/{state['max_q']}", f"**{state['host'].mention}** أجب بـ نعم أو لا! (متبقي **{rem}**)", C_GOLD))

        elif t == "riplka" and state.get("round_active"):
            if message.author.id in state["players"]:
                content = message.content.strip()
                if any(f"{cat}:" in content for cat in RIPLKA_CATS):
                    state["round_answers"][message.author.id] = content
                    await message.add_reaction("✅")

    await bot.process_commands(message)

# 
bot.run(TOKEN)
